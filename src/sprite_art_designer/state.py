"""Editor document state, explicit saves, and crash-recovery snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sprite_art import (
    PaletteCatalog,
    Sprite,
    dump_palette_catalog,
    dump_sprite,
    load_palette_catalog,
    load_sprite,
    load_sprite_directory,
)

KIND_FOLDERS = {
    "ship": "ships",
    "port": "ports",
}
"""Where each sprite kind is saved under ``assets/sprites``.

Sprite ids are unique across the whole tree, so the folder is presentation
only; an unlisted kind falls back to ``generic``."""


@dataclass
class EditorState:
    asset_root: Path
    data_root: Path
    palettes: PaletteCatalog
    sprites: dict[str, Sprite]
    sprite_paths: dict[str, Path]
    current_sprite_id: str
    dirty_sprites: set[str] = field(default_factory=set)
    palettes_dirty: bool = False

    @classmethod
    def load(cls, asset_root: Path, data_root: Path | None = None) -> EditorState:
        root = asset_root.resolve()
        sprites = load_sprite_directory(root / "sprites")
        if not sprites:
            raise ValueError(f"no sprite YAML files found below {root / 'sprites'}")
        paths = {
            sprite.id: Path(sprite.source).resolve()
            for sprite in sprites.values()
            if sprite.source is not None
        }
        return cls(
            asset_root=root,
            data_root=(data_root or Path.home() / ".edge-art-designer").resolve(),
            palettes=load_palette_catalog(root / "palettes.yaml"),
            sprites=sprites,
            sprite_paths=paths,
            current_sprite_id=sorted(sprites)[0],
        )

    @property
    def current_sprite(self) -> Sprite:
        return self.sprites[self.current_sprite_id]

    @property
    def recovery_root(self) -> Path:
        return self.data_root / "recovery"

    @property
    def export_root(self) -> Path:
        return self.data_root / "exports"

    def mark_sprite_dirty(self, sprite_id: str | None = None) -> None:
        self.dirty_sprites.add(sprite_id or self.current_sprite_id)

    def mark_palettes_dirty(self) -> None:
        self.palettes_dirty = True

    def sprite_path(self, sprite_id: str) -> Path:
        if sprite_id in self.sprite_paths:
            return self.sprite_paths[sprite_id]
        sprite = self.sprites[sprite_id]
        kind_folder = KIND_FOLDERS.get(sprite.kind, "generic")
        return self.asset_root / "sprites" / kind_folder / f"{sprite.id}.yaml"

    def save_current(self) -> None:
        sprite = self.current_sprite
        target = self.sprite_path(sprite.id)
        dump_sprite(sprite, target)
        sprite.source = str(target)
        self.sprite_paths[sprite.id] = target
        self.dirty_sprites.discard(sprite.id)
        if self.palettes_dirty:
            dump_palette_catalog(self.palettes, self.asset_root / "palettes.yaml")
            self.palettes_dirty = False
        recovery = self.recovery_path(sprite.id)
        recovery.unlink(missing_ok=True)

    def save_all(self) -> None:
        for sprite_id in sorted(self.dirty_sprites):
            sprite = self.sprites[sprite_id]
            target = self.sprite_path(sprite.id)
            dump_sprite(sprite, target)
            sprite.source = str(target)
            self.sprite_paths[sprite.id] = target
            self.recovery_path(sprite.id).unlink(missing_ok=True)
        self.dirty_sprites.clear()
        if self.palettes_dirty:
            dump_palette_catalog(self.palettes, self.asset_root / "palettes.yaml")
            self.palettes_dirty = False

    def add_sprite(self, sprite: Sprite) -> None:
        if sprite.id in self.sprites:
            raise ValueError(f"sprite id {sprite.id!r} already exists")
        self.sprites[sprite.id] = sprite
        self.current_sprite_id = sprite.id
        self.mark_sprite_dirty(sprite.id)

    def recovery_path(self, sprite_id: str) -> Path:
        return self.recovery_root / f"{sprite_id}.yaml"

    def write_recovery(self, sprite_id: str | None = None) -> Path:
        selected = sprite_id or self.current_sprite_id
        self.recovery_root.mkdir(parents=True, exist_ok=True)
        target = self.recovery_path(selected)
        dump_sprite(self.sprites[selected], target)
        return target

    def has_newer_recovery(self, sprite_id: str | None = None) -> bool:
        selected = sprite_id or self.current_sprite_id
        recovery = self.recovery_path(selected)
        if not recovery.exists():
            return False
        source = self.sprite_paths.get(selected)
        return source is None or not source.exists() or recovery.stat().st_mtime > source.stat().st_mtime

    def restore_recovery(self, sprite_id: str | None = None) -> Sprite:
        selected = sprite_id or self.current_sprite_id
        recovered = load_sprite(self.recovery_path(selected))
        recovered.source = str(self.sprite_paths.get(selected, self.sprite_path(selected)))
        self.sprites[selected] = recovered
        self.mark_sprite_dirty(selected)
        return recovered
