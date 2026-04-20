---
plan: 12-03
status: not_started
created: 2026-04-21
phase: 12-agent-standardization-skill-routing-failures-protocol
disk_reality: 0/17 inspectors migrated (all fail 5-block schema)
upstream_dependency: Plan 12-02 SUMMARY 존재 확인 필수
resume_command: /gsd:execute-phase 12 --wave 3
---

# HANDOFF — Plan 12-03 (Inspector 17-migration)

## 맥락

Phase 12 Wave 3 단독 Plan. Plan 12-02 Wave 2 에서 Producer 12개가 migration 완료된 후, 동일 5-block schema template 로 Inspector 17개를 6 sub-wave (Structural 3 → Content 3 → Style 3 → Compliance 3 → Technical 3 → Media 2) 로 migration. 완료 시 **30/30 AGENT.md schema compliant** + Phase 4 GAN_CLEAN 17/17 regression 유지 + FAIL-PROTO-02 Wave 3 supplement 기록.

## 선행 조건 (진입 전 확인)

1. **Plan 12-02 완료 확인**:
   ```bash
   ls .planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-02-SUMMARY.md
   python scripts/validate/verify_agent_md_schema.py --all   # producers 14/14 PASS 기대
   ```
   `12-02-SUMMARY.md` 가 없으면 `12-02-HANDOFF.md` 먼저 수행.

2. **현재 schema 상태**:
   ```
   FAIL: 17/31 AGENT.md violate 5-block schema
   (17개 = 모두 inspectors, producers 14/14 PASS)
   ```

3. **Plan 12-05 (FAILURES rotation) 완료 확인** — FAIL-PROTO-02 entry 를 append 하려면 rotation protocol 이 활성 상태여야 함. `git log --oneline | grep 12-05` 로 확인. (2026-04-21 시점: 완료됨 — `6de7068 docs(12-05): complete FAIL-PROTO-01 rotation protocol plan`.)

## 읽어야 할 파일

- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-03-PLAN.md` — 7 task, 6 sub-wave 구조
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/templates/inspector.md.template` — Plan 01 canonical template
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-01-SUMMARY.md` — verifier 사용법
- `.claude/agents/producers/trend-collector/AGENT.md` — 타입 다르지만 v1.2 style reference
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-04-SUMMARY.md` — SSOT matrix (Plan 03 완료 시 reciprocity drift 0 으로 떨어짐)
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/RESEARCH.md` — §FAIL-PROTO-02 supplement 패턴
- `./CLAUDE.md` — 한국어 존댓말 + FAILURES append-only 규칙
- `.claude/skills/` — 6개 skill 목록 (matrix 작성용)

## Sub-wave 구조 (병렬 허용 단위)

| Sub-wave | Inspectors | 카테고리 |
|----------|-----------|----------|
| 3a | ins-schema-integrity, ins-timing-consistency, ins-blueprint-compliance | Structural |
| 3b | ins-factcheck, ins-narrative-quality, ins-korean-naturalness | Content |
| 3c | ins-thumbnail-hook, ins-tone-brand, ins-readability | Style |
| 3d | ins-license, ins-platform-policy, ins-safety | Compliance |
| 3e | ins-audio-quality, ins-render-integrity, ins-subtitle-alignment | Technical |
| 3f | ins-mosaic, ins-gore | Media |

## 완료 판정

- [ ] `python scripts/validate/verify_agent_md_schema.py --all` → **30/30 or 31/31 PASS** (harvest-importer 포함 여부에 따라)
- [ ] `tests/phase12/test_agent_md_schema.py` GREEN (Plan 02 skip gate 해제 가능)
- [ ] `tests/phase12/test_mandatory_reads_prose.py` — 17개 inspector 포함 전수 GREEN (또는 Plan 06 에서 본격 검증)
- [ ] `tests/phase04/` GAN_CLEAN 17/17 regression 유지 — producer/inspector 페어 통신 손상 없음
- [ ] `.claude/failures/FAILURES.md` 에 FAIL-PROTO-02 Wave 3 supplement entry 단일 append
- [ ] `wiki/agent_skill_matrix.md` reciprocity drift → 0 (`python scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` exit 0)
- [ ] `12-03-SUMMARY.md` 존재
- [ ] STATE + ROADMAP 업데이트

## 리스크

- **maxTurns 상한 증빙**: `ins-factcheck` (maxTurns=10) 과 `ins-tone-brand` (maxTurns=5) 는 RUB-05 예외. template 의 `<constraints>` 블록에 명시적 기록 필요 — Plan 03 task 에 해당 필드 누락 시 Plan 06 prose validator 에서 FAIL.
- **한국어 존댓말 baseline**: 17개 파일 모두 표준 정중 존댓말 준수. "샘플링 금지" 한국어 literal 이 mandatory_reads 에 들어가야 함 (Plan 06 검증 대상).
- **병렬 커밋 시 --no-verify**: 6 sub-wave 가 병렬 실행될 경우 git hook 경쟁 회피. 단일 agent 순차 실행 시 일반 commit 사용.
