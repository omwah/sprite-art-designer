"""Focused editor widgets: mouse canvas, glyph picker, and live previews."""

from __future__ import annotations

from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Grid
from textual.geometry import Size
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Static

from sprite_art import PaletteCatalog, Sprite, Variant, render_sprite
from sprite_art.glyphs import AUTHORING_GLYPHS


class ArtCanvas(Widget, can_focus=True):
    """A one-terminal-cell painting surface with drag painting and erasing."""

    class Changed(Message):
        def __init__(self, canvas: ArtCanvas) -> None:
            self.canvas = canvas
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
        if cell is None or event.button not in (1, 3):
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


class GlyphPalette(Grid):
    class Selected(Message):
        def __init__(self, glyph: str) -> None:
            self.glyph = glyph
            super().__init__()

    def compose(self) -> ComposeResult:
        for index, (glyph, description) in enumerate(AUTHORING_GLYPHS):
            label = "␠" if glyph == " " else glyph
            yield Button(
                label,
                id=f"glyph-{index}",
                tooltip=description,
                classes="glyph-button",
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not event.button.id or not event.button.id.startswith("glyph-"):
            return
        index = int(event.button.id.removeprefix("glyph-"))
        self.post_message(self.Selected(AUTHORING_GLYPHS[index][0]))


class PreviewMatrix(Static):
    sprite: Sprite | None = None
    palettes: PaletteCatalog | None = None
    archetype_id = "humanoid_diplomat"
    view_id = "horizontal"
    facing: str | None = None
    seed = 7
    sizes: list[tuple[int, int]] = [(18, 3), (30, 5), (40, 7), (56, 12)]

    def configure(
        self,
        *,
        sprite: Sprite,
        palettes: PaletteCatalog,
        archetype_id: str,
        view_id: str,
        facing: str | None,
        seed: int,
        sizes: list[tuple[int, int]],
    ) -> None:
        self.sprite = sprite
        self.palettes = palettes
        self.archetype_id = archetype_id
        self.view_id = view_id
        self.facing = facing
        self.seed = seed
        self.sizes = sizes
        self.refresh_previews()

    def refresh_previews(self) -> None:
        if self.sprite is None or self.palettes is None:
            self.update("No preview")
            return
        view = self.sprite.views[self.view_id]
        panels: list[Panel] = []
        for configured_width, configured_height in self.sizes:
            width, height = (
                (configured_height, configured_width)
                if view.axis == "vertical"
                else (configured_width, configured_height)
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
            )
            panels.append(
                Panel(
                    art,
                    title=f"{self.view_id} · {width}×{height}",
                    border_style="grey35",
                    padding=(0, 0),
                )
            )
        self.update(Columns(panels, equal=False, expand=False, padding=(0, 1)))
