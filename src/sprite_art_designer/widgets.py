"""Focused editor widgets: mouse canvas, glyph picker, and live previews."""

from __future__ import annotations

from rich.color import Color
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, ItemGrid, Vertical, VerticalScroll
from textual.geometry import Size
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Select, Static, Switch, TabbedContent, TabPane, Tree

from sprite_art import PaletteCatalog, Sprite, Variant, render_sprite
from sprite_art.glyphs import AUTHORING_GLYPHS, SEMANTIC_GLYPHS

SEMANTIC_BUTTON_RENDERING = {
    "R": ("▀", "#f87171"),
    "Y": ("▀", "#facc15"),
    "G": ("▀", "#22c55e"),
    "B": ("▀", "#3b82f6"),
    "r": ("▄", "#f87171"),
    "y": ("▄", "#facc15"),
    "g": ("▄", "#22c55e"),
    "b": ("▄", "#3b82f6"),
}


class ArtCanvas(Widget, can_focus=True):
    """A one-terminal-cell painting surface with drag painting and erasing."""

    class Changed(Message):
        def __init__(self, canvas: ArtCanvas) -> None:
            self.canvas = canvas
            super().__init__()

    class GlyphPicked(Message):
        def __init__(self, canvas: ArtCanvas, glyph: str) -> None:
            self.canvas = canvas
            self.glyph = glyph
            super().__init__()

    variant: Variant | None = None
    selected_glyph: str = "█"
    cursor_x: int = 0
    cursor_y: int = 0
    _painting_button: int = 0

    def set_variant(self, variant: Variant | None) -> None:
        self.variant = variant
        self.cursor_x = 0
        self.cursor_y = 0
        self.refresh(layout=True)

    def set_glyph(self, glyph: str) -> None:
        self.selected_glyph = glyph

    def get_content_width(self, container: Size, viewport: Size) -> int:
        return max(1, (self.variant.width if self.variant else 1))

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        return max(1, (self.variant.height if self.variant else 1))

    def render(self) -> Text:
        if self.variant is None:
            return Text("Select a variant to paint.", style="dim")
        output = Text()
        for row_index, row in enumerate(self.variant.cells):
            for column, glyph in enumerate(row):
                shown = "·" if glyph == " " else glyph
                style = "grey35" if glyph == " " else "white"
                if column == self.cursor_x and row_index == self.cursor_y:
                    style += " on #315a74"
                output.append(shown, style=style)
            if row_index < self.variant.height - 1:
                output.append("\n")
        return output

    def _cell_from_event(self, event: events.MouseEvent) -> tuple[int, int] | None:
        if self.variant is None:
            return None
        x = event.screen_x - self.content_region.x
        y = event.screen_y - self.content_region.y
        if 0 <= x < self.variant.width and 0 <= y < self.variant.height:
            return x, y
        return None

    def _paint(self, x: int, y: int, button: int) -> None:
        if self.variant is None:
            return
        glyph = " " if button == 3 else self.selected_glyph
        row = self.variant.cells[y]
        if row[x] == glyph:
            return
        self.variant.cells[y] = row[:x] + glyph + row[x + 1 :]
        self.cursor_x = x
        self.cursor_y = y
        self.refresh()
        self.post_message(self.Changed(self))

    def on_mouse_down(self, event: events.MouseDown) -> None:
        cell = self._cell_from_event(event)
        if cell is None:
            return
        if event.button == 2:
            assert self.variant is not None
            glyph = self.variant.cells[cell[1]][cell[0]]
            self.cursor_x, self.cursor_y = cell
            self.set_glyph(glyph)
            self.refresh()
            self.post_message(self.GlyphPicked(self, glyph))
            event.stop()
            return
        if event.button not in (1, 3):
            return
        self.focus()
        self._painting_button = event.button
        self.capture_mouse()
        self._paint(*cell, event.button)
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._painting_button:
            return
        cell = self._cell_from_event(event)
        if cell is not None:
            self._paint(*cell, self._painting_button)
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._painting_button:
            self._painting_button = 0
            self.release_mouse()
            event.stop()

    def on_key(self, event: events.Key) -> None:
        if self.variant is None:
            return
        if event.key == "left":
            self.cursor_x = max(0, self.cursor_x - 1)
        elif event.key == "right":
            self.cursor_x = min(self.variant.width - 1, self.cursor_x + 1)
        elif event.key == "up":
            self.cursor_y = max(0, self.cursor_y - 1)
        elif event.key == "down":
            self.cursor_y = min(self.variant.height - 1, self.cursor_y + 1)
        elif event.key in ("space", "enter"):
            self._paint(self.cursor_x, self.cursor_y, 1)
        elif event.key in ("delete", "backspace"):
            self._paint(self.cursor_x, self.cursor_y, 3)
        else:
            return
        self.refresh()
        event.stop()


