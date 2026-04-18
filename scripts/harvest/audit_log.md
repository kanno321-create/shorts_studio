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

## Wave 2 Task 2 — FAILURES merge (2026-04-19T00:00:00Z)
Target: .claude/failures/_imported_from_shorts_naberal.md (500 lines)
Sources imported (SOURCES locked list, NOT glob):
  - shorts_naberal/.claude/failures/orchestrator.md (487 lines, sha256=978bb9381fee...)
Idempotency: verified — second dry-run correctly SKIPs (marker check before append)
Markers: exactly 1 `<!-- source: ... orchestrator.md -->` + 1 matching `<!-- END source: ... -->`
Header: contains "D-2 저수지 연동" + "Read-only archive" directive
HARVEST-04 satisfied.

## Wave 3 Task 1 — build_decisions (2026-04-18T19:18:04Z)
Output: .planning/phases/03-harvest/03-HARVEST_DECISIONS.md (39 rows: A=13 verbatim + B=16 + C=10)
Rule distribution (B/C 26): rule1=10, rule2=2, rule3=0, rule4=2, rule5=12 (sum=26 OK)
Verdict distribution: 승계=2, 폐기=15, 통합-재작성=20, cleanup=2 (sum=39 OK)
Method: inline Python fallback (.tmp_build_decisions.py — harvest_importer stage 6 requires prior stages in current CLI).
HARVEST-08 satisfied.

## Wave 3 Task 2 — Blacklist grep audit (2026-04-18T19:18:52Z)
- Audit 1 — skip_gates=True matches: 0 (expected 0)
- Audit 2 — TODO(next-session) matches: 0 (expected 0)
- Audit 3a — orchestrate.py paths: 0 (expected 0)
- Audit 3b — SKILL.md path=*create-shorts* matches: 0 (expected 0)
- Audit 3c — create-video/ path matches: 0 (expected 0)
- Audit 3d — longform/ at raw-dir-root (top-level) matches: 0 (expected 0)
- Audit 4 — selenium import matches: 0 (expected 0)
Result: PASS (all 7 checks 0 matches)

**Rule 1 deviation note:** Plan's original find regex `-path "*/longform/*"`
matched 6 legitimate Remotion composition files at
`remotion_src_raw/components/longform/*.tsx` (internal scene-code subtree,
harvested per Plan 03-04 studio@4bc7ece VALIDATION PASS). These are NOT
blacklist violations — the HARVEST_BLACKLIST entry
`{"path": "longform/", "reason": "A-11 ... shorts-only studio"}`
prohibits harvesting from `shorts_naberal/longform/` (Python + agent +
config tree), not arbitrary nested `longform/` subdirectories inside
legitimately harvested source trees. Audit 3d narrows to
`find .preserved/harvested -maxdepth 1 -type d -name "*longform*"`
to match blacklist intent (no top-level harvested raw dir sourced from
`shorts_naberal/longform/`).
HARVEST-07 satisfied.

## Wave 4 Task 1 — Tier 3 lockdown (2026-04-18T19:25:18Z)
attrib command: cmd.exe /c attrib +R /S /D C:\Users\PC\Desktop\naberal_group\studios\shorts\.preserved\harvested\*
return code: 0
probe file: .preserved/harvested/theme_bible_raw/documentary.md (rglob first *.md)
write probe result: PermissionError raised (expected - lockdown active)
Files with R attribute: 55 (theme_bible_raw=7, remotion_src_raw=40, hc_checks_raw=2, api_wrappers_raw=5, + directory nodes)
Independent verify: cmd.exe //c "attrib .preserved\harvested\*.* /s" shows 'A    R' on every file
Result: PASS
