# Edge of the Unknown Integration

`src/sprite_art/` is intentionally independent of Textual. It uses only Rich and
PyYAML, both already present in Edge of the Unknown. The editor package does not
need to be vendored into the game.

The editor-only color-well modal uses `textual-colorpicker`; it is not a
dependency of `sprite_art` and is therefore not part of the game vendoring seam.
`sprite_art.rexpaint` is editor support with no game-side dependency, but it is
imported by the package facade and so travels with it.

## Vendoring

Copy:

```text
src/sprite_art/              -> edge/art/sprite_art/
assets/palettes.yaml         -> edge/art/assets/palettes.yaml
assets/sprites/              -> edge/art/assets/sprites/
```

Then adjust relative imports if the package is nested as `edge.art.sprite_art`.
Alternatively, copy `sprite_art` as a top-level package unchanged. The `assets`
tree must exist at runtime beside the vendored package; the library reads it,
it is not embedded.

The loaded facade is:

```python
from pathlib import Path

from sprite_art import SpriteLibrary

SPRITES = SpriteLibrary.from_assets(
    Path(__file__).with_name("assets")
)

text = SPRITES.generate_ship(
    subtype="warship",
    seed=entity_seed,
    width=40,
    height=7,
    archetype_id=owner.archetype_id,
    facing="right",  # left, right, up, or down
)

text = SPRITES.generate_port(
    subtype="stardock",   # trading_port | starbase | stardock
    seed=sector_id,
    width=38,
    height=16,
    archetype_id=owner.archetype_id,
)
```

Both are thin wrappers over `generate_sprite(kind, subtype, ...)`. Each returns
`rich.text.Text`, falls back to its kind's default subtype for an unknown one,
omits facing from the deterministic seed, and shares one per-instance cache of
128 exact requests.

## The seed contract

This is the load-bearing part of the seam. Edge seeds its local RNG as:

```python
rng_seed = f"{seed}|{entity_type}|{subtype}"
if archetype_id:
    rng_seed += f"|{archetype_id}"
```

`sprite_art` seeds as:

```python
rng_seed = f"{seed}|{sprite.kind}|{sprite.role}"
if archetype_id:
    rng_seed += f"|{archetype_id}"
```

The two match **only** while each sprite document's `kind` equals Edge's
`entity_type` and its `role` equals Edge's `subtype`. Ships therefore carry
`kind: ship`, and all three stations carry `kind: port` — the stardock is a
special kind of starbase in the fiction, but at this seam it is a `port` whose
`role` is `stardock`, exactly as `PORT_SUBTYPES` already has it. Renaming either
field silently changes every sprite in the game.

One wrinkle to know about: `available_subtypes()` returns sprite **ids**, and
`generate_sprite` resolves by id, while `Sprite.role` is a separate field that
feeds the seed. They coincide in every shipped asset, but the schema permits
them to diverge.

For ships only, the renderer consumes two historical color-selection draws
before choosing variants, preserving the draw discipline the converted grammars
were authored against. Station streams are clean.

## Tier selection

`sprite_art._select_tier` maps one-to-one onto Edge's `hull.select_grammar`:
both budget on the **requested height**, and only the floor differs by axis.

| | Edge | `sprite_art` |
|---|---|---|
| horizontal (ships) | `ship._tier_height` — the tier's authored row height | `Tier.cross_axis_size` |
| vertical (ports) | `port._grammar_floor` — the minimum stacked height | `Tier.composed_length` |

A vertical view's width is not consulted; the tier fixes one structure width and
the painter centers or crops it, as `hull.render_grid` does.

## Migration from the current generator

In `edge/art/generator.py`:

1. Replace the module-level `ShipGenerator` and `PortGenerator` with one loaded
   `SpriteLibrary`.
2. Return `list(SPRITES.available_subtypes("ship"))` and
   `list(SPRITES.available_subtypes("port"))` from `available_subtypes`.
3. Route the `entity_type == "ship"` branch to `SPRITES.generate_ship(...)` and
   the `entity_type == "port"` branch to `SPRITES.generate_port(...)`.
4. Keep the outer `generate_sprite` cache or rely on the library cache, but not
   both unless the additional layer is useful for the art types that have not
   migrated.

The other half of the port seam is where Edge decides *which* subtype to ask
for: `edge/tui/art_adapter.py` `port_subtype()` returns `stardock` or
`trading_port`, and its `"starbase": ("port", "starbase")` entry covers the
third, all driven by `PortClass` in `edge/bigbang/populate.py`. Those strings
must keep matching the vendored sprites' `role` values.

