# Phase 13: Live Smoke 재도전 - Research

**Researched:** 2026-04-21
**Domain:** Real-API end-to-end smoke validation (Claude CLI + YouTube Data API v3 + Kling/Nano Banana/Typecast)
**Confidence:** HIGH (brownfield — inspects existing shipped infrastructure, no new SDK research)

---

## Summary

Phase 13 is **not a greenfield implementation phase**. Every piece of infrastructure already exists and is unit-tested:

- **Real Claude CLI path** — `scripts/orchestrator/invokers.py` (585 lines, Phase 9.1 ship + Phase 11 stdin fix + Phase 12 AGENT-STD-03 compression at L404)
- **YouTube smoke upload** — `scripts/publisher/smoke_test.py` (280 lines, Phase 8 Plan 06 ship, 15/15 MockYouTube tests green, OAuth credentials in place)
- **Full 0→13 harness** — `scripts/smoke/phase11_full_run.py` (493 lines, Phase 11 Plan 06 ship, dry-run 검증 완료, live run 은 Phase 11 시점 GATE 2 block 으로 aborted pre-billing)
- **production_metadata** — `scripts/publisher/production_metadata.py` (4-field TypedDict + HTML comment inject + streaming sha256)
- **publish_lock bypass** — `SHORTS_PUBLISH_LOCK_PATH` env override (pytest `tmp_publish_lock` fixture precedent)

Phase 12 unblocked the GATE 2 supervisor rc=1 "프롬프트가 너무 깁니다" via `_compress_producer_output()` (14KB → 2.4KB, 27% ratio). Phase 14 cleared 15 adapter drift failures.

**What Phase 13 actually needs:**
1. Re-execute the existing `phase11_full_run.py --live` harness (rename/clone → `phase13_live_smoke.py`) now that GATE 2 is structurally unblocked
2. Wire 6 new evidence JSON files into `.planning/phases/13-live-smoke/evidence/` (producer_output, supervisor_output, smoke_upload, budget_usage, smoke_e2e, preflight)
3. Add a lightweight **budget counter** (Anthropic is $0 since Max subscription — this is for Kling/Nano Banana/Typecast/ElevenLabs)
4. Add pytest marker `@pytest.mark.live_smoke` so evidence-shape tests run without triggering real APIs
5. Add `SMOKE_MODE=true` env flag to bypass publish_lock for a single-shot smoke + cleanup

**Primary recommendation:** Do NOT build a new pipeline. Clone `phase11_full_run.py` → `phase13_live_smoke.py`, add evidence persistence + budget counter, execute once, then anchor artifacts. Total new code ~400 lines across 5 files.

---

## User Constraints (from CLAUDE.md + PROJECT.md + ROADMAP.md)

### Locked Decisions (binding)

