"""Generate the complete role-specific ship asset roster.

The compact marker alphabet keeps glyph and semantic color authorship adjacent:
``Y/y`` is engine glow, ``X/x`` is a hot engine throat, ``R/r/O`` is a beacon,
``C/c`` is a window, ``G/g/K/L/U/u`` is armament, and ``B/b/P`` is defensive
energy. The markers become appropriate blocks, facets, beams, or muzzles and
never reach schema-v3 YAML.

Authoring conventions that keep the derived tiers readable:

- Full tiers are seven rows; rows 0 and 6 carry extremity detail (wisps,
  mast beacons, bell lips) because the medium tier crops them away.
- Medium columns are sampled as ``(width * 3 + 2) // 4``, so six-wide parts
  keep columns 0, 1, 2, 3, 5: frames either span the full width or close at
  column 3.
- Centerlines favor panel rhythms (``█▒█``, ``▓═╾``) that survive repetition.
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
    "X": ("▒", "E"),
    "x": ("░", "E"),
    "G": ("▀", "A"),
    "g": ("▄", "A"),
    "B": ("▀", "D"),
    "b": ("▄", "D"),
    "C": ("◆", "W"),
    "c": ("◇", "W"),
    "K": ("►", "A"),
    "L": ("═", "A"),
    "U": ("▲", "A"),
    "u": ("▼", "A"),
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
        repeat=maximum,
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


def _fixed_repetitions(tier: Tier, target: int) -> dict[str, int]:
    sizes = [part.variants[0].width for part in tier.sections]
    repeats = [1 for _part in tier.sections]
    total = sum(size * repeat for size, repeat in zip(sizes, repeats))
    while True:
        changed = False
        for index, part in enumerate(tier.sections):
            if repeats[index] < part.repeat and total + sizes[index] <= target:
                repeats[index] += 1
                total += sizes[index]
                changed = True
        if not changed:
            return {part.id: repeat for part, repeat in zip(tier.sections, repeats)}


def _set_fixed_repetitions(tier: Tier) -> None:
    repetitions = _fixed_repetitions(tier, TIER_TARGETS[tier.id])
    for section in tier.sections:
        section.repeat = repetitions[section.id]


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
        _set_fixed_repetitions(tier)
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
                        "twin_bell",
                        "     ",
                        " ▄▓▖ ",
                        "y▟█▓╾",
                        "y█x█▓",
                        "y▜█▓╾",
                        " ▀▓▘ ",
                        "     ",
                    ),
                    variant(
                        "vector_nozzle",
                        "     ",
                        " y▗▄ ",
                        "y▟█▓╾",
                        "y█x██",
                        " ▜█▓╾",
                        "  ▀▘ ",
                        "     ",
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
                        "faceted_core",
                        "     ",
                        " ▄▖  ",
                        "◢██◣ ",
                        "█x██╾",
                        "◥██◤ ",
                        " ▀▘  ",
                        "     ",
                    ),
                    variant(
                        "annular_ring",
                        "     ",
                        " ▗▓▖ ",
                        "▟█░█▙",
                        "█░▒░█",
                        "▜█░█▛",
                        " ▝▓▘ ",
                        "     ",
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "hull",
                "Narrow Fuselage",
                "hull",
                [
                    variant("panel_rib", "   ", "   ", "▓▓╾", "█▒█", "▓═╾", "   ", "   "),
                    variant("fastener_rib", "   ", "   ", "▓═╾", "█▒◆", "▓═╾", "   ", "   "),
                ],
                secondary=("armor", "bridge"),
                maximum=5,
            ),
            section(
                "screens",
                "Screened Cockpit",
                "screens",
                [
                    variant("canopy", "    ", " P  ", "◢█▙ ", "PC█╾", "◥█▛ ", "    ", "    "),
                    variant("armored_canopy", "    ", "    ", "P▟█▙", "PC▓╾", "P▜█▛", "    ", "    "),
                ],
                secondary=("bridge",),
            ),
            section(
                "main_gun",
                "Forward Gun",
                "main_gun",
                [
                    variant(
                        "long_barrel",
                        "      ",
                        "      ",
                        " ╾═▙  ",
                        "╾═LL▓K",
                        " ╾═▛  ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "muzzle_brake",
                        "      ",
                        " ╾G▙  ",
                        "╾═█▙  ",
                        "╾L═█GK",
                        "╾═█▛  ",
                        " ╾G▛  ",
                        "      ",
                    ),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("flare", "  ", "y█", "  "),
            body=[variant("dart", " ▘", "█▒", " ▖"), variant("thin", "  ", "█╾", "  ")],
            nose=variant("muzzle", "   ", "LGK", "   "),
            maximum=6,
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
                        "twin_bell",
                        "     ",
                        " Y▄  ",
                        "y▟x▓╾",
                        "y███▓",
                        "y▜x▓╾",
                        " Y▀  ",
                        "     ",
                    ),
                    variant(
                        "cluster_tug",
                        "     ",
                        "y▗▓  ",
                        "y▐█▓╾",
                        "y█x▓ ",
                        "y▐█▓╾",
                        "y▝▓  ",
                        "     ",
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "spindrive",
                "Drive Frame",
                "spindrive",
                [
                    variant(
                        "drive_cradle",
                        "     ",
                        "╔═╦═╗",
                        "║▓█▓║",
                        "╠═╬═╣",
                        "║▓█▓║",
                        "╚═╩═╝",
                        "     ",
                    ),
                    variant(
                        "service_module",
                        "     ",
                        "╭───╮",
                        "│▓░▓│",
                        "┤░O░├",
                        "│▓░▓│",
                        "╰───╯",
                        "     ",
                    ),
                ],
                secondary=("utility",),
            ),
            section(
                "hull",
                "Container Bays",
                "cargo",
                [
                    variant(
                        "boxcar",
                        "      ",
                        "╭─┬──╮",
                        "│▒│▒▒│",
                        "┤░┼░▒├",
                        "│▒│▒▒│",
                        "╰─┴──╯",
                        "      ",
                    ),
                    variant(
                        "tank_farm",
                        "      ",
                        "▗▄▄▄▄▖",
                        "▟█▒▒█▙",
                        "█▒◆▒█╺",
                        "▜█▒▒█▛",
                        "▝▀▀▀▀▘",
                        "      ",
                    ),
                    variant(
                        "open_rack",
                        "      ",
                        "╔════╗",
                        "║▤▤▤▤║",
                        "╠═╬══╣",
                        "║▦▦▦▦║",
                        "╚════╝",
                        "      ",
                    ),
                ],
                secondary=("hull", "utility"),
                maximum=5,
            ),
            section(
                "screens",
                "Control Collar",
                "screens",
                [
                    variant("bridge_collar", "    ", " R  ", "◢██▙", "PCC█", "◥██▛", "    ", "    "),
                    variant("sensor_collar", "    ", "    ", "P◢█▙", "PC◆█", "P◥█▛", "    ", "    "),
                ],
                secondary=("bridge", "sensors"),
            ),
            section(
                "main_gun",
                "Utility Prow",
                "main_gun",
                [
                    variant("docking_prow", "    ", "    ", "◢██▙", "█▓GK", "◥██▛", "    ", "    "),
                    variant("clamp_prow", "    ", " ▄  ", "▟██▙", "█╬═K", "▜██▛", " ▀  ", "    "),
                ],
                secondary=("utility", "weapons"),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "y█", "  "),
            body=[variant("box", "╭─╮", "│▒│", "╰─╯"), variant("tank", "▗▄▖", "█▒█", "▝▀▘")],
            nose=variant("cab", " R ", "PCC", " ▄ "),
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
                    variant(
                        "armored_bells",
                        "     ",
                        "▓y▓▖ ",
                        "▓y█▓╾",
                        "▓y█x█",
                        "▓y█▓╾",
                        "▓y▓▘ ",
                        "     ",
                    ),
                    variant(
                        "open_bells",
                        "     ",
                        "y▄▓▖ ",
                        "y█x▓╾",
                        "y███▓",
                        "y█x▓╾",
                        "y▀▓▘ ",
                        "     ",
                    ),
                ],
                secondary=("spindrive", "armor"),
            ),
            section(
                "spindrive",
                "Armored Drive",
                "spindrive",
                [
                    variant(
                        "armored_core",
                        "     ",
                        "▗▄█▄▖",
                        "▟█▤█▙",
                        "█▤x▤█",
                        "▜█▤█▛",
                        "▝▀█▀▘",
                        "     ",
                    ),
                    variant(
                        "reactor_bulge",
                        "     ",
                        " ▄▓▄ ",
                        "◢█O█◣",
                        "█▒x▒█",
                        "◥█▓█◤",
                        " ▀▓▀ ",
                        "     ",
                    ),
                ],
                secondary=("armor",),
            ),
            section(
                "hull",
                "Armored Spine",
                "armor",
                [
                    variant(
                        "plate_band",
                        "     ",
                        "▓▀▓▓╾",
                        "█▤██▓",
                        "██▒██",
                        "█▤██▓",
                        "▓▄▓▓╾",
                        "     ",
                    ),
                    variant(
                        "turret_band",
                        "     ",
                        "▟G▙  ",
                        "█▓▓▓╾",
                        "██▒██",
                        "█▤██▓",
                        "▓▄▓▓╾",
                        "     ",
                    ),
                ],
                secondary=("hull", "weapons"),
                maximum=5,
            ),
            section(
                "screens",
                "Screen Collar",
                "screens",
                [
                    variant("deflector_collar", "    ", " P  ", "◢▓█▙", "P█▓╾", "◥▓█▛", " P  ", "    "),
                    variant("cic_collar", "    ", "    ", "P▟▓▙", "P█C█", "P▜▓▛", "    ", "    "),
                ],
                secondary=("sensors",),
            ),
            section(
                "main_gun",
                "Spinal Gun",
                "main_gun",
                [
                    variant(
                        "heavy_spinal",
                        "       ",
                        "  ▄▄   ",
                        " ╾═▓▓▙ ",
                        "╾═L█▓▓K",
                        " ╾═▓▓▛ ",
                        "  ▀▀   ",
                        "       ",
                    ),
                    variant(
                        "siege_barrel",
                        "       ",
                        " ╾G▙   ",
                        "╾═█▓▙  ",
                        "╾L█▓▓GK",
                        "╾═█▓▛  ",
                        " ╾g▛   ",
                        "       ",
                    ),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("drive", "▓ ", "y█", "▓ "),
            body=[variant("armor", "▗▄", "█▤", "▝▀"), variant("turret", "G▓", "██", "▓▓")],
            nose=variant("gun", "   ", "LLK", "   "),
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
                        "triple_bell",
                        " y▗▓  ",
                        "y▟x▓▖ ",
                        "y▟██▓ ",
                        "y█x██▓",
                        "y▜██▓ ",
                        "y▜x▓▘ ",
                        " y▝▓  ",
                    ),
                    variant(
                        "fortified_cluster",
                        " ▓y▓▖ ",
                        "▓y▟x▓ ",
                        "▓y██▓╾",
                        "▓y█x██",
                        "▓y██▓╾",
                        "▓y▜x▓ ",
                        " ▓y▓▘ ",
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
                        "bastion_cage",
                        "      ",
                        "╔══╦═╗",
                        "║▓▓█▓║",
                        "╠▤▤x▤╣",
                        "║▓▓█▓║",
                        "╚══╩═╝",
                        "      ",
                    ),
                    variant(
                        "reactor_drum",
                        "  ▄▄  ",
                        " ▟██▙ ",
                        "▟█▒▒█▙",
                        "█▒xO▒█",
                        "▜█▒▒█▛",
                        " ▜██▛ ",
                        "  ▀▀  ",
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
                        "command_decks",
                        "  R   ",
                        " ╭C╮  ",
                        "▟▤▤▤█▙",
                        "█▒C▒▒█",
                        "▜▤▤▤█▛",
                        " ▄▄▄▄ ",
                        "      ",
                    ),
                    variant(
                        "battery_deck",
                        "      ",
                        " ▟G▙  ",
                        "▟▤▤▤█▙",
                        "█▒▒▒▒█",
                        "▜▤▤▤█▛",
                        " ▄▄▄▄ ",
                        "      ",
                    ),
                    variant(
                        "terrace_deck",
                        "      ",
                        "▗▄▓▓▄▖",
                        "▟█▤▤█▙",
                        "█▒◆▒◆█",
                        "▜█▤▤█▛",
                        "▝▀▓▓▀▘",
                        "      ",
                    ),
                ],
                secondary=("hull", "bridge"),
                maximum=4,
            ),
            section(
                "screens",
                "Forward Screen Complex",
                "screens",
                [
                    variant(
                        "flag_bridge",
                        "  P  ",
                        " ╭─╮ ",
                        "P▟██▙",
                        "P█CC█",
                        "P▜██▛",
                        " ╰─╯ ",
                        "  P  ",
                    ),
                    variant(
                        "armored_shoulder",
                        "     ",
                        " P P ",
                        "P◢██◣",
                        "P█C▓█",
                        "P◥██◤",
                        " P P ",
                        "     ",
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
                        "embedded_battery",
                        "       ",
                        " ▗▄▄▄▖ ",
                        "═▟███▙ ",
                        "╾L█▓█▓K",
                        "═▜███▛ ",
                        " ▝▀▀▀▘ ",
                        "       ",
                    ),
                    variant(
                        "twin_spinal",
                        "       ",
                        " ╾═█▙  ",
                        "╾═█▓▓▙ ",
                        "╾L█G█GK",
                        "╾═█▓▓▛ ",
                        " ╾═█▛  ",
                        "       ",
                    ),
                ],
                secondary=("weapons", "armor"),
            ),
        ],
        compact(
            tail=variant("drive", "y▓", "y█", "y▓"),
            body=[variant("decks", "▀C▀", "█▒█", "▄█▄"), variant("tower", " ▀ ", "█C█", "███")],
            nose=variant("battery", " P  ", "PGK ", " P  "),
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
                    variant(
                        "forked_nacelles",
                        "     ",
                        "y▟▓  ",
                        "y╾█▓╾",
                        " ▓▒▓ ",
                        "y╾█▓╾",
                        "y▜▓  ",
                        "     ",
                    ),
                    variant(
                        "ring_nacelle",
                        "     ",
                        "y▗▄▖ ",
                        "y▐█x▓",
                        " ▓▒▓╾",
                        "y▐█x▓",
                        "y▝▀▘ ",
                        "     ",
                    ),
                ],
            ),
            section(
                "drive_nodes",
                "Drive Nodes",
                "spindrive",
                [
                    variant("exposed_nodes", "    ", " O  ", "▓██╾", "█░▓█", "▓██╾", " R  ", "    "),
                    variant("veiled_nodes", "    ", "    ", "╭██╮", "█▒O█", "╰██╯", "    ", "    "),
                ],
                secondary=("radiator",),
            ),
            section(
                "patrol_spine",
                "Patrol Spine",
                "hull",
                [
                    variant("truss_rib", "    ", "▗▄▄▖", "█░▒█", "█▒░█", "▝▀▀▘", "    ", "    "),
                    variant("sensor_rib", " R  ", "▗▄▄▖", "█░c█", "█▒░█", "▝▀▀▘", "    ", "    "),
                ],
                secondary=("sensors",),
                maximum=7,
            ),
            section(
                "sensor_crown",
                "Sensor Crown",
                "sensors",
                [
                    variant("crown", " O█O ", "◇███◇", "O█CC█", " ◥██◤", "     "),
                    variant("dish_array", "  R  ", " ◢◣  ", "◢█C█◣", "O███O", "     "),
                ],
            ),
            section(
                "needle",
                "Needle Prow",
                "main_gun",
                [
                    variant(
                        "long_needle",
                        "      ",
                        "      ",
                        "  ╾─▙ ",
                        "╾──╼▓K",
                        "  ╾─▛ ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "probe_spike",
                        "      ",
                        "      ",
                        "  ╾▓▙ ",
                        "╾─╼▓▓K",
                        "  ╾▓▛ ",
                        "      ",
                        "      ",
                    ),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "y▓", "  "),
            body=[
                variant("truss", "▗▖", "█░", "▝▘"),
                variant("sensor", " R", "█O", "  "),
            ],
            nose=variant("needle", "   ", "╾╼K", "   "),
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
                    variant(
                        "civilian_bells",
                        "     ",
                        " Y▄  ",
                        "y▟█▓╾",
                        "y█x▒▓",
                        "y▜█▓╾",
                        " Y▀  ",
                        "     ",
                    ),
                    variant(
                        "shoddy_bells",
                        " y▖  ",
                        "y▟▓  ",
                        " ▓x█▓",
                        "y██▒▓",
                        "y▜▓▘ ",
                        "     ",
                        "     ",
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "armored_buttress",
                "Armored Buttress",
                "armor",
                [
                    variant("ribbed_collar", "    ", "▓▀▀▓", "█▤▤█", "█░░█", "█▤▤█", "▓▄▄▓", "    "),
                    variant("sealed_collar", "    ", "◢██◣", "█P P", "█▒▒█", "█P P", "◥██◤", "    "),
                ],
            ),
            section(
                "false_holds",
                "False Cargo Holds",
                "cargo",
                [
                    variant(
                        "container_seam",
                        "      ",
                        "╭────╮",
                        "│▒▒G▒│",
                        "┤░▒░▒├",
                        "│▒▒▒▒│",
                        "╰────╯",
                        "      ",
                    ),
                    variant(
                        "twin_boxes",
                        "      ",
                        "╔═╗╔═╗",
                        "║▒║║▒║",
                        "╠═╣╠═╣",
                        "║▒║║▒║",
                        "╚═╝╚═╝",
                        "      ",
                    ),
                    variant(
                        "tank_with_vent",
                        "      ",
                        "▗▄▄▄▄▖",
                        "▟█▒▒█▙",
                        "█▒▒g█╺",
                        "▜█▒▒█▛",
                        "▝▀▀▀▀▘",
                        "      ",
                    ),
                ],
                secondary=("weapons", "hull"),
                maximum=5,
            ),
            section(
                "masked_battery",
                "Masked Battery",
                "weapons",
                [
                    variant("closed", "    ", "◢██◣", "█▒▒█", "█g██", "◥██◤", "    ", "    "),
                    variant("revealed", " G  ", "▓█▓K", "█g█G", "▓█▓K", " g  ", "    ", "    "),
                ],
                secondary=("armor",),
            ),
            section(
                "merchant_prow",
                "Merchant Prow",
                "hull",
                [
                    variant("blunt", " R  ", " ▄  ", "▟██▙", "█C▓K", "▜██▛", " ▀  ", "    "),
                    variant("tapered", "    ", "    ", "◢▓█▙", "█CC╸", "◥▓█▛", "    ", "    "),
                ],
                secondary=("main_gun",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "y▓", " █"),
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
                    variant("big_bell", "    ", "y▟▓▖", "y█x▓", "y▜▓▘", "    "),
                    variant("twin_nozzle", " y▖ ", "y▟▓ ", "y▜▓▖", "y█x▓", " y▘ "),
                ],
            ),
            section(
                "sail_nodes",
                "Sail Nodes",
                "spindrive",
                [
                    variant("diamond_sails", "    ", "▗▄▄▖", "▓x▓▓", "▝▀▀▘", "    "),
                    variant("radiator_sails", " ◇  ", "▗▄▄▖", "▓x▓▓", "▝▀▀▘", " ◇  "),
                ],
                secondary=("radiator",),
            ),
            section(
                "cabin",
                "Cabin",
                "habitat",
                [
                    variant("windowed_cabin", " R  ", "╭──╮", "│CC│", "├▒▒┤", "╰──╯"),
                    variant("armored_cabin", "    ", "▗▄▄▖", "█C▒█", "█▒▒█", "▝▀▀▘"),
                ],
                secondary=("sensors",),
                maximum=3,
            ),
            section(
                "landing_nose",
                "Landing Nose",
                "utility",
                [
                    variant("docking_nose", "   ", "P▙ ", "P█►", "P▛ "),
                    variant("ramp_nose", "   ", "▟█ ", "PC►", "▜█ "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", "  ", "y▓", "  "),
            body=[variant("cabin", " ╭╮", "█CC", " ╰╯")],
            nose=variant("nose", " P ", "P█►", " P "),
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
                    variant(
                        "focused_bell",
                        "  Y  ",
                        " Y▖  ",
                        "y◢█▓ ",
                        "y█x█▓",
                        "y◥█▓ ",
                        " Y▘  ",
                        "  Y  ",
                    ),
                    variant(
                        "luminous_plume",
                        "     ",
                        " ◀y▖ ",
                        "◀y▟▓╾",
                        "◀y█x█",
                        "◀y▜▓╾",
                        " ◀y▘ ",
                        "     ",
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "engine_swell",
                "Engine Swell",
                "spindrive",
                [
                    variant(
                        "swell",
                        "  ▴  ",
                        "◢██◣ ",
                        "▓█O█▓",
                        "█▒x▒█",
                        "▓███▓",
                        "◥██◤ ",
                        "  ▾  ",
                    ),
                    variant(
                        "veined_swell",
                        "  O  ",
                        "◢█▓◣ ",
                        "▓x█x▓",
                        "█▓O▓█",
                        "▓x█x▓",
                        "◥█▓◤ ",
                        "  O  ",
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "diamond_radiators",
                "Diamond Radiators",
                "radiator",
                [
                    variant(
                        "panel_vanes",
                        " ▗▓▖ ",
                        " ▐▓▌ ",
                        " ▐▓▌ ",
                        "╠═╬═╣",
                        " ▐▓▌ ",
                        " ▐▓▌ ",
                        " ▝▓▘ ",
                    ),
                    variant(
                        "diamond_chain",
                        " ◤◥  ",
                        " ◢◣  ",
                        "  █  ",
                        "╾═█═╼",
                        "  █  ",
                        " ◥◤  ",
                        " ◣◢  ",
                    ),
                ],
                secondary=("hull",),
                maximum=5,
            ),
            section(
                "habitat_petals",
                "Habitat Petals",
                "habitat",
                [
                    variant(
                        "spread_petals",
                        "◢██◣ ",
                        " ╲╱  ",
                        "█C░C█",
                        "█O███",
                        "█C░C█",
                        " ╱╲  ",
                        "◥██◤ ",
                    ),
                    variant(
                        "folded_petals",
                        " ▄▄  ",
                        "╭██╮ ",
                        "█CC▓╾",
                        "█O▓██",
                        "█C▓▓╾",
                        "╰██╯ ",
                        " ▀▀  ",
                    ),
                ],
                secondary=("bridge",),
            ),
            section(
                "lance",
                "Lance",
                "main_gun",
                [
                    variant(
                        "long_lance",
                        "       ",
                        "       ",
                        "  ╾──▙ ",
                        "╾──L═▓K",
                        "  ╾──▛ ",
                        "       ",
                        "       ",
                    ),
                    variant(
                        "lensed_lance",
                        "       ",
                        "   ╾G▙ ",
                        "  ╾═▓▙ ",
                        "╾─═█O▓K",
                        "  ╾═▓▛ ",
                        "   ╾G▛ ",
                        "       ",
                    ),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "y█", " ▾"),
            body=[
                variant("diamond", "◤◥", "█♦", "◣◢"),
                variant("petal", "▀C", "█O", "▄C"),
            ],
            nose=variant("lance", "   ", "╾LK", "   "),
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
                    variant(
                        "patched_bells",
                        "     ",
                        "y▟▓▖ ",
                        "y█x▓╾",
                        "y█▒▒▓",
                        "y▜X▓ ",
                        " ▓▝▘ ",
                        "     ",
                    ),
                    variant(
                        "mismatched_nozzles",
                        " y▖  ",
                        "y▟█▓ ",
                        " ▓x▓╾",
                        "y███▓",
                        "y▜x▓ ",
                        " y▘  ",
                        "     ",
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "machine_shop",
                "Machine Shop",
                "utility",
                [
                    variant(
                        "workshop",
                        " R   ",
                        "╭─┬─╮",
                        "│C▒│▓",
                        "├▒O▒┤",
                        "│░▒░│",
                        "╰─┴─╯",
                        "     ",
                    ),
                    variant(
                        "external_rig",
                        "     ",
                        "▗▄╥▄▖",
                        "█▒C▒█",
                        "█░O░█",
                        "▝▀╨▀▘",
                        "     ",
                        "     ",
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "cargo_modules",
                "Cargo Modules",
                "cargo",
                [
                    variant(
                        "patched_container",
                        "      ",
                        "╭───┬╮",
                        "│▒▒│▒│",
                        "┤░▒C▒├",
                        "│▒▒│▒│",
                        "╰───┴╯",
                        "      ",
                    ),
                    variant(
                        "habitat_pod",
                        " ▄▄   ",
                        "▗▟██▙ ",
                        "▟C▒C▙ ",
                        "█▒O▒▒█",
                        "▜█▒▒▛ ",
                        "▝▀▀▀▘ ",
                        "      ",
                    ),
                    variant(
                        "salvage_rack",
                        "      ",
                        "╔═╦══╗",
                        "║░║▒▒║",
                        "╠═╬═╬╣",
                        "║▒║░▒║",
                        "╚═╩══╝",
                        "      ",
                    ),
                ],
                secondary=("hull",),
                maximum=6,
            ),
            section(
                "hearth_drum",
                "Hearth Drum",
                "habitat",
                [
                    variant(
                        "turning_drum",
                        " ╭──╮ ",
                        "╱░CC░╲",
                        "█░╭╮░█",
                        "█O││O█",
                        "█░╰╯░█",
                        "╲░CC░╱",
                        " ╰──╯ ",
                    ),
                    variant(
                        "locked_drum",
                        "      ",
                        "╭████╮",
                        "█▒C▒C█",
                        "█▒O▒C█",
                        "█▒C▒▒█",
                        "╰████╯",
                        "      ",
                    ),
                ],
                secondary=("bridge",),
            ),
            section(
                "mining_prow",
                "Mining Prow",
                "main_gun",
                [
                    variant("cutter", "     ", "  ▟▙ ", "──█▓K", "  ▜▛ ", "     ", "     "),
                    variant("drill", "     ", " ╭█╮ ", "─█G▓K", " ╰█╯ ", "     ", "     "),
                ],
                secondary=("utility",),
            ),
        ],
        compact(
            tail=variant("drive", " ▓", "y█", " ▓"),
            body=[
                variant("cargo", "██", "█▒", "██"),
                variant("drum", "╭╮", "CO", "╰╯"),
            ],
            nose=variant("cutter", "   ", "─GK", "   "),
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
                    variant(
                        "fronds",
                        "y╾   ",
                        "y╾▓▖ ",
                        "y╾█x▓",
                        "y╾█▓▓",
                        "y╾▓▘ ",
                        "y╾   ",
                        "     ",
                    ),
                    variant(
                        "barbed_cilia",
                        " y▖  ",
                        "╾y▟▓ ",
                        "y▟█x▓",
                        "y▜█▓▓",
                        "╾y▜▓ ",
                        " y▘  ",
                        "     ",
                    ),
                ],
                secondary=("spindrive",),
            ),
            section(
                "rear_carapace",
                "Rear Carapace",
                "armor",
                [
                    variant(
                        "pearl_plates",
                        "  ╭─╮",
                        " ╭██╯",
                        "╭█▒██",
                        "█▒◇▒█",
                        "╰█▒██",
                        " ╰██╮",
                        "  ╰─╯",
                    ),
                    variant(
                        "scarred_carapace",
                        "  ▗▄▖",
                        " ▗█▒▙",
                        "▗▄█◇█",
                        "█▒▒◆█",
                        "▝▀█▒█",
                        " ▝█▒▛",
                        "  ▝▀▘",
                    ),
                ],
            ),
            section(
                "weapon_ring",
                "Weapon Ring",
                "weapons",
                [
                    variant(
                        "open_pores",
                        "  R   ",
                        "╭────╮",
                        "█▒◆▒▒█",
                        "█G▒G▒█",
                        "█▒O▒▒█",
                        "╰────╯",
                        "  g   ",
                    ),
                    variant(
                        "sealed_ring",
                        "      ",
                        " ▗▄▄▖ ",
                        "▗▄██▄▖",
                        "█▒G▒▒█",
                        "▝▀██▀▘",
                        " ▝▀▀▘ ",
                        "      ",
                    ),
                ],
                secondary=("hangar", "hull"),
                maximum=4,
            ),
            section(
                "troop_lobe",
                "Troop Lobe",
                "hangar",
                [
                    variant(
                        "open_lobe",
                        " ╭█╮ ",
                        "╭█○█╮",
                        "█○▒○█",
                        "█▒O▒█",
                        "█○▒○█",
                        "╰█○█╯",
                        " ╰█╯ ",
                    ),
                    variant(
                        "armored_lobe",
                        "  ▗▄▖",
                        " ▗███",
                        "▗█▒▒█",
                        "█▒O▒█",
                        "▝█▒▒█",
                        " ▝███",
                        "  ▝▀▘",
                    ),
                ],
                secondary=("habitat",),
            ),
            section(
                "beak",
                "Carapace Beak",
                "screens",
                [
                    variant("hooked_beak", "     ", " P█P ", "P███▙", "P█O▓►", "P███▛", "  P█ ", "     "),
                    variant("armored_beak", "     ", "  P█P", "P███P", "P█▒▓►", "P███P", "  P█P", "     "),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "y╾", " ▾"),
            body=[
                variant("shell", "◢█", "█◇", "◥█"),
                variant("pores", "G█", "█O", "g█"),
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
                    variant(
                        "tendons",
                        " Y   ",
                        "yY╲▓ ",
                        "y▒██▓",
                        "y█x▒▓",
                        "yY╱▓ ",
                        " Y   ",
                        "     ",
                    ),
                    variant(
                        "spasm",
                        " YY  ",
                        "y╲▒▓ ",
                        "y███▓",
                        "y█x█▓",
                        "y╱▒▓ ",
                        "  Y  ",
                        "     ",
                    ),
                ],
                secondary=("reactor",),
            ),
            section(
                "marrow_knot",
                "Marrow Knot",
                "spindrive",
                [
                    variant("joint", " ▗▒▖", "╱███", "█O▒█", "╲███", " ▝▒▘"),
                    variant("scar_knot", "  ▴ ", "◢█▒◣", "██◊█", "◥█▒◤", "  ▾ "),
                ],
                secondary=("hull",),
            ),
            section(
                "bound_spars",
                "Bound Spars",
                "hull",
                [
                    variant("spar", "╲  ╱", "▓██▓", "█▒▒█", "▓██▓", "╱  ╲"),
                    variant("muscle_band", "▗▒▒▖", "█▓▓█", "█∞▒█", "█▓▓█", "▝▒▒▘"),
                ],
                secondary=("armor",),
                maximum=7,
            ),
            section(
                "nerve_cluster",
                "Nerve Cluster",
                "sensors",
                [
                    variant("eye_cluster", " O█O ", "█O███", "█▒█▒█", "█O▒██", " ◥█◤ "),
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
                    variant("barbed_beak", "    ", "╲█▙ ", "█▒GK", "╱█▛ ", "    "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "y▒", " ▾"),
            body=[
                variant("spar", "╲█", "█▒", "╱█"),
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
                        "triple_bell",
                        " Y▖  ",
                        "y▟▓▖ ",
                        "y█x▓╾",
                        "y███▓",
                        "y█x▓╾",
                        "y▜▓▘ ",
                        " Y▘  ",
                    ),
                    variant(
                        "armored_cluster",
                        " ▓y▓ ",
                        "▓y▟x▓",
                        "▓y██▓",
                        "▓y█x█",
                        "▓y██▓",
                        "▓y▜x▓",
                        " ▓y▓ ",
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
                        "buttress",
                        "▓███═",
                        " ║   ",
                        "╔═╦═╗",
                        "║▒▒▒║",
                        "╠P▒P╣",
                        "╚═╩═╝",
                        "▓███═",
                    ),
                    variant(
                        "layered_citadel",
                        "◢███◣",
                        "▓█▤█▓",
                        "█▤▒▤█",
                        "█▒P▒█",
                        "█▤▒▤█",
                        "▓█▤█▓",
                        "◥███◤",
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
                        " ▄▓▄▓ ",
                        "▓U▓U▓▓",
                        "╔════╗",
                        "║▒◇▒▒║",
                        "╚════╝",
                        "▓u▓u▓▓",
                        " ▀▓▀▓ ",
                    ),
                    variant(
                        "gunwalls",
                        "▓G▓G▓▓",
                        "▟█▙▟█▙",
                        "██████",
                        "█G▒▒G█",
                        "██████",
                        "▜█▛▜█▛",
                        "▓g▓g▓▓",
                    ),
                ],
                secondary=("hull", "armor"),
                maximum=4,
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
                        "triple_battery",
                        "      ",
                        "      ",
                        "─█G█▙ ",
                        "L█G█GK",
                        "─█G█▛ ",
                        "      ",
                        "      ",
                    ),
                    variant(
                        "armored_ram",
                        "      ",
                        "  P█P ",
                        "P████▙",
                        "P█G█GK",
                        "P████▛",
                        "  P█P ",
                        "      ",
                    ),
                ],
                secondary=("armor",),
            ),
        ],
        compact(
            tail=variant("drive", "▓█", "y█", "▓█"),
            body=[
                variant("battery", "GK", "██", "gK"),
                variant("keep", "P█", "█C", "P█"),
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
