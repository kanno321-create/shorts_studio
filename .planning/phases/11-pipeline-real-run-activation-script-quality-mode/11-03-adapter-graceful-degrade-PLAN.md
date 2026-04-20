---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 03
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/orchestrator/shorts_pipeline.py
  - tests/phase11/test_adapter_graceful_degrade.py
  - tests/phase11/test_argparse_session_id.py
autonomous: true
requirements: [PIPELINE-03, PIPELINE-04]
must_haves:
  truths:
    - "Missing env for ANY single adapter does NOT block ShortsPipeline.__init__ — logged as warning + self.X = injected_arg"
    - "Kling / Runway / Typecast / ElevenLabs / Shotstack / NanoBanana / KenBurns all follow the SAME graceful-degrade pattern (D-05 '동일 패턴' via helper)"
    - "Adapter internals (scripts/orchestrator/api/*.py) UNTOUCHED — eager ValueError preserved (D-06 regression protection)"
    - "shorts_pipeline.py line count net -2 (796 → ~794) — stays under 800-line soft cap (§Line Budget)"
    - "`--session-id` argparse optional (default=None → auto-timestamp via datetime.now().strftime('%Y%m%d_%H%M%S'))"
    - "Explicit `--session-id` still works (override path preserved for scheduler integration)"
    - "Existing test injecting `MagicMock(...)` adapters via kwargs continue to work (X or _try_adapter short-circuit)"
  artifacts:
    - path: "scripts/orchestrator/shorts_pipeline.py"
      provides: "_try_adapter helper + 7 unified adapter instantiations + relaxed argparse"
      contains: "def _try_adapter, args.session_id or datetime"
    - path: "tests/phase11/test_adapter_graceful_degrade.py"
      provides: "5 tests: missing env for each adapter doesn't block pipeline + helper uniform semantics"
      min_lines: 180
    - path: "tests/phase11/test_argparse_session_id.py"
      provides: "3 tests: required=False, auto-default generates timestamp, explicit override works"
      min_lines: 70
  key_links:
    - from: "ShortsPipeline.__init__"
      to: "_try_adapter helper"
      via: "7 unified call sites for kling / runway / typecast / elevenlabs / shotstack / nanobanana / ken_burns"
      pattern: "_try_adapter\\("
    - from: "shorts_pipeline.main argparse"
      to: "datetime.now().strftime"
      via: "args.session_id or datetime.now().strftime('%Y%m%d_%H%M%S')"
      pattern: "args\\.session_id or datetime"
---

<objective>
PIPELINE-03 + PIPELINE-04 argparse tie-in:
- (PIPELINE-03) Wrap 4 remaining eager adapter instantiations (Kling / Runway / Typecast / ElevenLabs) with the Phase 9.1 graceful-degrade pattern already applied to Shotstack/NanoBanana/KenBurns. D-05 mandates "동일 패턴"; RESEARCH §Line Budget + §Pattern 3 shows a `_try_adapter` helper is required to stay under the 800-line soft cap while honoring D-05.
- (PIPELINE-04 tie-in / D-16) Relax `--session-id` from `required=True` to optional with auto-timestamp default. Required so double-click `.cmd/.ps1` wrapper (Plan 11-04) can invoke without wrapping session-id injection logic.

Purpose: Resolves D10-PIPELINE-DEF-01 errors #3 (KlingI2VAdapter eager ValueError) + #4 (ShortsPipeline can't instantiate because first adapter blocks). Also unblocks wrapper UX (session-id auto-default).

Output:
- `scripts/orchestrator/shorts_pipeline.py` with `_try_adapter()` helper + 7 unified adapter calls (replacing 4 bare + 3 try/except blocks) + relaxed argparse
- `tests/phase11/test_adapter_graceful_degrade.py` with 5 tests
- `tests/phase11/test_argparse_session_id.py` with 3 tests
- Line delta: -2 (from 796 to ~794) per RESEARCH §Line Budget
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md
@scripts/orchestrator/shorts_pipeline.py

<interfaces>
<!-- Current shorts_pipeline.py adapter instantiation block (L209-235) -->

