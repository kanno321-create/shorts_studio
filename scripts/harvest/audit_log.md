[2026-04-18T19:04:18+00:00] [STAGE_3_ERROR] KeyError: "manifest missing entry 'theme_bible_raw'"
[2026-04-18T19:04:35+00:00] [STAGE_COPY_theme_bible_raw_OK] 7 files copied (Plan 03-03, manifest-driven fallback due to importer stage-gate bug)
[2026-04-18T19:04:50+00:00] [STAGE_3_ERROR] KeyError: "manifest missing entry 'remotion_src_raw'"
[2026-04-18T19:04:51+00:00] [STAGE_3_ERROR] KeyError: "manifest missing entry 'api_wrappers_raw'"
[2026-04-18T19:05:01+00:00] [STAGE_3_OK] api_wrappers_raw mode=cherry_pick files=5
[2026-04-18T19:05:08+00:00] [STAGE_3_OK] remotion_src_raw mode=tree files=40 size_mb=0.161 (manual fallback — stage 3 requires stages 1-2 in current CLI)

## Wave 2 Task 1 — diff_verifier aggregate (2026-04-19T00:00:00Z)
Result: ALL_CLEAN
- theme_bible_raw: 0 mismatches
- remotion_src_raw: 0 mismatches
- hc_checks_raw: 0 mismatches
- api_wrappers_raw: 0 mismatches
Method: inline Python fallback (fnmatch.fnmatchcase applied with per-entry ignore + global_ignore). --all flag NOT yet wired in diff_verifier.py — plan fallback used per RESEARCH.md §4.
