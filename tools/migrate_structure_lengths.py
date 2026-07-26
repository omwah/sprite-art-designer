"""Migrate ship tiers from repeat ranges to explicit structure lengths."""

from __future__ import annotations

from pathlib import Path

import yaml


STANDARD_LENGTHS = {3: 18, 5: 30, 7: 40, 12: 56}


def counts(sections: list[dict[str, object]], target: int, vertical: bool) -> dict[str, int]:
    sizes = [len(section["variants"][0]["cells"]) if vertical else len(section["variants"][0]["cells"][0]) for section in sections]
    result = [int(section["repeat"]["min"]) for section in sections]
    total = sum(size * count for size, count in zip(sizes, result))
    while True:
        changed = False
        for index, section in enumerate(sections):
            maximum = int(section["repeat"]["max"])
            if result[index] < maximum and total + sizes[index] <= target:
                result[index] += 1
                total += sizes[index]
                changed = True
        if not changed:
            return {str(section["id"]): count for section, count in zip(sections, result)}


for path in Path("assets/sprites/ships").glob("*.yaml"):
    data = yaml.safe_load(path.read_text())
    for view in data["views"].values():
        vertical = view["axis"] == "vertical"
        for tier in view["tiers"]:
            cross = len(tier["sections"][0]["variants"][0]["cells"][0]) if vertical else len(tier["sections"][0]["variants"][0]["cells"])
            tier["structure_lengths"] = counts(tier["sections"], STANDARD_LENGTHS.get(cross, 40), vertical)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
