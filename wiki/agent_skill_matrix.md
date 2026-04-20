# Agent × Skill Matrix — Phase 12 SKILL-ROUTE-01

**Single Source of Truth (SSOT)** for Agent × Skill routing.
AGENT.md `<skills>` 블록 과 bidirectional cross-reference.
`scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` 가 CI 검증 surface.

## Legend

- `required`: 에이전트가 본 skill 을 반드시 읽고 준수
- `optional`: 에이전트가 본 skill 을 보조적으로 활용 가능
- `n/a`: 본 skill 은 해당 에이전트 업무와 무관

## Matrix (31 agents × 5 공용 skill + 1 additional)

**Scope note**: Plan frontmatter 는 "30 agents" 로 기재 — disk 실측 시 `.claude/agents/producers/` 에 14 producer dir (trend-collector 부터 publisher 까지) + `.claude/agents/inspectors/` 에 17 inspector dir = 31 agent. Plan 01 SUMMARY (key-decisions §1) 에서 `verify_agent_md_schema.py` scope = 31 로 확정된 disk reality 를 본 matrix 도 동일 채택. harvest-importer (root-level) + shorts-supervisor 는 Phase 12 scope out 으로 제외.

### Producers (14)

| Agent | progressive-disclosure | gate-dispatcher | drift-detection | context-compressor | harness-audit | additional |
|-------|:---:|:---:|:---:|:---:|:---:|------------|
| trend-collector    | optional | required | n/a      | n/a | n/a | — |
| niche-classifier   | optional | required | n/a      | n/a | n/a | — |
| researcher         | optional | required | n/a      | n/a | n/a | — |
| director           | optional | required | n/a      | n/a | n/a | — |
| scripter           | optional | required | optional | n/a | n/a | — |
| script-polisher    | optional | required | optional | n/a | n/a | — |
| metadata-seo       | optional | required | n/a      | n/a | n/a | — |
| scene-planner      | optional | required | n/a      | n/a | n/a | — |
| shot-planner       | optional | required | optional | n/a | n/a | — |
| voice-producer     | optional | required | n/a      | n/a | n/a | — |
| asset-sourcer      | optional | required | optional | n/a | n/a | — |
| thumbnail-designer | optional | required | n/a      | n/a | n/a | — |
| assembler          | optional | required | n/a      | n/a | n/a | — |
| publisher          | optional | required | n/a      | n/a | n/a | — |

**Note**: trend-collector + scripter + asset-sourcer + shot-planner + script-polisher 만 `drift-detection` optional — 다른 producer 는 drift 검출이 책임 범위 외.

### Inspectors (17)

| Agent | progressive-disclosure | gate-dispatcher | drift-detection | context-compressor | harness-audit | additional |
|-------|:---:|:---:|:---:|:---:|:---:|------------|
| ins-schema-integrity    | n/a | required | n/a      | n/a      | n/a | — |
| ins-timing-consistency  | n/a | required | n/a      | n/a      | n/a | — |
| ins-blueprint-compliance | n/a | required | n/a      | n/a      | n/a | — |
| ins-factcheck           | n/a | required | optional | n/a      | n/a | notebooklm-query* |
| ins-narrative-quality   | n/a | required | n/a      | n/a      | n/a | — |
| ins-korean-naturalness  | n/a | required | n/a      | optional | n/a | — |
| ins-thumbnail-hook      | n/a | required | n/a      | n/a      | n/a | — |
| ins-tone-brand          | n/a | required | optional | n/a      | n/a | — |
| ins-readability         | n/a | required | n/a      | n/a      | n/a | — |
| ins-license             | n/a | required | n/a      | n/a      | n/a | — |
| ins-platform-policy     | n/a | required | n/a      | n/a      | n/a | — |
| ins-safety              | n/a | required | n/a      | n/a      | n/a | — |
| ins-audio-quality       | n/a | required | n/a      | n/a      | n/a | — |
| ins-render-integrity    | n/a | required | n/a      | n/a      | n/a | — |
| ins-subtitle-alignment  | n/a | required | n/a      | n/a      | n/a | — |
| ins-mosaic              | n/a | required | n/a      | n/a      | n/a | — |
| ins-gore                | n/a | required | n/a      | n/a      | n/a | — |

**Note**: `additional` 컬럼 의 `*` 접미사 는 D-2 Lock 기간 (2026-04-20 ~ 2026-06-20) 중 **신규 SKILL.md 생성 금지** 원칙 하 agent-specific 참조 (Phase 13+ 에서 실제 SKILL 생성 고려 시 drop).

## Reciprocity Contract (SKILL-ROUTE-01)

- **matrix cell = `required` → AGENT.md `<skills>` 에 "{skill} (required)" literal 존재** (bidirectional)
- **matrix cell = `optional` → AGENT.md `<skills>` 에 "{skill} (optional)" literal 존재** (bidirectional)
- **matrix cell = `n/a` → AGENT.md `<skills>` 에 해당 skill name 부재** (one-way)
- Inspector 전원 `progressive-disclosure` = n/a (Inspector 는 SKILL 작성자 아님 — 준수자)
- harness-audit 전원 n/a (agent 직접 호출 대상 아님 — 오케스트레이터 전용)

## Phase 12 Traceability

| REQ-ID | Implementation |
|--------|---------------|
| SKILL-ROUTE-01 | 본 파일 (SSOT) + `scripts/validate/verify_agent_skill_matrix.py` (CI) |

## Change History

- 2026-04-21: Phase 12 Plan 04 — 초기 생성 (5 공용 skill 실측 + additional 컬럼).
  REQUIREMENTS.md §383 "8 skill" 초안 은 Option A 로 정정 (RESEARCH.md §Open Question Q1).
  Row 수 = 31 (14 producer + 17 inspector) — Plan 01 SUMMARY disk reality 채택.
