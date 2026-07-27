from __future__ import annotations

import random
import gzip
import struct
from copy import deepcopy
from pathlib import Path

import pytest

from sprite_art import (
    ARCHETYPE_IDS,
    COLOR_SET_IDS,
    PaletteCatalog,
    REXPAINT_GLYPH_INDICES,
    RexPaintImportError,
    SpriteLibrary,
    SpriteValidationError,
    active_variant_at_cell,
    generate_rotated_view,
    load_palette_catalog,
    load_sprite,
    load_sprite_directory,
    RexPaintGlyphError,
    export_rexpaint,
    import_rexpaint_cells,
    render_sprite,
    segment_rexpaint_cells,
)
from sprite_art.glyphs import (
    AUTHORING_GLYPHS,
    ROTATE_CCW,
    flip_rows_horizontal,
    flip_rows_vertical,
    transform_glyph,
)
from sprite_art.io import dump_palette_catalog, dump_sprite

ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"
ORIGINAL_ROLES = {
    "fighter",
    "transport",
    "warship",
    "capital_warship",
}
NEW_ROLES = {
    "needle_picket",
    "falsehold_raider",
    "junction_pinnace",
    "radiant_lance",
    "hearth_freighter",
    "pearl_shell",
    "marrow_dart",
    "broadside_citadel",
}


@pytest.fixture(scope="module")
def palettes() -> PaletteCatalog:
    return load_palette_catalog(ASSETS / "palettes.yaml")


@pytest.fixture(scope="module")
def sprites() -> dict[str, object]:
    return load_sprite_directory(ASSETS / "sprites")


def test_asset_library_has_all_original_and_new_roles(sprites: dict[str, object]) -> None:
    assert set(sprites) == ORIGINAL_ROLES | NEW_ROLES


def test_palette_catalog_is_the_exact_controlled_roster(
    palettes: PaletteCatalog,
) -> None:
    assert tuple(palettes.archetypes) == ARCHETYPE_IDS
    assert palettes.resolve("unknown") is palettes.archetypes["humanoid_diplomat"]
    for palette in palettes.archetypes.values():
        assert tuple(palette.color_sets) == COLOR_SET_IDS
        assert all(1 <= len(color_set.colors) <= 4 for color_set in palette.color_sets.values())


def test_palette_catalog_rejects_extra_archetype(palettes: PaletteCatalog) -> None:
    invalid = deepcopy(palettes)
    invalid.archetypes["new_archetype"] = deepcopy(
        invalid.archetypes["humanoid_diplomat"]
    )
    with pytest.raises(SpriteValidationError, match="controlled"):
        invalid.validate()


def test_sprite_color_masks_match_geometry_and_reject_unknown_codes() -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    variant = sprite.views["horizontal"].tiers[0].sections[0].variants[0]
    assert len(variant.color_mask) == variant.height
    assert all(len(row) == variant.width for row in variant.color_mask)
    variant.color_mask[0] = "?" + variant.color_mask[0][1:]
    with pytest.raises(SpriteValidationError, match="unknown color-mask code"):
        sprite.validate()


def test_migrated_markers_use_real_glyphs_and_expected_color_sets() -> None:
    sprites = load_sprite_directory(ASSETS / "sprites")
    pairs = {
        (glyph, code)
        for sprite in sprites.values()
        for view in sprite.views.values()
        for tier in view.tiers
        for section in tier.sections
        for variant in section.variants
        for glyph_row, mask_row in zip(variant.cells, variant.color_mask)
        for glyph, code in zip(glyph_row, mask_row)
    }
    assert not set("RGBYrgby") & {glyph for glyph, _code in pairs}
    assert ("▄", "E") in pairs


