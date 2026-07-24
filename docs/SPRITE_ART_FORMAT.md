# Sprite Art Format

The format is versioned YAML. Palettes are centralized and controlled; each
sprite is an independent file that can be reviewed, copied, or evolved without
rewriting an asset monolith.

## Asset tree

```text
assets/
├── palettes.yaml
└── sprites/
    ├── ships/
    │   └── fighter.yaml
    └── generic/
        └── future_icon.yaml
```

Every document currently uses `schema_version: 1`. Sprite and palette versions
are deliberately independent migration seams even though they begin at the same
number.

## Sprite document

```yaml
schema_version: 1
id: fighter
name: Fighter
kind: ship
role: fighter
description: A compact combat craft.
views:
  horizontal:
    name: Horizontal
    axis: horizontal
    canonical_facing: right
    mirror_facing: left
    tiers:
      - id: full
        name: Full Detail
        sections:
          - id: hull
            name: Hull
            primary_property: hull
            secondary_properties: [armor]
            repeat: {min: 1, max: 6}
            variants:
              - id: hull_1
                weight: 1
                cells:
                  - "    "
                  - "████"
                  - "████"
                  - "    "
```

View names are data, not schema keywords. Ships currently store `horizontal`
and `vertical`; future sprite kinds may define names such as `docked`, `damaged`,
or `icon`.

### Composition axes

- `horizontal`: sections are authored tail-to-nose and joined left-to-right.
- `vertical`: sections remain tail-to-nose in the file but are stacked
  bottom-to-top, producing canonical nose-up art.
- `fixed`: one section and one or more weighted full-canvas variants.

Horizontal and vertical views are separate stored art. The editor's rotation
command only creates an editable starting point; rendering never rotates one
view to obtain another.

### Tiers

Tiers are ordered richest/largest first. A horizontal view selects by available
height; a vertical view selects by available width. A fixed view selects the
first canvas that fits both dimensions. If none fit, the smallest tier is used
and centered cropping provides the requested exact rectangle.

### Sections and variants

A section has one controlled `primary_property` and zero or more controlled
`secondary_properties`. These are metadata in schema v1; they do not alter
runtime composition.

The closed vocabulary is:

```text
thrusters, spindrive, hull, armor, screens, main_gun, weapons,
cargo, sensors, bridge, habitat, radiator, hangar, reactor, utility
```

Each section's variants must have identical rectangular dimensions. `weight`
is a positive integer. Equal weights use the same `random.Random.choice`
behavior as Edge's original grammar; unequal weights use weighted selection.

Repeats start at `min`, grow round-robin without exceeding the requested size,
and stop at `max`. Variant selection always consumes one random decision per
section regardless of repeat count.

### Glyph semantics

- `█`: bright plating.
- `▒` and `░`: dark recesses.
- structural half-block, line, corner, wedge, and bevel glyphs: mid-tone hull.
- `R`: palette-colored beacon marker, painted as `▀`.
- `Y`: palette-colored engine marker, painted as `▄`.
- space: transparent-looking terminal void.
- other one-cell glyphs: facets painted over bright plating.

All glyphs must occupy exactly one terminal cell.

## Palette catalog

`palettes.yaml` must contain exactly the 14 controlled Edge archetypes. IDs may
not be added, removed, renamed, or duplicated in the editor. Their color values
and color pools are editable.

```yaml
schema_version: 1
fallback_archetype: humanoid_diplomat
archetypes:
  humanoid_diplomat:
    bright: grey85
    mid: grey58
    dark: grey35
    beacon: [red, bright_red]
    engine: [yellow, bright_yellow]
    window: [bright_cyan, bright_yellow, grey100]
    facet: grey15
```

Unknown archetypes resolve to `humanoid_diplomat`.

## Rotation and reflection

“Generate vertical” rotates every horizontal tier, section variant, and cell 90°
counter-clockwise. Known structural glyphs are rotated through an explicit
mapping. An unmapped glyph becomes `◇`, and the editor reports the number of
fallback cells. The generated view is then ordinary editable YAML.

Left/right reflection reverses each row and swaps horizontal glyph twins.
Up/down reflection reverses row order and swaps vertical twins. Both transforms
are deterministic post-composition operations and consume no random values.

