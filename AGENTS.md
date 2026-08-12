# AGENTS.md — Edge Art Designer

## What this project is

`edge-art-designer` is a Python 3.12+ Pixi project for authoring procedural
Unicode sprite art in a resizable Textual TUI. Ships and stations (ports,
starbases, and the stardock) are the compositional asset types, while the
reusable `sprite_art` package also supports fixed-canvas sprites for future
art.

The application edits versioned YAML assets, renders changes at multiple sizes
in real time, supports mouse painting, and keeps geometry separate from the
controlled Edge of the Unknown archetype palettes.

## Authoritative design documents

Read these before architectural or format changes:

- `SHIP_DESIGN_PRINCIPALS.md` — visual and procedural ship-art principles.
- `docs/PORT_DESIGN_PRINCIPLES.md` — the same for stations.
- `docs/SPRITE_ART_FORMAT.md` — schema, composition, validation, and transform
  contract.
- `docs/EDGE_INTEGRATION.md` — the vendoring and game-runtime seam.

The authoring-only REXPaint and view-generation helpers live in the sibling
`sprite_art_authoring` package. Keep new authoring exports there rather than
adding them to the runtime facade.

If implementation changes any documented contract, update the relevant
document in the same change.

## Reference project

The existing game is at:

```text
/home/mcduffie/Devel/edge-of-the-unknown
```

Relevant reference files include:

- `edge/art/ship.py`
- `edge/art/hull.py`
- `edge/art/generator.py`
- `tests/test_ship_art.py`
- `docs/DESIGN_ARTGEN.md`
- `docs/SECTOR_SCENE_COMPOSITION.md`

Treat that repository as read-only unless the user explicitly requests changes
there. Reuse its public behavior and algorithms cleanly; do not modify it as a
side effect of editor work.

## Architecture

Dependencies flow in one direction:

```text
sprite_art_designer  →  sprite_art_authoring  →  sprite_art  →  Rich + PyYAML
       Textual                 tools consume both packages
```

- `src/sprite_art/` is the reusable, game-vendorable runtime library. It must
  not import Textual, editor code, or `sprite_art_authoring`.
- `src/sprite_art_authoring/` contains editor interchange and authoring
  transforms and may depend on `sprite_art`.
- `src/sprite_art_designer/` is the Textual application and may depend on both
  sprite-art packages.
- `assets/palettes.yaml` is the single palette catalog.
- `assets/sprites/` stores one independently versioned YAML file per sprite,
  foldered by kind (`ships/`, `ports/`). Sprite ids are unique across the whole
  tree, so the folder is presentation only.
- `tools/` contains development-time import/generation utilities, not runtime
  dependencies.

Keep the reader and renderer synchronous, deterministic, and usable without
launching the TUI.

## Sprite-art invariants

- Every glyph occupies exactly one terminal cell.
- Every variant is a non-empty rectangle with uniform row widths.
- All variants in a section have identical dimensions.
- All parts in a compositional tier have the same cross-axis size.
- Tiers are ordered richest/largest first, and strictly so: two tiers of equal
  size make the later one unreachable.
- Tier selection always budgets on the requested height. A horizontal view
  compares the tier's constant structure height; a vertical view compares the
  rows its sections stack to. A vertical view's width is not consulted.
- A fixed-canvas tier contains exactly one section.
- Variant weights are positive integers and default to equal likelihood.
- A section's `repeat` is a fixed authored count, optionally overridden per
  archetype. A resolved `0` omits the band; every archetype must still keep at
  least one band in every tier. Repetition consumes no random draws.
- Variant selection consumes exactly one random decision per section,
  independent of target size, repeat count, or archetype. The draw happens even
  for a zeroed band and is then discarded, so toggling one band off never
  reshuffles the others.
- The rendered archetype selects geometry as well as palette, through
  `Variant.archetypes` and `Section.archetype_repeats`. Both are kind-agnostic.
  An unknown or unset archetype composes the un-tagged, baseline art.
- Rendered output exactly fills the requested width and height.
- Facing is a deterministic post-composition transform and is not part of the
  random seed.
- Symmetry is never assumed. Art is stored as full, asymmetric-capable rows;
  Edge's left-half mirroring is consumed once at import.
- Horizontal and vertical views are independently stored art. Automatic
  rotation creates an editable starting view; runtime rendering does not rotate
  one orientation to obtain another.
- A vertical view's `section_order` decides whether its bands stack as authored
  or reversed. Only vertical views may reverse.
- Stations have a single `vertical` view and no mirror facing.
- Unknown 90-degree glyph rotations become `◇` and produce a warning.
- Left/right and up/down reflection must remain glyph-aware and reversible.

The four original gameplay ship roles are an intentional visual migration
rather than a byte-for-byte translation of Edge's in-code grammar; see
`docs/EDGE_INTEGRATION.md` for what the seam does and does not guarantee.

## Controlled vocabularies

Section properties are metadata in schema version 4. A section has one primary
property and zero or more secondary properties from:

```text
thrusters, spindrive, hull, armor, screens, main_gun, weapons,
cargo, sensors, bridge, habitat, radiator, hangar, reactor, utility,
docking, beacon, platform, tower
```

The last four name station parts. The list is shared across kinds rather than
scoped per kind, so the editor keeps one controlled Select.

The palette catalog must contain exactly these archetypes:

```text
humanoid_diplomat
canid_technologist
tentacled_envoy
brain_dome_automaton
ribbon_salvager
temporal_broker
cosmic_arbiter
telepath_aristocrat
engineered_aesthete
amorous_imp
horned_grudgekeeper
psionic_overlord
colonial_broodmaster
winged_schemer
```

The editor may change palette values but must not add, delete, duplicate, or
rename archetypes. Unknown archetypes fall back to `humanoid_diplomat`.

## Persistence and recovery

- Primary files are saved only through an explicit save action.
- Writes must be atomic.
- Unsaved sprite changes create crash-recovery snapshots below
  `.edge-art-designer/recovery/`.
- Recovery snapshots are not primary assets and remain Git-ignored.
- Each sprite file and the palette catalog carries its own `schema_version`.
- Reject invalid or unsupported data with actionable validation errors; do not
  silently repair authored geometry.

## TUI expectations

- Keep mouse painting and right-button erasing functional.
- Keep keyboard painting and cursor movement as an accessible alternative.
- Preview sizes, seed, archetype, view, and facing remain configurable.
- Wide terminals show navigator, canvas, tools, and previews together.
- Narrow terminals provide switchable panels without losing capabilities.
- Palette editing remains restricted to the controlled archetype list.
- Structural editing must preserve the schema invariants or report why an
  operation is invalid.

## Development commands

Use Pixi for all project checks:

```bash
pixi run app
pixi run lint
pixi run typecheck
pixi run test
pixi run check
```

Before handing off a change, run:

```bash
pixi run check
```

The required baseline is:

- Ruff clean.
- `mypy --strict` clean for `src/`.
- All pytest tests passing, including Textual Pilot resize and painting tests.

Add or update tests whenever changing schema validation, RNG behavior,
composition, transforms, persistence, or responsive UI behavior.

## File-editing guidance

- Preserve user-authored YAML and unrelated working-tree changes.
- Prefer small, typed functions and dataclasses in the reusable library.
- Keep generated assets deterministic and reviewable.
- Do not introduce a new runtime dependency without updating `pyproject.toml`,
  `pixi.lock`, and the architecture/integration documentation.
- Do not weaken validation merely to accept malformed assets.

