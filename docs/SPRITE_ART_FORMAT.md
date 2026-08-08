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
    └── ports/
        └── stardock.yaml
```

Sprite documents currently use `schema_version: 4`; the palette catalog remains
at `schema_version: 2`. Sprite and palette versions are independent migration
seams.

## Sprite document

```yaml
schema_version: 4
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
            repeat: 4
            variants:
              - id: hull_1
                weight: 1
                cells:
                  - "    "
                  - "████"
                  - "████"
                  - "    "
                color_mask:
                  - "SSSS"
                  - "SSSS"
                  - "SSSS"
                  - "SSSS"
```

View names are data, not schema keywords. Ships store `horizontal` and
`vertical`; stations store only `vertical` and declare no `mirror_facing`, so
they have a single orientation and no facing transform. Future sprite kinds may
define names such as `docked`, `damaged`, or `icon`.

### Composition axes

- `horizontal`: sections are authored tail-to-nose and joined left-to-right.
- `vertical`: sections are stacked downward in the order `section_order` names.
- `fixed`: one section and one or more weighted full-canvas variants.

A vertical view's `section_order` is `authored` (the default) or `reversed`.
Ship vertical views are rotations of tail-to-nose horizontal art, so they stack
`reversed` to read nose-up. Art authored directly downward, such as a station's
beacon over its body over its engine glow, uses `authored`. Only vertical views
may declare `reversed`.

Horizontal and vertical views are separate stored art. The editor's rotation
command only creates an editable starting point; rendering never rotates one
view to obtain another.

### Tiers, structure width, and repetition

Tiers are ordered richest/largest first. Each tier defines one shared
**structure width** (the cross-axis geometry of its structures); individual
structures cannot set an independent width. Each Section owns one non-negative,
fixed `repeat` count. A sprite's **length** is the resulting sequence of
structures, whose counts may differ. Rendering never grows those counts to fill
a requested box.

**Every view selects its tier on the requested height**, matching Edge's own
generators. A horizontal view compares the tier's constant structure height; a
vertical view compares its **composed length**, the rows its sections stack to
at their authored repeats. A vertical view's width is not consulted: the tier
fixes one structure width, and centered padding or cropping fits it to the box.
A fixed view selects the first canvas that fits both dimensions. If no tier
fits, the smallest is used and centered cropping provides the requested exact
rectangle.

Because the selector walks the list and takes the first tier that fits, tier
sizes must be **strictly** decreasing on that same measure — two tiers of equal
size make the later one unreachable. Per-archetype repeats make a vertical
view's composed length archetype-dependent, so the ordering must hold for every
archetype.

The editor exposes shared structure width on Tier properties. Changing it
resizes the cross-axis of every variant in every section in that tier as one
validated operation. For fixed canvases, the Tier width field is the canvas
width.

### Sections and variants

A section has one controlled `primary_property` and zero or more controlled
`secondary_properties`. These are metadata in schema v3; they do not alter
runtime composition.

The closed vocabulary is:

```text
thrusters, spindrive, hull, armor, screens, main_gun, weapons,
cargo, sensors, bridge, habitat, radiator, hangar, reactor, utility,
docking, beacon, platform, tower
```

The last four name station parts. The vocabulary is shared rather than scoped
per kind, so the editor keeps one controlled list; ships simply never use them.

Each section's variants must have identical rectangular dimensions. `weight`
is a positive integer. Equal weights use the same `random.Random.choice`
behavior as Edge's original grammar; unequal weights use weighted selection.

#### Per-archetype art

Two optional fields let the rendered archetype change geometry, not only color.
Both are **kind-agnostic**: ships may use them exactly as stations do.

`Variant.archetypes` scopes a variant to named archetypes; empty means any.
Selection resolves in three steps: variants naming the rendered archetype win
outright; if none name it, the un-tagged variants are used as the default art;
if every variant in the section is scoped, nothing is filtered so the pool is
never empty. This reproduces Edge's
`variants.get(archetype_id, variants["default"])`. An unknown or unset
archetype resolves to the un-tagged art.

`Section.archetype_repeats` overrides a section's `repeat` per archetype. A
resolved `0` omits that band entirely; a baseline `repeat: 0` plus one override
makes a band exclusive to a single archetype. Every archetype must still
resolve to at least one section with a positive repeat, or the tier would
compose an empty grid.

```yaml
- id: docking_arms
  primary_property: docking
  repeat: 2
  archetype_repeats:
    ribbon_salvager: 4
    cosmic_arbiter: 0
  variants:
    - id: salvaged_berths
      archetypes: [ribbon_salvager]
      cells: [...]
    - id: plain_berths      # no list: any archetype
      cells: [...]