- **REQ-12 Core Value path**: Phase 13 closes SC#1/SC#2 deferred from Phase 11 — real Claude CLI producer/supervisor + YouTube smoke upload with evidence anchor
- **Claude CLI Max 구독 경로 고정**: `ANTHROPIC_API_KEY` 등록 금지 (`project_claude_code_max_no_api_key.md`). Anthropic token cost = $0 marginal (월정액 Max 구독). 예산 계산에서 Claude 제외.
- **YouTube Data API v3 공식만** (CLAUDE.md 금기 #5, PUB-02, AF-8) — Selenium 영구 금지
- **I2V only** (CLAUDE.md 금기 #4, VIDEO-01, D-13) — T2V / text_to_video 금지. Nano Banana anchor → Kling/Runway I2V.
- **K-pop 트렌드 음원 금지** (CLAUDE.md 금기 #7, AF-13) — 하이브리드 crossfade + royalty-free만
- **일일 업로드 금지** (CLAUDE.md 금기 #8, AF-11) — Phase 13 smoke 는 1회 + `cleanup=True` 로 즉시 삭제 + publish_lock 우회 시 record_upload 도 skip (48h+ 카운터 소진 금지)
- **privacy=unlisted HARDCODED** (D-11) — `smoke_test.py` choices-locked, `ValueError` on `public`
- **Budget cap $5.00 USD HARD** (SMOKE-05) — 초과 시 `RuntimeError` + upload 차단
- **evidence chain anchoring** (SMOKE-01/02/04/06) — 각 SC 산출물을 `.planning/phases/13-live-smoke/evidence/` 에 영구 저장
- **나베랄 감마 존댓말 보고** — 대표님 대면 block 은 한국어 존댓말 (CLAUDE.md 필수사항 #7)

### Claude's Discretion (research this)

- Smoke script 파일명 / 구조 (phase11_full_run.py clone vs. from-scratch)
- Budget counter 데이터 구조 (단일 `budget_usage.json` vs. per-call append log)
- Evidence 파일 naming convention (timestamp format, 파일당 1 SC vs. 통합)
- pytest marker 이름 (`live_smoke` vs. `phase13_live` vs. `billable`)
- SMOKE_MODE 환경변수 vs. CLI `--smoke-mode` flag (publish_lock 우회 기전)
- Evidence shape verifier test 배치 (`tests/phase13/test_evidence_shapes.py` 단일 파일 vs. 6 파일 분할)

### Deferred Ideas (OUT OF SCOPE)

- NotebookLM RAG 실 호출 검증 (GATE 3 RESEARCH_NLM — NotebookLM Max 구독 inclusive, 예산 계산 제외)
- WhisperX 자막 정확도 검증 (SUBT-03 ±50ms) — Phase 10 이후 KPI loop
- Thumbnail CTR A/B test (DF-7) — v2
- Multi-niche smoke (현재 단일 채널 단일 니치만)
- Public upload (D-11 강제 unlisted, public 은 post-Phase-13 대표님 manual switch)
- 2nd video publish — publish_lock 48h+ 정상 경로 검증은 Phase 14+ 또는 운영 시작 후

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SMOKE-01 | Real Claude CLI producer 호출 1회 성공 + producer_output JSON anchor | `ClaudeAgentProducerInvoker` (invokers.py L301~, Phase 9.1) + Phase 11 stdin fix (L141) + retry-with-nudge 실증 GATE 1 (`7eb569b`) 확보 |
| SMOKE-02 | Real Claude CLI supervisor 17-inspector fan-out 1회 성공, AGENT-STD-03 압축 상태에서 rc=1 재현 0회 | `ClaudeAgentSupervisorInvoker.__call__` (invokers.py L396) + `_compress_producer_output()` (L495, 27% ratio) + Phase 12 test_phase11_smoke_replay_under_cli_limit GREEN |
| SMOKE-03 | YouTube 과금 smoke 업로드 1회 + cleanup=True + public 시도 ValueError | `scripts/publisher/smoke_test.py::run_smoke_test()` (280 lines, Phase 8) + OAuth `client_secret.json` + `youtube_token.json` in `config/` (shorts_naberal 승계) |
| SMOKE-04 | production_metadata HTML comment + YouTube videos.get readback 4 필드 | `scripts/publisher/production_metadata.py` (4-field TypedDict + HTML comment + sha256 stream) + regex `r'<!-- production_metadata\\n(\\{.*?\\})\\n-->' (DOTALL)` |
| SMOKE-05 | Budget cap $5 enforcement + budget_usage.json 기록 | Phase 9.1 `_check_cost_cap()` precedent (phase091_stage2_to_4.py $1.00 cap, $0.29 실제 소비) + Phase 11 `PER_GATE_COST_ESTIMATE_USD` heuristic (phase11_full_run.py L82~98) |
| SMOKE-06 | Full pipeline E2E (TREND→COMPLETE) 실 API 1회 완주 + 13 gate timestamps + final_video_id + total_cost_usd | `scripts/smoke/phase11_full_run.py` (493 lines) + `state/<session_id>/gate_NN.json` checkpointer + `_aggregate_gate_metrics()` |

---

## Current State Inventory

### Real Claude CLI Path (SMOKE-01/02 infrastructure)

**File:** `scripts/orchestrator/invokers.py` (585 lines — confirmed via `wc -l`)

| Component | Line | Shape | Phase Origin |
|-----------|------|-------|--------------|
| `CLAUDE_CLI_BIN = "claude"` | 61 | subprocess.run(["claude", "--print", ...]) via Max 구독 | Phase 9.1 (`8af5063`) |
| `_invoke_claude_cli` | 141~ | stdin PIPE + `communicate(input=user_prompt)` | Phase 11 (`c361ce4`) |
| `ClaudeAgentProducerInvoker.__call__` | 301~ | retry-with-nudge 3-attempt on JSONDecodeError | Phase 11 (`96001d3`) |
| `ClaudeAgentSupervisorInvoker.__call__` | 396~423 | `_compress_producer_output()` 압축 후 CLI body 주입 | Phase 12 (`_compress_...` at L495) |
| `_compress_producer_output` | 495~585 | 27% ratio, error_codes 전수 보존, severity_desc sort, budget 2000 chars | Phase 12 AGENT-STD-03 |
| Factory functions | 439~477 | `make_default_{producer,supervisor,asset_sourcer}_invoker` | Phase 9.1 |

**Confirmed blockers removed:**
- Phase 11 GATE 2 rc=1 "프롬프트가 너무 깁니다" → Phase 12 compression (14KB → 2.4KB) + 5 pytest GREEN including `test_phase11_smoke_replay_under_cli_limit`
- Phase 11 GATE 1 trend-collector JSON 미준수 → Phase 12 AGENT-STD-01 31/31 AGENT.md 5-block schema + `<output_format>` JSON 강제 + 5 금지 패턴

### YouTube Smoke Upload Path (SMOKE-03/04 infrastructure)

**File:** `scripts/publisher/smoke_test.py` (280 lines)

| Component | Shape | Confirmed |
|-----------|-------|-----------|
| `run_smoke_test(privacy='unlisted', cleanup=True)` | videos.insert → 30s polling → videos.delete | Phase 8 Plan 06 (15/15 MockYouTube tests) |
| `_build_smoke_plan()` | `production_metadata` 4 fields + `funnel.pinned_comment` + `privacyStatus="unlisted"` HARDCODED | `smoke_test.py:61~93` |
| `_wait_for_processing()` | 30s budget, 2s poll, timeout fall-through | `smoke_test.py:96~127` |
| `_delete_video()` | `SmokeTestCleanupFailure` on non-2xx | `smoke_test.py:130~139` |
| `publish(youtube, plan, ...)` chain | publish_lock → kst_window → production_metadata → videos.insert → thumbnails.set → commentThreads.insert → record_upload | `youtube_uploader.py:207~321` |

**Credentials (verified on disk 2026-04-21):**
```
config/client_secret.json       ✓ 400 bytes (OAuth Desktop client)
config/youtube_token.json       ✓ 844 bytes (refresh_token persisted)
config/youtube_token.json.bak_pre_analytics_scope ✓ 837 bytes (pre-analytics scope backup)
```

### production_metadata (SMOKE-04 infrastructure)

**File:** `scripts/publisher/production_metadata.py`

| Field | Source | Validation |
|-------|--------|------------|
| `script_seed` | orchestrator deterministic seed | plan.get('production_metadata', {}).get('script_seed', '') |
| `assets_origin` | `"kling:primary"` / `"runway:fallback"` / `"smoke:test"` | D-08 contract |
| `pipeline_version` | `PIPELINE_VERSION = "1.0.0"` constant | `youtube_uploader.py:263` overwrites plan value |
| `checksum` | `compute_checksum(mp4)` → `"sha256:<64hex>"` | 64KB streaming hash |

**Readback regex (SMOKE-04 verifier):**
```python
r'<!-- production_metadata\n(\{.*?\})\n-->'  # DOTALL flag
```

### Full 0→13 Harness (SMOKE-06 infrastructure)

**File:** `scripts/smoke/phase11_full_run.py` (493 lines)

| Section | Line | Shape |
|---------|------|-------|
| Env readiness check | 155~194 | required (TYPECAST/GOOGLE/YOUTUBE) + any_of (KLING\|FAL) + optional (ELEVENLABS/RUNWAY/SHOTSTACK) |
| `PER_GATE_COST_ESTIMATE_USD` | 82~98 | 13 gate × heuristic USD (total 예상 $3.44) |
| `_build_pipeline()` | 218~240 | explicit make_default_{producer,supervisor}_invoker wiring (auditable no-mock proof) |
| `_aggregate_gate_metrics()` | 243~303 | state/<sid>/gate_*.json walk → cost/retries/budget_breached |
| `_extract_upload_url()` | 306~327 | gate_12.json artifacts probe (video_url / youtube_url / url) |
| `_write_run_report()` | 330~364 | reports/phase11_smoke_<sid>.json persist |
| `_run_smoke()` | 367~458 | blocking pipeline.run() + exit 0/2/3/4/5 |
| CLI flags | 110~152 | --live / --dry-run mutex + --max-budget-usd default 5.00 + --session-id + --state-root |

**Prior execution results (Phase 11 verification):**
- Attempt 1 (`phase11_20260421_031945.json`): GATE 1 trend-collector JSONDecodeError → aborted 149.74s, $0.00 pre-billing
- Attempt 2 (`phase11_smoke_20260421_034724.json`): GATE 2 supervisor rc=1 → aborted 69.73s, $0.00 pre-billing
- **Both blockers structurally closed by Phase 12** (AGENT-STD-01 JSON schema + AGENT-STD-03 compression)

### Budget Counter (SMOKE-05 — NEW, does not exist yet)

**Precedent:** `phase091_stage2_to_4.py::_check_cost_cap(total_usd)` — Phase 9.1 Plan 06 shipped pattern

```python
def _check_cost_cap(total_usd: float, cap: float = 1.00) -> None:
    if total_usd > cap:
        raise RuntimeError(
            f"비용 상한 초과 ${total_usd:.2f} > ${cap:.2f} (대표님 중단)"
        )
```

**Extension needed for Phase 13:**
- File-based persistence (`.planning/phases/13-live-smoke/evidence/budget_usage.json`) for cross-gate accumulation
- Per-provider line items: `{"nanobanana": 0.08, "kling": 2.00, "typecast": 0.12, "total": 2.20, "cap": 5.00, "breached": false}`
- YouTube Data API v3 quota = free within 10,000 units/day (videos.insert=1600 + get=1 + delete=50 = 1651/10000 headroom)
- **Claude CLI = $0** (Max 구독, `project_claude_code_max_no_api_key.md` 고정)

### publish_lock Bypass (SMOKE-03 — NEW wiring needed)

**Existing override mechanism:** `SHORTS_PUBLISH_LOCK_PATH` env (publish_lock.py:58) — redirects lock file location

**Phase 13 approach (recommended):**
```python
# In phase13_live_smoke.py BEFORE pipeline.run():
import tempfile, os
# Use a temp lock file so the smoke doesn't consume 48h+ counter against real ops
os.environ["SHORTS_PUBLISH_LOCK_PATH"] = str(Path(tempfile.gettempdir()) / "phase13_smoke_lock.json")
```

**Why NOT a new `SMOKE_MODE=true` flag:** adding a new env branch in `publish_lock.py` requires new unit tests + Hook updates. The existing `SHORTS_PUBLISH_LOCK_PATH` is the Phase 8 documented override (D-06 intent) and pytest `tmp_publish_lock` fixture already uses it. Zero new code, same semantics.

---

## Technical Approach (per SC)

### SMOKE-01: Real Claude CLI producer 호출 + evidence anchor

**Delta from existing:**
- `phase11_full_run.py` does not persist per-GATE producer_output to evidence — checkpointer writes `state/<sid>/gate_NN.json` but the payload shape is `{_schema, session_id, gate, gate_index, timestamp, verdict, artifacts}` (not the raw producer_output).
- Add: after each gate's producer invocation (inside pipeline or post-run walk), extract the producer_output from checkpointer artifacts (or sidecar JSON) and write to `evidence/producer_output_YYYYMMDD.json`.

**Pattern:**
```python
# Post-run, walk state/<sid>/gate_*.json, collect producer_output from artifacts
evidence = {
    "session_id": sid,
    "timestamp": datetime.now().isoformat(),
    "producer_gates": {
        "TREND":    state["gate_01"]["artifacts"].get("producer_output"),
        "SCRIPT":   state["gate_05"]["artifacts"].get("producer_output"),
        # ... etc
    }
}
Path(f"evidence/producer_output_{session_id}.json").write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
)
```

**Verifier test (pytest, no real API):**
```python
@pytest.mark.live_smoke  # gated by env — does NOT run in CI
def test_producer_output_evidence_exists_and_shape():
    files = sorted(Path(".planning/phases/13-live-smoke/evidence/").glob("producer_output_*.json"))
    assert files, "SMOKE-01: producer_output evidence missing"
    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    assert "session_id" in payload
    assert "producer_gates" in payload
    assert payload["producer_gates"].get("TREND") is not None
```

### SMOKE-02: Real Claude CLI supervisor + rc=1 재현 0회

**Delta:** Phase 12 already proves compression via `test_phase11_smoke_replay_under_cli_limit`. Phase 13 needs evidence that **live run** no longer hits rc=1.

**Pattern:**
- Wrap `_invoke_claude_cli` returncode in evidence log: `{gate, attempt, returncode, stdout_len, stderr_tail}`
- Aggregate at run end: `supervisor_rc1_count == 0` assertion
- Capture pre-compression size + post-compression size per supervisor call into `evidence/supervisor_output_<sid>.json`

```python
# evidence/supervisor_output_YYYYMMDD.json
{
  "session_id": "20260421_XXXXXX",
  "supervisor_calls": [
    {"gate": "TREND", "inspector_count": 3, "pre_compress_bytes": 9824, "post_compress_bytes": 2373, "ratio": 0.24, "returncode": 0, "verdict": "PASS"},
    ...
  ],
  "rc1_count": 0,
  "compression_ratio_avg": 0.27
}
```

### SMOKE-03: YouTube 과금 smoke 업로드 + cleanup

**Reuse unchanged:** `run_smoke_test(privacy='unlisted', cleanup=True)` from `scripts/publisher/smoke_test.py`.

**Integration point:** at GATE 12 UPLOAD, the pipeline's `youtube_uploader.publish()` invocation needs to use the real MP4 artifact produced by GATE 9 ASSEMBLY (not the 1-byte fixture `tests/phase08/fixtures/sample_shorts.mp4` that smoke_test.py uses standalone).

**Pattern options:**
- **Option A (recommended):** let Phase 11 harness handle full 0→13 organically — GATE 12 calls `youtube_uploader.publish()` with the actual pipeline-produced MP4. Then post-run, issue a standalone `videos.delete(id=<video_id>)` cleanup via direct google-api call.
- **Option B:** hybrid — run GATE 0→11 for real asset production, then call `run_smoke_test()` with the pipeline-produced MP4 instead of the 1-byte fixture. Requires refactoring smoke_test.py to accept external video_path.

**Recommendation:** Option A preserves smoke_test.py as the isolated standalone pattern (Phase 8 contract). Phase 13 adds its own post-GATE-12 cleanup hook.

**ValueError check:** attempt `privacy='public'` in a dedicated test case (NOT a real API call — just `run_smoke_test(privacy='public')` which raises before any network call).

### SMOKE-04: production_metadata readback

**Delta:** existing code injects metadata on insert. Phase 13 needs a **post-upload videos.get()** to confirm the HTML comment survived round-trip.

**Pattern:**
```python
# After videos.insert succeeds, before videos.delete:
resp = youtube.videos().list(part="snippet", id=video_id).execute()
description_readback = resp["items"][0]["snippet"]["description"]
match = re.search(r'<!-- production_metadata\n(\{.*?\})\n-->', description_readback, re.DOTALL)
assert match, "production_metadata HTML comment survived YouTube round-trip"
metadata = json.loads(match.group(1))
for field in ("script_seed", "assets_origin", "pipeline_version", "checksum"):
    assert field in metadata and metadata[field], f"SMOKE-04: {field} missing from readback"

# Persist to evidence
Path(f"evidence/smoke_upload_{sid}.json").write_text(json.dumps({
    "session_id": sid, "video_id": video_id,
    "description_raw": description_readback,
    "production_metadata": metadata,
    "readback_verified": True,
}, ensure_ascii=False, indent=2), encoding="utf-8")
```

### SMOKE-05: Budget cap $5 enforcement

**New module (or inline in phase13_live_smoke.py):**

```python
# scripts/smoke/_budget_counter.py (or inline)
class BudgetCounter:
    def __init__(self, cap_usd: float = 5.00, evidence_path: Path = Path("evidence/budget_usage.json")):
        self.cap = cap_usd
        self.entries: list[dict] = []
        self.evidence_path = evidence_path

    def charge(self, provider: str, amount_usd: float, metadata: dict | None = None) -> None:
        total = sum(e["amount_usd"] for e in self.entries) + amount_usd
        if total > self.cap:
            raise RuntimeError(
                f"예산 상한 초과 ${total:.2f} > ${self.cap:.2f} 대표님 중단. "
                f"직전 호출: {provider} ${amount_usd:.2f}"
            )
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider, "amount_usd": amount_usd,
            "cumulative_usd": total, "metadata": metadata or {},
        })

    def persist(self) -> None:
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_path.write_text(json.dumps({
            "cap_usd": self.cap,
            "total_usd": round(sum(e["amount_usd"] for e in self.entries), 4),
            "entries": self.entries,
            "breached": any(e["cumulative_usd"] > self.cap for e in self.entries),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
```

**Provider unit prices (for cost accounting — Phase 9.1 precedent + published rates):**

| Provider | Unit | Price USD | Source |
|----------|------|-----------|--------|
| Claude CLI (producer/supervisor) | per call | $0.00 | Max 구독 inclusive (MEMORY.project_claude_code_max_no_api_key) |
| Nano Banana Pro (image gen) | per image | $0.04 | Phase 9.1 Plan 06 live smoke manifest |
| Kling I2V 2.6 Pro | per 5s clip | ~$0.35 | project_video_stack_kling26.md (FAL rate, ~$0.07/sec) |
| Runway Gen-3a Turbo I2V | per 5s clip | $0.25 | Phase 9.1 Plan 06 live smoke ($0.25 actual) |
| Typecast Korean TTS | per 1K chars | ~$0.12 | project_tts_stack_typecast.md (standard plan rate) |
| ElevenLabs (fallback) | per 1K chars | ~$0.30 | published Creator tier |
| NotebookLM | per query | $0.00 | Max 구독 inclusive (Google One) |
| YouTube Data API v3 | per unit | $0.00 | Free within 10K/day quota (smoke = ~1651 units) |

**Expected total per smoke run:** $1.50 ~ $3.00 (8 cuts × Kling $0.35 = $2.80 dominant + TTS $0.12 + thumbnail $0.04)

### SMOKE-06: Full E2E (TREND→COMPLETE) 13 gate timestamps + video_id + total_cost

**Reuse unchanged:** `phase11_full_run.py::_aggregate_gate_metrics()` already walks 13 gate checkpoints. Extend to include `final_video_id` extraction + `budget_usage.json` integration.

**Evidence file:**
```python
# evidence/smoke_e2e_YYYYMMDD.json
{
  "session_id": "20260421_XXXXXX",
  "status": "OK",
  "wall_time_seconds": 487.3,
  "gate_timestamps": {
    "IDLE": "2026-04-21T22:30:00+09:00",
    "TREND": "2026-04-21T22:30:15+09:00",
    ...
    "COMPLETE": "2026-04-21T22:38:07+09:00"
  },
  "gate_count": 13,
  "final_video_id": "dQw4w9WgXcQ",
  "total_cost_usd": 2.93,
  "budget_cap_usd": 5.00,
  "budget_breached": false,
  "supervisor_rc1_count": 0
}
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anthropic HTTP client | `httpx.post("https://api.anthropic.com/...")` | `subprocess.run(["claude", "--print", ...])` | Max 구독 중복 결제 + `project_claude_code_max_no_api_key.md` 영구 금지 |
| YouTube upload wrapper | direct `requests.post(youtube.com/...)` | `googleapiclient.discovery.build("youtube", "v3")` | OAuth flow + quota accounting + published error codes only in googleapiclient |
| OAuth token refresh | manual refresh_token POST | `scripts.publisher.oauth.get_credentials()` (Phase 8 ship) | google-auth handles expiry + retry + scope validation |
| production_metadata HTML comment parser | hand-rolled regex | `scripts/publisher/production_metadata.py` + contract test | sha256 streaming + DOTALL regex + ensure_ascii invariants already tested |
| SHA256 video checksum | `hashlib.sha256(path.read_bytes())` | `compute_checksum(Path)` (production_metadata.py:73) | 64KB streaming — 30MB+ MP4 won't double peak RSS |
| 48h+ publish lock bypass | delete lock file | `SHORTS_PUBLISH_LOCK_PATH` env override to temp path | Phase 8 D-06 documented override + pytest `tmp_publish_lock` precedent |
| Full 0→13 harness | from-scratch state machine | Clone `scripts/smoke/phase11_full_run.py` | 493 lines already battle-tested dry-run + 2 live attempts (pre-billing aborts) |
| Budget accumulator | per-gate accumulator dict in pipeline | Standalone `BudgetCounter` class with file persistence | Phase 9.1 `_check_cost_cap()` precedent (shipped pattern) |

**Key insight:** Every single piece exists. Phase 13 is a **wiring + evidence anchoring phase**, not a construction phase.

---

## Common Pitfalls

### Pitfall 1: Credential staleness

**What goes wrong:** `config/youtube_token.json` refresh_token expired → `InstalledAppFlow.run_local_server()` bootstrap triggers → blocks on browser OAuth → smoke hangs.
**Why it happens:** YouTube refresh_token has no expiry in theory, but Google may invalidate if unused for 6 months, password changed, or scope revoked.
**How to avoid:** Wave 0 Preflight step — run `scripts/publisher/oauth.py::get_credentials()` standalone first, confirm token refresh succeeds, confirm `config/youtube_token.json.bak_pre_analytics_scope` is the backup.
**Warning signs:** `RefreshError` in oauth.py stderr, `invalid_grant` in network trace.

### Pitfall 2: Claude CLI 인증 상태

**What goes wrong:** `shutil.which("claude")` returns None (PATH 문제) OR `claude` CLI logged-out → rc=1 "authentication required".
**Why it happens:** Windows PATH variable misconfig, OR Max subscription expired/reset.
**How to avoid:** Wave 0 Preflight — run `claude --print --append-system-prompt 'echo test' 'ping'` as smoke pre-flight. If rc≠0 or empty stdout, abort before billable API spend.
**Warning signs:** `_MISSING_CLI_MSG` raised, OR stdout contains "Please log in".

### Pitfall 3: Kling quota / model availability

**What goes wrong:** Kling 2.6 Pro model 계정 access revoked OR daily quota exhausted mid-run → 8 cuts × $0.35 budget already spent on first 4 cuts, next 4 fail with 429/403.
**Why it happens:** FAL.AI account billing issue OR Kling rate limit (~10 clips/min).
**How to avoid:** Wave 0 Preflight — `kling.image_to_video(small_test_image, "test motion")` once with $0.35 guard before running full pipeline. Phase 9.1 precedent: Runway substituted as fallback adapter (ADAPT-04 proven 742 passed).
**Warning signs:** `fal.client.exceptions.RateLimitError`, HTTP 429/403 from FAL endpoint.

### Pitfall 4: YouTube upload quota cliff

**What goes wrong:** `videos.insert` costs 1600 quota units out of 10,000/day budget → 5 smoke attempts = 8,000 units → 6th attempt fails with `quotaExceeded`.
**Why it happens:** Shared Google Cloud project may already consume quota from analytics polling or other services.
**How to avoid:** Single smoke run per day maximum (aligns with CLAUDE.md 금기 #8). `videos.list(part="status")` polls are free (1 unit each). `videos.delete` = 50 units.
**Warning signs:** `HttpError 403 quotaExceeded` from googleapiclient.

### Pitfall 5: Processing status timeout vs. cleanup ordering

**What goes wrong:** Video uploads successfully but `_wait_for_processing(30s)` times out → `_delete_video()` runs on not-yet-processed video → YouTube returns 409 Conflict → `SmokeTestCleanupFailure` → video remains on channel as unlisted.
**Why it happens:** Large MP4 (20MB+ 9:16 1080p) may take 60s+ to process on busy YT infrastructure.
**How to avoid:** `smoke_test.py` already handles this — timeout falls through to delete anyway. Delete on not-yet-processed usually succeeds (video is in "uploaded" state). If it fails, the `SmokeTestCleanupFailure` exception carries `video_id` for manual cleanup. Do NOT extend timeout beyond 30s — reasoning intact.
**Warning signs:** stdout `SMOKE_STATUS: cleanup-complete` missing OR `SmokeTestCleanupFailure` raised with video_id.

### Pitfall 6: Python CWD + relative path breakage

**What goes wrong:** `scripts/publisher/smoke_test.py` uses `Path("tests/phase08/fixtures/sample_shorts.mp4")` relative path → if pipeline is invoked from a non-repo-root CWD, path resolution fails with `FileNotFoundError`.
**Why it happens:** Windows double-click wrapper (`run_pipeline.cmd`) may not set CWD consistently.
**How to avoid:** `phase13_live_smoke.py` should `os.chdir(Path(__file__).resolve().parents[2])` at entry, OR resolve all paths via `_REPO_ROOT = Path(__file__).resolve().parents[2]` prefix.
**Warning signs:** `FileNotFoundError` on sample_shorts.mp4 or `.env`.

### Pitfall 7: Compression over-drops context for complex inspectors

**What goes wrong:** `_compress_producer_output()` drops `raw_response` + most of `semantic_feedback` (keeps 200 char prefix). Inspector needs more context (e.g., `ins-factcheck` maxTurns=10 expects citations list). Supervisor returns PASS incorrectly.
**Why it happens:** Phase 12 compression optimized for char budget 2000 — losses are quantified in 14KB → 2.4KB (27%) reduction but information loss for deep inspectors (factcheck, narrative-quality) is untested in live run.
**How to avoid:** Phase 13 evidence anchor `supervisor_output_<sid>.json` logs pre_compress_bytes + post_compress_bytes + `decisions_kept` / `decisions_dropped` counts per gate. 대표님 review verdict quality post-run — if supervisor PASS rate anomalously high (>95%), flag as Pitfall 7 candidate + open GAP for Phase 14+ tuning.
**Warning signs:** `decisions_dropped > 50%` + all verdicts PASS on first attempt.

### Pitfall 8: Windows cp949 stdout encoding

**What goes wrong:** Korean characters in logger output or evidence JSON write → `UnicodeEncodeError` on default Windows console → smoke run exits non-zero with cryptic encoding error.
**Why it happens:** Phase 6 STATE #28 + Phase 11 Plan 04 pattern — Windows default console is cp949, UTF-8 needs explicit reconfigure.
**How to avoid:** Already handled in `phase11_full_run.py:51~61` (`sys.stdout.reconfigure(encoding="utf-8")` + stderr fallback). Inherit in `phase13_live_smoke.py`. All JSON writes: `open(..., encoding="utf-8")` + `json.dumps(..., ensure_ascii=False)`.
**Warning signs:** `UnicodeEncodeError: 'cp949' codec can't encode`.

### Pitfall 9: Content policy violation auto-strike

**What goes wrong:** Claude-generated script → Kling-generated video passes our Inspector chain but YouTube ML classifier flags after upload → channel strike/suspension.
**Why it happens:** Inspector coverage gap for emergent content (deepfake detection, voice-likeness ML, cultural insensitivity patterns not in our blocklist).
**How to avoid:** privacy=unlisted HARDCODED (D-11) keeps video invisible to YouTube ML firehose. cleanup=True deletes within 30-60s post-upload so the strike window is minimal. This is the entire point of smoke design — **no public exposure, ever**.
**Warning signs:** N/A for unlisted (YouTube ML only flags public/scheduled content aggressively).

---

## Code Examples

### Example 1: Phase 13 live smoke entry (clone + wire evidence)

```python
# scripts/smoke/phase13_live_smoke.py
"""Phase 13 Live Smoke — real Claude CLI + real YouTube Data API v3."""
from __future__ import annotations
import json, logging, os, sys, tempfile, time, re
from datetime import datetime
from pathlib import Path

# Windows cp949 guard (Phase 11 pattern)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError) as err:
        sys.stderr.write(f"[phase13] stdout reconfigure skipped: {err}\n")

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Evidence dir
EVIDENCE = _REPO_ROOT / ".planning" / "phases" / "13-live-smoke" / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)

# publish_lock bypass — smoke must NOT consume 48h+ counter
os.environ.setdefault(
    "SHORTS_PUBLISH_LOCK_PATH",
    str(Path(tempfile.gettempdir()) / "phase13_smoke_lock.json"),
)

from scripts.orchestrator import ShortsPipeline  # noqa: E402
from scripts.orchestrator.invokers import (  # noqa: E402
    make_default_producer_invoker,
    make_default_supervisor_invoker,
)
from scripts.smoke.phase11_full_run import (  # noqa: E402 — reuse harness helpers
    _check_env_readiness,
    _print_env_report,
    _build_pipeline,
    _aggregate_gate_metrics,
    _extract_upload_url,
)

logger = logging.getLogger("smoke.phase13")
```

### Example 2: Budget counter with per-provider accounting

```python
# scripts/smoke/budget_counter.py (new, ~80 lines)
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json

class BudgetExceededError(RuntimeError):
    """예산 상한 초과 — 대표님 중단."""

class BudgetCounter:
    def __init__(self, cap_usd: float, evidence_path: Path):
        self.cap_usd = cap_usd
        self.entries: list[dict] = []
        self.evidence_path = evidence_path

    @property
    def total_usd(self) -> float:
        return sum(e["amount_usd"] for e in self.entries)

    def charge(self, provider: str, amount_usd: float, metadata: dict | None = None) -> None:
        projected = self.total_usd + amount_usd
        if projected > self.cap_usd:
            raise BudgetExceededError(
                f"예산 상한 초과 ${projected:.2f} > ${self.cap_usd:.2f} 대표님 중단 "
                f"(직전: {provider} ${amount_usd:.2f})"
            )
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "amount_usd": round(amount_usd, 4),
            "cumulative_usd": round(projected, 4),
            "metadata": metadata or {},
        })

    def persist(self) -> Path:
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cap_usd": self.cap_usd,
            "total_usd": round(self.total_usd, 4),
            "breached": self.total_usd > self.cap_usd,
            "entry_count": len(self.entries),
            "entries": self.entries,
        }
        self.evidence_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.evidence_path
```

### Example 3: production_metadata readback verifier

```python
# Inside phase13_live_smoke.py post-upload
def _verify_and_anchor_upload(youtube, video_id: str, sid: str) -> dict:
    import re
    resp = youtube.videos().list(part="snippet,status", id=video_id).execute()
    items = resp.get("items", [])
    if not items:
        raise RuntimeError(f"videos.list returned empty for {video_id} 대표님")
    snippet = items[0]["snippet"]
    desc = snippet.get("description", "")
    match = re.search(r'<!-- production_metadata\n(\{.*?\})\n-->', desc, re.DOTALL)
    metadata = json.loads(match.group(1)) if match else {}
    required_fields = ("script_seed", "assets_origin", "pipeline_version", "checksum")
    missing = [f for f in required_fields if not metadata.get(f)]
    evidence = {
        "session_id": sid,
        "video_id": video_id,
        "description_raw": desc,
        "production_metadata": metadata,
        "required_fields_present": len(missing) == 0,
        "missing_fields": missing,
    }
    path = EVIDENCE / f"smoke_upload_{sid}.json"
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("[phase13] smoke_upload evidence → %s", path)
    if missing:
        raise RuntimeError(
            f"SMOKE-04 실패 대표님: production_metadata 누락 필드 {missing}"
        )
    return evidence
```

---

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `state/<session_id>/gate_NN.json` checkpoints accumulate per smoke run — NOT pruned | No action (gitignored); if disk concern, add `--cleanup-checkpoints` flag post-run |
| Live service config | YouTube OAuth refresh_token in `config/youtube_token.json` — may be auto-rotated by Google; `.env` 5 API keys (ELEVENLABS/TYPECAST/FAL/GOOGLE/YOUTUBE_CLIENT_SECRETS_FILE) | Wave 0 Preflight validates all before billable run |
| OS-registered state | None — Phase 13 is a one-shot manual invocation, not a scheduled task | None — verified by absence of new Windows Task Scheduler or pm2 entries in plan |
| Secrets/env vars | `ANTHROPIC_API_KEY` MUST remain unset (금기). `SHORTS_PUBLISH_LOCK_PATH` set to temp by phase13_live_smoke.py (reverts on process exit) | None required |
| Build artifacts | Pipeline outputs `output/<session_id>/clip.mp4` — gitignored. YouTube receives upload then `videos.delete` within 30s | None — `cleanup=True` enforces artifact removal from YouTube; local MP4 can optionally be retained for 대표님 재생 |

**Nothing found in category:** OS-registered state (no cron/Task/launchd touch). Stored database (no SQLite/Mongo write).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `claude` CLI (Max 구독) | SMOKE-01, SMOKE-02, SMOKE-06 | ✓ (Phase 11 live attempts confirmed) | Claude Code 2.1.112+ | — (no fallback — SDK path 금지) |
| `config/client_secret.json` | SMOKE-03, SMOKE-04 | ✓ 400 bytes | OAuth 2.0 Desktop client | — |
| `config/youtube_token.json` | SMOKE-03, SMOKE-04 | ✓ 844 bytes | refresh_token present | `InstalledAppFlow.run_local_server()` interactive bootstrap (Wave 0 blocker if triggered) |
| Python 3.11 | All | ✓ (Phase 9.1 pinned) | 3.11.x | — |
| `googleapiclient` | SMOKE-03/04 | ✓ (Phase 8 dep) | pinned | — |
| `.env` ELEVENLABS_API_KEY | SMOKE-06 (GATE 7 fallback) | ✓ present | — | Typecast primary OK without ElevenLabs |
| `.env` TYPECAST_API_KEY | SMOKE-06 (GATE 7 primary) | ✓ present | — | ElevenLabs fallback |
| `.env` FAL_KEY | SMOKE-06 (GATE 8 Kling primary) | ✓ present | — | Runway fallback via `RUNWAY_API_KEY` |
| `.env` GOOGLE_API_KEY | SMOKE-06 (GATE 8/10 Nano Banana) | ✓ present | — | None — hard-required |
| Network access | All real API calls | ✓ (assume) | — | None |
| FFmpeg | GATE 9 ASSEMBLY ken_burns fallback | ✓ (Phase 9.1 ship) | bundled/system | — |

**Missing dependencies with no fallback:** None at present. Wave 0 Preflight re-validates.

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (Phase 4 baseline, 244/244 GREEN) |
| Config file | `pytest.ini` (Phase 14 registered `adapter_contract` marker; Phase 13 adds `live_smoke`) |
| Quick run command | `py -3.11 -m pytest tests/phase13/ -q -m "not live_smoke"` |
| Full suite command | `py -3.11 -m pytest tests/phase04 tests/phase10 tests/phase11 tests/phase12 tests/phase13/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SMOKE-01 | producer_output evidence file exists + shape valid | unit (evidence-shape) | `pytest tests/phase13/test_evidence_shapes.py::test_smoke_01_producer_output -x` | ❌ Wave 0 |
| SMOKE-02 | supervisor_output evidence rc1_count==0 + compression ratio logged | unit (evidence-shape) | `pytest tests/phase13/test_evidence_shapes.py::test_smoke_02_supervisor_output -x` | ❌ Wave 0 |
| SMOKE-03 | smoke_test.py ValueError on public + run_smoke_test happy path (mocked) | unit (mocked) | `pytest tests/phase13/test_smoke_03_upload_contract.py -x` | ❌ Wave 0 |
| SMOKE-04 | production_metadata readback regex + 4 fields | unit | `pytest tests/phase13/test_smoke_04_readback.py -x` | ❌ Wave 0 |
| SMOKE-05 | BudgetCounter charge + BudgetExceededError + persist schema | unit | `pytest tests/phase13/test_budget_counter.py -x` | ❌ Wave 0 |
| SMOKE-06 | smoke_e2e evidence 13-gate timestamp + final_video_id + total_cost_usd fields | unit (evidence-shape) | `pytest tests/phase13/test_evidence_shapes.py::test_smoke_06_e2e -x` | ❌ Wave 0 |
| — live end-to-end | real API run produces all 6 evidence files | integration (live, gated) | `pytest tests/phase13/test_live_run.py -m live_smoke --run-live` | ❌ Wave 0 |

### Sampling Rate (Nyquist strategy)

**The core tension:** real API smoke = $2-3 + YouTube quota burn. Every pytest invocation MUST NOT trigger this. But we still need regression coverage that the evidence shape + tooling work.

**Solution — two-tier separation:**

1. **Evidence-shape tests (always run, no API):**
   - Mock Claude CLI, mock youtube client via `tests/phase08/mocks/youtube_mock.py`
   - Assert fixture-based `.json` files have required keys, schema, types
   - Assert `run_smoke_test(privacy='public')` raises ValueError without any API call
   - Assert `BudgetCounter.charge(overage)` raises `BudgetExceededError`

2. **Live smoke test (opt-in only, `@pytest.mark.live_smoke`):**
   - Marker registered in `pytest.ini` (alongside `adapter_contract` from Phase 14)
   - `pytest --strict-markers` excludes by default (Phase 14 enabled — `addopts` config)
   - Run only via explicit `pytest -m live_smoke --run-live` (custom `conftest.py` flag requiring `--run-live`)
   - OR run standalone: `py -3.11 scripts/smoke/phase13_live_smoke.py --live --max-budget-usd 5.00`
   - Post-run, the regular evidence-shape tests pick up the newly-written JSON files and verify

**Per task commit:** `py -3.11 -m pytest tests/phase13/ -m "not live_smoke" -q` (must pass)
**Per wave merge:** `py -3.11 -m pytest tests/phase04 tests/phase11 tests/phase12 tests/phase13 -q` (zero regression)
**Phase gate:** Full evidence chain present + `py -3.11 -m pytest tests/phase13 -q -m "not live_smoke"` green + 1 live smoke run in git history with all 6 evidence files anchored + 대표님 verification block filled

### Wave 0 Gaps

- [ ] `tests/phase13/conftest.py` — shared fixtures (mock Claude CLI runner, fake youtube client, tmp_evidence_dir)
- [ ] `tests/phase13/test_evidence_shapes.py` — 6 evidence file shape tests (SMOKE-01/02/04/06 fixtures + assert keys)
- [ ] `tests/phase13/test_smoke_03_upload_contract.py` — ValueError test + MockYouTube happy path (reuse Phase 8 mocks)
- [ ] `tests/phase13/test_smoke_04_readback.py` — regex DOTALL + 4-field assert
- [ ] `tests/phase13/test_budget_counter.py` — BudgetCounter unit tests (charge + overage raise + persist shape)
- [ ] `tests/phase13/test_live_run.py` — `@pytest.mark.live_smoke` gated end-to-end runner
- [ ] `pytest.ini` amend — register `live_smoke` marker (next to `adapter_contract` from Phase 14)
- [ ] `tests/phase13/conftest.py` `--run-live` CLI option for opt-in gate
- [ ] `tests/phase13/fixtures/` — sample evidence JSON fixtures for shape-only tests (frozen golden files)
- [ ] Framework install: none — pytest 8.x + pytest-mock already installed per Phase 4 baseline

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `anthropic.Anthropic().messages.create()` SDK | `subprocess.run(["claude", "--print", ...])` CLI | Phase 9.1 session #24 commit `8af5063` | Max 구독 중복 결제 회피 + `ANTHROPIC_API_KEY` 영구 금지 |
| Full producer_output JSON in supervisor CLI body | `_compress_producer_output()` 27% ratio summary-only | Phase 12 AGENT-STD-03 | Phase 11 GATE 2 rc=1 "프롬프트가 너무 깁니다" 구조적 closure |
| Selenium YouTube upload | Google API Client Library `googleapiclient.discovery` | Phase 8 PUB-02 (AF-8) | Channel ban 위험 제거 |
| Hand-rolled SHA256 | `compute_checksum()` 64KB stream | Phase 8 Plan 05 | 30MB+ MP4 peak RSS bounded |
| Single `ClaudeAgentProducerInvoker` 1-attempt | retry-with-nudge 3-attempt on JSONDecodeError | Phase 11 (`96001d3`) | GATE 1 JSON recovery 실증 + retry exhaustion → FAILURES append |
| Runway gen3a_turbo ratio "9:16" | ratio "768:1280" numeric | Phase 9.1 Plan 06 deferred-items.md | HTTP 400 "must be one of 768:1280, 1280:768" resolved |
| `run_pipeline.ps1` bare invocation | ExecutionPolicy Bypass + try/catch/finally Read-Host | Phase 11 Plan 04 | Windows 더블클릭 UX + 창 닫힘 방지 |

**Deprecated/outdated:**
- `anthropic` Python SDK usage in `scripts/orchestrator/` — 영구 금지 (session #24 architectural correction)
- `phase11_full_run.py` as the entry harness — Phase 13 clones and extends (original preserved as Phase 11 evidence)

---

## Build Order Recommendation

### Wave 0: Preflight Infrastructure (no billable calls)

- Create `tests/phase13/` scaffolding + conftest + mock fixtures
- Register `@pytest.mark.live_smoke` in `pytest.ini`
- Add `--run-live` CLI option in `tests/phase13/conftest.py`
- Scaffold `scripts/smoke/budget_counter.py` (new module) + unit tests
- Scaffold `scripts/smoke/phase13_live_smoke.py` as clone of phase11_full_run.py with evidence hooks
- `tests/phase13/fixtures/` sample JSON evidence files (frozen golden)
- Preflight CLI subcommand: `phase13_live_smoke.py --preflight` — checks Claude CLI reachable + YouTube token refresh + API keys + write access to evidence dir
- **Gate:** `pytest tests/phase13/ -m "not live_smoke"` green + preflight dry-run exits 0

### Wave 1: Real Claude CLI Smoke (SMOKE-01 + SMOKE-02)

- Run `phase13_live_smoke.py --live --gates 0-6` (scope-limited — TREND through POLISH, no ASSETS yet so no Kling/Nano Banana spend)
- Estimated cost: ~$0.00 (Claude CLI is free; NotebookLM Max inclusive; only text gates)
- Produce `evidence/producer_output_<sid>.json` + `evidence/supervisor_output_<sid>.json`
- Verify `supervisor_rc1_count == 0` + all producer_output JSON parseable
- **Gate:** 2 evidence files present with required keys + shape tests green

### Wave 2: YouTube Upload Smoke (SMOKE-03 + SMOKE-04)

- Reuse existing `scripts/publisher/smoke_test.py::run_smoke_test()` directly (not via full pipeline) — faster iteration, pre-existing MP4 fixture
- Add `_verify_and_anchor_upload()` post-upload + pre-delete
- Verify `privacy='public'` ValueError raise (no API call)
- Produce `evidence/smoke_upload_<sid>.json` with production_metadata readback
- Estimated cost: $0.00 (YouTube API = free within quota)
- **Gate:** 1 evidence file with `required_fields_present: true` + video deleted from channel (verified via `videos.list()` returning empty items)

### Wave 3: Budget Cap Enforcement (SMOKE-05)

- Integrate `BudgetCounter` into `phase13_live_smoke.py`
- Wire provider charges at each adapter invocation (nanobanana $0.04, kling $0.35, typecast $0.12, runway $0.25 fallback, elevenlabs $0.30 fallback)
- Add budget cap RuntimeError before any billable call if projected total would exceed
- Add `evidence/budget_usage.json` persist at run end (even on failure)
- **Gate:** `test_budget_counter.py` green + dry-run cost preview printable

### Wave 4: Full E2E (SMOKE-06 — integrates Wave 1+2+3)

- Execute `phase13_live_smoke.py --live --max-budget-usd 5.00` (full 0→13 GATEs)
- Expected cost range: $1.50 ~ $3.00 (8 Kling cuts dominant + TTS + thumbnail)
- Single smoke run — 대표님 approval required per kickoff (kickoff already granted 2026-04-21 "페이즈 13해봐라 내가 승인할게")
- All 6 evidence files written
- 대표님 재생 가능: `start output/<session_id>/clip.mp4` + YouTube Studio 확인 (unlisted + deleted)
- **Gate:** `evidence/smoke_e2e_<sid>.json` has `gate_count == 13` + `final_video_id` non-empty + `total_cost_usd <= 5.00` + `supervisor_rc1_count == 0`

### Wave 5: Phase Gate + Evidence Validation

- Run full regression: `pytest tests/phase04 tests/phase11 tests/phase12 tests/phase13 -q`
- Full evidence-shape tests green post-live-run
- Write 13-VERIFICATION.md with all SC verdicts + human_verification block
- REQUIREMENTS.md SMOKE-01/02/03/04/05/06 flip `[x]`
- ROADMAP.md Phase 13 status `✅ Complete` + Progress Table update
- **Gate:** `/gsd:verify-work 13` passes + 대표님 human_verification block filled

---

## Open Questions (for plan-phase)

1. **Evidence file granularity** — single `evidence/producer_output_<sid>.json` with all 13 gate outputs concatenated, OR per-gate files `evidence/producer_output_<sid>_<gate>.json` (13+ files per run)?
   - Recommendation: single aggregated file per category (producer_output/supervisor_output/budget_usage/smoke_upload/smoke_e2e). 5 evidence files per live run. Readable in one session.

2. **Live smoke 재실행 정책** — Phase 13 is scoped to "1회 성공". If Wave 4 live run fails mid-pipeline (e.g. Kling 429), do we retry same-day (quota permitting) or defer to next-day?
   - Recommendation: `--max-attempts 2` flag; second attempt on different session_id; budget counter persists across attempts (cumulative cap still $5.00 across both attempts). If both fail, Phase 13 enters `complete_with_deferred` status (Phase 11 precedent).

3. **Scope-limited pre-run** — should Wave 1 (Claude-only, no paid APIs) be a separate `--gates 0-6` CLI flag, or integrated via `--dry-gates-after <N>` option?
   - Recommendation: `--dry-gates-after POLISH` — gates 0-6 execute real Claude CLI, gates 7-13 short-circuit to mock adapters. Needs hook into ShortsPipeline.run() OR per-gate guard. Simpler alternative: Wave 1 uses phase11_full_run.py dry-run mode for gates 7-13 (dry-run path already wired, just add Claude real toggle).

4. **Budget vs. $5 cap inclusion** — does `$0 Claude CLI` count against the $5 cap numerically (for anyway-show-it-in-ledger), or exclude (cap is "paid services only")?
   - Recommendation: include as `{"provider": "claude_cli", "amount_usd": 0.00}` entry so the ledger is complete; cap logic still enforced on `total_usd` which remains unchanged. Documentation clarity > ledger completeness trade-off.

5. **SCRIPT_QUALITY_DECISION.md verdict** — Phase 11 deferred SCRIPT-01 (대표님 6-axis eval A/B/C verdict). Phase 13 produces the first real video. Does Phase 13 scope include the verdict lock, or is it Phase 14+ scope?
   - Recommendation: Phase 13 Wave 4 produces video → 대표님 fills SCRIPT_QUALITY_DECISION.md frontmatter → Phase 13 `human_verification` block references verdict locked. Verdict closure is Phase 13 SC implicitly via `human_verification` (not a new SMOKE-NN REQ).

6. **Live run logging volume** — each supervisor call compressed from 14KB to 2.4KB for CLI; should we log the full 14KB pre-compression to evidence for forensic audit, or summary only?
   - Recommendation: summary only (pre_compress_bytes counter + post-compression payload). Full raw would balloon evidence files 100x+ for marginal audit value. If audit needed, re-run with `--verbose-compression` flag writing `evidence/supervisor_raw_<sid>_<gate>.json` ad-hoc.

7. **Post-smoke cleanup of pipeline MP4** — `output/<session_id>/clip.mp4` survives after YouTube delete. Keep for 대표님 재생 or auto-delete?
   - Recommendation: keep (Phase 9.1 Plan 06 precedent — `output/phase091_smoke/clip.mp4` retained for 대표님 playback). Gitignored anyway. Size ~2-5MB per run.

---

## Sources

### Primary (HIGH confidence)

- `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-VERIFICATION.md` — Phase 11 deferred SC#1/SC#2 root cause analysis + evidence chain
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-VERIFICATION.md` — Phase 12 AGENT-STD-03 compression closure + 27% ratio evidence
- `.planning/phases/09.1-production-engine-wiring/09.1-06-SUMMARY.md` — Phase 9.1 live smoke $0.29 precedent + budget cap pattern + Runway ratio pitfall
- `scripts/orchestrator/invokers.py` (585 lines) — real Claude CLI path verified
- `scripts/publisher/smoke_test.py` (280 lines) — YouTube smoke test verified
- `scripts/publisher/production_metadata.py` — 4-field TypedDict + HTML comment + sha256 stream verified
- `scripts/publisher/publish_lock.py` — `SHORTS_PUBLISH_LOCK_PATH` override mechanism verified
- `scripts/smoke/phase11_full_run.py` (493 lines) — full 0→13 harness verified
- `.claude/memory/project_claude_code_max_no_api_key.md` — Anthropic SDK 영구 금지 근거
- `.planning/REQUIREMENTS.md` §405~454 — SMOKE-01~06 정식 정의
- `.planning/ROADMAP.md` §342~356 — Phase 13 Goal + Depends + SC 6개
- `CLAUDE.md` — 나베랄 감마 identity + 금기사항 9개 + 필수사항 8개
- `config/client_secret.json` + `config/youtube_token.json` — on-disk verified (400 + 844 bytes)

### Secondary (MEDIUM confidence)

- `.claude/memory/project_tts_stack_typecast.md` — Typecast pricing (~$0.12/1K chars, creator tier)
- `.claude/memory/project_video_stack_kling26.md` — Kling 2.6 Pro pricing (~$0.35/5s clip via FAL)
- Kling published rates, Runway Gen-3a Turbo published rates (cross-verified with Phase 9.1 $0.29 actual spend)

### Tertiary (LOW confidence — flagged for Wave 0 validation)

- YouTube Data API v3 quota (10K/day for standard projects) — assumed current; Wave 0 can re-verify via `quotaUser.get` if needed
- ElevenLabs Creator tier rates (~$0.30/1K chars) — published but fallback-only, not on critical path

---

## Metadata

**Confidence breakdown:**
- Current state inventory: HIGH — every referenced file's existence + line count + key function position verified on disk
- Standard stack: HIGH — all dependencies already shipped + tested in prior phases
- Architecture (new budget counter): MEDIUM — pattern is Phase 9.1 precedent but new module
- Validation Architecture: HIGH — `live_smoke` marker mirrors Phase 14 `adapter_contract` precedent
- Pitfalls: HIGH-MEDIUM — Pitfalls 1-6/8 are infrastructure-level documented precedents; Pitfall 7 (compression over-drop) is LOW — only evidence + 대표님 review can confirm
- Budget pricing: MEDIUM — Kling/Typecast rates from project memory files (could drift month-over-month; Wave 0 Preflight should re-confirm)

**Research date:** 2026-04-21
**Valid until:** 2026-05-21 (30 days, stable domain — API pricing may drift, validate at Wave 0)
