"""Authoring transforms that create independently editable sprite views."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from sprite_art.glyphs import ROTATE_CCW, ROTATION_FALLBACK
from sprite_art.model import Sprite, View


@dataclass(frozen=True)
class RotationWarning:
    tier_id: str
    section_id: str
    variant_id: str
    glyph: str
    column: int
    row: int


def _rotate_cells_ccw(
    cells: list[str],
    *,
    tier_id: str,
    section_id: str,
    variant_id: str,
) -> tuple[list[str], list[RotationWarning]]:
    height = len(cells)
    width = len(cells[0])
    output = [[" " for _ in range(height)] for _ in range(width)]
    warnings: list[RotationWarning] = []
    for row, line in enumerate(cells):
        for column, glyph in enumerate(line):
            replacement = ROTATE_CCW.get(glyph)
            if replacement is None:
                replacement = ROTATION_FALLBACK
            if replacement == ROTATION_FALLBACK and glyph != ROTATION_FALLBACK:
                warnings.append(
                    RotationWarning(
                        tier_id=tier_id,
                        section_id=section_id,
                        variant_id=variant_id,
                        glyph=glyph,
                        column=column,
                        row=row,
                    )
                )
            output[width - 1 - column][row] = replacement
    return ["".join(line) for line in output], warnings


def _compact_rotated_cells_for_terminal_aspect(cells: list[str]) -> list[str]:
    """Fit a 90-degree rotation to 1:2 terminal cells with compact resampling.

    A literal cell-grid rotation maps a source ``W×H`` shape to ``H×W`` cells.
    The compact aspect-corrected result is ``2H×ceil(W/2)``: each rotated cell
    is doubled horizontally, then every other row is retained. This deliberately
    lossy downsampling keeps generated editable views practical in a TUI.
    """

    expanded = ["".join(glyph * 2 for glyph in row) for row in cells]
    return expanded[::2]


def _rotate_mask_ccw(rows: list[str]) -> list[str]:
    height = len(rows)
    width = len(rows[0])
    output = [[" " for _ in range(height)] for _ in range(width)]
    for row, line in enumerate(rows):
        for column, code in enumerate(line):
            output[width - 1 - column][row] = code
    return ["".join(line) for line in output]


def generate_rotated_view(
    sprite: Sprite,
    source_view_id: str = "horizontal",
    target_view_id: str = "vertical",
) -> tuple[View, list[RotationWarning]]:
    """Create a stored, editable nose-up view from a horizontal nose-right view."""

    source = sprite.views[source_view_id]
    if source.axis != "horizontal":
        raise ValueError("automatic vertical generation requires a horizontal source")
    target = deepcopy(source)
    target.id = target_view_id
    target.name = target_view_id.replace("_", " ").title()
    target.axis = "vertical"
    target.canonical_facing = "up"
    target.mirror_facing = "down"
    warnings: list[RotationWarning] = []
    for tier in target.tiers:
        for section in tier.sections:
            for variant in section.variants:
                rotated_cells, variant_warnings = _rotate_cells_ccw(
                    variant.cells,
                    tier_id=tier.id,
                    section_id=section.id,
                    variant_id=variant.id,
                )
                variant.cells = _compact_rotated_cells_for_terminal_aspect(
                    rotated_cells
                )
                variant.color_mask = _compact_rotated_cells_for_terminal_aspect(
                    _rotate_mask_ccw(variant.color_mask)
                )
                warnings.extend(variant_warnings)
    target.validate(sprite.id)
    return target, warnings
