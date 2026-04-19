---
phase: 06-wiki-notebooklm-integration-failures-reservoir
plan: 05
subsystem: wave-2-fallback-chain
tags: [notebooklm, fallback-chain, wiki-04, d-5, d-7, rag, grep-wiki, hardcoded-defaults, fault-injection, protocol, runtime-checkable]

# Dependency graph
requires:
  - phase: 06
    plan: 01
    provides: tests/phase06/conftest.py (tmp_wiki_dir + mock_notebooklm_skill_env fixtures — reused for keyword intersection and fault-injection tests)
  - phase: 06
    plan: 03
    provides: scripts/notebooklm/query.py query_notebook subprocess boundary (RAGBackend imports verbatim — single subprocess path preserved per D-7)
  - plan: 06-CONTEXT (D-5 3-tier mandate, D-10 canonical 5-component continuity, D-16 한국 시니어 context)
  - plan: 06-RESEARCH §Area 4 lines 619-690 (interface contract + failure mode matrix + deterministic test strategy + fault injection recipe)
provides:
  - scripts/notebooklm/fallback.py (231 lines — QueryBackend Protocol + 3 backends + chain orchestrator)
  - tests/phase06/test_fallback_chain.py (193 lines / 15 unit tests — backend isolation + chain sequencing + protocol runtime-check)
  - tests/phase06/test_fallback_injection.py (99 lines / 3 integration tests — D-5 acceptance via monkeypatched subprocess rc=1)
affects:
  - "Phase 7 E2E agent queries can rely on graceful degradation — no hard-fail when Google NotebookLM is down, auth expires, or notebook_id missing"
  - "Any downstream agent that needs RAG now has a 3-tier safety net instead of a single point of failure at Google"
  - "RuntimeError('all NotebookLM fallback tiers exhausted') literal is contract — pinned by test_chain_all_fail_raises_exhausted + test_chain_empty_backends_raises_exhausted; Phase 7 E2E monkeypatch can assert this exact string"

# Tech tracking
tech-stack:
  added: []  # stdlib-only: re, pathlib.Path, typing.Protocol + runtime_checkable. Zero new deps.
  patterns:
    - "Protocol-based backend interface with @runtime_checkable — structural typing for substitutability + isinstance() defense. Test test_query_backend_protocol_runtime_checkable locks the runtime-check capability so a future refactor removing the decorator trips CI."
    - "Keyword intersection semantics in GrepWikiBackend — ALL extracted tokens must appear for a hit, not ANY. Prevents noisy single-keyword matches that would dilute Tier 1 usefulness. Pinned by test_grep_wiki_requires_all_keywords with an intentionally partial-match md file."
    - "Korean-aware tokenizer regex r'[\\w가-힣]{3,}' — pulls ASCII word chars OR Hangul syllables, min length 3, first 5 tokens. Ko + En mixed questions (e.g., 'retention 완주율') tokenize cleanly in both scripts."
    - "Chain fall-through via broad Exception catch INSIDE NotebookLMFallbackChain.query only — individual backends must still raise verbatim so Phase 7 E2E logs can correlate diagnostic stderr with tier transitions. The single blanket catch is the ONLY silent-swallow site and is explicitly D-5 contract."
    - "Tier 2 never-raises guarantee — HardcodedDefaultsBackend.query returns sentinel for unknown ids. Eliminates the 'all three tiers fail' branch in practice; the final RuntimeError is only reachable if the user passes backends=[] or substitutes all 3 with failing Fakes (tested both)."
    - "D-7 subprocess boundary preservation — RAGBackend.query is a one-liner delegating to query_notebook. Zero subprocess/encoding/marker-strip duplication between Plan 03 and Plan 05. Any future change to the subprocess contract affects exactly one file."

key-files:
  created:
    - scripts/notebooklm/fallback.py (231 lines — QueryBackend Protocol, RAGBackend/GrepWikiBackend/HardcodedDefaultsBackend, NotebookLMFallbackChain)
    - tests/phase06/test_fallback_chain.py (193 lines, 15 unit tests)
    - tests/phase06/test_fallback_injection.py (99 lines, 3 integration tests)
  modified:
    - .planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md (rows 6-05-01 + 6-05-02 flipped ⬜ pending -> ✅ green with file-exists ✅)

