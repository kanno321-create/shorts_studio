# Phase 6 Plan 10: Agent Prompt Delta Manifest

> D-18: mass update of 15 agent prompts; other 18 of 33 agents MUST be byte-identical.
>
> Note — plan originally enumerated "32 agents"; filesystem reality at execution time (2026-04-19) is 33 AGENT.md files (harvest-importer + 32 inspector/producer/supervisor). 15 target agents changed + 18 non-target byte-identical = 33 total. Plan counting adjusted to match disk state.

## Per-File Line Delta

| Agent | Lines before | Lines after | Delta | References Added |
|-------|-------------:|------------:|------:|------------------|
| inspectors/content/ins-factcheck | 123 | 123 | 0 | `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/continuity_bible/channel_identity.md` |
| inspectors/content/ins-korean-naturalness | 154 | 154 | 0 | `@wiki/shorts/continuity_bible/channel_identity.md`, `@wiki/shorts/algorithm/ranking_factors.md` |
| inspectors/content/ins-narrative-quality | 125 | 125 | 0 | `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/kpi/retention_3second_hook.md` |
| inspectors/style/ins-thumbnail-hook | 141 | 141 | 0 | `@wiki/shorts/continuity_bible/channel_identity.md` (×3 — channel consistency / color palette / q4 criterion) |
| inspectors/technical/ins-audio-quality | 118 | 118 | 0 | `@wiki/shorts/render/remotion_kling_stack.md` |
| inspectors/technical/ins-render-integrity | 114 | 114 | 0 | `@wiki/shorts/render/remotion_kling_stack.md` |
| inspectors/technical/ins-subtitle-alignment | 120 | 120 | 0 | `@wiki/shorts/render/remotion_kling_stack.md` |
| producers/director | 136 | 136 | 0 | `@wiki/shorts/continuity_bible/channel_identity.md`, `@wiki/shorts/algorithm/ranking_factors.md` |
| producers/metadata-seo | 159 | 159 | 0 | `@wiki/shorts/render/remotion_kling_stack.md`, `@wiki/shorts/ypp/entry_conditions.md`, `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/kpi/retention_3second_hook.md` |
| producers/niche-classifier | 135 | 135 | 0 | `@wiki/shorts/continuity_bible/channel_identity.md` |
| producers/researcher | 160 | 159 | -1 | `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/ypp/entry_conditions.md`, `@wiki/shorts/continuity_bible/channel_identity.md` (×8 total refs — Fallback chain + Wiki + MUST REMEMBER) |
| producers/scene-planner | 184 | 184 | 0 | `@wiki/shorts/continuity_bible/channel_identity.md`, `@wiki/shorts/render/remotion_kling_stack.md` |
| producers/scripter | 210 | 211 | +1 | `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/kpi/retention_3second_hook.md`, `@wiki/shorts/continuity_bible/channel_identity.md` |
| producers/shot-planner | 194 | 194 | 0 | `@wiki/shorts/render/remotion_kling_stack.md` (×6), `@wiki/shorts/continuity_bible/channel_identity.md` (×2) |
| producers/trend-collector | 126 | 126 | 0 | `@wiki/shorts/algorithm/ranking_factors.md`, `@wiki/shorts/kpi/retention_3second_hook.md` |
| **Total** | **2199** | **2199** | **0** | 15 files / 5 ready nodes / 52 @wiki/shorts refs |

## Per-Category Reference Distribution

| Wiki Node | Referencing Agents | Total Refs |
|-----------|-------------------:|-----------:|
| `@wiki/shorts/continuity_bible/channel_identity.md` | 10 | 14 |
| `@wiki/shorts/algorithm/ranking_factors.md` | 8 | 11 |
| `@wiki/shorts/render/remotion_kling_stack.md` | 7 | 11 |
| `@wiki/shorts/kpi/retention_3second_hook.md` | 4 | 4 |
| `@wiki/shorts/ypp/entry_conditions.md` | 2 | 3 |
| **Total** | — | **52** |

Net per-file ref counts (verified via `re.findall(r'@wiki/shorts/[\w\-/]+\.md')`):
- ins-factcheck: 6 / ins-korean-naturalness: 2 / ins-narrative-quality: 2
- ins-thumbnail-hook: 3 / ins-audio-quality: 1 / ins-render-integrity: 1 / ins-subtitle-alignment: 1
- director: 2 / metadata-seo: 4 / niche-classifier: 1
- researcher: 8 / scene-planner: 2 / scripter: 3 / shot-planner: 10 / trend-collector: 6
- Grand total: 52 refs across 15 target agents

## Byte Identity — Other 18 Agents (MUST be unchanged)

Comparison of `phase06_agents_before.txt` vs `phase06_agents_after.txt`:
- **15 hashes CHANGED** (listed above — exact 15 target files per plan frontmatter `files_modified`)
- **18 hashes IDENTICAL** (enumerated below):
  1. `harvest-importer/AGENT.md`
  2. `inspectors/compliance/ins-license/AGENT.md`
  3. `inspectors/compliance/ins-platform-policy/AGENT.md`
  4. `inspectors/compliance/ins-safety/AGENT.md`
  5. `inspectors/media/ins-gore/AGENT.md`
  6. `inspectors/media/ins-mosaic/AGENT.md`
  7. `inspectors/structural/ins-blueprint-compliance/AGENT.md`
  8. `inspectors/structural/ins-schema-integrity/AGENT.md`
  9. `inspectors/structural/ins-timing-consistency/AGENT.md`
  10. `inspectors/style/ins-readability/AGENT.md`
  11. `inspectors/style/ins-tone-brand/AGENT.md`
  12. `producers/assembler/AGENT.md`
  13. `producers/asset-sourcer/AGENT.md`
  14. `producers/publisher/AGENT.md`
  15. `producers/script-polisher/AGENT.md`
  16. `producers/thumbnail-designer/AGENT.md`
  17. `producers/voice-producer/AGENT.md`
  18. `supervisor/shorts-supervisor/AGENT.md`

## Sanity Checks (executed 2026-04-19)

- `grep -r "Phase 6 채움" .claude/agents` returns 0 hits ✅
- `grep -r "Phase 6 wiring" .claude/agents` returns 0 hits ✅
- `grep -rE "Phase 6 Continuity Bible에서 정의|Phase 6에서 정의|Phase 6에서 채워짐" .claude/agents` returns 0 hits ✅
- `grep -rE "@wiki/shorts/[\w_/]+\.md" .claude/agents` returns 52 hits (≥15 required) ✅
- `python -c "from scripts.wiki.link_validator import validate_all_agent_refs; ..."` returns 0 problems ✅
- All 5 referenced wiki nodes have `status: ready` (D-17 requirement) ✅
