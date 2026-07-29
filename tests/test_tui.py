from __future__ import annotations

import gzip
import struct
from pathlib import Path
from shutil import copytree

import pytest
from textual.color import Color as TextualColor
from textual.css.query import NoMatches
from textual.containers import Horizontal, ItemGrid
from textual.widgets import Button, Label, Select, TabbedContent, TabPane, Tree
from textual_colorpicker import ColorPicker

from sprite_art.glyphs import (
    AUTHORING_GLYPHS,
    FACET_AUTHORING_GLYPHS,
    SHADED_AUTHORING_GLYPHS,
)
from sprite_art_designer.app import EdgeArtDesigner, HelpScreen, PaletteColorScreen, _new_sprite
from sprite_art_designer.widgets import (
    ArtCanvas,
    ColorSetSelector,
    GlyphPalette,
    PaletteColorGroup,
    PaletteColorSwatch,
    PreviewMatrix,
)

ROOT = Path(__file__).parents[1]


@pytest.mark.asyncio
async def test_app_mounts_wide_and_populates_editor() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        assert len(app.editor.sprites) == 12
        assert app.query_one("#nav-pane").display
        assert app.query_one("#canvas-pane").display
        assert app.query_one("#tools-pane").display
        assert app.query_one("#preview-pane").display
        assert app.query_one("#preview-matrix").render() is not None
        tree = app.query_one("#structure-tree")
        assert tree.cursor_node is not None
        assert tree.cursor_node.data.item is app.selection.item
        preview = app.query_one("#preview-pane")
        canvas = app.query_one("#canvas-pane")
        structure = app.query_one("#nav-pane")
        assert preview.region.x < canvas.region.x
        assert preview.region.y == canvas.region.y
        assert preview.region.y > structure.region.y
        art_canvas = app.query_one("#art-canvas")
        previous = app.query_one("#previous-structure")
        assert previous.region.y * 2 + previous.region.height == (
            art_canvas.region.y * 2 + art_canvas.region.height
        )
        top_row = app.query_one("#structure-tools")
        bottom_row = app.query_one("#preview-canvas")
        app._set_workspace_top_height(top_row.region.height - 4)
        await pilot.pause()
        assert top_row.region.height < bottom_row.region.height


@pytest.mark.asyncio
async def test_glyph_tab_separates_shaded_and_facet_glyphs() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        shaded = app.query_one("#shaded-glyph-palette", GlyphPalette)
        facet = app.query_one("#facet-glyph-palette", GlyphPalette)
        assert app.query_one("#shaded-glyph-title", Label).content == "Shaded glyphs"
        assert app.query_one("#facet-glyph-title", Label).content == "Facet glyphs"
        assert shaded.glyphs == SHADED_AUTHORING_GLYPHS
        assert facet.glyphs == FACET_AUTHORING_GLYPHS
        assert set(shaded.glyphs).isdisjoint(facet.glyphs)
        assert set(shaded.glyphs) | set(facet.glyphs) == set(AUTHORING_GLYPHS)
        assert app.query_one("#glyph-1", Button).parent is shaded
        facet_index = AUTHORING_GLYPHS.index(FACET_AUTHORING_GLYPHS[0])
        assert app.query_one(f"#glyph-{facet_index}", Button).parent is facet