key-decisions:
  - "Tier 2 DEFAULTS keyed by notebook_id exactly — chosen over keyword-based dispatch because (a) notebook_id is the canonical identity per D-4, (b) hardcoded strings are deliberately minimal (one short sentence each) and do not benefit from fuzzy matching, (c) sentinel for unknown ids ('fallback defaults unavailable for notebook_id=<id>') is trivially parseable so a caller can branch on degraded mode. Alternative (keyword scoring across DEFAULTS) rejected as over-engineered for a safety-net tier."
  - "GrepWikiBackend constants (SNIPPET_CHARS=500, KEYWORD_LIMIT=5, MIN_KEYWORD_LEN=3) hoisted to class attributes — testable via subclassing/override without editing production code. 500 chars per snippet chosen as a practical balance: long enough to capture one md section heading + opening paragraph, short enough that even 10 hits stay under 5KB (well below LLM context budgets downstream)."
  - "GrepWikiBackend keyword extraction uses re.findall once (not a loop), no lowercasing inside the loop — normalization happens exactly once before the file loop. Per-file cost = O(len(text) * keyword_count) for the `in` checks; for 10s of md files under wiki/ this is sub-millisecond even on Windows."
  - "`sorted(rglob(...))` in GrepWikiBackend — deterministic ordering so snippet concatenation is reproducible across runs and platforms. Tests don't depend on ordering but Phase 7 E2E diffs will benefit."
  - "Broad `except Exception` inside NotebookLMFallbackChain.query is intentional and documented inline — this is the ONE place where silent swallow is D-5 contract. The ``# noqa: BLE001`` comment prevents future linter auto-fixes from narrowing the catch (which would silently regress D-5 coverage for novel error types)."
  - "HardcodedDefaultsBackend strings kept extremely short (single sentence each) — the goal is 'last-known-good minimal context', not 'fake full answer'. A downstream agent receiving '색상=navy+gold, lens=35mm, style=cinematic, audience=한국 시니어, bgm=ambient' has enough to populate ContinuityPrefix defaults; attempting to generate multi-paragraph mock RAG answers would be dishonest (violates Professional Honesty rule) and would mask real RAG outages from pipeline operators."
  - "18 tests shipped vs plan's >=15 target — 3 bonus guards: test_hardcoded_known_id_production_bible_returns_YPP_canonical (locks the shorts-production-pipeline-bible D-5 string), test_grep_wiki_requires_all_keywords (proves intersection-not-union semantics), test_query_backend_protocol_runtime_checkable (pins @runtime_checkable decorator contract). Extras are pure regression guards, ~25ms added runtime."

patterns-established:
  - "Pattern: Tiered fallback chain with Protocol-based backends. scripts/notebooklm/fallback.py is the prototype — Protocol + concrete implementations that raise on failure + orchestrator that returns (answer, tier_used) tuple. Any future external-service dependency with a 'degraded mode acceptable' characteristic should follow this shape (e.g., Kling -> Runway -> manual B-roll; Typecast -> ElevenLabs -> silent text). Naming convention: <Service>Backend for tiers, <Service>FallbackChain for orchestrator, QueryBackend-style Protocol."
  - "Pattern: fault injection via fixture rewrite. test_fallback_injection.py rewrites mock_notebooklm_skill_env's scripts/run.py to emit rc=1 + stderr, proving the real RAGBackend (not a Fake) falls through. Reusable recipe for any subprocess-wrapped dependency — write failing child, let wrapper raise, assert chain tier transition."
  - "Pattern: sentinel string for unknown keys instead of None/exception. HardcodedDefaultsBackend returns `f'fallback defaults unavailable for notebook_id={notebook_id}'` for unknown ids. Caller can branch on presence of 'unavailable' substring, or parse the id back out. Avoids Optional[str] return type noise downstream. Tradeoff: caller must not confuse the sentinel with a real answer — but the sentinel is deliberately impossible to mistake for legitimate output."

requirements-completed: [WIKI-04]

# Metrics
duration: ~7m
completed: 2026-04-19
---

# Phase 6 Plan 05: Wave 2 Fallback Chain Summary