class WorkspaceSplitter(Widget):
    """One-row mouse-drag divider for the workspace's top and bottom rows."""

    class Moved(Message):
        def __init__(self, splitter: WorkspaceSplitter, screen_y: int) -> None:
            self.splitter = splitter
            self.screen_y = screen_y
            super().__init__()

    _dragging = False

    def render(self) -> Text:
        return Text()

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.button != 1:
            return
        self._dragging = True
        self.capture_mouse()
        self.post_message(self.Moved(self, event.screen_y))
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        self.post_message(self.Moved(self, event.screen_y))
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.release_mouse()
        event.stop()


class GlyphPalette(ItemGrid):
    class Selected(Message):
        def __init__(self, glyph: str) -> None:
            self.glyph = glyph
            super().__init__()

    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        glyphs: tuple[tuple[str, str], ...] = AUTHORING_GLYPHS,
        button_prefix: str = "glyph",
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            min_column_width=3,
            stretch_height=False,
        )
        self.glyphs = glyphs
        self.button_prefix = button_prefix

    def compose(self) -> ComposeResult:
        for index, (glyph, description) in enumerate(self.glyphs):
            label = "␠" if glyph == " " else glyph
            yield Button(
                label,
                id=f"{self.button_prefix}-{index}",
                tooltip=description,
                classes="glyph-button",
            )

    def set_selected_glyph(self, glyph: str) -> None:
        for index, (candidate, _description) in enumerate(self.glyphs):
            button = self.query_one(f"#{self.button_prefix}-{index}", Button)
            button.variant = "primary" if candidate == glyph else "default"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not event.button.id or not event.button.id.startswith(f"{self.button_prefix}-"):
            return
        index = int(event.button.id.removeprefix(f"{self.button_prefix}-"))
        glyph = self.glyphs[index][0]
        self.set_selected_glyph(glyph)
        self.post_message(self.Selected(glyph))


class SemanticGlyphRow(Horizontal):
    """A compact, contiguous row of semantic marker buttons."""

    class Selected(Message):
        def __init__(self, glyph: str) -> None:
            self.glyph = glyph
            super().__init__()

    glyphs = tuple(item for item in AUTHORING_GLYPHS if item[0] in SEMANTIC_GLYPHS)

    def compose(self) -> ComposeResult:
        for index, (glyph, description) in enumerate(self.glyphs):
            rendered_glyph, color = SEMANTIC_BUTTON_RENDERING[glyph]
            label = Text.assemble((rendered_glyph, color), f" ({glyph})")
            row = "upper" if index < 4 else "lower"
            yield Button(
                label,
                id=f"semantic-glyph-{index}",
                tooltip=description,
                classes=f"glyph-button semantic-{row}",
            )

    def set_selected_glyph(self, glyph: str) -> None:
        for index, (candidate, _description) in enumerate(self.glyphs):
            button = self.query_one(f"#semantic-glyph-{index}", Button)
            button.variant = "primary" if candidate == glyph else "default"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not event.button.id or not event.button.id.startswith("semantic-glyph-"):
            return
        index = int(event.button.id.removeprefix("semantic-glyph-"))
        glyph = self.glyphs[index][0]
        self.set_selected_glyph(glyph)
        self.post_message(self.Selected(glyph))


class DocumentBar(Horizontal):
    """The current-sprite picker and document-level actions."""

    def __init__(self, sprite_options: list[tuple[str, str]], current_sprite_id: str) -> None:
        super().__init__(id="document-bar")
        self.sprite_options = sprite_options
        self.current_sprite_id = current_sprite_id

    def compose(self) -> ComposeResult:
        yield Label("Sprite")
        yield Select(
            self.sprite_options,
            value=self.current_sprite_id,
            allow_blank=False,
            id="sprite-select",
        )
        yield Select(
            [
                ("New sprite", "new-sprite"),
                ("Save", "save"),
                ("Save all", "save-all"),
                ("Import RexPaint", "import-rexpaint"),
                ("Export RexPaint", "export-rexpaint"),
                ("Generate vertical", "rotate-vertical"),
            ],
            prompt="Actions",
            id="document-actions",
        )
        yield Label("", id="dirty-indicator")