@pytest.mark.asyncio
async def test_palette_is_second_tool_tab_and_displays_color_swatches() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tabs = app.query_one("#tool-tabs", TabbedContent)
        assert [pane.id for pane in tabs.query(TabPane)][:2] == [
            "glyph-tab",
            "palette-tab",
        ]
        tabs.active = "palette-tab"
        await pilot.pause()
        swatch = app.query_one("#palette-color-surface-0", PaletteColorSwatch)
        assert str(swatch.label) == "█"
        assert swatch.tooltip == "Edit surface color for █: grey85"
        assert swatch.styles.background is not None
        assert isinstance(swatch.parent, Horizontal)
        assert isinstance(swatch.parent.parent, PaletteColorGroup)
        assert isinstance(swatch.parent.parent.parent, ItemGrid)
        assert swatch.parent.parent.region.height == 4
        assert swatch.region.height == 3
        engine = app.query_one("#palette-color-engine-0", PaletteColorSwatch)
        assert isinstance(engine.parent, Horizontal)
        labels = app.query(".palette-group-label").results(Label)
        assert [label.content for label in labels] == [
            "Surface",
            "Engine",
            "Beacon",
            "Window",
            "Weapons",
            "Defensive",
        ]
        assert len(list(app.query(PaletteColorGroup))) == 6
        assert not app.query_one("#palette-color-beacon-2", PaletteColorSwatch).display
        assert app.query_one("#palette-add-beacon", Button).display
        assert not app.query_one("#palette-add-surface", Button).display


@pytest.mark.asyncio
async def test_palette_swatch_opens_color_picker_and_updates_palette() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#tool-tabs", TabbedContent).active = "palette-tab"
        await pilot.pause()
        assert await pilot.click("#palette-color-surface-0")
        await pilot.pause()
        assert isinstance(app.screen, PaletteColorScreen)
        picker = app.screen.query_one("#palette-color-picker", ColorPicker)
        picker.color = TextualColor.parse("#123456")
        assert await pilot.click("#confirm")
        await pilot.pause()
        assert (
            app.editor.palettes.archetypes[app.current_archetype]
            .color_set("surface")
            .colors[0]
            == "#123456"
        )
        assert app.editor.palettes_dirty
        swatch = app.query_one("#palette-color-surface-0", PaletteColorSwatch)
        assert swatch.color_value == "#123456"


@pytest.mark.asyncio
async def test_palette_color_picker_removes_selected_color_and_supports_undo() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#tool-tabs", TabbedContent).active = "palette-tab"
        await pilot.pause()
        colors = (
            app.editor.palettes.archetypes[app.current_archetype]
            .color_set("beacon")
            .colors
        )
        original = list(colors)

        assert await pilot.click("#palette-color-beacon-0")
        await pilot.pause()
        remove = app.screen.query_one("#remove", Button)
        assert not remove.disabled
        assert await pilot.click("#remove")
        await pilot.pause()

        assert colors == original[1:]
        assert app.editor.palettes_dirty
        assert app.query_one("#palette-color-beacon-0", PaletteColorSwatch).color_value == (
            original[1]
        )
        assert not app.query_one("#palette-color-beacon-1", PaletteColorSwatch).display

        app.action_undo()
        restored = (
            app.editor.palettes.archetypes[app.current_archetype]
            .color_set("beacon")
            .colors
        )
        assert restored == original


@pytest.mark.asyncio
async def test_palette_color_picker_disables_remove_for_only_color() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#tool-tabs", TabbedContent).active = "palette-tab"
        await pilot.pause()
        colors = (
            app.editor.palettes.archetypes[app.current_archetype]
            .color_set("beacon")
            .colors
        )
        colors[:] = colors[:1]
        app._refresh_palette_fields()

        assert await pilot.click("#palette-color-beacon-0")
        await pilot.pause()
        remove = app.screen.query_one("#remove", Button)
        assert remove.disabled


@pytest.mark.asyncio
async def test_palette_add_button_appends_colors_up_to_four() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#tool-tabs", TabbedContent).active = "palette-tab"
        await pilot.pause()
        def beacon_colors() -> list[str]:
            return (
                app.editor.palettes.archetypes[app.current_archetype]
                .color_set("beacon")
                .colors
            )

        assert len(beacon_colors()) == 2
        assert await pilot.click("#palette-add-beacon")
        await pilot.pause()
        assert len(beacon_colors()) == 3
        app._add_palette_color("beacon")
        await pilot.pause()
        assert len(beacon_colors()) == 4
        assert not app.query_one("#palette-add-beacon", Button).display
        app._add_palette_color("beacon")
        assert len(beacon_colors()) == 4


