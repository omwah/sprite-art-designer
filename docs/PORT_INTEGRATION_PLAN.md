# Ports, Starbases, and Stardock in Edge Art Designer

> **Status: implemented.** This is the plan as approved, kept for the reasoning
> behind each decision. Implementation diverged from it in several places —
> see [What changed during implementation](#what-changed-during-implementation)
> at the end before treating any detail here as current. The authoritative
> contracts live in `docs/SPRITE_ART_FORMAT.md`, `docs/EDGE_INTEGRATION.md`,
> `docs/PORT_DESIGN_PRINCIPLES.md`, and `AGENTS.md`.

## Context

Edge of the Unknown generates station art procedurally in
`/home/mcduffie/Devel/edge-of-the-unknown/edge/art/port.py`, on the shared
part/slot machinery in `edge/art/hull.py`. Ships already moved out of that
in-code grammar into authored YAML in this repository; ports, starbases, and the
stardock have not. That leaves station art un-editable, un-reviewable, and
changeable only by a Python edit.

This work brings the three port subtypes into `sprite_art` /
`sprite_art_designer` using the same schema, composition, and editing mechanisms
as ships, and keeps the vendoring seam back into the game intact for both kinds.

Three deliberate departures from Edge:

- **Vertical only.** Stations have a single `vertical` view and no facing mirror.
- **No symmetry assumption.** Edge authors ports as a left half and mirrors at
  render time. `sprite_art` stores full-width rows; mirroring happens once, at
  import, and is never a runtime concept.
- **Composition, not fill-to-fit.** Edge grows repeatable slots to fill a
  requested height. `sprite_art` uses authored per-section repeats plus size
  tiers — the model ships already adopted.

**On naming:** stardock is a special kind of starbase, but Edge's seed contract
forces the *kind* to be `port` for all three (`generator.py:88`,
`f"{seed}|{entity_type}|{subtype}"`). All three sprites therefore carry
`kind: port`, and the specialization lives in `role` / subtype —
`trading_port`, `starbase`, `stardock` — exactly as `PORT_SUBTYPES`
(`port.py:72`) already has it.

---

## Decisions taken

| Question | Decision |
|---|---|
| Tier selection | Always budget on requested **height**, matching Edge for both kinds (§1) |
| Edge's per-archetype port silhouettes | New optional `Variant.archetypes` allow-list; still exactly one RNG draw per section, from the filtered list (§2) |
| Per-archetype structure | New `Section.archetype_repeats`; `repeat` floor drops to 0 so a band can be omitted or species-exclusive (§2) |
| `_compose_vertical`'s section reversal | New `View.section_order` flag (`authored` \| `reversed`); ships keep `reversed`, ports use `authored` (§2) |
| Port part nouns | Extend the single shared `PROPERTY_IDS` vocabulary |
| Art source | Import from Edge's `PORT_GRAMMAR`, then hand-refine in the TUI (§3) |

The three schema additions land together as one bump to `schema_version: 4`.

---

## 1. Tier selection always budgets on height

This is the correctness fix that makes stations viable, so it lands first. It is
also a bug in the existing library, independent of ports.

### What Edge does

Edge always passes the requested **height** as the tier budget; only the *floor*
function differs per generator:

| Generator | Call | Floor |
|---|---|---|
| ships (`ship.py:531`) | `select_grammar(tiers, height, _tier_height)` | `_tier_height` (`:526`) — the tier's authored row height. Ship length grows by tiling along width, so height is the fixed dimension |
| ports (`port.py:384`) | `select_grammar(tiers, height, _grammar_floor)` | `_grammar_floor` (`:375`) — the minimum **stacked** height, `Σ(smallest part rows × min_repeat)` |

Both are "select on height". For a horizontal ship that height is the cross
axis; for a vertical port it is the composition axis.

### What `sprite_art` does

`render._select_tier` (`render.py:129`) generalized this as "always the cross
axis" instead of "always height":

- horizontal: `budget = height`, floor `Tier.cross_axis_size` = max variant
  height. **Identical to Edge.**
- vertical: `budget = width`, floor `Tier.cross_axis_size` = max variant width.
  **Wrong** — it compares the fixed structure width instead of the stacked
  height, which is the dimension the composition actually consumes.

Consequence at Edge's real boxes (`edge/core/config.py:1479-1481`: `port 16×6`,
`starbase 22×9`, `stardock 38×16`; the gallery at
`edge/tui/screens/sprites_gallery.py:85` asks `18×8`). `trading_port` in `16×6`:
`full` is 11 wide, so `11 ≤ 16` selects it, but it stacks ~10 rows and
`_fit_grid` center-crops 4 — removing the top beacon and bottom engine glow, the
two features that make a station read as a station. Edge, budgeting on height,
correctly drops to its compact grammar.