`edge/art/port.py` can be retired once ports are vendored, but **`edge/art/hull.py`
cannot**: `edge/art/discovery.py` still imports it, `generator.py` imports
`ARCHETYPE_STYLES` for `available_archetypes()`, and `tests/test_ship_art.py`
imports `GLYPH_FLIP`, `compose_horizontal`, and `flip_row`. Once both ships and
ports have migrated, `available_archetypes()` should read the vendored palette
catalog instead of `ARCHETYPE_STYLES`.

## Roles and subtypes

The four original gameplay role names remain available, but their schema-v4
assets are now native Edge Art Designer compositions rather than byte-for-byte
translations of the old in-code grammar. Vendoring these files is therefore an
intentional visual migration for:

- `fighter`
- `transport`
- `warship`
- `capital_warship`

The asset library also provides these gameplay roles:

- `needle_picket`
- `falsehold_raider`
- `junction_pinnace`
- `radiant_lance`
- `hearth_freighter`
- `pearl_shell`
- `marrow_dart`
- `broadside_citadel`

and these stations:

- `trading_port`
- `starbase`
- `stardock`

Edge's ship-class configuration and its role-coverage tests must add the new
ship roles when the assets are vendored. That configuration change belongs in
the game repository, not this editor repository.

## Stations

Stations differ from ships in three ways that callers can see:

- **One orientation.** A station has only a `vertical` view and declares no
  `mirror_facing`, so `generate_port` takes no `facing` argument and ignores the
  concept entirely.
- **No symmetry.** Edge authors a port as its left half and mirrors it at render
  time. Sprite documents store plain, full-width rows; mirroring happened once,
  during import, and is not a runtime concept. Station art can therefore be
  asymmetric.
- **Archetype changes geometry, not just palette.** `Variant.archetypes` and
  `Section.archetype_repeats` carry Edge's per-archetype port grammars, so
  `archetype_id` must be passed for stations rather than treated as a styling
  nicety. Omitting it renders the `default` silhouette.

### Divergences from Edge's port rendering

Station art is an intentional visual migration, as the original ship roles were.
Two differences are structural rather than artistic:

- **Growth became tiers.** Edge tiles a repeatable slot to fill the requested
  height exactly. Sprite documents use authored repeats and a discrete tier
  ladder, then center the result. A station therefore fills its box in steps
  rather than continuously. Where Edge's rich grammar happens to land on a
  requested height, output is glyph-identical — a `starbase` at 22x9 matches
  Edge exactly for every archetype.
- **Uniform section heights.** Edge composes freely from parts of differing
  heights, choosing a squat three-row cap or a tall five-row one. The schema
  requires every variant in a section to share one rectangle, so the imported
  tiers group parts by height instead. `trading_port` at 16x6 consequently
  renders the small-box silhouette where Edge renders the archetype one; that
  tier is a hand-refinement target, not a rendering bug.

`tools/import_edge_ports.py <edge-checkout> --audit` prints the tier ladder against the boxes
`SceneArtConfig` actually requests, and the test suite asserts that no station
crops at any of them.

## Determinism and compatibility

For ships, the renderer seeds as described above and consumes the two historical
color-selection draws before choosing one variant per section. This preserves
the renderer's established draw discipline, but the redesigned assets are not
expected to reproduce the former Edge glyphs or style spans. Equal variant
weights use `random.Random.choice`, and repeats are fixed authored counts that
consume no additional draws. Palette colors do not consume RNG, and windows
appear only where the authored color mask selects Window. Rich style spans
therefore follow the six-set palette contract rather than Edge's random-window
painter.

Archetype filtering and per-archetype repeats do not change the draw count: one
decision per section, always.

Vertical ship art is new. `up` uses the stored canonical vertical view; `down`
is its glyph-aware reflection. Edge does not currently request either — it
passes only `right` and `left` for ships — so the height-budgeted tier selection
described above changes which tier those views pick without affecting any
horizontal ship render.

## Caching

`SpriteLibrary` holds one `functools.lru_cache(maxsize=128)` per instance,
created in `__init__`. `clear_cache()` clears that instance only. The cache key
includes `facing` even though `facing` is not part of the RNG seed, so the two
mirrored renders of one composition are cached separately.
