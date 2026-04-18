---
phase: 3
slug: harvest
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
completed: 2026-04-19
---

# Phase 3 — Validation Strategy

> Per-phase validation contract. Infrastructure phase — validation is grep/file-test/command based rather than unit tests.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python 3.11.9 stdlib + grep + PowerShell (Windows-native) |
| **Config file** | `.planning/phases/03-harvest/path_manifest.json` (Wave 0 produces) |
| **Quick run command** | `python scripts/harvest/verify_harvest.py --quick` |
| **Full suite command** | `python scripts/harvest/verify_harvest.py` |
| **Estimated runtime** | ~10s quick / ~30s full |

---

## Sampling Rate

- **After every task commit:** Run `python scripts/harvest/verify_harvest.py --quick`
- **After every plan wave:** Run `python scripts/harvest/verify_harvest.py`
- **Before `/gsd:verify-work`:** Full suite must return exit 0 (all green)
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | AGENT-06 | file-exists | `test -f .claude/agents/harvest-importer/AGENT.md && wc -l .claude/agents/harvest-importer/AGENT.md \| awk '$1<=500'` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 0 | INFRA | grep | `grep -c "HARVEST_BLACKLIST" scripts/harvest/harvest_importer.py` (≥1) | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 0 | INFRA | file-exists | `test -f .planning/phases/03-harvest/path_manifest.json && python -c "import json;json.load(open('.planning/phases/03-harvest/path_manifest.json'))"` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | HARVEST-01 | diff | `python scripts/harvest/diff_verifier.py theme_bible_raw` (exit 0) | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | HARVEST-02 | diff | `python scripts/harvest/diff_verifier.py remotion_src_raw` (exit 0, node_modules excluded) | ❌ W0 | ⬜ pending |
| 3-04-01 | 04 | 1 | HARVEST-03 | diff | `python scripts/harvest/diff_verifier.py hc_checks_raw` (exit 0) | ❌ W0 | ⬜ pending |
| 3-05-01 | 05 | 1 | HARVEST-05 | diff | `python scripts/harvest/diff_verifier.py api_wrappers_raw` (exit 0) | ❌ W0 | ⬜ pending |
| 3-06-01 | 06 | 2 | HARVEST-04 | grep | `grep -c "source:" .claude/failures/_imported_from_shorts_naberal.md` (≥1) | ❌ W0 | ⬜ pending |
| 3-07-01 | 07 | 3 | HARVEST-08 | grep | `grep -cE "^\\| [ABC]-[0-9]+ " .planning/phases/03-harvest/03-HARVEST_DECISIONS.md` (=39) | ❌ W0 | ⬜ pending |
| 3-08-01 | 07 | 3 | HARVEST-07 | grep | `grep -r "skip_gates=True" .preserved/harvested/ \| wc -l` (=0) | ❌ W0 | ⬜ pending |
| 3-08-02 | 07 | 3 | HARVEST-07 | grep | `grep -r "TODO(next-session)" .preserved/harvested/ \| wc -l` (=0) | ❌ W0 | ⬜ pending |
| 3-09-01 | 08 | 4 | HARVEST-06 | python-write-probe | `python -c "open('.preserved/harvested/theme_bible_raw/.probe','w')"` must raise PermissionError (exit ≠0 expected) | ❌ W0 | ⬜ pending |
| 3-09-02 | 08 | 4 | HARVEST-06 | attrib-flag | `attrib .preserved\\harvested\\theme_bible_raw\\* \| grep -c " R "` (>0) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.claude/agents/harvest-importer/AGENT.md` — AGENT-06 spec, ≤500 lines (HARVEST_BLACKLIST Python dict referenceable)
- [ ] `scripts/harvest/harvest_importer.py` — 5-rule algorithm + parse CONFLICT_MAP + Python stdlib only
- [ ] `scripts/harvest/diff_verifier.py` — `filecmp.dircmp` based per-dir diff tool, takes raw dir name as arg
- [ ] `scripts/harvest/verify_harvest.py` — orchestrates 13 task-level checks above, exit code 0 iff all pass
- [ ] `.planning/phases/03-harvest/path_manifest.json` — filesystem scan of shorts_naberal/, resolves 4 raw dest → actual source mapping

---

## Manual-Only Verifications

*None — all Phase 3 behaviors have automated verification via grep/file-test/python command.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (path_manifest.json + 4 scripts + AGENT.md)
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter (after Wave 0 complete)

**Approval:** pending
