from __future__ import annotations

import gzip
import struct
from copy import deepcopy
from pathlib import Path

import pytest

from sprite_art import PaletteCatalog, load_sprite, render_sprite
from sprite_art_authoring import (
    REXPAINT_GLYPH_INDICES,
    RexPaintGlyphError,
    RexPaintImportError,
    export_rexpaint,
    generate_rotated_view,
    import_rexpaint_cells,
    segment_rexpaint_cells,
)

ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"

def test_rexpaint_export_is_deterministic_and_uses_one_column_major_layer(
    palettes: PaletteCatalog, tmp_path: Path
) -> None:
    sprite = load_sprite(ASSETS / "sprites" / "ships" / "fighter.yaml")
    first = export_rexpaint(sprite, palettes, tmp_path / "fighter.xp", width=40, height=7, seed=7)
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

def test_rexpaint_export_rejects_unmapped_glyph(palettes: PaletteCatalog, tmp_path: Path) -> None:
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
    assert (
        imported.glyphs
        == render_sprite(
            sprite, palettes, width=40, height=7, seed=7, primary_colors=True
        ).plain.splitlines()
    )
    assert not set("RGBYrgby") & set("".join(imported.glyphs))

def test_rexpaint_import_segments_active_variants(palettes: PaletteCatalog, tmp_path: Path) -> None:
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
    assert any("╹" in row for row in vertical.tiers[0].sections[0].variants[0].cells)
    changed.views["vertical"] = vertical
    export_rexpaint(
        changed,
        palettes,
        tmp_path / "vertical-half-beam.xp",
        width=14,
        height=7,
        view_id="vertical",
    )

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
