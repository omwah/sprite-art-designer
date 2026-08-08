# Port Design Principles

Companion to `SHIP_DESIGN_PRINCIPALS.md`, covering the three station subtypes:
`trading_port`, `starbase`, and `stardock`. The reasoning here originates in
Edge of the Unknown's `edge/art/port.py`, whose grammars these assets were
imported from.

## Stations are icons, not renderings

A station is often drawn as few as three rows tall. At that resolution an
implicit-surface trace has too few samples to read as anything recognizable,
which is why stations are hand-authored silhouettes rather than traced shapes. A
drawn silhouette stays crisp at three rows and keeps the BBS/ANSI heritage the
project is going for.

The practical consequence: **design each tier for the box it will actually be
selected at**, not by shrinking the largest one. The compact tiers are separate
drawings, not reductions.

## Vertical bands, top to bottom

Stations compose along the height axis as a stack of bands. Read top to bottom,
the vocabulary is:

1. a beacon or mast at the crown,
2. a control tower or deck below it,
3. a repeating body that sets the station's size,
4. a taper or base,
5. an engine glow at the foot.

Only the body repeats. Everything else appears once, which is what makes the
crown and foot the station's identity — and why cropping is so damaging. A
station cropped through its beacon and glow stops reading as a station. Tier
selection budgets on height precisely to prevent that; see
`docs/SPRITE_ART_FORMAT.md`.

## The beacon and glow language

Two cells carry meaning beyond their shape:

- `▀` in the Beacon color set is the navigation light at the crown.
- `▄` in the Engine color set is the drive glow at the foot.

Edge encodes these as `R` and `Y` markers that its painter expands; sprite
documents store the real glyph with its color-mask code instead. Keep them at
the extremities. A beacon in the middle of a hull reads as damage.

## Symmetry is a choice, not a rule

Edge authored every port as a left half and mirrored it at render time, which
guaranteed symmetry and halved the drawing. Sprite documents store full rows, so
that guarantee is gone and asymmetry is available. The imported assets are
symmetric because their source was; new work does not have to be.

If you do keep a station symmetric, the centre column still has to be a glyph
that reads correctly on the mirror axis. Corner, quadrant, and triangle glyphs
seam.

## Archetypes change the silhouette

Unlike ships, stations vary their geometry by owner archetype, not only their
palette. A Vesk trading post and a Quill one are different drawings. This is
carried by `Variant.archetypes` on the bands themselves and by
`Section.archetype_repeats` where a species builds more or fewer of something.

Two things follow:

- Archetype art is only as reachable as its tier. A per-archetype band in a tier
  that never gets selected at real box sizes is invisible. Check with
  `tools/import_edge_ports.py <edge-checkout> --audit`.
- An un-tagged variant is the fallback for every archetype that has no art of
  its own, so every band needs at least one.

## The Stardock

The flagship `stardock` silhouette deliberately evokes the classic TradeWars
2002 Federation Stardock: a vertical, left/right-symmetric station with a red
beacon up top, a control tower, a wide platform trailing thin docking arms, a
tapering chevron body, and a yellow engine glow at the bottom.

It has no per-archetype variants and should not gain any. It is the Federation's
one station, the same for everyone who sees it, and that uniformity is the point
of it.
