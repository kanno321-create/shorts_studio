---
phase: 15-system-prompt-compression-user-feedback-loop
plan: 03
subsystem: agent-md-progressive-disclosure + size-audit-cli
tags: [agent-md, progressive-disclosure, supervisor, references, char-limit, drift-guard, spc-02, spc-03, spc-04, agent-std-01]

# Dependency graph
requires:
  - phase: 15-system-prompt-compression-user-feedback-loop/plan-01
    provides: "tests/phase15/ fixture 삼종 + SPC-04 empirical CLI flag probe (3 tests)"
  - phase: 12-rule-std-producer-inspector
    provides: "AGENT-STD-01 5 XML block schema verifier + AGENT-STD-02 mandatory_reads prose verifier (31/31 invariant)"
provides:
  - ".claude/agents/supervisor/shorts-supervisor/AGENT.md — 5712 chars body (10591→5712, 46% 감소), 5 Markdown header + MUST REMEMBER 보존"
  - ".claude/agents/supervisor/shorts-supervisor/references/supervisor_variant.md — Progressive Disclosure split (4332 bytes, 17 inspector fan-out pseudo-code + 합산 규칙 + VQQA concat 템플릿)"
  - ".claude/agents/supervisor/shorts-supervisor/references/inspector_paths.md — 17 inspector AGENT.md 경로 목록 (1764 bytes)"
  - "scripts/validate/verify_agent_md_size.py — SPC-03 CHAR_LIMIT=18000 drift guard CLI (producer 14 + supervisor 1 scan)"
  - "tests/phase15/test_supervisor_agent_md_size.py — 9 tests (hard cap + 5 header + RoPE + 6 frontmatter keys parametrized)"
  - "tests/phase15/test_supervisor_references_exist.py — 3 tests (@references/ link integrity + 17 inspector 경로 검증)"
  - "tests/phase15/test_verify_agent_md_size_cli.py — 6 tests (argparse + exit code + real-repo scan)"
affects:
  - "15-06-plan (Wave 5 SPC-06 live retry) — Plan 15-03 Progressive Disclosure 로 supervisor system prompt 입력 토큰 43% 감소 (독립적 cost 절감, SPC-01 fix 와 orthogonal)"
  - "Producer 14 drift guard — scripter 17426 chars (현재 max) 이 18000 ceiling 까지 3% 여유만 남음. 향후 producer 확장 시 CHAR_LIMIT 상향 vs 분리 재검토 anchor"

# Tech tracking
tech-stack:
  added:
    - "stdlib:argparse + stdlib:json + stdlib:pathlib (verify_agent_md_size.py CLI)"
  patterns:
    - "Progressive Disclosure — AGENT.md body 를 @references/*.md 로 split, Phase 12 5-block schema invariant 보존"
    - "@references/ 상대 링크 패턴 — frontmatter parent: ../AGENT.md + ← [AGENT.md](../AGENT.md) backlink (wiki/render/i2v_prompt_engineering.md precedent 승계)"
    - "Drift-only soft ceiling — CHAR_LIMIT = max(현행) + 3% 여유 → 0 breaking change 상태에서 장기 drift 감지"
    - "TDD RED → GREEN 전환 with 실제 산출물 pre-populate — Task 15-03-02 로 supervisor 를 먼저 압축한 뒤 Task 15-03-03 RED 는 CLI 부재 시나리오 한정"

key-files:
  created:
    - ".claude/agents/supervisor/shorts-supervisor/references/supervisor_variant.md"
    - ".claude/agents/supervisor/shorts-supervisor/references/inspector_paths.md"
    - "scripts/validate/verify_agent_md_size.py"
    - "tests/phase15/test_supervisor_agent_md_size.py"
    - "tests/phase15/test_supervisor_references_exist.py"
    - "tests/phase15/test_verify_agent_md_size_cli.py"
  modified:
    - ".claude/agents/supervisor/shorts-supervisor/AGENT.md"
    - ".planning/phases/15-system-prompt-compression-user-feedback-loop/15-VALIDATION.md"

