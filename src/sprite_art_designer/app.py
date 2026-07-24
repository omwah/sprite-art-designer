"""Resizable Textual application for procedural sprite-art authoring."""

from __future__ import annotations

import argparse
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from rich.color import Color
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Switch,
    Tree,
)
from textual.widgets.tree import TreeNode

from sprite_art import (
    PROPERTY_IDS,
    Palette,
    Section,
    Sprite,
    Tier,
    Variant,
    View,
    generate_rotated_view,
)
from sprite_art.model import SCHEMA_VERSION

from .state import EditorState
from .widgets import (
    ArtCanvas,
    CanvasPane,
    DocumentBar,
    GlyphPalette,
    NarrowTabs,
    NavPane,
    PreviewMatrix,
    PreviewPane,
    ToolsPane,
)

SelectionKind = Literal["sprite", "view", "tier", "section", "variant"]


@dataclass
class Selection:
    kind: SelectionKind
    item: Sprite | View | Tier | Section | Variant
    parent: list[Any] | dict[str, View] | None = None


class ConfirmScreen(ModalScreen[bool]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self.message, id="dialog-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Continue", id="confirm", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class HelpScreen(ModalScreen[None]):
    """Scroll-friendly editor help, adapted from Edge's contextual help screen."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("question_mark", "close", "Close"),
    ]

    CSS = """
    HelpScreen { align: center middle; background: #0009; }
    HelpScreen #help-box {
        width: 72; max-width: 100%; max-height: 90%; height: auto;
        padding: 1 2; border: round #38bdf8; background: #10212c;
    }
    HelpScreen #help-title { text-style: bold; color: #7dd3fc; margin-bottom: 1; }
    HelpScreen .help-section { text-style: bold; color: #7dd3fc; margin-top: 1; }
    HelpScreen #help-footer { color: #78909c; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-box"):
            yield Static("Help — Edge Art Designer", id="help-title")
            yield Static("Canvas", classes="help-section")
            yield Static(
                "Left-drag paints · right-drag erases · arrows move · Space paints\n"
                "Enter also paints · Delete or Backspace erases"
            )
            yield Static("Shortcuts", classes="help-section")
            yield Static(
                "  Ctrl+S  Save current sprite\n"
                "  Ctrl+Shift+S  Save all modified assets\n"
                "  Ctrl+N  Create a sprite\n"
                "  Ctrl+R  Restore recovery snapshot\n"
                "  Ctrl+G  Generate vertical view\n"
                "  Ctrl+D  Duplicate selection\n"
                "  Delete  Delete selection\n"
                "  , / .  Previous / next structure\n"
                "  ?  Open or close this help"
            )
            yield Static("[dim]Esc or ? to close[/]", id="help-footer")

    def action_close(self) -> None:
        self.dismiss(None)


class NewSpriteScreen(ModalScreen[tuple[str, str, str] | None]):
    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Create sprite", classes="dialog-title")
            yield Label("Role / sprite ID")
            yield Input(placeholder="new_role", id="new-id")
            yield Label("Display name")
            yield Input(placeholder="New Role", id="new-name")
            yield Label("Asset type")
            yield Select(
                [("Ship composition", "ship"), ("Fixed canvas", "generic")],
                value="ship",
                allow_blank=False,
                id="new-kind",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        sprite_id = self.query_one("#new-id", Input).value.strip().lower()
        name = self.query_one("#new-name", Input).value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", sprite_id):
            self.notify(
                "ID must start with a letter and use lowercase letters, digits, or underscores.",
                severity="error",
            )
            return
        kind = str(self.query_one("#new-kind", Select).value)
        self.dismiss((sprite_id, name or sprite_id.replace("_", " ").title(), kind))


def _unique_id(existing: set[str], base: str) -> str:
    if base not in existing:
        return base
    suffix = 2
    while f"{base}_{suffix}" in existing:
        suffix += 1
    return f"{base}_{suffix}"


def _blank_variant(variant_id: str, width: int, height: int) -> Variant:
    return Variant(id=variant_id, cells=[" " * width for _ in range(height)])


def _default_section(
    section_id: str = "section",
    *,
    width: int = 6,
    height: int = 3,
) -> Section:
    return Section(
        id=section_id,
        name=section_id.replace("_", " ").title(),
        primary_property="utility",
        variants=[_blank_variant("variant_1", width, height)],
    )


def _new_sprite(sprite_id: str, name: str, kind: str) -> Sprite:
    if kind == "ship":
        sprite = Sprite(
            schema_version=SCHEMA_VERSION,
            id=sprite_id,
            name=name,
            kind="ship",
            role=sprite_id,
            description="",
            views={
                "horizontal": View(
                    id="horizontal",
                    name="Horizontal",
                    axis="horizontal",
                    canonical_facing="right",
                    mirror_facing="left",
                    tiers=[
                        Tier(
                            id="full",
                            name="Full Detail",
                            sections=[
                                Section(
                                    id="hull",
                                    name="Hull",
                                    primary_property="hull",
                                    variants=[_blank_variant("hull_1", 8, 3)],
                                )
                            ],
                        )
                    ],
                )
            },
        )
        vertical, _warnings = generate_rotated_view(sprite)
        sprite.views["vertical"] = vertical
    else:
        sprite = Sprite(
            schema_version=SCHEMA_VERSION,
            id=sprite_id,
            name=name,
            kind="generic",
            role=sprite_id,
            description="",
            views={
                "default": View(
                    id="default",
                    name="Default",
                    axis="fixed",
                    canonical_facing="default",
                    mirror_facing=None,
                    tiers=[
                        Tier(
                            id="full",
                            name="Full Detail",
                            sections=[_default_section("canvas", width=12, height=6)],
                        )
                    ],
                )
            },
        )
    sprite.validate()
    return sprite


class EdgeArtDesigner(App[None]):
    CSS_PATH = "styles.tcss"
    TITLE = "Edge Art Designer"

    BINDINGS = [
        ("ctrl+s", "save", "Save"),
        ("ctrl+shift+s", "save_all", "Save all"),
        ("ctrl+n", "new_sprite", "New sprite"),
        ("ctrl+r", "restore_recovery", "Restore recovery"),
        ("ctrl+g", "rotate_vertical", "Generate vertical"),
        ("ctrl+d", "duplicate_item", "Duplicate"),
        ("delete", "delete_item", "Delete"),
        ("h", "toggle_highlight", "Toggle highlight"),
        ("comma", "previous_structure", "Previous structure"),
        ("full_stop", "next_structure", "Next structure"),
        ("question_mark", "help", "Help"),
    ]

    def __init__(self, asset_root: Path) -> None:
        super().__init__()
        self.editor = EditorState.load(asset_root)
        self.selection: Selection | None = None
        self.selected_glyph = "█"
        self.preview_size = (56, 12)
        self.highlight_preview = False
        self.preview_seed = 7
        self.current_archetype = "humanoid_diplomat"
        self.current_view_id = "horizontal"
        self.current_facing: str | None = None
        self._recovery_timer: Timer | None = None
        self._narrow = False
        self._narrow_panel = "canvas"

    def compose(self) -> ComposeResult:
        initial_sprite = self.editor.current_sprite
        initial_view_id = (
            self.current_view_id
            if self.current_view_id in initial_sprite.views
            else next(iter(initial_sprite.views))
        )
        initial_view = initial_sprite.views[initial_view_id]
        initial_facings = [
            (initial_view.canonical_facing.title(), initial_view.canonical_facing)
        ]
        if initial_view.mirror_facing is not None:
            initial_facings.append(
                (initial_view.mirror_facing.title(), initial_view.mirror_facing)
            )
        yield Header(show_clock=True)
        yield DocumentBar(self._sprite_options(), self.editor.current_sprite_id)
        yield NarrowTabs()

        with Container(id="body"):
            with Vertical(id="workspace"):
                with Horizontal(id="structure-tools"):
                    yield NavPane()
                    yield ToolsPane(
                        self.current_archetype,
                        [
                            (view.name, view_id)
                            for view_id, view in initial_sprite.views.items()
                        ],
                        initial_view_id,
                        initial_facings,
                        self.preview_seed,
                        self.preview_size,
                        self.highlight_preview,
                    )
                with Horizontal(id="preview-canvas"):
                    yield PreviewPane()
                    yield CanvasPane()
        yield Footer()

    def _sprite_options(self) -> list[tuple[str, str]]:
        return [
            (self.editor.sprites[sprite_id].name, sprite_id)
            for sprite_id in sorted(self.editor.sprites)
        ]

    def on_mount(self) -> None:
        self._rebuild_tree()
        self.call_after_refresh(self._sync_tree_cursor_to_selection)
        self._refresh_palette_fields()
        self._refresh_preview_controls()
        self._refresh_preview()
        self._update_dirty_indicator()
        if self.editor.has_newer_recovery():
            self.notify(
                "A newer recovery snapshot exists. Press Ctrl+R to restore it.",
                severity="warning",
                timeout=8,
            )

    def _sync_tree_cursor_to_selection(self) -> None:
        if self.selection is None:
            return
        selected_item = self.selection.item
        tree = self.query_one("#structure-tree", Tree)

        def find(node: TreeNode[Any]) -> TreeNode[Any] | None:
            if isinstance(node.data, Selection) and node.data.item is selected_item:
                return node
            for child in node.children:
                result = find(child)
                if result is not None:
                    return result
            return None

        tree.move_cursor(find(tree.root))

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def on_resize(self, event: events.Resize) -> None:
        narrow = event.size.width < 100
        if narrow == self._narrow:
            return
        self._narrow = narrow
        self.screen.set_class(narrow, "narrow")
        self._apply_responsive_panels()

    def _apply_responsive_panels(self) -> None:
        panel_ids = ("nav", "canvas", "tools", "preview")
        workspace = self.query_one("#workspace")
        if not self._narrow:
            workspace.display = True
            self.query_one("#structure-tools").display = True
            self.query_one("#preview-canvas").display = True
            for panel_id in panel_ids:
                self.query_one(f"#{panel_id}-pane").display = True
            return
        workspace.display = True
        self.query_one("#structure-tools").display = self._narrow_panel in {
            "nav",
            "tools",
        }
        self.query_one("#preview-canvas").display = self._narrow_panel in {
            "canvas",
            "preview",
        }
        for panel_id in ("nav", "canvas", "tools"):
            self.query_one(f"#{panel_id}-pane").display = panel_id == self._narrow_panel
        self.query_one("#preview-pane").display = self._narrow_panel == "preview"

    def _show_narrow_panel(self, panel: str) -> None:
        self._narrow_panel = panel
        for name in ("nav", "canvas", "tools", "preview"):
            button = self.query_one(f"#panel-{name}", Button)
            button.variant = "primary" if name == panel else "default"
        self._apply_responsive_panels()

    def _rebuild_tree(self, select_item: object | None = None) -> None:
        tree = self.query_one("#structure-tree", Tree)
        sprite = self.editor.current_sprite
        tree.reset(sprite.name, Selection("sprite", sprite))
        selected_node: TreeNode[Any] | None = None
        for view in sprite.views.values():
            view_node = tree.root.add(
                f"{view.name} [{view.axis}]",
                Selection("view", view, sprite.views),
                expand=True,
            )
            if select_item is view:
                selected_node = view_node
            for tier in view.tiers:
                tier_node = view_node.add(
                    tier.name,
                    Selection("tier", tier, view.tiers),
                    expand=True,
                )
                if select_item is tier:
                    selected_node = tier_node
                for section in tier.sections:
                    section_node = tier_node.add(
                        f"{section.name} · {section.primary_property}",
                        Selection("section", section, tier.sections),
                        expand=True,
                    )
                    if select_item is section:
                        selected_node = section_node
                    for variant in section.variants:
                        variant_node = section_node.add_leaf(
                            f"{variant.id} · {variant.width}×{variant.height} · w{variant.weight}",
                            Selection("variant", variant, section.variants),
                        )
                        if select_item is variant:
                            selected_node = variant_node
        tree.root.expand_all()
        if selected_node is not None:
            tree.select_node(selected_node)
        elif tree.root.children:
            first_view = tree.root.children[0]
            if first_view.children and first_view.children[0].children:
                first_section = first_view.children[0].children[0]
                if first_section.children:
                    tree.select_node(first_section.children[0])

    def on_tree_node_selected(self, event: Tree.NodeSelected[Selection]) -> None:
        selection = event.node.data
        if not isinstance(selection, Selection):
            return
        self.selection = selection
        selected_view = self._view_for_structure(selection.item)
        if selected_view is not None and self.current_view_id != selected_view.id:
            self.current_view_id = selected_view.id
            self._refresh_preview_controls()
        self._populate_inspector()
        canvas = self.query_one("#art-canvas", ArtCanvas)
        if selection.kind == "variant":
            variant = selection.item
            assert isinstance(variant, Variant)
            canvas.set_variant(variant)
            self.query_one("#canvas-title", Label).update(
                f"{variant.id}"
            )
        else:
            canvas.set_variant(None)
        self._refresh_preview()

    def _view_for_structure(
        self,
        item: Sprite | View | Tier | Section | Variant,
    ) -> View | None:
        if isinstance(item, View):
            return item
        for view in self.editor.current_sprite.views.values():
            if any(tier is item for tier in view.tiers):
                return view
            for tier in view.tiers:
                if any(section is item for section in tier.sections):
                    return view
                if any(
                    variant is item
                    for section in tier.sections
                    for variant in section.variants
                ):
                    return view
        return None

    def _populate_inspector(self) -> None:
        if self.selection is None:
            return
        item = self.selection.item
        kind = self.selection.kind
        self.query_one("#selection-title", Label).update(kind.title())
        item_id = getattr(item, "id", "")
        name = getattr(item, "name", "")
        id_input = self.query_one("#item-id", Input)
        id_input.value = str(item_id)
        id_input.disabled = kind == "sprite"
        name_input = self.query_one("#item-name", Input)
        name_input.value = str(name)
        name_input.disabled = kind == "variant"
        section_fields = self.query_one("#section-fields")
        variant_fields = self.query_one("#variant-fields")
        section_fields.display = kind == "section"
        variant_fields.display = kind == "variant"
        if kind == "section":
            section_item = item
            assert isinstance(section_item, Section)
            self.query_one("#primary-property", Select).value = section_item.primary_property
            self.query_one("#secondary-properties", Input).value = ", ".join(
                section_item.secondary_properties
            )
            self.query_one("#repeat-min", Input).value = str(section_item.min_repeat)
            self.query_one("#repeat-max", Input).value = str(section_item.max_repeat)
        elif kind == "variant":
            variant_item = item
            assert isinstance(variant_item, Variant)
            self.query_one("#variant-weight", Input).value = str(variant_item.weight)
            self.query_one("#variant-width", Input).value = str(variant_item.width)
            self.query_one("#variant-height", Input).value = str(variant_item.height)

    def _mark_changed(self) -> None:
        self.editor.mark_sprite_dirty()
        self._update_dirty_indicator()
        self._refresh_preview()
        if self._recovery_timer is not None:
            self._recovery_timer.stop()
        self._recovery_timer = self.set_timer(0.4, self._write_recovery)

    def _write_recovery(self) -> None:
        self._recovery_timer = None
        try:
            self.editor.write_recovery()
        except Exception as error:
            self.notify(f"Recovery snapshot failed: {error}", severity="error")

    def _update_dirty_indicator(self) -> None:
        sprite_dirty = self.editor.current_sprite_id in self.editor.dirty_sprites
        palette_dirty = self.editor.palettes_dirty
        labels = []
        if sprite_dirty:
            labels.append("sprite modified")
        if palette_dirty:
            labels.append("palettes modified")
        self.query_one("#dirty-indicator", Label).update(
            "● " + ", ".join(labels) if labels else "Saved"
        )
        self.sub_title = (
            f"{self.editor.current_sprite.name}"
            + (" *" if labels else "")
        )

    def on_art_canvas_changed(self, event: ArtCanvas.Changed) -> None:
        self._mark_changed()

    def on_glyph_palette_selected(self, event: GlyphPalette.Selected) -> None:
        self.selected_glyph = event.glyph
        self.query_one("#art-canvas", ArtCanvas).set_glyph(event.glyph)
        shown = "space" if event.glyph == " " else event.glyph
        self.query_one("#selected-glyph", Label).update(f"Selected: {shown}")

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "preview-highlight":
            self.highlight_preview = event.value
            self._refresh_preview()

    def action_toggle_highlight(self) -> None:
        self.highlight_preview = not self.highlight_preview
        self.query_one("#preview-highlight", Switch).value = self.highlight_preview
        self._refresh_preview()

    def action_previous_structure(self) -> None:
        self._select_adjacent_structure(-1)

    def action_next_structure(self) -> None:
        self._select_adjacent_structure(1)

    def _select_adjacent_structure(self, delta: int) -> None:
        tree = self.query_one("#structure-tree", Tree)
        variants: list[TreeNode[Any]] = []

        def collect(node: TreeNode[Any]) -> None:
            if isinstance(node.data, Selection) and node.data.kind == "variant":
                variants.append(node)
            for child in node.children:
                collect(child)

        collect(tree.root)
        if not variants:
            return
        current_item = self.selection.item if self.selection is not None else None
        current_index = next(
            (
                index
                for index, node in enumerate(variants)
                if isinstance(node.data, Selection) and node.data.item is current_item
            ),
            0,
        )
        tree.select_node(variants[(current_index + delta) % len(variants)])

    def on_select_changed(self, event: Select.Changed) -> None:
        select_id = event.select.id
        if event.value is Select.BLANK:
            return
        value = str(event.value)
        if select_id == "sprite-select":
            if value == self.editor.current_sprite_id:
                return
            self.editor.current_sprite_id = value
            self.current_view_id = next(iter(self.editor.current_sprite.views))
            self._rebuild_tree()
            self._refresh_preview_controls()
            self._refresh_preview()
            self._update_dirty_indicator()
            if self.editor.has_newer_recovery():
                self.notify(
                    "This sprite has a newer recovery snapshot; Ctrl+R restores it.",
                    severity="warning",
                )
        elif select_id == "palette-archetype":
            self.current_archetype = value
            self._refresh_palette_fields()
            self._refresh_preview()
        elif select_id == "preview-view":
            if value in self.editor.current_sprite.views:
                self.current_view_id = value
                self._refresh_facing_options()
                self._refresh_preview()
        elif select_id == "preview-facing":
            self.current_facing = value
            self._refresh_preview()
        elif select_id == "preview-size":
            custom_size = self.query_one("#preview-custom-size", Input)
            custom_size.display = value == "custom"
            if value != "custom":
                self.preview_size = self._parse_preview_size(value)
                self._refresh_preview()

    def _refresh_preview_controls(self) -> None:
        view_select = self.query_one("#preview-view", Select)
        sprite = self.editor.current_sprite
        view_select.set_options(
            [(view.name, view_id) for view_id, view in sprite.views.items()]
        )
        if self.current_view_id not in sprite.views:
            self.current_view_id = next(iter(sprite.views))
        view_select.value = self.current_view_id
        self._refresh_facing_options()

    def _refresh_facing_options(self) -> None:
        view = self.editor.current_sprite.views[self.current_view_id]
        options = [(view.canonical_facing.title(), view.canonical_facing)]
        if view.mirror_facing is not None:
            options.append((view.mirror_facing.title(), view.mirror_facing))
        facing_select = self.query_one("#preview-facing", Select)
        facing_select.set_options(options)
        if self.current_facing not in {value for _, value in options}:
            self.current_facing = view.canonical_facing
        facing_select.value = self.current_facing

    def _refresh_preview(self) -> None:
        matrix = self.query_one("#preview-matrix", PreviewMatrix)
        matrix.configure(
            sprite=self.editor.current_sprite,
            palettes=self.editor.palettes,
            archetype_id=self.current_archetype,
            view_id=self.current_view_id,
            facing=self.current_facing,
            seed=self.preview_seed,
            size=self.preview_size,
            highlight_variant=self._selected_preview_variant(),
        )

    def _selected_preview_variant(self) -> Variant | None:
        if not self.highlight_preview or self.selection is None:
            return None
        return self.selection.item if isinstance(self.selection.item, Variant) else None

    def _refresh_palette_fields(self) -> None:
        palette = self.editor.palettes.archetypes[self.current_archetype]
        values = {
            "bright": palette.bright,
            "mid": palette.mid,
            "dark": palette.dark,
            "beacon": ", ".join(palette.beacon),
            "engine": ", ".join(palette.engine),
            "window": ", ".join(palette.window),
            "facet": palette.facet,
        }
        for field_name, value in values.items():
            self.query_one(f"#palette-{field_name}", Input).value = value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("panel-"):
            self._show_narrow_panel(button_id.removeprefix("panel-"))
        elif button_id == "new-sprite":
            self.action_new_sprite()
        elif button_id == "save":
            self.action_save()
        elif button_id == "save-all":
            self.action_save_all()
        elif button_id == "rotate-vertical":
            self.action_rotate_vertical()
        elif button_id == "apply-properties":
            self._apply_properties()
        elif button_id == "apply-palette":
            self._apply_palette()
        elif button_id == "apply-preview":
            self._apply_preview_configuration()
        elif button_id == "previous-structure":
            self.action_previous_structure()
        elif button_id == "next-structure":
            self.action_next_structure()
        elif button_id == "add-item":
            self.action_add_item()
        elif button_id == "duplicate-item":
            self.action_duplicate_item()
        elif button_id == "delete-item":
            self.action_delete_item()
        elif button_id == "move-up":
            self._move_selection(-1)
        elif button_id == "move-down":
            self._move_selection(1)

    def _apply_properties(self) -> None:
        if self.selection is None:
            return
        item = self.selection.item
        kind = self.selection.kind
        requested_id = self.query_one("#item-id", Input).value.strip()
        requested_name = self.query_one("#item-name", Input).value.strip()
        try:
            if kind != "sprite" and requested_id:
                self._rename_selected(requested_id)
            if kind != "variant" and requested_name:
                setattr(item, "name", requested_name)
            if kind == "section":
                assert isinstance(item, Section)
                primary = str(self.query_one("#primary-property", Select).value)
                secondary = [
                    value.strip()
                    for value in self.query_one("#secondary-properties", Input).value.split(",")
                    if value.strip()
                ]
                invalid = set(secondary) - set(PROPERTY_IDS)
                if invalid:
                    raise ValueError(f"Unknown secondary properties: {sorted(invalid)}")
                item.primary_property = primary
                item.secondary_properties = secondary
                item.min_repeat = int(self.query_one("#repeat-min", Input).value)
                item.max_repeat = int(self.query_one("#repeat-max", Input).value)
            elif kind == "variant":
                assert isinstance(item, Variant)
                item.weight = int(self.query_one("#variant-weight", Input).value)
                width = int(self.query_one("#variant-width", Input).value)
                height = int(self.query_one("#variant-height", Input).value)
                self._resize_variant(item, width, height)
            self.editor.current_sprite.validate()
        except Exception as error:
            self.notify(str(error), severity="error")
            self._populate_inspector()
            return
        self._rebuild_tree(select_item=item)
        if isinstance(item, Variant):
            self.query_one("#art-canvas", ArtCanvas).set_variant(item)
        self._mark_changed()

    def _rename_selected(self, requested_id: str) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", requested_id):
            raise ValueError("IDs use lowercase letters, digits, and underscores")
        assert self.selection is not None
        item = self.selection.item
        parent = self.selection.parent
        if isinstance(parent, list):
            existing = {getattr(entry, "id", "") for entry in parent if entry is not item}
            if requested_id in existing:
                raise ValueError(f"Duplicate ID {requested_id!r}")
            setattr(item, "id", requested_id)
        elif isinstance(parent, dict) and isinstance(item, View):
            if requested_id in parent and parent[requested_id] is not item:
                raise ValueError(f"Duplicate view ID {requested_id!r}")
            old_key = next(key for key, value in parent.items() if value is item)
            if old_key != requested_id:
                del parent[old_key]
                item.id = requested_id
                parent[requested_id] = item
                if self.current_view_id == old_key:
                    self.current_view_id = requested_id

    @staticmethod
    def _resize_variant(variant: Variant, width: int, height: int) -> None:
        if width < 1 or height < 1:
            raise ValueError("Canvas dimensions must be positive")
        old = variant.cells
        rows: list[str] = []
        for y in range(height):
            source = old[y] if y < len(old) else ""
            rows.append(source[:width].ljust(width))
        variant.cells = rows

    def _apply_palette(self) -> None:
        try:
            scalar = {
                field: self.query_one(f"#palette-{field}", Input).value.strip()
                for field in ("bright", "mid", "dark", "facet")
            }
            pools = {
                field: [
                    value.strip()
                    for value in self.query_one(f"#palette-{field}", Input).value.split(",")
                    if value.strip()
                ]
                for field in ("beacon", "engine", "window")
            }
            for color in [*scalar.values(), *(value for pool in pools.values() for value in pool)]:
                Color.parse(color)
            palette = Palette(
                bright=scalar["bright"],
                mid=scalar["mid"],
                dark=scalar["dark"],
                beacon=pools["beacon"],
                engine=pools["engine"],
                window=pools["window"],
                facet=scalar["facet"],
            )
            palette.validate(self.current_archetype)
        except Exception as error:
            self.notify(f"Invalid palette: {error}", severity="error")
            return
        self.editor.palettes.archetypes[self.current_archetype] = palette
        self.editor.mark_palettes_dirty()
        self._update_dirty_indicator()
        self._refresh_preview()

    def _apply_preview_configuration(self) -> None:
        try:
            seed = int(self.query_one("#preview-seed", Input).value)
            size_value = str(self.query_one("#preview-size", Select).value)
            if size_value == "custom":
                size_value = self.query_one("#preview-custom-size", Input).value
            size = self._parse_preview_size(size_value)
        except ValueError:
            self.notify("Use a size such as 18x3 or 56x12", severity="error")
            return
        self.preview_seed = seed
        self.preview_size = size
        self._refresh_preview()

    @staticmethod
    def _parse_preview_size(value: str) -> tuple[int, int]:
        width_text, height_text = value.strip().lower().split("x", 1)
        width, height = int(width_text), int(height_text)
        if width < 1 or height < 1:
            raise ValueError
        return width, height

    def action_save(self) -> None:
        try:
            self.editor.save_current()
        except Exception as error:
            self.notify(f"Save failed: {error}", severity="error")
            return
        self._update_dirty_indicator()
        self.notify(f"Saved {self.editor.current_sprite.name}")

    def action_save_all(self) -> None:
        try:
            self.editor.save_all()
        except Exception as error:
            self.notify(f"Save all failed: {error}", severity="error")
            return
        self._update_dirty_indicator()
        self.notify("Saved all modified sprites and palettes")

    def action_new_sprite(self) -> None:
        self.push_screen(NewSpriteScreen(), self._finish_new_sprite)

    def _finish_new_sprite(self, result: tuple[str, str, str] | None) -> None:
        if result is None:
            return
        sprite_id, name, kind = result
        try:
            self.editor.add_sprite(_new_sprite(sprite_id, name, kind))
        except Exception as error:
            self.notify(str(error), severity="error")
            return
        selector = self.query_one("#sprite-select", Select)
        selector.set_options(self._sprite_options())
        selector.value = sprite_id
        self.current_view_id = next(iter(self.editor.current_sprite.views))
        self._rebuild_tree()
        self._refresh_preview_controls()
        self._mark_changed()

    def action_rotate_vertical(self) -> None:
        sprite = self.editor.current_sprite
        if "horizontal" not in sprite.views:
            self.notify("This sprite has no horizontal source view.", severity="error")
            return
        if "vertical" in sprite.views:
            self.push_screen(
                ConfirmScreen(
                    "Replace the stored vertical view with a fresh rotation? "
                    "Manual vertical edits will be overwritten."
                ),
                self._finish_rotate_vertical,
            )
        else:
            self._finish_rotate_vertical(True)

    def _finish_rotate_vertical(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        try:
            vertical, warnings = generate_rotated_view(self.editor.current_sprite)
            self.editor.current_sprite.views["vertical"] = vertical
            self.editor.current_sprite.validate()
        except Exception as error:
            self.notify(f"Rotation failed: {error}", severity="error")
            return
        self.current_view_id = "vertical"
        self._rebuild_tree(select_item=vertical)
        self._refresh_preview_controls()
        self._mark_changed()
        if warnings:
            self.notify(
                f"Vertical view generated with {len(warnings)} fallback glyphs (◇).",
                severity="warning",
            )
        else:
            self.notify("Vertical view generated.")

    def action_restore_recovery(self) -> None:
        if not self.editor.has_newer_recovery():
            self.notify("No newer recovery snapshot for this sprite.")
            return
        self.push_screen(
            ConfirmScreen("Replace the in-memory sprite with its recovery snapshot?"),
            self._finish_restore_recovery,
        )

    def _finish_restore_recovery(self, confirmed: bool | None) -> None:
        if not confirmed:
            return
        try:
            self.editor.restore_recovery()
        except Exception as error:
            self.notify(f"Recovery failed: {error}", severity="error")
            return
        self.current_view_id = next(iter(self.editor.current_sprite.views))
        self._rebuild_tree()
        self._refresh_preview_controls()
        self._refresh_preview()
        self._update_dirty_indicator()
        self.notify("Recovery snapshot restored.")

    def action_add_item(self) -> None:
        if self.selection is None:
            return
        kind = self.selection.kind
        item = self.selection.item
        added: object | None = None
        if kind == "sprite":
            sprite = item
            assert isinstance(sprite, Sprite)
            view_id = _unique_id(set(sprite.views), "view")
            added = View(
                id=view_id,
                name=view_id.title(),
                axis="fixed",
                canonical_facing="default",
                mirror_facing=None,
                tiers=[Tier("full", "Full Detail", [_default_section("canvas")])],
            )
            sprite.views[view_id] = added
        elif kind == "view":
            view = item
            assert isinstance(view, View)
            tier_id = _unique_id({tier.id for tier in view.tiers}, "tier")
            if view.axis == "fixed":
                section = _default_section("canvas")
            elif view.axis == "horizontal":
                cross = view.tiers[0].sections[0].variants[0].height
                section = _default_section("section", width=4, height=cross)
            else:
                cross = view.tiers[0].sections[0].variants[0].width
                section = _default_section("section", width=cross, height=4)
            added = Tier(tier_id, tier_id.title(), [section])
            view.tiers.append(added)
        elif kind == "tier":
            tier = item
            assert isinstance(tier, Tier)
            view = self._view_containing(tier)
            if view.axis == "fixed":
                self.notify("Fixed tiers contain exactly one canvas section.", severity="warning")
                return
            section_id = _unique_id({section.id for section in tier.sections}, "section")
            first = tier.sections[0].variants[0]
            added = _default_section(
                section_id,
                width=4 if view.axis == "horizontal" else first.width,
                height=first.height if view.axis == "horizontal" else 4,
            )
            tier.sections.append(added)
        elif kind == "section":
            section_item = item
            assert isinstance(section_item, Section)
            variant_id = _unique_id(
                {variant.id for variant in section_item.variants},
                "variant",
            )
            first = section_item.variants[0]
            added = _blank_variant(variant_id, first.width, first.height)
            section_item.variants.append(added)
        else:
            self.action_duplicate_item()
            return
        try:
            self.editor.current_sprite.validate()
        except Exception as error:
            self.notify(str(error), severity="error")
            return
        self._rebuild_tree(select_item=added)
        self._mark_changed()

    def action_duplicate_item(self) -> None:
        if self.selection is None or self.selection.kind == "sprite":
            return
        item = self.selection.item
        parent = self.selection.parent
        duplicate = deepcopy(item)
        if isinstance(parent, list):
            existing = {getattr(entry, "id", "") for entry in parent}
            duplicate.id = _unique_id(existing, f"{getattr(item, 'id')}_copy")
            index = next(index for index, entry in enumerate(parent) if entry is item)
            parent.insert(index + 1, duplicate)
        elif isinstance(parent, dict) and isinstance(duplicate, View):
            duplicate.id = _unique_id(set(parent), f"{duplicate.id}_copy")
            duplicate.name += " Copy"
            parent[duplicate.id] = duplicate
        else:
            return
        self._rebuild_tree(select_item=duplicate)
        self._mark_changed()

    def action_delete_item(self) -> None:
        if self.selection is None or self.selection.kind == "sprite":
            return
        parent = self.selection.parent
        item = self.selection.item
        if isinstance(parent, list):
            if len(parent) <= 1:
                self.notify("The last item at this level cannot be deleted.", severity="warning")
                return
            parent.remove(item)
        elif isinstance(parent, dict):
            if len(parent) <= 1:
                self.notify("A sprite must keep at least one view.", severity="warning")
                return
            key = next(key for key, value in parent.items() if value is item)
            del parent[key]
            if self.current_view_id == key:
                self.current_view_id = next(iter(parent))
        self.editor.current_sprite.validate()
        self.selection = None
        self.query_one("#art-canvas", ArtCanvas).set_variant(None)
        self._rebuild_tree()
        self._refresh_preview_controls()
        self._mark_changed()

    def _move_selection(self, delta: int) -> None:
        if self.selection is None or not isinstance(self.selection.parent, list):
            return
        parent = self.selection.parent
        item = self.selection.item
        index = next(index for index, entry in enumerate(parent) if entry is item)
        target = index + delta
        if not 0 <= target < len(parent):
            return
        parent[index], parent[target] = parent[target], parent[index]
        # Tier order is semantically richest-first; invalid moves are rejected.
        try:
            self.editor.current_sprite.validate()
        except Exception as error:
            parent[index], parent[target] = parent[target], parent[index]
            self.notify(str(error), severity="warning")
            return
        self._rebuild_tree(select_item=item)
        self._mark_changed()

    def _view_containing(self, target: Tier) -> View:
        for view in self.editor.current_sprite.views.values():
            if any(tier is target for tier in view.tiers):
                return view
        raise LookupError("tier is not attached to a view")


def main() -> None:
    parser = argparse.ArgumentParser(description="Edit Edge sprite art")
    default_assets = Path(__file__).resolve().parents[2] / "assets"
    parser.add_argument(
        "asset_root",
        nargs="?",
        type=Path,
        default=default_assets,
        help="Directory containing palettes.yaml and sprites/",
    )
    args = parser.parse_args()
    EdgeArtDesigner(args.asset_root).run()


if __name__ == "__main__":
    main()
