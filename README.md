# Edge Art Designer

`edge-art-designer` is a resizable Textual application for authoring procedural
Unicode sprite art. Ships are its first compositional asset type, while a simple
fixed-canvas mode keeps the underlying `sprite_art` format and library useful for
future art.

The project follows the constraints in `SHIP_DESIGN_PRINCIPALS.md`:

- hand-authored rectangular pieces assembled procedurally;
- semantic detail tiers instead of blind scaling;
- seeded, size-stable variant selection;
- editable archetype palettes separated from geometry;
- independently stored horizontal and vertical views;
- glyph-aware reflection for four travel directions.
- native REXPaint `.xp` export and fixed-canvas import with a matching bundled art-font sheet.

## Run

```bash
pixi run app
```

The reusable package is `sprite_art`. The Textual application lives in
`sprite_art_designer`; Edge of the Unknown can vendor only `sprite_art` and the
YAML assets without taking an editor dependency.

## Data

```text
assets/
├── palettes.yaml
└── sprites/
    └── ships/
        ├── fighter.yaml
        ├── transport.yaml
        └── ...
```

Each sprite and the palette catalog carries its own `schema_version`. Ship roles
are file-backed sprite IDs. Geometry files reference no palette, so any controlled
archetype palette can be applied at render time.

See `docs/SPRITE_ART_FORMAT.md` and `docs/EDGE_INTEGRATION.md` for the format and
the vendoring seam.

## REXPaint interchange

Use **Export RexPaint** or `Ctrl+E` to write the current preview to
`~/.edge-art-designer/exports/`. Crash-recovery snapshots are likewise stored
under `~/.edge-art-designer/recovery/`. Install
`assets/rexpaint/edge-art-designer.png` as a 16-column REXPaint art font; its
slot order is documented in `assets/rexpaint/edge-art-designer-map.md`.

Use the **Actions** dropdown or `Ctrl+I` to bring a one-layer `.xp` file using
that font map back into the current preview. Import assumes that the image was
just exported with the same preview size, seed, view, facing, and active
variants; it segments the image into those active editable variants. All copies
of a repeated section must match.

## License

Licensed under the GNU Affero General Public License v3.0 or later. See
`LICENSE` for the full text.
