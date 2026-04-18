---
phase: 03-harvest
plan: 02
subsystem: harvest-infrastructure
tags: [path-manifest, ground-truth, harvest, filesystem-scan, secrets-policy]
requires: []
provides: ["path_manifest.json for Plans 03/04/05/06 and diff_verifier"]
affects: [harvest_importer.py, diff_verifier.py]
tech_stack:
  added: []
  patterns: [ast-literal-eval-safe-load, shutil-ignore-patterns, cherry-pick-cascade]
key_files:
  created:
    - .planning/phases/03-harvest/path_manifest.json
    - .planning/phases/03-harvest/03-02-SUMMARY.md
  modified: []
decisions:
  - "theme_bible_raw source = .claude/channel_bibles (NOT .claude/theme-bible per stale HARVEST_SCOPE.md prose)"
  - "remotion_src_raw source = remotion/src with node_modules excluded (758 MB)"
  - "hc_checks_raw = 2-file cherry_pick including companion test file"
  - "api_wrappers_raw = 5-file cherry_pick (scripts/api/ does not exist)"
  - "global_ignore enforces secret file exclusion (client_secret*.json, token_*.json, .env*, *.key, *.pem)"
metrics:
  duration_minutes: 3
  completed: 2026-04-19
  tasks_completed: 2
  commits: 1
requirements_completed: [HARVEST-01, HARVEST-02, HARVEST-03, HARVEST-05, HARVEST-07]
---

# Phase 03 Plan 02: PATH-MANIFEST Summary

Ground-truth source path registry for Wave 1 harvest copy operations — reconciles stale HARVEST_SCOPE.md prose table (3 of 4 paths wrong) with verified filesystem layout of shorts_naberal as of 2026-04-19.

---

## What Was Built

Single artifact: `.planning/phases/03-harvest/path_manifest.json` (69 lines, 2,541 bytes, sha256 `a73a2f3b4db4b4b25aa870ee04bea4b6ee7ecad5cf0cc9fc39d6ef113af8a341`).

Structure:
- Metadata: `manifest_version=1.0`, `generated_at=2026-04-19`, `source_root=C:/Users/PC/Desktop/shorts_naberal`
- `global_ignore`: 7 patterns (5 secret + 2 Python cache)
- 4 raw_dir entries (theme_bible_raw, remotion_src_raw, hc_checks_raw, api_wrappers_raw) — each with `source | cherry_pick | dest | ignore | req_id | note`
- `blacklist_exclusions` cross-reference to 02-HARVEST_SCOPE.md (full_file / path_prefix / pattern)

---

## Ground-Truth Verification (Task 1)

All 4 destination-anchor paths verified via `test -d`/`test -f`/`ls` on 2026-04-19:

| Logical name | Expected (HARVEST_SCOPE.md prose) | Actual (verified) | Status |
|---|---|---|---|
| theme_bible_raw | `.claude/theme-bible/` | `.claude/channel_bibles/` (7 md files) | REMAPPED |
| remotion_src_raw | `src/` | `remotion/src/` (+node_modules present, excluded) | REMAPPED |
| hc_checks_raw | `scripts/*hc_checks*` | `scripts/orchestrator/hc_checks.py` (1129 lines) + `scripts/orchestrator/tests/test_hc_checks.py` | EXACT-LOC |
| api_wrappers_raw | `scripts/api/` | DOES NOT EXIST — 5 scattered files in `scripts/{audio-pipeline,video-pipeline,avatar}/` | SCATTERED |

**Secret hazard confirmed:** 1 `client_secret*.json` and 3 `token_*.json` files exist at source root. `global_ignore` will defensively block them.

**Symlink scan:** No symlinks under `.claude/channel_bibles` or `remotion/src`.

**api_wrappers_raw cherry_pick final list (5 files — no adjustments needed):**
- `scripts/audio-pipeline/elevenlabs_alignment.py` (verified)
- `scripts/audio-pipeline/tts_generate.py` (verified)
- `scripts/video-pipeline/runway_client.py` (verified present — confirmed 2026-04-19; included as Runway fallback per D-3)
- `scripts/video-pipeline/_kling_i2v_batch.py` (verified — Kling primary)
- `scripts/avatar/heygen_client.py` (verified)

---

## Manifest Content (Full Audit Trail)

