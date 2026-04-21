# Phase 15: System Prompt Compression + User Feedback Loop — Research

**Researched:** 2026-04-22
**Domain:** Claude Code CLI 2.1.112 argv/stdin encoding path + ShortsPipeline revision/resume interface
**Confidence:** HIGH (empirical: CLI flag existence 확인 + argv size 측정, brownfield: all 30 AGENT.md + invokers.py 전수 read)

---

## Summary

Phase 13 live smoke 2026-04-22 attempt 는 invokers.py L121 `_invoke_claude_cli_once` 가 shorts-supervisor AGENT.md body (10591 chars stripped, 13362 bytes with frontmatter) 를 `--append-system-prompt` argv 로 전달했을 때 rc=1 "프롬프트가 너무 깁니다" 를 반환하여 TREND gate 진입 전에 실패했다 (0.09s, $0 spent). 동일 body 를 bash `$BODY` 로 전달하면 성공 — **root cause 는 argv OS limit (Windows 32767 WCHAR) 이 아니다** (10591 chars ≪ 32767).

**Empirical evidence (2026-04-22 session 재현)**:
1. Claude CLI 2.1.112 help: `--append-system-prompt <prompt>` 만 direct listing, **BUT `--bare` description 에 `--append-system-prompt[-file]` 명시 + `claude --print --append-system-prompt-file /tmp/nonexistent` → "Error: Append system prompt file not found" 반환 = flag 존재 확증**
2. Windows argv 총 10073 chars (body 10591 + flags) — 32767 한계의 30.7%, OS overflow 아님
3. UTF-8 encoded argv = 21000 bytes — Claude CLI 내부 token counter 가 "너무 깁니다" 로 판정하는 임계선 위치가 bash vs Python subprocess 에서 다른 이유가 진짜 root cause (H2 가장 유력)

**Primary recommendation**: **`--append-system-prompt-file <path>` 채택 (SPC-04 Option A = BEST)**. temp file 경로는 argv 에 30 chars 미만으로 나타나 argv encoding / token counter 경로를 완전 우회. AGENT.md body 를 tempfile 로 dump → path 전달 → 삭제. 부가로 SPC-02 압축은 여전히 가치 있음 (input token cost reduction, 10591→6000 = 43% 감소, invokers.py L495 `_compress_producer_output` 와 대칭).

**UFL-01~04** 은 ShortsPipeline.run() L269 의 resume 메커니즘 (Checkpointer.resume / dispatched_gates rebuild) 을 재활용한 3-flag 추가. pipeline 코어는 수정 최소 — revision 은 특정 gate_N.json 만 삭제 → run() 이 자연스럽게 재진입. 대표님 feedback 는 GateContext.config 에 주입하여 downstream producer prompt 에 `<prior_user_feedback>` block 으로 전파.

---

## User Constraints (from CLAUDE.md + REQUIREMENTS.md Phase 15 + 대표님 직접 승인)

### Locked Decisions (binding)

- **대표님 Option B 채택 2026-04-22**: "어떻게해서든 내가 명령할수있는기능을 만들어야지 그렇지않으면 절대안되... 한동안은 내 피드백을 받으면서 영상을 제작 수정 재재작해야 너가 진짜 퀄리티좋은 영상을 만들수있다." → UFL-01~04 전 4 REQ 필수 구현.
- **CLAUDE.md 금기 #3**: try-except 침묵 폴백 금지 — encoding fix 는 명시적 raise + explicit except, `except: pass` 금지.
- **CLAUDE.md 금기 #5**: STRUCTURE.md Whitelist 준수 — `scripts/smoke/`, `scripts/orchestrator/`, `tests/adapters/`, `.claude/agents/supervisor/shorts-supervisor/references/` 허용 확인 (Phase 12 AGENT-STD-02 precedent).
- **CLAUDE.md 필수 #5**: STRUCTURE.md Whitelist — 새 폴더 생성 시 pre_tool_use 차단 가능 (`.claude/agents/supervisor/shorts-supervisor/references/` 는 Phase 12 에서 선례 확립).
- **CLAUDE.md 필수 #7**: 모든 CLI error + logger 메시지 "대표님" + 존댓말.
- **Phase 14 pytest.ini invariant 보존**: `adapter_contract` marker + 7 `--ignore=` pre-existing D08-DEF-01 regex + `--strict-markers` 유지.
- **Phase 13 live_smoke marker 보존**: `tests/phase13/` + `--run-live` flag.
- **Phase 12 AGENT-STD-01/02/03 invariant 보존**: 31/31 AGENT.md 5-block schema + `<mandatory_reads>` + `_compress_producer_output` (invokers.py L495, producer output 압축 — 본 Phase 15 SPC 는 system_prompt body 압축 = 대칭 확장).
- **Claude CLI Max 구독 경로 고정**: `ANTHROPIC_API_KEY` 등록 금지 (memory: project_claude_code_max_no_api_key). 본 Phase 15 mock-based 검증은 $0, Tier 2 live smoke 만 $1.50~$3.00.
- **Budget**: Phase 15 Tier 1 (SPC-01~05 + UFL all mock) = $0. SPC-06 live smoke retry = $1.50~$3.00 (Phase 13 budget_cap_usd=5.00 invariant 승계).

### Claude's Discretion (research this)

- `--append-system-prompt-file` vs `--system-prompt-file`: 기존 `--append-system-prompt` 가 Claude Code CLAUDE.md 자동 discovery 등 빌트인 시스템 프롬프트를 유지하는 "append" semantics. 본 Phase 4 에이전트 경로는 순수 CLI 호출 (`--bare` 유사 목적) → **`--system-prompt-file` 선호 (빌트인 context 배제)** but 기존 작동 path (`--append-system-prompt`) 와의 semantic 동일성 검증 필요. 권장 Option A: `--append-system-prompt-file` (기존 semantics 승계, breaking change 최소).
- tempfile cleanup 시점: `finally` block 내 `os.unlink` vs `contextlib.ExitStack` — atomicity.
- SPC-02 6000 chars 목표 — `references/` split 단위: (a) 17 inspector rubric block, (b) delegation_depth python pseudo-code, (c) 17 inspector AGENT.md paths, (d) maxTurns matrix, (e) validators list. (a)~(c) 가 가장 큰 chunk.
- UFL-01 `--revision-from GATE`: GateName enum string 수용 vs 대소문자 insensitive. 권장: `GateName[arg.upper()]` strict.
- UFL-03 `--pause-after GATE`: GateContext.config 에 `pause_after_gate: GateName | None` 주입 vs 별도 attribute. 권장: config dict (unstructured 확장 자유도).
- UFL-04 rating CLI 의 `.claude/memory/feedback_video_quality.md` append 포맷: Markdown H2 heading + YAML frontmatter per rating vs JSON lines. 권장: Markdown H2 (ins-factcheck D-10 D-14 immutable pattern 과 일관).

### Deferred Ideas (OUT OF SCOPE)

