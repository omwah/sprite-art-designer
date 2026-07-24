# AGENTS.md — Edge Art Designer

## What this project is

`edge-art-designer` is a Python 3.12+ Pixi project for authoring procedural
Unicode sprite art in a resizable Textual TUI. Ships are the first compositional
asset type, while the reusable `sprite_art` package also supports fixed-canvas
sprites for future art.

The application edits versioned YAML assets, renders changes at multiple sizes
in real time, supports mouse painting, and keeps geometry separate from the
controlled Edge of the Unknown archetype palettes.

## Authoritative design documents

Read these before architectural or format changes:

- `SHIP_DESIGN_PRINCIPALS.md` — visual and procedural ship-art principles.
- `docs/SPRITE_ART_FORMAT.md` — schema, composition, validation, and transform
  contract.
- `docs/EDGE_INTEGRATION.md` — the vendoring and game-runtime seam.

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
sprite_art_designer  →  sprite_art  →  Rich + PyYAML
       Textual
```

- `src/sprite_art/` is the reusable, game-vendorable library. It must not import
  Textual or editor code.
- `src/sprite_art_designer/` is the Textual application and may depend on
  `sprite_art`.
- `assets/palettes.yaml` is the single palette catalog.
- `assets/sprites/` stores one independently versioned YAML file per sprite.
- `tools/` contains development-time import/generation utilities, not runtime
  dependencies.

Keep the reader and renderer synchronous, deterministic, and usable without
launching the TUI.

## Sprite-art invariants

- Every glyph occupies exactly one terminal cell.
- Every variant is a non-empty rectangle with uniform row widths.
- All variants in a section have identical dimensions.
- All parts in a compositional tier have the same cross-axis size.
- Tiers are ordered richest/largest first.
- A fixed-canvas tier contains exactly one section.
- Variant weights are positive integers and default to equal likelihood.
- Repetition starts at `min`, never exceeds `max`, and does not consume random
  draws.
- Variant selection consumes one random decision per section, independent of
  target size.
- Rendered output exactly fills the requested width and height.
- Facing is a deterministic post-composition transform and is not part of the
  random seed.
- Horizontal and vertical views are independently stored art. Automatic
  rotation creates an editable starting view; runtime rendering does not rotate
  one orientation to obtain another.
- Unknown 90-degree glyph rotations become `◇` and produce a warning.
- Left/right and up/down reflection must remain glyph-aware and reversible.

Preserve the converted horizontal output of `fighter`, `transport`, `warship`,
and `capital_warship`. For equivalent requests, both `Text.plain` and Rich style
spans must continue matching Edge of the Unknown.

## Controlled vocabularies

Section properties are metadata in schema version 1. A section has one primary
property and zero or more secondary properties from:

```text
thrusters, spindrive, hull, armor, screens, main_gun, weapons,
cargo, sensors, bridge, habitat, radiator, hangar, reactor, utility
```

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

