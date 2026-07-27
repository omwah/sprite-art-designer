"""Generate the complete role-specific ship asset roster.

The compact marker alphabet keeps glyph and semantic color authorship adjacent:
``Y/y`` is engine glow, ``R/r/O`` is a beacon, ``C/c`` is a window,
``G/g/K/L`` is armament, and ``B/b/P`` is defensive energy. The markers become
appropriate blocks, facets, beams, or muzzles and never reach schema-v2 YAML.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from sprite_art import Section, Sprite, Tier, Variant, View, dump_sprite
from sprite_art.model import SCHEMA_VERSION
from sprite_art.transform import generate_rotated_view

COLOR_MARKERS = {
    "R": ("▀", "B"),
    "r": ("▄", "B"),
    "Y": ("▀", "E"),
    "y": ("▄", "E"),
    "G": ("▀", "A"),
    "g": ("▄", "A"),
    "B": ("▀", "D"),
    "b": ("▄", "D"),
    "C": ("◆", "W"),
    "c": ("◇", "W"),
    "K": ("►", "A"),
    "L": ("═", "A"),
    "P": ("◇", "D"),
    "O": ("☼", "B"),
}

TIER_TARGETS = {"full": 48, "medium": 36, "compact": 18}


def variant(variant_id: str, *cells: str, weight: int = 1) -> Variant:
    migrated = [
        "".join(COLOR_MARKERS.get(glyph, (glyph, "S"))[0] for glyph in row) for row in cells
    ]
    color_mask = [
        "".join(COLOR_MARKERS.get(glyph, (glyph, "S"))[1] for glyph in row) for row in cells
    ]
    return Variant(
        id=variant_id,
        cells=migrated,
        color_mask=color_mask,
        weight=weight,
    )


def section(
    section_id: str,
    name: str,
    primary: str,
    variants: list[Variant],
    *,
    secondary: tuple[str, ...] = (),
    minimum: int = 1,
    maximum: int = 1,
) -> Section:
    return Section(
        id=section_id,
        name=name,
        primary_property=primary,
        secondary_properties=list(secondary),
        min_repeat=minimum,
        max_repeat=maximum,
        variants=variants,
    )


def compact(
    *,
    tail: Variant,
    body: list[Variant],
    nose: Variant,
    maximum: int = 10,
) -> Tier:
    return Tier(
        id="compact",
        name="Compact",
        sections=[
            section("drive", "Drive", "thrusters", [tail]),
            section(
                "body",
                "Body",
                "hull",
                body,
                secondary=("armor",),
                maximum=maximum,
            ),
            section("prow", "Prow", "weapons", [nose]),
        ],
    )


def _fit_rows(rows: list[str], height: int, fill: str) -> list[str]:
    """Center-crop or pad an authored grid without repairing its geometry."""

    width = len(rows[0])
    if len(rows) > height:
        start = (len(rows) - height) // 2
        return rows[start : start + height]
    padding = height - len(rows)
    top = padding // 2
    return [fill * width] * top + rows + [fill * width] * (padding - top)


def _scale_columns(rows: list[str]) -> list[str]:
    """Create the documented three-quarter-width medium structure."""

    width = len(rows[0])
    target = (width * 3 + 2) // 4
    if target == width:
        return list(rows)
    if target == 1:
        indices = [width // 2]
    else:
        indices = [index * (width - 1) // (target - 1) for index in range(target)]
    return ["".join(row[index] for index in indices) for row in rows]


def _normalize_tier(tier: Tier, height: int) -> None:
    for part in tier.sections:
        for authored in part.variants:
            widths = {len(row) for row in authored.cells}
            if len(widths) != 1:
                raise ValueError(
                    f"{tier.id}/{part.id}/{authored.id} has row widths {sorted(widths)}"
                )
            authored.cells = _fit_rows(authored.cells, height, " ")
            authored.color_mask = _fit_rows(authored.color_mask, height, "S")


def _medium_tier(full: Tier) -> Tier:
    medium = deepcopy(full)
    medium.id = "medium"
    medium.name = "Medium"
    _normalize_tier(medium, 5)
    for part in medium.sections:
        for authored in part.variants:
            authored.cells = _scale_columns(authored.cells)
            authored.color_mask = _scale_columns(authored.color_mask)
    return medium


def _structure_lengths(tier: Tier, target: int) -> dict[str, int]:
    sizes = [part.variants[0].width for part in tier.sections]
    repeats = [part.min_repeat for part in tier.sections]
    total = sum(size * repeat for size, repeat in zip(sizes, repeats))
    while True:
        changed = False
        for index, part in enumerate(tier.sections):
            if repeats[index] < part.max_repeat and total + sizes[index] <= target:
                repeats[index] += 1
                total += sizes[index]
                changed = True
        if not changed:
            return {part.id: repeat for part, repeat in zip(tier.sections, repeats)}


def _set_structure_lengths(tier: Tier) -> None:
    tier.structure_lengths = _structure_lengths(tier, TIER_TARGETS[tier.id])


def ship(
    role: str,
    name: str,
    description: str,
    full_sections: list[Section],
    compact_tier: Tier,
) -> Sprite:
    full = Tier(id="full", name="Full Detail", sections=full_sections)
    _normalize_tier(full, 7)
    medium = _medium_tier(full)
    _normalize_tier(compact_tier, 3)
    for tier in (full, medium, compact_tier):
        _set_structure_lengths(tier)
    sprite = Sprite(
        schema_version=SCHEMA_VERSION,
        id=role,
        name=name,
        kind="ship",
        role=role,
        description=description,
        views={
            "horizontal": View(
                id="horizontal",
                name="Horizontal",
                axis="horizontal",
                canonical_facing="right",
                mirror_facing="left",
                tiers=[full, medium, compact_tier],
            )
        },
    )
    sprite.validate()
    vertical, _warnings = generate_rotated_view(sprite)
    sprite.views["vertical"] = vertical
    sprite.validate()
    return sprite


def build() -> list[Sprite]:
    fighter = ship(
        "fighter",
        "Fighter",
        "A fast, fragile interceptor built as a short path from engine flare to forward gun.",
        [
            section(
                "thrusters",
                "Swept Thrusters",
                "thrusters",
                [
                    variant(
                        "split_flare", "     ", " y╺Y ", "y▖▓▘ ", "y█▓═ ", "y▘▓▖ ", " y╺Y ", "     "
                    ),
                    variant(
                        "hot_fork", "     ", "y▘ Y ", " y▙▓ ", "y█▓═ ", " y▛▓ ", "y▖ Y ", "     "
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "spindrive",
                "Drive Swell",
                "spindrive",
                [
                    variant(
                        "faceted",
                        "      ",
                        " ▗▓▖  ",
                        "◢███◣ ",
                        "█░██░█",
                        "◥███◤ ",
                        " ▝▓▘  ",
                        "      ",
                    ),
                    variant(
                        "open", "      ", " ╲  ╱ ", "▟███▙ ", "█▒██▒█", "▜███▛ ", " ╱  ╲ ", "      "
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "hull",
                "Narrow Fuselage",
                "hull",
                [
                    variant("cockpit_rib", "   ", " ╱ ", "▟█═", "█C█", "▜█═", " ╲ ", "   "),
                    variant("gun_rib", "   ", "   ", "▖◆╺", "█▒█", "▘◆╺", "   ", "   "),
                ],
                secondary=("armor", "bridge"),
                maximum=5,
            ),
            section(
                "screens",
                "Screened Cockpit",
                "screens",
                [
                    variant("cockpit", "    ", " P  ", "◢█▙ ", "PC█═", "◥█▛ ", "    ", "    "),
                    variant("low_screen", "    ", "    ", "P▟█ ", "PC█═", "P▜█ ", "    ", "    "),
                ],
                secondary=("bridge",),
            ),
            section(
                "main_gun",
                "Forward Gun",
                "main_gun",
                [
                    variant(
                        "needle",
                        "      ",
                        "      ",
                        "╺═▓▙  ",
                        "╺LL█GK",
                        "╺═▓▛  ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "forked",
                        "      ",
                        "      ",
                        " ╺═█▙ ",
                        "╺L██GK",
                        " ╺═█▛ ",
                        "      ",
                        "      ",
                    ),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("flare", "  ", "y═", "  "),
            body=[variant("dart", " ▘", "█C", " ▖"), variant("thin", "  ", "█═", "  ")],
            nose=variant("muzzle", "   ", "LGK", "   "),
            maximum=5,
        ),
    )

    transport = ship(
        "transport",
        "Transport",
        "A dependable modular carrier whose countable container bays determine its capacity.",
        [
            section(
                "thrusters",
                "Cargo Thrusters",
                "thrusters",
                [
                    variant(
                        "cluster", "     ", " yY  ", "y▟▓═ ", "y██▓ ", "y▜▓═ ", " yY  ", "     "
                    ),
                    variant("tug", "     ", "y▘Y  ", "y▙▓  ", "y██▓ ", "y▛▓  ", "y▖Y  ", "     "),
                ],
                secondary=("spindrive",),
            ),
            section(
                "spindrive",
                "Drive Frame",
                "spindrive",
                [
                    variant("braced", "    ", "╔══╗", "╠██╣", "║▒▒║", "╠██╣", "╚══╝", "    "),
                    variant("serviceable", "    ", "╭──╮", "│██│", "├░░┤", "│██│", "╰──╯", "    "),
                ],
                secondary=("utility",),
            ),
            section(
                "hull",
                "Container Bays",
                "cargo",
                [
                    variant(
                        "double_doors",
                        "      ",
                        "╭─┬─╮ ",
                        "│▒│▒│ ",
                        "┤░┼░├╺",
                        "│▒│▒│ ",
                        "╰─┴─╯ ",
                        "      ",
                    ),
                    variant(
                        "pod", "      ", "▗▄▄▄▖ ", "▟█▒▒▙ ", "█▒◆▒█╺", "▜█▒▒▛ ", "▝▀▀▀▘ ", "      "
                    ),
                    variant(
                        "rail_bay",
                        "      ",
                        "╔═══╗ ",
                        "║░▒░║ ",
                        "╠═╬═╣╺",
                        "║░▒░║ ",
                        "╚═══╝ ",
                        "      ",
                    ),
                ],
                secondary=("hull", "utility"),
                maximum=7,
            ),
            section(
                "screens",
                "Control Collar",
                "screens",
                [
                    variant("bridge", "    ", " R  ", "▟██▙", "PC C", "▜██▛", "    ", "    "),
                    variant("utility", "    ", "    ", "◢██◣", "PCC█", "◥██◤", "    ", "    "),
                ],
                secondary=("bridge", "sensors"),
            ),
            section(
                "main_gun",
                "Utility Prow",
                "main_gun",
                [
                    variant("stub", "    ", "    ", "██▙ ", "█▓GK", "██▛ ", "    ", "    "),
                    variant("clamp", "    ", "    ", "▟█▙ ", "█╬█►", "▜█▛ ", "    ", "    "),
                ],
                secondary=("utility", "weapons"),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "y█", "  "),
            body=[variant("bay", "▀▀▀", "█▒█", "▄▄▄"), variant("door", "╭─╮", "│░│", "╰─╯")],
            nose=variant("cab", " ▀", "PC", " ▄"),
            maximum=5,
        ),
    )

    warship = ship(
        "warship",
        "Warship",
        "A dense line combatant organized around armor, a defensive collar, and one weapon axis.",
        [
            section(
                "thrusters",
                "Armored Thrusters",
                "thrusters",
                [
                    variant("boxed", "    ", "yY═ ", "y▟▓ ", "y██▓", "y▜▓ ", "yY═ ", "    "),
                    variant("split", "    ", "y▘Y ", "y▙▓ ", "y██▓", "y▛▓ ", "y▖Y ", "    "),
                ],
                secondary=("spindrive", "armor"),
            ),
            section(
                "spindrive",
                "Armored Drive",
                "spindrive",
                [
                    variant("collared", "    ", "▓█═ ", "◢██◣", "█░░█", "◥██◤", "▓█═ ", "    "),
                    variant("slab", "    ", "▗▄▖ ", "▟██▙", "█▒▒█", "▜██▛", "▝▀▘ ", "    "),
                ],
                secondary=("armor",),
            ),
            section(
                "hull",
                "Armored Spine",
                "armor",
                [
                    variant(
                        "magazine", "     ", "▓██═ ", "◢███◣", "█░░░█", "◥███◤", "▓██═ ", "     "
                    ),
                    variant(
                        "faceted", "     ", " ▀▀  ", "▟█▒█▙", "█◇░◇█", "▜█▒█▛", " ▄▄  ", "     "
                    ),
                ],
                secondary=("hull", "weapons"),
                maximum=6,
            ),
            section(
                "screens",
                "Screen Collar",
                "screens",
                [
                    variant("projectors", "    ", " P  ", "P▟█▙", "P█C█", "P▜█▛", " P  ", "    "),
                    variant("armored", "    ", "    ", "P◢█◣", "P███", "P◥█◤", "    ", "    "),
                ],
                secondary=("sensors",),
            ),
            section(
                "main_gun",
                "Spinal Gun",
                "main_gun",
                [
                    variant(
                        "barrel",
                        "      ",
                        "      ",
                        "╺═██▙ ",
                        "╺LL█GK",
                        "╺═██▛ ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "heavy",
                        "      ",
                        "      ",
                        "═███▙ ",
                        "L███GK",
                        "═███▛ ",
                        "      ",
                        "      ",
                    ),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "y█", "  "),
            body=[variant("armor", "▗▖", "█▒", "▝▘"), variant("gun_rib", "▀G", "██", "▄g")],
            nose=variant("gun", "   ", "LGK", "   "),
            maximum=6,
        ),
    )

    capital_warship = ship(
        "capital_warship",
        "Capital Warship",
        "A command-scale fleet anchor with clustered drives, layered decks, and an embedded heavy prow.",
        [
            section(
                "thrusters",
                "Capital Thrusters",
                "thrusters",
                [
                    variant(
                        "cluster", " yY  ", "y╺Y═ ", "y▟▓▓ ", "y███▓", "y▜▓▓ ", "y╺Y═ ", " yY  "
                    ),
                    variant(
                        "fortified", "y▘Y  ", "y▙▓═ ", "y██▓ ", "y█░█▓", "y██▓ ", "y▛▓═ ", "y▖Y  "
                    ),
                ],
                secondary=("spindrive", "reactor"),
            ),
            section(
                "spindrive",
                "Drive Bastion",
                "spindrive",
                [
                    variant(
                        "bastion", "▓█═  ", "╔═╦═╗", "╠███╣", "║░▒░║", "╠███╣", "╚═╩═╝", "▓█═  "
                    ),
                    variant(
                        "reactor", " ▀▀  ", "▟███▙", "█▒◆▒█", "█◆░◆█", "█▒◆▒█", "▜███▛", " ▄▄  "
                    ),
                ],
                secondary=("armor", "reactor"),
            ),
            section(
                "hull",
                "Layered Heavy Hull",
                "armor",
                [
                    variant(
                        "decks",
                        "  R   ",
                        "╔═╦══╗",
                        "╠█C██╣",
                        "║░▒▒░║",
                        "╠████╣",
                        "╚═╩══╝",
                        "  ▄   ",
                    ),
                    variant(
                        "terrace",
                        " ╭─╮  ",
                        "╭╯C╰╮ ",
                        "▟███▙ ",
                        "█░▒░█╺",
                        "▜███▛ ",
                        "╰╮ ╭╯ ",
                        " ╰─╯  ",
                    ),
                    variant(
                        "keel", " ▀▀▀  ", "◢███◣ ", "█▒█▒█╺", "█░◇░█╺", "█▒█▒█╺", "◥███◤ ", " ▄▄▄  "
                    ),
                ],
                secondary=("hull", "bridge"),
                maximum=6,
            ),
            section(
                "screens",
                "Forward Screen Complex",
                "screens",
                [
                    variant(
                        "citadel", " P   ", "╭─╮  ", "P▟██▙", "P█C██", "P▜██▛", "╰─╯  ", " P   "
                    ),
                    variant(
                        "shoulders", "     ", "P▀ P ", "P◢█◣ ", "P█C█═", "P◥█◤ ", "P▄ P ", "     "
                    ),
                ],
                secondary=("bridge", "sensors"),
            ),
            section(
                "main_gun",
                "Heavy Battery",
                "main_gun",
                [
                    variant(
                        "embedded",
                        "       ",
                        "  ▗▄▖  ",
                        "═████▙ ",
                        "L████GK",
                        "═████▛ ",
                        "  ▝▀▘  ",
                        "       ",
                    ),
                    variant(
                        "fortress",
                        "       ",
                        " ╭──╮  ",
                        "═████▙ ",
                        "L█G█G█K",
                        "═████▛ ",
                        " ╰──╯  ",
                        "       ",
                    ),
                ],
                secondary=("weapons", "armor"),
            ),
        ],
        compact(
            tail=variant("drive", "y█", "y█", "y█"),
            body=[variant("decks", "▀C▀", "█▒█", "▄█▄"), variant("tower", " ▀ ", "█C█", "███")],
            nose=variant("battery", " ▀▀ ", "█G█K", " ▄▄ "),
            maximum=7,
        ),
    )

    needle_picket = ship(
        "needle_picket",
        "Needle Picket",
        "A lean independent patrol hull with exposed drive nodes and an oversized sensor prow.",
        [
            section(
                "thrusters",
                "Thruster Fork",
                "thrusters",
                [
                    variant("fork", "     ", " y╺Y ", "y▖█▓ ", "y██▓ ", "y▘█▓ ", "     "),
                    variant("split", " y   ", "y▘Y▓ ", " y██▓", "y▖Y▓ ", "     "),
                ],
            ),
            section(
                "drive_nodes",
                "Drive Nodes",
                "spindrive",
                [
                    variant("open", " O  ", "▓██═", "█░██", "▓██═", "    "),
                    variant("veiled", " R  ", "╭██╮", "█▒██", "╰██╯", "    "),
                ],
                secondary=("radiator",),
            ),
            section(
                "patrol_spine",
                "Patrol Spine",
                "hull",
                [
                    variant("sensor_rib", " R  ", "╭──╮", "█░c█", "╰──╯", "    "),
                    variant("plain_rib", "    ", "▗▄▄▖", "█▒░█", "▝▀▀▘", "    "),
                ],
                secondary=("sensors",),
                maximum=7,
            ),
            section(
                "sensor_crown",
                "Sensor Crown",
                "sensors",
                [
                    variant("crown", " O█O", "◇█C█", "O██O", " ◥█◤", "    "),
                    variant("dish", "  R ", "╭██╮", "O█C█", "╰██╯", "    "),
                ],
            ),
            section(
                "needle",
                "Needle Prow",
                "main_gun",
                [
                    variant("long", "     ", "  ╾▙ ", "╺═▓GK", "  ╾▛ ", "     "),
                    variant("probe", "     ", "  ─▙ ", "╺██GK", "  ─▛ ", "     "),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "Y█", "  "),
            body=[
                variant("spine", " ▴", "██", "  "),
                variant("sensor", " R", "█O", "  "),
            ],
            nose=variant("needle", "   ", "─GK", "   "),
            maximum=12,
        ),
    )

    falsehold_raider = ship(
        "falsehold_raider",
        "Falsehold Raider",
        "An armed merchant hull whose cargo seams conceal batteries and reinforced magazines.",
        [
            section(
                "merchant_drive",
                "Merchant Drive",
                "thrusters",
                [
                    variant("triple", " Y▶ ", "    ", "Y██▓", "    ", " Y▶ "),
                    variant("dirty", " YY ", "Y▶▓ ", "Y██▓", "    ", " Y▶ "),
                ],
                secondary=("spindrive",),
            ),
            section(
                "armored_buttress",
                "Armored Buttress",
                "armor",
                [
                    variant("ribbed", "▓██═", "╭──╮", "P▒▒P", "╰──╯", "▓██═"),
                    variant("sealed", "◢██◣", "█P P", "█░░█", "█P P", "◥██◤"),
                ],
            ),
            section(
                "false_holds",
                "False Cargo Holds",
                "cargo",
                [
                    variant("doors", " R    ", "╭────╮", "│▒C▒G│", "╰────╯", " ▾    "),
                    variant("containers", "      ", "╔════╗", "║▒G░C║", "╚════╝", "      "),
                ],
                secondary=("weapons", "hull"),
                maximum=8,
            ),
            section(
                "masked_battery",
                "Masked Battery",
                "weapons",
                [
                    variant("closed", "    ", "◢██◣", "█G█G", "◥██◤", "    "),
                    variant("open", " G  ", "▓█K ", "█G█G", "▓█K ", " g  "),
                ],
                secondary=("armor",),
            ),
            section(
                "merchant_prow",
                "Merchant Prow",
                "hull",
                [
                    variant("blunt", "    ", "██▙ ", "█C▓►", "██▛ ", "    "),
                    variant("tapered", "    ", "▓█▙ ", "█C█►", "▓█▛ ", "    "),
                ],
                secondary=("main_gun",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", " █"),
            body=[
                variant("hold", "██", "█▒", "██"),
                variant("gun_hold", "▀G", "█C", "▄g"),
            ],
            nose=variant("prow", "   ", "█GK", "   "),
            maximum=12,
        ),
    )

    junction_pinnace = ship(
        "junction_pinnace",
        "Junction Pinnace",
        "A tiny courier and landing craft wrapped around drive, compensator, and cabin.",
        [
            section(
                "overdrive",
                "Overdrive",
                "thrusters",
                [
                    variant("single", "    ", " YY▓", " Y█▓", "    "),
                    variant("fork", " Y  ", " Y▶▓", " Y▶▓", "    "),
                ],
            ),
            section(
                "sail_nodes",
                "Sail Nodes",
                "spindrive",
                [
                    variant("diamond", "▗▄▄▖", "▓██▓", "▓██▓", "▝▀▀▘"),
                    variant("open", " ◆  ", "▓██▓", "▓██▓", " ◇  "),
                ],
                secondary=("radiator",),
            ),
            section(
                "cabin",
                "Cabin",
                "habitat",
                [
                    variant("window", " R  ", "╭──╮", "█CC█", "╰──╯"),
                    variant("armored", "    ", "▗▄▄▖", "█C▒█", "▝▀▀▘"),
                ],
                secondary=("sensors",),
                maximum=3,
            ),
            section(
                "landing_nose",
                "Landing Nose",
                "utility",
                [
                    variant("round", "   ", "P▙ ", "P█►", "P▛ "),
                    variant("probe", "   ", "P▙ ", "█C►", "P▛ "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", "  ", "Y▓", "  "),
            body=[variant("cabin", " RC", "█C█", " ▄ ")],
            nose=variant("nose", " P", "P►", " P"),
            maximum=4,
        ),
    )

    radiant_lance = ship(
        "radiant_lance",
        "Radiant Lance",
        "A glittering military spine with folding diamond radiators and petal habitats.",
        [
            section(
                "fusion_bell",
                "Fusion Bell",
                "thrusters",
                [
                    variant("focused", " Y▶═", "    ", " Y▓ ", "Y██▓", " Y▓ ", "    ", " Y▶═"),
                    variant("hot", " YY═", " Y  ", "Y▟▓ ", "Y██▓", "Y▜▓ ", " Y  ", " YY═"),
                ],
                secondary=("reactor",),
            ),
            section(
                "engine_swell",
                "Engine Swell",
                "spindrive",
                [
                    variant("swell", " ▴  ", "◢██◣", "▓██▓", "█▒▒█", "▓██▓", "◥██◤", " ▾  "),
                    variant("veined", " O  ", "◢█O◣", "▓██▓", "█▒▒█", "▓██▓", "◥█O◤", " ▾  "),
                ],
                secondary=("reactor",),
            ),
            section(
                "diamond_radiators",
                "Diamond Radiators",
                "radiator",
                [
                    variant("open", "◢█◣ ", " ╲  ", "╭──╮", "│ ∞│", "╰──╯", " ╱  ", "◥█◤ "),
                    variant("folded", " ♦  ", " │  ", "▗▄▄▖", "█ ▒█", "▝▀▀▘", " │  ", " ◇  "),
                ],
                secondary=("hull",),
                maximum=6,
            ),
            section(
                "habitat_petals",
                "Habitat Petals",
                "habitat",
                [
                    variant("spread", "◢██◣", " ╲╱ ", "█C█C", "█O██", "█C█C", " ╱╲ ", "◥██◤"),
                    variant("folded", "    ", "╭██╮", "█C██", "█O█C", "████", "╰██╯", "    "),
                ],
                secondary=("bridge",),
            ),
            section(
                "lance",
                "Lance",
                "main_gun",
                [
                    variant(
                        "needle", "     ", "     ", "  ─▙ ", "─L█GK", "  ─▛ ", "     ", "     "
                    ),
                    variant("fork", "     ", "     ", "─G█▙ ", "L██GK", "─g█▛ ", "     ", "     "),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "Y█", " ▾"),
            body=[
                variant("fins", "◢█", "██", "◥█"),
                variant("petal", "▀C", "█O", "▄C"),
            ],
            nose=variant("lance", "   ", "LGK", "   "),
            maximum=11,
        ),
    )

    hearth_freighter = ship(
        "hearth_freighter",
        "Hearth Freighter",
        "A century-old modular transport made homelike through repairs, cargo, and a rotating drum.",
        [
            section(
                "retrofitted_drive",
                "Retrofitted Drive",
                "thrusters",
                [
                    variant("fusion", " Y▶ ", "    ", "Y▟▓ ", "Y██▓", "Y▜▓ ", "    "),
                    variant("patched", " YY ", "Y▶▓ ", " ▟▓ ", "Y██▓", " ▜▓ ", "    "),
                ],
                secondary=("spindrive",),
            ),
            section(
                "machine_shop",
                "Machine Shop",
                "utility",
                [
                    variant("shop", " R  ", "╭──╮", "│C▒│", "├▒▒┤", "╰──╯", " ▾  "),
                    variant("patched", "    ", "▗▄▄▖", "█▒C█", "█░▒█", "▝▀▀▘", "    "),
                ],
                secondary=("reactor",),
            ),
            section(
                "cargo_modules",
                "Cargo Modules",
                "cargo",
                [
                    variant("stack", "      ", "╭────╮", "│▒▒▒▒│", "├▒C▒▒┤", "╰────╯", "      "),
                    variant("pods", " ▗▄▄▖ ", " ╲  ╱ ", "██▒▒██", "██C▒██", " ╱  ╲ ", " ▝▀▀▘ "),
                ],
                secondary=("hull",),
                maximum=9,
            ),
            section(
                "hearth_drum",
                "Hearth Drum",
                "habitat",
                [
                    variant("turning", " ╭██╮ ", "╱ C C╲", "█C██C█", "█O██C█", "╲ C C╱", " ╰██╯ "),
                    variant("locked", "      ", "╭████╮", "█▒C▒C█", "█▒O▒C█", "╰████╯", "      "),
                ],
                secondary=("bridge",),
            ),
            section(
                "mining_prow",
                "Mining Prow",
                "main_gun",
                [
                    variant("laser", "     ", "  ▟  ", "──█GK", "  ▜  ", "     ", "     "),
                    variant("tractor", "     ", " ╭█╮ ", "─█G█K", " ╰█╯ ", "     ", "     "),
                ],
                secondary=("utility",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", "  "),
            body=[
                variant("cargo", "██", "█▒", "██"),
                variant("home", "▀C", "█O", "▄C"),
            ],
            nose=variant("laser", "   ", "─GK", "   "),
            maximum=14,
        ),
    )

    pearl_shell = ship(
        "pearl_shell",
        "Pearl Shell",
        "An alien troop shell with offset carapace plates and a ring of recessed weapon ports.",
        [
            section(
                "ciliary_drive",
                "Ciliary Drive",
                "thrusters",
                [
                    variant("fan", " YY ", "Y◢▓ ", "Y██▓", "Y██▓", "Y◥▓ ", "    ", " Y  "),
                    variant("barbs", " Y▶ ", "Y▟▓ ", "Y██▓", "Y▒█▓", "Y▜▓ ", "    ", " Y▶ "),
                ],
                secondary=("spindrive",),
            ),
            section(
                "rear_carapace",
                "Rear Carapace",
                "armor",
                [
                    variant("pearl", " ╭██╮", "╭████", "█████", "█▒◇██", "█████", "╰████", " ╰██╯"),
                    variant(
                        "scarred", "  ▗▄▖", "▗▄█▒█", "██◇██", "█▒▒██", "█████", "▝▀█▒█", "  ▝▀▘"
                    ),
                ],
            ),
            section(
                "weapon_ring",
                "Weapon Ring",
                "weapons",
                [
                    variant(
                        "ports",
                        " R    ",
                        "╭████╮",
                        "█G█G██",
                        "██O███",
                        "█G██G█",
                        "╰████╯",
                        "   g  ",
                    ),
                    variant(
                        "sealed",
                        "      ",
                        " ▗▄▄▖ ",
                        "▗▄██▄▖",
                        "█▒G▒██",
                        "▝▀██▀▘",
                        " ▝▀▀▘ ",
                        "      ",
                    ),
                ],
                secondary=("hangar", "hull"),
                maximum=5,
            ),
            section(
                "troop_lobe",
                "Troop Lobe",
                "hangar",
                [
                    variant("open", " ╭██╮", "╭█O██", "█████", "██○██", "█████", "╰██▒█", "  ╰█╯"),
                    variant("heavy", "  ▗▄▖", "▗▄███", "█▒▒██", "██O██", "█████", "▝▀███", " ▝▀▀▘"),
                ],
                secondary=("habitat",),
            ),
            section(
                "beak",
                "Carapace Beak",
                "screens",
                [
                    variant("hook", "     ", " P█P ", "P███▙", "P█O▓►", "P███▛", "  P█ ", "     "),
                    variant("round", "     ", "  P█P", "P███P", "P█O▓►", "P███P", "  P█P", "     "),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", " ▾"),
            body=[
                variant("shell", "◢█", "█◇", "◥█"),
                variant("ports", "G█", "█O", "g█"),
            ],
            nose=variant("beak", " P ", "P█►", " P "),
            maximum=10,
        ),
    )

    marrow_dart = ship(
        "marrow_dart",
        "Marrow Dart",
        "A reckless organic assault craft grown as bound spars, muscle bands, and a hardened beak.",
        [
            section(
                "sinew_drive",
                "Sinew Drive",
                "thrusters",
                [
                    variant("tendons", " Y   ", "YY╲▓ ", "Y▒██▓", "YY╱▓ ", "     "),
                    variant("spasm", " YY  ", "Y╲▒▓ ", "Y███▓", "Y╱▒▓ ", "  Y  "),
                ],
                secondary=("reactor",),
            ),
            section(
                "marrow_knot",
                "Marrow Knot",
                "spindrive",
                [
                    variant("joint", " ▗▒▖", "╱███", "█O██", "╲███", " ▝▒▘"),
                    variant("scar", "  ▴ ", "◢█▒◣", "██◊█", "◥█▒◤", "  ▾ "),
                ],
                secondary=("hull",),
            ),
            section(
                "bound_spars",
                "Bound Spars",
                "hull",
                [
                    variant("bones", "╲  ╱", "▓██▓", "█▒▒█", "▓██▓", "╱  ╲"),
                    variant("muscle", "▗▒▒▖", "█▓▓█", "█∞▒█", "█▓▓█", "▝▒▒▘"),
                ],
                secondary=("armor",),
                maximum=8,
            ),
            section(
                "nerve_cluster",
                "Nerve Cluster",
                "sensors",
                [
                    variant("eye", " O█O ", "█O███", "█████", "█O▒██", " ◥█◤ "),
                    variant("many_eyes", " R R ", "◢O█O◣", "█████", "◥█O█◤", "  ▾  "),
                ],
                secondary=("weapons",),
            ),
            section(
                "hardened_beak",
                "Hardened Beak",
                "main_gun",
                [
                    variant("fang", "    ", "◢▒▙ ", "██GK", "◥▒▛ ", "    "),
                    variant("barb", "    ", "╲█▙ ", "█▒GK", "╱█▛ ", "    "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "Y▒", " ▾"),
            body=[
                variant("bone", "╲█", "█▒", "╱█"),
                variant("muscle", "◢▒", "█◊", "◥▒"),
            ],
            nose=variant("fang", " ◢ ", "█GK", " ◥ "),
            maximum=12,
        ),
    )

    broadside_citadel = ship(
        "broadside_citadel",
        "Broadside Citadel",
        "A capital linebreaker built around layered lateral batteries and a fortress spine.",
        [
            section(
                "capital_drive",
                "Capital Drive",
                "thrusters",
                [
                    variant(
                        "seven_bell", " Y▶═ ", "     ", "Y▟▓▓ ", "Y███▓", "Y███▓", "Y▜▓▓ ", " Y▶═ "
                    ),
                    variant(
                        "armored", " YY═ ", "Y▶▓  ", " ▟██▓", "Y████", "Y███▓", " ▜██▓", " YY═ "
                    ),
                ],
                secondary=("reactor", "spindrive"),
            ),
            section(
                "drive_citadel",
                "Drive Citadel",
                "armor",
                [
                    variant(
                        "buttress", "▓███═", " ║   ", "╔═╦═╗", "║▒▒▒║", "╠P▒P╣", "╚═╩═╝", "▓███═"
                    ),
                    variant(
                        "layered", "◢███◣", "▓███▓", "█████", "█▒▒▒█", "█████", "▓███▓", "◥███◤"
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "broadside_decks",
                "Broadside Decks",
                "weapons",
                [
                    variant(
                        "open_bays",
                        " R    ",
                        "▓▀K▓▀K",
                        "╔════╗",
                        "║▒◇▒▒║",
                        "╚════╝",
                        "▓▀K▓▀K",
                        " r    ",
                    ),
                    variant(
                        "gunwalls",
                        "▓███L ",
                        "─G▙   ",
                        "██████",
                        "█G▒G██",
                        "██████",
                        "─g▛   ",
                        "▓███L ",
                    ),
                ],
                secondary=("hull", "armor"),
                maximum=10,
            ),
            section(
                "command_keep",
                "Command Keep",
                "bridge",
                [
                    variant("tower", "  R  ", " ╭─╮ ", "◢█C█◣", "█O█C█", "█████", "◥███◤", "  ▾  "),
                    variant(
                        "low_keep", "     ", " ▗▄▖ ", "◢█C█◣", "█O█C█", "█████", "◥███◤", "     "
                    ),
                ],
                secondary=("sensors", "screens"),
            ),
            section(
                "siege_prow",
                "Siege Prow",
                "main_gun",
                [
                    variant(
                        "triple",
                        "      ",
                        "      ",
                        "─█G█▙ ",
                        "L█G█GK",
                        "─█G█▛ ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "ram", "      ", "  P█P ", "P████▙", "P█G█GK", "P████▛", "  P█P ", "      "
                    ),
                ],
                secondary=("armor",),
            ),
        ],
        compact(
            tail=variant("drive", "██", "Y█", "██"),
            body=[
                variant("gunwall", "GK", "██", "gK"),
                variant("armor", "P█", "█C", "P█"),
            ],
            nose=variant("siege", " P█", "PGK", " P█"),
            maximum=15,
        ),
    )

    return [
        fighter,
        transport,
        warship,
        capital_warship,
        needle_picket,
        falsehold_raider,
        junction_pinnace,
        radiant_lance,
        hearth_freighter,
        pearl_shell,
        marrow_dart,
        broadside_citadel,
    ]


def main() -> None:
    output = Path("assets/sprites/ships")
    for sprite in build():
        dump_sprite(sprite, output / f"{sprite.id}.yaml")


if __name__ == "__main__":
    main()
