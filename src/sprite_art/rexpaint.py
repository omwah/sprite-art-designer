"""Native REXPaint ``.xp`` export for rendered sprite art."""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

from rich.console import Console
from rich.text import Text

from .glyphs import AUTHORING_GLYPHS, flip_rows_horizontal, flip_rows_vertical
from .model import PaletteCatalog, Section, Sprite, Variant
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


def import_rexpaint_cells(source: str | Path) -> list[str]:
    """Read one bundled-font REXPaint layer as rectangular glyph rows.

    Colors are deliberately not imported: sprite art stores geometry separately
    from its controlled archetype palettes.
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
    offset = 16
    for x in range(width):
        for y in range(height):
            glyph_index, *_colors = struct.unpack_from("<I6B", data, offset)
            offset += 10
            glyph = glyphs.get(glyph_index)
            if glyph is None:
                raise RexPaintImportError(
                    f"{path}: glyph index {glyph_index} at column {x}, row {y} "
                    "is not in the Edge art font map"
                )
            rows[y][x] = glyph
    return ["".join(row) for row in rows]


def _repeat_counts(
    sections: list[Section], variants: list[Variant], target: int, *, horizontal: bool
) -> list[int]:
    """Match the renderer's deterministic repeat-growth order."""

    footprints = [variant.width if horizontal else variant.height for variant in variants]
    repeats = [section.min_repeat for section in sections]
    total = sum(footprint * repeat for footprint, repeat in zip(footprints, repeats))
    growable = [
        index
        for index, section in enumerate(sections)
        if section.max_repeat > section.min_repeat
    ]
    progressed = True
    while progressed and growable:
        progressed = False
        for index in growable:
            if repeats[index] < sections[index].max_repeat and total + footprints[index] <= target:
                repeats[index] += 1
                total += footprints[index]
                progressed = True
    return repeats


def _restore_semantic_markers(variant: Variant, cells: list[str]) -> list[str]:
    """Recover unchanged authoring markers that rendering turns into block glyphs."""

    rendered_markers = {
        "R": "▀",
        "r": "▄",
        "Y": "▀",
        "y": "▄",
        "G": "▀",
        "B": "▀",
        "g": "▄",
        "b": "▄",
    }
    return [
        "".join(
            source if rendered_markers.get(source) == imported else imported
            for source, imported in zip(source_row, imported_row)
        )
        for source_row, imported_row in zip(variant.cells, cells)
    ]


def segment_rexpaint_cells(
    cells: list[str],
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
) -> list[tuple[Variant, list[str]]]:
    """Split a just-exported grid back into its active editable variants.

    The imported image must match the current render request exactly. Each
    repeated copy of one active variant must also be identical, since a section
    has only one editable source variant.
    """

    if len(cells) != height or any(len(row) != width for row in cells):
        raise RexPaintImportError(
            f"imported image is {max(map(len, cells), default=0)}x{len(cells)}, "
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
    repeats = _repeat_counts(
        tier.sections, variants, width if horizontal else height, horizontal=horizontal
    )

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

    rows = list(cells)
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        rows = flip_rows_horizontal(rows) if horizontal else flip_rows_vertical(rows)
    left = (width - natural_width) // 2
    top = (height - natural_height) // 2
    segments: list[tuple[Variant, list[str]]] = []
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
            if any(copy != copies[0] for copy in copies[1:]):
                raise RexPaintImportError(
                    f"active variant {variant.id!r} has edited repeated copies; make them match"
                )
            segments.append((variant, _restore_semantic_markers(variant, copies[0])))
            cursor += variant.width * repeat
    else:
        cursor = top
        for variant, repeat in reversed(list(zip(variants, repeats))):
            copies = [rows[cursor + copy * variant.height : cursor + (copy + 1) * variant.height]
                      for copy in range(repeat)]
            if any(copy != copies[0] for copy in copies[1:]):
                raise RexPaintImportError(
                    f"active variant {variant.id!r} has edited repeated copies; make them match"
                )
            segments.append((variant, _restore_semantic_markers(variant, copies[0])))
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
        preserve_authoring_markers=True,
    )
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_bytes(rexpaint_bytes(rendered, width=width, height=height))
    temporary.replace(target)
    return target