```json
{
  "manifest_version": "1.0",
  "generated_at": "2026-04-19",
  "source_root": "C:/Users/PC/Desktop/shorts_naberal",
  "global_ignore": [
    "client_secret*.json",
    "token_*.json",
    ".env*",
    "*.key",
    "*.pem",
    "__pycache__",
    "*.pyc"
  ],
  "theme_bible_raw": {
    "source": ".claude/channel_bibles",
    "cherry_pick": null,
    "dest": ".preserved/harvested/theme_bible_raw",
    "ignore": [],
    "req_id": "HARVEST-01",
    "note": "RESEARCH.md §2 remap — HARVEST_SCOPE.md prose table said '.claude/theme-bible/' which does NOT exist. Verified 2026-04-19: 7 md files at this path (documentary, humor, incidents, politics, trend, wildlife, README)."
  },
  "remotion_src_raw": {
    "source": "remotion/src",
    "cherry_pick": null,
    "dest": ".preserved/harvested/remotion_src_raw",
    "ignore": ["node_modules", "__pycache__", "*.pyc", ".venv", ".git"],
    "req_id": "HARVEST-02",
    "note": "RESEARCH.md §2 remap — HARVEST_SCOPE.md said 'src/' but Remotion lives at 'remotion/src/'. Parent's node_modules (758 MB, verified present 2026-04-19) excluded defensively via ignore pattern."
  },
  "hc_checks_raw": {
    "source": null,
    "cherry_pick": [
      "scripts/orchestrator/hc_checks.py",
      "scripts/orchestrator/tests/test_hc_checks.py"
    ],
    "dest": ".preserved/harvested/hc_checks_raw",
    "ignore": [],
    "req_id": "HARVEST-03",
    "note": "Single-file + companion tests per RESEARCH.md open question #3. Verified 2026-04-19: hc_checks.py = 1129 lines; test_hc_checks.py exists. Test file inclusion preserves Phase 5 orchestrator v2 regression baseline."
  },
  "api_wrappers_raw": {
    "source": null,
    "cherry_pick": [
      "scripts/audio-pipeline/elevenlabs_alignment.py",
      "scripts/audio-pipeline/tts_generate.py",
      "scripts/video-pipeline/runway_client.py",
      "scripts/video-pipeline/_kling_i2v_batch.py",
      "scripts/avatar/heygen_client.py"
    ],
    "dest": ".preserved/harvested/api_wrappers_raw",
    "ignore": [],
    "req_id": "HARVEST-05",
    "note": "RESEARCH.md §2 remap — scripts/api/ DOES NOT EXIST (verified 2026-04-19). Wrappers scattered across audio-pipeline/, video-pipeline/, avatar/. All 5 candidates verified present including runway_client.py (Kling primary per D-3, Runway fallback). If additional wrappers discovered in execution, update manifest and re-run diff_verifier."
  },
  "blacklist_exclusions": {
    "full_file": [
      "scripts/orchestrator/orchestrate.py",
      ".claude/skills/create-shorts/SKILL.md"
    ],
    "path_prefix": [
      "longform/",
      ".claude/skills/create-video/"
    ],
    "pattern": [
      "selenium"
    ],
    "source": "02-HARVEST_SCOPE.md § Harvest Blacklist (10 entries, Python dict literal)"
  }
}
```

---

## Cherry_pick Adjustments

**None.** All candidate files listed in the PLAN's behavior section were verified present on filesystem. `runway_client.py` WAS found (plan conservatively anticipated possible absence) — included in final manifest.

---

## Verification Results

**Task 1 (filesystem scan):** All 4 destination anchors exist; `scripts/api/` confirmed absent; 5 of 5 api_wrapper candidates verified; no symlinks in tree sources; secret files hazard (1 client_secret + 3 tokens) confirmed at source root.

**Task 2 (manifest validity):**
- `python -c "import json; json.load(open(...))"` → exits 0 (valid JSON) ✓
- All 4 raw_dir keys present with correct XOR structure (source XOR cherry_pick) ✓
- `theme_bible_raw.source == ".claude/channel_bibles"` ✓
- `remotion_src_raw.source == "remotion/src"` AND `"node_modules"` in ignore ✓
- `hc_checks_raw.source == null` AND cherry_pick non-empty (2 files) ✓
- `api_wrappers_raw.source == null` AND `len(cherry_pick) == 5` (>= 4) ✓
- `global_ignore` contains all 5 secret patterns ✓
- Every referenced source path exists when prepended with `source_root` (9/9 verified via `pathlib.Path.exists()`) ✓
- `blacklist_exclusions` present with 02-HARVEST_SCOPE.md cross-reference ✓

---

## Deviations from Plan

**None — plan executed exactly as written.**

Minor notes:
- Plan anticipated `runway_client.py` might be missing (instructed to "remove ONLY the missing file"). Live verification confirmed it present; no removal needed. 5 wrappers in final manifest vs. plan's minimum 4.
- UTF-8 encoding explicit in Python read calls (Windows cp949 default would fail on em-dash in `note` fields). Not a deviation — plan verify command already specified `encoding='utf-8'`.

No Rule 1/2/3/4 deviations triggered.

---

## Authentication Gates

None encountered.

---

## Known Stubs

None. path_manifest.json has no stub data — every `source`, `cherry_pick` entry, `ignore` pattern, and `req_id` is ground-truth verified.

---

## Confirmation Statement

**All 4 raw_dir sources verified on filesystem 2026-04-19.** Plans 03/04/05/06 can now `json.load()` this file and execute copies without guessing paths. Secret file hazard neutralized (global_ignore will be applied by harvest_importer.py via `shutil.ignore_patterns`).

**Wave 1 status:** UNBLOCKED. Deterministic input available for all 4 parallel copy operations.

---

## Self-Check: PASSED

- `.planning/phases/03-harvest/path_manifest.json`: FOUND
- `.planning/phases/03-harvest/03-02-SUMMARY.md`: FOUND (this file)
- Commit `609c3f8` (`feat(03-02): add path_manifest.json`): FOUND in `git log`