### The fix

Add a stacked-length accessor beside `Tier.cross_axis_size` (`model.py:196`):

```python
def composed_length(self, axis: Axis, archetype_id: str | None = None) -> int:
    """Rows (vertical) or columns (horizontal) this tier occupies at its
    authored repeats, resolved for one archetype (see §2). Exact, because
    Section.validate forces every variant in a section to share one
    (width, height)."""
```

`_select_tier` then becomes, for every axis, "the first tier whose height
requirement fits the requested height":

- `horizontal`: budget `height`, floor `cross_axis_size(axis)` — **unchanged**.
- `vertical`: budget `height`, floor `composed_length(axis, archetype_id)` — was
  `width` / `cross_axis_size`.
- `fixed`: unchanged (already checks both dimensions of the single canvas).
- No tier fits → last (smallest) tier, unchanged.

Width is deliberately not consulted for a vertical view, matching Edge: the tier
fixes one constant structure width, and `_fit_grid` (`render.py:368`) centers or
crops horizontally, exactly as Edge's `render_grid` (`hull.py:346-354`) does.

`_select_tier` needs `archetype_id` threaded in; §2 requires the same threading
for `_choose_variant`, so it is one plumbing pass, not two.

### Blast radius

- **Ship horizontal renders are byte-identical** — that branch is untouched, so
  the shipped ship assets and the `AGENTS.md` preservation clause are unaffected.
- **Ship vertical views may select a different tier.** Edge does not request them
  today (`generator.py:111` passes only `right`/`left` for ships; `up`/`down` is
  a `sprite_art` extension), so the impact is confined to editor previews and
  tests. Record a before/after tier-selection matrix over the 12 roles × a grid
  of box sizes as review evidence.

### Tier ordering validation

`View.validate` (`model.py:270`) requires tiers ordered richest-first by
`cross_axis_size`. Make the ordering key the same quantity the selector uses:
`cross_axis_size` for horizontal, `composed_length` for vertical — and because
§2 makes the latter archetype-dependent, the ordering must hold **for every
archetype** (15 passes over a handful of tiers; trivial). Verify the 12 shipped
ship assets still validate before committing.

---

## 2. `sprite_art` schema — v4

Three additions, one bump, one migration.

`src/sprite_art/model.py`

- `SPRITE_SCHEMA_VERSION = 4` (`:11`); `Sprite.validate` (`:287`) accepts only 4.
  `PALETTE_SCHEMA_VERSION` stays 2.
- `Variant.archetypes: list[str] = field(default_factory=list)` (`:80`).
  Validate: entries in `ARCHETYPE_IDS`, no duplicates. Empty means "any".
- `Section.archetype_repeats: dict[str, int] = field(default_factory=dict)`
  (`:140`). Validate: keys in `ARCHETYPE_IDS`, values `>= 0`.
- `Section.repeat` floor drops from `1` to `0` (`:167`).
- `View.section_order: Literal["authored", "reversed"] = "authored"` (`:236`).
  Validate: `reversed` only legal when `axis == "vertical"`.
- Extend `PROPERTY_IDS` (`:39`) with station nouns: `docking`, `beacon`,
  `platform`, `tower`. Metadata only; ships never use them.

`src/sprite_art/io.py` — `_variant_from_data`/`_to_data` (`:37`, `:180`),
`_section_from_data`/`_to_data` (`:52`, `:190`) and `_view_from_data`/`_to_data`
(`:86`, `:200`) carry the new fields, omitting each key at its default so
migrated ship YAML stays clean.

### Archetype filtering — varies a band's *content*

`render._choose_variant` (`:78`) gains the resolved `archetype_id` and applies
Edge's own fallback rule *before* the single draw:

```python
named = [v for v in section.variants if archetype_id in v.archetypes]
pool = named or [v for v in section.variants if not v.archetypes] or section.variants
```

Named variants win; if none name the archetype, the un-tagged variants are used;
if a section is entirely archetype-scoped, nothing is filtered so the pool can
never be empty. This reproduces
`variants.get(archetype_id, variants["default"])` (`port.py:445`), where the
un-tagged variants *are* Edge's `default` grammar.

Note for the import: `trading_port` and `starbase` each carry a `default` entry
**plus all 14 archetypes** (`port.py:177-247`, `:285-354`), so `default` is the
no-archetype/unknown fallback rather than one species' art. Each archetype
grammar has exactly one part per slot, so a known archetype's Edge silhouette is
fully deterministic; only `default` has three parts per slot and hence variety.

