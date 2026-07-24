"""Convenient loaded-library facade for game integration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from rich.text import Text

from .io import load_palette_catalog, load_sprite_directory
from .model import PaletteCatalog, Sprite
from .render import render_sprite


class SpriteLibrary:
    """Load an asset tree once and render cached sprites by gameplay role."""

    def __init__(
        self,
        sprites: dict[str, Sprite],
        palettes: PaletteCatalog,
        *,
        fallback_role: str = "fighter",
    ) -> None:
        if fallback_role not in sprites:
            raise ValueError(f"fallback role {fallback_role!r} is not loaded")
        self.sprites = sprites
        self.palettes = palettes
        self.fallback_role = fallback_role

    @classmethod
    def from_assets(cls, asset_root: str | Path) -> SpriteLibrary:
        root = Path(asset_root)
        return cls(
            load_sprite_directory(root / "sprites"),
            load_palette_catalog(root / "palettes.yaml"),
        )

    @property
    def available_roles(self) -> tuple[str, ...]:
        return tuple(sorted(self.sprites))

    @lru_cache(maxsize=128)
    def generate_ship(
        self,
        subtype: str,
        seed: int,
        width: int,
        height: int,
        archetype_id: str | None = None,
        facing: str = "right",
    ) -> Text:
        """Edge-compatible ship renderer, extended to left/right/up/down."""

        sprite = self.sprites.get(subtype.lower(), self.sprites[self.fallback_role])
        normalized_facing = facing.lower()
        view_id = (
            "vertical"
            if normalized_facing in {"up", "down"} and "vertical" in sprite.views
            else "horizontal"
            if "horizontal" in sprite.views
            else next(iter(sprite.views))
        )
        view = sprite.views[view_id]
        if normalized_facing not in {
            view.canonical_facing,
            view.mirror_facing,
        }:
            normalized_facing = view.canonical_facing
        return render_sprite(
            sprite,
            self.palettes,
            width=width,
            height=height,
            seed=seed,
            archetype_id=archetype_id or self.palettes.fallback_archetype,
            view_id=view_id,
            facing=normalized_facing,
        )

    def clear_cache(self) -> None:
        self.generate_ship.cache_clear()

