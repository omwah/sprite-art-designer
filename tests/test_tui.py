from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest
from textual.widgets import TabbedContent, Tree

from sprite_art.glyphs import AUTHORING_GLYPHS
from sprite_art_designer.app import EdgeArtDesigner, HelpScreen, _new_sprite
from sprite_art_designer.widgets import ArtCanvas, PreviewMatrix

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
async def test_preview_size_select_supports_custom_size() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        size_select = app.query_one("#preview-size")
        size_select.value = "custom"
        await pilot.pause()
        custom_size = app.query_one("#preview-custom-size")
        assert custom_size.display
        custom_size.value = "24x6"
        app._apply_preview_configuration()
        assert app.preview_size == (24, 6)
        assert app.query_one("#preview-matrix", PreviewMatrix).preview_size == (24, 6)


@pytest.mark.asyncio
async def test_preview_size_and_structure_tier_stay_in_sync() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#preview-size").value = "18x3"
        await pilot.pause()
        assert app.selection is not None
        assert app.selection.kind == "tier"
        assert app.selection.item.id == "compact"

        tree = app.query_one("#structure-tree", Tree)
        full_tier = tree.root.children[0].children[0]
        tree.select_node(full_tier)
        await pilot.pause()
        assert app.preview_size == (40, 7)

        compact_variant = tree.root.children[0].children[2].children[0].children[0]
        tree.select_node(compact_variant)
        await pilot.pause()
        assert app.query_one("#preview-size").value == "18x3"


@pytest.mark.asyncio
async def test_changing_ships_keeps_the_selected_preview_size() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        app.query_one("#preview-size").value = "30x5"
        await pilot.pause()
        sprite_select = app.query_one("#sprite-select")
        sprite_select.value = next(
            value for _, value in app._sprite_options() if value != app.editor.current_sprite_id
        )
        await pilot.pause()
        assert app.preview_size == (30, 5)
        assert app.query_one("#preview-size").value == "30x5"


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
    app = EdgeArtDesigner(asset_root)
    async with app.run_test(size=(120, 42)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        original = canvas.variant.cells[0][0]
        canvas.set_glyph("◆" if original != "◆" else "█")
        content_offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=content_offset)
        await pilot.pause(0.6)
        assert app.editor.current_sprite_id in app.editor.dirty_sprites
        assert app.editor.recovery_path(app.editor.current_sprite_id).exists()


@pytest.mark.asyncio
async def test_middle_click_picks_and_highlights_canvas_glyph() -> None:
    app = EdgeArtDesigner(ROOT / "assets")
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        canvas = app.query_one("#art-canvas", ArtCanvas)
        assert canvas.variant is not None
        glyph = canvas.variant.cells[0][0]
        offset = (
            canvas.content_region.x - canvas.region.x,
            canvas.content_region.y - canvas.region.y,
        )
        assert await pilot.click("#art-canvas", offset=offset, button=2)
        await pilot.pause()
        assert app.selected_glyph == glyph
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