### Archetype repeats — varies a tier's *skeleton*

`Section.archetype_repeats` resolves as
`section.archetype_repeats.get(archetype_id, section.repeat)`. A resolved `0`
omits the band for that archetype; a base `repeat: 0` plus a single override
makes a band species-exclusive.

This is orthogonal to `Variant.archetypes` — content versus structure — and both
are needed. Together they give per-archetype length and layout without file
duplication and without forcing every archetype's band to share one dimension.
The port import needs both: Edge's archetype grammars differ in `max_repeat`
(4 for `trading_port` bodies, 5 for `starbase`) as well as in part art.

Rules:

- **The draw still happens for a zeroed section, then is discarded.** Exactly one
  RNG draw per section regardless of resolved repeat, so the `AGENTS.md`
  invariant holds verbatim and — the practical reason — toggling a section
  between 0 and 1 does not reshuffle every other section's variant.
- **`Tier.validate` gains an empty-tier guard:** every archetype in
  `ARCHETYPE_IDS`, plus the no-archetype default, must resolve to at least one
  section with a nonzero repeat. Without it an archetype can be authored into an
  all-blank sprite that does not even error — `_fit_grid` (`render.py:368`)
  handles `nh == 0` by emitting a blank box.
- **This is not a reversion of `e48a030` ("Simplify section repetition model").**
  That commit removed runtime, size-driven `min`/`max` growth. This is an
  authored, archetype-keyed constant that consumes no random draws.

### Section order

`_compose_vertical` (`:264`) stops unconditionally reversing:

```python
ordered = list(zip(tier.sections, chosen, repeats))
if view.section_order == "reversed":
    ordered = list(reversed(ordered))
```

Apply the same conditional in `active_variant_at_cell` (`:218`) and
`rexpaint.segment_rexpaint_cells` (`:215`), which duplicate the walk. Both of
those cursor walks must also use the archetype-resolved repeats.

### Shared seeding helper

`render_sprite` (`:542-547`) and `selected_variants` (`:117-121`) each rebuild
the RNG seed by hand and must stay byte-identical — a live hazard. Extract:

```python
def _seed_rng(sprite: Sprite, seed: int, archetype_id: str | None) -> random.Random:
    key = f"{seed}|{sprite.kind}|{sprite.role}"
    if archetype_id:
        key += f"|{archetype_id}"
    rng = random.Random(key)
    if sprite.kind == "ship":
        rng.choice((0, 1))   # legacy color draws, ships only
        rng.choice((0, 1))
    return rng
```

`_consume_legacy_color_draws` (`:32`) currently burns two draws for *every* kind
despite its ship-scoped docstring. Gating on `kind == "ship"` leaves ship output
byte-identical and gives ports a clean stream.

### Migration

New `tools/migrate_sprites_v3_to_v4.py`, shaped like
`tools/migrate_fixed_repetition.py`: refuse non-v3 input, set
`schema_version: 4`, add `section_order: reversed` to every `axis: vertical`
view. `archetypes` and `archetype_repeats` default empty, so nothing else
changes. Applies to the 12 files in `assets/sprites/ships/`. Rendered output must
be byte-identical across the migration at a pinned tier, so the §1 selection
change cannot mask a `section_order` regression.

---

## 3. Port assets

### Import tool

New `tools/import_edge_ports.py`, modelled on `tools/import_edge_art.py` (which
already does the `sys.path.insert` + `noqa: PLC0415` dance at `:132`). It reads
`edge.art.port.PORT_GRAMMAR` and emits
`assets/sprites/ports/{trading_port,starbase,stardock}.yaml`.

Per subtype:

1. **Mirror once.** Expand every `Part.left` through `port._mirror_row`
   (`port.py:359`) into full-width rows. Symmetry is consumed here and never
   re-derived; the stored art is plain, asymmetric-capable rows.
2. **Merge archetypes into one tier set.** Edge nests
   `subtype -> archetype -> tiers`. Slots are positional, and every
   `trading_port`/`starbase` archetype grammar has the same slot count as its
   `default` tier 0, so slot *i* of every archetype folds into section *i*.
   `default` parts get no `archetypes` list; each archetype's single part gets
   `archetypes: [<that_archetype>]`.
3. **Carry each archetype's repeat.** Where an archetype's slot has a different
   `min_repeat`/`max_repeat` than `default`, record the chosen count in
   `archetype_repeats` rather than flattening it away.
