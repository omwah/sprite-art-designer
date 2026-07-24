"""Closed structural glyph alphabet and geometric transforms."""

from __future__ import annotations

from collections.abc import Mapping

ROTATION_FALLBACK = "◇"

BRIGHT_CHARS = frozenset("█")
DARK_CHARS = frozenset("▒░")
MID_CHARS = frozenset(
    "▟▙▜▛▓▄▀▌▐╾╼╽╿╻╹╺╸─│◢◣◥◤▴▾"
    "┌┐└┘├┤┬┴▤▦═║╱╲"
)
HULL_CHARS = BRIGHT_CHARS | DARK_CHARS | MID_CHARS

AUTHORING_GLYPHS: tuple[tuple[str, str], ...] = (
    (" ", "Void"),
    ("█", "Bright plating"),
    ("▓", "Mid plating"),
    ("▒", "Dark plating"),
    ("░", "Deep recess"),
    ("▄", "Lower half"),
    ("▀", "Upper half"),
    ("▌", "Left half"),
    ("▐", "Right half"),
    ("▟", "Bevel"),
    ("▙", "Bevel"),
    ("▜", "Bevel"),
    ("▛", "Bevel"),
    ("─", "Light beam"),
    ("│", "Light beam"),
    ("═", "Heavy beam"),
    ("║", "Heavy beam"),
    ("╾", "Tapered beam"),
    ("╼", "Tapered beam"),
    ("╽", "Tapered beam"),
    ("╿", "Tapered beam"),
    ("╺", "Heavy half beam"),
    ("╸", "Heavy half beam"),
    ("┌", "Corner"),
    ("┐", "Corner"),
    ("└", "Corner"),
    ("┘", "Corner"),
    ("├", "Junction"),
    ("┤", "Junction"),
    ("┬", "Junction"),
    ("┴", "Junction"),
    ("◢", "Facet edge"),
    ("◣", "Facet edge"),
    ("◥", "Facet edge"),
    ("◤", "Facet edge"),
    ("▶", "Muzzle"),
    ("◀", "Muzzle"),
    ("▴", "Muzzle"),
    ("▾", "Muzzle"),
    ("╱", "Diagonal"),
    ("╲", "Diagonal"),
    ("R", "Beacon marker"),
    ("Y", "Engine marker"),
    ("◇", "Facet"),
    ("◆", "Facet"),
    ("◊", "Facet"),
    ("☉", "Facet"),
    ("°", "Facet"),
    ("≡", "Facet"),
    ("⁐", "Facet"),
)


def _cycles(*cycles: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for cycle in cycles:
        for index, glyph in enumerate(cycle):
            result[glyph] = cycle[(index + 1) % len(cycle)]
    return result


# Each value is the source glyph rotated 90 degrees counter-clockwise.
ROTATE_CCW: dict[str, str] = {
    **_cycles(
        "─│",
        "═║",
        "╾╽╼╿",
        "╻╺╹╸",
        "▄▐▀▌",
        "▟▜▛▙",
        "◢◥◤◣",
        "┌└┘┐",
        "├┴┤┬",
        "▶▴◀▾",
        "►▲◄▼",
        "▬▮",
        "╱╲",
    ),
}
for _glyph in " █▓▒░R Y◇◆◊☉°◘◙":
    ROTATE_CCW[_glyph] = _glyph
ROTATE_CCW["≡"] = "║"
ROTATE_CCW["⁐"] = ROTATION_FALLBACK


HORIZONTAL_FLIP: dict[str, str] = {}
for _left, _right in (
    ("▟", "▙"),
    ("▜", "▛"),
    ("╾", "╼"),
    ("╽", "╽"),
    ("╿", "╿"),
    ("╺", "╸"),
    ("◢", "◣"),
    ("◥", "◤"),
    ("┌", "┐"),
    ("└", "┘"),
    ("├", "┤"),
    ("▶", "◀"),
    ("►", "◄"),
    ("▴", "▴"),
    ("▾", "▾"),
    ("▲", "▲"),
    ("▼", "▼"),
    ("▌", "▐"),
    ("╱", "╲"),
):
    HORIZONTAL_FLIP[_left] = _right
    HORIZONTAL_FLIP[_right] = _left


VERTICAL_FLIP: dict[str, str] = {}
for _top, _bottom in (
    ("▟", "▜"),
    ("▙", "▛"),
    ("╽", "╿"),
    ("╻", "╹"),
    ("◢", "◥"),
    ("◣", "◤"),
    ("┌", "└"),
    ("┐", "┘"),
    ("┬", "┴"),
    ("▴", "▾"),
    ("▲", "▼"),
    ("▄", "▀"),
    ("R", "r"),
    ("Y", "y"),
    ("╱", "╲"),
):
    VERTICAL_FLIP[_top] = _bottom
    VERTICAL_FLIP[_bottom] = _top


def transform_glyph(
    glyph: str,
    table: Mapping[str, str],
    fallback: str | None = None,
) -> str:
    if glyph in table:
        return table[glyph]
    return glyph if fallback is None else fallback


def flip_rows_horizontal(rows: list[str]) -> list[str]:
    return [
        "".join(HORIZONTAL_FLIP.get(glyph, glyph) for glyph in reversed(row))
        for row in rows
    ]


def flip_rows_vertical(rows: list[str]) -> list[str]:
    return [
        "".join(VERTICAL_FLIP.get(glyph, glyph) for glyph in row)
        for row in reversed(rows)
    ]
