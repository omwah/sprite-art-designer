"""Reusable procedural Unicode sprite-art reader and renderer."""

from .io import (
    dump_palette_catalog,
    dump_sprite,
    load_palette_catalog,
    load_sprite,
    load_sprite_directory,
)
from .library import SpriteLibrary
from .model import (
    ARCHETYPE_IDS,
    PROPERTY_IDS,
    Palette,
    PaletteCatalog,
    Section,
    Sprite,
    SpriteValidationError,
    Tier,
    Variant,
    View,
)
from .render import (
    RenderRequest,
    active_variant_at_cell,
    compose_grid,
    render_sprite,
    selected_tier,
    selected_variants,
)
from .rexpaint import (
    REXPAINT_FONT_COLUMNS,
    REXPAINT_GLYPH_INDICES,
    RexPaintGlyphError,
    RexPaintImportError,
    export_rexpaint,
    import_rexpaint_cells,
    rexpaint_bytes,
    segment_rexpaint_cells,
)
from .transform import RotationWarning, generate_rotated_view

__all__ = [
    "ARCHETYPE_IDS",
    "active_variant_at_cell",
    "PROPERTY_IDS",
    "Palette",
    "PaletteCatalog",
    "RenderRequest",
    "REXPAINT_FONT_COLUMNS",
    "REXPAINT_GLYPH_INDICES",
    "RexPaintGlyphError",
    "RexPaintImportError",
    "RotationWarning",
    "Section",
    "Sprite",
    "SpriteLibrary",
    "SpriteValidationError",
    "Tier",
    "Variant",
    "View",
    "compose_grid",
    "dump_palette_catalog",
    "dump_sprite",
    "export_rexpaint",
    "generate_rotated_view",
    "import_rexpaint_cells",
    "load_palette_catalog",
    "load_sprite",
    "load_sprite_directory",
    "render_sprite",
    "rexpaint_bytes",
    "selected_tier",
    "selected_variants",
    "segment_rexpaint_cells",
]
