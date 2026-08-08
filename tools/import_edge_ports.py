"""Translate Edge of the Unknown's in-code port grammars into sprite-art YAML.

This development utility intentionally imports the read-only reference checkout.
The generated YAML has no runtime dependency on that checkout.

Four things change on the way across:

* **Symmetry is consumed here.** Edge authors a port as its left half and
  mirrors it at render time. Sprite documents store plain, full-width rows, so
  every part is expanded through ``port._mirror_row`` exactly once, at import.
* **Archetypes fold into one document.** Edge nests
  ``subtype -> archetype -> tiers`` and swaps the whole grammar per species.
  Slots are positional, so slot *i* of every archetype becomes section *i*, with
  each archetype's parts tagged via ``Variant.archetypes`` and the ``default``
  parts left un-tagged as the fallback art.
* **Growth becomes tiers.** Edge tiles a repeatable slot to fill the requested
  height. Sprite documents use authored repeats, so the repeatable band is
  frozen at three heights: ``full``, ``medium``, and ``compact``.
* **Rectangles are made uniform.** Mirroring yields ragged widths and Edge's
  slots hold parts of differing heights, neither of which the schema allows.

Run ``--audit`` to print the resulting tier ladder against the boxes Edge asks
for, without writing anything.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from sprite_art import Section, Sprite, Tier, Variant, View, dump_sprite
from sprite_art.model import ARCHETYPE_IDS, SCHEMA_VERSION
from sprite_art.render import selected_tier

from edge_markers import HULL_MARKERS, migrate_rows

# Section identity per (subtype, slot count). Edge's slots are positional and
# unnamed; these give them the names and controlled properties the editor shows.
SECTIONS: dict[tuple[str, int], tuple[tuple[str, str, str], ...]] = {
    ("stardock", 4): (
        ("beacon_mast", "Beacon Mast", "beacon"),
        ("docking_deck", "Docking Deck", "docking"),
        ("body", "Body", "hull"),
        ("engine_taper", "Engine Taper", "thrusters"),
    ),
    ("stardock", 3): (
        ("beacon_mast", "Beacon Mast", "beacon"),
        ("arm_band", "Arm Band", "docking"),
        ("engine_glow", "Engine Glow", "thrusters"),
    ),
    ("trading_port", 3): (
        ("mast", "Mast", "tower"),
        ("core", "Core", "docking"),
        ("base", "Base", "platform"),
    ),
    ("starbase", 3): (
        ("cap", "Cap", "beacon"),
        ("body", "Body", "hull"),
        ("base", "Base", "thrusters"),
    ),
}

TIER_LABELS = {
    "full": "Full Detail",
    "medium": "Medium",
    "compact": "Compact",
    "minimal": "Minimal",
}

# The tier ladder per subtype: for each tier, which Edge grammar it is cut from
# and the stacked height to grow its repeatable band toward.
#
# Edge ships two grammars per subtype -- a rich one and a small-box one -- and
# fills the requested height by tiling. Sprite documents freeze that into a few
# authored heights, which forces two choices this table records:
#
# * A subtype whose rich grammar already overshoots its box cuts its smaller
#   tiers from the small grammar instead. Uniform section heights inflate the
#   rich grammars well past Edge's own floor -- Edge may pick a squat 3-row cap
#   where the schema makes every cap as tall as the tallest -- so trading_port
#   floors at 10 rows and starbase at 12.
# * The smallest rung sits at the small grammar's own floor, because
#   ``SpriteSize.min_height`` lets Edge ask for a 3-row station and a tier
#   taller than the box would be center-cropped through its beacon and glow.
#
# Heights must strictly decrease or the later tier is unreachable;
# ``View.validate`` enforces it. The targets bracket the boxes Edge requests:
# ``SceneArtConfig`` sizes ports 16x6, starbases 22x9, and stardocks 38x16, and
# the sprite gallery asks 18x8.
# ``short`` cuts a second, shorter tier from the same rich grammar by keeping
# only each slot's least tall parts. Edge picks freely among parts of differing
# heights -- a squat 3-row cap or a 5-row tall one -- while the schema makes
# every variant in a section share one height. Padding them all up to the
# tallest inflates the rich tier past the boxes Edge asks for, which would hide
# the per-archetype art entirely. Grouping the short parts into their own tier
# keeps that art reachable at a station's real size.
TIER_PLAN: dict[str, tuple[tuple[str, int, bool, int], ...]] = {
    #                 (tier id, source grammar, short parts only, target height)
    "stardock": (
        ("full", 0, False, 16),
        ("medium", 0, True, 11),
        ("compact", 1, False, 6),
        ("minimal", 1, False, 3),
    ),
    "starbase": (
        ("full", 0, False, 12),
        ("medium", 0, True, 9),
        ("compact", 1, False, 5),
        ("minimal", 1, False, 3),
    ),
    "trading_port": (
        ("full", 0, False, 10),
        ("medium", 0, True, 8),
        ("compact", 1, False, 6),
        ("minimal", 1, False, 3),
    ),
}

DESCRIPTIONS = {
    "stardock": (
        "The Federation flagship station: a beacon mast over a wide docking "
        "deck, a tapering body, and an engine glow at its foot."
    ),
    "starbase": (
        "A military station built as a blunt armored spindle between a pointed "
        "cap and a drive base."
    ),
    "trading_port": (
        "A small commercial dock: a signal mast above a panelled core hung with "
        "berthing arms."
    ),
}

AUDIT_BOXES = {
    "trading_port": [(16, 6), (18, 8), (8, 4), (4, 3)],
    "starbase": [(22, 9), (18, 8), (12, 5), (4, 3)],
    "stardock": [(38, 16), (18, 8), (24, 10), (4, 3)],
}


def _pad_width(rows: list[str], width: int, fill: str) -> list[str]:
    """Center each row in a wider box so a tier holds one structure width."""

    padded: list[str] = []
    for row in rows:
        left = (width - len(row)) // 2
        padded.append(fill * left + row + fill * (width - len(row) - left))
    return padded


def _pad_height(
    cells: list[str],
    mask: list[str],
    height: int,
    width: int,
    *,
    repeatable: bool,
    at_top: bool,
) -> tuple[list[str], list[str]]:
    """Grow a part to its section's height without breaking how it tiles.

    A repeatable band is emitted once per repeat, so padding it with blank rows
    would tile as stripes of hull and void. Those grow by repeating an authored
    row instead. Caps and bases are emitted once, so they pad with blank rows on
    the side facing away from their neighbour, keeping the join tight.
    """

    missing = height - len(cells)
    if missing <= 0:
        return cells, mask
    if repeatable:
        source = 0 if at_top else len(cells) - 1
        filler_cells = [cells[source]] * missing
        filler_mask = [mask[source]] * missing
    else:
        filler_cells = [" " * width] * missing
        filler_mask = ["S" * width] * missing
    if at_top:
        return filler_cells + cells, filler_mask + mask
    return cells + filler_cells, mask + filler_mask


def _repeat_for_target(fixed: int, block: int, target: int, cap: int) -> int:
    """Choose how many times a band tiles to land closest to a target height."""

    if block <= 0:
        return 1
    return max(1, min(cap, (target - fixed) // block))


def _build_tier(
    subtype: str,
    tier_id: str,
    tier_name: str,
    slots: tuple[Any, ...],
    archetype_slots: dict[str, tuple[Any, ...]],
    target_height: int,
    mirror_row: Any,
    *,
    short_parts_only: bool = False,
) -> Tier:
    """Fold one Edge grammar tier, plus its archetype variants, into a Tier."""

    definitions = SECTIONS[(subtype, len(slots))]

    # Mirror and split every contributing part first, so widths and heights can
    # be reconciled across the whole tier before any Section is built.
    per_slot: list[list[tuple[str, list[str], list[str], list[str]]]] = []
    for index, slot in enumerate(slots):
        entries: list[tuple[str, list[str], list[str], list[str]]] = []
        for part_index, part in enumerate(slot.parts):
            cells, mask = migrate_rows([mirror_row(row) for row in part.left], HULL_MARKERS)
            entries.append((f"default_{part_index + 1}", cells, mask, []))
        for archetype_id in ARCHETYPE_IDS:
            source = archetype_slots.get(archetype_id)
            if source is None:
                continue
            part = source[index].parts[0]
            cells, mask = migrate_rows([mirror_row(row) for row in part.left], HULL_MARKERS)
            entries.append((archetype_id, cells, mask, [archetype_id]))
        per_slot.append(entries)

    width = max(
        len(row) for entries in per_slot for _id, cells, _m, _a in entries for row in cells
    )

    sections: list[Section] = []
    slot_heights: list[int] = []
    for index, (slot, entries, definition) in enumerate(
        zip(slots, per_slot, definitions)
    ):
        section_id, name, property_id = definition
        repeatable = any(part.repeatable for part in slot.parts)
        if short_parts_only:
            # Take the shortest part, but never drop the last un-tagged variant
            # or an archetype's only one -- every archetype must still resolve
            # to art of its own.
            untagged = [len(c) for _i, c, _m, tags in entries if not tags]
            tagged = [len(c) for _i, c, _m, tags in entries if tags]
            height = max(min(untagged), min(tagged) if tagged else 0)
            entries = [entry for entry in entries if len(entry[1]) <= height]
        else:
            height = max(len(cells) for _id, cells, _m, _a in entries)
        slot_heights.append(height)
        variants: list[Variant] = []
        for variant_id, cells, mask, archetypes in entries:
            cells = _pad_width(cells, width, " ")
            mask = _pad_width(mask, width, "S")
            cells, mask = _pad_height(
                cells,
                mask,
                height,
                width,
                repeatable=repeatable,
                at_top=index == 0,
            )
            variants.append(
                Variant(
                    id=variant_id,
                    cells=cells,
                    color_mask=mask,
                    archetypes=archetypes,
                )
            )
        sections.append(
            Section(
                id=section_id,
                name=name,
                primary_property=property_id,
                repeat=1,
                variants=variants,
            )
        )

    # Grow the repeatable band toward this tier's target height.
    growable = [
        index for index, slot in enumerate(slots) if any(p.repeatable for p in slot.parts)
    ]
    if growable:
        index = growable[0]
        fixed = sum(h for i, h in enumerate(slot_heights) if i != index)
        cap = max(int(slots[index].max_repeat), 1)
        sections[index].repeat = _repeat_for_target(
            fixed, slot_heights[index], target_height, cap
        )
    return Tier(id=tier_id, name=tier_name, sections=sections)


def build_sprite(
    subtype: str,
    grammar: dict[str, tuple[tuple[Any, ...], ...]],
    mirror_row: Any,
) -> Sprite:
    """Build one vertical-only station sprite from an Edge port grammar."""

    default_tiers = grammar["default"]
    # Archetype grammars are single-tier and shaped like the rich default, so
    # they can only contribute to tiers cut from that grammar. Tiers cut from
    # the small-box grammar fall back to the default silhouette for everyone.
    archetype_slots = {
        archetype_id: tiers[0]
        for archetype_id, tiers in grammar.items()
        if archetype_id != "default" and len(tiers[0]) == len(default_tiers[0])
    }

    tiers: list[Tier] = []
    for tier_id, grammar_index, short, target in TIER_PLAN[subtype]:
        tiers.append(
            _build_tier(
                subtype,
                tier_id,
                TIER_LABELS[tier_id],
                default_tiers[grammar_index],
                archetype_slots if grammar_index == 0 else {},
                target,
                mirror_row,
                short_parts_only=short,
            )
        )

    sprite = Sprite(
        schema_version=SCHEMA_VERSION,
        id=subtype,
        name=subtype.replace("_", " ").title(),
        kind="port",
        role=subtype,
        description=DESCRIPTIONS[subtype],
        views={
            "vertical": View(
                id="vertical",
                name="Vertical",
                axis="vertical",
                canonical_facing="up",
                mirror_facing=None,
                section_order="authored",
                tiers=tiers,
            )
        },
    )
    sprite.validate()
    return sprite


def _audit(sprites: dict[str, Sprite]) -> None:
    for subtype, sprite in sprites.items():
        view = sprite.views["vertical"]
        print(f"\n{subtype}")
        for tier in view.tiers:
            heights = {
                tier.composed_length("vertical", archetype_id)
                for archetype_id in (None, *ARCHETYPE_IDS)
            }
            span = (
                f"h{min(heights)}"
                if len(heights) == 1
                else f"h{min(heights)}-{max(heights)}"
            )
            print(f"  {tier.id:<8} w{tier.cross_axis_size('vertical'):<3} {span}")
        for width, height in AUDIT_BOXES[subtype]:
            picks = {
                selected_tier(
                    sprite,
                    width=width,
                    height=height,
                    view_id="vertical",
                    archetype_id=archetype_id,
                ).id
                for archetype_id in (None, *ARCHETYPE_IDS)
            }
            crops = {
                archetype_id
                for archetype_id in (None, *ARCHETYPE_IDS)
                if selected_tier(
                    sprite,
                    width=width,
                    height=height,
                    view_id="vertical",
                    archetype_id=archetype_id,
                ).composed_length("vertical", archetype_id)
                > height
            }
            flag = f"  CROPS x{len(crops)}" if crops else ""
            print(f"    {width}x{height:<3} -> {'/'.join(sorted(picks))}{flag}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("edge_path", type=Path)
    parser.add_argument("--output", type=Path, default=Path("assets"))
    parser.add_argument(
        "--audit",
        action="store_true",
        help="print the tier ladder against Edge's requested boxes, write nothing",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(args.edge_path.resolve()))
    from edge.art.port import PORT_GRAMMAR, _mirror_row  # noqa: PLC0415

    sprites = {
        subtype: build_sprite(subtype, grammar, _mirror_row)
        for subtype, grammar in PORT_GRAMMAR.items()
    }
    if args.audit:
        _audit(sprites)
        return
    for subtype, sprite in sprites.items():
        dump_sprite(sprite, args.output / "sprites" / "ports" / f"{subtype}.yaml")


if __name__ == "__main__":
    main()
