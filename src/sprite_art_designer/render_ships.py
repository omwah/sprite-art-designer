"""Render a terminal gallery of authored ship sprites and tiers."""

from __future__ import annotations

import argparse
import secrets
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from yaml import YAMLError

from sprite_art import (
    ARCHETYPE_IDS,
    PaletteCatalog,
    Sprite,
    SpriteValidationError,
    Tier,
    View,
    load_palette_catalog,
    load_sprite_directory,
    render_sprite,
)

DEFAULT_ASSET_ROOT = Path(__file__).resolve().parents[2] / "assets"
DEFAULT_SPRITES_DIRECTORY = DEFAULT_ASSET_ROOT / "sprites"
DEFAULT_PALETTE_CATALOG = DEFAULT_ASSET_ROOT / "palettes.yaml"


class GallerySelectionError(ValueError):
    """A requested ship or tier is not present in the loaded gallery."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render ship sprite types and detail tiers to the terminal.",
    )
    parser.add_argument(
        "sprites_directory",
        nargs="?",
        type=Path,
        default=DEFAULT_SPRITES_DIRECTORY,
        help=f"Sprite YAML directory (default: {DEFAULT_SPRITES_DIRECTORY})",
    )
    parser.add_argument(
        "--archetype",
        "--archetype-palette",
        choices=ARCHETYPE_IDS,
        default="humanoid_diplomat",
        help="Archetype palette to apply (default: humanoid_diplomat)",
    )
    parser.add_argument(
        "--ship-type",
        "--ship-types",
        dest="ship_types",
        action="extend",
        nargs="+",
        metavar="ID",
        help="Ship type IDs to render; may be repeated (default: all)",
    )
    parser.add_argument(
        "--tier",
        "--tiers",
        dest="tiers",
        action="extend",
        nargs="+",
        metavar="ID",
        help="Tier IDs to render; may be repeated (default: all)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Deterministic render seed (default: a random 64-bit seed)",
    )
    return parser


def _deduplicate(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _select_ships(
    sprites: dict[str, Sprite], requested_ids: Sequence[str] | None
) -> list[Sprite]:
    ships = {sprite.id: sprite for sprite in sprites.values() if sprite.kind == "ship"}
    if not ships:
        raise GallerySelectionError("no ship sprites were found")
    if requested_ids is None:
        return [ships[sprite_id] for sprite_id in sorted(ships)]

    selected_ids = _deduplicate(requested_ids)
    missing = [sprite_id for sprite_id in selected_ids if sprite_id not in ships]
    if missing:
        available = ", ".join(sorted(ships))
        raise GallerySelectionError(
            f"unknown ship type(s): {', '.join(missing)}; available: {available}"
        )
    return [ships[sprite_id] for sprite_id in selected_ids]


def _gallery_view(sprite: Sprite) -> View:
    return sprite.views.get("horizontal", next(iter(sprite.views.values())))


def _select_tiers(view: View, requested_ids: Sequence[str] | None) -> list[Tier]:
    if requested_ids is None:
        return list(view.tiers)

    tiers = {tier.id: tier for tier in view.tiers}
    selected_ids = _deduplicate(requested_ids)
    missing = [tier_id for tier_id in selected_ids if tier_id not in tiers]
    if missing:
        available = ", ".join(tier.id for tier in view.tiers)
        raise GallerySelectionError(
            f"view {view.id!r} has no tier(s) {', '.join(missing)}; available: {available}"
        )
    return [tiers[tier_id] for tier_id in selected_ids]


def _tier_dimensions(view: View, tier: Tier) -> tuple[int, int]:
    if view.axis == "horizontal":
        width = sum(
            section.variants[0].width * section.repeat
            for section in tier.sections
        )
        return width, tier.cross_axis_size(view.axis)
    if view.axis == "vertical":
        height = sum(
            section.variants[0].height * section.repeat
            for section in tier.sections
        )
        return tier.cross_axis_size(view.axis), height
    variant = tier.sections[0].variants[0]
    return variant.width, variant.height


def _render_tier(
    sprite: Sprite,
    view: View,
    tier: Tier,
    palettes: PaletteCatalog,
    *,
    seed: int,
    archetype_id: str,
) -> tuple[Text, int, int]:
    isolated_view = replace(view, tiers=[tier])
    isolated_sprite = replace(
        sprite,
        views={**sprite.views, view.id: isolated_view},
    )
    width, height = _tier_dimensions(view, tier)
    art = render_sprite(
        isolated_sprite,
        palettes,
        width=width,
        height=height,
        seed=seed,
        archetype_id=archetype_id,
        view_id=view.id,
    )
    return art, width, height


def render_gallery(
    sprites: dict[str, Sprite],
    palettes: PaletteCatalog,
    console: Console,
    *,
    sprites_directory: Path,
    ship_type_ids: Sequence[str] | None,
    tier_ids: Sequence[str] | None,
    archetype_id: str,
    seed: int,
) -> None:
    ships = _select_ships(sprites, ship_type_ids)
    selections = [
        (ship, _gallery_view(ship), _select_tiers(_gallery_view(ship), tier_ids))
        for ship in ships
    ]

    console.print(
        Text.assemble(
            ("Ship sprite gallery", "bold"),
            f" · archetype={archetype_id} · seed={seed}",
        )
    )
    console.print(f"Sprites: {sprites_directory.resolve()}", style="dim")
    for ship, view, tiers in selections:
        console.rule(f"{ship.name} ({ship.id}) · {view.name}")
        for tier in tiers:
            art, width, height = _render_tier(
                ship,
                view,
                tier,
                palettes,
                seed=seed,
                archetype_id=archetype_id,
            )
            console.print(
                Panel.fit(
                    art,
                    title=f"{tier.name} ({tier.id}) · {width}×{height}",
                    border_style="cyan",
                    padding=(0, 1),
                )
            )


def _default_console() -> Console:
    """Keep the rendered palette and styling when stdout is redirected."""

    return Console(force_terminal=True, color_system="truecolor")


def main(argv: Sequence[str] | None = None, *, console: Console | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    output = console or _default_console()
    seed = args.seed if args.seed is not None else secrets.randbits(64)

    try:
        sprites = load_sprite_directory(args.sprites_directory)
        palettes = load_palette_catalog(DEFAULT_PALETTE_CATALOG)
        render_gallery(
            sprites,
            palettes,
            output,
            sprites_directory=args.sprites_directory,
            ship_type_ids=args.ship_types,
            tier_ids=args.tiers,
            archetype_id=args.archetype,
            seed=seed,
        )
    except (OSError, SpriteValidationError, GallerySelectionError, YAMLError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