**`scripts.notebooklm.fallback.NotebookLMFallbackChain` shipped — 3-tier graceful-degradation orchestrator per D-5. Tier 0 (RAGBackend via Plan 03 query_notebook) raises on subprocess failure; Tier 1 (GrepWikiBackend) does keyword-intersection grep across wiki/**/*.md and raises 'grep wiki: no hits' when empty; Tier 2 (HardcodedDefaultsBackend) never raises — returns D-10/D-16 canonical strings for known notebook ids, deterministic sentinel for unknown. Chain.query returns (answer, tier_used) on first success; only raises 'all NotebookLM fallback tiers exhausted' when every backend failed. 18 tests green (15 unit + 3 fault-injection proving D-5 acceptance via monkeypatched subprocess rc=1). Phase 5 329/329 regression preserved. Plan 07 Shotstack prefix injection + Phase 7 E2E agent query paths now have a production-ready safety net.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-04-19T07:49:48Z
- **Tasks:** 2 / 2 complete
- **Files created:** 3 (1 module + 2 test files = 523 lines total)
- **Files modified:** 1 (06-VALIDATION.md — rows 6-05-01/02 flipped ✅ green)
- **Tests added:** 18 (15 fallback_chain + 3 fallback_injection)
- **Phase 6 full suite:** 90/90 PASS (15 Plan 01 + 21 Plan 02 + 21 Plan 03 + 15 Plan 04 + 18 Plan 05)
- **Phase 5 regression:** 329/329 PASS

## Accomplishments

### Task 1 — `scripts/notebooklm/fallback.py` — 3-tier chain (commit `25993bb`, GREEN)

**Module structure (231 lines):**

1. **Module docstring** — D-5 rationale, tier matrix, acceptance criterion, design notes.
2. **`QueryBackend` Protocol** — `@runtime_checkable` so `isinstance()` works. Single method `query(question: str, notebook_id: str) -> str`. Docstring pins "MUST raise on failure" contract.
3. **`RAGBackend` (Tier 0)** — one-line wrapper over `scripts.notebooklm.query.query_notebook`. Zero duplication of subprocess/encoding/marker-strip logic (D-7 single boundary preserved).
4. **`GrepWikiBackend` (Tier 1)** — class constants `WIKI_ROOT_DEFAULT / SNIPPET_CHARS=500 / KEYWORD_LIMIT=5 / MIN_KEYWORD_LEN=3`. `_extract_keywords` uses `r'[\w가-힣]{3,}'` for Korean-aware tokenization. `query()` does case-insensitive intersection match, returns `\n\n`.join(snippets), raises `"grep wiki: no hits"` / `"grep wiki: empty keyword set"` on failure. Handles missing wiki dir gracefully (no hits -> raise).
5. **`HardcodedDefaultsBackend` (Tier 2)** — class-level `DEFAULTS` dict with D-10/D-5 canonical strings keyed by notebook_id. `query()` is one line — `self.DEFAULTS.get(notebook_id, f"fallback defaults unavailable for notebook_id={notebook_id}")`. Never raises.
6. **`NotebookLMFallbackChain`** — default `__init__` wires `[RAGBackend(), GrepWikiBackend(), HardcodedDefaultsBackend()]` in order. `query()` iterates via `enumerate`, broad `except Exception` with `# noqa: BLE001` (documented inline as D-5 contract), returns `(answer, tier_index)` on first success, raises `"all NotebookLM fallback tiers exhausted"` after the loop exits.
7. **`__all__`** locks the 5-symbol public surface.

**Acceptance criteria PASS (Task 1):**

- `python -c "import scripts.notebooklm.fallback"` exits 0 ✅
- `grep -c "class QueryBackend"` = 1 ✅
- `grep -c "class RAGBackend"` = 1 ✅
- `grep -c "class GrepWikiBackend"` = 1 ✅
- `grep -c "class HardcodedDefaultsBackend"` = 1 ✅
- `grep -c "class NotebookLMFallbackChain"` = 1 ✅
- `grep -c "all NotebookLM fallback tiers exhausted"` = 3 (>=1) ✅
- `grep -c "navy"` = 1 (>=1) ✅
- `grep -c "한국 시니어"` = 1 (>=1) ✅
- `grep -c "from .query import"` = 1 ✅
- Sanity runner: HardcodedDefaultsBackend seeded answer contains 색상+navy+cinematic; unknown id returns exact sentinel; default chain len==3; all checks → OK ✅