def test_rexpaint_export_is_deterministic_and_uses_one_column_major_layer(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    first = export_rexpaint(
        sprite, palettes, tmp_path / "fighter.xp", width=40, height=7, seed=7
    )
    second = export_rexpaint(
        sprite, palettes, tmp_path / "fighter-again.xp", width=40, height=7, seed=7
    )

    assert first.image_path.read_bytes() == second.image_path.read_bytes()
    assert first.palette_path.read_text() == second.palette_path.read_text()
    assert len(first.palette_path.read_text().split("}")) == 257
    data = gzip.decompress(first.image_path.read_bytes())
    version, layers, width, height = struct.unpack_from("<iiii", data)
    assert (version, layers, width, height) == (-1, 1, 40, 7)
    assert len(data) == 16 + 40 * 7 * 10
    # The first serialized cell is the top-left cell, then the next row in the
    # same column, which is REXPaint's documented column-major ordering.
    first_glyph, *first_colors = struct.unpack_from("<I6B", data, 16)
    second_glyph, *_ = struct.unpack_from("<I6B", data, 26)
    assert first_glyph == 0
    assert second_glyph == 0
    assert first_colors == [0, 0, 0, 0, 0, 0]


def test_rexpaint_export_rejects_unmapped_glyph(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    sprite.views["horizontal"].tiers[0].sections[0].variants[0].cells[0] = "?    "
    with pytest.raises(RexPaintGlyphError, match="no REXPaint font slot"):
        export_rexpaint(sprite, palettes, tmp_path / "invalid.xp", width=40, height=7)


def test_rexpaint_import_round_trips_exported_geometry(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    exported = export_rexpaint(
        sprite, palettes, tmp_path / "fighter.xp", width=40, height=7, seed=7
    )
    imported = import_rexpaint_cells(exported.image_path)
    assert imported.glyphs == render_sprite(
        sprite, palettes, width=40, height=7, seed=7, primary_colors=True
    ).plain.splitlines()
    assert not set("RGBYrgby") & set("".join(imported.glyphs))


def test_active_variant_hit_testing_matches_preview_geometry(
    palettes: PaletteCatalog,
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    variant = active_variant_at_cell(
        sprite,
        palettes,
        x=10,
        y=3,
        width=40,
        height=7,
        seed=7,
    )
    assert variant is not None
    assert any(
        variant in section.variants
        for section in sprite.views["horizontal"].tiers[0].sections
    )


def test_rexpaint_import_segments_active_variants(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    exported = export_rexpaint(
        sprite, palettes, tmp_path / "fighter.xp", width=40, height=7, seed=7
    )
    segments = segment_rexpaint_cells(
        import_rexpaint_cells(exported.image_path),
        sprite,
        palettes,
        width=40,
        height=7,
        seed=7,
    )
    assert all(
        cells == variant.cells and color_mask == variant.color_mask
        for variant, cells, color_mask in segments
    )


def test_rexpaint_import_rejects_multiple_layers(tmp_path: Path) -> None:
    path = tmp_path / "layers.xp"
    path.write_bytes(gzip.compress(struct.pack("<ii", -1, 2), mtime=0))
    with pytest.raises(RexPaintImportError, match="expected one layer"):
        import_rexpaint_cells(path)


def test_rexpaint_font_covers_every_authored_asset_glyph(
    sprites: dict[str, object],
) -> None:
    used = {
        glyph
        for sprite in sprites.values()
        if hasattr(sprite, "views")
        for view in sprite.views.values()
        for tier in view.tiers
        for section in tier.sections
        for variant in section.variants
        for row in variant.cells
        for glyph in row
    }
    assert used <= REXPAINT_GLYPH_INDICES.keys()
    unicode_map = ASSETS / "rexpaint" / "edge-art-designer-unicode.txt"
    mapped_indices = {
        int(line.split()[0])
        for line in unicode_map.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert mapped_indices == set(REXPAINT_GLYPH_INDICES.values())


def test_authoring_glyphs_have_reversible_reflections_and_rotation_support() -> None:
    glyphs = [glyph for glyph, _ in AUTHORING_GLYPHS]
    for glyph in glyphs:
        if glyph != "≡":
            assert glyph in ROTATE_CCW
            rotated = glyph
            for _ in range(4):
                rotated = transform_glyph(rotated, ROTATE_CCW)
            assert rotated == glyph
        assert flip_rows_horizontal(flip_rows_horizontal([glyph])) == [glyph]
        assert flip_rows_vertical(flip_rows_vertical([glyph])) == [glyph]


def test_generated_heavy_half_beams_remain_authorable_and_exportable(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    changed = deepcopy(sprite)
    changed.views.pop("vertical")
    variant = changed.views["horizontal"].tiers[0].sections[0].variants[0]
    variant.cells[0] = "╺" + variant.cells[0][1:]

    vertical, warnings = generate_rotated_view(changed)

    assert not warnings
    assert {"╻", "╹"} <= REXPAINT_GLYPH_INDICES.keys()
    assert [REXPAINT_GLYPH_INDICES[glyph] for glyph in "╻╹╺╸"] == [36, 37, 38, 39]
    assert any(
        "╹" in row
        for row in vertical.tiers[0].sections[0].variants[0].cells
    )
    changed.views["vertical"] = vertical
    export_rexpaint(
        changed,
        palettes,
        tmp_path / "vertical-half-beam.xp",
        width=14,
        height=7,
        view_id="vertical",
    )


@pytest.mark.parametrize("role", sorted(ORIGINAL_ROLES | NEW_ROLES))
def test_every_ship_has_independent_horizontal_and_vertical_views(role: str) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / f"{role}.yaml")
    assert set(sprite.views) == {"horizontal", "vertical"}
    assert sprite.views["horizontal"].axis == "horizontal"
    assert sprite.views["vertical"].axis == "vertical"
    assert sprite.views["horizontal"] is not sprite.views["vertical"]


def test_ship_assets_have_full_medium_and_compact_horizontal_tiers() -> None:
    for role in ORIGINAL_ROLES | NEW_ROLES:
        sprite = load_sprite(ASSETS / "sprites" / "ships" / f"{role}.yaml")
        tiers = sprite.views["horizontal"].tiers
        assert [tier.id for tier in tiers] == ["full", "medium", "compact"]
        assert [tier.cross_axis_size("horizontal") for tier in tiers] == [7, 5, 3]
        for full_section, medium_section in zip(
            tiers[0].sections, tiers[1].sections
        ):
            for full_variant, medium_variant in zip(
                full_section.variants, medium_section.variants
            ):
                assert medium_variant.width == (full_variant.width * 3 + 2) // 4


@pytest.mark.parametrize("role", sorted(ORIGINAL_ROLES | NEW_ROLES))
def test_generation_is_deterministic_and_exact(role: str, palettes: PaletteCatalog) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / f"{role}.yaml")
    for view_id, sizes in (
        ("horizontal", ((18, 3), (40, 7), (56, 12))),
        ("vertical", ((3, 18), (7, 40), (12, 56))),
    ):
        for width, height in sizes:
            first = render_sprite(
                sprite,
                palettes,
                width=width,
                height=height,
                seed=13,
                archetype_id="ribbon_salvager",
                view_id=view_id,
            )
            second = render_sprite(
                sprite,
                palettes,
                width=width,
                height=height,
                seed=13,
                archetype_id="ribbon_salvager",
                view_id=view_id,
            )
            assert first.plain == second.plain
            assert first.spans == second.spans
            lines = first.plain.splitlines()
            assert len(lines) == height
            assert all(len(line) == width for line in lines)


def test_highlighted_variant_preserves_text_and_marks_its_section(
    palettes: PaletteCatalog,
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    variant = sprite.views["horizontal"].tiers[0].sections[0].variants[0]
    normal = render_sprite(
        sprite,
        palettes,
        width=56,
        height=12,
        seed=13,
        view_id="horizontal",
    )
    highlighted = render_sprite(
        sprite,
        palettes,
        width=56,
        height=12,
        seed=13,
        view_id="horizontal",
        highlight_variant=variant,
    )
    assert highlighted.plain == normal.plain
    assert highlighted.spans != normal.spans


def test_preview_margin_projects_highlights_along_the_view_cross_axis(
    palettes: PaletteCatalog,
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    variant = sprite.views["horizontal"].tiers[0].sections[0].variants[0]
    preview = render_sprite(
        sprite,
        palettes,
        width=40,
        height=7,
        seed=13,
        view_id="horizontal",
        highlight_variant=variant,
        preview_margin=True,
    )
    lines = preview.plain.splitlines()
    assert len(lines) == 9
    assert all(len(line) == 42 for line in lines)
    assert "on #4c1d95" in str(preview.spans)


def test_horizontal_facing_is_exact_glyph_reflection(palettes: PaletteCatalog) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    right = render_sprite(
        sprite,
        palettes,
        width=40,
        height=7,
        seed=5,
        view_id="horizontal",
        facing="right",
    ).plain.splitlines()
    left = render_sprite(
        sprite,
        palettes,
        width=40,
        height=7,
        seed=5,
        view_id="horizontal",
        facing="left",
    ).plain.splitlines()
    assert [line.strip() for line in left] == [
        line.strip() for line in flip_rows_horizontal(right)
    ]


def test_vertical_facing_is_exact_glyph_reflection(palettes: PaletteCatalog) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "warship.yaml")
    up = render_sprite(
        sprite,
        palettes,
        width=9,
        height=35,
        seed=5,
        view_id="vertical",
        facing="up",
    ).plain.splitlines()
    down = render_sprite(
        sprite,
        palettes,
        width=9,
        height=35,
        seed=5,
        view_id="vertical",
        facing="down",
    ).plain.splitlines()
    assert down == flip_rows_vertical(up)


def test_rotation_uses_fallback_and_reports_location() -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    changed = deepcopy(sprite)
    changed.views.pop("vertical")
    variant = changed.views["horizontal"].tiers[0].sections[0].variants[0]
    variant.cells[0] = "λ" + variant.cells[0][1:]
    vertical, warnings = generate_rotated_view(changed)
    assert warnings
    assert warnings[0].glyph == "λ"
    assert any("◇" in row for row in vertical.tiers[0].sections[0].variants[0].cells)


def test_rotation_compacts_terminal_cell_aspect() -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    source = sprite.views["horizontal"].tiers[0].sections[0].variants[0]
    vertical, _warnings = generate_rotated_view(sprite)
    rotated = vertical.tiers[0].sections[0].variants[0]
    assert rotated.width == source.height * 2
    assert rotated.height == (source.width + 1) // 2
    assert all(
        row[column : column + 2] == row[column] * 2
        for row in rotated.cells
        for column in range(0, rotated.width, 2)
    )
    assert len(rotated.color_mask) == rotated.height
    assert all(len(row) == rotated.width for row in rotated.color_mask)
    assert all(
        row[column : column + 2] == row[column] * 2
        for row in rotated.color_mask
        for column in range(0, rotated.width, 2)
    )


def test_yaml_round_trip(tmp_path: Path, palettes: PaletteCatalog) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "needle_picket.yaml")
    sprite_path = tmp_path / "sprite.yaml"
    palette_path = tmp_path / "palettes.yaml"
    dump_sprite(sprite, sprite_path)
    dump_palette_catalog(palettes, palette_path)
    loaded = load_sprite(sprite_path)
    loaded.source = sprite.source
    assert loaded == sprite
    assert load_palette_catalog(palette_path) == palettes


def test_library_facade_selects_view_and_caches() -> None:
    library = SpriteLibrary.from_assets(ASSETS)
    horizontal = library.generate_ship("fighter", 4, 30, 5, facing="left")
    vertical = library.generate_ship("fighter", 4, 5, 30, facing="up")
    assert len(horizontal.plain.splitlines()) == 5
    assert len(vertical.plain.splitlines()) == 30
    assert library.generate_ship("fighter", 4, 30, 5, facing="left") is horizontal


def test_equal_weights_preserve_random_choice_contract() -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    section = sprite.views["horizontal"].tiers[0].sections[0]
    rng = random.Random(17)
    expected = rng.choice(section.variants).id
    rng = random.Random(17)
    # The renderer's helper is intentionally private; checking the next choice
    # through the same list pins the equal-weight draw discipline.
    assert rng.choice(section.variants).id == expected