4. **Tiers.** Edge `default` tier 0 → `full`, Edge `default` tier 1 → `compact`.
   Archetype grammars are single-tier and contribute only to `full`; at
   `compact` every archetype falls back to the default silhouette. A third
   `medium` tier is then hand-authored per subtype (see the audit below) so all
   three subtypes carry the same three-tier shape as ships and as the editor's
   new-sprite template.
5. **Constant width per tier.** Mirrored rows are not uniform inside a tier
   (stardock `full` mixes 15 and 13; `trading_port` `compact` mixes 7 and 5).
   Center-pad with spaces to the tier maximum, mask code `S`. Required by
   `Tier.validate` (`:229`) and `Variant.validate` (`:110`).
6. **Uniform height per section — two different rules.** `Section.validate`
   (`:183`) requires every variant in a section to share one height, but
   variants differ (stardock cap: 2/3/4 rows; the `starbase` default body is
   **1** row while every archetype body is **2**).
   - **Non-repeatable sections** (cap and base slots): pad with **blank rows at
     the outward end** — first section pads at the top, last section pads at the
     bottom — so the join with the neighbouring band stays tight.
   - **Repeatable sections** (body slots): pad by **replicating an authored
     row**, never with blanks. `_compose_vertical` (`:280-287`) emits the whole
     variant block once per repeat, so a blank-padded 1-row `starbase` body would
     tile as hull/blank/hull/blank — a ladder instead of a hull.
7. **Marker migration.** Reuse `import_edge_art.LEGACY_MARKERS` (`:29`): `R` →
   `▀` mask `B`, `Y` → `▄` mask `E`, everything else mask `S`. Factor that helper
   into a module shared by both importers rather than copying it.
8. **Repeat.** Baseline `repeat = slot.min_repeat`, with a `--body-repeat`
   override so each tier can be seeded at a legible stacked height rather than
   its minimum. Tuned by the audit below, then hand-refined in the TUI.
9. **View.** One `vertical` view: `axis: vertical`, `canonical_facing: up`,
   `mirror_facing: null`, `section_order: authored`. No horizontal view.
10. **Properties.** Beacon mast → `beacon`, control tower → `tower`, deck/arms →
    `docking`, platform → `platform`, tapering body → `hull`, engine glow →
    `thrusters`.

Sprite ids must not collide with any ship id — `load_sprite_directory`
(`io.py:136`) enforces globally unique ids across the whole tree.

### Tier-height audit (gate before the assets are committed)

With §1 in place this is a one-dimensional problem, but §2 makes stacked height
archetype-dependent, so the audit runs **per archetype**. Add a script (or a
test) that prints each `(tier, archetype)` pair's `composed_length` and the tier
`_select_tier` picks for every requested box:

| Source | Box | Binding height |
|---|---|---|
| `config.py:1479` `port` | 16×6 (min 4×3) | 3 – 6 |
| `config.py:1481` `starbase` | 22×9 (min 4×3) | 3 – 9 |
| `config.py:1480` `stardock` | 38×16 (min 4×3) | 3 – 16 |
| `sprites_gallery.py:85` | 18×8 | 8 |

Plus the intermediate heights `station_dimensions` (`config.py:1499-1514`)
produces. Tune each subtype's `medium` tier, the baseline repeats, and the
per-archetype overrides until every height in those ranges lands on a tier that
fits without cropping, for every archetype. Also confirm the tier's constant
width still reads well at the box width (e.g. a 15-wide stardock centered in 38
columns).

### Known, accepted divergences from Edge

- Edge grows repeatable slots to fill height; `sprite_art` uses authored repeats
  and three discrete tiers, then centers. Same trade ships already made — it is
  why the tier ladder above has to be tuned rather than derived.
- Archetype-specific *art* exists only at the `full` tier; `medium` and
  `compact` fall back to the default silhouette (archetype *repeats* still apply
  at every tier).

Ports are therefore an intentional visual migration, exactly as the four original
ship roles were.

---

## 4. `sprite_art` library facade

`src/sprite_art/library.py` is ship-only and cannot even be constructed from a
tree without a `fighter`.

- Replace `fallback_role: str = "fighter"` (`:23`) with
  `fallback_roles: dict[str, str]`, defaulting to
  `{"ship": "fighter", "port": "trading_port"}` (matching `port.py:444`);
  validate only the entries whose kind is actually present.
- Add `generate_sprite(kind, subtype, seed, width, height, archetype_id=None,
  facing=None)` as the general entry: resolve by `(kind, subtype.lower())`,
  falling back to that kind's fallback role; pick the view by `facing` when
  given, else the sprite's only view.
- Keep `generate_ship(...)` as a thin wrapper (Edge's existing seam, and what the
  integration doc documents) and add `generate_port(subtype, seed, width,
  height, archetype_id=None)`. `facing` is not a port concept.
