# Edge Art Designer REXPaint font map

`sprite_art.rexpaint.REXPAINT_GLYPH_INDICES` writes the following glyph indices
to `.xp` files. `edge-art-designer.png` is a 16-column art-font sheet whose
cells use these indices in reading order.

| Index | Glyph | Meaning |
| ---: | :---: | --- |
| 0 | space | Void |
| 1–5 | █ ■ ▓ ▒ ░ | Hull tones |
| 6–9 | ▄ ▀ ▌ ▐ | Half blocks |
| 10–15 | ▖ ▗ ▘ ▝ ▚ ▞ | Quarter blocks and diagonal splits |
| 16–19 | ▟ ▙ ▜ ▛ | Three-quarter bevels |
| 20–23 | ◢ ◣ ◥ ◤ | Half-cell facet edges |
| 24–27 | ╭ ╮ ╰ ╯ | Rounded corners |
| 28–39 | ─ │ ═ ║ ╾ ╼ ╽ ╿ ╻ ╹ ╺ ╸ | Beams |
| 40–50 | ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ▤ ▦ | Single-line junctions and structural hulls |
| 51–59 | ╔ ╗ ╚ ╝ ╠ ╣ ╦ ╩ ╬ | Double-line boxes and junctions |
| 60–77 | ╞ ╟ ╡ ╢ ╖ ╕ ╜ ╛ ╧ ╨ ╤ ╥ ╙ ╘ ╒ ╓ ╫ ╪ | Mixed-line pipes |
| 78–93 | ▬ ▮ ▶ ◀ ► ◄ ▴ ▾ ↑ ↓ → ← ↔ ↕ ▲ ▼ | Beams, muzzles, and arrows |
| 94–95 | ╱ ╲ | Diagonals |
| 96–114 | ◇ ◆ ◊ ☉ ° ≡ ◘ ◙ ☼ • ○ ♥ ♦ ♣ ♠ ∩ ∞ ⌐ ¬ | Facets |

Install the PNG as an **art** font, not as REXPaint's GUI font. It must remain a
16-column sheet; REXPaint 1.50+ supports the required extra rows. The exported
file references the glyph indices above, so switching to a different art font
changes its appearance.

## Install in REXPaint

1. Close REXPaint.
2. Copy these three files into REXPaint's `data/fonts/` directory:

   ```text
   edge-art-designer.png
   edge-art-designer-gui.png
   edge-art-designer-unicode.txt
   edge-art-designer-mirror.txt
   ```

3. Open `data/fonts/_config.xt` and add this row. It retains REXPaint's standard
   matching Edge GUI font while selecting the Edge atlas as the art font:

   ```text
   "Edge Art Designer 10x20"  edge-art-designer-gui  16  16  edge-art-designer  16  8  edge-art-designer-unicode  edge-art-designer-mirror  1
   ```

4. Restart REXPaint and choose **Edge Art Designer 10x20** with the font
   controls (`Ctrl+Page Up` / `Ctrl+Page Down`, or `<` / `>`).

The Unicode map labels the atlas slots with the glyphs in this document. The
mirror map makes REXPaint's horizontal and vertical flip commands use the same
glyph-aware pairs as Edge Art Designer. Keep these files and the PNG together;
an `.xp` export stores slot indices, not the font artwork.

Each `.xp` export is accompanied by a native palette text file. Copy it to
REXPaint's `data/palettes/` directory; its first six rows contain Surface,
Engine, Beacon, Window, Weapons, and Defensive colors respectively.

The atlas uses narrow 10×20 cells to match terminal proportions. It is generated
from REXPaint's edge-aligned 8×16 CP437 bitmap cells; regenerate it with
`tools/generate_rexpaint_font.py` when the glyph map changes.
