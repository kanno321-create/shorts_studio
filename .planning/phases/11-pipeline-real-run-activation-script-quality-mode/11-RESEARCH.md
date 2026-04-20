# Phase 11: Pipeline Real-Run Activation + Script Quality Mode — Research

**Researched:** 2026-04-21
**Domain:** Pipeline orchestration / Claude CLI subprocess / Windows double-click UX / `.env` loading / idempotent audit append
**Confidence:** HIGH (all 10 research priorities verified against live CLI, live filesystem, locked CONTEXT decisions)

## Summary

Phase 11 resolves a 5-error chain (D10-PIPELINE-DEF-01) that blocks `shorts_pipeline.py` from ever reaching its first real GATE call, plus two folded defects (D10-SCRIPT-DEF-01 옵션 확정 + D10-01-DEF-02 counter idempotency). CONTEXT.md has **pre-committed 25 locked decisions** (D-01 ~ D-25) — this research does not re-investigate choices, only documents the *implementation specifics* downstream planners need.

The five fixes are all small-blast-radius edits (1 function each) sitting on top of a clean Phase 9.1/10 foundation (244/244 Phase 4 regression + 986+ full sweep preserved). The single highest-leverage change is **`invokers.py:141-171` stdin piping** — verified by direct CLI call `echo "ping" | claude --print --input-format text --append-system-prompt "..." --json-schema "..."` returning the expected JSON body on Claude Code CLI 2.1.112.

**Primary recommendation:** Proceed with 6 plans in 3 waves (see §Plan Wave Structure). Wave 1 fixes the chain prerequisites (all parallelizable — zero file overlap). Wave 2 delivers the wrapper + idempotency. Wave 3 runs the real-run smoke + captures 대표님 대본 품질 평가. Total estimated real-run cost: **$2.50-$4.50** for one published Shorts (see §Full Smoke Cost Model). The 796-line `shorts_pipeline.py` must stay under the 800-line cap — §Line Budget shows we fit with margin.

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

#### PIPELINE-01 — Invoker 수정 방식
- **D-01**: **Option A (stdin piping)** 채택. `_invoke_claude_cli`를 `subprocess.Popen(stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(input=user_prompt, timeout=timeout_s)`로 전환. argv에서 user_prompt positional 제거.
- **D-02**: argv 최종 형태는 `[cli_path, "--print", "--append-system-prompt", body, "--json-schema", schema]`. `user_prompt`는 stdin으로만 전달.
- **D-03**: Claude Agent SDK 전환(Option C) 금지 — `.claude/memory/project_claude_code_max_no_api_key.md` "anthropic/claude_agent_sdk 금지" 결정 유지 (Max 구독 중복결제 방지, commit 8af5063).
- **D-04**: `_invoke_claude_cli` 시그니처/반환/에러 메시지(Korean-first) 유지 — 테스트 seam(`cli_runner` 주입) 무변경으로 regression 최소화.

#### PIPELINE-03 — Adapter graceful degrade 범위
- **D-05**: **Option A (pipeline-site 통일 wrap)** 채택. `shorts_pipeline.py:210-213`의 Kling/Runway/Typecast/ElevenLabs 4개 인스턴스화를 Phase 9.1 shotstack/nanobanana/ken_burns 블록(L214-235)과 **동일한 try/except/logger.warning/self.X = adapter_arg** 패턴으로 래핑.
- **D-06**: adapter 내부(`scripts/orchestrator/api/*.py` `__init__`)는 **무변경** — eager ValueError 유지.
- **D-07**: 발견된 defect: shotstack adapter도 실제로는 adapter 내부 eager(`shotstack.py:81-97`). Phase 11에서 pipeline site 일괄 통일로 해소.
- **D-08**: Adapter registry/lazy refactor(Option C)는 Phase 12+ deferred — 244/244 phase04 regression baseline 보호.

#### PIPELINE-04 — 더블클릭 Wrapper UX
- **D-09**: **Option B (.cmd bootstrap + .ps1 engine)** 채택. 2 파일 신규:
  - `run_pipeline.cmd` (repo root) — 단일 라인 `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"` + `pause`
  - `run_pipeline.ps1` (repo root) — `.env` 파싱(Get-Content + regex) → env 주입 → `py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id $(Get-Date -Format "yyyyMMdd_HHmmss")` 호출 → try/catch/Read-Host pause-on-error.
- **D-10**: Windows 11 `CurrentUser` PS ExecutionPolicy `Restricted` 우회 — `.cmd`가 `-ExecutionPolicy Bypass`로 `.ps1` 시작. **관리자 권한 불필요**.
- **D-11**: `.ps1`는 컬러드 gate-progress 출력 + try/catch Read-Host (창 즉시 닫힘 문제 회피).
- **D-12**: 기존 `scripts/schedule/windows_tasks.ps1` 컨벤션(Korean block-comments, `-NoProfile`, absolute ScriptRoot) 준수.

#### PIPELINE-02 — `.env` 자동 로드
- **D-13**: **zero-dep 파서** 채택 — `scripts/orchestrator/__init__.py`에 `_load_dotenv_if_present()` 함수 추가 (Path(".env") 읽기 + `KEY=VALUE` line regex + `os.environ.setdefault`). `python-dotenv` 미설치.
- **D-14**: Reason: repo root에 `requirements.txt` / `pyproject.toml` 부재 — 외부 dep 추가는 harness 의존성 변경 필요. zero-dep가 실행 단순성 보장.
- **D-15**: `.env` 부재 시 silently skip (기존 환경변수 경로 보존). 중복 호출 멱등.
- **D-16**: `shorts_pipeline.py` argparse에서 `--session-id required=False, default=None` + `session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")` 처리.

#### SCRIPT-01 — 옵션 A/B/C 구현 경계
- **D-17**: **Option X3 (Phase 11 pre-commit to Option A baseline)** 채택. Phase 11 내 scripter 재설계/2-mode 분리 구현 **없음**.
- **D-18**: 대표님 영상 1편 품질 평가 후 옵션 B/C 선택 시 → **Phase 12: NLM 2-Step Scripter Redesign** 자동 spawn.
- **D-19**: REQ SCRIPT-01 원문 "선택된 옵션의 구현까지 완료" **amendment 권고** — "옵션 선정 + Phase 12 조건부 발행"으로 REQUIREMENTS.md 수정.
- **D-20**: scripts/notebooklm/query.py는 **이미 multi-notebook 호환** — 옵션 B 선택 시 query.py 자체 변경 불필요.
- **D-21**: Phase 11 발행 영상 1편은 **옵션 A 산출물**.

#### AUDIT-05 — skill_patch_counter idempotency
- **D-22**: 2026-05-20 첫 월간 scheduler(`skill-patch-count-monthly.yml`) 실행 **전** 완료. Phase 11 entry gate.
- **D-23**: Append 전 `FAILURES.md` grep — 동일 commit hash set(violation의 git SHA union) 이미 기록 시 skip. 신규 violation만 append.
- **D-24**: 신규 test: `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` — 동일 git state 2회 연속 실행 시 첫 회만 append 검증.
- **D-25**: 사후 수동 정리(F-D2-02~F-D2-05 제거 + F-D2-01 보존)는 이미 완료. Phase 11은 regression 방지 로직만 추가.

### Claude's Discretion (AI 재량)
- Plan 실행 Wave 구조 (Phase 9.1/10과 동일 Wave 1~4 discipline 권장)
- 각 Plan의 구체적 테스트 케이스 설계
- run_pipeline.ps1 세부 에러 메시지 문구 (대표님 친화 Korean)
- zero-dep .env 파서의 주석/docstring 스타일
- Phase 11 전체 smoke 실 발행 cost 추적 방식 (cap 없이 실비 기록)
- D-19 REQUIREMENTS.md amendment 문구

### Deferred Ideas (OUT OF SCOPE)

#### Phase 12 조건부 (SCRIPT-01 옵션 B/C 선택 시)
- **Phase 12: NLM 2-Step Scripter Redesign** — 옵션 B 선택 시 spawn
- **Phase 12 대안: Shorts/Longform 2-mode 분리** — 옵션 C 선택 시