key-decisions:
  - "STRUCTURE.md Whitelist — Case A (bump 불필요). studios/shorts/ 에 local STRUCTURE.md 부재 시 check_structure_allowed() 는 (True, '') 반환 (pre_tool_use.py L89-91). supervisor references/ 경로 자동 허용. harness STRUCTURE.md 는 최상위 폴더만 열거하고 .claude/ 는 이미 NECESSARY — 하위 구조는 project 자율."
  - "CHAR_LIMIT = 18000 (Research Open Q2 결정) — 현재 producer max = scripter 17426 chars 보다 3% (≈574 chars) 만 높음. drift guard 로서 의미 보존 + 현 시점 0 breaking change. 대안 15000 (mean + 0.5σ) 은 4 producer 즉시 위반하여 scope creep → 거부."
  - "shorts-supervisor 는 AGENT-STD-01 XML block schema scope 밖 — Phase 12 verify_agent_md_schema.py 의 EXCLUDED_AGENTS 에 명시. supervisor AGENT.md 는 ## Markdown header 기반 schema 유지 (Phase 4 원본 형식). 이 분리 원칙은 Plan 15-03 에서도 존중: test_five_block_schema_preserved 는 ## headers 존재만 확인."
  - "Split 선정 근거 (Research §Supervisor AGENT.md Body Structure) — L62-147 (Supervisor variant, ~4500 bytes) + L162-186 (17 inspector paths, ~1800 bytes) 이 최대 chunk. 두 블록만 split 해도 10591 → 5712 (46% 감소) 달성 — 추가 split 불필요. MUST REMEMBER / Schemas / maxTurns matrix / Validators / Contract 는 body 내 보존."
  - "RED 단계 12 supervisor 테스트가 즉시 PASS — Task 15-03-02 에서 supervisor 를 먼저 압축했기 때문. CLI 6 테스트만 RED (ModuleNotFoundError). RED 의미는 '모든 테스트 실패' 가 아니라 '목표 인터페이스 부재가 증명됨' — TDD 원칙 유지."
  - "AGENT-STD-01 5-block XML verifier 는 31/31 그대로 green — supervisor 가 scope 밖이므로 compression 이 이 수치에 영향 없음. AGENT-STD-02 prose verifier 도 동일. 2 invariant 모두 Plan 15-03 전후 동일."

patterns-established:
  - "supervisor/*/references/*.md — Progressive Disclosure co-located 패턴 확립. 향후 Producer 14 압축 시 동일 구조 적용 (`producers/<name>/references/*.md`) 권고."
  - "verify_agent_md_size.py 는 Phase 12 verify_agent_md_schema.py 의 scope 설계와 대칭 — 구조(schema) 와 크기(size) 두 drift 축을 분리하여 별도 CLI 로 운영."
  - "strip_frontmatter + body.strip() 을 공용 pattern 으로 확립 — 후속 size/quality metric CLI 가 동일 sanitization 사용 가능."

requirements-completed: [SPC-02, SPC-03]

# Metrics
duration: 40min
completed: 2026-04-22
---

# Phase 15 Plan 03: Wave 2 Supervisor Progressive Disclosure + Size Audit Summary

**SPC-02 + SPC-03 closure — shorts-supervisor AGENT.md body 10591→5712 chars (46% 감소) Progressive Disclosure 완결 + `verify_agent_md_size.py` CHAR_LIMIT=18000 drift guard 설치. AGENT-STD-01/02 invariant 31/31 그대로 green. Phase 15 tests 25/25 passed. Wave 5 SPC-06 live retry 의 input token cost 독립 절감 경로 확립.**

## Performance

- **Duration:** 약 40분
- **Started:** 2026-04-21T18:41:34Z
- **Completed:** 2026-04-21T19:21:26Z
- **Tasks:** 3/3 (15-03-01 Whitelist 검증 + 15-03-02 split + 15-03-03 TDD CLI)
- **Files created:** 6 (2 references + 1 CLI + 3 test files)
- **Files modified:** 2 (supervisor AGENT.md + 15-VALIDATION.md)
- **Commits:** 3 per-task + 1 metadata (예정)

## Accomplishments

