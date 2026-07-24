"""Deterministic composition and Rich painting for sprite documents."""

from __future__ import annotations

import random
from dataclasses import dataclass

from rich.text import Text

from .glyphs import (
    BRIGHT_CHARS,
    DARK_CHARS,
    HULL_CHARS,
    flip_rows_horizontal,
    flip_rows_vertical,
)
from .model import Palette, PaletteCatalog, Section, Sprite, Tier, Variant, View

VOID_BG = "black"
WINDOW_PROBABILITY = 0.05


@dataclass(frozen=True)
class RenderRequest:
    sprite_id: str
    width: int
    height: int
    seed: int = 0
    archetype_id: str = "humanoid_diplomat"
    view_id: str = "horizontal"
    facing: str | None = None


def _choose_variant(
    section: Section,
    rng: random.Random,
    variant_overrides: dict[int, Variant] | None = None,
) -> Variant:
    weights = [variant.weight for variant in section.variants]
    if len(set(weights)) == 1:
        chosen = rng.choice(section.variants)
    else:
        chosen = rng.choices(section.variants, weights=weights, k=1)[0]
    variant_override = (
        variant_overrides.get(id(section.variants)) if variant_overrides else None
    )
    if variant_override is not None and any(
        variant is variant_override for variant in section.variants
    ):
        return variant_override
    return chosen


def selected_variants(
    sprite: Sprite,
    palettes: PaletteCatalog,
    *,
    width: int,
    height: int,
    seed: int = 0,
    archetype_id: str = "humanoid_diplomat",
    view_id: str = "horizontal",
    variant_overrides: dict[int, Variant] | None = None,
) -> dict[int, Variant]:
    """Return the variants used by the deterministic render for one preview."""

    if width < 1 or height < 1:
        raise ValueError("width and height must be positive")
    sprite.validate()
    palettes.validate()
    if view_id not in sprite.views:
        raise KeyError(f"sprite {sprite.id!r} has no view {view_id!r}")
    rng_seed = f"{seed}|{sprite.kind}|{sprite.role}"
    if archetype_id:
        rng_seed += f"|{archetype_id}"
    rng = random.Random(rng_seed)
    palette = palettes.resolve(archetype_id)
    rng.choice(palette.beacon)
    rng.choice(palette.engine)
    tier = _select_tier(sprite.views[view_id], width, height)
    return {
        id(section.variants): _choose_variant(section, rng, variant_overrides)
        for section in tier.sections
    }


def _select_tier(view: View, width: int, height: int) -> Tier:
    if view.axis == "horizontal":
        budget = height
        for tier in view.tiers:
            if tier.cross_axis_size(view.axis) <= budget:
                return tier
    elif view.axis == "vertical":
        budget = width
        for tier in view.tiers:
            if tier.cross_axis_size(view.axis) <= budget:
                return tier
    else:
        for tier in view.tiers:
            variant = tier.sections[0].variants[0]
            if variant.width <= width and variant.height <= height:
                return tier
    return view.tiers[-1]


def _repeat_counts(
    sections: list[Section],
    chosen: list[Variant],
    target: int,
    horizontal: bool,
) -> list[int]:
    footprints = [
        variant.width if horizontal else variant.height for variant in chosen
    ]
    repeats = [section.min_repeat for section in sections]
    total = sum(size * count for size, count in zip(footprints, repeats))
    growable = [
        index
        for index, section in enumerate(sections)
        if section.max_repeat > section.min_repeat
    ]
    progressed = True
    while progressed and growable:
        progressed = False
        for index in growable:
            if (
                repeats[index] < sections[index].max_repeat
                and total + footprints[index] <= target
            ):
                repeats[index] += 1
                total += footprints[index]
                progressed = True
    return repeats