From scripts/orchestrator/shorts_pipeline.py L209-235:
```python
# Adapters (injected for tests, constructed from env otherwise).
self.kling = kling_adapter or KlingI2VAdapter(circuit_breaker=self.kling_breaker)
self.runway = runway_adapter or RunwayI2VAdapter(circuit_breaker=self.runway_breaker)
self.typecast = typecast_adapter or TypecastAdapter(circuit_breaker=self.typecast_breaker)
self.elevenlabs = elevenlabs_adapter or ElevenLabsAdapter(circuit_breaker=self.elevenlabs_breaker)
try:
    self.shotstack = shotstack_adapter or ShotstackAdapter(circuit_breaker=self.shotstack_breaker)
except ValueError as err:
    logger.warning("[pipeline] shotstack adapter 미초기화 (대표님 — SHOTSTACK_API_KEY 없음, Phase 9.1 ken_burns 로컬 대체로 실 호출 경로 부재): %s", err)
    self.shotstack = shotstack_adapter
try:
    self.nanobanana = nanobanana_adapter or NanoBananaAdapter(
        circuit_breaker=self.nanobanana_breaker
    )
except ValueError as err:
    logger.warning("[pipeline] nanobanana adapter 미초기화 (대표님): %s", err)
    self.nanobanana = nanobanana_adapter
try:
    self.ken_burns = ken_burns_adapter or KenBurnsLocalAdapter(
        circuit_breaker=self.ken_burns_breaker
    )
except KenBurnsUnavailable as err:
    logger.warning("[pipeline] ken_burns 미초기화 (대표님 ffmpeg 확인): %s", err)
    self.ken_burns = ken_burns_adapter
```

From scripts/orchestrator/shorts_pipeline.py L746-760 (argparse):
```python
parser.add_argument("--session-id", required=True, help="Session identifier")
# ... other args ...
args = parser.parse_args(argv)
# ...
pipeline = ShortsPipeline(
    session_id=args.session_id,   # <-- passes verbatim
    state_root=Path(args.state_root),
)
```

Adapter __init__ exceptions (verified per RESEARCH §Pattern 3):
- KlingI2VAdapter: ValueError when KLING_API_KEY + FAL_KEY both missing
- RunwayI2VAdapter: ValueError (key), ValueError (model), ValueError (ratio)
- TypecastAdapter: ValueError (TYPECAST_API_KEY)
- ElevenLabsAdapter: ValueError (ELEVENLABS_API_KEY)
- ShotstackAdapter: ValueError (SHOTSTACK_API_KEY — D-07 defect)
- NanoBananaAdapter: ValueError (GOOGLE_API_KEY)
- KenBurnsLocalAdapter: KenBurnsUnavailable (ffmpeg check)