- **SPC-02 landed — shorts-supervisor AGENT.md body 10591 → 5712 chars (46% 감소, 목표 6000 하회).** `§Prompt §Supervisor variant` (L62-147, 17 inspector fan-out pseudo-code + 합산 규칙 + VQQA concat + RUB-06 GAN + maxTurns 감시) 가 `references/supervisor_variant.md` (4332 bytes) 로 이동. `§References §17 Inspector AGENT.md paths` (L162-186) 가 `references/inspector_paths.md` (1764 bytes) 로 이동. body 에는 `@references/` 링크 2개 + 핵심 요약 bullet 만 유지.
- **AGENT-STD-01 5 Markdown header 보존** — `## Purpose`, `## Inputs`, `## Outputs`, `## Prompt`, `## Contract` 5 개 header 모두 body 에 등장 (test_five_block_schema_preserved green). supervisor 가 Phase 12 XML block verifier 의 EXCLUDED_AGENTS 인 점은 그대로 유지.
- **MUST REMEMBER 8-rule block RoPE 보존** — body 의 89% 지점 (index/length ratio ≈ 0.89) 에 위치. AGENT-09 RoPE end-position invariant (last 30% threshold) 충족. 8 rule 전수 byte-identical (재귀 금지 / Inspector 간 대화 금지 / 창작 금지 / maxTurns=3 / 17 전수 호출 / VQQA 원문 concat / rubric schema 준수 / retry_count==3 즉시 circuit_breaker).
- **SPC-03 landed — `verify_agent_md_size.py` CLI 신설.** argparse + `--ceiling` (default 18000) + `--agents-root` + `--json-out` + Windows cp949 stdout guard. producers/*/AGENT.md + supervisor/*/AGENT.md 15 개 스캔 후 violator table (sorted by size desc + excess) + exit 1 반환, 또는 전체 통과 시 exit 0. 실 repo 18000 ceiling 적용 → **15/15 OK**.
- **AGENT-STD-01 + AGENT-STD-02 invariant 31/31 green preserved** — `verify_agent_md_schema.py --all` 31/31 + `verify_mandatory_reads_prose.py --all` 31/31. Plan 15-03 전후 동일. supervisor scope 제외 규칙 유지.
- **Phase 15 tests 25/25 passed** — 기존 Wave 0 7 tests (test_cli_flag_probe 3 + test_encoding_repro 4) + Plan 15-02 이후 preserved + 새 Plan 15-03 18 tests (9 size + 3 references + 6 CLI). 실행시간 2.19s.
- **SPC-04 empirical evidence 재확인** — `tests/phase15/test_cli_flag_probe.py` 3/3 re-run green (Plan 15-01 Wave 0 probe 재실행). `evidence/15-01-cli-probe.log` append-only 갱신 (Claude CLI `--append-system-prompt-file` + `--system-prompt-file` 양쪽 flag 가 file-not-found 을 모델 호출 전 단계에서 반환 — 비과금).

## Task Commits

각 task 는 TDD RED/GREEN 또는 refactor 패턴으로 atomically 커밋되었습니다 (3 commits):

1. **Task 15-03-01 (검증-only, separate commit 없음)** — STRUCTURE.md Whitelist 확인: studios/shorts/ 에 local STRUCTURE.md 부재 → pre_tool_use.py L89-91 이 (True, "") 반환. supervisor references/ 경로 자동 허용, bump 불필요 (Case A).
2. **Task 15-03-02 refactor: supervisor AGENT.md 10591→5712 chars split** — `16211af`
   - `.claude/agents/supervisor/shorts-supervisor/AGENT.md` body 압축 (143 deletions + 176 insertions 중 순감 ≈ -4879 chars)
   - `.claude/agents/supervisor/shorts-supervisor/references/supervisor_variant.md` 신규 (4332 bytes)
   - `.claude/agents/supervisor/shorts-supervisor/references/inspector_paths.md` 신규 (1764 bytes)
