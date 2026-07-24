"""Versioned in-memory model for generic and compositional sprite art."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from rich.cells import get_character_cell_size

SCHEMA_VERSION = 1

Axis = Literal["horizontal", "vertical", "fixed"]

PROPERTY_IDS: tuple[str, ...] = (
    "thrusters",
    "spindrive",
    "hull",
    "armor",
    "screens",
    "main_gun",
    "weapons",
    "cargo",
    "sensors",
    "bridge",
    "habitat",
    "radiator",
    "hangar",
    "reactor",
    "utility",
)

ARCHETYPE_IDS: tuple[str, ...] = (
    "humanoid_diplomat",
    "canid_technologist",
    "tentacled_envoy",
    "brain_dome_automaton",
    "ribbon_salvager",
    "temporal_broker",
    "cosmic_arbiter",
    "telepath_aristocrat",
    "engineered_aesthete",
    "amorous_imp",
    "horned_grudgekeeper",
    "psionic_overlord",
    "colonial_broodmaster",
    "winged_schemer",
)


class SpriteValidationError(ValueError):
    """A sprite or palette document violates the authoring contract."""


@dataclass
class Variant:
    id: str
    cells: list[str]
    weight: int = 1

    @property
    def width(self) -> int:
        return max((len(row) for row in self.cells), default=0)

    @property
    def height(self) -> int:
        return len(self.cells)

    def validate(self, context: str) -> None:
        if not self.id:
            raise SpriteValidationError(f"{context}: variant id cannot be empty")
        if self.weight < 1:
            raise SpriteValidationError(f"{context}/{self.id}: weight must be at least 1")
        if not self.cells:
            raise SpriteValidationError(f"{context}/{self.id}: cells cannot be empty")
        widths = {len(row) for row in self.cells}
        if len(widths) != 1:
            raise SpriteValidationError(
                f"{context}/{self.id}: every row must have the same character count"
            )
        for row_index, row in enumerate(self.cells):
            for column, glyph in enumerate(row):
                if get_character_cell_size(glyph) != 1:
                    raise SpriteValidationError(
                        f"{context}/{self.id}: glyph {glyph!r} at "
                        f"{column},{row_index} is not one terminal cell wide"
                    )


@dataclass
class Section:
    id: str
    name: str
    primary_property: str
    secondary_properties: list[str] = field(default_factory=list)
    min_repeat: int = 1
    max_repeat: int = 1
    variants: list[Variant] = field(default_factory=list)

    @property
    def repeatable(self) -> bool:
        return self.max_repeat > 1

    def validate(self, context: str) -> None:
        section_context = f"{context}/{self.id}"
        if not self.id:
            raise SpriteValidationError(f"{context}: section id cannot be empty")
        if self.primary_property not in PROPERTY_IDS:
            raise SpriteValidationError(
                f"{section_context}: unknown primary property {self.primary_property!r}"
            )
        invalid_secondary = set(self.secondary_properties) - set(PROPERTY_IDS)
        if invalid_secondary:
            raise SpriteValidationError(
                f"{section_context}: unknown secondary properties "
                f"{sorted(invalid_secondary)!r}"
            )
        if self.primary_property in self.secondary_properties:
            raise SpriteValidationError(
                f"{section_context}: primary property cannot also be secondary"
            )
        if len(set(self.secondary_properties)) != len(self.secondary_properties):
            raise SpriteValidationError(
                f"{section_context}: secondary properties must be unique"
            )
        if self.min_repeat < 1 or self.max_repeat < self.min_repeat:
            raise SpriteValidationError(
                f"{section_context}: repeat range must satisfy 1 <= min <= max"
            )
        if not self.variants:
            raise SpriteValidationError(f"{section_context}: requires at least one variant")
        seen: set[str] = set()
        dimensions: set[tuple[int, int]] = set()
        for variant in self.variants:
            if variant.id in seen:
                raise SpriteValidationError(
                    f"{section_context}: duplicate variant id {variant.id!r}"
                )
            seen.add(variant.id)
            variant.validate(section_context)
            dimensions.add((variant.width, variant.height))
        if len(dimensions) != 1:
            raise SpriteValidationError(
                f"{section_context}: variants must share one rectangular size"
            )


@dataclass
class Tier:
    id: str
    name: str
    sections: list[Section] = field(default_factory=list)

    def cross_axis_size(self, axis: Axis) -> int:
        if not self.sections:
            return 0
        if axis == "horizontal":
            return max(variant.height for section in self.sections for variant in section.variants)
        if axis == "vertical":
            return max(variant.width for section in self.sections for variant in section.variants)
        first = self.sections[0].variants[0]
        return max(first.width, first.height)

    def validate(self, context: str, axis: Axis) -> None:
        tier_context = f"{context}/{self.id}"
        if not self.id:
            raise SpriteValidationError(f"{context}: tier id cannot be empty")
        if not self.sections:
            raise SpriteValidationError(f"{tier_context}: requires at least one section")
        if axis == "fixed" and len(self.sections) != 1:
            raise SpriteValidationError(
                f"{tier_context}: fixed views require exactly one section"
            )
        seen: set[str] = set()
        cross_sizes: set[int] = set()
        for section in self.sections:
            if section.id in seen:
                raise SpriteValidationError(
                    f"{tier_context}: duplicate section id {section.id!r}"
                )
            seen.add(section.id)
            section.validate(tier_context)
            for variant in section.variants:
                cross_sizes.add(
                    variant.height if axis == "horizontal" else variant.width
                )
        if axis != "fixed" and len(cross_sizes) != 1:
            raise SpriteValidationError(
                f"{tier_context}: every part must share the same cross-axis size"
            )


@dataclass
class View:
    id: str
    name: str
    axis: Axis
    canonical_facing: str
    mirror_facing: str | None
    tiers: list[Tier] = field(default_factory=list)

    def validate(self, context: str) -> None:
        view_context = f"{context}/{self.id}"
        if not self.id:
            raise SpriteValidationError(f"{context}: view id cannot be empty")
        if self.axis not in ("horizontal", "vertical", "fixed"):
            raise SpriteValidationError(f"{view_context}: unsupported axis {self.axis!r}")
        if not self.canonical_facing:
            raise SpriteValidationError(
                f"{view_context}: canonical_facing cannot be empty"
            )
        if self.axis == "fixed" and self.mirror_facing is not None:
            raise SpriteValidationError(
                f"{view_context}: fixed views cannot declare a mirror facing"
            )
        if not self.tiers:
            raise SpriteValidationError(f"{view_context}: requires at least one tier")
        seen: set[str] = set()
        sizes: list[int] = []
        for tier in self.tiers:
            if tier.id in seen:
                raise SpriteValidationError(
                    f"{view_context}: duplicate tier id {tier.id!r}"
                )
            seen.add(tier.id)
            tier.validate(view_context, self.axis)
            sizes.append(tier.cross_axis_size(self.axis))
        if sizes != sorted(sizes, reverse=True):
            raise SpriteValidationError(
                f"{view_context}: tiers must be ordered richest/largest first"
            )


@dataclass
class Sprite:
    schema_version: int
    id: str
    name: str
    kind: str
    role: str
    description: str
    views: dict[str, View] = field(default_factory=dict)
    source: str | None = None

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise SpriteValidationError(
                f"{self.id or 'sprite'}: unsupported schema_version "
                f"{self.schema_version}; expected {SCHEMA_VERSION}"
            )
        if not self.id or not self.role:
            raise SpriteValidationError("sprite id and role cannot be empty")
        if not self.views:
            raise SpriteValidationError(f"{self.id}: requires at least one view")
        for key, view in self.views.items():
            if key != view.id:
                raise SpriteValidationError(
                    f"{self.id}: view key {key!r} does not match id {view.id!r}"
                )
            view.validate(self.id)


@dataclass
class Palette:
    bright: str
    mid: str
    dark: str
    beacon: list[str]
    engine: list[str]
    window: list[str]
    facet: str

    def validate(self, context: str) -> None:
        scalar_colors = {
            "bright": self.bright,
            "mid": self.mid,
            "dark": self.dark,
            "facet": self.facet,
        }
        for field_name, value in scalar_colors.items():
            if not value:
                raise SpriteValidationError(f"{context}.{field_name} cannot be empty")
        for field_name, values in (
            ("beacon", self.beacon),
            ("engine", self.engine),
            ("window", self.window),
        ):
            if not values or any(not value for value in values):
                raise SpriteValidationError(
                    f"{context}.{field_name} requires one or more colors"
                )


@dataclass
class PaletteCatalog:
    schema_version: int
    archetypes: dict[str, Palette]
    fallback_archetype: str = "humanoid_diplomat"

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise SpriteValidationError(
                "palette catalog has unsupported schema_version "
                f"{self.schema_version}; expected {SCHEMA_VERSION}"
            )
        actual = set(self.archetypes)
        expected = set(ARCHETYPE_IDS)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise SpriteValidationError(
                f"palette archetypes are controlled; missing={missing}, extra={extra}"
            )
        if self.fallback_archetype != "humanoid_diplomat":
            raise SpriteValidationError(
                "fallback_archetype must remain 'humanoid_diplomat'"
            )
        for archetype_id, palette in self.archetypes.items():
            palette.validate(archetype_id)

    def resolve(self, archetype_id: str | None) -> Palette:
        return self.archetypes.get(
            (archetype_id or "").lower(),
            self.archetypes[self.fallback_archetype],
        )
