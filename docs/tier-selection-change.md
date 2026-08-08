# Tier selection: before and after height budgeting

Generated evidence for the `_select_tier` change described in
`docs/EDGE_INTEGRATION.md`. A vertical view now budgets on the rows its
sections stack to, rather than on its constant structure width.

Across 1728 renders (12 roles x 2 views x facings x 3 archetypes x 12 boxes),
780 changed tier. **Every one is a vertical view**; horizontal ship
renders are byte-identical in glyphs and style spans.

Cells are `before -> after`, canonical facing, `humanoid_diplomat`.

## horizontal

| role | 16x5 | 20x7 | 24x3 | 40x7 | 12x4 | 56x12 | 10x10 | 18x8 | 22x9 | 38x16 | 6x6 | 30x5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| broadside_citadel | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| capital_warship | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| falsehold_raider | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| fighter | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| hearth_freighter | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| junction_pinnace | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| marrow_dart | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| needle_picket | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| pearl_shell | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| radiant_lance | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| transport | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |
| warship | medium | full | compact | full | compact | full | full | full | full | full | medium | medium |

## vertical

| role | 16x5 | 20x7 | 24x3 | 40x7 | 12x4 | 56x12 | 10x10 | 18x8 | 22x9 | 38x16 | 6x6 | 30x5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| broadside_citadel | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| capital_warship | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| falsehold_raider | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| fighter | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> medium** | compact | **full -> compact** |
| hearth_freighter | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| junction_pinnace | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | full | **medium -> compact** | **full -> compact** | **full -> compact** | full | compact | **full -> compact** |
| marrow_dart | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| needle_picket | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| pearl_shell | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| radiant_lance | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| transport | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |
| warship | **full -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **medium -> compact** | **full -> compact** | **full -> compact** | **full -> compact** | compact | **full -> compact** |