```

Neither field changes how many random decisions a render consumes: the variant
draw happens once per section regardless of the resolved repeat, and is
discarded when that repeat is zero. Toggling a band off therefore leaves every
other band's chosen variant untouched.

What these fields cannot vary is the skeleton *within* a section: a section's
variants share one `(width, height)` and a tier's variants share one cross-axis
size, so an archetype's band is normalized to its section's rectangle.
Horizontal and vertical views are independent stored art, so a tag applied to
one must be applied to the other separately.

Variant dimensions are therefore edited on Section properties rather than on
an individual Variant. The Section length field resizes every variant in the
section along the composition axis. For fixed canvases, it is the canvas
height. Section properties also edit the Section's single fixed repetition
value. Variant selection always consumes one random decision per section
regardless of repeat count or archetype.

### Glyph and color-mask semantics

Geometry and color are stored as matching rectangular grids. `cells` contains
the rendered glyph. `color_mask` contains one controlled code per cell:

| Code | Color set |
|---|---|
| `S` | Surface |
| `E` | Engine |
| `B` | Beacon |
| `W` | Window |
| `A` | Weapons (armament) |
| `D` | Defensive |

Spaces must use `S`; all visible glyphs may use any color set. Masks are
repeated, fitted, cropped, rotated, and reflected with their glyph grids.
Reflection changes mask positions but never substitutes mask codes.

Every color set uses the same glyph-driven shading:

- `█` and `■` use slot 1.
- structural blocks, lines, corners, wedges, and bevels use slot 2.
- `▒` and `░` use slot 3.
- other one-cell glyphs use slot 4 over slot 1 as their background.
- a missing slot falls back to slot 1.
- space is transparent-looking terminal void.

The editor displays these slots as `█`, `▓`, `▒`, and `◇`, without textual slot
labels. Windows are manually painted with the Window mask; runtime rendering
never places them randomly.

All glyphs must occupy exactly one terminal cell.

## REXPaint export

The reusable library exports a deterministic, one-layer REXPaint `.xp` file and
a matching native REXPaint palette `.txt` file. Export uses the same width,
height, seed, archetype, view, facing, and variant overrides as the Rich preview.
It writes the real authored glyph and uses the cell's color-set slot-1 color as
foreground so import can infer the mask. YAML remains authoritative.

An `.xp` file stores glyph *indices* rather than glyph shapes. The exporter uses
the index order in `sprite_art.rexpaint.REXPAINT_GLYPH_INDICES`; its matching
font sheet is `assets/rexpaint/edge-art-designer.png`. Install that sheet as a
16-column REXPaint art font, retaining the supplied index order. An authored
glyph absent from the map rejects export with its cell position rather than
being silently substituted. The map and font evolve together, so an `.xp` file
must be opened with the matching version of the art font.

Import accepts only a one-layer `.xp` file using that same glyph map. It splits
the image into the current preview's active variants and assigns each visible
cell to the color set containing the nearest configured RGB color. Controlled
color-set order breaks exact ties. Preserved, distinguishable export colors
round-trip; edited, duplicate, or similar colors can produce approximate masks.
Dimensions, seed, view, facing, and active variants must still match. Repeated
glyph and inferred-mask copies must agree.

## Palette catalog

`palettes.yaml` must contain exactly the 14 controlled Edge archetypes. IDs may
not be added, removed, renamed, or duplicated in the editor. Their color values
and color pools are editable.

```yaml
schema_version: 2
fallback_archetype: humanoid_diplomat
archetypes:
  humanoid_diplomat:
    color_sets:
      surface: [grey85, grey58, grey35, grey15]
      engine: [yellow, bright_yellow]
      beacon: [red, bright_red]
      window: [bright_cyan, bright_yellow, grey100]
      weapons: ['#DF7070']
      defensive: ['#60a5fa']
```

Every archetype contains exactly these six sets. A set contains one to four
colors; the first is required and is the fallback for missing slots. The
Palette tab can add colors until the four-slot limit is reached. The shipped
catalog uses a common red armament accent and a distinct blue defensive shade
for each archetype.

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