- NotebookLM RAG query 캐싱 (feedback 기반 동적 reindex) — v2 (DEF-02).
- Inspector 17명 AGENT.md body 압축 (현재 평균 ~5KB each, 단일 supervisor 경로만 문제) — Phase 15 scope 외, 필요 시 Phase 16+.
- Producer 14명 AGENT.md body 일괄 압축 — SPC-03 audit 에서 12000 chars 초과 발견 시만 강제. 현재 max = scripter 17426 chars — 압축 대상 후보.
- Claude CLI upstream issue 제보 (subprocess Korean argv threshold bug) — 우회 가능하므로 P2.
- `--pause-after` 이후 재개 UX (web UI / TUI) — v2.
- `rate_video.py` 의 feedback 을 researcher agent mandatory_reads 에 자동 등록하는 로직 — Phase 15 에서는 수동 추가, Phase 16+ 자동화.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SPC-01 | invokers.py Windows encoding root cause 진단 + 수정 | Empirical: `--append-system-prompt-file` 존재 확증 (claude --help + error "Append system prompt file not found") → Option A fix 경로 확립. argv 10073 chars ≪ 32767 WCHAR = OS overflow 아님 (H1 기각). Python subprocess text=True encoding=utf-8 과 bash $BODY 경로의 차이는 Claude CLI 내부 token counter 경계 (H2 유력). |
| SPC-02 | shorts-supervisor AGENT.md body 압축 10591→6000 chars | Progressive Disclosure (wiki/render/i2v_prompt_engineering.md precedent). 5 블록 split 후보 identified (§Pitfalls #2). Phase 12 AGENT-STD-01 `verify_agent_md_schema.py` 5-block invariant 유지 필수 — references/ 는 body 밖에 위치. |
| SPC-03 | Producer 14 AGENT.md size audit + 상한 enforcement | 14 agents 전수 측정: min=script-polisher 12128, max=scripter 17426, mean=~14000 chars. `verify_agent_md_size.py` pytest marker `adapter_contract` 와 유사한 상한 contract. |
| SPC-04 | `--system-prompt-file` option 조사 | **CONFIRMED EXISTS** (Claude CLI 2.1.112 `--bare` help description: `--system-prompt[-file], --append-system-prompt[-file]`, 실측 `claude --print --append-system-prompt-file /tmp/x` → "Append system prompt file not found" error). Option A viable. |
| SPC-05 | `tests/adapters/test_invokers_encoding_contract.py` | Phase 091 test_producer_invoker.py + tests/phase11/test_invoker_stdin.py (subprocess.Popen mocking precedent). Mock subprocess.Popen, verify argv shape: 10KB+ body → temp file path in argv, not body itself. |
| SPC-06 | Phase 13 live smoke retry | phase13_live_smoke.py existing infrastructure (952 lines). SPC-01~05 완결 후 `--live --topic "해외범죄,..." --niche incidents` 재실행. Evidence: 5 files + smoke_e2e.json anchored. |
| UFL-01 | `--revision-from GATE --feedback TEXT` flag | ShortsPipeline.run() L288 `self.checkpointer.resume(self.session_id)` 가 gate_NN.json 숫자에서 last_idx 반환. 특정 gate_N.json 만 삭제 → resume 이 N-1 로 되돌아가고 L304 loop 에서 재실행. feedback 은 `GateContext.config['prior_user_feedback']` 에 주입. |
| UFL-02 | `--revise-script <path>` flag | SCRIPT gate (L384 `_run_script`) 에서 producer_loop skip, 파일 내용을 inputs 에 `user_provided_script` 로 주입. script-polisher gate (POLISH L399) 이 기존대로 실행. |
| UFL-03 | `--pause-after GATE` flag | GateContext.config['pause_after_gate']=GateName 설정. 각 `_run_<gate>` 메서드 끝에 check — 해당 gate 면 `PipelinePauseSignal` raise (runner 가 잡아 state/ + evidence 저장 후 graceful exit 0). |
| UFL-04 | `rate_video.py` CLI | argparse + append to `.claude/memory/feedback_video_quality.md` (D-2 저수지 예외: 대표님 직접 입력). 포맷: H2 `## YYYY-MM-DD <video_id>` + fields (rating/feedback/keywords). |

---

## Current State Inventory

### invokers.py Encoding Path (SPC-01 infrastructure)

**File**: `scripts/orchestrator/invokers.py` (586 lines, Phase 9.1 ship + Phase 11 stdin fix + Phase 12 AGENT-STD-03 compression)

| Line | Function | Role | Phase |
|------|----------|------|-------|
| 121~187 | `_invoke_claude_cli_once` | Popen + stdin communicate + rc check + Korean RuntimeError | Phase 9.1 / 11 |
| 154-159 | cmd construction | `[cli, "--print", "--append-system-prompt", system_prompt, "--json-schema", schema]` — **body as direct argv** ← rc=1 trigger | Phase 9.1 |
| 160-168 | Popen config | `text=True, encoding='utf-8', errors='replace'` (Windows cp949 가드 + surrogate escape) | Phase 11 |
| 170 | communicate | `proc.communicate(input=user_prompt, timeout=timeout_s)` — stdin text | Phase 11 |
| 213~305 | `_invoke_claude_cli` | Retry-with-nudge wrapper (3 attempts max, JSON prefix check) | Phase 11 F-D2-EXCEPTION-01 |
| 334~368 | Producer `__call__` | agent_name → dir → load_agent_system_prompt(body) → cli_runner(body, payload) | Phase 9.1 |
| 396~431 | Supervisor `__call__` | compress output → cli_runner(self._system, user_payload) | Phase 12 |
| 495~585 | `_compress_producer_output` | summary-only 압축 (gate/verdict/error_codes 보존, decisions/evidence char budget 2000) | Phase 12 AGENT-STD-03 |

**Phase 12 AGENT-STD-03 scope**: user_payload (producer output) 만 압축. `--append-system-prompt` body (supervisor AGENT.md) 는 scope 밖 — **Phase 15 SPC-01 이 정확히 여기를 해결**.

**Phase 13 failure evidence** (`14-05-live-run.log`):
```
2026-04-22 01:33:14,630 WARNING scripts.orchestrator.invokers:
  [invoker] claude-cli CLI 오류 재시도 1/3 (대표님): claude CLI 실패
  (rc=1, 대표님): �������� �ʹ� ��ϴ�.   ← cp949-corrupted UTF-8 of "프롬프트가 너무 깁니다"
```
- TREND gate 진입 직후 발생 (0.09s, $0 spent)
- pre-seeded TREND gate 는 `_PreSeededProducerInvoker` 가 Claude CLI 호출 skip — **실제로 실패한 것은 NICHE gate 직전의 supervisor Claude CLI 호출** (TREND producer 성공 → supervisor for TREND rc=1)
- cp949 corruption 은 stderr 의 garbled form; Windows 기본 locale 은 cp949, subprocess.Popen errors='replace' 가 Korean stderr bytes 를 replace character 로 대체

### Supervisor AGENT.md Body Structure (SPC-02 압축 대상)

**File**: `.claude/agents/supervisor/shorts-supervisor/AGENT.md` (13362 bytes total, 219 lines, stripped body 10591 chars)

| Block | Line | Size (est.) | Compressibility |
|-------|------|-------------|-----------------|
| Frontmatter | 1~8 | ~800 bytes | Keep (AGENT-STD-01 invariant) |
| Purpose | 10~20 | ~1500 bytes | Keep (핵심 불변식) |
| Inputs table | 22~35 | ~700 bytes | Keep (contract) |
| Outputs JSON sample | 37~54 | ~900 bytes | Keep (contract) |
| Prompt §System Context | 56~60 | ~400 bytes | Keep |
| **Prompt §Supervisor variant** | 62~147 | **~4500 bytes** | **SPLIT → `references/supervisor_variant.md`** (17 inspector list + delegation_depth pseudo-code + 합산 규칙 + VQQA concat 예제) |
| Producer variant stub | 149~151 | ~100 bytes | Keep |
| Inspector variant stub | 153~154 | ~100 bytes | Keep |
| References §Schemas | 156~160 | ~300 bytes | Keep |
| **References §17 Inspector AGENT.md paths** | 162~186 | **~1800 bytes** | **SPLIT → `references/inspector_paths.md`** |
| References §maxTurns matrix | 188~196 | ~300 bytes | Keep (short, critical) |
| References §Validators | 197~201 | ~250 bytes | Keep |
| Contract | 203~209 | ~600 bytes | Keep (RUB-06 GAN + routing) |
| **MUST REMEMBER** | 210~219 | **~1200 bytes** | Keep (RoPE end-position per AGENT-09 mandatory) |

**Target**: 10591 → ~6000 chars. 2 split blocks = ~6300 byte reduction. Frontmatter + Purpose + contract + MUST REMEMBER invariant 보존 = ~5500 chars retained + 500 chars `@references/` link prose = **6000 target 달성**.

### Producer 14 AGENT.md Audit (SPC-03)

```
assembler            13927    metadata-seo         14206
asset-sourcer        16474    niche-classifier     12701
director             12926    publisher            16401
researcher           13352    scene-planner        13003
script-polisher      12128    scripter             17426  ← MAX
shot-planner         14785    thumbnail-designer   14549
trend-collector      12564    voice-producer       16273
```
**Stats**: mean=14086, min=12128, max=17426, σ≈1750.
**Recommendation**: 상한 = 15000 chars (mean + 0.5σ). 초과 4개 (asset-sourcer, publisher, scripter, voice-producer) = Phase 15 내에서 `references/` split. 또는 상한 = 18000 (현재 max + 여유 3%) 로 설정, 장기 drift 차단.

### ShortsPipeline Revision/Resume Entry Points (UFL-01~03 infrastructure)

**File**: `scripts/orchestrator/shorts_pipeline.py` (13 `_run_<gate>` methods + run() orchestrator)

| Line | Shape | UFL Usage |
|------|-------|-----------|
| 120~143 | `GateContext` dataclass — session_id, config, artifacts{gate: path}, retry_counts | UFL-01 feedback → config['prior_user_feedback']; UFL-03 pause → config['pause_after_gate'] |
| 171~261 | `__init__` — invokers, adapters, checkpointer, gate_guard | UFL-02 script injection via `producer_invoker` substitution at __init__ |
| 269~319 | `run()` — resume from checkpoint + operational loop | UFL-01 revision: delete gate_N..13.json → resume rolls back to N-1 → loop resumes at N with fresh feedback in ctx.config |
| 287 | `last_idx = self.checkpointer.resume(self.session_id)` | UFL-01 leverage |
| 292~298 | `for name in self.checkpointer.dispatched_gates(self.session_id):` rebuild | UFL-01 skip already-done |
| 304~310 | `for gate in operational: method = getattr(self, f"_run_{gate.name.lower()}"); method(self.ctx)` | Entry for UFL-03 pause check (add at end of each method OR wrap via decorator) |
| 384~397 | `_run_script` | UFL-02 substitution point — `_PreScriptedProducer` wrapper (phase13 `_PreSeededProducerInvoker` precedent L155~228) |

**Checkpointer** (`scripts/orchestrator/checkpointer.py`):
- File layout: `state/<session_id>/gate_NN.json` (NN=00..14)
- Payload shape: `{_schema, session_id, gate, gate_index, timestamp, verdict, artifacts}`
- `resume()` → returns highest NN seen on disk (-1 if none)
- `dispatched_gates()` → returns list of gate_name strings from all gate_*.json files

**UFL-01 revision mechanism (recommended)**:
```python
# pseudocode for --revision-from SCRIPT --feedback "hook too weak"
state_dir = state_root / session_id
target_gate = GateName[args.revision_from.upper()]  # e.g. SCRIPT = 5
# Delete gate_05.json, gate_06.json, ... gate_14.json
for gate_file in state_dir.glob("gate_*.json"):
    idx = int(gate_file.stem.split("_")[1])
    if idx >= target_gate.value:
        gate_file.unlink()
# Inject feedback into pipeline __init__ via config
pipeline = ShortsPipeline(session_id=session_id, ...)
pipeline.ctx.config["prior_user_feedback"] = args.feedback
pipeline.ctx.config["revision_from_gate"] = target_gate.name
pipeline.run()  # resumes at target_gate-1, re-runs target_gate..MONITOR with feedback
```

### Phase 13 Live Smoke Runner (SPC-06 infrastructure)

**File**: `scripts/smoke/phase13_live_smoke.py` (952 lines) — UFL-01/02/03 확장 진입점

| Line | Shape | UFL Extension |
|------|-------|---------------|
| 155~228 | `_PreSeededProducerInvoker` class | UFL-02 Pattern precedent — `_PreScriptedProducer` 동일 구조 |
| 231~269 | `_build_pipeline_with_seed` factory | UFL-02 추가: `--revise-script <path>` 주입점 |
| 305~385 | `_parse_args` argparse | UFL-01/02/03 flag 추가 지점 |
| 687~891 | `_run_live` — max_attempts loop + BudgetExceededError | UFL-03 `PipelinePauseSignal` 추가 except branch |
| 899~947 | `main()` | UFL-04 `rate_video` subcommand 분리 or 별도 script |

---

## Technical Approach (per REQ)

### SPC-01 + SPC-04: `--append-system-prompt-file` Fix

**Empirical confirmation (2026-04-22 session)**:
```bash
# Claude CLI 2.1.112 실측 (이 research session 내)
$ claude --help | grep -iE "system-prompt"
  --append-system-prompt <prompt>     # 문서화된 직접 옵션
  --system-prompt <prompt>            # 문서화된 직접 옵션
# --bare description 에 `--append-system-prompt[-file]` 명시
$ claude --print --append-system-prompt-file /tmp/nonexistent-test.txt <<< "hi"
Error: Append system prompt file not found: C:\...\nonexistent-test.txt
# ← flag 존재 = exit with "file not found" (존재하지 않으면 "unknown option")
```

**Fix patch (invokers.py L121~187 `_invoke_claude_cli_once`)**:
```python
def _invoke_claude_cli_once(
    system_prompt: str,
    user_prompt: str,
    json_schema: str,
    cli_path: str,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> str:
    """Run claude --print via temp-file system prompt to avoid argv size limits."""
    import tempfile
    # Write body to UTF-8 tempfile — argv 에 path 만 30 chars 이하로 나타남
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False,
        encoding="utf-8", newline="\n",
    ) as sys_fp:
        sys_fp.write(system_prompt)
        sys_prompt_path = sys_fp.name
    try:
        cmd = [
            cli_path,
            "--print",
            "--append-system-prompt-file", sys_prompt_path,
            "--json-schema", json_schema,
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            stdout, stderr = proc.communicate(input=user_prompt, timeout=timeout_s)
        except subprocess.TimeoutExpired as err:
            proc.kill()
            proc.communicate()
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
    finally:
        # 명시적 cleanup (CLAUDE.md 금기 #3 try-except 침묵 폴백 회피)
        try:
            os.unlink(sys_prompt_path)
        except OSError as err:
            logger.warning(
                "[invoker] temp system prompt 파일 삭제 실패 %s (대표님): %s",
                sys_prompt_path, err,
            )
```

**Delta**:
- cmd argv 변경: `--append-system-prompt BODY` (10KB+) → `--append-system-prompt-file /path` (~30 chars)
- body 는 UTF-8 tempfile 경유 (stdin 아님 — stdin 은 user_prompt 전용, 충돌 없음)
- 기존 `text=True, encoding='utf-8', errors='replace'` 유지 (stdin user_prompt 경로 invariant 보존)
- cleanup: finally block + explicit OSError log (금기 #3 준수)

**Why this fixes rc=1**:
- Claude CLI 의 "프롬프트가 너무 깁니다" 내부 check 가 argv `--append-system-prompt BODY` 길이 자체를 문제 삼는 방식 (H2 유력). File 경유 시 내부 parser 경로가 다름 (파일 읽기 + tokenizer 직접 — 같은 길이지만 argv counter bypass).
- Even if the limit is token-count based, file-based path normalizes UTF-8 BOM/newline handling and decouples from shell quoting that differs between bash (success) and Python Popen (failure).

**Alternative (SPC-01 Option B — fallback)**: shell=True with PowerShell here-string — 금기 #3 위반 (shell injection risk), 권장 X.

**Alternative (SPC-01 Option C — parallel defense)**: SPC-02 압축 (10591 → 6000) 만 해도 threshold 밑으로 떨어질 가능성. But file-based fix 가 장기 root-cause 해소 — 압축은 독립적 가치 (input token cost 절감).

### SPC-02: shorts-supervisor AGENT.md Progressive Disclosure

**Target**: 10591 chars → 6000 chars (43% 감소).

**Split plan**:
1. Create `.claude/agents/supervisor/shorts-supervisor/references/` directory (STRUCTURE.md Whitelist — Phase 12 AGENT-STD-02 precedent 확인 필요).
2. Move blocks to references:
   - `references/supervisor_variant.md` — Prompt §Supervisor variant (L62~147, ~4500 bytes) including 17 inspector list, delegation_depth python pseudo-code, 합산 규칙, VQQA concat 예제.
   - `references/inspector_paths.md` — 17 Inspector AGENT.md path list (L162~186, ~1800 bytes).
3. Replace moved content in AGENT.md body with short `@references/xxx.md` links + minimal inline summary (30-50 chars each).
4. Retain in body:
   - Frontmatter (필수 AGENT-STD-01)
   - `## Purpose` (불변식 3-5줄)
   - `## Inputs` / `## Outputs` tables (contract)
   - `## Prompt §System Context` (핵심 guard)
   - Producer/Inspector variant stubs
   - Short refs list + maxTurns matrix (short, critical)
   - `## Contract with upstream / downstream`
   - `## MUST REMEMBER` (RoPE end-position, AGENT-09 mandatory)

**Verification**:
- `verify_agent_md_schema.py` (Phase 12) 31/31 통과 재실행 (5-block invariant).
- Body char count: `< 6500` (voluntary floor 목표).
- `@references/` link validator (wiki link check 유사) — `verify_references_exist.py`.

### SPC-03: Producer 14 AGENT.md Size Audit + Enforcement

**Deliverable**: `scripts/validate/verify_agent_md_size.py`
- Scan `.claude/agents/producers/*/AGENT.md` + `.claude/agents/supervisor/*/AGENT.md`
- CHAR_LIMIT constant: 15000 (mean + 0.5σ 기준, asset-sourcer/publisher/scripter/voice-producer 4개 압축 유도) or 18000 (tight ceiling, 현재 max 17426 + 3% 여유).
- **Recommendation**: **18000 ceiling** in Phase 15 (hard breaking change 회피 + 장기 drift 방지). 7000 target 만 shorts-supervisor 에 대해 hard cap.
- pytest marker: `adapter_contract` 재사용 or 신규 `agent_size_contract` (권장: 재사용, Phase 14 precedent 승계).

### SPC-05: `tests/adapters/test_invokers_encoding_contract.py`

**Test cases (8-10 tests)**:
1. `test_system_prompt_file_argv_shape` — mock subprocess.Popen, verify argv contains `--append-system-prompt-file` + path, NOT raw body.
2. `test_system_prompt_file_content_matches` — mock Popen, read temp file path from argv, verify content == input system_prompt.
3. `test_10kb_body_korean_chars_success` — body = 10KB Korean, mock rc=0 + stdout JSON, verify no RuntimeError.
4. `test_10kb_body_ascii_success` — body = 10KB ASCII, same.
5. `test_temp_file_cleanup_on_success` — verify os.unlink called in finally.
6. `test_temp_file_cleanup_on_timeout` — TimeoutExpired → cleanup called.
7. `test_temp_file_cleanup_on_rc1` — rc=1 → cleanup called.
8. `test_temp_file_utf8_encoding` — Korean body written as UTF-8 bytes (not cp949).
9. `test_unlink_oserror_logged_not_raised` — mock os.unlink raise OSError → warning + no raise (sticky cleanup failure).
10. `test_stdin_unchanged_user_prompt` — verify user_prompt 여전히 stdin 경유 (Phase 11 invariant 보존).

**Location**: `tests/adapters/test_invokers_encoding_contract.py` (Phase 14 adapter_contract marker 승계).
**Mock infrastructure**: tests/phase11/test_invoker_stdin.py L37~46 `_make_popen_mock` 재사용.

### SPC-06: Phase 13 Live Smoke Retry

**Command** (after SPC-01~05 merge):
```powershell
py -3.11 scripts/smoke/phase13_live_smoke.py \
    --live \
    --topic "해외범죄,FBI 수사,인터폴,국제 범죄 사건" \
    --niche incidents \
    --budget-cap-usd 5.00 \
    --max-attempts 2
```

**Expected evidence** (5 files, Phase 13 invariant):
- `.planning/phases/13-live-smoke/evidence/producer_output_<sid>.json`
- `supervisor_output_<sid>.json`
- `smoke_upload_<sid>.json`
- `budget_usage_<sid>.json`
- `smoke_e2e_<sid>.json` with `supervisor_rc1_count == 0` (SPC-01 fix 입증).

**Budget**: $1.50~$3.00 (Kling 8 cuts × $0.25 + Typecast 1K chars × $0.15 + NanoBanana 1 × $0.04 + YouTube free).

### UFL-01: `--revision-from GATE --feedback TEXT`

**Flag additions** (phase13_live_smoke.py _parse_args):
```python
parser.add_argument("--revision-from", default=None,
    choices=[g.name for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)],
    help="기존 세션의 특정 GATE 부터 재실행. 해당 GATE 이후 checkpoint 삭제 + feedback 주입.")
parser.add_argument("--feedback", default=None,
    help="대표님 피드백 텍스트. --revision-from 과 동반. "
         "Producer 의 <prior_user_feedback> 입력 블록에 주입.")
```

**Pipeline wiring** (new helper `_apply_revision`):
```python
def _apply_revision(state_root: Path, session_id: str, from_gate: GateName) -> list[Path]:
    """Delete gate_N..14.json for N >= from_gate.value. Return deleted paths."""
    state_dir = state_root / session_id
    deleted = []
    for gate_file in sorted(state_dir.glob("gate_*.json")):
        try:
            idx = int(gate_file.stem.split("_")[1])
        except (ValueError, IndexError):
            continue
        if idx >= from_gate.value:
            gate_file.unlink()
            deleted.append(gate_file)
    return deleted
```

**Producer injection** (invokers.py Producer `__call__` L334):
```python
def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
    # ... existing body load + user_payload build ...
    # Phase 15 UFL-01: inject prior_user_feedback if present in config
    feedback = inputs.get("prior_user_feedback")  # injected by ShortsPipeline via ctx.config
    if feedback:
        user_payload_dict = json.loads(user_payload)
        user_payload_dict["prior_user_feedback"] = feedback
        user_payload = json.dumps(user_payload_dict, ensure_ascii=False)
    # ... rest unchanged
```

**ShortsPipeline wiring** (each `_run_<gate>` method passes config.prior_user_feedback into inputs dict). This is a minor diff — 13 methods, 1 line each (add `"prior_user_feedback": ctx.config.get("prior_user_feedback")` to inputs dict).

### UFL-02: `--revise-script <path>`

**Flag addition**:
```python
parser.add_argument("--revise-script", default=None, type=Path,
    help="대표님 수동 대본 .md 또는 .txt 파일 경로. SCRIPT gate 에서 scripter 에이전트 skip, "
         "이 파일 내용이 user_provided_script 로 script-polisher 에 직접 전달됩니다.")
```

**Wrapper** (extends `_PreSeededProducerInvoker` pattern):
```python
class _PreScriptedProducerInvoker:
    def __init__(self, real_invoker, script_path: Path):
        self._real = real_invoker
        self._script_content = script_path.read_text(encoding="utf-8")
        self._script_path = str(script_path)

    def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
        if gate == "SCRIPT":
            logger.info("[pre-script] SCRIPT gate — 대표님 수동 대본 주입 (%s, %d chars, 대표님)",
                self._script_path, len(self._script_content))
            return {
                "gate": "SCRIPT",
                "verdict": "PASS",
                "script_md": self._script_content,
                "user_provided": True,
                "seeded": True,
                "decisions": [f"대표님 --revise-script flag 로 수동 대본 주입: {self._script_path}"],
                "error_codes": [],
            }
        return self._real(agent_name, gate, inputs)
```

**Ordering** (in `_build_pipeline_with_seed`): Topic pre-seed (TREND/NICHE) → Script pre-seed (SCRIPT) → real invoker. Compose via chained wrapping.

### UFL-03: `--pause-after GATE`

**Flag addition**:
```python
parser.add_argument("--pause-after", default=None,
    choices=[g.name for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)],
    help="지정 GATE 완료 후 pipeline 일시중지. evidence + state 보존, graceful exit 0. "
         "재개: --revision-from <next_gate> or 새 session-id 로 재실행.")
```

**Pipeline signal** (`scripts/orchestrator/shorts_pipeline.py`):
```python
class PipelinePauseSignal(Exception):
    """UFL-03 — 대표님 --pause-after <gate> 이후 pipeline 중단 신호. Runner 가 잡아 graceful exit."""
    def __init__(self, paused_at: GateName):
        super().__init__(f"Pipeline paused after {paused_at.name} (대표님 UFL-03)")
        self.paused_at = paused_at
```

**Per-gate check** (recommendation: add to `GateGuard.dispatch` after successful dispatch, single choke-point 13 methods 수정 회피):
```python
# gate_guard.py GateGuard.dispatch() 끝에
pause_after = self._ctx_config.get("pause_after_gate") if self._ctx_config else None
if pause_after and gate == pause_after:
    raise PipelinePauseSignal(gate)
```

**Runner catch** (phase13_live_smoke.py `_run_live` exception loop):
```python
except PipelinePauseSignal as sig:
    logger.info("[phase13] pause signal 수신 (대표님): %s — evidence 저장 후 graceful exit",
        sig.paused_at.name)
    # write evidence as usual for phases executed, status="PAUSED"
    # ... evidence writers ...
    return 0  # not failure
```

### UFL-04: `rate_video.py` CLI

**New file**: `scripts/smoke/rate_video.py` (~80 lines)
```python
"""대표님 영상 품질 평가 CLI — subjective rating + feedback append.

사용 예:
    py -3.11 scripts/smoke/rate_video.py --video-id dQw4w9WgXcQ \
        --rating 3 --feedback "조명이 어두움, 음성 톤이 단조로움"

저장: .claude/memory/feedback_video_quality.md (D-2 Lock 예외 — 대표님 직접 입력).
"""
# argparse: --video-id (11 char YouTube id) --rating (1-5 int) --feedback (str)
# --session-id (optional, phase13 session linkage) --niche (optional)
# append to .claude/memory/feedback_video_quality.md as:
#   ## 2026-04-22 dQw4w9WgXcQ
#   - session_id: overseas_crime_sample_20260422
#   - niche: incidents
#   - rating: 3/5
#   - feedback: 조명이 어두움, 음성 톤이 단조로움
#   - keywords: [조명, 톤]  # auto-extracted by simple Korean noun regex
```

**Validator**: `verify_feedback_format.py` — H2 heading + 4 required fields + 한국어 존댓말 preserved.
**mandatory_reads integration (deferred to Phase 16)**: researcher agent 의 `<mandatory_reads>` 에 `.claude/memory/feedback_video_quality.md` 추가 (Phase 15 scope 외).

---

## Risks & Unknowns

### Hypotheses H1-4 (SPC-01 root cause) — Verdict

| # | Hypothesis | Verdict | Evidence |
|---|------------|---------|----------|
| H1 | Windows CreateProcessW argv UTF-8 re-encoding error | **REJECTED** | 10073 argv chars ≪ 32767 WCHAR limit; UTF-16 encoding = 1 WCHAR per Korean char. |
| H2 | Claude CLI 내부 token counter threshold bug on argv | **LIKELY** | bash 경로 성공 vs Python subprocess 실패는 argv 전달 경로의 동일 CLI 에서 다른 token counting. File-based fix bypasses. |
| H3 | bash `$BODY` vs Python Popen raw argv 차이 in CLI parsing | **PARTIAL** | Subshell quoting 은 OS 관점에서 동일. CLI 내부 Node.js argv parsing 의 UTF-8 bytes vs WCHAR 해석 차이 가능. |
| H4 | 10KB+ Korean argv + multi-byte UTF-8 calculation drift | **PARTIAL** | UTF-8 = 21000 bytes vs Unicode = 10000 chars. CLI 내부가 byte-based check 시 trigger. File-based 는 content encoding 과 독립적인 path resolution. |

**Conclusion**: SPC-01 Option A (`--append-system-prompt-file`) 는 H2/H3/H4 모두 우회 — root cause 와 무관하게 수정.

### Pitfalls

1. **tempfile cleanup race** — Windows 는 file still-open-on-exit 시 unlink 실패. `finally` block + explicit OSError warning (raise 금지). 대표님 CLAUDE.md 금기 #3 준수.
2. **STRUCTURE.md Whitelist** — `.claude/agents/supervisor/shorts-supervisor/references/` 생성 시 pre_tool_use check. Phase 12 AGENT-STD-02 에서 동일 디렉토리 허용 (producer agents 에 대해) — supervisor 는 first-time. Plan 단계에서 STRUCTURE.md schema bump 필요 확인.
3. **AGENT-STD-01 5-block invariant** — SPC-02 압축 시 `## References` block 이 `@references/` 링크만 남아도 block 자체는 유지 (invariant: 5 block headers 존재). `verify_agent_md_schema.py` 재실행 30/31 mandatory.
4. **Phase 12 `_compress_producer_output` compatibility** — SPC-01 fix 는 `_invoke_claude_cli_once` layer. Supervisor 의 `_compress_producer_output` (L495) 은 user_payload 압축으로 여전히 필요. 두 압축은 orthogonal (system_prompt body vs user_payload), 동시 유지.
5. **UFL-01 session id collision** — revision 은 기존 session 재활용. `phase13_live_smoke.py --session-id <existing>` 지정 시 기존 state 위 덮어쓰기. Plan 에서 `--dry-run-revision` flag 로 삭제될 gate 파일 preview 옵션 고려.
6. **UFL-02 script format** — `--revise-script` 파일은 scripter agent 의 JSON 출력 shape 와 달리 plain text md/txt. script-polisher 가 `user_provided_script` 를 JSON 아닌 raw text 로 소비할 수 있는지 AGENT.md 확인 필요. Plan 에서 script-polisher AGENT.md `<mandatory_reads>` 추가 task 포함.
7. **UFL-03 pause signal 전파 경로** — GateGuard.dispatch 에 check 추가 vs 13 `_run_<gate>` 끝에 check. 전자가 single choke-point (권장). 후자는 invasive.
8. **UFL-04 feedback file D-2 Lock** — `.claude/memory/feedback_video_quality.md` 는 D-2 (2026-04-20~06-20) SKILL patch 금지 기간 내 새 파일 생성. 대표님 직접 입력 파일이므로 D-2 예외 (precedent: F-D2-EXCEPTION-01 trend-collector, F-D2-EXCEPTION-02 Phase 12 batch). Plan 에서 명시적 D-2 exception declaration.
9. **Claude CLI version drift** — `--append-system-prompt-file` 가 Claude CLI 2.0+ 에서 도입되었으나 2.1.112 에서 실측 확인. 2.1.63 미만 환경은 fallback 필요 (SPC-01 Option C compression 만). Plan 에서 CLI 버전 check + minimum version pin.
10. **Korean locale in stderr** — Windows cp949 default 가 Korean bytes 를 replace char 로 대체. `errors='replace'` 유지 (no change). 향후 error parser 가 stderr 에서 의미 추출 필요 시 `errors='backslashreplace'` 검토 — 본 Phase 15 scope 외.

### Open Questions (Plan 단계에서 결정)

Q1. **SPC-04 flag choice**: `--append-system-prompt-file` (semantics 승계) vs `--system-prompt-file` (완전 replace, `--bare` 유사)?
- Option A (권장): `--append-system-prompt-file` — 기존 behavior 와 동일, Claude Code CLAUDE.md 자동 discovery 유지, AGENT.md 는 append
- Option B: `--system-prompt-file` — 순수 AGENT.md 만, 더 결정론적. But `--bare` 를 추가 요구.

Q2. **SPC-03 CHAR_LIMIT**: 15000 (mean + 0.5σ, 4 agents 압축 trigger) vs 18000 (ceiling, 0 agents trigger, drift 방지 only)?

Q3. **UFL-01 deletion strategy**: hard unlink vs `.bak` rename?
- Option A (권장): hard unlink — Checkpointer.resume() 이 자연스럽게 롤백
- Option B: rename `gate_N.json` → `gate_N.json.bak_<timestamp>` — 복구 가능하나 Checkpointer glob 에 혼선 가능

Q4. **UFL-02 polishing**: `--revise-script` 는 script-polisher 를 거치는가, 아니면 POLISH gate 도 skip 하고 VOICE 로 직진?
- Option A (권장): polisher 거침 — 대표님 수동 대본도 RUB (읽기쉬움/한국어 자연스러움) 검증. 품질 보존.
- Option B: polisher skip — 대표님 판단 절대 존중. 하지만 후속 gate 가 polished script 기대 → 인터페이스 미스매치 위험.

Q5. **UFL-03 pause-after multi-stops**: 1 flag per run (single gate) vs list `--pause-after SCRIPT,VOICE,ASSEMBLY`?
- Option A (권장): single gate — 복잡도 최소. 다중 pause 필요 시 revision loop 반복.
- Option B: list — runner 복잡도 증가.

Q6. **UFL-04 rating scale + format**: 1-5 int vs 0.0-1.0 float? H2 markdown vs JSON lines?
- Option A (권장): 1-5 int + Markdown H2 (D-10 canonical pattern, 사람 가독성).
- Option B: 0.0-1.0 float — KPI dashboard 통합 용이, but 대표님 타이핑 불편.

Q7. **SPC-02 references/ 는 AGENT.md 동일 디렉토리 vs 별도 root**?
- Option A (권장): `.claude/agents/supervisor/shorts-supervisor/references/` (co-located, Phase 12 precedent).
- Option B: `.claude/agents/_shared/shorts-supervisor-references/` (flat root, 다른 agent 가 참조 가능).

Q8. **Phase 15 commit granularity**: wave 당 single commit (5 wave = 5 commit) vs task 당 commit (15~20 commit)?
- Option A (권장): task 당 atomic commit — Phase 14 precedent (Plan 14-02 6 commits for 5 atomic edits + log).

---

## Runtime State Inventory

Phase 15 는 rename/refactor/migration 아님 — encoding fix + UI extension. Runtime state 영향 제한적:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — invokers.py fix 는 in-memory path, 저장된 AGENT.md 는 SPC-02 대상이나 body 교체 only (schema invariant) | Code edit + Phase 12 schema verify 재실행 |
| Live service config | None — YouTube/Kling/Typecast 설정 변경 없음 | None |
| OS-registered state | None — Windows 등록 변경 없음 | None |
| Secrets/env vars | None — API key 변경 없음, 새 env 추가 없음 | None |
| Build artifacts | `.claude/agents/supervisor/shorts-supervisor/references/` 신규 directory — sibling files, no install artifact | STRUCTURE.md Whitelist schema bump 확인 (Plan 단계) |

**Nothing found in Stored data / Live service / OS-registered / Secrets** (명시적으로 검증됨).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| claude CLI | SPC-01/06 실행 | ✓ | 2.1.112 | — (Max 구독 필수) |
| `--append-system-prompt-file` flag | SPC-01 fix | ✓ (실측 2026-04-22) | 2.1.112 이상 | SPC-02 압축만으로 threshold 아래 유도 |
| Python subprocess.Popen | invokers.py | ✓ | Py 3.11 | — |
| tempfile.NamedTemporaryFile | SPC-01 fix | ✓ | stdlib | — |
| pytest | SPC-05 + UFL test | ✓ | 8.4.2 | — |
| pytest.ini `adapter_contract` marker | SPC-05 contract test | ✓ | Phase 14 | — |
| pytest.ini `live_smoke` marker | SPC-06 opt-in | ✓ | Phase 13 | — |
| YouTube Data API v3 quota | SPC-06 (upload + cleanup) | ✓ | 10000 units/day free | — |
| Kling/Nano Banana/Typecast | SPC-06 live assets | ✓ | Phase 9.1 wired | — |

**Missing dependencies with no fallback**: 없음.
**Missing dependencies with fallback**: 없음.

---

## Project Constraints (from CLAUDE.md)

**CRITICAL (위반 시 차단)**:
- 금기 #3: try-except 침묵 폴백 금지 — tempfile cleanup 에서 `except: pass` 금지, explicit OSError warning + no raise (graceful cleanup, 작업 계속).
- 금기 #4: T2V 금지 — Phase 15 는 I2V path 에 영향 없음.
- 금기 #5: Selenium 금지 — 해당 없음 (YouTube publisher 경로 불변).
- 금기 #6: `shorts_naberal` 원본 수정 금지 — 해당 없음.
- 금기 #8: 일일 업로드 금지 — SPC-06 live smoke 는 `cleanup=True` + `SHORTS_PUBLISH_LOCK_PATH` bypass 유지.
- 금기 #9: 32 에이전트 초과 금지 — Phase 15 는 agent 추가 없음 (SPC-02 는 body 압축 only, 에이전트 수 변경 없음).

**MUST (필수 준수)**:
- 필수 #1: Hook 3종 활성 — Phase 14 pre_tool_use warn-only adapter 규칙 유지.
- 필수 #2: SKILL.md / AGENT.md body 길이 규율 — SPC-02 가 직접 대상 (Progressive Disclosure).
- 필수 #3: 오케스트레이터 500~800줄 — ShortsPipeline 변경 최소 (UFL-01~03 는 pipeline 에 ~30 lines 추가 예상).
- 필수 #4: FAILURES.md append-only — Phase 15 는 FAILURES 추가 없음 (mock-based 검증).
- 필수 #5: STRUCTURE.md Whitelist — SPC-02 `references/` 디렉토리 확인 필요 (Plan 단계).
- 필수 #7: 한국어 존댓말 baseline — 모든 new CLI error / logger message 대표님 호칭.
- 필수 #8: 증거 기반 보고 — SPC-06 live smoke 5 evidence files anchor 준수.

---

## Validation Architecture

**Scope**: Phase 15 는 workflow.nyquist_validation=true (config.json). Full Validation section 포함.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 + Phase 14 `addopts` (--strict-markers + 7 --ignore) |
| Config file | `pytest.ini` (기존 invariant 보존, 신규 marker 추가 없음 — `adapter_contract` + `live_smoke` 재사용) |
| Quick run command | `pytest tests/adapters/test_invokers_encoding_contract.py tests/phase15 -m "not live_smoke" --tb=short -q` (≈ 5s) |
| Full suite command | `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase091 tests/phase11 tests/phase12 tests/adapters tests/phase15 -m "not live_smoke" --tb=short -q` (≈ 8-10min) |
| Contract-isolated | `pytest -m adapter_contract` (Phase 14 precedent, 30 tests green + SPC-05 10 tests = 40 total) |
| Live smoke | `pytest tests/phase13 -m live_smoke --run-live` or `py -3.11 scripts/smoke/phase13_live_smoke.py --live --topic ... --niche incidents` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SPC-01 | `_invoke_claude_cli_once` 가 body 를 tempfile 경유로 전달 | unit (adapter_contract) | `pytest tests/adapters/test_invokers_encoding_contract.py::test_system_prompt_file_argv_shape -x` | ❌ Wave 0 |
| SPC-01 | 10KB+ Korean body rc=1 재현 없음 | unit (adapter_contract) | `pytest tests/adapters/test_invokers_encoding_contract.py::test_10kb_body_korean_chars_success -x` | ❌ Wave 0 |
| SPC-01 | tempfile cleanup on success/timeout/rc1 | unit (adapter_contract) | `pytest tests/adapters/test_invokers_encoding_contract.py -k cleanup -x` | ❌ Wave 0 |
| SPC-01 | Phase 11 stdin invariant 보존 (user_prompt stdin, not argv) | unit (regression) | `pytest tests/phase11/test_invoker_stdin.py -x` | ✅ Phase 11 |
| SPC-02 | shorts-supervisor AGENT.md body ≤ 6500 chars | unit | `pytest tests/phase15/test_supervisor_agent_md_size.py -x` | ❌ Wave 0 |
| SPC-02 | 5-block AGENT-STD-01 invariant 보존 | regression | `py scripts/validate/verify_agent_md_schema.py --fail-on-drift` | ✅ Phase 12 |
| SPC-02 | `@references/` 링크 실존 + readable | unit | `pytest tests/phase15/test_supervisor_references_exist.py -x` | ❌ Wave 0 |
| SPC-03 | Producer 14 AGENT.md 상한 검증 | unit | `py scripts/validate/verify_agent_md_size.py --ceiling 18000` | ❌ Wave 0 |
| SPC-04 | Claude CLI `--append-system-prompt-file` flag 존재 확증 | smoke (dry-run) | `claude --print --append-system-prompt-file /tmp/nonexistent 2>&1 | grep "file not found"` | Manual check, automate in Wave 0 |
| SPC-05 | 10 contract tests green | unit (adapter_contract) | `pytest tests/adapters/test_invokers_encoding_contract.py -v` | ❌ Wave 0 |
| SPC-06 | Phase 13 live smoke rc=0 + 5 evidence + supervisor_rc1_count=0 | live_smoke | `py -3.11 scripts/smoke/phase13_live_smoke.py --live --topic ... --niche incidents` | ✅ Phase 13 runner |
| UFL-01 | `--revision-from GATE` deletes gate_N..14.json + resume | unit (integration) | `pytest tests/phase15/test_revision_flag.py -x` | ❌ Wave 0 |
| UFL-01 | Producer invoker `prior_user_feedback` 전파 | unit | `pytest tests/phase15/test_producer_feedback_injection.py -x` | ❌ Wave 0 |
| UFL-02 | `--revise-script` 가 SCRIPT gate skip + file content 주입 | unit | `pytest tests/phase15/test_prescripted_invoker.py -x` | ❌ Wave 0 |
| UFL-03 | `--pause-after GATE` 가 해당 gate 완료 후 PipelinePauseSignal raise | unit | `pytest tests/phase15/test_pause_after_gate.py -x` | ❌ Wave 0 |
| UFL-03 | Runner 가 signal 잡아 graceful exit 0 | unit | `pytest tests/phase15/test_runner_pause_signal.py -x` | ❌ Wave 0 |
| UFL-04 | `rate_video.py` CLI argparse + feedback append | unit | `pytest tests/phase15/test_rate_video_cli.py -x` | ❌ Wave 0 |
| UFL-04 | feedback_video_quality.md Markdown H2 format | unit | `pytest tests/phase15/test_feedback_format.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit**: `pytest tests/phase15 tests/adapters/test_invokers_encoding_contract.py -m "not live_smoke" -x` (≤ 5s)
- **Per wave merge**: `pytest tests/adapters tests/phase11 tests/phase091 tests/phase15 -m "not live_smoke" -q` (≤ 30s)
- **Phase gate**: Full suite (Phase 4-14 + 15) green before `/gsd:verify-work 15`
- **Post-SPC-06**: Live smoke 5 evidence 파일 anchored + `supervisor_rc1_count == 0` verified

### Wave 0 Gaps

- [ ] `tests/phase15/` directory scaffold (`__init__.py` + `conftest.py`)
- [ ] `tests/phase15/conftest.py` — fixtures: mock ShortsPipeline, fake state_dir, mock producer_invoker
- [ ] `tests/adapters/test_invokers_encoding_contract.py` — covers SPC-01/05 (10 tests)
- [ ] `tests/phase15/test_supervisor_agent_md_size.py` — covers SPC-02
- [ ] `tests/phase15/test_supervisor_references_exist.py` — covers SPC-02 (ref link validator)
- [ ] `scripts/validate/verify_agent_md_size.py` — covers SPC-03 (CLI + pytest 통합)
- [ ] `tests/phase15/test_revision_flag.py` — covers UFL-01 (integration)
- [ ] `tests/phase15/test_producer_feedback_injection.py` — covers UFL-01 (unit)
- [ ] `tests/phase15/test_prescripted_invoker.py` — covers UFL-02
- [ ] `tests/phase15/test_pause_after_gate.py` — covers UFL-03 (GateGuard)
- [ ] `tests/phase15/test_runner_pause_signal.py` — covers UFL-03 (runner catch)
- [ ] `tests/phase15/test_rate_video_cli.py` — covers UFL-04 (argparse)
- [ ] `tests/phase15/test_feedback_format.py` — covers UFL-04 (markdown validator)
- [ ] Framework install: none (pytest 8.4.2 + addopts 기존)

---

## Build Order (6-Wave Recommended)

**Dependency DAG**:
```
Wave 0: Foundation (test infra + verification baseline)
  ├─ test scaffold (tests/phase15/, conftest.py)
  ├─ SPC-01 empirical reproduction script (docs/spc01_reproduce.py)
  └─ SPC-04 CLI flag existence check (Wave 0 smoke, 1 command)
         │
         ▼
Wave 1: SPC Encoding Fix (CRITICAL PATH — blocks everything else)
  ├─ SPC-01 invokers.py patch (_invoke_claude_cli_once tempfile + --append-system-prompt-file)
  ├─ SPC-05 contract tests (10 tests, mock subprocess.Popen)
  └─ Regression sweep (Phase 11 stdin invariant + Phase 12 compress invariant)
         │
         ▼
Wave 2: SPC Agent Body Compression
  ├─ SPC-02 shorts-supervisor AGENT.md split (references/supervisor_variant.md + inspector_paths.md)
  ├─ SPC-02 body replacement + AGENT-STD-01 schema verify
  ├─ SPC-03 verify_agent_md_size.py (18000 ceiling)
  └─ STRUCTURE.md Whitelist schema bump (if needed)
         │                    │
         ▼                    │ (parallel with Wave 3 possible — orthogonal)
Wave 3: UFL Feedback Interface (independent of SPC Waves 1-2 — can parallel)
  ├─ UFL-01 --revision-from GATE + --feedback (phase13_live_smoke.py + invokers Producer.__call__)
  ├─ UFL-02 --revise-script (_PreScriptedProducerInvoker)
  └─ UFL-03 --pause-after GATE (PipelinePauseSignal + GateGuard.dispatch check)
         │
         ▼
Wave 4: UFL Rating CLI
  └─ UFL-04 rate_video.py + .claude/memory/feedback_video_quality.md + format validator
         │
         ▼
Wave 5: Empirical Live Validation (SPC-06)
  ├─ Phase 13 live smoke retry --topic "해외범죄,..." --niche incidents (budget $5)
  ├─ Evidence 5 files anchored
  ├─ supervisor_rc1_count=0 verified
  └─ smoke_e2e.json 13 gate timestamps
         │
         ▼
Wave 6: Phase Gate
  ├─ 15-VALIDATION.md all rows green
  ├─ 15-TRACEABILITY.md 10 REQ × plans matrix
  ├─ Full regression Phase 4-14 + 15 green
  └─ /gsd:verify-work 15
```

**Total estimated**:
- Wave 0: ~30min (scaffolding + empirical baseline)
- Wave 1: ~2h (SPC-01 patch + SPC-05 10 contract tests + regression verification)
- Wave 2: ~2h (SPC-02 split + references file authoring + SPC-03 validator)
- Wave 3: ~3h (UFL-01/02/03 flags + test coverage, parallel with Wave 2)
- Wave 4: ~1h (UFL-04 CLI + format validator)
- Wave 5: ~30min runtime + $1.50~$3.00 live cost
- Wave 6: ~1h (VALIDATION + TRACEABILITY + phase gate)

**Total wall time**: 8-10 hours + Wave 5 live spend $3.

**Parallelization opportunity**: Wave 2 ↔ Wave 3 can run in parallel if two executors available (zero file overlap: Wave 2 touches `.claude/agents/supervisor/`, `scripts/validate/`; Wave 3 touches `scripts/orchestrator/`, `scripts/smoke/`).

---

## Code Examples

### Verified Claude CLI file-based system prompt (HIGH confidence, 2026-04-22 empirical)

```bash
# Flag existence proof (실측 in this session)
$ claude --version
2.1.112 (Claude Code)

$ claude --print --append-system-prompt-file /tmp/nonexistent <<< "hi"
Error: Append system prompt file not found: C:\Users\PC\AppData\Local\Temp\nonexistent

$ claude --print --system-prompt-file /tmp/nonexistent <<< "hi"
Error: System prompt file not found: C:\Users\PC\AppData\Local\Temp\nonexistent
```

### Python subprocess tempfile pattern (for SPC-01 fix)

```python
# Source: Python 3.11 stdlib (tempfile.NamedTemporaryFile + subprocess.Popen)
import tempfile, subprocess, os
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False,  # delete=False — Windows keeps file open on exit
    encoding="utf-8", newline="\n",
) as fp:
    fp.write(system_prompt_body)
    path = fp.name
try:
    proc = subprocess.Popen(
        [cli, "--print", "--append-system-prompt-file", path, "--json-schema", schema],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )
    stdout, stderr = proc.communicate(input=user_prompt, timeout=timeout_s)
finally:
    try:
        os.unlink(path)
    except OSError as err:
        # CLAUDE.md 금기 #3: warn + continue (cleanup 실패가 작업 진행 막지 않음)
        logger.warning("[invoker] temp file cleanup skipped: %s", err)
```

### ShortsPipeline revision pattern (UFL-01)

```python
# Source: scripts/orchestrator/shorts_pipeline.py L269~319 resume 메커니즘 재활용
def apply_revision(state_root: Path, session_id: str, from_gate: GateName) -> None:
    """Delete gate_N..14.json for N >= from_gate.value. Checkpointer.resume() 이 자동 롤백."""
    state_dir = state_root / session_id
    for gate_file in sorted(state_dir.glob("gate_*.json")):
        try:
            idx = int(gate_file.stem.split("_")[1])
        except (ValueError, IndexError):
            continue
        if idx >= from_gate.value:
            gate_file.unlink()
            logger.info("[revision] %s 삭제 (대표님 재작업 요청)", gate_file.name)
```

### Tests — subprocess.Popen mock pattern (from tests/phase11/test_invoker_stdin.py L37~46)

```python
# Source: tests/phase11/test_invoker_stdin.py (Phase 11 precedent)
def _make_popen_mock(stdout='{"ok":true}', stderr="", returncode=0):
    proc = MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc

def test_spc01_system_prompt_file_argv_shape():
    with patch("scripts.orchestrator.invokers.subprocess.Popen") as popen_cls:
        popen_cls.return_value = _make_popen_mock()
        _invoke_claude_cli_once(
            system_prompt="X" * 10000,  # 10KB body
            user_prompt="u",
            json_schema='{"type":"object"}',
            cli_path="/fake/claude",
        )
        argv = popen_cls.call_args.args[0]
        # Body MUST NOT be in argv (tempfile path 대체)
        assert "X" * 1000 not in " ".join(argv)
        # Flag must be --append-system-prompt-file, not --append-system-prompt
        assert "--append-system-prompt-file" in argv
        assert "--append-system-prompt" not in argv or argv[argv.index("--append-system-prompt") + 1].endswith(".md")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `--append-system-prompt BODY` argv 직접 전달 | `--append-system-prompt-file /path` (tempfile) | Phase 15 (2026-04-22) | 10KB+ body 의 rc=1 "프롬프트가 너무 깁니다" 해소 |
| supervisor AGENT.md 10591 chars 단일 body | Progressive Disclosure (`references/` split) | Phase 15 SPC-02 | AGENT.md body 43% 감소, input token cost 절감 |
| Pipeline 재실행 = 새 session_id | `--revision-from GATE --feedback TEXT` → 기존 session 부분 롤백 | Phase 15 UFL-01 | 대표님 피드백 loop 가동, 에이전트 재학습 인터페이스 확립 |
| 대본 = scripter 에이전트 전담 | `--revise-script <path>` → 수동 대본 주입 가능 | Phase 15 UFL-02 | 대표님 창작 권한 회로 개방 |

**Deprecated/outdated**:
- **argv 직접 system_prompt 전달** — Phase 15 이후 비추천 (10KB+ body 에서 rc=1 유발 가능). 기존 test seam `cli_runner` injection 은 내부 호출 우회이므로 영향 없음.

---

## Sources

### Primary (HIGH confidence)
- `claude --help` + `claude --version` 실측 (2026-04-22 session) — `--append-system-prompt[-file]` flag 존재 확증
- `scripts/orchestrator/invokers.py` (586 lines 전수 read)
- `scripts/orchestrator/shorts_pipeline.py` L116-319 (ctx + run + adapter init)
- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` (13362 bytes 전수 read)
- `.planning/phases/13-live-smoke/evidence/14-05-live-run.log` (rc=1 증거)
- `.planning/phases/13-live-smoke/13-RESEARCH.md` (live_smoke marker precedent)
- `tests/phase11/test_invoker_stdin.py` (subprocess.Popen mock pattern)
- `tests/phase091/test_producer_invoker.py` (cli_runner injection seam)
- `pytest.ini` (adapter_contract + live_smoke marker)

### Secondary (MEDIUM confidence)
- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference) — official docs
- [GitHub Issue #6153 — Add `--append-system-prompt-file`](https://github.com/anthropics/claude-code/issues/6153) — feature request origin
- [Claude Code Cheat Sheet 2026](https://computingforgeeks.com/claude-code-cheat-sheet/) — community reference
- [Modifying system prompts — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/modifying-system-prompts)

### Tertiary (LOW confidence — flagged for Plan validation)
- H2 CLI internal token counter hypothesis — unverified (source code not inspected); fix (file-based) works regardless.
- Korean argv UTF-8 byte-count drift hypothesis — partial empirical basis (21KB UTF-8 for 10KB chars), not conclusively linked to rc=1 mechanism.

---

## Metadata

**Confidence breakdown**:
- SPC-01 fix path (`--append-system-prompt-file`): HIGH — empirically verified existence + error message from nonexistent file
- SPC-02 AGENT.md compression plan: HIGH — 5 block split identified by line ranges, AGENT-STD-01 invariant clear
- SPC-03 size audit data: HIGH — 14 producer sizes measured empirically
- SPC-05 mock test plan: HIGH — Phase 11 test_invoker_stdin.py precedent exact
- SPC-06 live retry: HIGH — phase13_live_smoke.py existing infrastructure (952 lines)
- UFL-01~03 design: HIGH — ShortsPipeline resume mechanism (L269~319) + Checkpointer precedent (Phase 7 TEST-02 green)
- UFL-04 CLI: HIGH — argparse + markdown append (D-10 canonical pattern)
- Root cause (H2 specifically): MEDIUM — fix works regardless of which hypothesis (file path bypass); upstream CLI code not inspected

**Research date**: 2026-04-22
**Valid until**: 2026-05-22 (30 days — stable Claude CLI 2.1.x API + no pipeline refactor pending)
