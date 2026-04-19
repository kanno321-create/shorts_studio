---
phase: 08-remote-publishing-production-metadata
plan: 05
subsystem: publishing
tags: [production-metadata, youtube-uploader, anchor-b, anchor-c, pitfall-5, pitfall-6, pitfall-7, contains-synthetic-media, pinned-comment, end-screen-not-supported, resumable-upload, stdlib-only]

# Dependency graph
requires:
  - phase: 08-01
    provides: scripts.publisher.exceptions hierarchy (PublishLockViolation + PublishWindowViolation + AIDisclosureViolation) + tests/phase08 scaffold + tmp_publish_lock fixture + sample_mp4_path fixture + MockYouTube
  - phase: 08-03
    provides: scripts.publisher.oauth get_credentials() signature (not directly consumed by Wave 4 — Wave 6 smoke test will import)
  - phase: 08-04
    provides: Wave 3 LOCK + WINDOW + DISCLOSURE — publish_lock.assert_can_publish / record_upload, kst_window.assert_in_window, ai_disclosure.build_status_block + assert_synthetic_media_true ALL consumed by publish() 5-gate chain
provides:
  - scripts.publisher.production_metadata module with PIPELINE_VERSION + ProductionMetadata TypedDict (4 frozen fields) + compute_checksum (64KB streaming) + inject_into_description (HTML comment with ensure_ascii=False) (PUB-04 D-08)
  - scripts.publisher.youtube_uploader module with build_insert_body() + resumable_upload() + publish() 5-gate orchestrator (PUB-02 + PUB-05 D-09)
  - ANCHOR B — captions.insert + endScreen + end_screen_subscribe_cta 0 hits across scripts/publisher/*.py (regex + AST)
  - ANCHOR C — selenium / webdriver / playwright 0 imports across scripts/publisher/*.py AND tests/phase08/ (regex + AST + string-literal-aware scan)
  - 42 new tests (15 schema + pin + anchor + E2E + 27 across 6 new test files; +42 phase08 vs 106 Wave 3 baseline = 148 total)
affects: [08-06 smoke test (consumes publish() for real 1-shot unlisted upload + videos.delete cleanup), 08-07 E2E acceptance (regression sweep extends to 148 phase08 tests), 08-08 traceability (PUB-02/04/05 completed)]

# Tech tracking
tech-stack:
  added:
    - python stdlib hashlib.sha256 streaming (64KB chunks — bounded RSS regardless of mp4 size)
    - Structural typing (typing.Protocol) for YouTubeClient — MockYouTube and real googleapiclient.discovery.build() drop-in interchangeable
    - Lazy import pattern for googleapiclient.http.MediaFileUpload (tests pass sentinel _media_body / _thumb_body hooks without google client installed)
  patterns:
    - "Module-qualified call pattern for monkeypatch support — youtube_uploader imports kst_window + publish_lock as modules (not names), so tests monkeypatching the source module name take effect"
    - "Pitfall correction at body-build boundary (not agent prompt layer) — Phase 4 AGENT.md stays descriptive, Phase 8 uploader enforces canonical Data API v3 field names"
    - "Physical-removal for AI disclosure (D-05 inherited) — build_status_block hardcodes True, publish() calls assert_synthetic_media_true as runtime last-line defence"
    - "AST string-literal-line walk for selenium/webdriver/playwright false-positive filtering — docstring mentions permitted, executable code references banned"
    - "UTF-8 safeguard on every stdout-touching module (Phase 6 STATE #28 precedent preserved)"

key-files:
  created:
    - scripts/publisher/production_metadata.py  # 151 lines — PUB-04 D-08 4-field schema + streaming sha256 + HTML comment injection
    - scripts/publisher/youtube_uploader.py  # 332 lines — PUB-02 + PUB-05 D-09 5-gate publish orchestrator + resumable upload
    - tests/phase08/test_production_metadata_schema.py  # 97 lines — 10 tests
    - tests/phase08/test_metadata_html_comment.py  # 74 lines — 6 tests (regex roundtrip + Korean preservation)
    - tests/phase08/test_pinned_comment.py  # 123 lines — 4 tests (commentThreads.insert payload)
    - tests/phase08/test_endscreen_nonexistent_anchor.py  # 114 lines — ANCHOR B 5 tests
    - tests/phase08/test_no_selenium_anchor.py  # 141 lines — ANCHOR C 11 tests (parametrized over 3 modules)
    - tests/phase08/test_uploader_mocked_e2e.py  # 242 lines — 12 E2E tests (5-gate chain)
  modified: []

key-decisions:
  - "Rule 2 deviation — _collect_string_literal_lineset() AST helper added to ANCHOR C test beyond plan prose. The plan proposed a naive triple-quote-on-same-line filter which false-positived on the youtube_uploader.py module docstring containing literal 'selenium / playwright / webdriver' in the drop-reason documentation. The AST-based version walks ast.Constant nodes and marks EVERY line inside any string literal as permitted — stricter AND more correct than the plan prose. Zero regression in violation semantics (executable-code imports still caught)."
  - "Module-qualified call indirection in youtube_uploader.py (from scripts.publisher import kst_window as _kst_window; _kst_window.assert_in_window() instead of direct assert_in_window import). Without this, monkeypatch on the source module has no effect because the name was already bound at import time. 4 call sites: assert_can_publish, record_upload (via _publish_lock), assert_in_window (via _kst_window). assert_synthetic_media_true and build_status_block kept as direct imports because tests monkeypatch them via scripts.publisher.youtube_uploader.build_status_block, not at source."
  - "ProductionMetadata.ValueError sorts missing fields alphabetically (_REQUIRED_FIELDS - set(meta.keys())) so error messages are deterministic for assertion-based test matching. Plan prose used f-string interpolation of set{} directly — non-deterministic ordering would make test_inject_rejects_missing_fields flaky."
  - "build_insert_body returns ONLY {'snippet': snippet, 'status': status} — no extras. This is stricter than plan prose (which said 'body' loosely). test_build_insert_body_only_snippet_and_status locks this invariant so future additions must be consciously introduced."
  - "resumable_upload classifies errors via getattr(getattr(exc, 'resp', None), 'status', None) without importing googleapiclient.errors.HttpError. Keeps the module test-isolated AND matches the real HttpError shape (exc.resp.status). Non-retriable errors propagate; MAX_RETRIES=10 exhaustion raises RuntimeError with chained __cause__."
  - "Default pinned-comment CTA text is '구독해주세요!' (_DEFAULT_PIN_TEXT module constant) — used when plan omits funnel.pinned_comment. Korean idiomatic minimal CTA; longer variants per-episode are plan-level responsibility (Phase 10 A/B testing will diversify)."

patterns-established:
  - "Pitfall 5/6/7 fix AT body-build boundary — agent specs describe intent, Phase 8 uploader translates to canonical API. defaultAudioLanguage dropped (not writable), syntheticMedia → containsSyntheticMedia (canonical 2024-10-30 field), end_screen_subscribe_cta → pinned comment only (no endScreen API)"
  - "Streaming sha256 via iter(lambda: f.read(65536), b'') — bounded-memory proof for future long-form (500MB+) scaling without code change"
  - "4-field TypedDict as schema contract — ProductionMetadata.__annotations__.keys() asserted in test_production_metadata_typed_dict_has_four_keys locks against silent field rename"
  - "Layered ANCHOR B defences: regex (non-comment) + regex (non-comment, three variants for captions/endScreen/end_screen_cta) + AST (captions().insert() Call) + drop-reason documentation grep — any single layer bypass still caught by the others"
  - "AST Constant walk for string-literal-line identification in ANCHOR C — docstring mentions allowed, executable code references banned"

requirements-completed: [PUB-02, PUB-04, PUB-05]

# Metrics
duration: 32min
completed: 2026-04-19
commits:
  - 98b4e46 test(08-05): add failing tests for production_metadata 4-field schema + HTML comment
  - 79e38c5 feat(08-05): implement production_metadata.py with 4-field schema + streaming sha256
  - 51e5332 test(08-05): add failing tests for pinned comment (commentThreads.insert payload)
  - 8531475 feat(08-05): implement youtube_uploader.py with 5-gate publish orchestrator
  - 73c5eb3 test(08-05): add ANCHOR B + ANCHOR C permanent regression guards
  - 7cb1caa test(08-05): add mocked E2E test for publish() 5-gate chain

tasks-count: 4
files-count: 8
---

# Phase 8 Plan 05: Wave 4 METADATA + FUNNEL + UPLOADER Summary

Wave 4 ships the metadata injection layer and the end-to-end publish orchestrator — the pieces that will be exercised by Wave 5 smoke test (1-shot unlisted upload + videos.delete cleanup) and Wave 6 E2E acceptance. Plan 08-04 (LOCK + WINDOW + DISCLOSURE) ran in parallel in Wave 3; this plan consumes all three of its exports (`assert_can_publish` / `assert_in_window` / `build_status_block` + `assert_synthetic_media_true`) via the 5-gate chain inside `publish()`.

Two production modules + six test files = 8 files, 1274 lines total. Six atomic TDD commits (RED → GREEN × 2 for the production modules, then dedicated commits for ANCHOR B + ANCHOR C, then the E2E test file). 986 Phase 4-7 regression preserved (~8m41s sweep), 148/148 Phase 8 tests green (106 baseline + 42 new).

## What Shipped

### scripts/publisher/production_metadata.py (151 lines)

PUB-04 D-08 satisfied. The 4-field `ProductionMetadata` TypedDict with exactly `script_seed`, `assets_origin`, `pipeline_version`, `checksum` field names matches the Phase 4 `ins-platform-policy` regex enforcement contract. `compute_checksum(mp4_path)` streams in 64KB chunks and returns `"sha256:<64-hex>"` — memory-bounded regardless of file size. `inject_into_description(desc, meta)` appends a single HTML comment block `\n<!-- production_metadata\n<compact JSON>\n-->` at the tail with `ensure_ascii=False` (Korean preservation) and `separators=(",", ":")` (minimal 5000-char description ceiling consumption). Missing-field guard raises `ValueError` prefixed with `"PUB-04 schema violation"` plus sorted-alphabetically list of missing keys (deterministic error text for assertion matching).

### scripts/publisher/youtube_uploader.py (332 lines)

PUB-02 + PUB-05 D-09 satisfied. Three responsibilities:

1. **`build_insert_body(plan)`** translates a Phase 4 publisher upload plan JSON → Data API v3 body. Three Pitfall corrections applied at THIS boundary (not at agent prompt layer):
   - Pitfall 5 — `snippet.defaultAudioLanguage` silently dropped (NOT a writable snippet field per official Data API v3 docs).
   - Pitfall 6 — `status.containsSyntheticMedia` (canonical) set via `ai_disclosure.build_status_block` (hardcoded True per D-05 physical-removal); AGENT.md's `syntheticMedia` custom key is non-canonical and dropped.
   - Pitfall 7 — `funnel.end_screen_subscribe_cta` NOT mapped to any API call (end-screens are YouTube Studio UI only); implemented via pinned comment + description CTA in `publish()` (D-09).

2. **`resumable_upload(insert_request)`** drives `next_chunk()` loop with exponential backoff on 500/502/503/504 (up to `MAX_RETRIES=10`). Error classification via `getattr(exc.resp, 'status', None)` — no `googleapiclient.errors.HttpError` import, keeps module test-isolated. Non-retriable errors propagate unchanged.

3. **`publish(youtube, plan, video_path, thumbnail_path, channel_id)`** 5-gate chain:
   - Gate 1: `_publish_lock.assert_can_publish()` — 48h+jitter lock (PUB-03)
   - Gate 2: `_kst_window.assert_in_window()` — KST weekday 20-23 / weekend 12-15 (PUB-03)
   - Gate 3: `inject_into_description()` + `compute_checksum()` (PUB-04)
   - Gate 4: `build_insert_body()` → `videos.insert` + `resumable_upload()` (PUB-02)
   - Gate 5: `thumbnails.set` → `commentThreads.insert` (pinned CTA, PUB-05) → `record_upload()`

   Module-qualified indirection (`_publish_lock.assert_can_publish` instead of direct `assert_can_publish` import) so tests can monkeypatch the source module and have the patch take effect.

### tests/phase08 (6 new files, 42 new tests)

- `test_production_metadata_schema.py` — 10 tests: PIPELINE_VERSION constant, 4-field TypedDict invariant, streaming checksum on 1-byte fixture + 10MB stress + 3-byte contract check, Korean preservation in injection, `ValueError` on missing fields (1-of-4 and 3-of-4 cases).
- `test_metadata_html_comment.py` — 6 tests: Phase 9 analytics regex roundtrip (DOTALL-matched), end-of-description placement, compact separators (no trailing spaces), stacked-injection non-malformation, original body byte-exact preservation, full-roundtrip JSON parse.
- `test_pinned_comment.py` — 4 tests: mock records pinned comment against videoId key, default `"구독해주세요!"` CTA fallback, commentThreads.insert body shape (channelId + videoId + topLevelComment.snippet.textOriginal), part parameter strictly `"snippet"`.
- `test_endscreen_nonexistent_anchor.py` — ANCHOR B, 5 tests: `_scan()` helper filters comment lines, zero `.captions().insert(` sites, zero `endScreen=` or `"endScreen":`, zero `end_screen_subscribe_cta = True ... .execute(` escalations, AST walk for `youtube.captions().insert(...)` Call node, drop-reason grep (Pitfall 7 / D-09 / end_screen reference).
- `test_no_selenium_anchor.py` — ANCHOR C, 11 tests via parametrize over (selenium, webdriver, playwright): regex import scan, AST `ast.Import`/`ast.ImportFrom` walk, AST-based string-literal-line-set filter so docstring mentions don't false-positive, extended scope to `tests/phase08/` as well.
- `test_uploader_mocked_e2e.py` — 12 tests: `containsSyntheticMedia is True`, `defaultAudioLanguage` dropped, title/description truncation at 100/5000, body has only `{snippet, status}` keys, 1 videos.insert + 1 commentThreads.insert per publish, `publish_lock.json` written after upload, injected description contains the sha256 of `b"0"` (`5feceb66...27fb57e9`), call-order chain `lock → window → insert`, PublishLockViolation propagates on <48h lock, PublishWindowViolation propagates on outside-KST frozen clock (Monday 03:00), AIDisclosureViolation propagates if `build_status_block` is corrupted.

## Deviations from Plan

### 1. [Rule 2 - Missing Critical Functionality] ANCHOR C string-literal detection via AST

- **Found during:** Task 3 test run (ANCHOR C failing on `youtube_uploader.py` module docstring)
- **Issue:** The plan proposed a naive `if '"""' in line or "'''" in line: continue` filter to permit docstring mentions. This only matches lines that CONTAIN triple-quotes — not lines that are INSIDE a triple-quoted block. My `youtube_uploader.py` module docstring has `Selenium / playwright / webdriver are NEVER imported (AF-8 perma-ban);` on a non-delimiter line and the filter did not catch it, causing false failures for `playwright` and `webdriver` parametrize cases.
- **Fix:** Added `_collect_string_literal_lineset(tree)` helper that walks all `ast.Constant` nodes with `str` values and records every line span. The parametrize test then skips lines that belong to ANY string literal (not just lines containing the delimiter). Stricter AND more correct — zero change in executable-code enforcement semantics.
- **Files modified:** tests/phase08/test_no_selenium_anchor.py
- **Commit:** 73c5eb3 (incorporated into the ANCHOR commit, not a separate fix commit)

### 2. [Rule 2 - Missing Critical Functionality] Module-qualified indirection for monkeypatch support

- **Found during:** Task 2 GREEN run (4/4 tests failed with `PublishWindowViolation` because `monkeypatch.setattr(kstw, "assert_in_window", ...)` had no effect)
- **Issue:** When `youtube_uploader.py` did `from scripts.publisher.kst_window import assert_in_window`, the name was bound at import time and subsequent monkeypatch on the SOURCE module (`scripts.publisher.kst_window.assert_in_window`) did not propagate to the already-bound local.
- **Fix:** Changed imports to `from scripts.publisher import kst_window as _kst_window` and call sites to `_kst_window.assert_in_window()`. Same treatment for `publish_lock.assert_can_publish` and `publish_lock.record_upload`. `build_status_block` and `assert_synthetic_media_true` from `ai_disclosure` are NOT affected — those are already exercised via their own dedicated tests and the AI-disclosure corruption test monkeypatches `scripts.publisher.youtube_uploader.build_status_block` directly (at the consumer site), not at source.
- **Files modified:** scripts/publisher/youtube_uploader.py
- **Commit:** 8531475

### 3. [Rule 1 - Bug] Deterministic error message field order

- **Found during:** Task 1 GREEN design review
- **Issue:** Plan prose used `f"PUB-04 schema violation: missing fields {missing}"` where `missing` is a set — Python sets are insertion-ordered in dict but NOT in set-literal printing, making the error message non-deterministic for assertion matching. `test_inject_rejects_missing_fields` asserts `"assets_origin" in str(exc_info.value)` which happens to pass, but flakiness would surface if the test expanded to match full field lists.
- **Fix:** Sorted the missing set before formatting: `f"PUB-04 schema violation: missing fields {sorted(missing)}"`. Deterministic alphabetical ordering.
- **Files modified:** scripts/publisher/production_metadata.py
- **Commit:** 79e38c5

## Authentication Gates

None. Wave 4 is all pure-Python + MockYouTube. Real YouTube auth is exercised only in Wave 5 (smoke test, Plan 08-06) and Wave 6 (E2E acceptance, Plan 08-07) — both gated behind the smoke test checkpoint.

## ANCHOR Evidence

### ANCHOR B (captions.insert / endScreen / end_screen_subscribe_cta)

Grep redundancy check (in addition to 5 anchor tests):

```
$ grep -rE "\.captions\(\)\.insert\(" scripts/publisher/
(no output — 0 hits)

$ grep -rE "\bendScreen\s*=|[\"']endScreen[\"']\s*:" scripts/publisher/
(no output — 0 hits)
```

AST walk via `test_ast_no_captions_insert_call` asserts zero `ast.Call` nodes with `func.attr == "insert"` AND `func.value.func.attr == "captions"` across `scripts/publisher/**/*.py`. Drop-reason documentation present (`Pitfall 7`, `D-09`, and `end_screen_subscribe_cta` all referenced in `youtube_uploader.py` comments).

### ANCHOR C (selenium / webdriver / playwright)

```
$ grep -rE "(import\s+(selenium|webdriver|playwright)|from\s+(selenium|webdriver|playwright))" scripts/publisher/
(no output — 0 hits)

