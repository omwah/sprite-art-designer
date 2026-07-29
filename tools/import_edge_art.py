"""Translate Edge of the Unknown's in-code ship grammars into sprite-art YAML.

This development utility intentionally imports the read-only reference checkout.
The generated YAML has no runtime dependency on that checkout.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from sprite_art import (
    ColorSet,
    Palette,
    PaletteCatalog,
    Section,
    Sprite,
    Tier,
    Variant,
    View,
    dump_palette_catalog,
    dump_sprite,
    generate_rotated_view,
)
from sprite_art.model import SCHEMA_VERSION

LEGACY_MARKERS = {
    "R": ("▀", "B"),
    "r": ("▄", "B"),
    "Y": ("▀", "E"),
    "y": ("▄", "E"),
    "G": ("▀", "A"),
    "g": ("▄", "A"),
    "B": ("▀", "D"),
    "b": ("▄", "D"),
}
DEFENSIVE_COLORS = {
    "humanoid_diplomat": "#60a5fa",
    "canid_technologist": "#2563eb",
    "tentacled_envoy": "#22d3ee",
    "brain_dome_automaton": "#38bdf8",
    "ribbon_salvager": "#1d4ed8",
    "temporal_broker": "#818cf8",
    "cosmic_arbiter": "#0ea5e9",
    "telepath_aristocrat": "#6366f1",
    "engineered_aesthete": "#3b82f6",
    "amorous_imp": "#7dd3fc",
    "horned_grudgekeeper": "#0284c7",
    "psionic_overlord": "#4f46e5",
    "colonial_broodmaster": "#93c5fd",
    "winged_schemer": "#0891b2",
}


def _migrate_rows(rows: tuple[str, ...]) -> tuple[list[str], list[str]]:
    cells = ["".join(LEGACY_MARKERS.get(glyph, (glyph, "S"))[0] for glyph in row) for row in rows]
    color_mask = [
        "".join(LEGACY_MARKERS.get(glyph, (glyph, "S"))[1] for glyph in row) for row in rows
    ]
    return cells, color_mask


FULL_SECTIONS = (
    ("thrusters", "Thrusters", "thrusters"),
    ("spindrive", "Spindrive", "spindrive"),
    ("hull", "Hull", "hull"),
    ("screens", "Screens", "screens"),
    ("main_gun", "Main Gun", "main_gun"),
)
COMPACT_SECTIONS = (
    ("thrusters", "Thrusters", "thrusters"),
    ("hull", "Hull", "hull"),
    ("main_gun", "Main Gun", "main_gun"),
)


def _tier(source_slots: tuple[Any, ...], index: int) -> Tier:
    definitions = FULL_SECTIONS if len(source_slots) == 5 else COMPACT_SECTIONS
    sections: list[Section] = []
    for slot_index, (slot, definition) in enumerate(zip(source_slots, definitions)):
        section_id, name, property_id = definition
        sections.append(
            Section(
                id=section_id,
                name=name,
                primary_property=property_id,
                repeat=int(slot.min_repeat),
                variants=[
                    Variant(
                        id=f"{section_id}_{variant_index + 1}",
                        cells=_migrate_rows(part.left)[0],
                        color_mask=_migrate_rows(part.left)[1],
                    )
                    for variant_index, part in enumerate(slot.parts)
                ],
            )
        )
    return Tier(
        id="full" if index == 0 else "compact",
        name="Full Detail" if index == 0 else "Compact",
        sections=sections,
    )


def _sprite(role: str, tiers: tuple[tuple[Any, ...], ...]) -> Sprite:
    sprite = Sprite(
        schema_version=SCHEMA_VERSION,
        id=role,
        name=role.replace("_", " ").title(),
        kind="ship",
        role=role,
        description="Translated from Edge of the Unknown's original ship grammar.",
        views={
            "horizontal": View(
                id="horizontal",
                name="Horizontal",
                axis="horizontal",
                canonical_facing="right",
                mirror_facing="left",
                tiers=[_tier(source_tier, index) for index, source_tier in enumerate(tiers)],
            )
        },
    )
    vertical, _warnings = generate_rotated_view(sprite)
    sprite.views["vertical"] = vertical
    sprite.validate()
    return sprite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("edge_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path("assets"))
    args = parser.parse_args()

    sys.path.insert(0, str(args.edge_path.resolve()))
    from edge.art.hull import ARCHETYPE_STYLES  # noqa: PLC0415
    from edge.art.ship import SHIP_GRAMMAR  # noqa: PLC0415

    output = args.output
    palettes = PaletteCatalog(
        schema_version=2,
        archetypes={
            archetype_id: Palette(
                color_sets={
                    "surface": ColorSet([style.bright, style.mid, style.dark, style.facet]),
                    "engine": ColorSet(list(style.bottom)),
                    "beacon": ColorSet(list(style.top)),
                    "window": ColorSet(list(style.window)),
                    "weapons": ColorSet(["#DF7070"]),
                    "defensive": ColorSet([DEFENSIVE_COLORS.get(archetype_id, "#60a5fa")]),
                }
            )
            for archetype_id, style in ARCHETYPE_STYLES.items()
            if archetype_id != "default"
        },
    )
    dump_palette_catalog(palettes, output / "palettes.yaml")
    for role, tiers in SHIP_GRAMMAR.items():
        dump_sprite(
            _sprite(role, tiers),
            output / "sprites" / "ships" / f"{role}.yaml",
        )


if __name__ == "__main__":
    main()
