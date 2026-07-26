"""Build the narrow REXPaint font atlas from an aligned CP437 bitmap font."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from sprite_art.rexpaint import REXPAINT_GLYPH_INDICES

CELL_WIDTH = 10
CELL_HEIGHT = 20
COLUMNS = 16
FALLBACK_FONT = "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"
CONTROL_GLYPHS = "☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼"


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def _cp437_slots() -> dict[str, int]:
    characters = list(bytes(range(32, 256)).decode("cp437"))
    slots = {glyph: index + 32 for index, glyph in enumerate(characters)}
    slots.update({glyph: index for index, glyph in enumerate(CONTROL_GLYPHS)})
    return slots


def _font_cell(font: Path, slot: int, destination: Path) -> None:
    source_x = slot % COLUMNS * 8
    source_y = slot // COLUMNS * 16
    _run(
        "convert",
        str(font),
        "-crop",
        f"8x16+{source_x}+{source_y}",
        "-filter",
        "point",
        "-resize",
        f"{CELL_WIDTH}x{CELL_HEIGHT}!",
        str(destination),
    )


def _fallback_cell(glyph: str, destination: Path) -> None:
    _run(
        "convert",
        "-size",
        f"{CELL_WIDTH}x{CELL_HEIGHT}",
        "xc:black",
        "-font",
        FALLBACK_FONT,
        "-pointsize",
        "14",
        "-fill",
        "white",
        "-gravity",
        "center",
        "-annotate",
        "0",
        glyph,
        str(destination),
    )


def _composite_cell(canvas: Path, cell: Path, index: int) -> None:
    x = index % COLUMNS * CELL_WIDTH
    y = index // COLUMNS * CELL_HEIGHT
    _run("convert", str(canvas), str(cell), "-geometry", f"+{x}+{y}", "-composite", str(canvas))


def build(source_font: Path, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    output = output_directory / "edge-art-designer.png"
    gui_output = output_directory / "edge-art-designer-gui.png"
    glyph_count = len(REXPAINT_GLYPH_INDICES)
    rows = (glyph_count + COLUMNS - 1) // COLUMNS
    slots = _cp437_slots()

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary = Path(temporary_directory)
        canvas = temporary / "atlas.png"
        _run("convert", "-size", f"{COLUMNS * CELL_WIDTH}x{rows * CELL_HEIGHT}", "xc:black", str(canvas))
        for glyph, index in REXPAINT_GLYPH_INDICES.items():
            cell = temporary / f"{index}.png"
            slot = slots.get(glyph)
            if slot is None:
                _fallback_cell(glyph, cell)
            else:
                _font_cell(source_font, slot, cell)
            _composite_cell(canvas, cell, index)
        shutil.copyfile(canvas, output)

    _run(
        "convert",
        str(source_font),
        "-filter",
        "point",
        "-resize",
        f"{COLUMNS * CELL_WIDTH}x{COLUMNS * CELL_HEIGHT}!",
        str(gui_output),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_font", type=Path, help="An 8x16 CP437 REXPaint font sheet")
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("assets/rexpaint"),
        help="Directory for the generated art and GUI font sheets",
    )
    args = parser.parse_args()
    build(args.source_font, args.output_directory)


if __name__ == "__main__":
    main()