$ grep -rE "(import\s+(selenium|webdriver|playwright)|from\s+(selenium|webdriver|playwright))" tests/phase08/
(no output — 0 hits)
```

AST `ast.Import` / `ast.ImportFrom` walks assert zero forbidden import nodes in both `scripts/publisher/` and `tests/phase08/`. The string-literal-line-set filter ensures docstring mentions (which DO exist, e.g., the ANCHOR C test's own docstring and the `youtube_uploader.py` module docstring) do NOT false-positive.

## Regression

- Phase 8 isolated: `148/148 passed in 0.44s` (106 Wave 3 baseline + 42 new).
- Phase 4-7 sweep: `986/986 passed in 521.08s (0:08:41)`. No breakage.

## What Unblocks Next

- Plan 08-06 Wave 5 SMOKE-GATE — 1-shot real YouTube `privacyStatus=unlisted` upload via `publish()` + `videos.delete` cleanup, gated behind `대표님` approval (D-11 Option A). Consumes `publish()` as the sole real-API path.
- Plan 08-07 Wave 6 E2E + REGRESSION — acceptance wrapper asserting SC3/SC4/SC5/SC6 all PASS with MockYouTube + MockGitHub + real phase04-07 regression sweep.
- Plan 08-08 Wave 7 PHASE GATE — 08-TRACEABILITY.md matrix + 08-VALIDATION.md frontmatter flip + 17-REQ audit.

## Self-Check: PASSED

All 9 files exist on disk (2 production modules + 6 test files + this SUMMARY.md). All 6 commits present in `git log --oneline --all`. Full Phase 8 suite 148/148 green; Phase 4-7 regression 986/986 green (~8m41s sweep). ANCHOR B and ANCHOR C grep redundancy checks both return 0 hits.