def _compose_horizontal(
    tier: Tier,
    rng: random.Random,
    target: int,
    highlight_variant: Variant | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> tuple[list[str], list[str]]:
    chosen = [
        _choose_variant(section, rng, variant_overrides) for section in tier.sections
    ]
    repeats = _repeat_counts(tier.sections, chosen, target, horizontal=True)
    height = chosen[0].height
    rows = [
        "".join(
            variant.cells[row] * repeat
            for variant, repeat in zip(chosen, repeats)
        )
        for row in range(height)
    ]
    mask = [
        "".join(
            ("1" if highlight_variant in section.variants else "0")
            * variant.width
            * repeat
            for section, variant, repeat in zip(tier.sections, chosen, repeats)
        )
        for _ in range(height)
    ]
    return rows, mask


def _compose_vertical(
    tier: Tier,
    rng: random.Random,
    target: int,
    highlight_variant: Variant | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> tuple[list[str], list[str]]:
    chosen = [
        _choose_variant(section, rng, variant_overrides) for section in tier.sections
    ]
    repeats = _repeat_counts(tier.sections, chosen, target, horizontal=False)
    rows: list[str] = []
    mask: list[str] = []
    # Sections remain authored tail -> nose. Nose-up art is displayed top-down,
    # so the semantic section order is reversed without changing each part.
    for section, variant, repeat in reversed(list(zip(tier.sections, chosen, repeats))):
        for _ in range(repeat):
            rows.extend(variant.cells)
            marker = "1" if highlight_variant in section.variants else "0"
            mask.extend([marker * variant.width for _ in range(variant.height)])
    return rows, mask


def compose_grid(
    sprite: Sprite,
    rng: random.Random,
    width: int,
    height: int,
    view_id: str,
    facing: str | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> list[str]:
    view = sprite.views[view_id]
    tier = _select_tier(view, width, height)
    if view.axis == "horizontal":
        rows, _mask = _compose_horizontal(
            tier, rng, width, variant_overrides=variant_overrides
        )
    elif view.axis == "vertical":
        rows, _mask = _compose_vertical(
            tier, rng, height, variant_overrides=variant_overrides
        )
    else:
        rows = list(_choose_variant(tier.sections[0], rng, variant_overrides).cells)
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        if view.axis == "horizontal":
            rows = flip_rows_horizontal(rows)
        elif view.axis == "vertical":
            rows = flip_rows_vertical(rows)
    return rows


def _compose_grid_with_highlight(
    sprite: Sprite,
    rng: random.Random,
    width: int,
    height: int,
    view_id: str,
    highlight_variant: Variant | None,
    facing: str | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> tuple[list[str], list[str]]:
    view = sprite.views[view_id]
    tier = _select_tier(view, width, height)
    if view.axis == "horizontal":
        rows, mask = _compose_horizontal(
            tier, rng, width, highlight_variant, variant_overrides
        )
    elif view.axis == "vertical":
        rows, mask = _compose_vertical(
            tier, rng, height, highlight_variant, variant_overrides
        )
    else:
        variant = _choose_variant(tier.sections[0], rng, variant_overrides)
        rows = list(variant.cells)
        marker = "1" if highlight_variant in tier.sections[0].variants else "0"
        mask = [marker * variant.width for _ in range(variant.height)]
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        if view.axis == "horizontal":
            rows = flip_rows_horizontal(rows)
            mask = flip_rows_horizontal(mask)
        elif view.axis == "vertical":
            rows = flip_rows_vertical(rows)
            mask = flip_rows_vertical(mask)
    return rows, mask


def _fit_grid(
    rows: list[str],
    width: int,
    height: int,
    *,
    reverse_vertical_bias: bool = False,
) -> list[str]:
    natural_height = len(rows)
    natural_width = max((len(row) for row in rows), default=0)
    pad_delta = max(0, height - natural_height)
    crop_delta = max(0, natural_height - height)
    pad_top = (
        (pad_delta + 1) // 2 if reverse_vertical_bias else pad_delta // 2
    )
    crop_top = (
        (crop_delta + 1) // 2 if reverse_vertical_bias else crop_delta // 2
    )
    fitted: list[str] = []
    for y in range(height):
        source = y - pad_top + crop_top
        if not 0 <= source < natural_height:
            fitted.append(" " * width)
            continue
        row = rows[source].ljust(natural_width)
        if natural_width <= width:
            left = (width - natural_width) // 2
            fitted.append(
                (" " * left)
                + row
                + (" " * (width - natural_width - left))
            )
        else:
            start = (natural_width - width) // 2
            fitted.append(row[start : start + width].ljust(width))
    return fitted


def _paint_grid(
    rows: list[str],
    palette: Palette,
    beacon_color: str,
    engine_color: str,
    rng: random.Random,
    width: int,
    height: int,
    reverse_vertical_bias: bool = False,
    highlight_mask: list[str] | None = None,
) -> Text:
    output = Text()
    fitted_rows = _fit_grid(
        rows, width, height, reverse_vertical_bias=reverse_vertical_bias
    )
    fitted_mask = (
        _fit_grid(
            highlight_mask, width, height, reverse_vertical_bias=reverse_vertical_bias
        )
        if highlight_mask is not None
        else ["0" * width for _ in range(height)]
    )
    for y, line in enumerate(fitted_rows):
        for x, glyph in enumerate(line):
            highlighted = fitted_mask[y][x] == "1"
            background = "#4c1d95" if highlighted else VOID_BG
            if glyph == " ":
                output.append(" ", style=f"on {background}" if highlighted else "")
            elif glyph == "R":
                output.append(
                    "▀",
                    style=f"{beacon_color} on {background}"
                    if highlighted
                    else beacon_color,
                )
            elif glyph == "r":
                output.append(
                    "▄",
                    style=f"{beacon_color} on {background}"
                    if highlighted
                    else beacon_color,
                )
            elif glyph == "Y":
                output.append(
                    "▄",
                    style=f"{engine_color} on {background}"
                    if highlighted
                    else engine_color,
                )
            elif glyph == "y":
                output.append(
                    "▀",
                    style=f"{engine_color} on {background}"
                    if highlighted
                    else engine_color,
                )
            elif glyph in HULL_CHARS:
                if glyph in BRIGHT_CHARS and rng.random() < WINDOW_PROBABILITY:
                    color = rng.choice(palette.window)
                elif glyph in DARK_CHARS:
                    color = palette.dark
                elif glyph in BRIGHT_CHARS:
                    color = palette.bright
                else:
                    color = palette.mid
                output.append(glyph, style=f"{color} on {background}")
            else:
                output.append(
                    glyph,
                    style=f"{palette.facet} on {background if highlighted else palette.bright}",
                )
        if y < height - 1:
            output.append("\n")
    return output


def render_sprite(
    sprite: Sprite,
    palettes: PaletteCatalog,
    *,
    width: int,
    height: int,
    seed: int = 0,
    archetype_id: str = "humanoid_diplomat",
    view_id: str = "horizontal",
    facing: str | None = None,
    highlight_variant: Variant | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> Text:
    """Render one exact-sized, deterministic Rich sprite.

    The seed string matches Edge's current ship generator for ship documents,
    allowing the converted horizontal grammars to preserve their identities.
    Facing remains a post-composition transform and is deliberately absent from
    the seed.
    """

    if width < 1 or height < 1:
        raise ValueError("width and height must be positive")
    sprite.validate()
    palettes.validate()
    if view_id not in sprite.views:
        raise KeyError(f"sprite {sprite.id!r} has no view {view_id!r}")
    rng_seed = f"{seed}|{sprite.kind}|{sprite.role}"
    if archetype_id:
        rng_seed += f"|{archetype_id}"
    rng = random.Random(rng_seed)
    palette = palettes.resolve(archetype_id)
    beacon_color = rng.choice(palette.beacon)
    engine_color = rng.choice(palette.engine)
    rows, highlight_mask = _compose_grid_with_highlight(
        sprite,
        rng,
        width,
        height,
        view_id,
        highlight_variant,
        facing,
        variant_overrides,
    )
    view = sprite.views[view_id]
    requested_facing = facing or view.canonical_facing
    reverse_vertical_bias = (
        view.axis == "vertical"
        and view.mirror_facing is not None
        and requested_facing == view.mirror_facing
    )
    return _paint_grid(
        rows,
        palette,
        beacon_color,
        engine_color,
        rng,
        width,
        height,
        reverse_vertical_bias,
        highlight_mask=highlight_mask if highlight_variant is not None else None,
    )
