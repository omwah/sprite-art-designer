"""Generate the eight original, literature-inspired ship role files."""

from __future__ import annotations

from pathlib import Path

from sprite_art import Section, Sprite, Tier, Variant, View, dump_sprite
from sprite_art.model import SCHEMA_VERSION
from sprite_art.transform import generate_rotated_view


def variant(variant_id: str, *cells: str, weight: int = 1) -> Variant:
    return Variant(id=variant_id, cells=list(cells), weight=weight)


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


def ship(
    role: str,
    name: str,
    description: str,
    full_sections: list[Section],
    compact_tier: Tier,
) -> Sprite:
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
                tiers=[
                    Tier(id="full", name="Full Detail", sections=full_sections),
                    compact_tier,
                ],
            )
        },
    )
    sprite.validate()
    vertical, _warnings = generate_rotated_view(sprite)
    sprite.views["vertical"] = vertical
    sprite.validate()
    return sprite


def build() -> list[Sprite]:
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
                    variant("fork", "     ", "  Y▓ ", " YY█▓", "  Y▓ ", "     "),
                    variant("split", " Y   ", "  Y▓ ", " Y██▓", "  Y▓ ", "     "),
                ],
            ),
            section(
                "drive_nodes",
                "Drive Nodes",
                "spindrive",
                [
                    variant("open", " ▴  ", "▓██═", "████", "▓██═", "    "),
                    variant("veiled", " R  ", "◢██◣", "████", "◥██◤", "    "),
                ],
                secondary=("radiator",),
            ),
            section(
                "patrol_spine",
                "Patrol Spine",
                "hull",
                [
                    variant("sensor_rib", " R  ", "┌──┐", "█▒▒█", "└──┘", "    "),
                    variant("plain_rib", "    ", "◢██◣", "█◇▒█", "◥██◤", "    "),
                ],
                secondary=("sensors",),
                maximum=7,
            ),
            section(
                "sensor_crown",
                "Sensor Crown",
                "sensors",
                [
                    variant("crown", " ◢█◣", "◇███", "████", " ◥█◤", "    "),
                    variant("dish", "  R ", "◢██◣", "█☉██", "◥██◤", "    "),
                ],
            ),
            section(
                "needle",
                "Needle Prow",
                "main_gun",
                [
                    variant("long", "     ", "  ╾▙ ", "──▓▓▶", "  ╾▛ ", "     "),
                    variant("probe", "     ", "  ─▙ ", "─██▓▶", "  ─▛ ", "     "),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", "  ", "Y█", "  "),
            body=[
                variant("spine", " ▴", "██", "  "),
                variant("sensor", " R", "█◇", "  "),
            ],
            nose=variant("needle", "   ", "─▓▶", "   "),
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
                    variant("ribbed", "▓██═", "┌──┐", "█▒▒█", "└──┘", "▓██═"),
                    variant("sealed", "◢██◣", "████", "█░░█", "████", "◥██◤"),
                ],
            ),
            section(
                "false_holds",
                "False Cargo Holds",
                "cargo",
                [
                    variant("doors", " R    ", "┌────┐", "│▒◇▒▒│", "└────┘", " ▾    "),
                    variant("containers", "      ", "◢████◣", "█▒┤├▒█", "◥████◤", "      "),
                ],
                secondary=("weapons", "hull"),
                maximum=8,
            ),
            section(
                "masked_battery",
                "Masked Battery",
                "weapons",
                [
                    variant("closed", "    ", "◢██◣", "█≡██", "◥██◤", "    "),
                    variant("open", " ▴  ", "▓█▶ ", "████", "▓█▶ ", " ▾  "),
                ],
                secondary=("armor",),
            ),
            section(
                "merchant_prow",
                "Merchant Prow",
                "hull",
                [
                    variant("blunt", "    ", "██▙ ", "██▓▶", "██▛ ", "    "),
                    variant("tapered", "    ", "▓█▙ ", "███▶", "▓█▛ ", "    "),
                ],
                secondary=("main_gun",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", " █"),
            body=[
                variant("hold", "██", "█▒", "██"),
                variant("gun_hold", "▀█", "█◇", "▄█"),
            ],
            nose=variant("prow", "   ", "██▶", "   "),
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
                    variant("diamond", "◢██◣", "▓██▓", "▓██▓", "◥██◤"),
                    variant("open", " ▴  ", "▓██▓", "▓██▓", " ▾  "),
                ],
                secondary=("radiator",),
            ),
            section(
                "cabin",
                "Cabin",
                "habitat",
                [
                    variant("window", " R  ", "████", "█◇██", "    "),
                    variant("armored", "    ", "◢██◣", "█▒██", "◥██◤"),
                ],
                secondary=("sensors",),
                maximum=3,
            ),
            section(
                "landing_nose",
                "Landing Nose",
                "utility",
                [
                    variant("round", "   ", "▓▙ ", "██▶", "▓▛ "),
                    variant("probe", "   ", "─▙ ", "█▓▶", "─▛ "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", "  ", "Y▓", "  "),
            body=[variant("cabin", " ▴", "██", " ▾")],
            nose=variant("nose", "  ", "█▶", "  "),
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
                    variant("veined", " R  ", "◢█◇◣", "▓██▓", "█▒▒█", "▓██▓", "◥█◇◤", " ▾  "),
                ],
                secondary=("reactor",),
            ),
            section(
                "diamond_radiators",
                "Diamond Radiators",
                "radiator",
                [
                    variant("open", "◢█◣ ", " ╲  ", "┌──┐", "│▒▒│", "└──┘", " ╱  ", "◥█◤ "),
                    variant("folded", " ▴  ", " │  ", "┌──┐", "│◇▒│", "└──┘", " │  ", " ▾  "),
                ],
                secondary=("hull",),
                maximum=6,
            ),
            section(
                "habitat_petals",
                "Habitat Petals",
                "habitat",
                [
                    variant("spread", "◢██◣", " ╲╱ ", "████", "█☉██", "████", " ╱╲ ", "◥██◤"),
                    variant("folded", "    ", "◢██◣", "████", "█◇██", "████", "◥██◤", "    "),
                ],
                secondary=("bridge",),
            ),
            section(
                "lance",
                "Lance",
                "main_gun",
                [
                    variant("needle", "     ", "     ", "  ─▙ ", "──█▓▶", "  ─▛ ", "     ", "     "),
                    variant("fork", "     ", "     ", "─▓█▙ ", "─██▓▶", "─▓█▛ ", "     ", "     "),
                ],
                secondary=("weapons",),
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "Y█", " ▾"),
            body=[
                variant("fins", "◢█", "██", "◥█"),
                variant("petal", "▀█", "█◇", "▄█"),
            ],
            nose=variant("lance", "   ", "─█▶", "   "),
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
                    variant("shop", " R  ", "┌──┐", "│◇▒│", "│▒▒│", "└──┘", " ▾  "),
                    variant("patched", "    ", "◢██◣", "█▒◇█", "█░▒█", "◥██◤", "    "),
                ],
                secondary=("reactor",),
            ),
            section(
                "cargo_modules",
                "Cargo Modules",
                "cargo",
                [
                    variant("stack", "      ", "┌────┐", "│▒▒▒▒│", "│▒◇▒▒│", "└────┘", "      "),
                    variant("pods", " ◢██◣ ", " ╲  ╱ ", "██▒▒██", "██◇▒██", " ╱  ╲ ", " ◥██◤ "),
                ],
                secondary=("hull",),
                maximum=9,
            ),
            section(
                "hearth_drum",
                "Hearth Drum",
                "habitat",
                [
                    variant("turning", " ◢██◣ ", "╱    ╲", "█◇████", "█☉████", "╲    ╱", " ◥██◤ "),
                    variant("locked", "      ", "◢████◣", "█▒◇▒▒█", "█▒☉▒▒█", "◥████◤", "      "),
                ],
                secondary=("bridge",),
            ),
            section(
                "mining_prow",
                "Mining Prow",
                "main_gun",
                [
                    variant("laser", "     ", "  ▟  ", "──█▓▶", "  ▜  ", "     ", "     "),
                    variant("tractor", "     ", " ◢█◣ ", "─█◇█▶", " ◥█◤ ", "     ", "     "),
                ],
                secondary=("utility",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", "  "),
            body=[
                variant("cargo", "██", "█▒", "██"),
                variant("home", "▀█", "█☉", "▄█"),
            ],
            nose=variant("laser", "   ", "─█▶", "   "),
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
                    variant("pearl", " ◢██◣", "◢████", "█████", "█▒◇██", "█████", "◥████", " ◥██◤"),
                    variant("scarred", "  ◢█◣", "◢██▒█", "██◇██", "█▒▒██", "█████", "◥██▒█", "  ◥█◤"),
                ],
            ),
            section(
                "weapon_ring",
                "Weapon Ring",
                "weapons",
                [
                    variant("ports", " R    ", "◢████◣", "█◇█◇██", "██☉███", "█◇██◇█", "◥████◤", "   ▾  "),
                    variant("sealed", "      ", " ◢██◣ ", "◢████◣", "█▒◊▒██", "◥████◤", " ◥██◤ ", "      "),
                ],
                secondary=("hangar", "hull"),
                maximum=5,
            ),
            section(
                "troop_lobe",
                "Troop Lobe",
                "hangar",
                [
                    variant("open", " ◢██◣", "◢█◇██", "█████", "██☉██", "█████", "◥██▒█", "  ◥█◤"),
                    variant("heavy", "  ◢█◣", "◢████", "█▒▒██", "██◇██", "█████", "◥████", " ◥██◤"),
                ],
                secondary=("habitat",),
            ),
            section(
                "beak",
                "Carapace Beak",
                "screens",
                [
                    variant("hook", "     ", " ◢█◣ ", "◢███▙", "██◇▓▶", "◥███▛", "  ◥█ ", "     "),
                    variant("round", "     ", "  ◢█◣", "◢████", "██☉▓▶", "◥████", "  ◥█◤", "     "),
                ],
                secondary=("sensors",),
            ),
        ],
        compact(
            tail=variant("drive", " █", "Y█", " ▾"),
            body=[
                variant("shell", "◢█", "█◇", "◥█"),
                variant("ports", "▀█", "█☉", "▄█"),
            ],
            nose=variant("beak", " ◢ ", "██▶", " ◥ "),
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
                    variant("joint", " ◢▒◣", "╱███", "█☉██", "╲███", " ◥▒◤"),
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
                    variant("muscle", "◢▒▒◣", "█▓▓█", "█◊▒█", "█▓▓█", "◥▒▒◤"),
                ],
                secondary=("armor",),
                maximum=8,
            ),
            section(
                "nerve_cluster",
                "Nerve Cluster",
                "sensors",
                [
                    variant("eye", " ◢█◣ ", "█☉███", "█████", "█◇▒██", " ◥█◤ "),
                    variant("many_eyes", " R R ", "◢◇█◇◣", "█████", "◥█◇█◤", "  ▾  "),
                ],
                secondary=("weapons",),
            ),
            section(
                "hardened_beak",
                "Hardened Beak",
                "main_gun",
                [
                    variant("fang", "    ", "◢▒▙ ", "██▓▶", "◥▒▛ ", "    "),
                    variant("barb", "    ", "╲█▙ ", "█▒▓▶", "╱█▛ ", "    "),
                ],
            ),
        ],
        compact(
            tail=variant("drive", " ▴", "Y▒", " ▾"),
            body=[
                variant("bone", "╲█", "█▒", "╱█"),
                variant("muscle", "◢▒", "█◊", "◥▒"),
            ],
            nose=variant("fang", " ◢ ", "█▓▶", " ◥ "),
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
                    variant("seven_bell", " Y▶═ ", "     ", "Y▟▓▓ ", "Y███▓", "Y███▓", "Y▜▓▓ ", " Y▶═ "),
                    variant("armored", " YY═ ", "Y▶▓  ", " ▟██▓", "Y████", "Y███▓", " ▜██▓", " YY═ "),
                ],
                secondary=("reactor", "spindrive"),
            ),
            section(
                "drive_citadel",
                "Drive Citadel",
                "armor",
                [
                    variant("buttress", "▓███═", " │   ", "┌───┐", "│▒▒▒│", "│▒◇▒│", "└───┘", "▓███═"),
                    variant("layered", "◢███◣", "▓███▓", "█████", "█▒▒▒█", "█████", "▓███▓", "◥███◤"),
                ],
                secondary=("spindrive",),
            ),
            section(
                "broadside_decks",
                "Broadside Decks",
                "weapons",
                [
                    variant("open_bays", " R    ", "▓█▶▓█▶", "┌────┐", "│▒◇▒▒│", "└────┘", "▓█▶▓█▶", " ▾    "),
                    variant("gunwalls", "▓███═ ", "─▓▙   ", "██████", "█◇▒◇██", "██████", "─▓▛   ", "▓███═ "),
                ],
                secondary=("hull", "armor"),
                maximum=10,
            ),
            section(
                "command_keep",
                "Command Keep",
                "bridge",
                [
                    variant("tower", "  R  ", " ┌─┐ ", "◢███◣", "█☉███", "█████", "◥███◤", "  ▾  "),
                    variant("low_keep", "     ", " ◢█◣ ", "◢███◣", "█◇███", "█████", "◥███◤", "     "),
                ],
                secondary=("sensors", "screens"),
            ),
            section(
                "siege_prow",
                "Siege Prow",
                "main_gun",
                [
                    variant("triple", "      ", "      ", "─███▙ ", "─██▓▓▶", "─███▛ ", "      ", "      "),
                    variant("ram", "      ", "  ◢█◣ ", "─████▙", "─███▓▶", "─████▛", "  ◥█◤ ", "      "),
                ],
                secondary=("armor",),
            ),
        ],
        compact(
            tail=variant("drive", "██", "Y█", "██"),
            body=[
                variant("gunwall", "█▶", "██", "█▶"),
                variant("armor", "██", "█◇", "██"),
            ],
            nose=variant("siege", " ██", "██▶", " ██"),
            maximum=15,
        ),
    )

    return [
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