@pytest.mark.asyncio
async def test_color_set_selector_defaults_to_surface() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        selector = app.query_one("#color-set-selector", ColorSetSelector)
        assert app.selected_color_set_id == "surface"
        assert selector.query_one("#color-set-surface", Button).variant == "primary"


@pytest.mark.asyncio
async def test_preview_structure_selection_activates_clicked_variant() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        preview = app.query_one("#preview-matrix", PreviewMatrix)
        app.on_preview_matrix_structure_selected(
            PreviewMatrix.StructureSelected(preview, 10, 3)
        )
        await pilot.pause()
        assert app.selection is not None
        assert app.selection.kind == "variant"


@pytest.mark.asyncio
async def test_narrow_layout_uses_switchable_panels() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(80, 32)) as pilot:
        await pilot.pause()
        assert app._narrow
        assert app.query_one("#canvas-pane").display
        assert not app.query_one("#preview-pane").display
        await pilot.click("#panel-nav")
        await pilot.pause()
        assert app.query_one("#nav-pane").region.width == 80
        await pilot.click("#panel-preview")
        await pilot.pause()
        preview = app.query_one("#preview-pane")
        assert preview.display
        assert preview.region.width == 80
        assert app.query_one("#preview-matrix").region.width > 0


@pytest.mark.asyncio
async def test_preview_size_select_only_offers_tiers() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        size_select = app.query_one("#preview-size")
        assert all(value != "custom" for _, value in size_select._options)
        with pytest.raises(NoMatches):
            app.query_one("#preview-custom-size")


@pytest.mark.asyncio
async def test_tier_selection_updates_preview_tier_selector() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#structure-tree", Tree)
        full_tier = tree.root.children[0].children[0]
        tree.select_node(full_tier)
        await pilot.pause()
        assert app.preview_size[1] == full_tier.data.item.cross_axis_size("horizontal")
        assert app.query_one("#preview-size").value == full_tier.data.item.id


@pytest.mark.asyncio
async def test_preview_tier_selector_selects_the_matching_tier() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tier_select = app.query_one("#preview-size", Select)
        tier_select.value = "medium"
        await pilot.pause()
        assert app.selection is not None
        assert app.selection.kind == "tier"
        assert app.selection.item.id == "medium"
        assert tier_select.value == "medium"


@pytest.mark.asyncio
async def test_t_shortcut_cycles_ship_tiers() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#structure-tree", Tree)
        await pilot.press("t")
        assert app.selection is not None
        assert app.selection.kind == "variant"
        medium_tier = tree.root.children[0].children[1]
        first_variant = medium_tier.children[0].children[0]
        assert app.selection.item is first_variant.data.item
        assert tree.cursor_node is first_variant
        assert medium_tier.is_expanded
        assert app.query_one("#art-canvas", ArtCanvas).variant is app.selection.item
        assert app.query_one("#preview-size", Select).value == "medium"


@pytest.mark.asyncio
async def test_o_shortcut_switches_orientation_and_loads_matching_variant() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        source = app.query_one("#art-canvas", ArtCanvas).variant
        assert source is not None
        await pilot.press("o")
        assert app.current_view_id == "vertical"
        assert app.selection is not None
        assert app.selection.kind == "variant"
        assert app.selection.item.id == source.id
        assert app.query_one("#art-canvas", ArtCanvas).variant is app.selection.item


@pytest.mark.asyncio
async def test_question_mark_opens_help_modal() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.press("question_mark")
        assert isinstance(app.screen, HelpScreen)
        await pilot.press("escape")
        assert not isinstance(app.screen, HelpScreen)


@pytest.mark.asyncio
async def test_h_shortcut_toggles_preview_highlight() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.press("h")
        assert app.highlight_preview
        await pilot.press("h")
        assert not app.highlight_preview


