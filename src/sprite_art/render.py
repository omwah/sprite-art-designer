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
from .model import (
    COLOR_CODE_TO_SET,
    SURFACE_MASK_CODE,
    ColorSet,
    Palette,
    PaletteCatalog,
    Section,
    Sprite,
    Tier,
    Variant,
    View,
)

VOID_BG = "black"

def _consume_legacy_color_draws(rng: random.Random) -> None:
    """Keep converted ship variant choices stable after removing color RNG."""

    rng.choice((0, 1))
    rng.choice((0, 1))


def glyph_color_slot(glyph: str) -> int:
    """Map a glyph to its full, structural, recess, or facet palette slot."""

    if glyph in BRIGHT_CHARS:
        return 0
    if glyph in DARK_CHARS:
        return 2
    if glyph in HULL_CHARS:
        return 1
    return 3


def glyph_colors(
    glyph: str,
    color_set: ColorSet,
    *,
    primary_only: bool = False,
) -> tuple[str, str | None]:
    """Return foreground and optional facet background for one authored cell."""

    if primary_only:
        return color_set.colors[0], None
    slot = glyph_color_slot(glyph)
    foreground = color_set.color_for_slot(slot)
    background = color_set.colors[0] if slot == 3 else None
    return foreground, background


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
    _consume_legacy_color_draws(rng)
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


def selected_tier(sprite: Sprite, *, width: int, height: int, view_id: str) -> Tier:
    """Return the structural tier selected for an exact render size."""

    if width < 1 or height < 1:
        raise ValueError("width and height must be positive")
    if view_id not in sprite.views:
        raise KeyError(f"sprite {sprite.id!r} has no view {view_id!r}")
    return _select_tier(sprite.views[view_id], width, height)