### Task 2 — tests (commits `0369f8b` RED + `25993bb` makes them GREEN)

**`tests/phase06/test_fallback_chain.py` (193 lines, 15 unit tests):**

| # | Test | Target |
|---|------|--------|
| 1 | `test_hardcoded_known_id_channel_bible_returns_D10_canonical` | Tier 2 contains 색상+navy+cinematic+한국 시니어 |
| 2 | `test_hardcoded_known_id_production_bible_returns_YPP_canonical` | Tier 2 contains YPP+T2V+I2V only |
| 3 | `test_hardcoded_unknown_id_returns_sentinel` | Exact string contract |
| 4 | `test_hardcoded_never_raises` | Tier 2 safety net |
| 5 | `test_grep_wiki_finds_keyword_intersection` | Tier 1 happy path |
| 6 | `test_grep_wiki_no_hits_raises` | "grep wiki: no hits" surface |
| 7 | `test_grep_wiki_empty_question_raises` | "empty keyword set" surface |
| 8 | `test_grep_wiki_requires_all_keywords` | Intersection (not union) semantics |
| 9 | `test_chain_default_constructs_3_backends` | Default constructor wires [RAG, grep, defaults] in order |
| 10 | `test_chain_tier_0_success_short_circuits` | tier=0 return |
| 11 | `test_chain_falls_through_to_tier_1` | tier=1 return |
| 12 | `test_chain_falls_through_to_tier_2` | tier=2 return + Tier 2 canonical content |
| 13 | `test_chain_all_fail_raises_exhausted` | Final RuntimeError literal |
| 14 | `test_chain_empty_backends_raises_exhausted` | Empty list -> exhausted |
| 15 | `test_query_backend_protocol_runtime_checkable` | `isinstance()` works |

**`tests/phase06/test_fallback_injection.py` (99 lines, 3 integration tests — D-5 acceptance):**

| # | Test | Evidence |
|---|------|----------|
| 1 | `test_real_rag_backend_falls_through_on_auth_failure` | Rewrites fake skill's run.py to emit stderr+rc=1; seeds wiki with keyword-matching md; asserts `tier in (1, 2)` — D-5 canonical acceptance |
| 2 | `test_real_rag_backend_falls_through_to_defaults_when_wiki_empty` | rc=1 + empty wiki dir -> Tier 2 fires; asserts `tier == 2` + 'navy' or 'cinematic' in answer |
| 3 | `test_rag_success_returns_tier_0` | rc=0 subprocess; asserts tier=0 short-circuit (includes `sys.stdout.reconfigure(encoding='utf-8')` in child for Windows cp949 survival — mirrors Plan 03 test discipline) |

**Acceptance criteria PASS (Task 2):**

- `pytest test_fallback_chain.py -q --no-cov` exits 0 ✅ (15 tests)
- `pytest test_fallback_injection.py -q --no-cov` exits 0 ✅ (3 tests)
- `grep -cE "^def test_" test_fallback_chain.py` = 15 (>=12) ✅
- `grep -cE "^def test_" test_fallback_injection.py` = 3 (>=3) ✅
- `grep -c "tier == 2" test_fallback_injection.py` = 1 (>=1) ✅
- `grep -c "exhausted" test_fallback_chain.py` = 4 (>=1) ✅

## Task Commits

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1a | RED — failing tests for 3-tier chain | `0369f8b` | tests/phase06/test_fallback_chain.py (193 / 15 tests), tests/phase06/test_fallback_injection.py (99 / 3 tests) |
| 1b | GREEN — fallback.py implementation | `25993bb` | scripts/notebooklm/fallback.py (231 lines) |

Plan metadata commit: pending (final step — includes SUMMARY + STATE + ROADMAP + REQUIREMENTS + VALIDATION updates).

## D-5 Fault-Injection Evidence

The canonical D-5 acceptance criterion from ROADMAP SC #3 is **"intentional API fail simulation"**. Three integration tests prove this end-to-end:

