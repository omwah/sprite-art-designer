"""The legacy glyph markers shared by the Edge art importers.

Edge's in-code grammars encode a cell's semantic color inside the glyph string:
``R`` is an upper-half red beacon block, ``Y`` a lower-half yellow engine glow,
and so on. Sprite documents store geometry and color as separate parallel grids,
so importing splits each marker into its real glyph and its color-mask code.
"""

from __future__ import annotations

LEGACY_MARKERS: dict[str, tuple[str, str]] = {
    "R": ("▀", "B"),
    "r": ("▄", "B"),
    "Y": ("▀", "E"),
    "y": ("▄", "E"),
    "G": ("▀", "A"),
    "g": ("▄", "A"),
    "B": ("▀", "D"),
    "b": ("▄", "D"),
}

HULL_MARKERS: dict[str, tuple[str, str]] = {
    "R": ("▀", "B"),
    "Y": ("▄", "E"),
}
"""Markers as ``edge.art.hull.render_grid`` paints them, for station art.

That painter is unconditional: ``R`` becomes an upper-half block in the beacon
hue and ``Y`` a lower-half block in the engine hue.

``LEGACY_MARKERS`` above deliberately departs from it, pairing each marker's
upper- and lower-half form by letter case so ship art can pick the half that
reads best. Stations keep the painter's own mapping instead, because a station's
glow sits on its bottom row: a lower-half block is flush with the foot of the
silhouette, while an upper-half one leaves a gap beneath the drive."""


def migrate_rows(
    rows: tuple[str, ...] | list[str],
    markers: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[str], list[str]]:
    """Split marker-bearing rows into parallel glyph and color-mask grids."""

    table = LEGACY_MARKERS if markers is None else markers
    cells = [
        "".join(table.get(glyph, (glyph, "S"))[0] for glyph in row) for row in rows
    ]
    color_mask = [
        "".join(table.get(glyph, (glyph, "S"))[1] for glyph in row) for row in rows
    ]
    return cells, color_mask