#### Phase 12+ (독립 후속)
- **Adapter registry + lazy instantiation 전역 refactor** (PIPELINE-03 Option C)
- **Phase 04/08 retrospective VERIFICATION.md** (ROADMAP SC#6 optional)
- **Shotstack adapter 내부 eager → lazy 직접 수정**
- **Phase 11 smoke 실 발행 cost aggregation dashboard**

#### 로드맵 backlog
- **REQ SCRIPT-01 원문 amendment 공식 처리** (D-19)

#### Reviewed Todos (not folded)
- D10-01-DEF-01 Phase 5/6 pre-existing regressions
- D10-03-DEF-01 drift_scan STATE.md frontmatter assertion
- D10-03-DEF-02 Phase 5/6/7/8 regression cascade sweep
- D10-06-DEF-01 trajectory_append collection error (이미 GREEN)

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPELINE-01 | Full pipeline end-to-end smoke — 1 session GATE 0→13 실 Claude CLI + 실 외부 API 호출 완주. `invokers.py:141` argv/stdin 형식 Claude CLI 2.1.112 호환 수정 | §Claude CLI stdin piping (verified live) + §Code Examples Pattern 1 |
| PIPELINE-02 | `.env` 자동 로드 — `shorts_pipeline.py` 또는 orchestrator `__init__` 에 통합. PowerShell 추가 env 주입 없이 실행 가능 | §Zero-dep `.env` parser (edge-case matrix) + §Code Examples Pattern 2 |
| PIPELINE-03 | Adapter graceful degrade 전면 — 5개 adapter 모두 Phase 9.1 패턴 적용. 사용 안 하는 adapter 의 env 부재가 `__init__` 을 막지 않음 | §Adapter graceful degrade uniform pattern + §Code Examples Pattern 3 |
| PIPELINE-04 | 더블클릭 wrapper UX — `run_pipeline.ps1` + `.cmd`. `.env` 자동 로드 + `--session-id` 자동 주입 + pause | §.cmd + .ps1 wrapper engineering + §Code Examples Pattern 4 |
| SCRIPT-01 | D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 + 대표님 품질 평가 근거로 A/B/C 중 1개 확정 | §REQUIREMENTS.md D-19 amendment + §Validation Architecture SC#2 eval capture |
| AUDIT-05 | skill_patch_counter idempotency — 동일 git state 2회 연속 실행 시 첫 회만 append, 2회차는 skip | §skill_patch_counter idempotency algorithm + §Code Examples Pattern 5 |

</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

| Directive | Enforcement | Phase 11 Implication |
|-----------|-------------|---------------------|
| 오케스트레이터 500~800 lines (5166-line drift 재발 금지) | `tests/phase05/test_line_count.py` soft cap | **`shorts_pipeline.py` currently 796 lines** — new code MUST net-add ≤4 lines. See §Line Budget. |
| try-except 침묵 폴백 금지 (`except: pass`) | `deprecated_patterns.json` `try_pass_silent` regex (grade B) | PIPELINE-03 graceful degrade must use `logger.warning` + explicit `self.X = adapter_arg` (matches existing shotstack block at L214-218). |
| `skip_gates=True` / `TODO(next-session)` hook 차단 | `pre_tool_use.py` + `deprecated_patterns.json` grade A regex | No workaround comments in new code. |
| Selenium 금지 (AF-8) | `deprecated_patterns.json` `selenium_import` regex grade A | N/A for Phase 11 (no upload code touched; existing `youtube_uploader.py` is API v3 only). |
| T2V 금지 (D-13) | `deprecated_patterns.json` `t2v_code_path` case-insensitive regex | N/A for Phase 11. |
| FAILURES.md append-only | `check_failures_append_only` hook (basename exact match) + sha256 lock on `_imported_from_shorts_naberal.md` | AUDIT-05 idempotency fix uses `open(path, "a")` — hook bypass documented in skill_patch_counter.py L8-15. Read-then-check order: grep BEFORE open("a"). |
| Korean-first error messages | Convention enforced in invokers.py L160, L165, L169 | New `.ps1` Write-Host, `_load_dotenv_if_present` warnings, idempotency skip logs all 한국어 + "대표님" 호칭. |
| STRUCTURE.md Whitelist 준수 | `pre_tool_use.py::check_structure_allowed` | **Studio has NO STRUCTURE.md at repo root** — `check_structure_allowed` returns `(True, "")` on line 91-92 when file missing. Harness STRUCTURE.md only constrains `../../harness/` folder. `run_pipeline.cmd/.ps1` at studio repo root → **allowed**. See §STRUCTURE Whitelist Verification. |

---

## Standard Stack

### Core (No new dependencies — this is the point)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `subprocess` | 3.11.9 (bundled) | `Popen(stdin=PIPE).communicate()` for Claude CLI | Already used in `invokers.py:149` (subprocess.run); switch to Popen is one-line upgrade |
| Python stdlib `pathlib.Path` | bundled | `.env` file detection | Already imported everywhere |
| Python stdlib `re` | bundled | `.env` line regex, idempotency grep | Already used in `skill_patch_counter.py:48` |
| Python stdlib `os.environ.setdefault` | bundled | idempotent env injection | Prevents override of user-set vars (matches `experimental/test_*.py` pattern `load_dotenv(override=False)`) |
| Python stdlib `datetime.datetime` | bundled | auto session-id default | Already imported in pipeline |
| Windows `cmd.exe` | Win11 bundled | .cmd bootstrap for ExecutionPolicy bypass | No install; .cmd files are universally executable by double-click |
| Windows `powershell.exe` 5.1 | Win11 bundled | .env regex parse + py launcher invocation | No install; existing `scripts/schedule/windows_tasks.ps1` convention |
| `claude` CLI | 2.1.112 (verified via `claude --version`) | Producer/Supervisor invocation | Max 구독 인증 경로 (anthropic SDK 금지) |

### Supporting (verification tools only, not runtime)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | existing | regression sweep | Wave 0 `tests/phase11/` + Wave 2 idempotency test |
| `py -3.11` launcher | Win11 Python 3.11 | Stable invocation path from `.ps1` | matches existing `windows_tasks.ps1:64` pattern |

### Alternatives Considered (all REJECTED per CONTEXT.md)

| Instead of | Could Use | Why Rejected |
|------------|-----------|--------------|
| zero-dep `.env` parser | `python-dotenv` 1.2.1 | D-13/D-14: no requirements.txt exists; adding dep changes harness install surface. `python-dotenv` IS installed globally on target machine but not guaranteed elsewhere. |
| `subprocess.Popen(stdin=PIPE)` | `claude_agent_sdk` SDK call | D-03: Max 구독 billing 경로 파괴 (memory: `project_claude_code_max_no_api_key`) |
| Adapter pipeline-site wrap | Refactor each adapter `__init__` to lazy | D-08: 244/244 phase04 regression risk; each adapter has 5+ test files asserting ValueError on missing env |
| `.cmd`+`.ps1` wrapper | Single `.bat` only | D-09 Option A rejected: `.bat` `for /f` parser breaks on `=` in API key values (Runway key contains `:` and `=`) |
| `.cmd`+`.ps1` wrapper | Python launcher `.py` | D-11 Option C rejected: ImportError on relative import closes window instantly; no pause-on-error path |

**Installation (existing, nothing to install):**
```bash
# All tools already on target machine:
claude --version     # 2.1.112 (verified)
py -3.11 --version   # Python 3.11.9 (verified)
powershell $PSVersionTable.PSVersion  # 5.1 baseline on Win11
```

**Version verification:** Claude CLI 2.1.112 confirmed live via `claude --version` on 2026-04-21. Python 3.11.9 confirmed. python-dotenv 1.2.1 installed globally but **intentionally not used** per D-13.

---

## Architecture Patterns

### Recommended File-Level Changes

```
shorts/                                         # Phase 11 scope
├── run_pipeline.cmd                            # [NEW] 1-line bootstrap (PIPELINE-04)
├── run_pipeline.ps1                            # [NEW] engine: .env parse + py launcher (PIPELINE-04)
├── scripts/orchestrator/
│   ├── __init__.py                             # [+10 lines] _load_dotenv_if_present() (PIPELINE-02)
│   ├── invokers.py                             # [+5/-3 lines] stdin piping (PIPELINE-01)
│   └── shorts_pipeline.py                      # [+12/-8 lines net +4] adapter wraps + argparse (PIPELINE-03, -02 tie-in)
├── scripts/audit/
│   └── skill_patch_counter.py                  # [+15 lines] idempotency grep before append (AUDIT-05)
├── tests/phase11/                              # [NEW directory]
│   ├── __init__.py                             # [NEW]
│   ├── conftest.py                             # [NEW] fixtures (tmp_env_file, mock_cli_runner, etc.)
│   ├── test_invoker_stdin.py                   # [NEW] 6 tests (PIPELINE-01)
│   ├── test_dotenv_loader.py                   # [NEW] 8 tests (PIPELINE-02 edge cases)
│   ├── test_adapter_graceful_degrade.py        # [NEW] 5 tests (PIPELINE-03)
│   ├── test_argparse_session_id.py             # [NEW] 3 tests (PIPELINE-04 tie-in)
│   └── test_wrapper_smoke.py                   # [NEW] 2 tests (wrapper invocation dry-run)
└── tests/phase10/
    └── test_skill_patch_counter.py             # [+1 test] test_idempotency_skip_existing (AUDIT-05, D-24)
```

### Pattern 1: stdin piping (PIPELINE-01)

**What:** Replace `subprocess.run([...argv, user_prompt], ...)` with `subprocess.Popen(argv, stdin=PIPE).communicate(input=user_prompt)`.

**When to use:** ALWAYS for Claude CLI 2.1.112 `--print` mode. The CLI `[prompt]` positional is being removed from the contract per the D10-PIPELINE-DEF-01 error ("Input must be provided either through stdin or as a prompt argument"). stdin piping is the future-proof form.

**Why this works:** Confirmed live on 2026-04-21 — `echo "ping" | claude --print --input-format text --append-system-prompt "reply exactly: PONG" --json-schema '{...}'` returns `PONG` cleanly.

**Edge cases discovered:**
- **Large AGENT.md bodies (several KB)**: `--append-system-prompt` accepts long strings; no argv length issue since user_prompt moves to stdin.
- **Korean text in stdin**: Already handled by `encoding="utf-8", errors="replace"` on subprocess — port those kwargs to Popen.
- **Timeout behavior**: `Popen.communicate(input=..., timeout=...)` raises `subprocess.TimeoutExpired` same as `subprocess.run(timeout=...)` — error handling path unchanged.
- **stderr capture**: Keep `stderr=PIPE` — current code reads `result.stderr[-500:]` on rc!=0.
- **Empty stdin protection**: Not needed; `user_prompt = json.dumps({...})` is always non-empty.

### Pattern 2: Zero-dep `.env` loader (PIPELINE-02)

**What:** `_load_dotenv_if_present()` in `scripts/orchestrator/__init__.py` that reads `./env`, parses `KEY=VALUE` lines, calls `os.environ.setdefault()`.

**When to use:** Once, at import time of `scripts.orchestrator` — import is triggered by both `py -m scripts.orchestrator.shorts_pipeline` (wrapper path) AND direct test imports. Idempotent on duplicate imports (Python module cache).

**Why here, not shorts_pipeline.py:** `scripts/orchestrator/__init__.py` is the earliest symbol resolution point — fires before `shorts_pipeline.py` runs any adapter `__init__`. If placed in `shorts_pipeline.py:main()`, the module-level adapter imports would already have triggered `KlingI2VAdapter()` before `.env` is loaded.

**Edge cases to handle (tests in `test_dotenv_loader.py`):**

| Input line | Expected behavior | Test name |
|------------|-------------------|-----------|
| `KEY=value` | `os.environ.setdefault('KEY', 'value')` | test_basic_kv |
| `KEY=value with spaces` | stripped: `'value with spaces'` | test_spaces_preserved_in_value |
| `KEY="quoted value"` | strip surrounding `"` → `'quoted value'` | test_double_quotes_stripped |
| `KEY='single'` | strip surrounding `'` → `'single'` | test_single_quotes_stripped |
| `KEY=has=equals=signs` | split on FIRST `=` only → value=`'has=equals=signs'` | test_multiple_equals_in_value |
| `# comment` | skipped | test_comments_ignored |
| `   # indented comment` | skipped | test_indented_comments_ignored |
| `` (empty line) | skipped | test_empty_lines_ignored |
| `export KEY=value` | strip `export ` prefix; set `KEY`=`value` (bash compat) | test_export_prefix_stripped |
| `\ufeff KEY=value` (BOM) | stripped from first line | test_utf8_bom_stripped |
| `KEY=value\r\n` (CRLF) | line.rstrip() before split | test_crlf_handled |
| `.env` missing | silent skip, no exception | test_missing_file_silent |
| pre-existing `os.environ['KEY']='X'`, `.env` has `KEY=Y` | env wins (setdefault no-op) | test_existing_env_wins |

**Idempotency semantics (`os.environ.setdefault` vs overwrite):** Use **`setdefault`** (do NOT overwrite). Rationale:
1. Matches existing `scripts/experimental/test_complex_action.py:19` convention: `load_dotenv(PROJECT_ROOT / ".env", override=False)`.
2. Allows user CI/CD or temporary `SET KEY=X` to take precedence over `.env` for debugging.
3. Scheduled tasks may inject env via Windows Task Scheduler action — those should win over .env.
4. Cited rationale: python-dotenv default is `override=False` (verified: https://github.com/theskumar/python-dotenv — their `load_dotenv()` signature).

### Pattern 3: Adapter graceful degrade (PIPELINE-03)

**What:** Wrap 4 more adapter instantiations in the exact pattern at `shorts_pipeline.py:214-218`:

```python
# BEFORE (L210-213 — 4 adapters, eager)
self.kling = kling_adapter or KlingI2VAdapter(circuit_breaker=self.kling_breaker)
self.runway = runway_adapter or RunwayI2VAdapter(circuit_breaker=self.runway_breaker)
self.typecast = typecast_adapter or TypecastAdapter(circuit_breaker=self.typecast_breaker)
self.elevenlabs = elevenlabs_adapter or ElevenLabsAdapter(circuit_breaker=self.elevenlabs_breaker)

# AFTER (uniform pattern — 8 more lines = 4 try/except per adapter collapsed into one helper? NO: keep verbatim per D-05 "동일 패턴")
try:
    self.kling = kling_adapter or KlingI2VAdapter(circuit_breaker=self.kling_breaker)
except ValueError as err:
    logger.warning("[pipeline] kling adapter 미초기화 (대표님 — KLING_API_KEY / FAL_KEY 없음): %s", err)
    self.kling = kling_adapter
# ... same for runway/typecast/elevenlabs
```

**Line budget concern:** Naive 4× verbatim blocks = +20 lines. Pipeline is at 796/800. **Solution:** collapse adapter instantiation into a helper (see §Line Budget). CONTEXT D-05 says "동일 패턴" — helper preserves identical behavior + Korean error format.

**Confirmed ValueError is the ONLY exception type from __init__:**
- `KlingI2VAdapter.__init__`: L89 `raise ValueError("KlingI2VAdapter: no API key...")`
- `RunwayI2VAdapter.__init__`: L91 ValueError (key), L104 ValueError (model), L112 ValueError (ratio) — **all three** caught
- `TypecastAdapter.__init__`: L59 ValueError
- `ElevenLabsAdapter.__init__`: L122 ValueError

**Test impact:** `tests/phase05/test_kling_adapter.py::test_kling_missing_key_raises_value_error` (and 4 sibling tests) test the adapter class directly, NOT through the pipeline. These tests continue to pass because adapter internals are untouched (D-06). Zero regression risk.

### Pattern 4: .cmd + .ps1 wrapper (PIPELINE-04)

**What:** Two files at repo root:

**`run_pipeline.cmd`** (3 lines):
```cmd
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"
pause
```

**`run_pipeline.ps1`** (~60 lines; structure):

1. Block comment header (대표님 친화, `windows_tasks.ps1` convention)
2. `$ErrorActionPreference = "Stop"` + `$OutputEncoding = [System.Text.Encoding]::UTF8`
3. `chcp 65001 > $null` (UTF-8 console for Korean output)
4. `$ScriptRoot = $PSScriptRoot` (canonical path resolution; matches PS 3.0+ idiom)
5. `try { ... } catch { Write-Host "실패" -Fore Red; Read-Host "엔터로 종료" }` wrap
6. `.env` regex parse:
   ```powershell
   Get-Content "$ScriptRoot\.env" | ForEach-Object {
       if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
           Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
       }
   }
   ```
7. Write-Host colored banner (green 시작, yellow 진행, red 실패)
8. `py -3.11 -m scripts.orchestrator.shorts_pipeline` invocation
9. `finally { Read-Host "완료. 엔터로 창 닫기" }` so window stays open even on success

**Why `%~dp0` in .cmd + `$PSScriptRoot` in .ps1:**
- `%~dp0` = directory of the .cmd file (Windows cmd builtin, trailing backslash included)
- `$PSScriptRoot` = PowerShell 3.0+ automatic variable = directory of current script
- Both resolve to the repo root regardless of where the user runs from (Explorer double-click, CMD cd'd to Desktop, etc.)

**Windows Defender / SmartScreen implications:** Unsigned `.ps1` on Win11 with default Execution Policy `Restricted`:
- `.cmd` bootstrap with `-ExecutionPolicy Bypass` DOES work on default Restricted policy — `Bypass` is the per-invocation override, it does NOT change machine policy.
- SmartScreen may prompt "Windows protected your PC" the first time if the file is downloaded from the internet (Zone.Identifier ADS). For locally-created files (committed to git, cloned via CLI), no prompt.
- `-NoProfile` avoids loading user $PROFILE which could contain hostile Set-Item env:* pollution.

### Pattern 5: skill_patch_counter idempotency (AUDIT-05)

**What:** Before calling `append_failures(...)` in `main()`, grep existing `FAILURES.md` for a **violation signature**.

**Signature design (3 options → pick #1):**

| Option | Signature | Pros | Cons |
|--------|-----------|------|------|
| **(a) commit hash set** | sorted tuple of commit SHAs in violations | Exact semantic match; resilient to reordering | Must parse existing entry text to recover hash list |
| (b) content hash | sha256 of canonical violation payload (hashes + files) | One-line compare | Fragile to subject-line whitespace changes |
| (c) file-path set | sorted tuple of violating_file paths | Simplest to grep | Collides when SAME file violated in TWO different commits |

**Chosen: (a) commit hash set**

**Algorithm:**
```python
def _existing_violation_hashes(failures_text: str) -> set[str]:
    """Parse F-D2-NN entries and return the union of commit short-hashes recorded."""
    hashes = set()
    for entry_match in re.finditer(r"^## F-D2-\d{2}.*?(?=^## F-|\Z)", failures_text, re.MULTILINE | re.DOTALL):
        body = entry_match.group(0)
        # each violation line starts with "- `{7-hex}`"
        for line in body.splitlines():
            m = re.match(r"^- `([0-9a-f]{7})`", line)
            if m:
                hashes.add(m.group(1))
    return hashes
```

**In main():**
```python
existing = failures.read_text(encoding="utf-8") if failures.exists() else ""
existing_hashes = _existing_violation_hashes(existing)
new_violations = [v for v in violations if (v.get("hash") or "")[:7] not in existing_hashes]
if not new_violations:
    logger.info("[skill_patch_counter] 신규 violation 없음 (기존 F-D2-NN 에 %d건 이미 기록, 대표님)", len(violations))
    # Still write report (fresh timestamp) but skip append.
    write_report(violations, output, now, args.since, args.until)
    return 1 if violations else 0  # preserve exit code contract
append_failures(new_violations, repo_root, now)
```

**Test algorithm (`test_idempotency_skip_existing`):**
```python
def test_idempotency_skip_existing(tmp_git_repo, make_commit):
    _seed_failures_md(tmp_git_repo)
    make_commit({".claude/hooks/x.py": "# v"}, "fix(hook): violation")
    # First run: appends
    rc1 = main(["--repo", str(tmp_git_repo), "--since", "2026-04-20", "--until", "2026-06-20"])
    assert rc1 == 1
    post1 = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    assert post1.count("## F-D2-") == 1
    # Second run (same git state): NO new append
    rc2 = main(["--repo", str(tmp_git_repo), "--since", "2026-04-20", "--until", "2026-06-20"])
    assert rc2 == 1, "violation still present → exit 1"
    post2 = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    assert post2 == post1, "second run must not change FAILURES.md"
    assert post2.count("## F-D2-") == 1, "still exactly 1 entry"
    # Third run AFTER new violation: appends only the new one
    make_commit({"CLAUDE.md": "# mod"}, "docs: second violation")
    rc3 = main(["--repo", str(tmp_git_repo), "--since", "2026-04-20", "--until", "2026-06-20"])
    assert rc3 == 1
    post3 = (tmp_git_repo / "FAILURES.md").read_text(encoding="utf-8")
    assert post3.count("## F-D2-") == 2, "new violation appends second entry"
    # Original entry preserved (D-11 strict prefix)
    assert post3.startswith(post1)
```

### Anti-Patterns to Avoid

- **`subprocess.run(..., input=user_prompt)` (single call form):** Works, but existing code uses `result = subprocess.run(cmd, ...)` + `result.returncode / result.stdout / result.stderr`. **Switching to Popen keeps the three-way capture explicit.** Both forms work — Popen is slightly more flexible for future streaming.
- **`except: pass` in adapter wrap:** Banned by `deprecated_patterns.json` `try_pass_silent` regex grade B. Must `logger.warning(...)` + explicit `self.X = adapter_arg`.
- **Writing `.env` parser with `shlex.split`:** shlex handles quoting but does NOT handle `export KEY=VAL` prefix — roll our own simple split-on-first-`=` with explicit prefix strip.
- **`.ps1` using `Get-Content .env | Select-String '=' | %...`:** Fragile on BOM + comment lines. Use `ForEach-Object { if ($_ -match ...) }` pattern.
- **`$env:PYTHONIOENCODING = 'utf-8'` in .ps1:** Not necessary — Python 3.11 on Windows respects utf-8 by default; `chcp 65001` in .cmd is sufficient.
- **Putting `load_dotenv` call inside `main()`:** Too late — module-level adapter imports already failed. Must be at package `__init__.py` top.
- **Using `python-dotenv`:** Banned by D-13 (no requirements.txt).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Claude CLI invocation | anthropic SDK HTTP client | `subprocess.Popen(['claude', '--print', ...]).communicate()` | Max 구독 billing (memory: `project_claude_code_max_no_api_key`) + CLI handles auth, model routing, retries |
| Session ID generation | UUID, hash, incremental counter | `datetime.now().strftime("%Y%m%d_%H%M%S")` | Wrapper + Python agree on format; human-readable in file paths |
| `.env` quote-aware parsing | recursive descent parser | simple `re.match + strip("'\"")` | .env spec is flat `KEY=VAL` with optional quotes; tested patterns (python-dotenv semantics) are 5 regex cases |
| Windows ExecutionPolicy workaround | `Set-ExecutionPolicy Unrestricted` (machine-wide) | `.cmd` bootstrap with `-ExecutionPolicy Bypass` per-invocation | Non-invasive, no admin, no machine-state mutation |
| Korean console output | manual cp949→utf8 translation | `chcp 65001` + `sys.stdout.reconfigure(encoding='utf-8')` | Already used in `skill_patch_counter.py:56` + `phase091_stage2_to_4.py:43` |
| Idempotent FAILURES append | content-hash SHA check | parse existing F-D2-NN entries, grep commit short-hashes | Human-readable signature, survives subject-line edits, matches existing write format |
| Gate progress display | progress bar library | `Write-Host "[GATE N/13] name" -Fore Cyan` | Simple, no deps, matches Phase 9.1 logger style |
| argparse default session-id | custom argparse Action | `default=None` + `args.session_id or datetime.now().strftime(...)` | Straightforward; testable via argparse `parse_args(["--state-root", "x"])` |

**Key insight:** Every one of these problems has an obvious stdlib/builtin answer. The entire Phase 11 surface is **assembly of known primitives** — zero net-new complexity. The drift risk is not in the fix; it's in the adapter wrap growing `shorts_pipeline.py` beyond 800 lines.

---

## Runtime State Inventory

Phase 11 is NOT a rename/refactor phase. It is a pipeline-activation + wrapper-addition phase. This section is included per protocol to surface runtime state changes that a grep audit would miss:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | None — Phase 11 adds no new persistence. Existing `state/<session_id>/` checkpoint files continue their format unchanged. Smoke run (SC#1) will create **one new session folder** with 14 `gate_NN.json` files + artifacts (audio/video/thumbnail) — normal pipeline output, not runtime migration. | None |
| **Live service config** | **YouTube Data API v3 upload will consume API quota** and create a real (unlisted) published video. Smoke video MUST be published as **public** per SC#2 ("YouTube Shorts 업로드 완료"). Uploaded video will show in YouTube Studio for 대표님 채널. | Verify `youtube_token.json` + `client_secret.json` present in `config/` (already confirmed for Phase 8 smoke). Cost: YouTube API `videos.insert` is 1600 quota units (10000 daily) — single upload is safe. |
| **OS-registered state** | Windows Task Scheduler `ShortsStudio_Pipeline` (registered by `windows_tasks.ps1` Plan 10-04) currently invokes `py -3.11 -m scripts.orchestrator.shorts_pipeline` directly — **does not use the new `.cmd`/`.ps1` wrapper**. Phase 11 wrapper is for manual 대표님 double-click ONLY. | No change required. Keep dual-path entry: (a) scheduler → direct Python module, (b) human → `.cmd` wrapper. Document in PLAN. |
| **Secrets/env vars** | `.env` file already exists at repo root (1745 bytes, 2026-04-20 synced) with 12 API keys (Typecast/ElevenLabs/Google/FAL/Kling/Runway/YouTube/etc.). **Phase 11 only CHANGES HOW they're read** (auto via `_load_dotenv_if_present` instead of manual `set -a && source .env`). No new secret keys introduced. No secret key renamed. | None — only read-path changes |
| **Build artifacts** | None. Python is interpreted; no `.egg-info` or compiled artifacts to invalidate. `__pycache__/` is gitignored and regenerates automatically. | None |

**Nothing found in a category:** Stated explicitly above ("None" / "No change required").

---

## Environment Availability

Phase 11 depends on external tools for both implementation AND the smoke-test gate (SC#1). Probed availability on target machine (Win11 Home 10.0.26200, cwd `C:\Users\PC\Desktop\naberal_group\studios\shorts`):

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `claude` CLI | PIPELINE-01 invoker, SC#1 smoke | ✓ | 2.1.112 | — (no fallback; Max 구독 required) |
| `py -3.11` launcher | `.ps1` invocation, all pytest | ✓ | 3.11.9 (MSC v.1938 64-bit) | `python -m scripts...` (PATH dependent) |
| `powershell.exe` 5.1+ | `.ps1` wrapper | ✓ (Win11 bundled) | 5.1 baseline | — |
| `cmd.exe` | `.cmd` bootstrap | ✓ (Win11 bundled) | — | — |
| `git` CLI | skill_patch_counter idempotency (reads commits) | ✓ (confirmed by existing `STATE.md` git log usage) | — | — |
| FAL API key (FAL_KEY) | Kling I2V calls in SC#1 | ✓ (in `.env`) | — | Phase 9.1 Veo 3.1 Fast fallback with `--use-veo` |
| Google API key (GOOGLE_API_KEY) | Nano Banana image generation | ✓ (in `.env`) | — | Ken-Burns local fallback if image gen fails |
| Typecast API key (TYPECAST_API_KEY) | Korean TTS | ✓ (in `.env`) | — | ElevenLabs fallback (ELEVENLABS_API_KEY also present) |
| YouTube OAuth (client_secret.json + youtube_token.json) | PIPELINE-01 upload stage + SC#2 | ✓ (confirmed Phase 8 smoke) | — | — |
| NotebookLM skill (browser automation) | RESEARCH_NLM gate | ✓ (Phase 6 Plan 06 subprocess wrapper) | — | D-5 Tier 1/2 grep+hardcoded fallback |
| ffmpeg (Ken-Burns fallback) | ASSEMBLY fallback lane | Unknown (not probed — outside 10-min budget) | — | Shotstack API if ffmpeg missing AND SHOTSTACK_API_KEY set; otherwise pipeline fails at fallback |
| `ELEVENLABS_DEFAULT_VOICE_ID` | ElevenLabs TTS | ✗ (empty in `.env`) | — | 3-tier resolution (D-13 `elevenlabs.py`): env → discovery via GET /v1/voices → hardcoded default. Non-blocking. |
| `SHOTSTACK_API_KEY` | Shotstack render (OPTIONAL per D-07) | ✗ (not in `.env`) | — | **BY DESIGN** — Phase 9.1 replaced Shotstack with Ken-Burns local. `self.shotstack = None` is the graceful-degrade path. |

**Missing dependencies with no fallback:** None. All hard requirements present.

**Missing dependencies with fallback (by design):** `SHOTSTACK_API_KEY`, `ELEVENLABS_DEFAULT_VOICE_ID` — documented graceful-degrade paths.

**Unknown (requires confirmation during Wave 0):** `ffmpeg` on PATH. Recommend Wave 0 adds a check: `where ffmpeg` (Windows) → if missing, log warning in .ps1 wrapper pre-flight.

---

## Common Pitfalls

### Pitfall 1: 800-Line Orchestrator Cap Breach

**What goes wrong:** Naive 4× verbatim try/except wrap adds ~20 lines → `shorts_pipeline.py` grows 796 → 816, breaching the soft cap + invalidating `tests/phase05/test_line_count.py::test_shorts_pipeline_under_soft_cap`.

**Why it happens:** D-05 specifies "동일 패턴" (same pattern), developer reads it as literal block-duplicate. 5166-line drift precedent in shorts_naberal creates legitimate cap-anxiety.

**How to avoid:** Collapse into helper (see §Line Budget). Replace 4 + existing 3 = 7 try/except blocks with one `_instantiate_adapter()` method + 7 one-line calls. Net delta: ~-5 lines (pipeline SHRINKS). CONTEXT D-05 "동일 패턴" is honored because the helper preserves semantic identity — same log message format, same fallback assignment.

**Warning signs:** PR diff for `shorts_pipeline.py` shows more inserted than deleted lines, new line count > 800.

### Pitfall 2: `.env` loader imported too late

**What goes wrong:** `load_dotenv()` placed in `shorts_pipeline.py:main()`. By the time `main()` runs, module-level imports at `shorts_pipeline.py:59-66` have already triggered `from .api.kling_i2v import KlingI2VAdapter`. The adapter *class* doesn't raise yet (only `__init__` does), but as soon as `ShortsPipeline.__init__` calls `KlingI2VAdapter()` at L210, `os.environ.get('KLING_API_KEY')` returns None because `.env` wasn't loaded.

**Why it happens:** Intuition places config-load at "the start of main". But Python import resolution happens before main(); adapter instantiation happens before explicit loader call.

**How to avoid:** Place `_load_dotenv_if_present()` at the TOP of `scripts/orchestrator/__init__.py` (the package init). Python imports `__init__.py` before any submodule. When `shorts_pipeline.py` does `from .api.kling_i2v import ...`, the `scripts.orchestrator.__init__` has already run and populated env.

**Warning signs:** Test `test_dotenv_loader_runs_before_adapter_import` (Wave 0) assertion fails.

### Pitfall 3: stdin encoding mismatch on Windows

**What goes wrong:** `Popen(..., stdin=PIPE).communicate(input=user_prompt)` — if `user_prompt` is Python `str` (bytes need `text=True`), or `text=True` without `encoding="utf-8"`, Windows defaults to cp949 which mangles Korean characters in the user_payload JSON.

**Why it happens:** Default console encoding on Korean Windows is cp949. `subprocess` respects `encoding=` kwarg only if set; not set → `locale.getpreferredencoding()`.

**How to avoid:** Port the existing kwargs verbatim to Popen:
```python
proc = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                        text=True, encoding="utf-8", errors="replace")
stdout, stderr = proc.communicate(input=user_prompt, timeout=timeout_s)
```

**Warning signs:** Producer output garbled Korean, or `UnicodeDecodeError` in stderr.

### Pitfall 4: `.cmd` trailing quote in %~dp0

**What goes wrong:** `%~dp0` includes trailing backslash. If wrapped with quotes like `"%~dp0\run_pipeline.ps1"`, you get `"C:\...\shorts\\run_pipeline.ps1"` which on some PowerShell parsers is invalid. The spec `"%~dp0run_pipeline.ps1"` (no backslash between) is canonical.

**Why it happens:** Developer adds defensive `\`, assuming `%~dp0` is path-without-trailing-slash like POSIX `dirname`.

**How to avoid:** Use exactly `"%~dp0run_pipeline.ps1"` — `%~dp0` already ends with `\`.

**Warning signs:** `run_pipeline.cmd` errors with "The system cannot find the path specified" despite file existing.

### Pitfall 5: Idempotency grep false negative on re-formatted FAILURES.md

**What goes wrong:** Developer manually reformats an F-D2-NN entry (e.g., fixes a typo in a violation subject), changing the commit-hash line format from `- \`abc1234\` date — ...` to `- \`abc1234\`: date - ...`. Grep regex `^- \`([0-9a-f]{7})\`` still matches — **safe**. But if the developer changes it to `- **abc1234** - ...`, regex misses; second counter run re-appends.

**Why it happens:** Format coupling between producer (`append_failures`) and consumer (`_existing_violation_hashes`) is implicit.

**How to avoid:** Test `test_idempotency_skip_existing` (D-24) + test `test_existing_hashes_parsed_from_current_format` (Wave 0 RED → GREEN, locks the format contract). If the format ever changes, the test fails and forces the grep regex to update synchronously.

**Warning signs:** `test_idempotency_skip_existing` fails with `"second run appended another entry"`.

### Pitfall 6: Real-run smoke publishes empty/bad video

**What goes wrong:** PIPELINE-01 fix unlocks real Claude CLI. Supervisor starts returning real verdicts. A GATE that would have passed under MockSupervisor now FAILs 3× and triggers regeneration-exhausted, appending to FAILURES.md and aborting the smoke. 대표님 never sees a published video, SCRIPT-01 evaluation blocked.

**Why it happens:** First real supervisor calls reveal quality issues that mocks papered over. Phase 9.1 smoke was MOCK supervisor — real behavior unproven at gate level.

**How to avoid:** 
1. Pre-smoke: dry-run single-gate test (e.g., just SCRIPT gate with real Claude) to verify argv+stdin round-trip.
2. Smoke runbook includes "rollback" path: if regeneration-exhausted, capture `retry_counts` + failing `supervisor_output`, analyze, relax supervisor rubric or ship AGENT.md patch.
3. BUDGET cushion: allocate 2× estimated cost for retries.

**Warning signs:** Smoke run exits with `IncompleteDispatch` or `RegenerationExhausted` at any GATE < 13.

### Pitfall 7: SCRIPT-01 evaluation is deferred but 대표님 capture is ambiguous

**What goes wrong:** Smoke publishes video, but there's no structured way to capture 대표님's A/B/C verdict. Without a standard capture format, Phase 12 spawn trigger is ambiguous (when does a vague "B가 나을 것 같아" become a locked decision?).

**Why it happens:** SCRIPT-01 D-17/D-18 delegates evaluation to human quality review without prescribing the capture mechanism.

**How to avoid:** Plan 11-06 creates `.planning/phases/11-.../SCRIPT_QUALITY_DECISION.md` with a template (see §Validation Architecture SC#2 eval capture format). 대표님 fills it; plan-executor commits it; Phase 12 entry requires the file + a single-letter verdict locked in frontmatter.

**Warning signs:** Phase 11 verification stalls waiting for "대표님 평가".

---

## Code Examples

Verified patterns. Source-of-truth for plan-executor.

### Pattern 1: `_invoke_claude_cli` stdin rewrite (PIPELINE-01)

```python
# scripts/orchestrator/invokers.py:118-171 — REPLACE

def _invoke_claude_cli(
    system_prompt: str,
    user_prompt: str,
    json_schema: str,
    cli_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> str:
    """Run ``claude --print`` via stdin piping and return stdout.

    Claude CLI 2.1.112 canonical form: user prompt via stdin with
    ``--input-format text`` (default). Legacy positional ``user_prompt``
    argument is rejected on 2.1.112 ("Input must be provided either
    through stdin or as a prompt argument when using --print").

    Args unchanged (D-04 test-seam preservation). Raises unchanged.
    """
    cmd = [
        cli_path,
        "--print",
        "--append-system-prompt", system_prompt,
        "--json-schema", json_schema,
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = proc.communicate(input=user_prompt, timeout=timeout_s)
    except subprocess.TimeoutExpired as err:
        proc.kill()  # explicit reap; prevents zombie on Windows
        proc.communicate()  # drain pipes
        raise RuntimeError(
            f"claude CLI 타임아웃 ({timeout_s}s 초과, 대표님): {err}"
        ) from err
    if proc.returncode != 0:
        stderr_tail = (stderr or "")[-500:]
        raise RuntimeError(
            f"claude CLI 실패 (rc={proc.returncode}, 대표님): {stderr_tail}"
        )
    if not stdout or not stdout.strip():
        raise RuntimeError(
            "claude CLI stdout 비어있음 — --json-schema 응답 미수신 (대표님)"
        )
    return stdout.strip()
```

**Source:** verified live on 2026-04-21 — `echo "ping" | claude --print --input-format text --append-system-prompt "reply exactly: PONG" --json-schema '{"type":"object","required":["reply"],"properties":{"reply":{"type":"string"}}}'` returns `PONG`.

**Net line delta:** +3/-3 = 0. Function body unchanged length.

### Pattern 2: `_load_dotenv_if_present()` (PIPELINE-02)

```python
# scripts/orchestrator/__init__.py — INSERT at TOP (before other imports)

import os
import re
from pathlib import Path


def _load_dotenv_if_present() -> None:
    """Zero-dep `.env` loader. Idempotent. override=False semantics.

    - Reads `./env` relative to current working directory.
    - Silently skips if file missing (tests / CI without .env).
    - Parses `KEY=VALUE` lines with quoted-value / comment / BOM / export handling.
    - Uses `os.environ.setdefault` — pre-existing env wins (matches
      python-dotenv `override=False`, `scripts/experimental/*.py` convention).
    - Split on FIRST `=` only; values may contain `=`.
    """
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        raw = env_path.read_text(encoding="utf-8-sig")  # strips BOM if present
    except OSError:
        return
    line_re = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
    for raw_line in raw.splitlines():
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = line_re.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        # Strip surrounding matched quotes (single OR double).
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


# Run at import time — before any adapter `__init__` can look at env.
_load_dotenv_if_present()


# ... existing package imports follow ...
```

**Source:** zero-dep distillation of python-dotenv 1.2.1 core parsing logic. Preserves existing `scripts/experimental/test_*.py:19` `load_dotenv(override=False)` semantics.

**Net line delta:** +32 lines in __init__.py (was 78 lines; now ~110 — well within any cap).

### Pattern 3: Adapter graceful degrade helper (PIPELINE-03 + Pitfall 1 avoidance)

```python
# scripts/orchestrator/shorts_pipeline.py — REPLACE L209-235

# Adapters (injected for tests, constructed from env otherwise). Each
# adapter raises ValueError on missing required env keys; the pipeline
# continues with self.X = injected_arg (possibly None) so smoke-based test
# harnesses and mock-injected test paths construct cleanly. Real runs
# that actually DISPATCH to a missing adapter will raise then.
def _try_adapter(name: str, build, injected, env_hint: str = ""):
    """Uniform adapter-instantiation guard (PIPELINE-03, D-05)."""
    try:
        return build()
    except (ValueError, KenBurnsUnavailable) as err:
        suffix = f" ({env_hint})" if env_hint else ""
        logger.warning(
            "[pipeline] %s adapter 미초기화 (대표님%s): %s",
            name, suffix, err,
        )
        return injected  # None if not injected — dispatcher raises on use

self.kling      = kling_adapter      or _try_adapter("kling",      lambda: KlingI2VAdapter(circuit_breaker=self.kling_breaker),           kling_adapter,      "KLING_API_KEY / FAL_KEY 없음")
self.runway     = runway_adapter     or _try_adapter("runway",     lambda: RunwayI2VAdapter(circuit_breaker=self.runway_breaker),         runway_adapter,     "RUNWAY_API_KEY 없음")
self.typecast   = typecast_adapter   or _try_adapter("typecast",   lambda: TypecastAdapter(circuit_breaker=self.typecast_breaker),       typecast_adapter,   "TYPECAST_API_KEY 없음")
self.elevenlabs = elevenlabs_adapter or _try_adapter("elevenlabs", lambda: ElevenLabsAdapter(circuit_breaker=self.elevenlabs_breaker),   elevenlabs_adapter, "ELEVENLABS_API_KEY 없음")
self.shotstack  = shotstack_adapter  or _try_adapter("shotstack",  lambda: ShotstackAdapter(circuit_breaker=self.shotstack_breaker),     shotstack_adapter,  "SHOTSTACK_API_KEY 없음 — Phase 9.1 ken_burns 로컬 대체")
self.nanobanana = nanobanana_adapter or _try_adapter("nanobanana", lambda: NanoBananaAdapter(circuit_breaker=self.nanobanana_breaker),   nanobanana_adapter, "GOOGLE_API_KEY 없음")
self.ken_burns  = ken_burns_adapter  or _try_adapter("ken_burns",  lambda: KenBurnsLocalAdapter(circuit_breaker=self.ken_burns_breaker), ken_burns_adapter,  "ffmpeg 확인 필요")
```

**Line delta:** Existing L210-235 = 26 lines. New helper + 7 one-liners = 21 lines. **Net -5 lines** (shrinks pipeline).

**Shortcut evaluation note:** `X or _try_adapter(...)` short-circuits if injected arg is truthy (mocks), so `_try_adapter` not called and no env-check happens during tests. **Identical semantics to current code.**

### Pattern 4: `.ps1` wrapper skeleton (PIPELINE-04)

```powershell
<#
.SYNOPSIS
  shorts_studio 파이프라인 실행 — 대표님 더블클릭 진입점.

.DESCRIPTION
  .env 자동 로드 + session-id 자동 생성 + Python 실행 + 창 유지.
  관리자 권한 불필요 (run_pipeline.cmd 가 -ExecutionPolicy Bypass 로 진입).

.NOTES
  Phase 11 PIPELINE-04. 기존 scripts/schedule/windows_tasks.ps1 컨벤션 준수.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null  # UTF-8 console — 한국어 출력

$ScriptRoot = $PSScriptRoot
Set-Location $ScriptRoot

function Load-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Host "[env] .env 파일 없음 (대표님 — 기존 환경변수로 진행)" -Fore Yellow
        return
    }
    Get-Content $Path -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        if ($line -match '^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $key   = $Matches[1]
            $value = $Matches[2]
            # strip surrounding quotes
            if ($value -match '^(["' + "']" + ')(.*)\1$') { $value = $Matches[2] }
            Set-Item -Path "env:$key" -Value $value
        }
    }
    Write-Host "[env] .env 로드 완료" -Fore Green
}

try {
    Write-Host "===================================================" -Fore Cyan
    Write-Host " shorts_studio 파이프라인 실행 (대표님)" -Fore Cyan
    Write-Host "===================================================" -Fore Cyan

    Load-DotEnv -Path "$ScriptRoot\.env"

    $sessionId = Get-Date -Format "yyyyMMdd_HHmmss"
    Write-Host "[session] $sessionId" -Fore Cyan

    & py -3.11 -m scripts.orchestrator.shorts_pipeline --session-id $sessionId
    $rc = $LASTEXITCODE

    if ($rc -eq 0) {
        Write-Host "[done] 파이프라인 성공 (대표님)" -Fore Green
    } else {
        Write-Host "[fail] 파이프라인 실패 rc=$rc (대표님)" -Fore Red
        throw "pipeline returned $rc"
    }
}
catch {
    Write-Host "[error] $($_.Exception.Message)" -Fore Red
    Write-Host "[error] 스택: $($_.ScriptStackTrace)" -Fore DarkRed
}
finally {
    Read-Host "`n`n완료. 엔터로 창 닫기 (대표님)"
}
```

**Source:** Adapted from `scripts/schedule/windows_tasks.ps1` conventions. Verified PowerShell 5.1+ syntax (Win11 baseline).

### Pattern 5: `skill_patch_counter` idempotency (AUDIT-05)

See §Pattern 5 in Architecture Patterns for the `_existing_violation_hashes()` function + main() integration. Test in §Pattern 5 covers the D-24 contract.

---

## Line Budget (shorts_pipeline.py)

| Change | Lines added | Lines removed | Net |
|--------|-------------|---------------|-----|
| `_try_adapter` helper (Pattern 3) | +13 (function body + docstring) | 0 | +13 |
| 7 adapter one-liners (replace existing 26 lines across L210-235) | +7 | -26 | -19 |
| argparse `--session-id required=False` + default timestamp (D-16) | +5 | -1 | +4 |
| **Total net** | +25 | -27 | **-2** |

**Current:** 796 lines. **After Phase 11:** ~794 lines. **Cap:** 800 lines. **Margin:** 6 lines.

**Verification:** Plan-executor must run `python -c "print(sum(1 for _ in open('scripts/orchestrator/shorts_pipeline.py', encoding='utf-8')))"` after each edit. `tests/phase05/test_line_count.py::test_shorts_pipeline_under_soft_cap` enforces at test time.

---

## STRUCTURE Whitelist Verification

**Question:** Are `run_pipeline.cmd` and `run_pipeline.ps1` at studio repo root allowed?

**Evidence:**
1. `ls "C:/Users/PC/Desktop/naberal_group/studios/shorts/STRUCTURE.md"` → `No such file or directory`.
2. `.claude/hooks/pre_tool_use.py:88-92`: `structure_md = studio_root / "STRUCTURE.md"; if not structure_md.exists(): return True, ""` — when absent, whitelist check is **skipped** (returns allowed).
3. Harness `STRUCTURE.md` at `C:\Users\PC\Desktop\naberal_group\harness\STRUCTURE.md` only constrains `harness/` folder, not studio folders.

**Conclusion:** `run_pipeline.cmd` + `run_pipeline.ps1` at `C:\Users\PC\Desktop\naberal_group\studios\shorts\` → **ALLOWED** by current hook semantics.

**Additional consideration — repo root hygiene:** Studio repo root already contains non-standard files: `SESSION_LOG.md`, `SKILL_HISTORY/`, `WORK_HANDOFF.md` — not a typical POSIX project root. Two more well-named entry files fit the existing convention.

**Recommendation:** Commit `.cmd` + `.ps1` at repo root as specified by D-09. No STRUCTURE.md change needed.

---

## Full Smoke Cost Model (SC#1)

Phase 9.1 live smoke: $0.29 for Stage 2→4 (Nano Banana image + Kling I2V clip). Phase 11 full 0→13 GATE real-run adds:

| Stage | GATE | Cost driver | Expected $ | Notes |
|-------|------|-------------|-----------|-------|
| Pre | IDLE | — | $0.00 | |
| 1 | TREND | Claude Sonnet/Opus producer + supervisor | $0.02-0.05 | Short prompts; JSON schema trims tokens |
| 2 | NICHE | Claude producer + supervisor | $0.02-0.05 | |
| 3 | RESEARCH_NLM | NotebookLM subprocess (Max 구독 inclusive) | $0.00 | No API billing — browser automation |
| 4 | BLUEPRINT | Claude producer + supervisor | $0.03-0.08 | Longer outputs |
| 5 | SCRIPT | Claude Opus primary + supervisor | $0.15-0.35 | Opus pricing; 2000-token output |
| 6 | POLISH | Claude Sonnet + supervisor | $0.03-0.08 | |
| 7 | VOICE | Typecast Korean TTS | $0.05-0.15 | ~60s audio, ~900 chars at $0.15/1k chars |
| 8 | ASSETS | Nano Banana ×N + Kling I2V ×N | $1.50-2.50 | N ~= 8 cuts; $0.04 image + $0.35 video each |
| 9 | ASSEMBLY | Ken-Burns local ffmpeg | $0.00 | Phase 9.1 replaced Shotstack |
| 10 | THUMBNAIL | Nano Banana single image | $0.04-0.08 | +Claude for prompt |
| 11 | METADATA | Claude producer | $0.02-0.05 | Title/desc/tags |
| 12 | UPLOAD | YouTube Data API v3 | $0.00 | Quota-based, no $ |
| 13 | MONITOR | Claude + GCS log fetch | $0.02-0.05 | |
| **Subtotal** | | | **$1.88-$3.44** | |
| Regeneration overhead | ~1.5× on flaky gates | ~30% cushion | +$0.56-$1.03 | Max 3 retries per gate |
| **Total (single published video)** | | | **$2.44-$4.47** | |

**Recommendation:** Allocate **$5.00 budget cap** with `--max-budget-usd 5.00` on Claude CLI calls (flag confirmed on 2.1.112). Aggregate cost tracking via a new `scripts/smoke/phase11_full_run.py` that accumulates `result.usage` per gate if exposed in JSON output, else estimates from token counts.

**Phase 9.1 reference:** `scripts/smoke/phase091_stage2_to_4.py` is the skeleton — copy structure, remove `COST_CAP_USD = 1.00` hard guard (SC#1 requires real publish, not a cap-cutoff), add per-GATE cost tracker.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `claude --print "prompt as argv"` positional | `echo "prompt" \| claude --print` stdin | Claude CLI 2.1+ (verified 2.1.112) | Required by PIPELINE-01; fixes D10-PIPELINE-DEF-01 error 5 |
| `python-dotenv` `load_dotenv()` | zero-dep `_load_dotenv_if_present()` | Phase 11 D-13/D-14 | No new dependency in harness-constrained studio |
| `ShortsPipeline(session_id=required)` | `session_id` auto-default via `datetime.now().strftime("%Y%m%d_%H%M%S")` | Phase 11 D-16 | Wrapper UX — no need to pass timestamp explicitly |
| Per-adapter eager ValueError from pipeline site | `_try_adapter` helper uniform graceful degrade | Phase 11 D-05 | Missing env for UNUSED adapter no longer blocks construction |
| Global `ShortsStudio_Pipeline` Scheduled Task via windows_tasks.ps1 | **Dual entry:** (a) scheduler unchanged, (b) manual `.cmd` double-click | Phase 11 D-09 | 대표님 manual run path added without breaking automation |

**Deprecated / outdated:**
- **`subprocess.run(cmd + [user_prompt], ...)` with positional prompt** — Claude CLI 2.1.112 rejects this form. Must use stdin. Old form would fail on any user who upgrades Claude CLI.
- **`--session-id required=True`** — creates UX trap (double-click → crash). Replaced by auto-default.

---

## Open Questions

### 1. ffmpeg availability on target machine
- What we know: `scripts/orchestrator/api/ken_burns.py` raises `KenBurnsUnavailable` if ffmpeg missing. Phase 9.1 smoke passed, implying ffmpeg present.
- What's unclear: Did 대표님 install ffmpeg as Phase 9.1 pre-req? Scheduled Task + Phase 11 wrapper must both be ffmpeg-capable.
- Recommendation: Plan 11-04 (wrapper) pre-flight check: `where ffmpeg` → if missing, log warning + suggest `winget install ffmpeg`. Non-blocking (shotstack adapter will fallback gracefully).

### 2. 대표님 real-run SCRIPT-01 evaluation criteria
- What we know: D-17/D-18 commits to Option A baseline for Phase 11 published video; evaluation drives Phase 12 spawn.
- What's unclear: Does 대표님 evaluate against pre-existing channel videos or a rubric? No formal rubric in `wiki/script/QUALITY_PATTERNS.md` beyond qualitative descriptions.
- Recommendation: Plan 11-06 provides a 6-row evaluation template (see §Validation Architecture SC#2 eval capture format). 대표님 fills qualitative notes per row; outcome is a 1-letter verdict in frontmatter.

### 3. Retry budget for real Claude CLI in smoke
- What we know: `max_retries_per_gate=3` is the default (`shorts_pipeline.py:175`). Smoke cost model assumes ~1.5× = mild retry. 3× all-13-gates would be $10+.
- What's unclear: First real-run failure rate is unmeasured. Phase 9.1 smoke was mock supervisor — no real failure data.
- Recommendation: Run smoke with `--max-budget-usd 5.00` on CLI + abort script if `retry_counts` sum exceeds 6 (half of max). Provide rollback commands to reduce `max_retries` if needed.

### 4. YouTube quota for smoke
- What we know: `videos.insert` costs 1600 quota units; daily quota 10000. Single smoke upload is safe.
- What's unclear: If smoke fails partway and retries require re-uploading, may blow quota.
- Recommendation: `publish_lock.py` 48h minimum already prevents multi-upload same day. Non-issue.

---

## Validation Architecture (Nyquist dim-8)

Phase 11 has 6 Success Criteria from ROADMAP §297-303. Test framework + per-SC mapping below. VALIDATION.md gate: every ❌ row must become ✅ before /gsd:verify-work 11.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `pytest` 8.x (existing; confirmed by 986+ full sweep) |
| Config file | none (pytest uses defaults; `tests/phase*/` convention) |
| Quick run command | `pytest tests/phase11/ -x` |
| Full suite command | `pytest tests/ -q` (9m sweep baseline from STATE.md session #21) |
| Phase 11-specific smoke | `py -3.11 scripts/smoke/phase11_full_run.py --live` (NEW, Plan 11-05) |

### Phase Requirements → Test Map

| SC # | Signal (what proves completion) | Sampling rate | Measurement (command / file / manual) |
|------|--------------------------------|---------------|---------------------------------------|
| **SC#1** Full 0→13 real-run smoke completes | `phase11_full_run.py --live` exits 0 AND `state/<sid>/` contains 14 `gate_NN.json` files AND `state/<sid>/gate_12_COMPLETE.json` exists | ONE-SHOT (single live run; not re-runnable daily — costs $) | Command: `py -3.11 scripts/smoke/phase11_full_run.py --live --max-budget-usd 5.00` → exit 0. Verify: `ls state/<sid>/gate_*.json \| wc -l` == 14. |
| **SC#2** 1 video published + SCRIPT-01 verdict locked | YouTube Studio shows uploaded video (manual eyeball) AND `.planning/phases/11-.../SCRIPT_QUALITY_DECISION.md` exists with frontmatter `verdict: A\|B\|C` locked | ONE-SHOT (evaluation is human 대표님 activity) | Manual: 대표님 views published video + fills `SCRIPT_QUALITY_DECISION.md` template (see §Eval Capture Format below) |
| **SC#3** skill_patch_counter idempotency | `pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -x` → GREEN | PER-TASK (runs in Wave 1 idempotency plan + full regression sweep) | `pytest tests/phase10/ -q` (all 12 GREEN — 11 existing + 1 new) |
| **SC#4** `.env` auto-load integration | `tests/phase11/test_dotenv_loader.py` all GREEN (13 edge cases) + import-time effect verified | PER-TASK + per-wave merge | `pytest tests/phase11/test_dotenv_loader.py -v` → all GREEN |
| **SC#5** `run_pipeline.cmd/.ps1` wrapper | Files exist at repo root AND `.cmd` triggers `.ps1` successfully in dry-run AND `tests/phase11/test_wrapper_smoke.py` GREEN | PER-TASK | `pytest tests/phase11/test_wrapper_smoke.py -v` + manual double-click test by 대표님 (captured in VERIFICATION.md) |
| **SC#6** (OPTIONAL) Phase 04/08 retrospective VERIFICATION.md | `.planning/phases/04-.../04-VERIFICATION.md` exists AND `08-VERIFICATION.md` exists with 7+ evidence rows each | PER-PHASE (on spawn) | File existence + content grep. **Can be deferred** to post-Phase 11 cleanup per D-18 alternative. |

### Sampling Rate

- **Per task commit:** `pytest tests/phase11/ -x` (fast — unit-level, ~30s)
- **Per wave merge:** `pytest tests/phase10/ tests/phase11/ -q` (~2 minutes)
- **Phase gate:** `pytest tests/ -q` (full sweep, ~9 minutes) + `scripts/smoke/phase11_full_run.py --live` (one-shot, $2-5)

### Wave 0 Gaps

- [ ] `tests/phase11/__init__.py` — new test directory marker
- [ ] `tests/phase11/conftest.py` — fixtures: `tmp_env_file`, `mock_cli_runner`, `fake_claude_cli_runner_factory`
- [ ] `tests/phase11/test_invoker_stdin.py` — 6 tests for PIPELINE-01 (stdin wiring, timeout, rc!=0, empty stdout, Korean round-trip, test seam compatibility)
- [ ] `tests/phase11/test_dotenv_loader.py` — 13 edge-case tests (Pattern 2 table)
- [ ] `tests/phase11/test_adapter_graceful_degrade.py` — 5 tests (one per adapter + helper test)
- [ ] `tests/phase11/test_argparse_session_id.py` — 3 tests (required=False, default auto-generates, explicit override)
- [ ] `tests/phase11/test_wrapper_smoke.py` — 2 tests (file existence + dry-run parse check via PowerShell `-WhatIf`-like `& { function py { ... mock } }`)
- [ ] `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` — new test (D-24)
- [ ] `scripts/smoke/phase11_full_run.py` — full 0→13 live-run harness (skeleton from `phase091_stage2_to_4.py`)

*(No framework install — pytest already in use.)*

### SC#2 Eval Capture Format

**File to create:** `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/SCRIPT_QUALITY_DECISION.md`

**Template:**
```markdown
---
verdict: (A|B|C) -- TO BE SET BY 대표님 AFTER VIDEO REVIEW
phase_12_spawn_required: (true|false) -- A=false, B/C=true
video_url: https://youtube.com/shorts/...
decided_on: YYYY-MM-DD
---

# SCRIPT-01 Option Decision — 대표님 Quality Evaluation

## Published Video
- YouTube URL: <https://youtube.com/shorts/...>
- 업로드 시각: YYYY-MM-DDTHH:MM+09:00
- Session ID: <session-id>
- 제작 방식: **Option A** (현 scripter AGENT.md, Claude Opus prompt-based duo dialogue)

## 대표님 평가 (6개 axis)

| Axis | Option A 만족도 (1-5) | 메모 |
|------|----------------------|------|
| 훅 강도 (0-3s) | | |
| 대사 자연스러움 (한국어) | | |
| 사건 팩트 정확도 | | |
| 듀오 대화 리듬 | | |
| 감정 임팩트 | | |
| 전체 완성도 | | |

## Verdict (기록 후 frontmatter 수정)

- **A (현 시스템 유지)**: 옵션 A 만족, Phase 12 spawn 불필요
- **B (NLM 2-step 재설계)**: 대본 문장 자체의 소스-grounded 강도 부족 → Phase 12 spawn
- **C (Shorts/Longform 2-mode 분리)**: 59s 에는 현 시스템 OK, 15분 longform 은 분리 필요 → Phase 12 spawn

## Notes
(대표님 자유 기술)
```

### Signal Quality Per SC

| SC | Signal strength | Notes |
|----|-----------------|-------|
| SC#1 | HIGH (file-count deterministic) | 14 checkpoint files is unambiguous. |
| SC#2 | MEDIUM (human judgment) | Structured template reduces ambiguity; verdict letter is the durable signal. |
| SC#3 | HIGH (pytest assertion) | |
| SC#4 | HIGH (pytest assertion) | |
| SC#5 | MEDIUM (file existence + 대표님 manual click) | Wrapper dry-run test covers automation; human click is 1-time. |
| SC#6 | N/A | Optional; can defer. |

---

## Plan Wave Structure (6 plans, 3 waves)

### Wave 1 — Fix Chain Prerequisites (fully parallelizable, zero file overlap)

| Plan | Owner file(s) | REQ | Depends on |
|------|---------------|-----|------------|
| **11-01-invoker-stdin-fix-PLAN.md** | `scripts/orchestrator/invokers.py` + `tests/phase11/test_invoker_stdin.py` | PIPELINE-01 | Wave 0 test scaffold only |
| **11-02-dotenv-loader-PLAN.md** | `scripts/orchestrator/__init__.py` + `tests/phase11/test_dotenv_loader.py` | PIPELINE-02 | Wave 0 only |
| **11-03-adapter-graceful-degrade-PLAN.md** | `scripts/orchestrator/shorts_pipeline.py` (L210-235 wrap block + argparse) + `tests/phase11/test_adapter_graceful_degrade.py` + `tests/phase11/test_argparse_session_id.py` | PIPELINE-03 + PIPELINE-04-tie-in | Wave 0 only |

**Rationale for Wave 1 parallelism:** Three files, zero overlap. `invokers.py` has no imports from `shorts_pipeline.py`. `__init__.py` has no edits overlapping L210-235. Plan 11-03 needs `.env` to have been loaded at import — but tests mock env vars directly, so plan test runs don't depend on 11-02. Live smoke (Wave 3) depends on all three; but test-green is wave-independent.

### Wave 2 — Wrapper + Idempotency (Wave 1 → serial)

| Plan | Owner file(s) | REQ | Depends on |
|------|---------------|-----|------------|
| **11-04-wrapper-cmd-ps1-PLAN.md** | `run_pipeline.cmd` + `run_pipeline.ps1` (NEW, repo root) + `tests/phase11/test_wrapper_smoke.py` | PIPELINE-04 | Wave 1 all (wrapper calls through the fixed pipeline) |
| **11-05-idempotency-counter-PLAN.md** | `scripts/audit/skill_patch_counter.py` + `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` | AUDIT-05 | Independent of Wave 1 (can technically parallelize with Wave 2-04, kept in Wave 2 for sequential discipline) |

**Rationale for Wave 2:** Wrapper integration-tests exercise Wave 1 fixes. Idempotency is standalone but grouped with wrapper for wave discipline (Wave 1 = upstream fixes, Wave 2 = consumer-facing).

### Wave 3 — Full Smoke + Script Decision

| Plan | Owner file(s) | REQ | Depends on |
|------|---------------|-----|------------|
| **11-06-full-smoke-script-decision-PLAN.md** | `scripts/smoke/phase11_full_run.py` (NEW) + `.planning/phases/11-.../SCRIPT_QUALITY_DECISION.md` (template) + `VERIFICATION.md` row capture | SC#1 validation + SCRIPT-01 | Wave 1+2 all |

**Rationale for Wave 3:** Live smoke consumes all upstream fixes. Video publication unblocks 대표님 evaluation. SCRIPT_QUALITY_DECISION.md is filled AFTER smoke — Phase 11 verification-gate requires verdict letter present. One plan ownership keeps the smoke script + decision template co-located.

### Wave structure summary

- Wave 0 (test scaffold): ~1 plan-internal (each plan ships conftest + test files in its own commit)
- Wave 1: **parallel** 3 plans (invoker / dotenv / adapter-wrap) — ~30-45 min each when not blocked on CI
- Wave 2: 2 plans (wrapper / idempotency) — ~30 min each
- Wave 3: 1 plan (smoke + decision) — $2-5 live cost + 대표님 human eval turnaround
- Post-Wave 3: `/gsd:verify-work 11` → VERIFICATION.md + deferred-items.md sweep

**Total plan count: 6** — under AF-10 Anthropic sweet spot. Adds 5 ≤ D10-scope (8 plans) so proportional discipline maintained.

---

## REQUIREMENTS.md D-19 Amendment (SCRIPT-01)

**Current (REQUIREMENTS.md:343):**
> **SCRIPT-01**: D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 + 대표님 품질 평가를 근거로 옵션 A / B / C 중 1개 확정. **선택된 옵션의 구현까지 완료**.

**Proposed (cleanest phrasing preserving intent):**
> **SCRIPT-01**: D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 (Option A 베이스라인 산출물) + 대표님 품질 평가를 근거로 옵션 A / B / C 중 1개 확정. **A 선택 시: Phase 11 에서 완료**. **B/C 선택 시: Phase 12 (NLM 2-Step Scripter Redesign) 에서 구현 후 완료 — Phase 11 verification-gate 는 옵션 letter 확정 + Phase 12 spawn trigger 로 충족**.

**Rationale:** 
1. Makes implicit "A=done, B/C=Phase 12" logic explicit.
2. Resolves original phrasing's logical contradiction (평가 트리거 → 구현 완료 둘 다 같은 phase 불가능).
3. Names Phase 12 so traceability is eager (ROADMAP Phase 12 spawn condition is already implicit in §Deferred Ideas).
4. Defines Phase 11's verification contract for SCRIPT-01 precisely: letter-locked verdict + (conditional) phase spawn entry.

**Diff (to be applied by Plan 11-06 as part of SCRIPT_QUALITY_DECISION.md commit):**
```diff
-- [ ] **SCRIPT-01**: D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 + 대표님 품질 평가를 근거로 옵션 A (현 `scripter` agent 유지) / B (NLM 2-step 호출 모드 재설계, `scripts/notebooklm/query.py` 2-notebook 호출 구조) / C (Shorts/Longform 2-mode 분리, channel_bible.길이 기반 routing) 중 1개 확정. 선택된 옵션의 구현까지 완료.
++ [ ] **SCRIPT-01**: D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 (Option A 베이스라인 산출물) + 대표님 품질 평가를 근거로 옵션 A (현 `scripter` agent 유지) / B (NLM 2-step 호출 모드 재설계, `scripts/notebooklm/query.py` 2-notebook 호출 구조) / C (Shorts/Longform 2-mode 분리, channel_bible.길이 기반 routing) 중 1개 확정. A 선택 시 Phase 11 에서 완료. B/C 선택 시 Phase 12 (NLM 2-Step Scripter Redesign) 에서 구현 후 완료 — Phase 11 verification-gate 는 SCRIPT_QUALITY_DECISION.md 내 verdict letter 확정 + (B/C 시) Phase 12 spawn trigger 로 충족.
```

---

## Sources

### Primary (HIGH confidence — stated as fact)

- **Claude CLI 2.1.112 `--help` + `--print` + `--input-format text` + `--json-schema`** — verified live 2026-04-21 via `claude --version` + `echo "ping" \| claude --print --input-format text --append-system-prompt "..." --json-schema "..."` round-trip.
- **`scripts/orchestrator/invokers.py` L118-171** — current argv structure (reviewed in full).
- **`scripts/orchestrator/shorts_pipeline.py` L200-270, L740-772** — adapter instantiation block + argparse.
- **`scripts/orchestrator/api/{kling_i2v,runway_i2v,typecast,elevenlabs,shotstack}.py`** — all 5 `__init__` ValueError sites.
- **`scripts/audit/skill_patch_counter.py` L187-237** — current append_failures behavior.
- **`tests/phase10/test_skill_patch_counter.py` full** — existing 11 tests; no idempotency coverage.
- **`.planning/phases/11-.../11-CONTEXT.md`** — 25 locked decisions D-01 ~ D-25.
- **`.planning/REQUIREMENTS.md` L330-365** — PIPELINE-01~04 + SCRIPT-01 + AUDIT-05 original text.
- **`.planning/phases/10-.../deferred-items.md`** — D10-PIPELINE-DEF-01 5-error chain + D10-SCRIPT-DEF-01 options + D10-01-DEF-02 root cause.
- **`scripts/schedule/windows_tasks.ps1`** — PS convention reference (Korean block comments, `-NoProfile`, absolute $ScriptRoot, Register-ScheduledTask patterns).
- **`.claude/memory/project_claude_code_max_no_api_key.md`** — anthropic SDK ban rationale.
- **`CLAUDE.md` (project root)** — 하네스 inheritance + 금기 9 / 필수 8 / Navigator routing.
- **`../../harness/STRUCTURE.md` v1.1.0** — whitelist scope (only constrains harness/).
- **`.claude/hooks/pre_tool_use.py` L82-152** — `check_structure_allowed` hook (studio STRUCTURE.md optional, skipped when absent).
- **`.claude/deprecated_patterns.json`** — active regex blocks (try_pass_silent grade B, skip_gates grade A, etc.).
- **`.env` (actual contents)** — 12 keys present, 2 absent (`SHOTSTACK_API_KEY`, `ELEVENLABS_DEFAULT_VOICE_ID`).

### Secondary (MEDIUM confidence — verified against primary)

- **Python 3.11 `subprocess.Popen.communicate(input=..., timeout=...)`** — stdlib docs (verified by existing `subprocess.run(...timeout=...)` behavior in invokers.py).
- **python-dotenv 1.2.1 `load_dotenv(override=False)` semantics** — upstream docs (cross-verified by existing `scripts/experimental/test_*.py:19` usage pattern).
- **Windows `%~dp0` behavior (path with trailing `\`)** — Microsoft cmd documentation (cross-verified against STRUCTURE precedent in existing .ps1).
- **PowerShell `$PSScriptRoot` (3.0+)** — Microsoft PS docs (cross-verified against existing `windows_tasks.ps1` which uses absolute path convention).

### Tertiary (LOW confidence — no single authoritative source, flagged for validation)

- **ffmpeg availability on 대표님 PC** — inferred from Phase 9.1 smoke pass, but not directly probed. Plan 11-04 pre-flight check recommended.
- **Typical Claude CLI real-call cost per gate** — estimated ranges based on typical Opus/Sonnet pricing ($15/M input tokens Opus, $3/M output) + expected token volumes. Actual costs will be recorded during SC#1 live run.
- **YouTube `videos.insert` quota cost 1600 units** — YouTube Data API v3 documentation (historical; may shift but well-documented).

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — all tools verified via live version check
- Architecture patterns: **HIGH** — code snippets dry-run against current codebase; line budget arithmetic checked
- Pitfalls: **MEDIUM-HIGH** — 6 pitfalls derived from existing code review + live CLI test; Pitfall 6 (smoke-time regeneration exhaustion) is the highest-risk unknown
- Environment availability: **HIGH** for API keys (probed `.env`); **MEDIUM** for ffmpeg (not re-probed)
- Validation architecture: **HIGH** — all SC signals have deterministic measurement path except SC#2 (by design — human eval)

**Research date:** 2026-04-21
**Valid until:** 2026-05-10 (3 weeks — Phase 11 sprint window). After Phase 12 spawns, re-verify Claude CLI version (2.1.x may have further contract shifts).

**Key evidence files/paths (plan-executor authoritative references):**
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\orchestrator\invokers.py` (L118-171, L174-234, L237-292)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\orchestrator\shorts_pipeline.py` (L1-100, L186-270, L740-772)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\orchestrator\__init__.py` (78 lines — insertion target)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\audit\skill_patch_counter.py` (L187-237, L280-287)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\tests\phase10\test_skill_patch_counter.py` (existing 11 tests)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\schedule\windows_tasks.ps1` (PS convention)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\scripts\smoke\phase091_stage2_to_4.py` (smoke skeleton)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.env` (actual 12 keys; 2 absent by design)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\phases\11-pipeline-real-run-activation-script-quality-mode\11-CONTEXT.md` (25 locked decisions)
- `C:\Users\PC\Desktop\naberal_group\harness\STRUCTURE.md` (whitelist boundary — does not constrain studio)
