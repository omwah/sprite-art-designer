"""Migrate schema-v3 sprites to v4 by recording their vertical section order.

Schema v4 adds three optional authoring fields: ``Variant.archetypes``,
``Section.archetype_repeats``, and ``View.section_order``. The first two default
to empty and need no migration. The third does: v3 renderers always reversed a
vertical view's sections, because every vertical view in the tree was generated
by rotating tail-to-nose horizontal art. That reversal is now recorded on the
view instead of hardcoded in the composer, so existing vertical views must
declare ``section_order: reversed`` to keep rendering identically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def migrate_sprite(data: dict[str, Any]) -> dict[str, Any]:
    """Return one schema-v4 sprite with its section order made explicit."""

    if int(data.get("schema_version", 0)) != 3:
        raise ValueError("v4 migration requires sprite schema version 3")
    for view in data["views"].values():
        if view.get("axis") != "vertical":
            continue
        # Rebuild the mapping so the new key lands before ``tiers`` rather than
        # after the sprite's entire body of art.
        ordered: dict[str, Any] = {}
        for key, value in view.items():
            if key == "tiers":
                ordered["section_order"] = "reversed"
            ordered[key] = value
        view.clear()
        view.update(ordered)
    data["schema_version"] = 4
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
