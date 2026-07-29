"""Native REXPaint ``.xp`` export for rendered sprite art."""

from __future__ import annotations

import gzip
import struct
from dataclasses import dataclass
from pathlib import Path

from rich.color import Color
from rich.console import Console
from rich.text import Text

from .glyphs import AUTHORING_GLYPHS, flip_rows_horizontal, flip_rows_vertical
from .model import (
    COLOR_SET_CODES,
    COLOR_SET_IDS,
    SURFACE_MASK_CODE,
    Palette,
    PaletteCatalog,
    Sprite,
    Variant,
)
from .render import render_sprite, selected_tier, selected_variants

REXPAINT_VERSION = -1
REXPAINT_FONT_COLUMNS = 16
"""The bundled font uses a 16-column glyph sheet, as REXPaint expects."""
MAX_REXPAINT_CELLS = 250_000

# ``.xp`` files store font-slot indices, not Unicode code points.  Keep this
# compact, stable mapping in lockstep with the bundled font sheet.
REXPAINT_GLYPH_INDICES = {
    glyph: index
    for index, glyph in enumerate(glyph for glyph, _ in AUTHORING_GLYPHS)
}


class RexPaintGlyphError(ValueError):
    """A rendered glyph has no slot in the bundled REXPaint font."""


class RexPaintImportError(ValueError):
    """A REXPaint file cannot be safely imported as Edge sprite geometry."""


RGB = tuple[int, int, int]


@dataclass(frozen=True)
class RexPaintImage:
    glyphs: list[str]
    foreground: list[list[RGB]]

    @property
    def width(self) -> int:
        return len(self.glyphs[0]) if self.glyphs else 0

    @property
    def height(self) -> int:
        return len(self.glyphs)


@dataclass(frozen=True)
class RexPaintExport:
    image_path: Path
    palette_path: Path


def import_rexpaint_cells(source: str | Path) -> RexPaintImage:
    """Read one bundled-font REXPaint layer with its foreground colors.

    Imported colors are later matched to the closest controlled color set.
    """

    path = Path(source)
    max_bytes = 16 + MAX_REXPAINT_CELLS * 10
    try:
        with gzip.open(path, "rb") as compressed:
            data = compressed.read(max_bytes + 1)
    except (OSError, EOFError) as error:
        raise RexPaintImportError(f"could not read REXPaint file {path}: {error}") from error
    if len(data) > max_bytes:
        raise RexPaintImportError(
            f"{path}: image exceeds the {MAX_REXPAINT_CELLS:,}-cell import limit"
        )
    if len(data) < 8:
        raise RexPaintImportError(f"{path}: file is too short for a REXPaint image")
    _version, layers = struct.unpack_from("<ii", data)
    if layers != 1:
        raise RexPaintImportError(
            f"{path}: expected one layer, found {layers}; flatten it in REXPaint first"
        )
    if len(data) < 16:
        raise RexPaintImportError(f"{path}: file is too short for a REXPaint image")
    width, height = struct.unpack_from("<ii", data, 8)
    if width < 1 or height < 1 or width * height > MAX_REXPAINT_CELLS:
        raise RexPaintImportError(f"{path}: unsupported image dimensions {width}x{height}")
    expected_bytes = 16 + width * height * 10
    if len(data) != expected_bytes:
        raise RexPaintImportError(
            f"{path}: expected {expected_bytes} bytes for a {width}x{height} image, "
            f"found {len(data)}"
        )
    glyphs = {index: glyph for glyph, index in REXPAINT_GLYPH_INDICES.items()}
    rows = [[" "] * width for _ in range(height)]
    foreground: list[list[RGB]] = [
        [(0, 0, 0) for _ in range(width)] for _ in range(height)
    ]
    offset = 16
    for x in range(width):
        for y in range(height):
            glyph_index, red, green, blue, *_background = struct.unpack_from(
                "<I6B", data, offset
            )
            offset += 10
            glyph = glyphs.get(glyph_index)
            if glyph is None:
                raise RexPaintImportError(
                    f"{path}: glyph index {glyph_index} at column {x}, row {y} "
                    "is not in the Edge art font map"
                )
            rows[y][x] = glyph
            foreground[y][x] = (red, green, blue)
    return RexPaintImage(["".join(row) for row in rows], foreground)


def _truecolor(value: str) -> RGB:
    color = Color.parse(value).get_truecolor()
    return color.red, color.green, color.blue


def _distance(left: RGB, right: RGB) -> int:
    return sum((left[index] - right[index]) ** 2 for index in range(3))


def _infer_color_mask(image: RexPaintImage, palette: Palette) -> list[str]:
    candidates = {
        color_set_id: [
            _truecolor(color)
            for color in palette.color_set(color_set_id).colors
        ]
        for color_set_id in COLOR_SET_IDS
    }
    result: list[str] = []
    for glyph_row, color_row in zip(image.glyphs, image.foreground):
        codes: list[str] = []
        for glyph, color in zip(glyph_row, color_row):
            if glyph == " ":
                codes.append(SURFACE_MASK_CODE)
                continue
            color_set_id = min(
                COLOR_SET_IDS,
                key=lambda candidate: min(
                    _distance(color, configured)
                    for configured in candidates[candidate]
                ),
            )
            codes.append(COLOR_SET_CODES[color_set_id])
        result.append("".join(codes))
    return result


