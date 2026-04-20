# FAILURES.md — Append-Only Reservoir

> **D-11:** Append-only via `check_failures_append_only` in `.claude/hooks/pre_tool_use.py`.
>          Modification of existing lines is physically blocked (deny). Only Write with
>          existing-content-as-prefix or new-entry append is allowed.
> **D-14:** Separate from `_imported_from_shorts_naberal.md` (Phase 3 sha256-locked).
>          This file never modifies or duplicates that file — only accumulates Phase 6+ entries.
> **D-2 저수지 원칙:** New failures accumulate here. 30-day aggregation (Plan 09) scans both
>                     this file and `_imported_from_shorts_naberal.md` to surface patterns
>                     (recurrence ≥ 3 → `SKILL.md.candidate` dry-run).

## Entry Schema

```
### FAIL-NNN: [one-line summary]
- **Tier**: A/B/C/D
- **발생 세션**: YYYY-MM-DD 세션 N
- **재발 횟수**: 1
- **Trigger**: [what triggers this failure]
- **무엇**: [what went wrong, observable symptom]
- **왜**: [root cause, invariant violated]
- **정답**: [correct behavior, invariant restored]
- **검증**: [how to verify the fix holds — grep/test/metric]
- **상태**: [observed | resolved | recurring]
- **관련**: [links to other FAIL-IDs, FAILURES_INDEX.md category, wiki nodes]
```

## Entries

(none yet — first Phase 6+ entry goes below this header line; do NOT modify the
above schema or any existing entry once added — append-only Hook will deny.)

### FAIL-ARCH-01: docs/ARCHITECTURE.md Phase status 라인 stale — 다른 세션 "Phase 8" 오인
- **Tier**: B
- **발생 세션**: 2026-04-21 세션 #28 (발견), 최초 drift 발생 2026-04-20 Phase 9 Plan 01 작성 시점
- **재발 횟수**: 1
- **Trigger**: Phase 완결 시 `docs/ARCHITECTURE.md` L6 `**Phase status:**` 헤더 업데이트 누락
- **무엇**: Phase 9 Plan 01 시점 "Phase 8 완결 / Phase 9 진행 중" 으로 작성된 status 라인이 Phase 9 + 9.1 완결 + Phase 10 Entry Gate PASSED 이후에도 갱신 안 됨. 다른 Claude 세션이 이 파일을 읽고 "Phase 8" 이라고 오인 — 대표님 "다른 나베가 페이즈 8이라는데,,,실제로는 10을 작업하고있거든" 질문 유발
- **왜**: `Last updated:` 라인은 자동 갱신되지만 status 문장은 수동 갱신 필요. Phase gate 진입·완결 checkpoint 에 해당 라인 패치가 포함 안 됨
- **정답**: 각 Phase VERIFICATION 완결 시 `docs/ARCHITECTURE.md` L6 status 라인을 새 상태로 교체 (예: "Phase 9 + 9.1 완결, Phase 10 Entry Gate PASSED"). 세션 #28 에서 수동 패치 완료 (commit `e57f891` 포함)
- **검증**: `grep -n "Phase status" docs/ARCHITECTURE.md` → 현재 Phase 번호 vs `.planning/ROADMAP.md` [x] 마커 일치 여부. 세션 시작 session_start.py Hook 에 "ARCHITECTURE.md Phase status 일치 검사" 추가 후보
- **상태**: resolved (세션 #28 패치) — 재발 방지는 Phase 완결 체크리스트에 라인 업데이트 추가 필요
- **관련**: commit `e57f891` / `WORK_HANDOFF.md` 세션 #28 완료 항목 / `CLAUDE.md` Navigator 재설계와 동반 발견
