# Edge of the Unknown Integration

`src/sprite_art/` is intentionally independent of Textual. It uses only Rich and
PyYAML, both already present in Edge of the Unknown. The editor package does not
need to be vendored into the game.

The editor-only color-well modal uses `textual-colorpicker`; it is not a
dependency of `sprite_art` and is therefore not part of the game vendoring seam.

## Vendoring

Copy:

```text
src/sprite_art/              -> edge/art/sprite_art/
assets/palettes.yaml         -> edge/art/assets/palettes.yaml
assets/sprites/              -> edge/art/assets/sprites/
```

Then adjust relative imports if the package is nested as `edge.art.sprite_art`.
Alternatively, copy `sprite_art` as a top-level package unchanged.

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
```

`generate_ship` returns `rich.text.Text`, falls back to `fighter` for an unknown
role, omits facing from the deterministic seed, and caches 128 exact requests.
Its arguments match Edge's current `ShipGenerator` seam while extending facing
to `up` and `down`.

## Migration from the current generator

In `edge/art/generator.py`:

1. Replace the module-level `ShipGenerator` with one loaded `SpriteLibrary`.
2. Return `list(SPRITES.available_roles)` for ship subtypes.
3. Route the existing ship branch to `SPRITES.generate_ship(...)`.
4. Keep the outer `generate_sprite` cache or rely on the library cache, but not
   both unless the additional layer is useful for non-ship art.

The four converted horizontal roles preserve the original grammar and seeded
variant choices. Schema-v2 color masks intentionally replace marker glyphs and
random window placement:

- `fighter`
- `transport`
- `warship`
- `capital_warship`

The asset library adds these gameplay roles:

- `needle_picket`
- `falsehold_raider`
- `junction_pinnace`
- `radiant_lance`
- `hearth_freighter`
- `pearl_shell`
- `marrow_dart`
- `broadside_citadel`

Edge's ship-class configuration and its role-coverage tests must add these roles
when the assets are vendored. That configuration change belongs in the game
repository, not this editor repository.

## Determinism and compatibility

For ships, the renderer seeds its local RNG as:

```text
seed | ship | role | archetype_id
```

It consumes the two historical color-selection draws before choosing one
variant per section, keeping converted geometry stable. Equal variant weights
use `random.Random.choice`, and repeats consume no additional draws. Palette
colors no longer consume RNG, and windows appear only where the authored
color mask selects Window. Rich style spans therefore follow the new six-set
palette contract rather than Edge's random-window painter.

Vertical art is new. `up` uses the stored canonical vertical view; `down` is its
glyph-aware reflection.
