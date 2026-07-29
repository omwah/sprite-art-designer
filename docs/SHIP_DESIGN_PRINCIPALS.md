# Procedural ANSI/Unicode Spaceship Art in *Edge of the Unknown*

## Overview

The spaceship art system in *Edge of the Unknown* is best understood as
**procedural composition of hand-authored cell art**, not as unconstrained
generative drawing.

Each ship is assembled from small Unicode fragments chosen by a seeded random
number generator, repeated by fixed authored section counts, fitted to the
requested dimensions, optionally reflected to face the opposite direction, and
finally painted into a `rich.text.Text` object with an archetype-specific
terminal palette. This hybrid method preserves crisp, recognizable silhouettes
at very small terminal sizes while still giving individual ships stable visual
variety.

The design is governed primarily by:

- `edge/art/ship.py` — ship roles, section grammars, tier selection, and the
  ship generator.
- `edge/art/hull.py` — shared part/slot types, horizontal composition,
  glyph-aware reflection, palettes, and cell painting.
- `edge/art/generator.py` — deterministic local RNG construction, caching, and
  dispatch.
- `docs/DESIGN_ARTGEN.md` — the procedural-art architecture and design intent.
- `docs/SECTOR_SCENE_COMPOSITION.md` — how generated ships are sized and placed
  in the arrival scene.

## 1. Hand-authored grammar, procedurally assembled

At ship-sprite scale—sometimes only three rows high—fully mathematical shape
generation is counterproductive. Signed-distance fields and per-cell noise do
not have enough samples to describe a readable spacecraft: outlines become
blobs and random detail becomes speckle. The game therefore reserves raster and
SDF methods for larger organic subjects such as planets and uses **compositional
cell art** for ships.

The basic vocabulary consists of two authored types:

- A **variant** is a rectangular fragment made from full Unicode rows.
- A **section** is one semantic position in a ship. It offers interchangeable
  variants and defines one fixed positive repetition count.

A ship grammar is an ordered list of sections. Generation chooses one variant
from each section, repeats it by its authored count, then joins the resulting
fragments edge-to-edge. The geometry is
authored; the combination, length, lights, windows, color treatment, and facing
are procedural.

This creates a useful middle ground:

- stronger visual authorship than a noise field;
- more variety than a collection of fixed sprites;
- predictable silhouettes at tiny sizes;
- arbitrary requested boxes instead of a handful of asset resolutions.

The canonical first part in each slot anchors the intended silhouette, while
additional parts provide seeded variations such as towers, nacelles, vents,
panels, or different engine blocks.

## 2. A ship is a readable sequence of functional sections

The four classic roles use a nose-right five-part sequence:

```text
THRUSTERS → SPINDRIVE → HULL → SCREENS → MAIN GUN
tail                                      nose
```

These sections are not merely decorative. They deliberately echo the four
player-modifiable engine-room subsystems, with the structural/cargo hull added
as the repeatable backbone:

| Section | Visual job | Mechanical association |
|---|---|---|
| Thrusters | Exhaust glow and engine block | Thrusters |
| Spindrive | Warp block ahead of the engines | Spindrive |
| Hull | Cargo bays, armour, structure, towers | Hull size and capacity |
| Screens | Deflector facets near the bow | Screens |
| Main gun | Barrel, taper, and muzzle | Main Gun |

The principle is **mechanical legibility through silhouette**: even stylized
art should suggest what kind of machine the player is looking at. A transport
gets a broad, repeatable container backbone; a fighter is thin and swept; a
warship emphasizes armour, screens, and a spinal weapon; a capital warship
gains a tall superstructure and heavy prow.

Specialist roles use the same tail-to-nose reasoning with role-specific section
names and properties; `SHIP_TYPE_PRINCIPLES.md` defines each grammar. The
current public role vocabulary is:

- `fighter`
- `transport`
- `warship`
- `capital_warship`
- `needle_picket`
- `falsehold_raider`
- `junction_pinnace`
- `radiant_lance`
- `hearth_freighter`
- `pearl_shell`
- `marrow_dart`
- `broadside_citadel`

An unknown role falls back to the fighter grammar inside `SpriteLibrary`, while
coverage tests ensure that every role shipped in game configuration maps to a
real art subtype rather than silently relying on that fallback.

## 3. Asymmetry is essential to “ship-ness”

Ports and starbases are vertically stacked, left/right-symmetric structures.
Ships use the same general grammar machinery along the other axis but
intentionally reject that symmetry.