datetime already imported (L~40 region uses `from datetime import datetime`).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wave 0 tests — 5 graceful-degrade + 3 argparse session-id</name>
  <files>tests/phase11/test_adapter_graceful_degrade.py, tests/phase11/test_argparse_session_id.py</files>
  <read_first>
    - scripts/orchestrator/shorts_pipeline.py (L1-270 — ShortsPipeline constructor; L740-770 — argparse/main)
    - scripts/orchestrator/api/kling_i2v.py (L81-95 area — ValueError raise on missing key)
    - scripts/orchestrator/api/runway_i2v.py (L77-117 — three ValueError sites)
    - scripts/orchestrator/api/typecast.py (L51-65 — ValueError)
    - scripts/orchestrator/api/elevenlabs.py (L109-140 — ValueError)
    - tests/phase11/conftest.py (reuses fixtures from Plan 11-01)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 3 + §Line Budget
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-05, D-06, D-07, D-16
  </read_first>
  <behavior>
    **test_adapter_graceful_degrade.py (5 tests):**
    - Test 1 `test_pipeline_constructs_when_kling_env_missing`: monkeypatch clears KLING_API_KEY + FAL_KEY → ShortsPipeline() instantiates; `self.kling is None`; `logger.warning` captured with "kling adapter 미초기화" + "대표님"
    - Test 2 `test_pipeline_constructs_when_runway_env_missing`: clears RUNWAY_API_KEY → pipeline builds; `self.runway is None`; warning logged
    - Test 3 `test_pipeline_constructs_when_typecast_env_missing`: clears TYPECAST_API_KEY → pipeline builds; `self.typecast is None`
    - Test 4 `test_pipeline_constructs_when_elevenlabs_env_missing`: clears ELEVENLABS_API_KEY → pipeline builds; `self.elevenlabs is None`
    - Test 5 `test_pipeline_all_adapters_missing_still_constructs`: all adapter env cleared simultaneously → pipeline builds; all 7 adapter slots None; one warning per missing adapter (7 warnings); but pipeline.run() would raise on dispatch — not tested here

    **test_argparse_session_id.py (3 tests):**
    - Test 1 `test_session_id_optional`: `main(["--state-root", str(tmp_path)])` without --session-id does NOT raise SystemExit; pipeline would attempt to run but we patch ShortsPipeline — assert constructor received a session_id matching `r'^\d{8}_\d{6}$'` (timestamp format)
    - Test 2 `test_session_id_auto_default_generates_timestamp`: like Test 1, verify datetime.now() called, session_id format YYYYMMDD_HHMMSS
    - Test 3 `test_explicit_session_id_override`: `main(["--session-id", "sess_test_override", "--state-root", str(tmp_path)])` → ShortsPipeline receives `session_id="sess_test_override"`

    All tests use MagicMock to inject all 7 adapters to avoid real adapter construction during instantiation tests.
  </behavior>
  <action>
    Create `tests/phase11/test_adapter_graceful_degrade.py`:
    ```python
    """PIPELINE-03 adapter graceful-degrade tests (5 cases)."""
    from __future__ import annotations

    import logging
    import os
    from pathlib import Path
    from unittest.mock import MagicMock

    import pytest


    _ADAPTER_ENV_KEYS = {
        "kling":      ("KLING_API_KEY", "FAL_KEY"),
        "runway":     ("RUNWAY_API_KEY",),
        "typecast":   ("TYPECAST_API_KEY",),
        "elevenlabs": ("ELEVENLABS_API_KEY",),
        "shotstack":  ("SHOTSTACK_API_KEY",),
        "nanobanana": ("GOOGLE_API_KEY",),
    }


    def _clear_env(monkeypatch, keys):
        for k in keys:
            monkeypatch.delenv(k, raising=False)


    def _build_pipeline_skipping_adapter(adapter_name: str, monkeypatch, tmp_path, caplog):
        """Clear env keys for the given adapter; construct pipeline.

        Returns (pipeline, captured warning records filtered to the adapter).
        """
        from scripts.orchestrator import ShortsPipeline

        # Clear env for the target adapter
        for key in _ADAPTER_ENV_KEYS.get(adapter_name, ()):
            monkeypatch.delenv(key, raising=False)

        # Mock ALL other invokers + checkpointer dependencies so constructor
        # is safe to call without a full environment.
        caplog.set_level(logging.WARNING, logger="scripts.orchestrator.shorts_pipeline")
        pipeline = ShortsPipeline(
            session_id="test_graceful",
            state_root=tmp_path,
            producer_invoker=MagicMock(),
            supervisor_invoker=MagicMock(),
        )
        # Adapter whose env we cleared should be None (helper returned the
        # injected value, which defaults to None).
        adapter_attr = "ken_burns" if adapter_name == "ken_burns" else adapter_name
        assert getattr(pipeline, adapter_attr) is None, (
            f"pipeline.{adapter_attr} must be None when env missing"
        )
        adapter_warnings = [
            r for r in caplog.records
            if r.levelname == "WARNING" and adapter_name in r.getMessage()
        ]
        return pipeline, adapter_warnings


    def test_pipeline_constructs_when_kling_env_missing(monkeypatch, tmp_path, caplog):
        pipeline, warnings = _build_pipeline_skipping_adapter("kling", monkeypatch, tmp_path, caplog)
        assert pipeline is not None
        assert len(warnings) >= 1
        assert "대표님" in warnings[0].getMessage()


    def test_pipeline_constructs_when_runway_env_missing(monkeypatch, tmp_path, caplog):
        pipeline, warnings = _build_pipeline_skipping_adapter("runway", monkeypatch, tmp_path, caplog)
        assert pipeline is not None
        assert len(warnings) >= 1
        assert "대표님" in warnings[0].getMessage()


    def test_pipeline_constructs_when_typecast_env_missing(monkeypatch, tmp_path, caplog):
        pipeline, warnings = _build_pipeline_skipping_adapter("typecast", monkeypatch, tmp_path, caplog)
        assert pipeline is not None
        assert len(warnings) >= 1
        assert "대표님" in warnings[0].getMessage()


    def test_pipeline_constructs_when_elevenlabs_env_missing(monkeypatch, tmp_path, caplog):
        pipeline, warnings = _build_pipeline_skipping_adapter("elevenlabs", monkeypatch, tmp_path, caplog)
        assert pipeline is not None
        assert len(warnings) >= 1
        assert "대표님" in warnings[0].getMessage()


    def test_pipeline_all_adapters_missing_still_constructs(monkeypatch, tmp_path, caplog):
        """All network adapters missing env → pipeline constructs, 6+ warnings logged."""
        from scripts.orchestrator import ShortsPipeline

        # Clear all adapter env keys
        for keys in _ADAPTER_ENV_KEYS.values():
            for k in keys:
                monkeypatch.delenv(k, raising=False)

        caplog.set_level(logging.WARNING, logger="scripts.orchestrator.shorts_pipeline")
        pipeline = ShortsPipeline(
            session_id="test_all_missing",
            state_root=tmp_path,
            producer_invoker=MagicMock(),
            supervisor_invoker=MagicMock(),
        )

        # All 6 network adapter slots should be None (ken_burns depends on
        # ffmpeg; may or may not be available — not asserted here).
        assert pipeline.kling is None
        assert pipeline.runway is None
        assert pipeline.typecast is None
        assert pipeline.elevenlabs is None
        assert pipeline.shotstack is None
        assert pipeline.nanobanana is None

        # At least one warning per adapter that was missing
        warn_msgs = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
        for adapter in ("kling", "runway", "typecast", "elevenlabs", "shotstack", "nanobanana"):
            assert any(adapter in m for m in warn_msgs), (
                f"Expected a warning mentioning {adapter!r}; got: {warn_msgs}"
            )
    ```

    Create `tests/phase11/test_argparse_session_id.py`:
    ```python
    """PIPELINE-04 tie-in — argparse session-id relax (3 cases, D-16)."""
    from __future__ import annotations

    import re
    from pathlib import Path
    from unittest.mock import MagicMock, patch

    import pytest


    _TS_RE = re.compile(r"^\d{8}_\d{6}$")


    def _run_main(monkeypatch, argv, tmp_path):
        """Patch ShortsPipeline to a recording MagicMock; call main(argv)."""
        from scripts.orchestrator import shorts_pipeline as sp

        recorded = {}

        class RecordingPipeline:
            def __init__(self, session_id, state_root, **kwargs):
                recorded["session_id"] = session_id
                recorded["state_root"] = state_root

            def run(self):
                return "ok"

        monkeypatch.setattr(sp, "ShortsPipeline", RecordingPipeline)
        # Ensure state-root present for any argv
        full_argv = list(argv) + ["--state-root", str(tmp_path)]
        rc = sp.main(full_argv)
        return rc, recorded


    def test_session_id_optional(monkeypatch, tmp_path):
        """main() without --session-id must NOT raise SystemExit."""
        rc, recorded = _run_main(monkeypatch, [], tmp_path)
        assert rc == 0
        assert "session_id" in recorded
        assert _TS_RE.match(recorded["session_id"]), (
            f"Expected auto-generated timestamp; got {recorded['session_id']!r}"
        )


    def test_session_id_auto_default_generates_timestamp(monkeypatch, tmp_path):
        """Auto default must be `datetime.now().strftime('%Y%m%d_%H%M%S')` shape."""
        rc, recorded = _run_main(monkeypatch, [], tmp_path)
        assert rc == 0
        assert _TS_RE.match(recorded["session_id"])


    def test_explicit_session_id_override(monkeypatch, tmp_path):
        """Explicit --session-id wins over auto-default."""
        rc, recorded = _run_main(monkeypatch, ["--session-id", "sess_test_override"], tmp_path)
        assert rc == 0
        assert recorded["session_id"] == "sess_test_override"
    ```

    All 5+3=8 tests RED until Task 2 lands.
  </action>
  <verify>
    <automated>pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py --collect-only -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `tests/phase11/test_adapter_graceful_degrade.py` exists with 5 test functions
    - `tests/phase11/test_argparse_session_id.py` exists with 3 test functions
    - Collection succeeds for both files (no syntax errors)
    - `pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -v 2>&1 | grep -E "FAILED|ERROR"` → non-zero count (RED expected)
  </acceptance_criteria>
  <done>8 RED tests seeded covering adapter degrade + argparse relax.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement _try_adapter helper + 7 unified calls + argparse relax — line budget -2</name>
  <files>scripts/orchestrator/shorts_pipeline.py</files>
  <read_first>
    - scripts/orchestrator/shorts_pipeline.py (L1-100 imports; L180-250 adapter block; L740-770 argparse)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 3 (L657-688 helper skeleton) + §Line Budget (L771-782)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-05, D-06, D-07, D-16
    - tests/phase11/test_adapter_graceful_degrade.py (from Task 1)
    - tests/phase11/test_argparse_session_id.py (from Task 1)
  </read_first>
  <behavior>
    - 8 Phase 11 tests GREEN (5 degrade + 3 argparse)
    - `shorts_pipeline.py` line count: was 796, after change must be ≤ 798 (target -2 per §Line Budget, margin ≤ +2 if needed but MUST stay ≤ 800)
    - Phase 4 baseline 244/244 GREEN (adapter internals unchanged per D-06)
    - Phase 5 adapter tests continue passing (tests patch adapter classes directly, not pipeline)
    - Pipeline `--session-id` optional (required=False + auto-default)
    - Explicit `--session-id` still works
  </behavior>
  <action>
    **Part A — Replace adapter block L209-235 with helper + unified calls.**

    Step 1: Ensure imports at top include `KenBurnsUnavailable` (already imported near L50-70 region; if not, add `from .api.ken_burns import KenBurnsUnavailable`).

    Step 2: Replace the ENTIRE block at L209-235 (current 27 lines) with the following 21-line block:

    ```python
            # Adapters (injected for tests, constructed from env otherwise).
            # Missing env for an adapter is logged + the slot is set to the
            # injected arg (usually None) so mock-based test harnesses still
            # construct cleanly; real runs that DISPATCH to a missing adapter
            # raise at use-site (D-05 '동일 패턴' via helper; D-06 adapter
            # internals untouched; line-budget §Line Budget: net -5 on block).
            def _try_adapter(name, build, injected, hint):
                try:
                    return build()
                except (ValueError, KenBurnsUnavailable) as err:
                    suffix = f" — {hint}" if hint else ""
                    logger.warning("[pipeline] %s adapter 미초기화 (대표님%s): %s", name, suffix, err)
                    return injected

            self.kling      = kling_adapter      or _try_adapter("kling",      lambda: KlingI2VAdapter(circuit_breaker=self.kling_breaker),           kling_adapter,      "KLING_API_KEY / FAL_KEY 없음")
            self.runway     = runway_adapter     or _try_adapter("runway",     lambda: RunwayI2VAdapter(circuit_breaker=self.runway_breaker),         runway_adapter,     "RUNWAY_API_KEY 없음")
            self.typecast   = typecast_adapter   or _try_adapter("typecast",   lambda: TypecastAdapter(circuit_breaker=self.typecast_breaker),       typecast_adapter,   "TYPECAST_API_KEY 없음")
            self.elevenlabs = elevenlabs_adapter or _try_adapter("elevenlabs", lambda: ElevenLabsAdapter(circuit_breaker=self.elevenlabs_breaker),   elevenlabs_adapter, "ELEVENLABS_API_KEY 없음")
            self.shotstack  = shotstack_adapter  or _try_adapter("shotstack",  lambda: ShotstackAdapter(circuit_breaker=self.shotstack_breaker),     shotstack_adapter,  "SHOTSTACK_API_KEY 없음, Phase 9.1 ken_burns 로컬 대체")
            self.nanobanana = nanobanana_adapter or _try_adapter("nanobanana", lambda: NanoBananaAdapter(circuit_breaker=self.nanobanana_breaker),   nanobanana_adapter, "GOOGLE_API_KEY 없음")
            self.ken_burns  = ken_burns_adapter  or _try_adapter("ken_burns",  lambda: KenBurnsLocalAdapter(circuit_breaker=self.ken_burns_breaker), ken_burns_adapter,  "ffmpeg 확인 필요")
    ```

    Note the comment about D-05 "동일 패턴" — helper preserves identical log shape `"[pipeline] X adapter 미초기화 (대표님 — HINT): err"` matching the existing shotstack format verbatim.

    **Part B — Relax argparse + auto-timestamp (around L746-760).**

    Locate the argparse block. Replace:
    ```python
    parser.add_argument("--session-id", required=True, help="Session identifier")
    ```
    with:
    ```python
    parser.add_argument(
        "--session-id", required=False, default=None,
        help="Session identifier (default: yyyyMMdd_HHMMSS auto-generated)",
    )
    ```

    And replace the `ShortsPipeline(session_id=args.session_id, ...)` construction with:
    ```python
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=Path(args.state_root),
    )
    ```

    Ensure `from datetime import datetime` is present near the top (it is — existing import; confirm by `grep -n "from datetime import" scripts/orchestrator/shorts_pipeline.py`).

    **Part C — Line budget verification.**

    After edits, run:
    ```
    python -c "print(sum(1 for _ in open('scripts/orchestrator/shorts_pipeline.py', encoding='utf-8')))"
    ```
    Expected: 794 (±1). MUST be ≤ 800.

    **Part D — Verification sweep.**
    ```
    pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -v   # 8 GREEN
    pytest tests/phase04/ -q                                                                               # 244/244
    pytest tests/phase05/test_line_count.py -v                                                            # line count cap GREEN
    pytest tests/phase05/ -q 2>&1 | tail -20                                                              # Phase 5 baseline
    ```

    If `tests/phase05/test_line_count.py::test_shorts_pipeline_under_soft_cap` fails, the helper needs further compaction — consolidate the 7 one-liner lambdas if necessary, but preserve the exact log message format for D-05 compliance.
  </action>
  <verify>
    <automated>pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py tests/phase04/ tests/phase05/test_line_count.py -q 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def _try_adapter" scripts/orchestrator/shorts_pipeline.py` returns 1 match
    - `grep -c "_try_adapter(" scripts/orchestrator/shorts_pipeline.py` returns 8 (1 def + 7 call sites)
    - `grep -n "required=False" scripts/orchestrator/shorts_pipeline.py` returns ≥1 match on the `--session-id` argparse line
    - `grep -n "args.session_id or datetime" scripts/orchestrator/shorts_pipeline.py` returns 1 match
    - Line count: `python -c "print(sum(1 for _ in open('scripts/orchestrator/shorts_pipeline.py', encoding='utf-8')))"` returns a number ≤ 800 (target ~794)
    - `pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -v` → 8 passed
    - `pytest tests/phase04/ -q` → 244/244 passed
    - `pytest tests/phase05/test_line_count.py -v` → line-count caps GREEN
    - `grep -c "except ValueError" scripts/orchestrator/shorts_pipeline.py` decreases relative to prior (3 old blocks collapsed into 1 helper) — expect 1 occurrence inside `_try_adapter`
    - No files under `scripts/orchestrator/api/` modified: `git status scripts/orchestrator/api/` reports clean for this plan
  </acceptance_criteria>
  <done>8 Phase 11 tests GREEN + line count ≤ 800 + 244/244 phase04 preserved + adapter internals untouched (D-06).</done>