class NarrowTabs(Horizontal):
    """Panel switcher shown when the workspace is too narrow for all panes."""

    def __init__(self) -> None:
        super().__init__(id="narrow-tabs")

    def compose(self) -> ComposeResult:
        yield Button("Navigate", id="panel-nav")
        yield Button("Canvas", id="panel-canvas", variant="primary")
        yield Button("Tools", id="panel-tools")
        yield Button("Preview", id="panel-preview")


class NavPane(Vertical):
    """Sprite composition navigator and structural editing controls."""

    def __init__(self) -> None:
        super().__init__(id="nav-pane", classes="pane")

    def compose(self) -> ComposeResult:
        yield Label("Structure", classes="pane-title")
        yield Tree("Sprite", id="structure-tree")
        with Horizontal(id="structure-actions-row"):
            with Grid(id="structure-actions"):
                yield Button("+", id="add-item", tooltip="Add child")
                yield Button("⧉", id="duplicate-item", tooltip="Duplicate")
                yield Button("−", id="delete-item", tooltip="Delete")
                yield Button("↑", id="move-up", tooltip="Move up")
                yield Button("↓", id="move-down", tooltip="Move down")


class CanvasPane(Vertical):
    """Editable cell canvas."""

    def __init__(self) -> None:
        super().__init__(id="canvas-pane", classes="pane")

    def compose(self) -> ComposeResult:
        yield Label("Select a variant", id="canvas-title", classes="pane-title")
        with VerticalScroll(id="canvas-scroll"):
            with Horizontal(id="canvas-navigation"):
                with Vertical(classes="canvas-navigation-button"):
                    yield Button("‹", id="previous-structure", tooltip="Previous structure (,)")
                with Vertical(classes="canvas-art-wrapper"):
                    yield ArtCanvas(id="art-canvas")
                with Vertical(classes="canvas-navigation-button"):
                    yield Button("›", id="next-structure", tooltip="Next structure (.)")


class GlyphToolsTab(TabPane):
    """Glyph selection tab."""

    def __init__(self) -> None:
        super().__init__("Glyphs", id="glyph-tab")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield GlyphPalette(
                id="glyph-palette",
                glyphs=tuple(item for item in AUTHORING_GLYPHS if item[0] not in SEMANTIC_GLYPHS),
            )
            with Vertical(id="semantic-glyph-row"):
                yield SemanticGlyphRow(id="semantic-glyph-upper")
                yield SemanticGlyphRow(id="semantic-glyph-lower")
            yield Label("Selected: █", id="selected-glyph")


class PropertiesToolsTab(TabPane):
    """Structure selection metadata tab."""

    def __init__(self) -> None:
        super().__init__("Properties", id="properties-tab")

    def compose(self) -> ComposeResult:
        from sprite_art import PROPERTY_IDS

        with VerticalScroll():
            yield Label("Selection", id="selection-title", classes="section-title")
            yield Label("ID")
            yield Input(id="item-id")
            yield Label("Name")
            yield Input(id="item-name")
            with Vertical(id="section-fields"):
                yield Label("Primary property")
                yield Select(
                    [(value.replace("_", " ").title(), value) for value in PROPERTY_IDS],
                    value="utility",
                    allow_blank=False,
                    id="primary-property",
                )
                yield Label("Secondary properties (comma-separated)")
                yield Input(id="secondary-properties")
            with Vertical(id="variant-fields"):
                yield Label("Selection weight")
                yield Input(value="1", type="integer", id="variant-weight")
                yield Label("Canvas width / height")
                with Horizontal(classes="canvas-dimensions"):
                    yield Input(value="1", type="integer", id="variant-width")
                    yield Input(value="1", type="integer", id="variant-height")
            yield Button("Apply properties", id="apply-properties", variant="primary")


class PaletteToolsTab(TabPane):
    """Controlled archetype palette tab."""

    def __init__(self, current_archetype: str) -> None:
        super().__init__("Palette", id="palette-tab")
        self.current_archetype = current_archetype

    def compose(self) -> ComposeResult:
        from sprite_art import ARCHETYPE_IDS

        with VerticalScroll():
            yield Label("Controlled archetype")
            yield Select(
                [(value.replace("_", " ").title(), value) for value in ARCHETYPE_IDS],
                value=self.current_archetype,
                allow_blank=False,
                id="palette-archetype",
            )
            with ItemGrid(
                min_column_width=25,
                regular=False,
                classes="palette-swatch-row",
            ):
                yield PaletteColorGroup(
                    "Surface colors",
                    (("bright", 0), ("mid", 0), ("dark", 0), ("facet", 0)),
                )
                for field_name in ("beacon", "engine", "window"):
                    yield PaletteColorGroup(
                        field_name.replace("_", " ").title(),
                        tuple((field_name, index) for index in range(3)),
                    )


