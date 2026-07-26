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

- `█` and `■`: bright plating.
- `▒` and `░`: dark recesses.
- structural half-block, line, single/double/mixed box, corner, wedge, and bevel
  glyphs: mid-tone hull.
- `R` / `r`: palette-colored beacon markers, painted as `▀` / `▄`.
- `Y` / `y`: palette-colored engine markers, painted as `▀` / `▄`.
- `G` / `g`: always-green signal markers, painted as `▀` / `▄`.
- `B` / `b`: always-blue signal markers, painted as `▀` / `▄`.
- space: transparent-looking terminal void.
- other one-cell glyphs: facets painted over bright plating.

All glyphs must occupy exactly one terminal cell.

## REXPaint export

The reusable library can export a rendered request as a deterministic, one-layer
REXPaint `.xp` file. Export uses the same width, height, seed, palette,
view, facing, and variant overrides as the Rich preview. It preserves authored
semantic marker glyphs instead of substituting their preview-only
block-glyph effects, while retaining their palette colors.
The file is not an alternate editable source format: YAML remains authoritative.

An `.xp` file stores glyph *indices* rather than glyph shapes. The exporter uses
the stable index order in `sprite_art.rexpaint.REXPAINT_GLYPH_INDICES`; its
matching font sheet is `assets/rexpaint/edge-art-designer.png`. Install that
sheet as a 16-column REXPaint art font, retaining the supplied index order. An
authored glyph absent from the map rejects export with its cell position rather
than being silently substituted.

Import accepts only a one-layer `.xp` file using that same glyph map and is a
round-trip editing operation: it splits a just-exported image into the active
variants of the current preview's selected tier. The file dimensions, preview
size, seed, view, facing, and active variant selections must therefore still
match the export. Repeated copies must match one another; the importer cannot
infer separate source art from a repeated section. Unchanged semantic authoring
markers are recovered from their rendered block-glyph forms using
the current active source variant; edits to those cells become literal glyphs.

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
counter-clockwise. Because terminal cells are approximately twice as tall as
they are wide, the generated view doubles each rotated cell horizontally and
retains every other rotated row. This compact, deliberately lossy resampling
produces a proportionate editable starting view without making it excessively
wide. Known structural glyphs are rotated through an explicit mapping. An
unmapped glyph becomes `◇`, and the editor reports the number of fallback cells.
The generated view is then ordinary editable YAML.

Left/right reflection reverses each row and swaps horizontal glyph twins.
Up/down reflection reverses row order and swaps vertical twins. Both transforms
are deterministic post-composition operations and consume no random values.
