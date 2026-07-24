"""YAML I/O for the sprite-art schema."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .model import (
    Palette,
    PaletteCatalog,
    Section,
    Sprite,
    SpriteValidationError,
    Tier,
    Variant,
    View,
)


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SpriteValidationError(f"{context} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _string_list(value: object, context: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SpriteValidationError(f"{context} must be a list of strings")
    return list(value)


def _variant_from_data(data: object, context: str) -> Variant:
    item = _mapping(data, context)
    return Variant(
        id=str(item.get("id", "")),
        weight=int(item.get("weight", 1)),
        cells=_string_list(item.get("cells", []), f"{context}.cells"),
    )


def _section_from_data(data: object, context: str) -> Section:
    item = _mapping(data, context)
    variants_data = item.get("variants", [])
    if not isinstance(variants_data, list):
        raise SpriteValidationError(f"{context}.variants must be a list")
    repeat = _mapping(item.get("repeat", {}), f"{context}.repeat")
    return Section(
        id=str(item.get("id", "")),
        name=str(item.get("name", item.get("id", ""))),
        primary_property=str(item.get("primary_property", "utility")),
        secondary_properties=_string_list(
            item.get("secondary_properties", []),
            f"{context}.secondary_properties",
        ),
        min_repeat=int(repeat.get("min", 1)),
        max_repeat=int(repeat.get("max", 1)),
        variants=[
            _variant_from_data(variant, f"{context}.variants[{index}]")
            for index, variant in enumerate(variants_data)
        ],
    )


def _tier_from_data(data: object, context: str) -> Tier:
    item = _mapping(data, context)
    sections_data = item.get("sections", [])
    if not isinstance(sections_data, list):
        raise SpriteValidationError(f"{context}.sections must be a list")
    return Tier(
        id=str(item.get("id", "")),
        name=str(item.get("name", item.get("id", ""))),
        sections=[
            _section_from_data(section, f"{context}.sections[{index}]")
            for index, section in enumerate(sections_data)
        ],
    )


def _view_from_data(view_id: str, data: object, context: str) -> View:
    item = _mapping(data, context)
    tiers_data = item.get("tiers", [])
    if not isinstance(tiers_data, list):
        raise SpriteValidationError(f"{context}.tiers must be a list")
    mirror = item.get("mirror_facing")
    return View(
        id=view_id,
        name=str(item.get("name", view_id.replace("_", " ").title())),
        axis=str(item.get("axis", "fixed")),  # type: ignore[arg-type]
        canonical_facing=str(item.get("canonical_facing", "default")),
        mirror_facing=None if mirror is None else str(mirror),
        tiers=[
            _tier_from_data(tier, f"{context}.tiers[{index}]")
            for index, tier in enumerate(tiers_data)
        ],
    )


def load_sprite(path: str | Path) -> Sprite:
    source_path = Path(path)
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    data = _mapping(raw, str(source_path))
    views_data = _mapping(data.get("views", {}), f"{source_path}.views")
    sprite = Sprite(
        schema_version=int(data.get("schema_version", 0)),
        id=str(data.get("id", "")),
        name=str(data.get("name", data.get("id", ""))),
        kind=str(data.get("kind", "generic")),
        role=str(data.get("role", data.get("id", ""))),
        description=str(data.get("description", "")),
        source=str(source_path),
        views={
            view_id: _view_from_data(
                view_id,
                view_data,
                f"{source_path}.views.{view_id}",
            )
            for view_id, view_data in views_data.items()
        },
    )
    sprite.validate()
    return sprite


def load_sprite_directory(path: str | Path) -> dict[str, Sprite]:
    root = Path(path)
    sprites: dict[str, Sprite] = {}
    for source_path in sorted(root.rglob("*.yaml")):
        sprite = load_sprite(source_path)
        if sprite.id in sprites:
            raise SpriteValidationError(
                f"duplicate sprite id {sprite.id!r}: "
                f"{sprites[sprite.id].source} and {source_path}"
            )
        sprites[sprite.id] = sprite
    return sprites


def load_palette_catalog(path: str | Path) -> PaletteCatalog:
    source_path = Path(path)
    raw = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    data = _mapping(raw, str(source_path))
    archetypes_data = _mapping(
        data.get("archetypes", {}),
        f"{source_path}.archetypes",
    )
    catalog = PaletteCatalog(
        schema_version=int(data.get("schema_version", 0)),
        fallback_archetype=str(
            data.get("fallback_archetype", "humanoid_diplomat")
        ),
        archetypes={
            archetype_id: Palette(
                bright=str(_mapping(value, archetype_id).get("bright", "")),
                mid=str(_mapping(value, archetype_id).get("mid", "")),
                dark=str(_mapping(value, archetype_id).get("dark", "")),
                beacon=_string_list(
                    _mapping(value, archetype_id).get("beacon", []),
                    f"{archetype_id}.beacon",
                ),
                engine=_string_list(
                    _mapping(value, archetype_id).get("engine", []),
                    f"{archetype_id}.engine",
                ),
                window=_string_list(
                    _mapping(value, archetype_id).get("window", []),
                    f"{archetype_id}.window",
                ),
                facet=str(_mapping(value, archetype_id).get("facet", "")),
            )
            for archetype_id, value in archetypes_data.items()
        },
    )
    catalog.validate()
    return catalog


def _variant_to_data(variant: Variant) -> dict[str, object]:
    return {
        "id": variant.id,
        "weight": variant.weight,
        "cells": list(variant.cells),
    }


def _section_to_data(section: Section) -> dict[str, object]:
    return {
        "id": section.id,
        "name": section.name,
        "primary_property": section.primary_property,
        "secondary_properties": list(section.secondary_properties),
        "repeat": {"min": section.min_repeat, "max": section.max_repeat},
        "variants": [_variant_to_data(variant) for variant in section.variants],
    }


def _tier_to_data(tier: Tier) -> dict[str, object]:
    return {
        "id": tier.id,
        "name": tier.name,
        "sections": [_section_to_data(section) for section in tier.sections],
    }


def _view_to_data(view: View) -> dict[str, object]:
    return {
        "name": view.name,
        "axis": view.axis,
        "canonical_facing": view.canonical_facing,
        "mirror_facing": view.mirror_facing,
        "tiers": [_tier_to_data(tier) for tier in view.tiers],
    }


def sprite_to_data(sprite: Sprite) -> dict[str, object]:
    return {
        "schema_version": sprite.schema_version,
        "id": sprite.id,
        "name": sprite.name,
        "kind": sprite.kind,
        "role": sprite.role,
        "description": sprite.description,
        "views": {
            view_id: _view_to_data(view)
            for view_id, view in sprite.views.items()
        },
    }


def palette_catalog_to_data(catalog: PaletteCatalog) -> dict[str, object]:
    return {
        "schema_version": catalog.schema_version,
        "fallback_archetype": catalog.fallback_archetype,
        "archetypes": {
            archetype_id: {
                "bright": palette.bright,
                "mid": palette.mid,
                "dark": palette.dark,
                "beacon": list(palette.beacon),
                "engine": list(palette.engine),
                "window": list(palette.window),
                "facet": palette.facet,
            }
            for archetype_id, palette in catalog.archetypes.items()
        },
    }


def _atomic_yaml_write(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        ),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def dump_sprite(sprite: Sprite, path: str | Path) -> None:
    sprite.validate()
    _atomic_yaml_write(Path(path), sprite_to_data(sprite))


def dump_palette_catalog(catalog: PaletteCatalog, path: str | Path) -> None:
    catalog.validate()
    _atomic_yaml_write(Path(path), palette_catalog_to_data(catalog))