class PaletteColorGroup(Vertical):
    """A labeled palette color pool that can wrap as one responsive unit."""

    def __init__(self, label: str, swatches: tuple[tuple[str, int], ...]) -> None:
        super().__init__(classes="palette-color-group")
        self.label = label
        self.swatches = swatches

    def compose(self) -> ComposeResult:
        yield Label(self.label, classes="palette-group-label")
        with Horizontal(classes="palette-color-group-swatches"):
            for field_name, index in self.swatches:
                yield PaletteColorSwatch(field_name, index)

    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        """Reserve one label row and two complete swatch rows in an ItemGrid."""
        return 3


class PaletteColorSwatch(Button):
    """A clickable palette color shown against its own background."""

    class Selected(Message):
        def __init__(self, swatch: PaletteColorSwatch) -> None:
            super().__init__()
            self.swatch = swatch

    def __init__(self, field_name: str, index: int) -> None:
        super().__init__("", id=f"palette-color-{field_name}-{index}")
        self.field_name = field_name
        self.color_index = index
        self.color_value = ""

    def set_color(self, color: str | None) -> None:
        self.display = color is not None
        if color is None:
            return
        parsed = Color.parse(color).get_truecolor()
        self.color_value = color
        self.label = ""
        self.tooltip = f"Edit {self.field_name.replace('_', ' ')}: {color}"
        self.styles.background = f"#{parsed.red:02x}{parsed.green:02x}{parsed.blue:02x}"
        luminance = (parsed.red * 299 + parsed.green * 587 + parsed.blue * 114) / 1000
        self.styles.color = "black" if luminance >= 140 else "white"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.Selected(self))


class ShipConfigToolsTab(TabPane):
    """Per-tier ship width and structure-length configuration."""

    def __init__(self) -> None:
        super().__init__("Ship Config", id="ship-config-tab")

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Label("Select a tier to configure its ship width and structure lengths.")
            yield Label("Tier", id="ship-config-tier")
            yield Label("Ship width", id="ship-config-width")
            yield Label("Structure lengths (structure: count)")
            yield Input(id="ship-config-lengths")
            yield Button("Apply ship config", id="apply-ship-config", variant="primary")


class PreviewToolsTab(TabPane):
    """Preview view, random seed, and size controls tab."""

    def __init__(
        self,
        view_options: list[tuple[str, str]],
        initial_view_id: str,
        facing_options: list[tuple[str, str]],
        seed: int,
        size: tuple[int, int],
        tier_options: list[tuple[str, str]],
        initial_tier_id: str,
        highlight_enabled: bool,
    ) -> None:
        super().__init__("Preview", id="preview-tab")
        self.view_options = view_options
        self.initial_view_id = initial_view_id
        self.facing_options = facing_options
        self.seed = seed
        self.preview_size = size
        self.tier_options = tier_options
        self.initial_tier_id = initial_tier_id
        self.highlight_enabled = highlight_enabled

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-controls"):
            yield Label("View")
            yield Select(self.view_options, value=self.initial_view_id, allow_blank=False, id="preview-view")
            yield Label("Facing")
            yield Select(
                self.facing_options,
                value=self.facing_options[0][1],
                allow_blank=False,
                id="preview-facing",
            )
            yield Label("Seed")
            with Horizontal(id="preview-seed-controls"):
                yield Input(value=str(self.seed), type="integer", id="preview-seed")
                yield Button("Reset", id="reset-preview-seed")
            yield Label("Tier")
            with Horizontal(id="preview-size-controls"):
                yield Select(
                    self.tier_options,
                    value=Select.NULL,
                    allow_blank=False,
                    id="preview-size",
                )
                yield Input(placeholder="Custom: 40x7", id="preview-custom-size")
            yield Label("Highlight edit")
            yield Switch(value=self.highlight_enabled, id="preview-highlight")
            yield Button("Apply", id="apply-preview", variant="primary")