def active_variant_at_cell(
    sprite: Sprite,
    palettes: PaletteCatalog,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    seed: int = 0,
    archetype_id: str = "humanoid_diplomat",
    view_id: str = "horizontal",
    facing: str | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> Variant | None:
    """Return the active source variant occupying one rendered preview cell."""

    if not 0 <= x < width or not 0 <= y < height:
        return None
    view = sprite.views[view_id]
    tier = _select_tier(view, width, height)
    active = selected_variants(
        sprite,
        palettes,
        width=width,
        height=height,
        seed=seed,
        archetype_id=archetype_id,
        view_id=view_id,
        variant_overrides=variant_overrides,
    )
    variants = [active[id(section.variants)] for section in tier.sections]
    horizontal = view.axis != "vertical"
    repeats = [section.repeat for section in tier.sections]
    natural_width = sum(variant.width * repeat for variant, repeat in zip(variants, repeats))
    natural_height = (
        variants[0].height
        if horizontal
        else sum(variant.height * repeat for variant, repeat in zip(variants, repeats))
    )
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        if horizontal:
            x = width - 1 - x
        else:
            y = height - 1 - y
    natural_x = x - (width - natural_width) // 2 if natural_width <= width else x + (natural_width - width) // 2
    natural_y = y - (height - natural_height) // 2 if natural_height <= height else y + (natural_height - height) // 2
    if horizontal:
        if not 0 <= natural_y < natural_height:
            return None
        cursor = 0
        for variant, repeat in zip(variants, repeats):
            length = variant.width * repeat
            if cursor <= natural_x < cursor + length:
                return variant
            cursor += length
    else:
        if not 0 <= natural_x < natural_width:
            return None
        cursor = 0
        for variant, repeat in reversed(list(zip(variants, repeats))):
            length = variant.height * repeat
            if cursor <= natural_y < cursor + length:
                return variant
            cursor += length
    return None


def _compose_horizontal(
    tier: Tier,
    rng: random.Random,
    target: int,
    highlight_variant: Variant | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    chosen = [
        _choose_variant(section, rng, variant_overrides) for section in tier.sections
    ]
    repeats = [section.repeat for section in tier.sections]
    height = chosen[0].height
    rows = [
        "".join(
            variant.cells[row] * repeat
            for variant, repeat in zip(chosen, repeats)
        )
        for row in range(height)
    ]
    color_mask = [
        "".join(
            variant.color_mask[row] * repeat
            for variant, repeat in zip(chosen, repeats)
        )
        for row in range(height)
    ]
    highlight_mask = [
        "".join(
            ("1" if highlight_variant in section.variants else "0")
            * variant.width
            * repeat
            for section, variant, repeat in zip(tier.sections, chosen, repeats)
        )
        for _ in range(height)
    ]
    return rows, color_mask, highlight_mask


def _compose_vertical(
    tier: Tier,
    rng: random.Random,
    target: int,
    highlight_variant: Variant | None = None,
    variant_overrides: dict[int, Variant] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    chosen = [
        _choose_variant(section, rng, variant_overrides) for section in tier.sections
    ]
    repeats = [section.repeat for section in tier.sections]
    rows: list[str] = []
    color_mask: list[str] = []
    highlight_mask: list[str] = []
    # Sections remain authored tail -> nose. Nose-up art is displayed top-down,
    # so the semantic section order is reversed without changing each part.
    for section, variant, repeat in reversed(list(zip(tier.sections, chosen, repeats))):
        for _ in range(repeat):
            rows.extend(variant.cells)
            color_mask.extend(variant.color_mask)
            marker = "1" if highlight_variant in section.variants else "0"
            highlight_mask.extend(
                [marker * variant.width for _ in range(variant.height)]
            )
    return rows, color_mask, highlight_mask


def _flip_mask_horizontal(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def _flip_mask_vertical(rows: list[str]) -> list[str]:
    return list(reversed(rows))


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
        rows, _color_mask, _highlight_mask = _compose_horizontal(
            tier, rng, width, variant_overrides=variant_overrides
        )
    elif view.axis == "vertical":
        rows, _color_mask, _highlight_mask = _compose_vertical(
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
) -> tuple[list[str], list[str], list[str]]:
    view = sprite.views[view_id]
    tier = _select_tier(view, width, height)
    if view.axis == "horizontal":
        rows, color_mask, highlight_mask = _compose_horizontal(
            tier, rng, width, highlight_variant, variant_overrides
        )
    elif view.axis == "vertical":
        rows, color_mask, highlight_mask = _compose_vertical(
            tier, rng, height, highlight_variant, variant_overrides
        )
    else:
        variant = _choose_variant(tier.sections[0], rng, variant_overrides)
        rows = list(variant.cells)
        color_mask = list(variant.color_mask)
        marker = "1" if highlight_variant in tier.sections[0].variants else "0"
        highlight_mask = [marker * variant.width for _ in range(variant.height)]
    requested_facing = facing or view.canonical_facing
    if view.mirror_facing is not None and requested_facing == view.mirror_facing:
        if view.axis == "horizontal":
            rows = flip_rows_horizontal(rows)
            color_mask = _flip_mask_horizontal(color_mask)
            highlight_mask = _flip_mask_horizontal(highlight_mask)
        elif view.axis == "vertical":
            rows = flip_rows_vertical(rows)
            color_mask = _flip_mask_vertical(color_mask)
            highlight_mask = _flip_mask_vertical(highlight_mask)
    return rows, color_mask, highlight_mask


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


def _add_preview_margin(
    rows: list[str],
    highlight_mask: list[str],
    axis: str,
) -> tuple[list[str], list[str]]:
    """Add a one-cell preview margin and project a selected part into it."""

    width = len(rows[0])
    blank_row = " " * (width + 2)
    blank_mask = "0" * (width + 2)
    padded_rows = [f" {row} " for row in rows]
    padded_mask = [f"0{row}0" for row in highlight_mask]
    if axis == "horizontal":
        projected = "".join(
            "1" if any(row[column] == "1" for row in highlight_mask) else "0"
            for column in range(width)
        )
        margin_mask = f"0{projected}0"
        return [blank_row, *padded_rows, blank_row], [
            margin_mask,
            *padded_mask,
            margin_mask,
        ]
    if axis == "vertical":
        padded_mask = [
            f"{'1' if '1' in row else '0'}{row}{'1' if '1' in row else '0'}"
            for row in highlight_mask
        ]
    return [blank_row, *padded_rows, blank_row], [
        blank_mask,
        *padded_mask,
        blank_mask,
    ]


def _paint_grid(
    rows: list[str],
    color_mask: list[str],
    palette: Palette,
    width: int,
    height: int,
    reverse_vertical_bias: bool = False,
    highlight_mask: list[str] | None = None,
    preview_margin_axis: str | None = None,
    primary_colors: bool = False,
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
    fitted_colors = _fit_grid(
        color_mask,
        width,
        height,
        reverse_vertical_bias=reverse_vertical_bias,
    )
    fitted_colors = [
        "".join(
            code if code in COLOR_CODE_TO_SET else SURFACE_MASK_CODE
            for code in row
        )
        for row in fitted_colors
    ]
    if preview_margin_axis is not None:
        fitted_rows, fitted_mask = _add_preview_margin(
            fitted_rows,
            fitted_mask,
            preview_margin_axis,
        )
        fitted_colors = [
            SURFACE_MASK_CODE * (width + 2),
            *(f"{SURFACE_MASK_CODE}{row}{SURFACE_MASK_CODE}" for row in fitted_colors),
            SURFACE_MASK_CODE * (width + 2),
        ]
        width += 2
        height += 2
    for y, line in enumerate(fitted_rows):
        for x, glyph in enumerate(line):
            highlighted = fitted_mask[y][x] == "1"
            background = "#4c1d95" if highlighted else VOID_BG
            if glyph == " ":
                output.append(" ", style=f"on {background}" if highlighted else "")
            else:
                color_set_id = COLOR_CODE_TO_SET[fitted_colors[y][x]]
                color_set = palette.color_set(color_set_id)
                foreground, facet_background = glyph_colors(
                    glyph, color_set, primary_only=primary_colors
                )
                cell_background = background if highlighted else facet_background
                style = foreground
                if cell_background is not None:
                    style += f" on {cell_background}"
                output.append(
                    glyph,
                    style=style,
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
    preview_margin: bool = False,
    primary_colors: bool = False,
) -> Text:
    """Render one deterministic Rich sprite, optionally with a preview margin.

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
    _consume_legacy_color_draws(rng)
    rows, color_mask, highlight_mask = _compose_grid_with_highlight(
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
        color_mask,
        palette,
        width,
        height,
        reverse_vertical_bias,
        highlight_mask=highlight_mask if highlight_variant is not None else None,
        preview_margin_axis=view.axis if preview_margin else None,
        primary_colors=primary_colors,
    )
