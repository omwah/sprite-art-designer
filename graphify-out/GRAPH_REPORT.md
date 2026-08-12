# Graph Report - sprite-art-designer  (2026-08-12)

## Corpus Check
- 39 files · ~81,274 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 902 nodes · 2197 edges · 64 communities (58 shown, 6 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 207 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a72bbfc0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_sprite_art.py
- EditorState
- ConfirmScreen
- EdgeArtDesigner
- Tier
- .on_button_pressed
- ._refresh_preview
- render.py
- .__init__
- import_edge_ports.py
- render_ships.py
- GroupedSpriteSelect
- rexpaint.py
- ArtCanvas
- sprite_art/__init__.py
- Button
- Selection
- generate_rexpaint_font.py
- test_render_ships.py
- PaletteColorScreen
- SpriteLibrary
- app.py
- PreviewMatrix
- Sprite
- WorkspaceSplitter
- .on_select_changed
- rexpaint_bytes
- migrate_color_masks.py
- Ports, Starbases, and Stardock in Edge Art Designer
- migrate_sprite
- migrate_sprite
- load_palette_catalog
- edge-art-designer
- PaletteCatalog
- Procedural ANSI/Unicode Spaceship Art in *Edge of the Unknown*
- export_rexpaint
- AGENTS.md — Edge Art Designer
- Sprite Art Format
- Edge of the Unknown Integration
- selected_tier
- .__init__
- Port Design Principles
- Fighter
- Transport
- Warship
- Capital Warship
- Needle Picket
- Falsehold Raider
- Junction Pinnace
- Radiant Lance
- Hearth Freighter
- Pearl Shell
- Marrow Dart
- Broadside Citadel
- Edge Art Designer
- Ship Type Design Principles and Media Touchstones
- PaletteColorGroup
- Tier selection: before and after height budgeting
- ._apply_responsive_panels
- test_section_order_decides_which_authored_band_lands_on_top
- Edge Art Designer REXPaint font map

## God Nodes (most connected - your core abstractions)
1. `EdgeArtDesigner` - 149 edges
2. `PaletteCatalog` - 57 edges
3. `load_sprite()` - 55 edges
4. `Sprite` - 55 edges
5. `Variant` - 42 edges
6. `Tier` - 40 edges
7. `ArtCanvas` - 31 edges
8. `render_sprite()` - 30 edges
9. `EditorState` - 25 edges
10. `Section` - 22 edges

## Surprising Connections (you probably didn't know these)
- `refresh_ship()` --calls--> `load_sprite()`  [INFERRED]
  tools/refresh_medium_tiers.py → src/sprite_art/io.py
- `main()` --calls--> `dump_sprite()`  [INFERRED]
  tools/generate_original_ships.py → src/sprite_art/io.py
- `main()` --calls--> `dump_sprite()`  [INFERRED]
  tools/import_edge_art.py → src/sprite_art/io.py
- `main()` --calls--> `dump_sprite()`  [INFERRED]
  tools/import_edge_ports.py → src/sprite_art/io.py
- `refresh_ship()` --calls--> `dump_sprite()`  [INFERRED]
  tools/refresh_medium_tiers.py → src/sprite_art/io.py

## Import Cycles
- None detected.

## Communities (64 total, 6 thin omitted)

### Community 0 - "test_sprite_art.py"
Cohesion: 0.10
Nodes (33): parametrize, load_sprite(), A zero baseline plus one override makes a band that species alone has., The variant draw still happens for a zeroed section, then is discarded. Without…, A zero repeat omits one band; only emptying a whole tier is an error., Two tiers of equal size make the later one unreachable., A repeating band padded with void would tile as hull/void/hull/void., Edge's ``variants.get(archetype_id, variants["default"])`` rule. Variants… (+25 more)

### Community 1 - "EditorState"
Cohesion: 0.26
Nodes (3): EditorState, Path, dump_sprite()

### Community 2 - "ConfirmScreen"
Cohesion: 0.10
Nodes (20): ConfirmScreen, HelpScreen, NewSpriteScreen, PaletteColorResult, Scroll-friendly editor help, adapted from Edge's contextual help screen., Request a native REXPaint file to split into active source variants., A color-picker change, including an explicit removal request., RexPaintImportScreen (+12 more)

### Community 3 - "EdgeArtDesigner"
Cohesion: 0.11
Nodes (47): asyncio, EdgeArtDesigner, Path, A vertical-only kind has one view and one facing, so both are inert., The override is scoped to the archetype currently being previewed., Shrinking a tier onto the next one would make that next one unreachable., test_a_repeat_override_that_collapses_the_tier_ladder_is_rejected(), test_app_mounts_wide_and_populates_editor() (+39 more)

### Community 4 - "Tier"
Cohesion: 0.06
Nodes (48): Axis, _int_mapping(), _mapping(), Any, YAML I/O for the sprite-art schema., _section_from_data(), _section_to_data(), sprite_to_data() (+40 more)

### Community 5 - ".on_button_pressed"
Cohesion: 0.15
Nodes (4): Any, The box the preview actually renders into. ``preview_size`` is stored before…, _unique_id(), TreeNode

### Community 7 - "render.py"
Cohesion: 0.22
Nodes (18): Random, _add_preview_margin(), _choose_variant(), compose_grid(), _compose_grid_with_highlight(), _compose_horizontal(), _compose_vertical(), _fit_grid() (+10 more)

### Community 8 - ".__init__"
Cohesion: 0.15
Nodes (9): GlyphToolsTab, PaletteToolsTab, PreviewToolsTab, PropertiesToolsTab, Structure selection metadata tab., Controlled archetype palette tab., Preview view, random seed, and size controls tab., TabPane (+1 more)

### Community 9 - "import_edge_ports.py"
Cohesion: 0.13
Nodes (22): migrate_rows(), The legacy glyph markers shared by the Edge art importers. Edge's in-code…, Split marker-bearing rows into parallel glyph and color-mask grids., main(), Any, Translate Edge of the Unknown's in-code ship grammars into sprite-art YAML.…, _sprite(), _tier() (+14 more)

### Community 10 - "render_ships.py"
Cohesion: 0.15
Nodes (21): ArgumentParser, _deduplicate(), _default_console(), _gallery_view(), GallerySelectionError, main(), _parser(), Console (+13 more)

### Community 11 - "GroupedSpriteSelect"
Cohesion: 0.15
Nodes (11): RenderableType, SpriteOptionGroups, SpriteSelectValue, GroupedSpriteSelect, Text, An internal, disabled Select value used to label an option group., An internal, disabled Select value that spaces option groups., A Select whose disabled options serve as visible group headers. (+3 more)

### Community 12 - "rexpaint.py"
Cohesion: 0.12
Nodes (22): RGB, _SectionData, flip_rows_horizontal(), flip_rows_vertical(), Closed structural glyph alphabet and geometric transforms., transform_glyph(), ordered_sections(), Order one vertical view's per-section data as it stacks on screen. Ship… (+14 more)

### Community 13 - "ArtCanvas"
Cohesion: 0.13
Nodes (8): Key, MouseEvent, MouseMove, Size, ArtCanvas, Changed, GlyphPicked, A one-terminal-cell painting surface with drag painting and erasing.

### Community 14 - "sprite_art/__init__.py"
Cohesion: 0.15
Nodes (15): Focused editor widgets: mouse canvas, glyph picker, and live previews., Reusable procedural Unicode sprite-art reader and renderer., ColorSet, Palette, Versioned in-memory model for generic and compositional sprite art., Return one glyph-shading slot, falling back to the full-block color., Section, glyph_color_slot() (+7 more)

### Community 15 - "Button"
Cohesion: 0.26
Nodes (5): Button, Horizontal, ComposeResult, ComposeResult, Vertical

### Community 16 - "Selection"
Cohesion: 0.13
Nodes (3): NodeSelected, Return this sprite's declared geometry archetypes in catalog order., Selection

### Community 17 - "generate_rexpaint_font.py"
Cohesion: 0.27
Nodes (17): build(), _composite_cell(), _cp437_slots(), _diagonal_cell(), _fallback_cell(), _font_cell(), main(), Path (+9 more)

### Community 18 - "test_render_ships.py"
Cohesion: 0.18
Nodes (14): CaptureFixture, MonkeyPatch, Textual editor for the reusable :mod:`sprite_art` package., StringIO, _console_output(), Console, Path, test_cli_defaults_to_every_tier_for_a_selected_ship() (+6 more)

### Community 19 - "PaletteColorScreen"
Cohesion: 0.18
Nodes (10): ItemGrid, PaletteColorScreen, Choose one palette color with the packaged Textual color picker., ColorSetSelector, GlyphPalette, PaletteColorSwatch, Pressed, Named color-mask selectors kept separate from authored glyphs. (+2 more)

### Community 20 - "SpriteLibrary"
Cohesion: 0.17
Nodes (8): Text, Render one cached sprite, matching Edge's generator arguments. ``kind`` and…, Edge-compatible ship renderer, extended to left/right/up/down., Edge-compatible station renderer for ports, starbases, and stardocks. Stations…, Load an asset tree once and render cached sprites by kind and subtype., Return the loaded sprite ids, optionally limited to one kind. Edge enumerates…, Deprecated alias for the ship subtypes., SpriteLibrary

### Community 21 - "app.py"
Cohesion: 0.17
Nodes (18): _blank_variant(), _default_section(), main(), _new_sprite(), Resizable Textual application for procedural sprite-art authoring., One rung of a station ladder: a beacon cap, a repeating body, a base. Stations…, _station_tier(), View (+10 more)

### Community 22 - "PreviewMatrix"
Cohesion: 0.19
Nodes (9): Message, MouseDown, PreviewMatrix, A click on a rendered art cell that may belong to a structure., Return an aspect-corrected preview box for the stored view axis., Translate a click through the Columns, Panel, and preview margins., StructureSelected, Static (+1 more)

### Community 23 - "Sprite"
Cohesion: 0.19
Nodes (9): Text, Sprite, Variant, active_variant_at_cell(), Return the variants used by the deterministic render for one preview., Return the active source variant occupying one rendered preview cell., Build the render RNG for one sprite request. Every caller that needs to…, _seed_rng() (+1 more)

### Community 24 - "WorkspaceSplitter"
Cohesion: 0.31
Nodes (4): MouseUp, Moved, One-row mouse-drag divider for the workspace's top and bottom rows., WorkspaceSplitter

### Community 26 - "rexpaint_bytes"
Cohesion: 0.36
Nodes (8): Console, Text, ValueError, Encode an exact rectangular Rich text grid as a one-layer ``.xp`` file., A rendered glyph has no slot in the bundled REXPaint font., rexpaint_bytes(), RexPaintGlyphError, _rgb()

### Community 27 - "migrate_color_masks.py"
Cohesion: 0.46
Nodes (7): main(), _migrate_palettes(), _migrate_sprite(), Any, Path, Migrate schema-v1 marker glyphs and palettes to schema-v2 color masks., _write_yaml()

### Community 28 - "Ports, Starbases, and Stardock in Edge Art Designer"
Cohesion: 0.05
Nodes (36): 1. Tier selection always budgets on height, 2. `sprite_art` schema — v4, 3. Port assets, 4. `sprite_art` library facade, 5. Editor (`sprite_art_designer`), 6. Documentation, 7. Tests, 8. Verification (+28 more)

### Community 29 - "migrate_sprite"
Cohesion: 0.40
Nodes (5): main(), migrate_sprite(), Any, Migrate schema-v2 repeat ranges and tier lengths to fixed Section repeats., Return one schema-v3 sprite with a single fixed repeat per Section.

### Community 30 - "migrate_sprite"
Cohesion: 0.40
Nodes (5): main(), migrate_sprite(), Any, Migrate schema-v3 sprites to v4 by recording their vertical section order.…, Return one schema-v4 sprite with its section order made explicit.

### Community 31 - "load_palette_catalog"
Cohesion: 0.14
Nodes (16): fixture, Editor document state, explicit saves, and crash-recovery snapshots., _atomic_yaml_write(), dump_palette_catalog(), load_palette_catalog(), load_sprite_directory(), palette_catalog_to_data(), Path (+8 more)

### Community 33 - "PaletteCatalog"
Cohesion: 0.16
Nodes (18): PaletteCatalog, Render one deterministic Rich sprite, optionally with a preview margin. The…, render_sprite(), A station's beacon band is drawn at the top, where it is authored., Pin the composed output of every authored tier in the whole roster. This is the…, test_a_zero_repeat_omits_one_band_for_one_archetype(), test_active_variant_hit_testing_matches_preview_geometry(), test_archetype_filtering_does_not_change_the_draw_count() (+10 more)

### Community 34 - "Procedural ANSI/Unicode Spaceship Art in *Edge of the Unknown*"
Cohesion: 0.12
Nodes (14): 10. Constraints that keep the method reliable, 11. Practical authoring principles, 1. Hand-authored grammar, procedurally assembled, 2. A ship is a readable sequence of functional sections, 3. Asymmetry is essential to “ship-ness”, 4. Author once, face either direction, 5. Responsive art uses semantic tiers, not blind scaling, 6. Determinism is part of visual identity (+6 more)

### Community 35 - "export_rexpaint"
Cohesion: 0.24
Nodes (13): export_rexpaint(), import_rexpaint_cells(), Path, Atomically write a deterministic REXPaint image and matching palette., Read one bundled-font REXPaint layer with its foreground colors. Imported…, Path, test_generated_heavy_half_beams_remain_authorable_and_exportable(), test_rexpaint_export_is_deterministic_and_uses_one_column_major_layer() (+5 more)

### Community 36 - "AGENTS.md — Edge Art Designer"
Cohesion: 0.17
Nodes (11): AGENTS.md — Edge Art Designer, Architecture, Authoritative design documents, Controlled vocabularies, Development commands, File-editing guidance, Persistence and recovery, Reference project (+3 more)

### Community 37 - "Sprite Art Format"
Cohesion: 0.17
Nodes (11): Asset tree, Composition axes, Glyph and color-mask semantics, Palette catalog, Per-archetype art, REXPaint export, Rotation and reflection, Sections and variants (+3 more)

### Community 38 - "Edge of the Unknown Integration"
Cohesion: 0.18
Nodes (10): Caching, Determinism and compatibility, Divergences from Edge's port rendering, Edge of the Unknown Integration, Migration from the current generator, Roles and subtypes, Stations, The seed contract (+2 more)

### Community 39 - "selected_tier"
Cohesion: 0.20
Nodes (10): Return the structural tier selected for an exact render size., selected_tier(), A vertical view is bounded by the rows it stacks to, not by its width. Station…, No station may be center-cropped at the sizes the game asks for.…, The two historical draws belong to converted ship grammars only. Reproducing a…, test_every_station_tier_fits_the_boxes_edge_requests(), test_horizontal_tier_selection_still_budgets_on_structure_height(), test_stations_consume_no_legacy_ship_color_draws() (+2 more)

### Community 41 - "Port Design Principles"
Cohesion: 0.25
Nodes (7): Archetypes change the silhouette, Port Design Principles, Stations are icons, not renderings, Symmetry is a choice, not a rule, The beacon and glow language, The Stardock, Vertical bands, top to bottom

### Community 42 - "Fighter"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Fighter, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 43 - "Transport"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Media touchstones, Scale and color intent, Silhouette and section grammar, Transport

### Community 44 - "Warship"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Media touchstones, Scale and color intent, Silhouette and section grammar, Warship

### Community 45 - "Capital Warship"
Cohesion: 0.33
Nodes (6): Avoid, Capital Warship, Core fantasy, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 46 - "Needle Picket"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Media touchstones, Needle Picket, Scale and color intent, Silhouette and section grammar

### Community 47 - "Falsehold Raider"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Falsehold Raider, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 48 - "Junction Pinnace"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Junction Pinnace, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 49 - "Radiant Lance"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Media touchstones, Radiant Lance, Scale and color intent, Silhouette and section grammar

### Community 50 - "Hearth Freighter"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Hearth Freighter, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 51 - "Pearl Shell"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Media touchstones, Pearl Shell, Scale and color intent, Silhouette and section grammar

### Community 52 - "Marrow Dart"
Cohesion: 0.33
Nodes (6): Avoid, Core fantasy, Marrow Dart, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 53 - "Broadside Citadel"
Cohesion: 0.33
Nodes (6): Avoid, Broadside Citadel, Core fantasy, Media touchstones, Scale and color intent, Silhouette and section grammar

### Community 54 - "Edge Art Designer"
Cohesion: 0.33
Nodes (5): Data, Edge Art Designer, License, REXPaint interchange, Run

### Community 55 - "Ship Type Design Principles and Media Touchstones"
Cohesion: 0.40
Nodes (5): Purpose, Reviewing a ship type, Role comparison, Shared visual language, Ship Type Design Principles and Media Touchstones

### Community 57 - "PaletteColorGroup"
Cohesion: 0.40
Nodes (3): PaletteColorGroup, A labeled palette color pool that can wrap as one responsive unit., Reserve one label row and a three-row bordered swatch row.

### Community 58 - "Tier selection: before and after height budgeting"
Cohesion: 0.50
Nodes (3): horizontal, Tier selection: before and after height budgeting, vertical

### Community 60 - "test_section_order_decides_which_authored_band_lands_on_top"
Cohesion: 0.50
Nodes (4): A vertical sprite whose two bands are unambiguous and unrandomized., The v3-to-v4 migration guard. v3 renderers always reversed a vertical view's…, test_section_order_decides_which_authored_band_lands_on_top(), _two_band_vertical()

## Knowledge Gaps
- **146 isolated node(s):** `edge-art-designer`, `What this project is`, `Authoritative design documents`, `Reference project`, `Architecture` (+141 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EdgeArtDesigner` connect `EdgeArtDesigner` to `EditorState`, `ConfirmScreen`, `Tier`, `.on_button_pressed`, `._refresh_preview`, `.__init__`, `GroupedSpriteSelect`, `ArtCanvas`, `Selection`, `PaletteColorScreen`, `WorkspaceSplitter`, `app.py`, `PreviewMatrix`, `Sprite`, `.on_art_canvas_glyph_picked`, `.on_select_changed`, `._apply_responsive_panels`, `.on_workspace_splitter_moved`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Why does `Sprite` connect `Sprite` to `test_sprite_art.py`, `EditorState`, `Tier`, `render.py`, `import_edge_ports.py`, `render_ships.py`, `rexpaint.py`, `sprite_art/__init__.py`, `Selection`, `SpriteLibrary`, `app.py`, `PreviewMatrix`, `.on_select_changed`, `rexpaint_bytes`, `load_palette_catalog`, `PaletteCatalog`, `export_rexpaint`, `selected_tier`, `test_section_order_decides_which_authored_band_lands_on_top`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `PaletteCatalog` connect `PaletteCatalog` to `test_sprite_art.py`, `export_rexpaint`, `Tier`, `render.py`, `selected_tier`, `import_edge_ports.py`, `render_ships.py`, `rexpaint.py`, `sprite_art/__init__.py`, `SpriteLibrary`, `app.py`, `PreviewMatrix`, `Sprite`, `rexpaint_bytes`, `test_section_order_decides_which_authored_band_lands_on_top`, `load_palette_catalog`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `EdgeArtDesigner` (e.g. with `EditorState` and `ArtCanvas`) actually correct?**
  _`EdgeArtDesigner` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `PaletteCatalog` (e.g. with `SpriteLibrary` and `RenderRequest`) actually correct?**
  _`PaletteCatalog` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `Sprite` (e.g. with `SpriteLibrary` and `RenderRequest`) actually correct?**
  _`Sprite` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Variant` (e.g. with `RenderRequest` and `RexPaintExport`) actually correct?**
  _`Variant` has 5 INFERRED edges - model-reasoned connections that need verification._