</task>

</tasks>

<verification>
**Per-plan verify:**
```bash
pytest tests/phase11/test_adapter_graceful_degrade.py tests/phase11/test_argparse_session_id.py -v  # 8 GREEN
pytest tests/phase04/ -q                                                                             # 244/244
pytest tests/phase05/test_line_count.py -v                                                          # cap GREEN
python -c "print(sum(1 for _ in open('scripts/orchestrator/shorts_pipeline.py', encoding='utf-8')))"  # ≤ 800
git status scripts/orchestrator/api/                                                                 # clean
```

**PIPELINE-03 linkage:** Adapters no longer block construction. **PIPELINE-04 tie-in:** session-id auto-default enables wrapper UX (Plan 11-04 will consume).
</verification>

<success_criteria>
- [ ] `_try_adapter` helper defined inside `ShortsPipeline.__init__` (or at module scope if structurally equivalent)
- [ ] All 7 adapter instantiations use the helper — 동일 패턴 (D-05)
- [ ] `scripts/orchestrator/api/*.py` UNTOUCHED (D-06)
- [ ] `shorts_pipeline.py` line count ≤ 800
- [ ] `--session-id` argparse optional with auto-timestamp default (D-16)
- [ ] Explicit `--session-id` still works
- [ ] 8 Phase 11 tests GREEN (5 degrade + 3 argparse)
- [ ] 244/244 phase04 baseline preserved
</success_criteria>

<output>
After completion, create `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-03-SUMMARY.md` with:
- Files modified + net line delta on shorts_pipeline.py (target -2)
- Test count before/after (264 → 272)
- Line-count verification output
- Confirmation adapter internals untouched (git status clean for api/)
</output>