@pytest.mark.asyncio
async def test_preview_navigation_buttons_and_shortcuts_skip_inactive_variants() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#structure-tree", Tree)
        sections = tree.root.children[0].children[0].children
        active_variants = app._preview_variants()
        first_active = active_variants[id(sections[0].data.item.variants)]
        second_active = active_variants[id(sections[1].data.item.variants)]
        third_active = active_variants[id(sections[2].data.item.variants)]

        assert app.selection is not None
        assert app.selection.item is first_active
        await pilot.click("#next-structure")
        assert app.selection is not None
        assert app.selection.kind == "variant"
        assert app.selection.item is second_active
        await pilot.press("comma")
        assert app.selection.item is first_active
        await pilot.press("full_stop")
        assert app.selection.item is second_active
        await pilot.press("full_stop")
        assert app.selection.item is third_active


@pytest.mark.asyncio
async def test_rexpaint_export_uses_current_preview_configuration(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    copytree(ROOT / "assets", asset_root)
    app = EdgeArtDesigner(asset_root, data_root=tmp_path / ".edge-art-designer")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.preview_size = (18, 3)
        app.preview_seed = 42
        sprite_id = app.editor.current_sprite.id
        app.action_export_rexpaint()

    output = (
        tmp_path
        / ".edge-art-designer"
        / "exports"
        / f"{sprite_id}-horizontal-right-18x3-seed42.xp"
    )
    assert output.exists()
    assert struct.unpack_from("<iiii", gzip.decompress(output.read_bytes())) == (
        -1,
        1,
        18,
        3,
    )


@pytest.mark.asyncio
async def test_rexpaint_import_updates_current_structure_without_new_view(tmp_path: Path) -> None:
    asset_root = tmp_path / "assets"
    copytree(ROOT / "assets", asset_root)
    app = EdgeArtDesigner(asset_root, data_root=tmp_path / ".edge-art-designer")
    async with app.run_test(size=(80, 32)) as pilot:
        await pilot.pause()
        current_view_id = app.current_view_id
        view_count = len(app.editor.current_sprite.views)
        app.action_export_rexpaint()
        export_path = next(app.editor.export_root.glob("*.xp"))
        app._finish_import_rexpaint(export_path)
        await pilot.pause()
        assert app.current_view_id == current_view_id
        assert len(app.editor.current_sprite.views) == view_count
        assert isinstance(app.query_one("#document-actions"), Select)


@pytest.mark.asyncio
async def test_v_shortcut_cycles_variant_and_overrides_preview_selection() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        first = app.selection.item
        await pilot.press("v")
        assert app.selection is not None
        assert app.selection.kind == "variant"
        assert app.selection.item is not first
        assert isinstance(app.selection.parent, list)
        overrides = app.query_one("#preview-matrix", PreviewMatrix).variant_overrides
        assert overrides is not None
        assert overrides[id(app.selection.parent)] is app.selection.item


@pytest.mark.asyncio
async def test_explicit_variant_selection_persists_after_browsing_away() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#structure-tree", Tree)
        section = tree.root.children[0].children[0].children[0]
        first_variant, selected_variant = section.children[:2]
        tree.select_node(selected_variant)
        await pilot.pause()
        assert selected_variant.label.style == "#d9e3ea"
        assert first_variant.label.style == "dim #718096"

        tree.select_node(section)
        await pilot.pause()
        overrides = app.query_one("#preview-matrix", PreviewMatrix).variant_overrides
        assert overrides is not None
        assert overrides[id(section.data.item.variants)] is selected_variant.data.item

        tree.select_node(first_variant)
        await pilot.pause()
        await pilot.press("full_stop")
        tree.select_node(section)
        await pilot.pause()
        overrides = app.query_one("#preview-matrix", PreviewMatrix).variant_overrides
        assert overrides is not None
        assert overrides[id(section.data.item.variants)] is first_variant.data.item


@pytest.mark.asyncio
async def test_preview_tab_can_reset_seed() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#tool-tabs", TabbedContent).active = "preview-tab"
        await pilot.pause()
        app.preview_seed = 123
        app.query_one("#preview-seed").value = "123"
        app._reset_preview_seed()
        assert app.preview_seed == 7
        assert app.query_one("#preview-seed").value == "7"


@pytest.mark.asyncio
async def test_structure_selection_switches_preview_to_its_view() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#structure-tree")
        vertical_view = next(
            node for node in tree.root.children if node.data.item.id == "vertical"
        )
        tree.select_node(vertical_view.children[0].children[0].children[0])
        await pilot.pause()
        assert app.current_view_id == "vertical"
        assert app.query_one("#preview-view").value == "vertical"


def test_preview_dimensions_account_for_terminal_aspect() -> None:
    assert PreviewMatrix.dimensions_for_view("horizontal", 56, 12) == (56, 12)
    assert PreviewMatrix.dimensions_for_view("vertical", 56, 12) == (24, 28)


def test_new_generic_sprite_uses_fixed_canvas_model() -> None:
    sprite = _new_sprite("test_icon", "Test Icon", "generic")
    assert sprite.kind == "generic"
    assert sprite.views["default"].axis == "fixed"
    assert sprite.views["default"].tiers[0].sections[0].variants[0].cells


def test_new_ship_sprite_has_full_medium_and_compact_tiers() -> None:
    sprite = _new_sprite("test_ship", "Test Ship", "ship")
    tiers = sprite.views["horizontal"].tiers
    assert [tier.id for tier in tiers] == ["full", "medium", "compact"]
    assert [tier.cross_axis_size("horizontal") for tier in tiers] == [7, 5, 3]


@pytest.mark.asyncio
async def test_mouse_paint_marks_dirty_and_writes_recovery(
    tmp_path: Path,
) -> None:
    asset_root = tmp_path / "assets"
    copytree(ROOT / "assets", asset_root)
    app = EdgeArtDesigner(asset_root, data_root=tmp_path / ".edge-art-designer")
    async with app.run_test(size=(120, 42)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        original = canvas.variant.cells[0][0]
        canvas.set_glyph("◆" if original != "◆" else "█")
        app._select_color_set("window")
        content_offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=content_offset)
        await pilot.pause(0.6)
        assert app.editor.current_sprite_id in app.editor.dirty_sprites
        assert app.editor.recovery_path(app.editor.current_sprite_id).exists()
        assert canvas.variant.color_mask[0][0] == "W"


@pytest.mark.asyncio
async def test_middle_click_picks_and_highlights_canvas_glyph() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        canvas.variant.cells[0] = "█" + canvas.variant.cells[0][1:]
        glyph = canvas.variant.cells[0][0]
        color_set_id = "engine"
        canvas.variant.color_mask[0] = "E" + canvas.variant.color_mask[0][1:]
        offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=offset, button=2)
        await pilot.pause()
        assert app.selected_glyph == glyph
        assert app.selected_color_set_id == color_set_id
        glyph_index = next(
            index
            for index, (candidate, _description) in enumerate(AUTHORING_GLYPHS)
            if candidate == glyph
        )
        assert app.query_one(f"#glyph-{glyph_index}").variant == "primary"


@pytest.mark.asyncio
async def test_undo_and_redo_restore_canvas_edits() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        original = canvas.variant.cells[0][0]
        canvas.set_glyph("◆" if original != "◆" else "█")
        offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=offset)
        changed = app.query_one("#art-canvas", ArtCanvas).variant
        assert changed is not None
        assert changed.cells[0][0] != original

        await pilot.press("ctrl+z")
        restored = app.query_one("#art-canvas", ArtCanvas).variant
        assert restored is not None
        assert restored.cells[0][0] == original

        await pilot.press("ctrl+y")
        redone = app.query_one("#art-canvas", ArtCanvas).variant
        assert redone is not None
        assert redone.cells[0][0] != original
