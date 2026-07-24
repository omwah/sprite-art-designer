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
from .render import RenderRequest, compose_grid, render_sprite
from .transform import RotationWarning, generate_rotated_view

__all__ = [
    "ARCHETYPE_IDS",
    "PROPERTY_IDS",
    "Palette",
    "PaletteCatalog",
    "RenderRequest",
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
    "generate_rotated_view",
    "load_palette_catalog",
    "load_sprite",
    "load_sprite_directory",
    "render_sprite",
]