- Replace `available_roles` (`:39`) with
  `available_subtypes(kind: str | None = None)` filtered on `sprite.kind`, so
  ports never leak into Edge's ship role list. Keep `available_roles` as a
  ship-filtered deprecated alias.
- **Fix the cache.** `@lru_cache` at `:43` decorates the *unbound method*, so the
  cache is shared across every `SpriteLibrary` instance, `clear_cache()` clears
  all of them, and cached instances are never collected. Build a per-instance
  `functools.lru_cache(maxsize=128)` in `__init__`.

---

## 5. Editor (`sprite_art_designer`)

### Supporting a vertical-only, facing-less kind

| File:line | Change |
|---|---|
| `app.py:189` `NewSpriteScreen` | Add `("Station composition", "port")` to the kind Select |
| `app.py:318` `_new_sprite` | Third branch: one `vertical` view, `canonical_facing="up"`, `mirror_facing=None`, `section_order="authored"`, three tiers (`full`/`medium`/`compact`) matching the imported port shape; no `generate_rotated_view` call |
| `state.py:72` | Replace the `"ships" if kind == "ship" else "generic"` ternary with a `KIND_FOLDERS` map (`ship→ships`, `port→ports`, default `generic`) |
| `app.py:442` | Stop defaulting `current_view_id` to the literal `"horizontal"`; use `next(iter(sprite.views))`, matching `on_select_changed:1254` |
| `app.py:417,425` bindings; `widgets.py:366`; help at `app.py:162,168` | Disable `ctrl+g` (rotate_vertical), `o` (toggle_orientation) and the DocumentBar "Generate vertical" item when the sprite has no horizontal source / no alternate view. They are currently always live and merely fail with a notification |
| `widgets.py:627-641`, `app.py:467-473,1369` | Hide `#preview-facing` and its `#view-facing-controls` row when `mirror_facing is None`, instead of a dead one-option Select in a 4-row block |
| `widgets.py:474`, `app.py:815,1558` | Relabel "Ship width (cross-axis cells)" to an axis-aware "Structure width"; surface the tier's `composed_length` beside it, since that is now what selects the tier |

Tier size is now archetype-dependent, so `_set_preview_size_for_tier`
(`app.py:1338`) and the Tier properties readout must resolve against
`current_archetype`, and changing the archetype Select must refresh both.

### New UI: per-archetype variant scope and repeats

Both new controls live on `PropertiesToolsTab` (`widgets.py:458`) and both are
scoped to the **currently previewed archetype**, which is the ambient context the
author already works in — a full 14-row matrix per section would swamp the panel.

- `#variant-fields`: an archetype allow-list — a `SelectionList` over
  `ARCHETYPE_IDS`, empty meaning "any".
- `#section-fields`: alongside the existing baseline repeat Input, a "repeat for
  *current archetype*" control that writes `archetype_repeats[current_archetype]`
  or clears it back to the baseline, plus a one-line read-only summary of any
  other overrides on that section.

Both route through the normal `_mark_changed` / history path.

A persistent variant override (`app.py:1399 _preview_variant_overrides`, keyed by
`id(section.variants)`) may point at a variant the current archetype filters out.
`_choose_variant` must ignore an override outside the filtered pool.

### CLI gallery

`render_ships.py:88` hard-filters `sprite.kind == "ship"` and raises `"no ship
sprites were found"`. Add a `--kind` flag (default `ship`), generalize the error
text, and add an `edge-art-render-sprites` console script alongside
`edge-art-render-ships` (`pyproject.toml:10-12,38-44`).

### Pre-existing bug that vertical-only art makes the default path

`preview_size` is stored *pre*-aspect-correction; `PreviewMatrix.
dimensions_for_view` (`widgets.py:736`) maps a vertical pair `(a, b)` to
`(b*2, (a+1)//2)`, which `_set_preview_size_for_tier` (`app.py:1348`) matches by
storing `(stacked_height*2, width)`. That pairing is self-consistent — but
`action_export_rexpaint` (`app.py:1675`) and `_finish_import_rexpaint`
(`app.py:1718`) pass `self.preview_size` **raw**, bypassing the helper. For
horizontal views that is the identity, so it is invisible today; for vertical
views it transposes the box. Route both REXPaint paths through
`dimensions_for_view` and cover the vertical case —
`test_rexpaint_export_uses_current_preview_configuration`
(`tests/test_tui.py:546`) only exercises horizontal.

---

## 6. Documentation

### `docs/EDGE_INTEGRATION.md` — ports

