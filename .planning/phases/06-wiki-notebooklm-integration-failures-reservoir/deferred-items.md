# Phase 6 Deferred Items

Items that cannot be completed within Phase 6 and require follow-up action.

## Blocking — User Action Required

### D-04-01: NotebookLM channel-bible notebook URL

- **Status:** BLOCKED — awaiting 대표님 creation in the Google NotebookLM console
- **Current placeholder:** `TBD-url-await-user` (registered in external
  skill `shorts_naberal/.claude/skills/notebooklm/data/library.json` under
  id `naberal-shorts-channel-bible`)
- **Why deferred:** Google NotebookLM notebooks can only be created
  through the Google web console (browser UI, manual upload of sources).
  There is no public API for headless notebook creation as of 2026-04.
  Automating via Playwright was ruled out per CONTEXT §Deferred Ideas line 207.
- **Unblock procedure:**
  1. Open https://notebooklm.google.com
  2. Create new notebook named `Naberal Shorts Channel Bible`
  3. Upload `wiki/continuity_bible/channel_identity.md` (+ optionally
     `wiki/continuity_bible/prefix.json` and `CLAUDE.md`) as sources
  4. Copy the notebook URL (Share -> Copy link)
  5. Provide the URL to Claude
  6. Claude runs:
     ```bash
     python -c "from pathlib import Path; from scripts.notebooklm.library import add_channel_bible_entry; add_channel_bible_entry(Path(r'C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json'), url='<real URL>')"
     ```
  7. The helper updates the `url` + `updated_at` fields; `created_at`,
     `use_count`, `last_used` are preserved (idempotency contract).
- **Impact if not resolved:** Plan 05 Fallback Chain `RAGBackend` Tier 0 will
  return a subprocess error (notebook URL invalid) and fall through to Tier 1
  (grep wiki) and Tier 2 (hardcoded defaults). Phase 7 E2E test will surface
  the degradation. Phase 6 itself does NOT require the real URL — registration
  with the placeholder is sufficient for Plan 05 library lookup to succeed.
- **Resolution phase:** Phase 6 execute (if URL arrives in time) or Phase 7
  integration test (first live query attempt).

### External-repo side-effect: shorts_naberal library.json mutation

- **Touched file:** `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json`
- **Nature of change:** D-8-compliant append of `naberal-shorts-channel-bible`
  entry. Existing `shorts-production-pipeline-bible` and `crime-stories-+-typecast-emotion`
  entries untouched byte-identical (dict equality). `active_notebook_id`
  unchanged.
- **D-7 note:** This is the only file in the external `shorts_naberal` repo
  that Phase 6 is permitted to touch (D-7 reference principle + D-8 channel-bible
  append). No skill code is copied into `studios/shorts`; no `import` of
  `shorts_naberal` is introduced.
- **When to commit:** After 대표님 provides the real URL and `add_channel_bible_entry`
  is rerun against the real library.json (Phase 7 E2E or explicit unblock).
  Until then, the external library.json may show either (a) no change, if the
  helper hasn't been run against it yet, or (b) the placeholder entry, if it
  has. Both states are acceptable for Phase 6 close.

## Measurement-Only Deferrals (D-15 carry-over to Phase 9)

### SKILL.md line-count audit findings

- **Status:** Recorded during Wave 4 (Plans 08-10) if any SKILL exceeds 500 lines.
- **Resolution phase:** Phase 9 docs + deferred-items cleanup.
- **Note:** Phase 6 only measures; does NOT split or trim any SKILL per D-15.

## Authentication Refresh

### NotebookLM browser_state expiry

- **Status:** Potential — external skill `browser_state` last confirmed
  functional 2026-04-07. Expiry cadence per Google is roughly 30-60 days.
- **Symptom:** Plan 05 Fallback Chain Tier 0 returns a subprocess failure
  with stderr mentioning "not authenticated" or "session expired".
- **Unblock procedure:** 대표님 runs
  `python scripts/run.py auth_manager.py setup` inside
  `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/`
  once (browser pops for Google login; state persists).
- **Impact if not resolved:** Tier 0 always fails; Tier 1 grep and Tier 2
  hardcoded defaults still work (graceful degradation; pipeline keeps running).