class ToolsPane(Vertical):
    """Glyph, property, palette, and preview editing tabs."""

    def __init__(
        self,
        current_archetype: str,
        view_options: list[tuple[str, str]],
        initial_view_id: str,
        facing_options: list[tuple[str, str]],
        seed: int,
        size: tuple[int, int],
        tier_options: list[tuple[str, str]],
        initial_tier_id: str,
        highlight_enabled: bool,
    ) -> None:
        super().__init__(id="tools-pane", classes="pane")
        self.current_archetype = current_archetype
        self.view_options = view_options
        self.initial_view_id = initial_view_id
        self.facing_options = facing_options
        self.seed = seed
        self.preview_size = size
        self.tier_options = tier_options
        self.initial_tier_id = initial_tier_id
        self.highlight_enabled = highlight_enabled

    def compose(self) -> ComposeResult:
        with TabbedContent(id="tool-tabs"):
            yield GlyphToolsTab()
            yield PaletteToolsTab(self.current_archetype)
            yield PreviewToolsTab(
                self.view_options,
                self.initial_view_id,
                self.facing_options,
                self.seed,
                self.preview_size,
                self.tier_options,
                self.initial_tier_id,
                self.highlight_enabled,
            )
            yield PropertiesToolsTab()
            yield ShipConfigToolsTab()


class PreviewPane(Vertical):
    """Live rendered sprite preview."""

    def __init__(self) -> None:
        super().__init__(id="preview-pane", classes="pane")

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="preview-scroll"):
            yield PreviewMatrix(id="preview-matrix")


class PreviewMatrix(Static):
    class StructureSelected(Message):
        """A click on a rendered art cell that may belong to a structure."""

        def __init__(self, preview: PreviewMatrix, x: int, y: int) -> None:
            self.preview = preview
            self.x = x
            self.y = y
            super().__init__()

    sprite: Sprite | None = None
    palettes: PaletteCatalog | None = None
    archetype_id = "humanoid_diplomat"
    view_id = "horizontal"
    facing: str | None = None
    seed = 7
    preview_size: tuple[int, int] = (56, 12)
    highlight_variant: Variant | None = None
    variant_overrides: dict[int, Variant] | None = None

    @staticmethod
    def dimensions_for_view(
        axis: str,
        configured_width: int,
        configured_height: int,
    ) -> tuple[int, int]:
        """Return an aspect-corrected preview box for the stored view axis."""

        if axis == "vertical":
            return configured_height * 2, (configured_width + 1) // 2
        return configured_width, configured_height

    def configure(
        self,
        *,
        sprite: Sprite,
        palettes: PaletteCatalog,
        archetype_id: str,
        view_id: str,
        facing: str | None,
        seed: int,
        size: tuple[int, int],
        highlight_variant: Variant | None,
        variant_overrides: dict[int, Variant] | None,
    ) -> None:
        self.sprite = sprite
        self.palettes = palettes
        self.archetype_id = archetype_id
        self.view_id = view_id
        self.facing = facing
        self.seed = seed
        self.preview_size = size
        self.highlight_variant = highlight_variant
        self.variant_overrides = variant_overrides
        self.refresh_previews()

    def refresh_previews(self) -> None:
        if self.sprite is None or self.palettes is None:
            self.update("No preview")
            return
        view = self.sprite.views[self.view_id]
        width, height = self.dimensions_for_view(
            view.axis,
            *self.preview_size,
        )
        art = render_sprite(
            self.sprite,
            self.palettes,
            width=width,
            height=height,
            seed=self.seed,
            archetype_id=self.archetype_id,
            view_id=self.view_id,
            facing=self.facing,
            highlight_variant=self.highlight_variant,
            variant_overrides=self.variant_overrides,
            preview_margin=True,
        )
        # The panel has one border cell and the matrix has one padding cell on
        # each side. Keeping the widget at this natural width lets its scroll
        # parent center it instead of stretching it across the pane.
        self.styles.width = width + 6
        self.update(
            Columns(
                [
                    Panel(
                        art,
                        title=f"{self.view_id} · {width}×{height}",
                        border_style="grey35",
                        padding=(0, 0),
                    )
                ],
                equal=False,
                expand=False,
                padding=(0, 1),
            )
        )

    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Translate a click through the Columns, Panel, and preview margins."""

        if event.button != 1 or self.sprite is None:
            return
        view = self.sprite.views[self.view_id]
        width, height = self.dimensions_for_view(view.axis, *self.preview_size)
        x = event.screen_x - self.content_region.x - 3
        y = event.screen_y - self.content_region.y - 2
        if 0 <= x < width and 0 <= y < height:
            self.post_message(self.StructureSelected(self, x, y))
            event.stop()
