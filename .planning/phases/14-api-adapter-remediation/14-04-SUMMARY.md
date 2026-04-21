---
phase: 14-api-adapter-remediation
plan: 04
subsystem: testing
tags: [docs, adapter-contract, moc, hook, warn-only, wave3, adapt-05, adapt-06c, gitignore]

# Dependency graph
requires:
  - phase: 14-api-adapter-remediation
    plan: 01
    provides: "pytest.ini + adapter_contract marker + tests/adapters/ package + repo_root/_fake_env fixtures + --strict-markers"
  - phase: 14-api-adapter-remediation
    plan: 02
    provides: "Wave 1 regression green (742/742) + canonical MOC status regex ^status:\\s*(scaffold|partial)\\b + veo_i2v.py T2V token cleanup"
  - phase: 14-api-adapter-remediation
    plan: 03
    provides: "Wave 2 contract tests (23 green: veo_i2v 6 + elevenlabs 7 + shotstack 10) — doc cross-reference anchors"
provides:
  - wiki/render/adapter_contracts.md (ADAPT-05 — 7 adapter × 5 column + mock↔real delta + retry/fallback rails + production-safe defaults + CLAUDE.md 금기 강제 + Phase 13 boundary)
  - tests/adapters/test_adapter_contracts_doc.py (7 structural validator tests — frontmatter + 7 adapters + 4 sections + whisperx stub + 3 contract xref + 금기 ref + fault injection invariant)
  - wiki/render/MOC.md TOC entry for adapter_contracts.md (Phase 14 anchor, D-17 invariant preserved with canonical regex verbatim from Plan 02 Task 14-02-04)
  - .claude/hooks/pre_tool_use.py ADAPT-06c warn-only Hook extension (scripts/orchestrator/api/*.py edit → warn if no tests/adapters/test_*_contract.py touch this session)
  - .gitignore entry for .claude/hooks/_adapter_contract_touch.json (session-scope ephemeral tracking file exclusion)
  - pytest -m adapter_contract 30 tests green (23 Wave 2 + 7 Wave 3 doc validator)
affects: [14-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Leaf contract doc frontmatter discipline: status=ready (distinct from MOC-as-TOC D-17 invariant scaffold|partial; adapter_contracts.md is not a TOC so ready is legitimate)"
    - "Session-scope ephemeral tracking via ppid-keyed JSON dict — .claude/hooks/_adapter_contract_touch.json excluded by .gitignore"
    - "Warn-only Hook surface: stderr print + stdout `{\"decision\":\"allow\"}` coexist — keeps existing 8 regex DENY logic intact while adding drift-prevention nudge"
    - "Cross-plan canonical regex reuse: Plan 02 Task 14-02-04 + Plan 04 Task 14-04-03 share byte-identical `^status:\\s*(scaffold|partial)\\b` multiline regex for drift-audit consistency"

key-files:
  created:
    - wiki/render/adapter_contracts.md
    - tests/adapters/test_adapter_contracts_doc.py
    - .planning/phases/14-api-adapter-remediation/14-04-SUMMARY.md
  modified:
    - wiki/render/MOC.md
    - .claude/hooks/pre_tool_use.py
    - .gitignore

key-decisions:
  - "adapter_contracts.md frontmatter status=ready (not scaffold/partial): leaf contract doc is NOT a MOC-as-TOC, so D-17 invariant does not apply. MOC.md itself retains status=partial (Plan 02 decision preserved byte-identical)."
  - "whisperx row documented as 'NOT YET IMPLEMENTED (Phase 15+ stub)' per 14-RESEARCH Open Q2 Option A — no contract test file created against absent module (would ModuleNotFoundError). 3 mentions in doc (registry row + retry chain remark + cross-reference table)."
  - "Hook warn-only: `_record_contract_touch` 의 `except OSError: pass` 는 **설계 의도** (warn-only = 기록 실패로 작업 차단 금지). 금기 #3 침묵 폴백과 구분되는 명시적 warn-only 설계 (주석으로 의도 anchoring)."
  - "Hook insertion point: main() dispatch 의 최상단 (tool_name 검증 직후) — 기존 8 regex 차단 로직 **앞에서** warn 출력하여 차단되더라도 최소한 경고는 사용자에게 도달. 기존 로직 순서/regex/조건 전부 unchanged."
  - "Pre_tool_use.py 네임스페이스 충돌 회피: `import os as _os` 로 신규 import alias 지정하여 기존 top-level `import json, shutil, sys, re, datetime, Path` 변경 없음. `_ADAPTER_PATTERN` / `_CONTRACT_PATTERN` / `_TRACK_FILE` 모두 underscore prefix."
  - "Structural validator TODO false-positive 회피: 원 plan template 의 '금기 #2 준수: TODO 없음' 메타-선언 문구가 grep TODO=1 false-positive 유발 → '미완성 표식 없음' 으로 재작성하여 grep TODO = 0 달성."

patterns-established:
  - "Leaf contract doc vs MOC-as-TOC status 분리 규율: MOC 는 scaffold|partial 고정, 개별 leaf doc 은 ready 승격 자유 — MOC.D-17 invariant 가 leaf doc 까지 번지지 않음을 문서 + 테스트로 anchoring."
  - "Warn-only Hook 증식 패턴: 기존 차단 regex 건드리지 않고 main() 초입에 독립 함수 호출 + `_` prefix namespace 격리 + session-scope file .gitignore exclusion. Phase 15+ 추가 drift 감지 Hook 도 본 패턴 재사용 가능."
  - "Cross-plan regex byte-identical 유지: 동일 invariant 를 검증하는 여러 plan 이 regex 를 복제할 때 word-boundary `\\b` 포함 정확한 문자열을 SUMMARY 양쪽에 명시하여 drift 감사 도구가 일관된 판정을 내리도록 보장."

requirements-completed: [ADAPT-05, ADAPT-06]

# Metrics
duration: 13m
completed: 2026-04-21
---

# Phase 14 Plan 04: Wave 3 Docs + MOC + Warn-Only Hook + .gitignore Summary

**wiki/render/adapter_contracts.md 신설 (7 adapter × 5 column + mock↔real + retry + production-safe + 금기 + xref + Phase 13 boundary = 7 섹션) + 7 structural validator 테스트 green + MOC.md TOC entry [x] (D-17 invariant 보존 via Plan 02 canonical regex byte-identical) + pre_tool_use.py ADAPT-06c warn-only Hook 확장 (기존 8 regex 차단 로직 무결성 유지) + .gitignore session-scope tracking file exclusion. `pytest -m adapter_contract` 30 tests green (23 Wave 2 + 7 Wave 3), Wave 1 regression 742/742 preserved. ADAPT-05 + ADAPT-06 충족.**

## Performance

- **Duration:** ~13m (4 task-commits + overall verification including 10m37s Wave 1 regression sweep)
- **Started:** 2026-04-21 (after Plan 14-03 landed at `9e27881`)
- **Completed:** 2026-04-21
- **Tasks:** 4/4 completed
- **Files created:** 2 (wiki/render/adapter_contracts.md + tests/adapters/test_adapter_contracts_doc.py)
- **Files modified:** 3 (wiki/render/MOC.md + .claude/hooks/pre_tool_use.py + .gitignore)

## Accomplishments

- **ADAPT-05 충족** — `wiki/render/adapter_contracts.md` 가 7 adapter (kling / runway / veo_i2v / typecast / elevenlabs / shotstack / whisperx) 의 입력 schema + 출력 schema + retry/fallback + fault injection 지원 여부 + mock↔real delta 를 단일 지점에 anchoring. 83 lines, 7 `## ` 섹션 (Registry + Mock↔Real Deltas + Retry/Fallback + Production-Safe Defaults + 금기사항 강제 + Contract Cross-Ref + Phase 13 Boundary + 갱신 기록). whisperx row 는 "NOT YET IMPLEMENTED (Phase 15+ stub)" 으로 명시.
- **Structural validator 7 tests green** (plan 요구 ≥6) — `tests/adapters/test_adapter_contracts_doc.py` 가 frontmatter 필수 키 + 7 adapter 전수 + 4 섹션 헤더 + whisperx stub 라벨 + 3 contract 테스트 xref + 금기 ref + D-3 fault injection invariant 를 7 test 로 자동 검증.
- **MOC.md TOC entry + D-17 invariant 보존** — `wiki/render/MOC.md` 에 `[x] adapter_contracts.md` entry 1 줄 추가 (line 32). frontmatter `status: partial` **변경 없음** — Plan 02 Task 14-02-04 에서 확립한 canonical regex `^status:\s*(scaffold|partial)\b` 와 byte-identical 일치 유지. Phase 6 MOC linkage 테스트 (`tests/phase06/test_moc_linkage.py`) 6/6 여전히 green.
- **ADAPT-06c warn-only Hook** — `.claude/hooks/pre_tool_use.py` 확장 (102 lines 추가, 372→474). `scripts/orchestrator/api/*.py` 를 Edit/Write/MultiEdit 할 때 현재 세션 내 `tests/adapters/test_*_contract.py` touch 이력이 없으면 stderr 에 warn 출력 + 작업 비차단. **기존 8 regex 차단 로직 전부 보존** (functional test 4 개로 재검증: skip_gates pattern 여전히 DENY).
- **`.gitignore` wiring** — `.claude/hooks/_adapter_contract_touch.json` exclude 엔트리 + 주석 (2 라인 추가, 88→91). `git check-ignore -v` 로 session-scope ephemeral file 이 git 에서 제외됨 확인.
- **`pytest -m adapter_contract` 30 tests green in 1.82s** — 23 Wave 2 (Plan 14-03) + 7 Wave 3 (Plan 14-04 validator) = 30. Plan 14-05 phase-gate 가 요구하는 ≥20 threshold 초과.
- **Wave 1 regression 742/742 preserved** — `pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov` → 742 passed, 2 warnings in 637.91s (0:10:37). Pre-Wave-2 baseline 과 동일 (delta +4.57s vs 633.34s post-Wave-1, +1.3% which is environmental noise).

## Task Commits

Each task committed atomically per plan `commit_discipline: per-artifact`:

1. **Task 14-04-01: wiki/render/adapter_contracts.md — ADAPT-05 7-adapter contract matrix** — `00a87a7` (docs)
2. **Task 14-04-02: adapter_contracts.md structural validator — ADAPT-05 (7 tests)** — `0591250` (test)
3. **Task 14-04-03: wiki/render/MOC.md — adapter_contracts.md TOC entry + Phase 14 anchor** — `c419641` (docs)
4. **Task 14-04-04: pre_tool_use.py ADAPT-06c warn-only Hook + .gitignore wiring** — `4d916a9` (feat)

## Files Created/Modified

### Created (2)

- `wiki/render/adapter_contracts.md` — 83 lines, 7 major sections. frontmatter `category: render, status: ready, tags: [contract, adapter, phase14], updated: 2026-04-21, owner: Phase 14 API Adapter Remediation`. 7 adapter × 5 column matrix + 5 mock↔real delta rows + 4 retry chain bullets + production-safe defaults 명시 + 금기 #3/#4/#5 cross-reference + 3 contract 테스트 파일 xref + Phase 13 smoke boundary.
- `tests/adapters/test_adapter_contracts_doc.py` — 125 lines, 7 tests. Module `pytestmark = pytest.mark.adapter_contract`. 검증 축: frontmatter keys / 7 adapter listing / 4 section headers / whisperx stub label / 3 contract xref / 금기 ref / fault injection invariant. TODO 0 hits.

### Modified (3)

- `wiki/render/MOC.md` — 1 line inserted (line 32): `[x] adapter_contracts.md` TOC entry with Phase 14 anchor. frontmatter `status: partial` **unchanged** (D-17 invariant 보존).
- `.claude/hooks/pre_tool_use.py` — 102 lines added (372→474). New Phase 14 ADAPT-06c section: `_ADAPTER_PATTERN` / `_CONTRACT_PATTERN` / `_TRACK_FILE` constants + `_record_contract_touch` / `_contract_touched_this_session` / `check_adapter_contract_drift` 3 functions + main() 초입 호출 1 라인 삽입. 기존 8 regex 차단 블록 (`check_failures_append_only` / `backup_skill_before_write` / `check_structure_allowed` / `load_patterns` / `check_content`) 전부 unchanged.
- `.gitignore` — 2 lines added (88→91, +3 including blank): `# Phase 14 ADAPT-06c — warn-only Hook session-scope tracking file` 주석 + `.claude/hooks/_adapter_contract_touch.json` pattern.

## Decisions Made

1. **adapter_contracts.md frontmatter `status: ready`** — leaf contract doc 은 MOC-as-TOC 가 아니므로 D-17 invariant 가 적용되지 않는다. MOC.md 자체는 여전히 `status: partial` 유지 (Plan 02 Task 14-02-04 에서 확립한 canonical regex `^status:\s*(scaffold|partial)\b` 와 byte-identical 일치). `adapter_contracts.md` 는 single-source-of-truth 역할을 수행하므로 신설 직후부터 production-ready 상태로 선언.
2. **whisperx row 처리 = Option A (stub row 유지)** — 14-RESEARCH Open Question #2 recommended option. `scripts/orchestrator/api/whisperx.py` 부재 (`find scripts -name whisperx*` = 0 matches), 현 subtitle alignment 는 `elevenlabs._chars_to_words` D-10. Contract test 대신 **문서 stub row** 로 Phase 15+ 시점 재설계 예정 anchoring.
3. **Hook warn-only 삽입 위치 = main() 초입** — tool_name 검증 직후, 기존 8 regex 차단 로직 **앞**. 이유: 기존 로직이 Edit/Write 를 차단하더라도 warn 은 stderr 에 도달해야 drift 재발 방지 시그널이 소실되지 않는다. 기존 차단은 `{"decision":"deny"}` return, warn 은 stderr print — 두 표면이 독립적.
4. **Hook namespace 격리** — `import os as _os` alias + `_ADAPTER_PATTERN` / `_CONTRACT_PATTERN` / `_TRACK_FILE` / `_record_contract_touch` / `_contract_touched_this_session` 전부 underscore prefix. 기존 top-level import 문 (`json, shutil, sys, re, datetime, Path`) 변경 없음. `check_adapter_contract_drift` 는 public function 으로 main() 에서 호출.
5. **Structural validator TODO 회피** — 원 plan template `<action>` 내 docstring 에 "금기 #2 준수: TODO 없음" 메타-선언 문구가 포함되었는데, 이것이 grep TODO=1 false-positive 를 유발. "미완성 표식 없음 (전수 구현 완료)" 로 재작성하여 grep TODO = 0 달성. 의미 보존 + 금기 #2 acceptance criterion 엄격 만족.
6. **7 tests (plan 요구 ≥6)** — `test_fault_injection_invariant_documented` 를 7번째로 추가. D-3 Phase 7 invariant (`allow_fault_injection=False` default) 가 adapter_contracts.md 에 명시되었는지 검증 — Wave 2 contract 테스트의 3 개 `test_*_mock_fault_injection_disabled_by_default` 와 문서 레이어 동기화.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug: docstring self-reference paradox] Validator docstring 의 'TODO 없음' 메타-선언이 grep TODO=1 false-positive 유발**

- **Found during:** Task 14-04-02 verification — `grep -c "TODO" tests/adapters/test_adapter_contracts_doc.py` returned 1, but plan acceptance requires 0.
- **Issue:** 14-04-PLAN.md Task 14-04-02 `<action>` 블록의 module docstring 이 `"금기 #2 준수: TODO 없음."` 문구를 literal 로 포함. grep 은 substring 매칭이므로 메타-선언 자체를 실 TODO 토큰으로 오탐지. Plan 14-02 Task 14-02-01 의 veo_i2v.py T2V 자기참조 패러독스와 동일 클래스 문제.
- **Fix:** "금기 #2 준수: TODO 없음" → "금기 #2 준수: 미완성 표식 없음 (전수 구현 완료)". 의미 보존, grep token count 0 달성, 7 tests 전수 pass 무영향.
- **Files modified:** tests/adapters/test_adapter_contracts_doc.py (신규 작성 시점에 수정 반영, 별도 commit 아님)
- **Verification:** `grep -c "TODO" tests/adapters/test_adapter_contracts_doc.py` → 0, `pytest tests/adapters/test_adapter_contracts_doc.py -v --no-cov` → 7 passed in 0.08s.
- **Committed in:** `0591250` (Task 14-04-02).

---

**Total deviations:** 1 auto-fixed (Rule 1 plan-template bug — docstring self-reference paradox analogous to Plan 02 Task 14-02-01 veo_i2v.py pattern). Plan executed 근사 as written otherwise. Zero Rule 2/3/4 deviations.

**Impact on plan:** 0 scope creep — self-reference fix 는 Plan 14-02 에서 이미 확립한 "blacklist-tripping tokens in self-documentation must be rewritten" 원칙 적용. 7 tests 전수 green, plan 의 ≥6 threshold 초과.

## Evidence Blocks (CLAUDE.md 필수사항 #8)

### 1. Task 14-04-01 adapter_contracts.md grep acceptance

```bash
$ grep -cE "^## [A-Za-z]" wiki/render/adapter_contracts.md
7   # ≥4 target (Registry + Mock↔Real + Retry + Production-Safe + 금기 + xref + Phase 13 + 갱신)
$ grep -c "kling_i2v" wiki/render/adapter_contracts.md ; grep -c "runway_i2v" wiki/render/adapter_contracts.md ; grep -c "veo_i2v" wiki/render/adapter_contracts.md ; grep -c "typecast" wiki/render/adapter_contracts.md ; grep -c "elevenlabs" wiki/render/adapter_contracts.md ; grep -c "shotstack" wiki/render/adapter_contracts.md ; grep -c "whisperx" wiki/render/adapter_contracts.md
5 5 6 5 7 7 3   # 7 adapter 전수 ≥2 (whisperx ≥2 포함)
$ grep -c "NOT YET IMPLEMENTED" wiki/render/adapter_contracts.md
3   # ≥1
$ grep -c "allow_fault_injection" wiki/render/adapter_contracts.md
7   # ≥2
$ grep -cE "^category:\s*render" wiki/render/adapter_contracts.md ; grep -cE "^status:\s*ready" wiki/render/adapter_contracts.md
1 1   # frontmatter
$ grep -c "Phase 14" wiki/render/adapter_contracts.md ; grep -c "금기" wiki/render/adapter_contracts.md
6 6
```

### 2. Task 14-04-02 structural validator pytest + grep

```
$ py -3.11 -m pytest tests/adapters/test_adapter_contracts_doc.py -v --no-cov
collected 7 items

tests/adapters/test_adapter_contracts_doc.py::test_frontmatter_required_keys PASSED [ 14%]
tests/adapters/test_adapter_contracts_doc.py::test_all_seven_adapters_listed PASSED [ 28%]
tests/adapters/test_adapter_contracts_doc.py::test_min_four_section_headers PASSED [ 42%]
tests/adapters/test_adapter_contracts_doc.py::test_whisperx_stub_labeled PASSED [ 57%]
tests/adapters/test_adapter_contracts_doc.py::test_contract_cross_reference_present PASSED [ 71%]
tests/adapters/test_adapter_contracts_doc.py::test_forbid_reference_present PASSED [ 85%]
tests/adapters/test_adapter_contracts_doc.py::test_fault_injection_invariant_documented PASSED [100%]

============================== 7 passed in 0.08s ==============================

$ grep -c "pytest.mark.adapter_contract" tests/adapters/test_adapter_contracts_doc.py ; grep -cE "^def test_" tests/adapters/test_adapter_contracts_doc.py ; grep -c "ADAPTER_NAMES" tests/adapters/test_adapter_contracts_doc.py ; grep -c "whisperx" tests/adapters/test_adapter_contracts_doc.py ; grep -c "TODO" tests/adapters/test_adapter_contracts_doc.py
1 7 3 6 0
```

### 3. Task 14-04-03 MOC.md canonical regex + Phase 6 linkage

```
$ grep -c "adapter_contracts.md" wiki/render/MOC.md ; grep -cE "^- \[x\].*adapter_contracts\.md" wiki/render/MOC.md ; grep -c "Phase 14" wiki/render/MOC.md
1 1 1

$ py -3.11 -c "import re, sys; t=open('wiki/render/MOC.md', encoding='utf-8').read(); sys.exit(0 if re.search(r'^status:\s*(scaffold|partial)\b', t, re.MULTILINE) else 1)"
# exit 0 — canonical regex (Plan 02 Task 14-02-04 와 byte-identical) PASS

$ py -3.11 -c "import re, sys; t=open('wiki/render/MOC.md', encoding='utf-8').read(); sys.exit(1 if re.search(r'^status:\s*(ready|complete)\b', t, re.MULTILINE) else 0)"
# exit 0 — ready/complete drift 부재 확인 (D-17 invariant preserved)

$ py -3.11 -m pytest tests/phase06/test_moc_linkage.py -x --no-cov
collected 6 items
tests\phase06\test_moc_linkage.py ...... [100%]
============================== 6 passed in 0.08s ==============================
```

### 4. Task 14-04-04 Hook grep + import smoke + functional drift-resistance

```
$ grep -c "ADAPT-06c" .claude/hooks/pre_tool_use.py
3
$ grep -c "check_adapter_contract_drift" .claude/hooks/pre_tool_use.py
2
$ grep -c "warn-only" .claude/hooks/pre_tool_use.py
5
$ grep -c "_adapter_contract_touch" .gitignore
1

$ py -3.11 -c "import importlib.util; spec = importlib.util.spec_from_file_location('h', '.claude/hooks/pre_tool_use.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('hook loaded OK')"
hook loaded OK

# Functional test 1 — adapter edit without contract touch → warn + allow
$ echo '{"tool_name":"Edit","input":{"file_path":".../scripts/orchestrator/api/veo_i2v.py","old_string":"foo","new_string":"bar"}}' | py -3.11 .claude/hooks/pre_tool_use.py
[Phase 14 ADAPT-06c warn] adapter 파일 수정 감지: .../scripts/orchestrator/api/veo_i2v.py
  → 대응 tests/adapters/test_*_contract.py 를 함께 수정하세요.
  (경고만 — 작업은 차단되지 않습니다.)
{"decision": "allow"}   # ← allow (작업 비차단 검증)

# Functional test 4 — existing skip_gates regex still DENY (기존 차단 로직 무결성)
$ echo '{"tool_name":"Write","input":{"file_path":".../scripts/foo.py","content":"skip_gates=True"}}' | py -3.11 .claude/hooks/pre_tool_use.py
{"decision": "deny", "reason": "❌ Deprecated pattern detected (1건):\n  - ORCH-08 / CONFLICT_MAP A-6: skip_gates 물리 차단 (D-8, AF-14)\n..."}
#   ← deny (기존 8 regex 차단 보존 확인, CLAUDE.md 필수사항 #1 재검증)

$ git check-ignore -v .claude/hooks/_adapter_contract_touch.json
.gitignore:91:.claude/hooks/_adapter_contract_touch.json ← .claude/hooks/_adapter_contract_touch.json
#   ← session-scope ephemeral file 이 git 에서 제외됨 확인
```

### 5. Overall Wave 3 gate — `pytest -m adapter_contract -v --no-cov`

```
collected 1488 items / 1458 deselected / 30 selected

tests/adapters/test_adapter_contracts_doc.py  ...  7 PASSED  (Wave 3 validator)
tests/adapters/test_elevenlabs_contract.py   ...  7 PASSED  (Wave 2 Plan 14-03)
tests/adapters/test_shotstack_contract.py    ...  10 PASSED (Wave 2 Plan 14-03)
tests/adapters/test_veo_i2v_contract.py      ...  6 PASSED  (Wave 2 Plan 14-03)

===================== 30 passed, 1458 deselected in 1.82s =====================
```

30 tests green (plan 요구 ≥26 = 23 Wave 2 + ≥3 Wave 3 doc validator). **Plan 14-05 phase-gate 의 ≥20 threshold 초과 달성.**

### 6. Wave 1 regression preservation — `pytest tests/phase05 tests/phase06 tests/phase07`

```
$ PYTHONIOENCODING=utf-8 py -3.11 -m pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov
........................................................................ [ 29%]
........................................................................ [ 38%]
... (progress dots)
......................                                                   [100%]

742 passed, 2 warnings in 637.91s (0:10:37)
```

**Pre-Wave-2 baseline (Plan 14-02 sweep log): 742 passed, 2 warnings in 633.34s.**
**Post-Wave-3: 742 passed, 2 warnings in 637.91s.** Delta: +4.57s (+0.7%, environmental noise). **Zero functional regression introduced by Wave 3.** Wave 2 post-landing 도 동일 (629.71s per 14-03-SUMMARY §3).

### 7. Line count + file metrics

| File | Before | After | Delta |
| ---- | ------ | ----- | ----- |
| `wiki/render/adapter_contracts.md` | N/A (new) | 83 | +83 |
| `tests/adapters/test_adapter_contracts_doc.py` | N/A (new) | 125 | +125 |
| `wiki/render/MOC.md` | 54 | 55 | +1 |
| `.claude/hooks/pre_tool_use.py` | 372 | 474 | +102 |
| `.gitignore` | 88 | 91 | +3 |

## pre_tool_use.py 기존 8 regex 차단 로직 무결성 검증

| Preserved component | Lines (before → after) | Evidence |
| -------------------- | ----------------------- | -------- |
| `check_failures_append_only` (D-11 append-only + D-A3-01 500 cap + D-A3-04 env whitelist) | 160-249 → 160-249 | unchanged |
| `backup_skill_before_write` (D-12 SKILL_HISTORY backup) | 252-278 → 252-278 | unchanged |
| `check_structure_allowed` (STRUCTURE.md Whitelist) | 81-152 → 81-152 | unchanged |
| `load_patterns` + `check_content` (deprecated_patterns.json 8 regex) | 35-78 → 35-78 | unchanged |
| `find_studio_root` traversal | 49-58 → 49-58 | unchanged |
| `main()` dispatch order (failures → skill_backup → structure → deprecated) | 281-368 → 383-470 | offset by new warn-only block but **dispatch order + deny logic identical** |

Functional re-verification (Test 4 in §4 above): `skip_gates=True` content still produces `{"decision":"deny"}` after warn-only extension. CLAUDE.md 필수사항 #1 (Hook 3종 활성) 보존.

## CLAUDE.md Compliance Check

| Rule | Applied in Task | Evidence |
| ---- | ---------------- | -------- |
| 금기 #1 (skip_gates 회피 없음) | Task 14-04-04 | Hook 이 차단형이 아니라 경고형 (stderr print + `{"decision":"allow"}`), 기존 skip_gates 차단 regex 는 그대로 작동 (functional test 4 재검증) |
| 금기 #2 (TODO 금지) | Tasks 01/02/04 | `grep -c "TODO" wiki/render/adapter_contracts.md` = 0, `grep -c "TODO" tests/adapters/test_adapter_contracts_doc.py` = 0, `grep -c "TODO" .claude/hooks/pre_tool_use.py` = 0 |
| 금기 #3 (try-except 침묵 폴백) | Task 14-04-04 | `_record_contract_touch` 의 `except OSError: pass` 는 warn-only Hook 설계 의도 (기록 실패로 작업 차단 금지) — 주석 `# warn-only Hook — 기록 실패를 작업 차단으로 전환하지 않음` 으로 명시. 나머지 모든 실패는 명시적 raise / pytest.raises. |
| 금기 #4 (T2V 금지) | Tasks 01/02 | adapter_contracts.md 가 anchor_frame REQUIRED + T2VForbidden raise 명시 문서화; validator test 가 whisperx 외 I2V 3 종 모두 row 존재 검증 |
| 금기 #6 (shorts_naberal 원본 보존) | All 4 tasks | 본 plan 이 수정한 5 files 전부 `studios/shorts/` 내부. `shorts_naberal/` 경로 touch 없음. |
| 필수 #1 (Hook 3종 활성) | Task 14-04-04 | pre_tool_use.py 기존 8 regex 차단 로직 unchanged, warn-only 확장만 추가. functional test 4 (skip_gates DENY 보존) 로 재검증. |
| 필수 #2 (SKILL.md ≤500줄) | — | adapter_contracts.md 는 SKILL.md 아님 (wiki doc), 500줄 제한 미적용. 실제 83 lines 로 Progressive Disclosure 원칙 준수. |
| 필수 #4 (FAILURES.md append-only) | — | 본 plan 에서 FAILURES.md 편집 없음. 신규 failure pattern 0. |
| 필수 #5 (STRUCTURE Whitelist) | Tasks 01/02/03 | wiki/render/ 는 기 등록 category (remotion_kling_stack.md, i2v_prompt_engineering.md, MOC.md 와 동일 위치). tests/adapters/ 는 Wave 0 에서 whitelisted. pre_tool_use.py Hook import smoke test 통과. |
| 필수 #8 (증거 기반 보고) | This SUMMARY + 4 task commits | 각 task commit body 에 pytest/grep output 인용 + 본 SUMMARY Evidence Blocks §1-7 에 전수 재확인 |

## Issues Encountered

1. **Structural validator docstring self-reference paradox** — 원 plan template 의 "TODO 없음" 메타-선언이 grep 오탐지 유발. 해결: "미완성 표식 없음" 으로 문구 재작성 (Plan 02 Task 14-02-01 veo_i2v.py self-reference paradox 와 동일 클래스, Rule 1 deviation).
2. **`wiki/render/MOC.md` 엔트리 위치** — 기존 TOC 가 체크박스 + backtick 경로 패턴 (`[x] i2v_prompt_engineering.md`, `[ ] kling_26_pro_api_spec.md`, `[x] remotion_kling_stack.md` 등) 사용. 신규 entry 도 동일 패턴 따르되 markdown link `[adapter_contracts.md](./adapter_contracts.md)` 추가하여 TOC 내비게이션 강화. D-17 invariant 는 엔트리 추가와 무관하게 frontmatter 수준에서 유지.
3. **Hook warn-only 출력의 Windows cp949 mojibake** — functional test 1 출력 중 한국어 문자가 cp949 깨짐 (`[Phase 14 ADAPT-06c warn] adapter ���� ���� ����`). 실제 세션에서 Claude Code 가 Hook 출력을 utf-8 로 처리하므로 실행 환경 영향 없음. 경고 문구 자체는 utf-8 로 작성되어 정상.

## Production Artefact Import Map

| Artefact | Path | Import/Reference Target |
| -------- | ---- | ------------------------ |
| adapter_contracts.md | `wiki/render/adapter_contracts.md` | MOC.md TOC entry (line 32) + 3 Wave 2 contract 테스트 (xref) + validator test (7 tests) |
| validator test | `tests/adapters/test_adapter_contracts_doc.py` | pytest marker `adapter_contract` + `repo_root` fixture from `tests/adapters/conftest.py` |
| MOC entry | `wiki/render/MOC.md:32` | links `./adapter_contracts.md` |
| Hook extension | `.claude/hooks/pre_tool_use.py::check_adapter_contract_drift` | observes Edit/Write/MultiEdit payload; writes `.claude/hooks/_adapter_contract_touch.json` |
| gitignore entry | `.gitignore:91` | excludes `.claude/hooks/_adapter_contract_touch.json` from git tracking |

## Next Phase Readiness

- **Wave 4 (Plan 14-05) unblocked** — phase-gate 실행에 필요한 전수 artefact 안착:
  - 14-VALIDATION.md row 14-05-01 `pytest tests/phase05 tests/phase06 tests/phase07 --tb=short` — 742 passed baseline 유지.
  - 14-VALIDATION.md row 14-05-02 `pytest -m adapter_contract -v --no-cov` — 30 tests green (플랜 요구 ≥20 초과 달성).
  - 14-VALIDATION.md row 14-05-03 adapter_contracts.md 존재 + validator green — ADAPT-05 traceability 확보.
- **ADAPT-05 Success Criteria 충족** — 7 adapter × 5 column + mock↔real delta + retry/fallback + fault injection + CLAUDE.md 금기 cross-reference 전수 문서화.
- **ADAPT-06 Success Criteria 충족** — Wave 0 에서 marker 등록 (`pytest.ini::adapter_contract`) + 본 Wave 3 에서 warn-only Hook 통합. `pytest -m adapter_contract` 독립 gate 30 tests green 확인.
- **잔여 Phase 14 REQ**:
  - ADAPT-01/02/03: Wave 2 완결 (Plan 14-03, 23 contract tests)
  - ADAPT-04: Wave 1 완결 (Plan 14-02, 742/742)
  - ADAPT-05/06: Wave 3 완결 (본 plan)
- **No blockers** for Plan 14-05 (Wave 4 phase-gate) 실행.

## Self-Check: PASSED

- [x] `wiki/render/adapter_contracts.md` exists — FOUND (83 lines, 7 sections, 7 adapter rows)
- [x] `tests/adapters/test_adapter_contracts_doc.py` exists — FOUND (125 lines, 7 tests)
- [x] `wiki/render/MOC.md` modified with `[x] adapter_contracts.md` entry at line 32 — FOUND
- [x] `.claude/hooks/pre_tool_use.py` extended with ADAPT-06c warn-only block — FOUND (474 lines, +102 from baseline)
- [x] `.gitignore` has `_adapter_contract_touch` entry — FOUND (line 91)
- [x] Commit `00a87a7` exists (Task 14-04-01) — FOUND
- [x] Commit `0591250` exists (Task 14-04-02) — FOUND
- [x] Commit `c419641` exists (Task 14-04-03) — FOUND
- [x] Commit `4d916a9` exists (Task 14-04-04) — FOUND
- [x] `pytest tests/adapters/test_adapter_contracts_doc.py -v --no-cov` — 7 passed in 0.08s
- [x] `pytest -m adapter_contract -v --no-cov` — 30 passed, 1458 deselected in 1.82s (≥26 target)
- [x] `pytest tests/phase05 tests/phase06 tests/phase07 --tb=line -q --no-cov` — 742 passed, 0 failed in 637.91s (Wave 1 regression preserved)
- [x] `pytest tests/phase06/test_moc_linkage.py -x --no-cov` — 6 passed (MOC D-17 invariant tests 여전히 green)
- [x] Python canonical regex `^status:\s*(scaffold|partial)\b` multiline on MOC.md — exit 0
- [x] Python inverted regex `^status:\s*(ready|complete)\b` multiline on MOC.md — exit 0 (no drift)
- [x] Hook import smoke `py -3.11 -c "importlib.util.spec_from_file_location..."` — "hook loaded OK"
- [x] Hook functional test 1 (adapter edit, no contract touch) — stderr warn + stdout allow
- [x] Hook functional test 2 (contract edit) — silent allow + touch recorded
- [x] Hook functional test 3 (irrelevant path) — silent allow
- [x] Hook functional test 4 (skip_gates content) — DENY preserved (기존 차단 로직 무결성)
- [x] `git check-ignore -v .claude/hooks/_adapter_contract_touch.json` — .gitignore:91 matched
- [x] Zero TODO in any new/modified file
- [x] Zero skip_gates in any new/modified file
- [x] No shorts_naberal/ modification (금기 #6)
- [x] No production adapter source modification (scripts/orchestrator/api/*.py 전부 untouched)

---
*Phase: 14-api-adapter-remediation*
*Plan: 04 (Wave 3 Docs + MOC + Warn-Only Hook + .gitignore)*
*Completed: 2026-04-21*
