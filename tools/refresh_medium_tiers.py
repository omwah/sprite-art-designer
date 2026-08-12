"""Generate five-cell Medium tiers and regenerate vertical ship views."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from sprite_art import Tier, dump_sprite, load_sprite
from sprite_art_authoring import generate_rotated_view


def _fit_rows(cells: list[str], height: int, fill: str = " ") -> list[str]:
    """Center-crop or pad a rectangular horizontal-art variant to ``height``."""

    current_height = len(cells)
    width = len(cells[0])
    if current_height > height:
        start = (current_height - height) // 2
        return cells[start : start + height]
    if current_height < height:
        padding = height - current_height
        top = padding // 2
        return [fill * width] * top + cells + [fill * width] * (padding - top)
    return list(cells)


def _resize_tier(tier: Tier, height: int) -> None:
    for section in tier.sections:
        for variant in section.variants:
            variant.cells = _fit_rows(variant.cells, height)
            variant.color_mask = _fit_rows(variant.color_mask, height, "S")


def _scale_columns(cells: list[str], numerator: int, denominator: int) -> list[str]:
    """Resample rows while preserving the leftmost and rightmost glyphs."""

    width = len(cells[0])
    target_width = max(1, (width * numerator + denominator // 2) // denominator)
    if target_width == width:
        return list(cells)
    if target_width == 1:
        indices = [width // 2]
    else:
        indices = [
            index * (width - 1) // (target_width - 1)
            for index in range(target_width)
        ]
    return ["".join(row[index] for index in indices) for row in cells]


def _medium_tier(full: Tier) -> Tier:
    medium = deepcopy(full)
    medium.id = "medium"
    medium.name = "Medium"
    _resize_tier(medium, 5)
    for section in medium.sections:
        for variant in section.variants:
            variant.cells = _scale_columns(variant.cells, 3, 4)
            variant.color_mask = _scale_columns(variant.color_mask, 3, 4)
    return medium


def refresh_ship(path: Path) -> int:
    """Refresh one ship YAML asset and return its rotation-warning count."""

    sprite = load_sprite(path)
    horizontal = sprite.views["horizontal"]
    full = next(tier for tier in horizontal.tiers if tier.id == "full")
    medium = _medium_tier(full)
    _resize_tier(full, 7)
    horizontal.tiers = [
        full,
        medium,
        *(tier for tier in horizontal.tiers if tier.id not in {"full", "medium"}),
    ]
    vertical, warnings = generate_rotated_view(sprite)
    sprite.views["vertical"] = vertical
    sprite.validate()
    dump_sprite(sprite, path)
    return len(warnings)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_root", type=Path, nargs="?", default=Path("assets"))
    args = parser.parse_args()
    paths = sorted((args.asset_root / "sprites" / "ships").glob("*.yaml"))
    warning_count = sum(refresh_ship(path) for path in paths)
    print(f"Refreshed {len(paths)} ships ({warning_count} rotation warnings).")


if __name__ == "__main__":
    main()
