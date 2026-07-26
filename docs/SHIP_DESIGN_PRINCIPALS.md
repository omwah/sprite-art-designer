# Procedural ANSI/Unicode Spaceship Art in *Edge of the Unknown*

## Overview

The spaceship art system in *Edge of the Unknown* is best understood as
**procedural composition of hand-authored cell art**, not as unconstrained
generative drawing.

Each ship is assembled from small Unicode fragments chosen by a seeded random
number generator, stretched to the requested dimensions by repeating selected
hull sections, optionally reflected to face the opposite direction, and finally
painted into a `rich.text.Text` object with an archetype-specific terminal
palette. This hybrid method preserves crisp, recognizable silhouettes at very
small terminal sizes while still giving individual ships stable visual variety.

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

The basic vocabulary consists of two immutable types:

- A **part** is a rectangular fragment made from full Unicode rows. A part may
  be marked repeatable.
- A **slot** is one semantic position in a ship. It offers interchangeable parts
  and defines minimum and maximum repetition counts.

A ship grammar is an ordered tuple of slots. Generation chooses one part from
each slot, then joins the resulting fragments edge-to-edge. The geometry is
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

Full-detail ships are authored nose-right as a left-to-right sequence:

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

The current public role vocabulary is:

- `fighter`
- `transport`
- `warship`
- `capital_warship`

An unknown role falls back to the fighter grammar inside `ShipGenerator`,
while coverage tests ensure that every role shipped in game configuration maps
to a real art subtype rather than silently relying on that fallback.

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

Characters such as full blocks, shade blocks, rules, and light markers pass
through unchanged.

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

Width is handled independently. The composer:

1. chooses exactly one part per slot;
2. starts every slot at its minimum repetition count;
3. grows repeatable sections one block at a time in round-robin order;
4. stops when another block would exceed the target width or the slot reaches
   its maximum.

For ships, the repeatable section is primarily the hull backbone, so increasing
width makes a ship longer without stretching its glyphs or distorting its bow
and engines. The composed width grows monotonically and does not overshoot the
request unless the grammar's irreducible minimum is already wider than the box.

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
part-selection draw per grammar slot, regardless of how many times the chosen
hull fragment is repeated. Repetition is calculated arithmetically. Changing
the available width does not unexpectedly shift the random stream used later
for palette choices and windows.

`generate_sprite` is cached with an LRU cache, currently holding 128 request
variants. Caching is a performance optimization, not a source of identity:
uncached generation remains deterministic.

## 7. Geometry and color are separate systems

The grammar defines structure through a small, closed hull alphabet. The shared
painter interprets those glyphs semantically:

| Authored cell | Rendered meaning |
|---|---|
| `█` | Bright, lit plating |
| `▒`, `░` | Dark recesses |
| Half blocks, box drawing, rules, wedges | Mid-tone hull, struts, bevels, and panels |
| `R` | Navigation beacon marker, rendered as `▀` |
| `Y` | Engine/glow marker, rendered as `▄` |
| space | Transparent-looking terminal void |
| Any other non-space glyph | Facet or etched surface feature |

The grammar therefore carries shading in its character choices rather than
hard-coded colors. A single shape can be recolored coherently without changing
its construction.

Facet glyphs are painted in a dedicated facet color over a bright-hull
background so their negative space looks etched into plating. Bright hull cells
have a small fixed chance—five percent—to become lit windows, adding signs of
life without dissolving the silhouette into noise.

The output is a Rich `Text` grid. Unicode supplies the geometry; Rich styles
supply terminal foreground/background colors and ultimately the ANSI
presentation. Keeping those responsibilities separate makes the art usable in
the Textual UI, terminal previews, and vector sprite-sheet exports through the
same generation path.

## 8. Archetype controls style; role controls shape

Ship role answers **what kind of vessel is this?** Archetype answers **whose
design language does it use?**

The owner's `archetype_id` selects a shared hull palette containing:

- bright, middle, and dark hull tones;
- pools of beacon and engine-light colors;
- window colors;
- a facet color.

The key is deliberately an archetype rather than a species name or ID. Species
can be renamed or reskinned in a roster without destabilizing the underlying
visual family. Ships and ports owned by the same technological culture can also
share a coherent palette. Unknown or absent archetypes fall back to the
Federation-like grey `humanoid_diplomat` style.

The seed chooses steady light hues from the selected palette once per sprite.
Thus palette establishes cultural continuity while seeded choices keep members
of that culture from looking completely cloned.

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
- composed width grows monotonically and respects bounds;
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
   tier before color or window variation is considered.
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
7. **Encode light and material with the established glyph vocabulary.** Let
   palettes recolor the structure instead of embedding cultural identity into
   one-off geometry without a deliberate reason.
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
