"""Migrate schema-v2 repeat ranges and tier lengths to fixed Section repeats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def migrate_sprite(data: dict[str, Any]) -> dict[str, Any]:
    """Return one schema-v3 sprite with a single fixed repeat per Section."""

    if int(data.get("schema_version", 0)) != 2:
        raise ValueError("fixed-repetition migration requires sprite schema version 2")
    for view in data["views"].values():
        for tier in view["tiers"]:
            lengths = tier.pop("structure_lengths", {})
            for section in tier["sections"]:
                old_repeat = section.get("repeat", {})
                fallback = old_repeat.get("min", 1)
                section["repeat"] = int(lengths.get(section["id"], fallback))
    data["schema_version"] = 3
    return data


def main() -> None:
    for path in sorted(Path("assets/sprites").rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        migrated = migrate_sprite(data)
        path.write_text(
            yaml.safe_dump(
                migrated,
                allow_unicode=True,
                sort_keys=False,
                width=1000,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