- Vendoring unchanged; `assets/sprites/ports/` copies with the rest of the tree.
- Call seam:
  ```python
  text = SPRITES.generate_port(
      subtype="stardock",          # trading_port | starbase | stardock
      seed=sector_id,
      width=width, height=height,
      archetype_id=owner.archetype_id,
  )
  ```
- Migration in `edge/art/generator.py`: the `entity_type == "port"` branch
  (`:107`) routes to `SPRITES.generate_port(...)`; `available_subtypes("port")`
  (`:37`) returns `list(SPRITES.available_subtypes("port"))`.
- **Where Edge chooses the subtype** — the other half of the seam:
  `edge/tui/art_adapter.py:99 port_subtype()` (returns `stardock` /
  `trading_port`) and `art_adapter.py:78` (`"starbase": ("port", "starbase")`),
  driven by `PortClass` (`edge/bigbang/populate.py:125`). These strings must
  continue to equal the vendored sprites' `role` values.
- **Seed contract.** Edge seeds `f"{seed}|{entity_type}|{subtype}"` + archetype
  (`generator.py:88-92`); `sprite_art` seeds `f"{seed}|{kind}|{role}"` +
  archetype. They match only while port documents carry `kind: port` and a
  `role` equal to Edge's subtype string. State this as a hard vendoring
  requirement for both kinds.
- **Tier selection maps 1:1 onto Edge's.** `hull.select_grammar` +
  `_tier_height` (ships) and `_grammar_floor` (ports) both budget on height;
  `sprite_art._select_tier` now does the same, with `cross_axis_size` as the
  horizontal floor and `composed_length` as the vertical floor. Document this so
  the seam is checkable rather than assumed.
- **Archetype now affects geometry, not only palette** — `Variant.archetypes` and
  `Section.archetype_repeats` — so `archetype_id` must be passed for stations,
  not treated as a styling nicety.
- Ports ignore `facing` and expose only a `vertical` view.
- Unknown port subtype falls back to `trading_port`, matching `port.py:444`.
- The two legacy color draws are now ship-only; port streams are clean.
- `edge/art/port.py` can be retired, but **`edge/art/hull.py` cannot**:
  `edge/art/discovery.py:15` still imports it, `generator.py:7` imports
  `ARCHETYPE_STYLES` for `available_archetypes()` (`:47`), and
  `tests/test_ship_art.py:16` imports `GLYPH_FLIP`, `compose_horizontal`,
  `flip_row`. Note that `available_archetypes()` should switch to the vendored
  palette catalog once both kinds have migrated.
- Divergences from Edge port rendering, per §3.

### `docs/EDGE_INTEGRATION.md` — gaps in the existing ship seam

1. The seed contract above. The doc currently states `seed | ship | role |
   archetype_id` without saying that `ship` is `Sprite.kind` and `role` is
   `Sprite.role`, or that both must equal Edge's `entity_type` / `subtype`.
2. `available_roles` returns sprite **ids**, and `generate_ship` looks them up by
   id, while `Sprite.role` is a separate field that feeds the seed. They coincide
   in all shipped assets but the schema permits divergence.
3. Cache semantics after the §4 fix: per-instance, `maxsize=128`, keyed including
   `facing` even though `facing` is not in the seed, `clear_cache()` now
   instance-scoped.
4. Double-caching guidance for Edge's outer `generate_sprite` `@lru_cache`
   (`generator.py:57`) now that two kinds share the library cache.
5. That the two legacy color draws apply to `kind: ship` only.
6. That `assets/` must exist at runtime beside the vendored package, and that
   `sprite_art_authoring.rexpaint` is editor support with no game-side dependency and is not vendored into Edge.
7. That ship *horizontal* selection is unchanged by §1, while ship `up`/`down`
   views — a `sprite_art` extension Edge does not currently request — may pick a
   different tier.

### `docs/SPRITE_ART_FORMAT.md`