1. **`test_real_rag_backend_falls_through_on_auth_failure`** — rewrites the fake skill's `run.py` to `sys.stderr.write('not authenticated'); sys.exit(1)`. The real `RAGBackend.query(...)` raises `RuntimeError` as per Plan 03 contract. Chain catches, advances to Tier 1 `GrepWikiBackend`, which finds `channel_identity.md` containing '색상' and '한국' keywords. Result: `tier in (1, 2)`, answer non-empty.

2. **`test_real_rag_backend_falls_through_to_defaults_when_wiki_empty`** — same subprocess failure + empty wiki dir forces Tier 1 to raise 'grep wiki: no hits'. Tier 2 activates deterministically. Asserts `tier == 2` and answer contains 'navy' or 'cinematic' (D-10 canonical substrings).

3. **`test_rag_success_returns_tier_0`** — control case. rc=0 subprocess; chain returns `tier == 0` and full answer passes through. Proves the short-circuit is not broken by the fault-injection plumbing.

Chain invariants pinned:
- RAG failure NEVER reaches caller as an unhandled exception (unless wiki is empty AND notebook_id is unknown AND caller explicitly passes `backends=[]` or all-failing Fakes).
- Tier 2 is the safety net: for any `notebook_id` the caller passes, Tier 2 returns SOME string, even if it's the sentinel.
- The literal `"all NotebookLM fallback tiers exhausted"` is pinned by 4 greps and 2 explicit test assertions — Phase 7 E2E monkeypatch tests can rely on this exact substring.

## Plan-required verification suite

| Check | Result |
|-------|--------|
| `python -c "from scripts.notebooklm.fallback import NotebookLMFallbackChain; chain = NotebookLMFallbackChain(); assert len(chain.backends) == 3; print('OK')"` | PASS (OK) |
| `python -m pytest tests/phase06/test_fallback_chain.py tests/phase06/test_fallback_injection.py -q --no-cov` exits 0 | PASS (18 passed in 0.20s) |
| `grep -c "all NotebookLM fallback tiers exhausted" scripts/notebooklm/fallback.py` >= 1 | PASS (=3) |
| Hardcoded defaults contain 한국 시니어 + navy + cinematic + T2V 금지 I2V only | PASS (all 4 literals grep-confirmed) |
| Tier 0 short-circuit + Tier 1 fall-through + Tier 2 degradation proven | PASS (tests 10, 11, 12 + injection tests 1-3) |
| Phase 5 regression | PASS (329/329) |
| Phase 6 full suite | PASS (90/90) |

## Decisions Made

See `key-decisions` in frontmatter. Highlights:

- **Tier 2 keyed by notebook_id exactly** (not keyword scoring) — D-4 canonical identity + deliberately minimal strings + deterministic sentinel for unknown ids. Over-engineering avoided.
- **GrepWikiBackend intersection-not-union semantics** — ALL keywords must match. Pinned by `test_grep_wiki_requires_all_keywords`. Prevents noisy single-term matches.
- **Broad `except Exception` documented with `# noqa: BLE001`** — the ONE silent-swallow site in the codebase, and it's D-5 contract. Linter override prevents future auto-fix from narrowing.
- **18 tests vs plan's >=15** — 3 bonus guards locked additional invariants (production-bible canonical, intersection semantics, Protocol runtime-check).
- **Class constants hoisted** (SNIPPET_CHARS, KEYWORD_LIMIT, MIN_KEYWORD_LEN) — testable via subclassing.

## Deviations from Plan

**None.** Plan 05 executed exactly as written. No Rule 1 (bugs), Rule 2 (missing functionality), Rule 3 (blockers), or Rule 4 (architectural) deviations encountered.

The plan specified `>=12 / >=3` test def counts and the implementation shipped 15 / 3 — the extra 3 tests in test_fallback_chain.py are not deviations, they are extensions beyond the plan's minimum bar (additional invariant guards, zero extra runtime impact, zero contract changes). All bonus tests were derivable from the plan's `<behavior>` specification.

## Authentication Gates

None. Plan 05 is pure wrapper code. No NotebookLM API calls executed (the `mock_notebooklm_skill_env` fixture replaces the real skill with a tmp_path fake). The real Playwright authentication gate continues to live in Plan 04 canary query (already deferred via deferred-items.md entry D-04-01).