def _flip_mask_horizontal(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def _flip_mask_vertical(rows: list[str]) -> list[str]:
    return list(reversed(rows))


def segment_rexpaint_cells(
    image: RexPaintImage,
    sprite: Sprite,
    palettes: PaletteCatalog,
    *,
    width: int,
    height: int,
    seed: int = 0,
    archetype_id: str = "humanoid_diplomat",
    view_id: str = "horizontal",
    facing: str | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> list[tuple[Variant, list[str], list[str]]]:
    """Split a just-exported grid back into its active editable variants.

    The imported image must match the current render request exactly. Each
    repeated copy of one active variant must also be identical, since a section
    has only one editable source variant.
    """

    if image.height != height or image.width != width:
        raise RexPaintImportError(
            f"imported image is {image.width}x{image.height}, "
            f"but the current preview is {width}x{height}"
        )
    view = sprite.views.get(view_id)
    if view is None:
        raise RexPaintImportError(f"sprite {sprite.id!r} has no view {view_id!r}")
    tier = selected_tier(sprite, width=width, height=height, view_id=view_id)
    active = selected_variants(
        sprite,
        palettes,
        width=width,
        height=height,
        seed=seed,
        archetype_id=archetype_id,
        view_id=view_id,
        variant_overrides=variant_overrides,
    )
    variants = [active[id(section.variants)] for section in tier.sections]
    horizontal = view.axis != "vertical"
    repeats = [section.repeat for section in tier.sections]

    natural_width = sum(variant.width * repeat for variant, repeat in zip(variants, repeats))
    natural_height = (
        variants[0].height
        if horizontal
        else sum(variant.height * repeat for variant, repeat in zip(variants, repeats))
    )
    if natural_width > width or natural_height > height:
        raise RexPaintImportError(
            "the current preview crops this structure; choose a larger preview before import"
        )

    rows = list(image.glyphs)
    color_mask = _infer_color_mask(image, palettes.resolve(archetype_id))
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        if horizontal:
            rows = flip_rows_horizontal(rows)
            color_mask = _flip_mask_horizontal(color_mask)
        else:
            rows = flip_rows_vertical(rows)
            color_mask = _flip_mask_vertical(color_mask)
    left = (width - natural_width) // 2
    top = (height - natural_height) // 2
    segments: list[tuple[Variant, list[str], list[str]]] = []
    if horizontal:
        cursor = left
        for variant, repeat in zip(variants, repeats):
            copies = [
                [
                    row[cursor + copy * variant.width : cursor + (copy + 1) * variant.width]
                    for row in rows[top : top + variant.height]
                ]
                for copy in range(repeat)
            ]
            mask_copies = [
                [
                    row[cursor + copy * variant.width : cursor + (copy + 1) * variant.width]
                    for row in color_mask[top : top + variant.height]
                ]
                for copy in range(repeat)
            ]
            if any(copy != copies[0] for copy in copies[1:]) or any(
                copy != mask_copies[0] for copy in mask_copies[1:]
            ):
                raise RexPaintImportError(
                    f"active variant {variant.id!r} has edited repeated glyph or "
                    "color-mask copies; make them match"
                )
            segments.append((variant, copies[0], mask_copies[0]))
            cursor += variant.width * repeat
    else:
        cursor = top
        for variant, repeat in reversed(list(zip(variants, repeats))):
            copies = [rows[cursor + copy * variant.height : cursor + (copy + 1) * variant.height]
                      for copy in range(repeat)]
            mask_copies = [
                color_mask[
                    cursor + copy * variant.height : cursor + (copy + 1) * variant.height
                ]
                for copy in range(repeat)
            ]
            if any(copy != copies[0] for copy in copies[1:]) or any(
                copy != mask_copies[0] for copy in mask_copies[1:]
            ):
                raise RexPaintImportError(
                    f"active variant {variant.id!r} has edited repeated glyph or "
                    "color-mask copies; make them match"
                )
            segments.append((variant, copies[0], mask_copies[0]))
            cursor += variant.height * repeat
    return segments


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


def rexpaint_palette_text(palette: Palette) -> str:
    """Build REXPaint's 16x16 native text palette with one row per color set."""

    entries: list[RGB] = [(0, 0, 0)] * 256
    for row, color_set_id in enumerate(COLOR_SET_IDS):
        for column, color in enumerate(palette.color_set(color_set_id).colors):
            entries[row * REXPAINT_FONT_COLUMNS + column] = _truecolor(color)
    return " ".join(f"{{{red:3d},{green:3d},{blue:3d}}}" for red, green, blue in entries)


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
) -> RexPaintExport:
    """Atomically write a deterministic REXPaint image and matching palette."""

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
        primary_colors=True,
    )
    target = Path(destination)
    palette_target = target.with_name(f"{target.stem}-palette.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(rexpaint_bytes(rendered, width=width, height=height))
    temporary.replace(target)
    palette_temporary = palette_target.with_suffix(palette_target.suffix + ".tmp")
    palette_temporary.write_text(
        rexpaint_palette_text(palettes.resolve(archetype_id)), encoding="utf-8"
    )
    palette_temporary.replace(palette_target)
    return RexPaintExport(target, palette_target)