- `schema_version: 4`; asset tree gains `sprites/ports/`.
- Rewrite "Tiers, ship width, and repetition" (`:77-91`). Its current selection
  sentence is both wrong and self-contradictory ("A horizontal view selects by
  available ship width; a vertical view selects by available ship width").
  Replace with: every view selects on requested **height** — a horizontal view
  against the tier's constant structure height, a vertical view against the
  tier's stacked height — and rename "ship width" to kind-neutral "structure
  width".
- Document `composed_length`, its archetype dependence, and the
  axis-appropriate richest-first ordering constraint holding per archetype.
- New `Variant.archetypes` (band content) and `Section.archetype_repeats` (tier
  skeleton): the "named wins, else un-tagged, else all" rule, `0` omitting a
  band, the empty-tier guard, and that the draw still happens for a zeroed
  section so selection remains one draw per section.
- Record explicitly that both fields are **kind-agnostic**: ships may use them
  for per-archetype art, subject to the structural limits (a section's variants
  share one `(width, height)`; a tier's variants share one cross-axis size;
  horizontal and vertical are independent stored art, so tags are authored
  twice).
- New `View.section_order` field, default, and vertical-only constraint.
- Extended property vocabulary (`docking`, `beacon`, `platform`, `tower`).
- Drop the stale `generic/future_icon.yaml` example now that `ports/` is a real
  second kind.

### `AGENTS.md`

- Add ports/starbases/stardock to "What this project is".
- Replace the stale "Repetition starts at `min`, never exceeds `max`" invariant
  (superseded by `e48a030`) with: repeat is an authored count, optionally
  overridden per archetype, `0` omits the band, and it consumes no random draws.
- New invariants: stations are vertical-only with no mirror facing; symmetry is
  never assumed in `sprite_art`; tier selection always budgets on requested
  height; archetype filtering and archetype repeats never change the
  one-draw-per-section count.
- Update the controlled property vocabulary block and the asset-tree description.

### `docs/PORT_DESIGN_PRINCIPLES.md` (new)

Short companion to `SHIP_DESIGN_PRINCIPALS.md` carrying over the reasoning in
`port.py`'s module docstring (`:1-49`): stations stay iconic at very small sizes,
silhouettes are hand-authored rather than traced, vertical band stacking, the
beacon/glow language, and the TradeWars 2002 Federation Stardock heritage of the
flagship silhouette.

---

## 7. Tests

`tests/test_sprite_art.py`

- Roster assertions (`:42-57`, `:151`, `:457`, `:477`) become kind-filtered;
  `load_sprite_directory` `rglob`s (`io.py:134`), so the new `ports/` files load
  automatically and would otherwise break these immediately.
- Tier selection: a vertical view selects on stacked height, not width — pin this
  with a case where the two rules disagree; horizontal selection is byte-identical
  to today; the smallest tier is still the final fallback.
- Tier ordering validation rejects a vertical view whose stacked heights are not
  non-increasing, **for any archetype**.
- Schema v4 round-trips `archetypes`, `archetype_repeats` and `section_order`
  through `dump_sprite` / `load_sprite`; validation rejects an unknown archetype
  id in either field, a negative repeat, and `section_order: reversed` on a
  non-vertical view.
- Archetype filtering: an archetype with named variants gets only those; an
  archetype with none gets the un-tagged pool; the RNG draw count is unchanged
  either way.
- Archetype repeats: an override changes the composed length and can change the
  selected tier; `0` omits the band; a base `0` plus one override makes a band
  species-exclusive; the empty-tier guard rejects an archetype with no surviving
  section; **toggling a section between 0 and 1 leaves every other section's
  chosen variant unchanged** (the draw-then-discard rule).
- **Migration regression:** every ship role renders byte-identically
  (`Text.plain` and style spans) across the v3→v4 migration, at a pinned tier so
  the §1 change cannot mask a `section_order` regression.
- Port assets, parametrized over the three subtypes × archetypes: exact
  requested width and height; constant width within each tier; determinism for a
  fixed seed; archetype-stable silhouettes; **no vertical crop at any height in
  the ranges listed in §3**; a repeatable body section tiles without blank bands.
- Ports consume no legacy color draws; ships still do.

`tests/test_tui.py`

- Update `len(app.editor.sprites) == 12` (`:38`).
- Pilot: create a port via `NewSpriteScreen`; the facing Select and "Generate
  vertical" action are absent and `ctrl+g` / `o` are inert.
- Pilot: edit a variant's archetype allow-list, and set a per-archetype repeat to
  0, confirming the preview follows the archetype Select in both cases.
- REXPaint export/import round-trip on a **vertical** view, covering the
  `dimensions_for_view` fix.

`tests/test_render_ships.py` — cover `--kind port`.

---

## 8. Verification

```bash
pixi run check                     # ruff + mypy --strict on src/ + pytest
pixi run app                       # author/inspect a port in the TUI
pixi run render-ships --kind port
python tools/import_edge_ports.py --audit    # per-archetype tier-height table, §3
```

Manual checks in the TUI:

1. Open `stardock`: a single Vertical view, no facing control, `o` and `ctrl+g`
   inert.
2. Cycle the archetype Select on `trading_port` and `starbase`: the silhouette
   changes and is stable for a fixed seed.
3. Set a section's repeat to 0 for one archetype: that band disappears for that
   archetype only, the tier size readout updates, and the other sections keep
   their variants.
4. Sweep the preview height across every tier boundary: the requested rectangle
   is filled exactly, and beacon and glow survive at `16×6`, `18×8`, `22×9`,
   `38×16`.
5. Export and re-import a vertical REXPaint round-trip.

Cross-repo sanity (read-only, in `/home/mcduffie/Devel/edge-of-the-unknown`):
render the same `(subtype, seed, archetype, width, height)` tuples through
`edge.art.generator.generate_sprite("port", ...)` and through the new library,
side by side. Output is *not* expected to match — this confirms the migration is
a deliberate visual change rather than an accidental one, and produces the
before/after evidence for the Edge-side change alongside the ship vertical
tier-selection matrix from §1.

---

## Files touched

**Library:** `src/sprite_art/model.py`, `io.py`, `render.py`, `library.py`

**Authoring:** `src/sprite_art_authoring/rexpaint.py`

**Editor:** `src/sprite_art_designer/app.py`, `widgets.py`, `state.py`,
`render_ships.py`, `styles.tcss`

**Tools:** new `tools/import_edge_ports.py`, new
`tools/migrate_sprites_v3_to_v4.py`, shared marker helper factored out of
`tools/import_edge_art.py`

**Assets:** new `assets/sprites/ports/*.yaml`; `assets/sprites/ships/*.yaml`
migrated to v4

**Docs:** `docs/EDGE_INTEGRATION.md`, `docs/SPRITE_ART_FORMAT.md`, `AGENTS.md`,
new `docs/PORT_DESIGN_PRINCIPLES.md`

**Build:** `pyproject.toml` (new console script + pixi task)

**Tests:** `tests/test_sprite_art.py`, `tests/test_tui.py`,
`tests/test_render_ships.py`

---

## What changed during implementation

Six things came out differently once the code was written. Each is reflected in
the authoritative docs; this list exists so the plan above is not mistaken for a
description of what shipped.

**Tier ordering is strict, not merely non-increasing.** §1 asked for
non-increasing tier sizes. Two tiers of equal size make the later one
unreachable, so `View.validate` requires each tier to be *strictly* smaller than
the last. That exposed one real asset defect: `junction_pinnace`'s vertical
`medium` and `compact` tiers both stacked to 11 rows, making Compact
unselectable. Its vertical compact body repeat dropped from 4 to 3, matching the
other eleven ships.

**Stations have four tiers, cut mechanically rather than hand-authored.** §3
planned two imported tiers plus a hand-authored `medium`. The importer instead
produces `full`, `medium`, `compact`, and `minimal` from Edge's two grammars,
with `medium` cut from the rich grammar by keeping only each slot's shortest
parts (`short_parts_only`). Uniform section heights inflate the rich grammars
past the boxes Edge requests — `trading_port` floors at 10 rows, `starbase` at
12 — so without that grouping the per-archetype art would never be reachable at
a station's real size. `minimal` exists because `SpriteSize.min_height` lets
Edge ask for a 3-row station. With all four rungs, no station crops at any box
the game requests.

**Stations need their own marker table.** §3 step 7 planned to reuse
`import_edge_art.LEGACY_MARKERS`, which maps `Y` to `▀`. That table
intentionally departs from Edge's painter, pairing each marker's upper- and
lower-half form by letter case so ship art can pick whichever half reads best.
Stations want the painter's own mapping: a station's glow sits on its bottom
row, where a lower-half `▄` is flush with the foot of the silhouette and an
upper-half `▀` leaves a gap beneath the drive. `HULL_MARKERS` carries that;
`LEGACY_MARKERS` is unchanged.

**The new-sprite station template has three tiers, not four.** A blank template
does not need the `minimal` rung; authors add one if their station needs it.

**One more raw-`preview_size` site than §5 found.** The plan named
`action_export_rexpaint` and `_finish_import_rexpaint`. `_preview_variants` had
the same bug, which matters more now that tier selection depends on height. All
three route through a new `_preview_dimensions` helper.

**The migration regression test is a committed fixture.** §7 described comparing
renders across the migration. What shipped is
`tests/fixtures/tier_renders.json`, pinning the composed output of all 84
authored tiers at their natural boxes — a guard that outlives the migration
itself. The one-off before/after comparison is recorded in
`docs/tier-selection-change.md`.

### Verification, as actually run

```bash
pixi run check
pixi run render-ships -- --kind port --sprite-id stardock
python tools/import_edge_ports.py /path/to/edge-of-the-unknown --audit
```

Note the `--audit` invocation needs the Edge checkout path; §8 omitted it.