## Known Stubs

None. Every created file contains substantive production code or genuine assertions:

- `scripts/notebooklm/fallback.py` (231 lines) — 4 concrete classes + Protocol + orchestrator, no placeholders, no TODOs, no stub bodies.
- `tests/phase06/test_fallback_chain.py` (193 lines) — 15 real assertions, no skipped or stubbed tests.
- `tests/phase06/test_fallback_injection.py` (99 lines) — 3 real subprocess round-trips through fake skill trees with fault injection.

Zero `TODO`, `FIXME`, `not implemented`, `pass`-only bodies, `skip_gates`, `TODO(next-session)`, or lowercase `t2v` tokens in any new file.

## Deferred Issues

**None new this plan.**

Existing D-04-01 deferred item (real `naberal-shorts-channel-bible` NotebookLM URL) remains — Plan 05 is not blocked by it because the fallback chain's Tier 0 failure path is exactly what the canary-query blocker surfaces. If/when Plan 04 canary succeeds with a real URL, Tier 0 will serve answers; until then, Tier 1 (grep wiki) + Tier 2 (hardcoded defaults) keep the pipeline functional.

## Next Plan Readiness

**Plan 06 (Wave 3 Continuity Prefix Pydantic Schema) unblocked:**
- Nothing in Plan 06 depends on fallback.py directly — but the existence of a reliable RAG fallback means pydantic schema validation failures in production can log a clear diagnostic ("NotebookLM exhausted, hardcoded defaults used for field X") rather than silently corrupting render jobs.

**Plan 07 (Wave 3 Shotstack Prefix Injection) unblocked:**
- Shotstack adapter's filter chain can now consume ContinuityPrefix built from whichever tier actually succeeded. A tier-2 (hardcoded) answer still provides color palette + lens + style + audience + BGM — exactly the 5 fields Shotstack's prefix filter needs.

**Phase 7 E2E agent queries unblocked:**
- Any agent wrapping NotebookLM queries should now import `NotebookLMFallbackChain` instead of `query_notebook` directly. The (answer, tier_used) tuple lets the agent log degradation events without changing behavior.

**Recommended next action:** `/gsd:execute-phase 6` to advance to Plan 06 Wave 3 Continuity Prefix Pydantic Schema.

## Self-Check: PASSED

Verified on disk:
- `scripts/notebooklm/fallback.py` — FOUND (231 lines; QueryBackend, RAGBackend, GrepWikiBackend, HardcodedDefaultsBackend, NotebookLMFallbackChain all `class` defined)
- `tests/phase06/test_fallback_chain.py` — FOUND (193 lines, 15 test defs)
- `tests/phase06/test_fallback_injection.py` — FOUND (99 lines, 3 test defs)
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-VALIDATION.md` — MODIFIED (rows 6-05-01 + 6-05-02 flipped ✅ green)

Verified in git log:
- `0369f8b` (RED) — FOUND via `git log --oneline`
- `25993bb` (GREEN) — FOUND via `git log --oneline`

Verified at runtime:
- `python -c "from scripts.notebooklm.fallback import NotebookLMFallbackChain; print(len(NotebookLMFallbackChain().backends))"` → 3
- `python -m pytest tests/phase06/test_fallback_chain.py tests/phase06/test_fallback_injection.py -q --no-cov` → 18 passed
- `python -m pytest tests/phase06/ -q --no-cov` → 90 passed (15 Plan 01 + 21 Plan 02 + 21 Plan 03 + 15 Plan 04 + 18 Plan 05)
- `python -m pytest tests/phase05/ -q --no-cov` → 329 passed (regression preserved)
- No drift tokens in new files (skip_gates/TODO(next-session)/lowercase-t2v/text_to_video/text2video/segments — 0 hits)

**Phase 6 Plan 05 complete. Wave 2 Fallback Chain shipped. Ready for Plan 06 (Wave 3 Continuity Prefix Pydantic Schema).**

---
*Phase: 06-wiki-notebooklm-integration-failures-reservoir*
*Plan: 05 (Wave 2 Fallback Chain)*
*Completed: 2026-04-19*