Every ship fragment is authored as complete rows. Dorsal bridges, ventral pods,
offset nacelles, swept wings, and uneven weapon arrangements are drawn directly
into those rows. The tail and nose must remain visibly different; tests
explicitly guard against accidentally producing a ship identical to its own
mirror.

This asymmetry has two benefits:

1. It makes direction of travel instantly readable.
2. It permits functional storytelling—engines belong aft, screens and weapons
   belong forward, and vertical structures need not be artificially mirrored.

## 4. Author once, face either direction

All ship grammars are authored facing right. A left-facing ship is produced only
after composition by reflecting every completed row.

Reflection is glyph-aware:

1. reverse the characters in the row;
2. replace every directional Unicode glyph with its mirror twin.

Examples include:

```text
▟ ↔ ▙    ▜ ↔ ▛    ▖ ↔ ▗    ▘ ↔ ▝
◢ ↔ ◣    ◥ ↔ ◤    ╭ ↔ ╮    ╰ ↔ ╯
┌ ↔ ┐    └ ↔ ┘    ╾ ↔ ╼    ▶ ↔ ◀
╱ ↔ ╲
```

Characters such as full blocks, shade blocks, and rules pass through unchanged.

This transform is an **involution**: applying it twice returns the original
row. It also consumes no random values. The generator deliberately excludes
`facing` from its RNG seed, so left- and right-facing renderings are the same
ship rather than two independently randomized designs.

## 5. Responsive art uses semantic tiers, not blind scaling

Each role owns multiple grammar tiers ordered from tallest and richest to
smallest and simplest.

The generator selects the first tier whose authored row height fits the
requested height. Large boxes therefore receive the full silhouette, while a
three-row box receives a purpose-built compact grammar—typically a readable
glow/body/muzzle pattern—instead of a detailed ship cropped into nonsense. If
even the smallest tier exceeds the height, the compact tier is still selected
as the safest fallback and the painter performs centered cropping.

Length is authored independently within each tier. The composer:

1. chooses exactly one variant per section;
2. repeats it by the Section's fixed positive count;
3. joins the repeated sections in semantic tail-to-nose order.

For ships, the repeatable section is primarily the hull backbone, so increasing
its authored count makes a tier longer without stretching its glyphs or
distorting its bow and engines. Requested boxes do not change authored
repetition.

The final painter always returns the exact requested rectangle:

- smaller art is centered and padded with empty cells;
- wider or taller art is cropped symmetrically;
- cropping preserves both iconic extremities as fairly as possible rather than
  discarding only the bow or tail.

## 6. Determinism is part of visual identity

Procedural variation must never make a known ship change appearance between
visits or replays.

The public sprite generator receives a stable seed plus entity type, subtype,
dimensions, archetype, and facing. It builds a local `random.Random` from a
string containing:

```text
seed | entity_type | subtype | archetype_id
```

The caller supplies the stable entity-derived seed; the art layer keeps this
presentation randomness local rather than adding visual-only state to core game
models. The same complete request therefore produces the same glyphs and Rich
style spans.

Composition also preserves RNG stability across widths. It makes one random
variant-selection draw per section, regardless of how many times the chosen
hull fragment is repeated. Repetition is fixed authored data and consumes no
random draws. The
renderer retains the two historical pre-composition draws so converted variant
choices stay stable, but palette shading and windows consume no random draws.

`generate_sprite` is cached with an LRU cache, currently holding 128 request
variants. Caching is a performance optimization, not a source of identity:
uncached generation remains deterministic.

## 7. Geometry and color are separate systems

The grammar stores a glyph grid and an equally sized color-mask grid. The mask
chooses Surface, Engine, Beacon, Window, Weapons, or Defensive; the painter
interprets glyph shape the same way inside every set:

| Authored cell | Rendered meaning |
|---|---|
| `█`, `■` | First/full-block color |
| `▒`, `░` | Third/recess color |
| Half blocks, box drawing, rules, wedges | Second/structural color |
| space | Transparent-looking terminal void |
| Any other non-space glyph | Fourth/facet color over the first color |

The glyph carries shading while the parallel mask carries function. A single
shape can be recolored or reassigned without substituting marker characters.

If a color set contains fewer than four colors, missing glyph slots fall back
to its first color. Windows are placed only by painting the Window mask; the
renderer never turns Surface cells into windows randomly.

