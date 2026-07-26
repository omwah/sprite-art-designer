"""Closed structural glyph alphabet and geometric transforms."""

from __future__ import annotations

from collections.abc import Mapping

ROTATION_FALLBACK = "◇"
SEMANTIC_GLYPHS = frozenset({"R", "Y", "G", "B", "r", "y", "g", "b"})
"""Authoring glyphs rendered as colored beacon, engine, or signal effects."""

BRIGHT_CHARS = frozenset("█■")
DARK_CHARS = frozenset("▒░")
MID_CHARS = frozenset(
    "▟▙▜▛▓▄▀▌▐╾╼╽╿╻╹╺╸─│◢◣◥◤▴▾"
    "┌┐└┘├┤┬┴┼▤▦═║╔╗╚╝╠╣╦╩╬"
    "╡╢╖╕╜╛╧╨╤╥╙╘╒╓╫╪╞╟▬▮╱╲"
)
HULL_CHARS = BRIGHT_CHARS | DARK_CHARS | MID_CHARS

AUTHORING_GLYPHS: tuple[tuple[str, str], ...] = (
    (" ", "Void"),
    ("█", "Bright plating"),
    ("▓", "Mid plating"),
    ("▒", "Dark plating"),
    ("░", "Deep recess"),
    ("■", "Bright plating"),
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
    ("┼", "Cross junction"),
    ("▤", "Structural hull"),
    ("▦", "Structural hull"),
    ("╔", "Double corner"),
    ("╗", "Double corner"),
    ("╚", "Double corner"),
    ("╝", "Double corner"),
    ("╠", "Double junction"),
    ("╣", "Double junction"),
    ("╦", "Double junction"),
    ("╩", "Double junction"),
    ("╬", "Double cross junction"),
    ("╞", "Mixed junction"),
    ("╟", "Mixed junction"),
    ("╡", "Mixed junction"),
    ("╢", "Mixed junction"),
    ("╖", "Mixed corner"),
    ("╕", "Mixed corner"),
    ("╜", "Mixed corner"),
    ("╛", "Mixed corner"),
    ("╧", "Mixed junction"),
    ("╨", "Mixed junction"),
    ("╤", "Mixed junction"),
    ("╥", "Mixed junction"),
    ("╙", "Mixed corner"),
    ("╘", "Mixed corner"),
    ("╒", "Mixed corner"),
    ("╓", "Mixed corner"),
    ("╫", "Mixed cross junction"),
    ("╪", "Mixed cross junction"),
    ("▬", "Heavy beam"),
    ("▮", "Vertical heavy beam"),
    ("▶", "Muzzle"),
    ("◀", "Muzzle"),
    ("►", "Muzzle"),
    ("◄", "Muzzle"),
    ("▴", "Muzzle"),
    ("▾", "Muzzle"),
    ("↑", "Arrow"),
    ("↓", "Arrow"),
    ("→", "Arrow"),
    ("←", "Arrow"),
    ("↔", "Double arrow"),
    ("↕", "Double arrow"),
    ("▲", "Muzzle"),
    ("▼", "Muzzle"),
    ("╱", "Diagonal"),
    ("╲", "Diagonal"),
    ("◇", "Facet"),
    ("◆", "Facet"),
    ("◊", "Facet"),
    ("☉", "Facet"),
    ("°", "Facet"),
    ("≡", "Facet"),
    ("◘", "Facet"),
    ("◙", "Facet"),
    ("☼", "Facet"),
    ("•", "Facet"),
    ("○", "Facet"),
    ("♥", "Facet"),
    ("♦", "Facet"),
    ("♣", "Facet"),
    ("♠", "Facet"),
    ("∩", "Facet"),
    ("∞", "Facet"),
    ("⌐", "Facet"),
    ("¬", "Facet"),
    ("R", "Palette beacon marker (upper signal)"),
    ("G", "Always-green signal marker (upper signal)"),
    ("B", "Always-blue signal marker (upper signal)"),
    ("Y", "Palette engine marker (upper signal)"),
    ("r", "Palette beacon marker (lower signal)"),
    ("g", "Always-green signal marker (lower signal)"),
    ("b", "Always-blue signal marker (lower signal)"),
    ("y", "Palette engine marker (lower signal)"),
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
        "╔╚╝╗",
        "╠╩╣╦",
        "╞╨╢╥",
        "╟╧╡╤",
        "╖╒╘╛",
        "╕╓╙╜",
        "╫╪",
        "▶▴◀▾",
        "►▲◄▼",
        "→↑←↓",
        "↔↕",
        "▬▮",
        "╱╲",
    ),
}
for _glyph in " █■▓▒░RrYyGBgb◇◆◊☉°◘◙☼•○♥♦♣♠∩∞⌐¬┼▤▦╬":
    ROTATE_CCW[_glyph] = _glyph
ROTATE_CCW["≡"] = "║"


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
    ("╔", "╗"),
    ("╚", "╝"),
    ("╠", "╣"),
    ("╞", "╢"),
    ("╟", "╡"),
    ("╖", "╓"),
    ("╕", "╒"),
    ("╜", "╘"),
    ("╛", "╙"),
    ("▶", "◀"),
    ("►", "◄"),
    ("→", "←"),
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
    ("╔", "╚"),
    ("╗", "╝"),
    ("╦", "╩"),
    ("╖", "╜"),
    ("╕", "╛"),
    ("╒", "╘"),
    ("╓", "╙"),
    ("╧", "╤"),
    ("╨", "╥"),
    ("┬", "┴"),
    ("▴", "▾"),
    ("▲", "▼"),
    ("↑", "↓"),
    ("▄", "▀"),
    ("R", "r"),
    ("Y", "y"),
    ("G", "g"),
    ("B", "b"),
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