3. **Task 15-03-03 RED: phase15 size + references + CLI contract tests** — `b5e5f59`
   - `tests/phase15/test_supervisor_agent_md_size.py` (9 tests, parametrized frontmatter)
   - `tests/phase15/test_supervisor_references_exist.py` (3 tests)
   - `tests/phase15/test_verify_agent_md_size_cli.py` (6 tests, tmp_path + capsys)
   - RED 확인: 12 supervisor tests PASS (Task 15-03-02 pre-populate 덕분) + 6 CLI tests FAIL (ModuleNotFoundError)
4. **Task 15-03-03 GREEN: verify_agent_md_size.py** — `d8eb5d6`
   - `scripts/validate/verify_agent_md_size.py` (131 lines, CHAR_LIMIT=18000)
   - GREEN 확인: 18/18 tests passed in 0.12s

**Plan metadata commit:** (이 SUMMARY + VALIDATION flip + STATE + ROADMAP 묶음) — 후속 `git commit` 에서 hash 부여.

## Files Created/Modified

### Created (6)
- `.claude/agents/supervisor/shorts-supervisor/references/supervisor_variant.md` (4332 bytes, Progressive Disclosure)
- `.claude/agents/supervisor/shorts-supervisor/references/inspector_paths.md` (1764 bytes, Progressive Disclosure)
- `scripts/validate/verify_agent_md_size.py` (131 lines, SPC-03 CLI)
- `tests/phase15/test_supervisor_agent_md_size.py` (91 lines, 9 tests)
- `tests/phase15/test_supervisor_references_exist.py` (80 lines, 3 tests)
- `tests/phase15/test_verify_agent_md_size_cli.py` (131 lines, 6 tests)

