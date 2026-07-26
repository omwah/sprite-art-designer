"""Native REXPaint ``.xp`` export for rendered sprite art."""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

from rich.console import Console
from rich.text import Text

from .glyphs import AUTHORING_GLYPHS
from .model import PaletteCatalog, Sprite, Variant
from .render import render_sprite

REXPAINT_VERSION = -1
REXPAINT_FONT_COLUMNS = 16
"""The bundled font uses a 16-column glyph sheet, as REXPaint expects."""

# ``.xp`` files store font-slot indices, not Unicode code points.  Keep this
# compact, stable mapping in lockstep with the bundled font sheet.
REXPAINT_GLYPH_INDICES = {
    glyph: index
    for index, glyph in enumerate(
        [glyph for glyph, _ in AUTHORING_GLYPHS] + ["▤", "▦"]
    )
}


class RexPaintGlyphError(ValueError):
    """A rendered glyph has no slot in the bundled REXPaint font."""


def _rgb(text: Text, offset: int, console: Console) -> tuple[int, int, int, int, int, int]:
    style = text.get_style_at_offset(console, offset)
    foreground = style.color.get_truecolor() if style.color is not None else None
    background = style.bgcolor.get_truecolor() if style.bgcolor is not None else None
    return (
        foreground.red if foreground is not None else 0,
        foreground.green if foreground is not None else 0,
        foreground.blue if foreground is not None else 0,
        background.red if background is not None else 0,
        background.green if background is not None else 0,
        background.blue if background is not None else 0,
    )


def rexpaint_bytes(text: Text, *, width: int, height: int) -> bytes:
    """Encode an exact rectangular Rich text grid as a one-layer ``.xp`` file."""

    rows = text.plain.splitlines()
    if len(rows) != height or any(len(row) != width for row in rows):
        raise ValueError("REXPaint export requires an exact rectangular text grid")

    output = bytearray(struct.pack("<iiii", REXPAINT_VERSION, 1, width, height))
    # REXPaint serializes cells in column-major order.
    console = Console(color_system="truecolor")
    for x in range(width):
        for y in range(height):
            offset = y * (width + 1) + x
            glyph = text.plain[offset]
            try:
                glyph_index = REXPAINT_GLYPH_INDICES[glyph]
            except KeyError as error:
                raise RexPaintGlyphError(
                    f"glyph {glyph!r} at column {x}, row {y} has no REXPaint font slot"
                ) from error
            output.extend(struct.pack("<I6B", glyph_index, *_rgb(text, offset, console)))
    return gzip.compress(bytes(output), mtime=0)


def export_rexpaint(
    sprite: Sprite,
    palettes: PaletteCatalog,
    destination: str | Path,
    *,
    width: int,
    height: int,
    seed: int = 0,
    archetype_id: str = "humanoid_diplomat",
    view_id: str = "horizontal",
    facing: str | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> Path:
    """Render and atomically write a deterministic one-layer REXPaint file."""

    rendered = render_sprite(
        sprite,
        palettes,
        width=width,
        height=height,
        seed=seed,
        archetype_id=archetype_id,
        view_id=view_id,
        facing=facing,
        variant_overrides=variant_overrides,
    )
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(rexpaint_bytes(rendered, width=width, height=height))
    temporary.replace(target)
    return target