The output is a Rich `Text` grid. Unicode supplies the geometry; Rich styles
supply terminal foreground/background colors and ultimately the ANSI
presentation. Keeping those responsibilities separate makes the art usable in
the Textual UI, terminal previews, and vector sprite-sheet exports through the
same generation path.

## 8. Archetype controls style; role controls shape

Ship role answers **what kind of vessel is this?** Archetype answers **whose
design language does it use?**

The owner's `archetype_id` selects six controlled color sets. Each contains one
to four ordered colors demonstrated in the editor by `█`, `▓`, `▒`, and `◇`.

The key is deliberately an archetype rather than a species name or ID. Species
can be renamed or reskinned in a roster without destabilizing the underlying
visual family. Ships and ports owned by the same technological culture can also
share a coherent palette. Unknown or absent archetypes fall back to the
Federation-like grey `humanoid_diplomat` style.

Palette shading is deterministic and independent of the seed. Seeded variation
comes from structural variant selection.

## 9. Scene composition protects the sprite's meaning

Generating a readable ship is only half of the problem; the arrival scene must
present it at a meaningful scale and in clear space.

The scene follows several rules:

- **Scale communicates category.** The intended hierarchy is planet ≫ Stardock
  > starbase > port > ship > fighter/mine glyph. A visiting ship must never
  visually rival the world or station it approaches.
- **Ships occupy open sky.** They are placed to the left of the primary subject
  with stable, seeded jitter so repeated sectors do not look like identical
  forms.
- **Ships face the subject.** Traffic generally points toward the primary body;
  when there is no primary, one ship may face another.
- **Crop to ink before placement.** Transparent padding in the requested sprite
  box must not reserve empty sky.
- **Occupancy is authoritative.** Art, labels, and small scattered glyphs cannot
  overlap reserved cells.
- **Failure degrades to information, not clutter.** If no clear berth exists,
  the object becomes a clickable text row instead of being painted over another
  sprite.

These layout rules preserve the art's silhouette and directional cues while
keeping the game interface truthful and usable.

## 10. Constraints that keep the method reliable

The implementation turns its artistic assumptions into testable contracts:

- every part in a tier has the same number of rows;
- every row within a part has the same width;
- grammar tiers are ordered tallest-first and reach a three-row compact form;
- every asymmetric glyph used by a ship exists in the mirror table;
- reflection is reversible;
- generation is deterministic in both text and style spans;
- part-selection draw count is independent of width;
- each section has one positive fixed repetition count;
- every generated result exactly fills its requested box;
- opposite facings are exact glyph-aware reflections;
- ship silhouettes remain genuinely asymmetric;
- all configured ship roles and roster archetypes have art coverage.

These are not merely implementation tests. They express the core artistic
principles in executable form and make the procedural vocabulary safe to
extend.

## 11. Practical authoring principles

When adding or revising ship art:

1. **Design the silhouette first.** It must read in monochrome and at the compact
   tier before color-mask detail is considered.
2. **Make role visible.** Cargo, speed, armour, screens, and weapon emphasis
   should be apparent in section proportions and glyph density.
3. **Keep tail and nose distinct.** Canonical rows face right, and every
   directional glyph must have a valid mirror.
4. **Use full rectangular parts.** Equal tier heights and uniform row widths are
   composition invariants.
5. **Repeat structure, not extremities.** Length should come from the hull
   backbone; engines and prow remain iconic caps.
6. **Provide a semantic compact tier.** Never assume the full-detail drawing can
   simply be cropped to three rows.
7. **Encode shading with glyphs and function with masks.** Let palettes recolor
   the structure instead of embedding color intent into substitute glyphs.
8. **Preserve RNG draw discipline.** Size changes must not introduce a
   variable number of random part-selection draws.
9. **Judge art in context.** Preview both facings, multiple widths and heights,
   multiple archetypes, and the scale hierarchy of the sector scene.
10. **Add or update contract tests with the grammar.** Procedural art remains
    maintainable when its visual assumptions are mechanically checked.

## Summary

The system's central idea is simple: **procedural does not have to mean
uncontrolled**. *Edge of the Unknown* gets variety by recombining carefully
drawn Unicode parts under a deterministic grammar. It gets readability by
mapping those parts to ship function, preserving asymmetry, and selecting
purpose-built detail tiers. It gets cultural identity by painting geometry
through archetype palettes. Finally, it protects all of those choices through
stable seeds, glyph-aware reflection, responsive composition, scene-scale
rules, caching, and executable tests.

The result is terminal art that feels authored, varies like a generated world,
and remains reproducible enough to belong in a deterministic game.