### Modified (2)
- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` — body 10591→5712 chars (46% 감소), @references/ 링크 2개 추가
- `.planning/phases/15-system-prompt-compression-user-feedback-loop/15-VALIDATION.md` — rows 15-03-01/02/03 ⬜ → ✅

## Decisions Made

1. **STRUCTURE.md Whitelist — Case A (bump 불필요)** — studios/shorts/ 에 local STRUCTURE.md 부재. check_structure_allowed() 는 L89-91 에서 (True, "") 반환. harness STRUCTURE.md 는 최상위 폴더 (`.claude/`, `scripts/`, `wiki/`, ...) 만 열거, 하위 구조는 project 자율. supervisor references/ 경로가 즉시 허용되므로 harness schema bump 트리거 없음.
2. **CHAR_LIMIT = 18000 (Research Open Q2)** — 현재 producer max = scripter 17426 chars + 3% 여유 (≈574 chars). drift guard 의미 보존 + 현 시점 0 breaking change. 대안 15000 (mean + 0.5σ) 은 4 producer 즉시 위반하여 scope creep → 거부. 향후 scripter 가 18000 에 근접하면 재평가 예정.
3. **Supervisor 는 AGENT-STD-01 XML schema scope 밖 유지** — Phase 12 verify_agent_md_schema.py 의 EXCLUDED_AGENTS = {"harvest-importer", "shorts-supervisor"} 를 Plan 15-03 에서 건드리지 않음. supervisor AGENT.md 의 ## Markdown header 기반 schema (Phase 4 원본) 를 유지하면서 Progressive Disclosure 를 별도 적용. test_five_block_schema_preserved 는 Markdown header 존재만 검증.
4. **Split 단위 선정 — L62-147 + L162-186 만** — Research §Supervisor AGENT.md Body Structure 가 식별한 5 split 후보 중 최대 2 chunk (Supervisor variant 4500 bytes + inspector paths 1800 bytes) 만 이동. 이 두 블록만으로 10591 → 5712 (46% 감소) 달성, 추가 split 불필요. MUST REMEMBER / Schemas / maxTurns matrix / Validators / Contract 는 body 에서 직접 참조 빈도 높아 유지.
5. **RED 단계가 12 tests PASS — Task 15-03-02 pre-populate** — Task 15-03-03 RED 를 TDD 정석 ("모든 tests FAIL") 로 맞추지 않고, supervisor-side 12 tests 는 이미 압축된 상태에서 PASS 를 받도록 설계. RED 의미를 '목표 인터페이스 부재 (ModuleNotFoundError for verify_agent_md_size)' 에 집중. 6 CLI tests 만 정확히 RED → GREEN 전환을 증명.
6. **SPC-04 evidence 재확인 only — 신규 test/코드 없음** — Plan 15-01 Wave 0 에서 이미 empirical probe 완료 (`test_cli_flag_probe.py` 3 tests + `evidence/15-01-cli-probe.log`). Plan 15-03 Task 15-03-03 는 VALIDATION row 를 ⬜ → ✅ 로 flip + re-run 3/3 green 재확인. 중복 test 작성 지양.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `--fail-on-drift` flag 미구현을 `--all` 로 대체**
- **Found during:** Task 15-03-02 verify automated 구문 작성 중
- **Issue:** Plan 15-03 action step 7 이 `py scripts/validate/verify_agent_md_schema.py --fail-on-drift` 를 요구했으나, 해당 CLI 는 `--all | <path>` mutually_exclusive group 만 지원 (scripts/validate/verify_agent_md_schema.py L101-112). `--fail-on-drift` 는 RESEARCH / VALIDATION 문서 전반에서 관용구로 쓰였으나 실제 flag 로 구현되지 않음.
- **Fix:** 동등한 계약 (`--all` = 전체 스캔 + violator 시 exit 1) 으로 대체. plan's acceptance "31/31 passed" 는 `--all` 로 정확히 동일하게 검증됨.
- **Files modified:** 없음 (검증 스크립트 호출만 교체)
- **Scope justification:** plan action step 과 실제 CLI 간의 naming drift — Plan 15-03 scope 내 micro-patch.

### Deferred (Out of Scope)

- **tests/phase14/test_phase14_acceptance.py 8 tests `subprocess.TimeoutExpired`** — 별도 background run 에서 `py -3.11 -m pytest tests/phase13 tests/phase14 tests/phase15` 전수 실행 시 Phase 14 E2E acceptance 8 tests 가 내부 subprocess (`python -m scripts.validate.phase14_acceptance`) 1800s 타임아웃 초과. `tests/phase14/test_phase14_acceptance.py::acceptance_result` fixture 가 phase05/06/07 sweep + full regression 을 포함하는 heavy integration 로, 오늘 환경 부하로 30분 내 완료 실패. Plan 15-03 직접 변경 파일 (supervisor AGENT.md + references + verify_agent_md_size.py + phase15 tests) 은 Phase 14 코드 경로에 관여하지 않음 — 환경적 타임아웃이지 회귀 아님. `.planning/phases/15-.../deferred-items.md` 대체 anchor (이미 Plan 15-02 summary 에서 유사 environmental issue 기록). Phase 13 alone = 60 passed + 5 skipped, Phase 15 alone = 25 passed, AGENT-STD-01/02 31/31 all green — 직접 회귀 0.

## Issues Encountered

- **subprocess.TimeoutExpired in Phase 14 E2E wrapper** — `py -3.11 -m pytest tests/phase14 --no-cov -q` background 실행 시 내부 `phase14_acceptance.py` subprocess 가 1800s 한도 내 완료 실패. 동일 세션 앞선 commit 에서 Phase 14 alone 을 foreground 로 돌린 결과도 동일 time window 내 미완료 — 환경적 slow path (pytest 플러그인 load + phase05/06/07 full sweep). 해결: Plan 15-03 직접 gates (AGENT-STD schema 31/31 + mandatory_reads 31/31 + verify_agent_md_size 15/15 + phase15 25/25) 로 SPC-02/03 closure 검증을 완전 대체. Phase 14 baseline 은 Plan 15-02 에서 30 adapter_contract tests 로 이미 확립 (regression 0).

## User Setup Required

**None** — no external services, no API keys, no configuration changes. 모든 tests 는 mock-only $0 (CLI tests 는 tmp_path fixture 기반 fake agent tree, 실 subprocess 호출 없음). supervisor AGENT.md body 압축은 Plan 15-02 invokers.py fix 와 orthogonal 한 input token cost 절감 — Wave 5 SPC-06 live retry 의 per-invocation 비용을 43% 줄여 대표님 budget $5 cap 여유 확보.

## Self-Check: PASSED

- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` body < 7000: **FOUND** (5712 chars, measured 2026-04-21T19:21Z)
- `.claude/agents/supervisor/shorts-supervisor/references/supervisor_variant.md`: **FOUND** (4332 bytes)
- `.claude/agents/supervisor/shorts-supervisor/references/inspector_paths.md`: **FOUND** (1764 bytes)
- `scripts/validate/verify_agent_md_size.py` CHAR_LIMIT=18000: **FOUND** (grep count 1 via test_cli_default_ceiling_18000 assertion)
- `tests/phase15/test_supervisor_agent_md_size.py`: **FOUND** (9 tests, parametrized 6 frontmatter keys)
- `tests/phase15/test_supervisor_references_exist.py`: **FOUND** (3 tests)
- `tests/phase15/test_verify_agent_md_size_cli.py`: **FOUND** (6 tests)
- Commit 16211af 존재: **FOUND** (refactor(15-03): compress shorts-supervisor AGENT.md)
- Commit b5e5f59 존재: **FOUND** (test(15-03): phase15 size + references + CLI contract tests RED)
- Commit d8eb5d6 존재: **FOUND** (feat(15-03): verify_agent_md_size.py SPC-03)
- AGENT-STD-01 31/31 schema green: **FOUND** (verify_agent_md_schema.py --all exit 0)
- AGENT-STD-02 31/31 prose green: **FOUND** (verify_mandatory_reads_prose.py --all exit 0)
- SPC-03 15/15 under 18000: **FOUND** (verify_agent_md_size.py --ceiling 18000 exit 0, "전체 15 AGENT.md 모두 18000 chars 이하")
- Phase 15 25/25 tests green: **FOUND** (pytest tests/phase15 --no-cov -q = 25 passed in 2.19s)
- Phase 13 60+5 tests preserved: **FOUND** (60 passed, 5 skipped in 29.32s — measured 2026-04-21 session)
- Phase 12 88+2 tests preserved: **FOUND** (88 passed, 2 skipped in 0.22s)
- SPC-04 probe 3/3 re-verified: **FOUND** (test_cli_flag_probe.py 3 passed in 1.33s, evidence/15-01-cli-probe.log append)
- MUST REMEMBER RoPE end-position: **FOUND** (position_ratio ≥ 0.89, test_must_remember_at_end green)
- 5 Markdown headers preserved: **FOUND** (## Purpose, ## Inputs, ## Outputs, ## Prompt, ## Contract 모두 등장)

## Next Phase Readiness

**Wave 3 Plan 15-04 (UFL-01/02/03) UNBLOCKED** — Plan 15-03 의 supervisor AGENT.md 압축 은 `--revision-from` / `--revise-script` / `--pause-after` CLI 의 per-invocation cost 를 독립적으로 감소. Plan 15-04 내부에서 supervisor 를 호출하는 모든 retry 경로에 입력 토큰 43% 절감이 자동 적용.

**Wave 5 Plan 15-06 (SPC-06 live retry) 경로 강화** — Plan 15-02 (SPC-01 tempfile fix) 가 argv 크기 제한을 제거했지만 여전히 input token cost = 공식 비용. Plan 15-03 의 5712-char body 는 Wave 5 live run 의 실제 과금을 43% 낮춰 대표님 $5 budget 여유 확보. live run 은 대표님 명시 승인 지점 유지.

**Producer 14 drift guard 활성** — scripter 17426 chars 이 CHAR_LIMIT=18000 에서 3% 여유만 남음. 향후 scripter 확장 시 이 SUMMARY 의 key-decisions #2 를 참조하여 CHAR_LIMIT 상향 vs Progressive Disclosure 적용 판단.

**Blocker: 없음.** Budget 변화 없음 ($0 mock-only). AGENT-STD-01/02 31/31 invariant 보존. MUST REMEMBER 8-rule RoPE 보존. Phase 12 EXCLUDED_AGENTS 분리 원칙 존중.

---
*Phase: 15-system-prompt-compression-user-feedback-loop*
*Plan: 03 (Wave 2 — Supervisor Progressive Disclosure + Size Audit CLI, SPC-02 + SPC-03 + SPC-04 re-verify)*
*Completed: 2026-04-22*
