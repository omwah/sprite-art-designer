"""Migrate schema-v1 marker glyphs and palettes to schema-v2 color masks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"

MARKERS: dict[str, tuple[str, str]] = {
    "R": ("▀", "B"),
    "r": ("▄", "B"),
    "Y": ("▀", "E"),
    "y": ("▄", "E"),
    "G": ("▀", "A"),
    "g": ("▄", "A"),
    "B": ("▀", "D"),
    "b": ("▄", "D"),
}


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _migrate_sprite(path: Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return False
    for view in data.get("views", {}).values():
        for tier in view.get("tiers", []):
            for section in tier.get("sections", []):
                for variant in section.get("variants", []):
                    cells: list[str] = variant["cells"]
                    migrated_cells: list[str] = []
                    color_mask: list[str] = []
                    for row in cells:
                        glyphs: list[str] = []
                        colors: list[str] = []
                        for glyph in row:
                            replacement, code = MARKERS.get(glyph, (glyph, "S"))
                            glyphs.append(replacement)
                            colors.append(code)
                        migrated_cells.append("".join(glyphs))
                        color_mask.append("".join(colors))
                    variant["cells"] = migrated_cells
                    variant["color_mask"] = color_mask
    data["schema_version"] = 2
    _write_yaml(path, data)
    return True


def _migrate_palettes(path: Path) -> bool:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return False
    for palette in data.get("archetypes", {}).values():
        palette["color_sets"] = {
            "surface": [
                palette.pop("bright"),
                palette.pop("mid"),
                palette.pop("dark"),
                palette.pop("facet"),
            ],
            "engine": palette.pop("engine"),
            "beacon": palette.pop("beacon"),
            "window": palette.pop("window"),
            "weapons": ["#22c55e"],
            "defensive": ["#3b82f6"],
        }
    data["schema_version"] = 2
    _write_yaml(path, data)
    return True


def main() -> None:
    migrated = sum(
        _migrate_sprite(path) for path in sorted((ASSETS / "sprites").rglob("*.yaml"))
    )
    migrated += _migrate_palettes(ASSETS / "palettes.yaml")
    print(f"Migrated {migrated} asset files to schema version 2")


if __name__ == "__main__":
    main()
