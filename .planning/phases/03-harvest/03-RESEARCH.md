---
status: complete
phase: 03-harvest
date: 2026-04-19
researcher: gsd-phase-researcher
confidence: HIGH
---

# Phase 3: Harvest — Research

**Domain:** File ingestion + path-sensitive drift audit on Windows, with Python-stdlib integrity verification (`filecmp.dircmp`) and OS-level immutable lockdown (`attrib +R /S /D` via `cmd.exe`).

**Primary recommendation:** Build the harvest-importer as a **single Python script** (`scripts/harvest/harvest_importer.py`) using only Python 3.11 stdlib (`shutil`, `filecmp`, `ast`, `subprocess`, `pathlib`, `hashlib`). No external dependencies. It performs 4 copy stages → FAILURES merge → CONFLICT_MAP 39-entry parse → Blacklist grep audit → `cmd.exe //c attrib +R /S /D` lockdown. Pre-locked decisions from `02-HARVEST_SCOPE.md` are the only input; the importer never re-derives A-class judgments.

---

## Executive Summary

Phase 3 is **pure infrastructure** — no design decisions remain open. The 02-HARVEST_SCOPE.md already fixes (a) A-class 13 verdicts (2 승계 / 3 폐기 / 8 통합-재작성), (b) Python-dict-literal blacklist of 10 entries, (c) 4 raw directory mappings, (d) 5-rule algorithm for B/C 26 items, and (e) FAILURES merge protocol. Research here focuses on three orthogonal risks: **(1)** the path mappings in HARVEST_SCOPE.md do NOT match the actual shorts_naberal layout (verified by `ls`), so the planner must re-map or the importer will fail at stage 1; **(2)** `attrib +R /S /D` does not work under Git Bash glob expansion and must be invoked through `cmd.exe //c` with Windows-style path; **(3)** Python's `filecmp.dircmp` needs a recursive traversal wrapper because the default only reports immediate children. Validation architecture uses 9 file-existence/grep/exit-code commands plus one Python write-denial probe — all framework-free.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions (from 02-HARVEST_SCOPE.md, re-surfaced in 03-CONTEXT.md)

**A-class 13 verdicts (sealed in Phase 2):**
- 승계 2건: A-2 (cuts[] schema), A-9 (탐정님 호명 금지 regex)
- 폐기 3건: A-5 (TODO 미연결 4곳), A-6 (skip_gates block), A-11 (longform-scripter)
- 통합-재작성 8건: A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 (concept-reference only; rewritten in Phase 4+)

**B/C 26 algorithm (5-rule, executed in this phase):**
1. Harvest blacklist takes precedence → 폐기
2. Scope boundary (longform / JP / worktree / duo_japan) → 폐기
3. Session-77+ canonical forms → 승계 신형
4. Pure cosmetic cleanup (gitignore / worktree copy / .tmp) → cleanup
5. Default → 통합-재작성

**HARVEST_BLACKLIST (Python dict literal, 10 entries):**
- `orchestrate.py:1239-1291` (A-6 skip_gates block)
- `orchestrate.py:520 / 781 / 1051 / 1129` (A-5 TODO 4곳)
- `longform/` prefix (A-11, scope-out)
- `.claude/skills/create-video/` (A-12)
- `.claude/skills/create-shorts/SKILL.md` (A-3, old dispatch)
- `selenium` regex pattern (AF-8)
- `scripts/orchestrator/orchestrate.py` whole file (D-7, 5166→500-800 rewrite deferred to Phase 5)

**4 raw directory mappings (HARVEST-01 / 02 / 03 / 05):**
| Destination | Intended source (per HARVEST_SCOPE.md) | REQ ID |
|-------------|----------------------------------------|--------|
| `.preserved/harvested/theme_bible_raw/` | `.claude/theme-bible/` | HARVEST-01 |
| `.preserved/harvested/remotion_src_raw/` | `src/` (exclude `node_modules/`) | HARVEST-02 |
| `.preserved/harvested/hc_checks_raw/` | `scripts/*hc_checks*` | HARVEST-03 |
| `.preserved/harvested/api_wrappers_raw/` | `scripts/api/` (exclude `orchestrate.py`) | HARVEST-05 |

**FAILURES merge (HARVEST-04):**
- Source: `.claude/failures/**/FAILURES.md` + root `FAILURES.md`
- Target: `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
- Rule: append-only concat + `<!-- source: ... -->` comments per block

**Tier 3 Lockdown (HARVEST-06):**
- Windows `attrib +R /S /D` recursively after all copies complete
- Python `PermissionError` on write attempt = proof of lockdown

### Claude's Discretion

- Raw-dir copy order (no dependency between the 4)
- Lockdown timing (must be last)
- HARVEST_DECISIONS.md format (must match HARVEST_SCOPE.md §A 5-column table shape)
- Importer implementation language (Python recommended over inline bash — see § Implementation Approaches)

### Deferred Ideas (OUT OF SCOPE)

None for Phase 3. CONTEXT.md explicitly states "Phase 3 is execution-only; new decisions limited to B/C 26 algorithm output."

---

## Phase Requirements

| ID | Description | Research support |
|----|-------------|-------------------|
| **HARVEST-01** | `theme-bible` → `theme_bible_raw/` full copy | § Implementation Approaches — Path remapping (theme-bible ≠ actual path) |
| **HARVEST-02** | Remotion `src/` → `remotion_src_raw/` (exclude `node_modules/`) | § Implementation — `shutil.copytree(ignore=shutil.ignore_patterns('node_modules'))` |
| **HARVEST-03** | `hc_checks` → `hc_checks_raw/` | § Implementation — actual file: `scripts/orchestrator/hc_checks.py` (single 1129-line file) |
| **HARVEST-04** | FAILURES concat → `_imported_from_shorts_naberal.md` | § Implementation — only 1 source file exists (`.claude/failures/orchestrator.md`, 487 lines), no root FAILURES.md |
| **HARVEST-05** | API wrappers → `api_wrappers_raw/` | § Implementation — `scripts/api/` does NOT exist; wrappers live in `scripts/audio-pipeline/`, `scripts/video-pipeline/`, `scripts/avatar/` |
| **HARVEST-06** | `attrib +R /S /D` recursive | § Implementation — must use `cmd.exe //c`, NOT Git Bash glob |
| **HARVEST-07** | Honor 10-entry blacklist | § Implementation — `ast.literal_eval` parses dict safely |
| **HARVEST-08** | HARVEST_DECISIONS.md with 39 entries | § DAG — T5 parses CONFLICT_MAP.md via `### A-N / B-N / C-N` regex (confirmed: exactly 13+16+10=39 entries in source) |
| **AGENT-06** | harvest-importer agent | § Implementation — single Python script design |

---

## Implementation Approaches

### §1. harvest-importer: Python Script (NOT inline bash)

**Recommendation: single Python file — `studios/shorts/scripts/harvest/harvest_importer.py`.**

Reasons:
1. Python stdlib covers every need: `shutil.copytree` (copy), `filecmp.dircmp` (diff verification), `ast.literal_eval` (blacklist parse — SAFE, no `eval`), `subprocess.run` (cmd.exe attrib invocation), `hashlib.sha256` (file-level integrity), `re` (grep audit).
2. The importer must parse a Python dict literal from `02-HARVEST_SCOPE.md`. Doing this in bash is error-prone; Python does it in 1 line.
3. Error reporting must include structured audit logs (which entry skipped, which blacklist rule matched, which file had diff mismatch). Python data structures beat bash `echo >> log`.
4. The "harvest-importer" is both an **agent (AGENT-06)** and a **script** — the SKILL.md / AGENT.md file is the spec, the `.py` file is the executor.

**Design:**
```
scripts/harvest/
├── harvest_importer.py     # Main entry — orchestrates 6 stages
├── blacklist_parser.py     # ast.literal_eval of HARVEST_BLACKLIST dict
├── decision_builder.py     # 5-rule algorithm for B/C 26
├── conflict_parser.py      # CONFLICT_MAP.md → 39-entry list (regex on `### X-N`)
├── diff_verifier.py        # filecmp.dircmp recursive wrapper (source vs dest)
├── lockdown.py             # cmd.exe //c attrib +R /S /D wrapper
└── audit_log.md            # append-only log emitted by each stage
```

**Invocation** (from `studios/shorts/` root):
```bash
python scripts/harvest/harvest_importer.py \
  --source C:/Users/PC/Desktop/shorts_naberal \
  --scope .planning/phases/02-domain-definition/02-HARVEST_SCOPE.md \
  --conflict-map C:/Users/PC/Desktop/shorts_naberal/.planning/codebase/CONFLICT_MAP.md \
  --dest .preserved/harvested \
  --failures-out .claude/failures/_imported_from_shorts_naberal.md \
  --decisions-out .planning/phases/03-harvest/HARVEST_DECISIONS.md \
  --lockdown \
  --audit-log scripts/harvest/audit_log.md
```

**AGENT.md** (for AGENT-06) should be ≤ 200 lines — pure spec:
- Inputs (scope md, conflict map, source path)
- Outputs (4 raw dirs, FAILURES merge, HARVEST_DECISIONS.md, audit log)
- Invariants (never writes to `shorts_naberal/`, lockdown must be last, blacklist is read-only)
- One-shot only — agent is deprecated after Phase 3 completes (not referenced in Phase 4+)

### §2. Path Remapping — CRITICAL BLOCKER

**Finding (HIGH confidence, verified by `ls` on 2026-04-19):**

The paths in 02-HARVEST_SCOPE.md do NOT match the actual `shorts_naberal` filesystem. The planner MUST include a remap step or the importer will silently skip all stages with "source not found."

| Intended source (HARVEST_SCOPE.md) | Actual source | Status |
|------------------------------------|---------------|--------|
| `.claude/theme-bible/` | `.claude/channel_bibles/` | RENAMED — 7 md files inside |
| `src/` (Remotion) | `remotion/src/` | NESTED — also need to ignore `remotion/node_modules` (758 MB) |
| `scripts/*hc_checks*` | `scripts/orchestrator/hc_checks.py` (single file) + `scripts/orchestrator/tests/test_hc_checks.py` | EXACT-LOC — not a glob folder |
| `scripts/api/` | DOES NOT EXIST — API wrappers scattered across:<br>• `scripts/audio-pipeline/elevenlabs_alignment.py`<br>• `scripts/audio-pipeline/tts_generate.py`<br>• `scripts/video-pipeline/runway_client.py`<br>• `scripts/video-pipeline/_kling_i2v_batch.py`<br>• `scripts/avatar/heygen_client.py` | SCATTERED |
| `FAILURES.md` (root) | DOES NOT EXIST at `shorts_naberal/FAILURES.md` | Only `.claude/failures/orchestrator.md` (487 lines) exists |

**Recommended action for planner:** First wave (W1) creates a **path_manifest.json** that lists `{logical_name: actual_source_path}` based on ground-truth filesystem scan. The importer reads this manifest, NOT the prose table in HARVEST_SCOPE.md. Example manifest entry:

```json
{
  "theme_bible_raw": {
    "source": "C:/Users/PC/Desktop/shorts_naberal/.claude/channel_bibles",
    "dest": ".preserved/harvested/theme_bible_raw",
    "ignore": [],
    "req_id": "HARVEST-01"
  },
  "api_wrappers_raw": {
    "source": null,
    "dest": ".preserved/harvested/api_wrappers_raw",
    "cherry_pick": [
      "scripts/audio-pipeline/elevenlabs_alignment.py",
      "scripts/audio-pipeline/tts_generate.py",
      "scripts/video-pipeline/runway_client.py",
      "scripts/video-pipeline/_kling_i2v_batch.py",
      "scripts/avatar/heygen_client.py"
    ],
    "req_id": "HARVEST-05"
  }
}
```

This is a **departure from the prose mapping** — but HARVEST_SCOPE.md explicitly says planner has discretion over "4 raw 디렉토리 병렬 복사 순서" and the pre-locked decision is the destination structure and the blacklist, NOT the literal source paths.

### §3. Copy Strategy — `shutil.copytree` with ignore patterns

**Stdlib function** (confirmed Python 3.11.9 available):
```python
import shutil
shutil.copytree(
    src=r"C:/Users/PC/Desktop/shorts_naberal/remotion/src",
    dst=r".preserved/harvested/remotion_src_raw",
    ignore=shutil.ignore_patterns("node_modules", "__pycache__", "*.pyc", ".venv"),
    symlinks=False,     # dereference — source is regular file tree (verified)
    dirs_exist_ok=False, # fail if dest exists — forces clean state
)
```

**For scattered API wrappers** (no single source dir), use `shutil.copy2` per file to preserve mtime:
```python
for relative_path in manifest["api_wrappers_raw"]["cherry_pick"]:
    src = source_root / relative_path
    dst = dest_root / "api_wrappers_raw" / Path(relative_path).name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
```

**Ignore pattern list** (lean — most excluded content not present in harvest sources):
- `node_modules` — 758 MB, remotion only
- `__pycache__`, `*.pyc` — Python bytecode
- `.venv` — test dirs sometimes include virtualenvs
- `.git` — defensive (no .git expected in subtrees but be safe)

### §4. Diff Verification — `filecmp.dircmp` RECURSIVE

**Trap:** `filecmp.dircmp(a, b).left_only` only reports immediate children. You must recurse through `common_dirs`.

**Stdlib recipe** (verified correct for Python 3.11):
```python
import filecmp
from pathlib import Path

def deep_diff(src: Path, dst: Path) -> list[str]:
    """Return list of mismatch paths. Empty list == perfect copy."""
    mismatches = []
    def walk(a, b, prefix=""):
        cmp = filecmp.dircmp(a, b)
        for name in cmp.left_only:
            mismatches.append(f"MISSING_IN_DEST: {prefix}/{name}")
        for name in cmp.right_only:
            mismatches.append(f"EXTRA_IN_DEST: {prefix}/{name}")
        for name in cmp.diff_files:
            mismatches.append(f"CONTENT_DIFF: {prefix}/{name}")
        for name in cmp.funny_files:
            mismatches.append(f"COMPARE_ERROR: {prefix}/{name}")
        for name in cmp.common_dirs:
            walk(Path(a) / name, Path(b) / name, f"{prefix}/{name}")
    walk(src, dst)
    return mismatches
```

**Note:** `dircmp.diff_files` uses shallow comparison (`os.stat` only) by default. For cryptographic guarantee add `filecmp.cmp(shallow=False)` per file — but that doubles runtime. Recommendation: shallow + hash-check random sample of 10% of files post-copy.

**Validation command (Bash-level, no Python):** `diff -r` is NOT available on Windows Git Bash by default for this purpose. Use `fc /b` via `cmd.exe` OR defer entirely to the Python wrapper above. PowerShell `Compare-Object` is another option:

```powershell
Compare-Object (Get-ChildItem -Recurse $src | % FullName) (Get-ChildItem -Recurse $dst | % FullName)
```

### §5. Tier 3 Lockdown — `cmd.exe //c attrib +R /S /D`

**Live test finding (HIGH confidence, verified 2026-04-19):**

Git Bash CANNOT invoke `attrib +R /S /D "path/*"` directly — the shell's glob expansion mangles the Windows-native syntax. Test output:

```
$ attrib +R /S /D "attrib_dir_test\\*"
매개 변수 형식이 틀립니다  -    (Korean Windows: "parameter format invalid")
→ WRITE_ALLOWED (unexpected) — lockdown did NOT apply
```

**Working invocation** (verified writes are denied after):
```bash
cmd.exe //c "attrib +R /S /D C:\\path\\to\\.preserved\\harvested\\*"
```

Python wrapper:
```python
import subprocess
from pathlib import Path

def lockdown(target: Path):
    # Normalize to Windows path, ensure trailing \* for recursion
    win_path = str(target.resolve()).replace("/", "\\")
    cmd = ["cmd.exe", "/c", f"attrib +R /S /D {win_path}\\*"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"attrib failed: {result.stderr}")
```

**Verification that lockdown actually applied:**
```python
from pathlib import Path
probe = Path(".preserved/harvested/theme_bible_raw/README.md")
try:
    probe.write_text("tamper")
    raise AssertionError("LOCKDOWN FAILED — write succeeded")
except PermissionError:
    pass  # expected
```

**Unlock for emergency** (document in AGENT.md but forbid normal use):
```bash
cmd.exe //c "attrib -R /S /D C:\\path\\to\\.preserved\\harvested\\*"
```

**Scope of `attrib +R`:** Sets the read-only file attribute. Does NOT prevent `del` by admin, does NOT survive clean re-clone. Sufficient for Phase 3 goal (structural drift prevention during normal agent workflow).

### §6. FAILURES Merge — Append-only Concat with Source Comments

**Source reality** (verified): only 1 file exists — `.claude/failures/orchestrator.md` (487 lines). HARVEST_SCOPE.md's `**/FAILURES.md` glob will match zero additional files. The "agent-per-directory" pattern (`paperclip/agents/<agent>/FAILURES.md`) referenced inside `orchestrator.md` itself does NOT actually exist in the source tree — it was a proposed schema that never got populated.

**Merge template:**
```markdown
# FAILURES — Imported from shorts_naberal (2026-04-19 Phase 3 Harvest)

> Read-only archive. Originals live in shorts_naberal/ (DO NOT modify).
> D-2 저수지 연동: 첫 1~2개월 SKILL patch 금지 기간 동안 이 파일은 참조 전용.

<!-- source: shorts_naberal/.claude/failures/orchestrator.md -->
<!-- imported: 2026-04-19 by harvest_importer.py v1.0 -->
<!-- sha256: <digest-of-source> -->

[... full content of orchestrator.md appended verbatim ...]

<!-- END source: shorts_naberal/.claude/failures/orchestrator.md -->
```

If future FAILURES files are discovered, each gets its own `<!-- source: ... -->` / `<!-- END source: ... -->` block.

### §7. CONFLICT_MAP Parsing — Regex Against Heading Format

**Source structure verified:** CONFLICT_MAP.md uses `### A-N. <summary>`, `### B-N. <summary>`, `### C-N. <summary>` as section headers. Exactly 13 A, 16 B, 10 C = 39. No missing IDs (grep-counted).

**Parse recipe:**
```python
import re
from pathlib import Path

ENTRY_RE = re.compile(r"^### ([ABC])-(\d+)\.\s+(.*)$", re.MULTILINE)

def parse_conflict_map(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    entries = []
    for m in ENTRY_RE.finditer(text):
        entries.append({
            "class": m.group(1),
            "num": int(m.group(2)),
            "summary": m.group(3).strip(),
            "id": f"{m.group(1)}-{m.group(2)}",
        })
    return entries

# Invariant check
assert len([e for e in entries if e["class"] == "A"]) == 13
assert len([e for e in entries if e["class"] == "B"]) == 16
assert len([e for e in entries if e["class"] == "C"]) == 10
```

### §8. 5-rule Algorithm for B/C 26 Judgments

Each entry in CONFLICT_MAP.md includes a "신형 위치" row in its content table. The importer extracts this row plus the "구형 위치" row for heuristic scoring:

```python
def judge(entry: dict, body: str, blacklist: list) -> str:
    # Rule 1: blacklist precedence
    for bl in blacklist:
        if bl.get("file") and bl["file"] in body:
            return "폐기"
        if bl.get("path") and bl["path"] in body:
            return "폐기"
    # Rule 2: scope boundary
    if any(token in body for token in ["longform/", "incidents_jp", "duo_japan", "worktree"]):
        return "폐기"
    # Rule 3: Session 77+ canonical
    if re.search(r"세션 (7[7-9]|8\d|9\d)", body) or "17일 uncommitted" in body:
        return "승계 신형"
    # Rule 4: cosmetic cleanup
    if entry["class"] == "C" and any(tok in body for tok in ["gitignore", "worktree_copy", ".tmp_", "_backup_"]):
        return "cleanup"
    # Rule 5: default
    return "통합-재작성"
```

Output is appended to HARVEST_DECISIONS.md in the same 5-column format as HARVEST_SCOPE.md §A table (id / summary / verdict / rationale / execution).

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json`. All 5 Phase 3 success criteria MUST have automated verification.

### Test Framework

| Property | Value |
|----------|-------|
| **Framework** | Python 3.11 stdlib (`unittest` optional) + Bash/PowerShell + `cmd.exe` for Windows attrib |
| **Config file** | None (command-based, like Phase 2) |
| **Quick run command** | `python studios/shorts/scripts/harvest/verify_harvest.py --quick` (runs all 10 checks in one shot; ~5s) |
| **Full suite command** | `python studios/shorts/scripts/harvest/verify_harvest.py --full` (adds deep diff + sha256 on 10% sample; ~30s) |
| **Estimated quick runtime** | < 10 s |

No new framework installation required — same stance as Phase 2.

### Phase Requirements → Test Map

| REQ ID | Behavior | Test type | Automated command | Expected output | File exists? |
|--------|----------|-----------|--------------------|----------------|-------------|
| HARVEST-01 | `theme_bible_raw/` full copy | smoke | `test -d studios/shorts/.preserved/harvested/theme_bible_raw && ls studios/shorts/.preserved/harvested/theme_bible_raw/*.md \| wc -l` | ≥ 7 (matches source `.claude/channel_bibles/*.md` count) | ❌ Wave 0 |
| HARVEST-02 | Remotion `src/` copy, `node_modules` excluded | smoke | `test -d studios/shorts/.preserved/harvested/remotion_src_raw/components && test ! -d studios/shorts/.preserved/harvested/remotion_src_raw/../node_modules` | exit 0 | ❌ Wave 0 |
| HARVEST-03 | `hc_checks` file present | smoke | `test -f studios/shorts/.preserved/harvested/hc_checks_raw/hc_checks.py && wc -l studios/shorts/.preserved/harvested/hc_checks_raw/hc_checks.py \| awk '{print $1}'` | 1129 (matches source line count) | ❌ Wave 0 |
| HARVEST-04 | FAILURES merge file exists + source comment | unit | `grep -c "<!-- source: shorts_naberal/.claude/failures/orchestrator.md -->" studios/shorts/.claude/failures/_imported_from_shorts_naberal.md` | ≥ 1 | ❌ Wave 0 |
| HARVEST-05 | API wrappers (5 files cherry-picked) | smoke | `ls studios/shorts/.preserved/harvested/api_wrappers_raw/*.py \| wc -l` | ≥ 5 (elevenlabs_alignment, tts_generate, runway_client, _kling_i2v_batch, heygen_client) | ❌ Wave 0 |
| HARVEST-06 | `attrib +R` applied — write denial | integration | `python -c "from pathlib import Path; p=Path('studios/shorts/.preserved/harvested/theme_bible_raw/README.md'); import sys; \\ntry: p.write_text('tamper'); print('FAIL'); sys.exit(1)\\nexcept PermissionError: print('OK'); sys.exit(0)"` | `OK` + exit 0 | ❌ Wave 0 |
| HARVEST-07 | Blacklist grep audit | unit | `grep -rE "skip_gates\\s*=\\s*True\|TODO\\(next-session\\)" studios/shorts/.preserved/harvested/ \| wc -l` | 0 | ❌ Wave 0 |
| HARVEST-07 | Blacklist file-path audit | unit | `find studios/shorts/.preserved/harvested -name "orchestrate.py" -o -name "SKILL.md" -path "*create-shorts*" -o -path "*longform*" \| wc -l` | 0 | ❌ Wave 0 |
| HARVEST-08 | HARVEST_DECISIONS.md has 39 entries | unit | `grep -cE "^\| (A\|B\|C)-[0-9]+ " studios/shorts/.planning/phases/03-harvest/HARVEST_DECISIONS.md` | 39 | ❌ Wave 0 |
| AGENT-06 | harvest-importer AGENT.md ≤ 500 lines, description ≤ 1024 chars | unit | `wc -l studios/shorts/.claude/agents/harvest-importer/AGENT.md \| awk '{print $1}'` and `python -c "import re,sys; d=open('studios/shorts/.claude/agents/harvest-importer/AGENT.md').read(); m=re.search(r'^description:\\s*(.+)$', d, re.M); print(len(m.group(1)) if m else 0)"` | ≤ 500 and ≤ 1024 | ❌ Wave 0 |
| Bonus: diff integrity | 4 raw dirs match source | integration | `python studios/shorts/scripts/harvest/diff_verifier.py --all` | `ALL_CLEAN` + exit 0 | ❌ Wave 0 |

### Sampling Rate (Nyquist)

- **Per task commit (wave-local):** quick smoke for that wave only — 1-2 commands, ~1s each
- **Per wave merge:** all prior-wave commands + current-wave = cumulative ≤ 10s
- **Phase gate (before `/gsd:verify-work 3`):** full 11-test suite green + deep-diff integration
- **Max feedback latency:** < 10 s for quick, < 30 s for full

### Wave 0 Gaps

Every verification above requires a test scaffold that does NOT yet exist. Wave 0 (before any harvest execution) MUST create:

- [ ] `studios/shorts/scripts/harvest/verify_harvest.py` — single-entrypoint verifier (11 checks, argparse `--quick` / `--full`)
- [ ] `studios/shorts/scripts/harvest/diff_verifier.py` — `filecmp.dircmp` recursive wrapper
- [ ] `studios/shorts/scripts/harvest/path_manifest.json` — logical-name → actual source path (§2 remap)
- [ ] `studios/shorts/scripts/harvest/__init__.py` — makes module importable for sub-modules
- [ ] `studios/shorts/.claude/agents/harvest-importer/AGENT.md` — agent spec (AGENT-06, ≤ 500 lines)

No pytest framework is needed — all checks are file-existence / grep / exit-code / Python one-liners. Same framework-free stance as Phase 2. `unittest` MAY be used internally by `verify_harvest.py` but is not required by the harness.

### Manual-Only Verifications

| Behavior | REQ | Why manual | Instruction |
|----------|-----|-----------|-------------|
| B/C 26 judgment reasonableness | HARVEST-08 | 5-rule algorithm is heuristic; rationale quality needs human scan | 대표님 reads 26 judgment rows in HARVEST_DECISIONS.md, flags any clearly wrong verdict |
| FAILURES merge semantic intactness | HARVEST-04 | Diff can be byte-clean but insertion of comments could break markdown rendering | 대표님 opens `_imported_from_shorts_naberal.md` in editor, verifies structure |

---

## DAG — Task Dependencies

```
                  ┌──────────────────────────┐
                  │ W0: Scaffold & Manifest  │
                  │ (verify_harvest.py,      │
                  │  diff_verifier.py,       │
                  │  path_manifest.json,     │
                  │  AGENT.md)               │
                  └──────────┬───────────────┘
                             │
            ┌────────────────┼────────────────┬────────────────┐
            ▼                ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ W1-T1:       │ │ W1-T2:       │ │ W1-T3:       │ │ W1-T4:       │
    │ Copy         │ │ Copy         │ │ Copy         │ │ Copy         │
    │ theme_bible  │ │ remotion_src │ │ hc_checks    │ │ api_wrappers │
    │ HARVEST-01   │ │ HARVEST-02   │ │ HARVEST-03   │ │ HARVEST-05   │
    │ (parallel)   │ │ (parallel)   │ │ (parallel)   │ │ (parallel)   │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │                │
           └────────────────┴────────┬───────┴────────────────┘
                                     ▼
                          ┌──────────────────────┐
                          │ W2-T1: Diff verify   │
                          │ (filecmp.dircmp)     │
                          │ depends on W1-T1..4  │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ W2-T2: FAILURES      │
                          │ merge HARVEST-04     │
                          │ (sequential, small)  │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ W3-T1: Parse         │
                          │ CONFLICT_MAP (39)    │
                          │ + run 5-rule algo    │
                          │ → HARVEST_DECISIONS  │
                          │ HARVEST-08           │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ W3-T2: Blacklist     │
                          │ grep audit           │
                          │ HARVEST-07           │
                          │ (MUST be before W4)  │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ W4-T1: Tier 3        │
                          │ lockdown (attrib +R) │
                          │ HARVEST-06           │
                          │ (MUST be last)       │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ W4-T2: verify_harvest│
                          │ --full (11 checks)   │
                          │ Phase gate           │
                          └──────────────────────┘
```

**Parallelization opportunities:**
- W1-T1..T4 are independent (different source paths, different dest subdirs). 4-way parallel.
- W2-T2 (FAILURES merge) can run in parallel with W2-T1 (diff verify) — different files.
- W3-T1 and W3-T2 can run in parallel — decisions writing is independent of blacklist grep.

**Strict sequential edges:**
- Lockdown (W4-T1) MUST come last — locking before decisions/audit means the audit log file itself can't be written.
- Diff verify (W2-T1) MUST come after all copies (W1-T*) — can't verify a partial copy.

**AGENT-06 implementation lives in W0.** The agent spec MD + Python script are scaffolded before W1 starts so the importer is callable.

---

## Edge Cases & Pitfalls

### E1. Git Bash attrib glob failure

**Pitfall:** Running `attrib +R /S /D "path\\*"` directly in Git Bash fails with "매개 변수 형식이 틀립니다" (parameter format invalid). Writes still succeed after the (failed) lockdown — **silent security hole**.

**Detection:** Live-tested 2026-04-19; write succeeded after bogus attrib command.

**Avoidance:** Always invoke via `subprocess.run(["cmd.exe", "/c", "attrib +R /S /D <win-path>\\*"])`. Verify by writing a probe file, attempting modification, and catching `PermissionError`.

### E2. `shutil.copytree` fails on pre-existing destination

**Pitfall:** `dirs_exist_ok=False` (default) raises `FileExistsError` if dest dir exists. If a previous Phase 3 attempt left partial contents, re-run crashes.

**Avoidance:** First task of W1 = `shutil.rmtree(dest / subdir, ignore_errors=True)` before copy. This is safe because lockdown hasn't been applied yet (W4). If lockdown WAS applied (re-run after full success), the `rmtree` will fail — surface that as a distinct error: "phase already complete; un-lock first".

### E3. `filecmp.dircmp` shallow default

**Pitfall:** Default comparison uses `os.stat` only (size + mtime). A corrupted copy with matching size could pass. 

**Avoidance:** For HARVEST-08 smoke, shallow is fine (mtime preserved by `copy2`). For `--full` verify, add sha256 spot-check on 10% random sample.

### E4. CONFLICT_MAP.md regex fragility

**Pitfall:** Heading format `### A-5. TODO(next-session)` — the parenthesis in the summary could interact with regex special chars. Verified safe for current content (2026-04-18 CONFLICT_MAP.md has no `)` immediately after `\d+\.` pattern).

**Avoidance:** Use raw string `r"^### ([ABC])-(\d+)\."` — dot is the only metachar and it's literal here.

### E5. `ast.literal_eval` safety vs. `eval`

**Pitfall:** The HARVEST_BLACKLIST is a Python dict literal inside a markdown code block. Using `eval()` on untrusted markdown is a security hole (even though this markdown is authored by us, agent discipline = zero-trust).

**Avoidance:** Use `ast.literal_eval(code_block_text)` — only accepts literals (dict / list / str / int / bool / None). Silently refuses function calls, imports, or comprehensions.

```python
import ast, re
scope_md = Path("02-HARVEST_SCOPE.md").read_text(encoding="utf-8")
# Match the python code block starting with HARVEST_BLACKLIST = [
m = re.search(r"HARVEST_BLACKLIST\s*=\s*(\[.*?\n\])", scope_md, re.DOTALL)
blacklist = ast.literal_eval(m.group(1))
```

### E6. Symbolic links / NTFS junctions

**Pitfall:** `shutil.copytree(symlinks=False)` dereferences symlinks — copies target content. If source contains a junction pointing outside `shorts_naberal/`, we could accidentally harvest external paths.

**Check:** Source tree scan:
```bash
find C:/Users/PC/Desktop/shorts_naberal -type l 2>&1 | head
```

**If any found:** switch to `symlinks=True` and document the junction in `path_manifest.json`. For now (verified 2026-04-19), no junctions observed.

### E7. FAILURES merge — single source, not `**/FAILURES.md`

**Pitfall:** HARVEST_SCOPE.md says "`.claude/failures/**/FAILURES.md` + root `FAILURES.md`". Reality: only `.claude/failures/orchestrator.md` (487 lines, file name NOT `FAILURES.md`).

**Avoidance:** The glob should be `.claude/failures/*.md` (excluding README.md) rather than `**/FAILURES.md`. Document this in AGENT.md.

### E8. Windows path length limits

**Pitfall:** Windows default MAX_PATH is 260 chars. Concatenating `C:/Users/PC/Desktop/naberal_group/studios/shorts/.preserved/harvested/remotion_src_raw/components/...` can exceed.

**Detection:** Remotion src is deep but deep-nested node_modules was already excluded.

**Avoidance:** If any `shutil.copy2` raises `FileNotFoundError` with "The system cannot find the path specified" at deep levels, enable long-path support via `\\\\?\\` prefix or move to Python `pathlib` + Win10 long-path setting. Not expected for this phase.

### E9. Read-only `.gitkeep` after lockdown

**Pitfall:** `.preserved/harvested/.gitkeep` from Phase 2 scaffold will receive `attrib +R` too. Subsequent `git rm` or file deletion requires `attrib -R` first.

**Avoidance:** Document lockdown UNDO procedure in AGENT.md (emergency only). For normal development, treat `.preserved/harvested/` as immutable.

### E10. 39-entry invariant assertion failure

**Pitfall:** If future CONFLICT_MAP.md updates introduce or remove entries, the `assert len(...) == 39` invariant breaks. This is DESIRED behavior (we want to know) but must fail loudly.

**Avoidance:** The invariant lives in `harvest_importer.py` and emits a structured error: `CONFLICT_MAP_COUNT_MISMATCH: expected 13/16/10, got X/Y/Z. Refusing to proceed.` This routes to audit_log.md and exits non-zero.

---

## Runtime State Inventory

> Phase 3 is a copy / lockdown phase, not a rename / refactor. No string replacement across runtime state. But verified systematically:

| Category | Items found | Action |
|----------|-------------|--------|
| Stored data | None — no databases, no memory stores touched. `.preserved/harvested/` is new content, not mutation of existing records. | None |
| Live service config | None — Phase 3 does not touch any live service (no n8n, no Datadog, no cron). | None |
| OS-registered state | None — no Windows Task Scheduler entries, no launchd plists. Tier 3 lockdown uses filesystem attributes only (attrib +R), not OS services. | None |
| Secrets / env vars | None — harvest-importer reads local markdown/python files only, no credentials. `shorts_naberal/client_secret.json` and `token*.json` exist at source root — **explicitly exclude these from copy** (add to ignore patterns). | Ignore pattern: `client_secret*.json`, `token_*.json` |
| Build artifacts | None — no compile step. Python bytecode caches (`__pycache__`, `*.pyc`) already in ignore pattern. Remotion `node_modules/` explicitly excluded. | None (patterns already cover) |

**Canonical question answered:** After every file is copied to `.preserved/harvested/`, no runtime system has cached or registered state related to this harvest. The only post-copy mutation is the `attrib +R` filesystem attribute, which is self-contained.

**Additional secret-safety rule for planner:** Add `client_secret*.json`, `token_*.json`, `.env*` to the ignore pattern set in `path_manifest.json`. Source root `shorts_naberal/client_secret.json` and token files WOULD be copied by naive tree-walking — these must NOT land in `.preserved/harvested/`.

---

## Environment Availability

| Dependency | Required by | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.11+ | harvest_importer.py, verify_harvest.py | ✓ | 3.11.9 | — |
| Python stdlib (shutil, filecmp, ast, subprocess, pathlib, hashlib, re) | all harvest logic | ✓ | stdlib | — |
| `cmd.exe` (Windows native) | attrib +R /S /D | ✓ | Windows 11 26200 | — |
| Git Bash | developer shell | ✓ | — | PowerShell / cmd.exe directly |
| `shorts_naberal/` source tree | copy source | ✓ | at `C:/Users/PC/Desktop/shorts_naberal` | — (blocking if missing) |
| CONFLICT_MAP.md source | 39-entry parse | ✓ | at `shorts_naberal/.planning/codebase/CONFLICT_MAP.md`, 38,608 bytes | — (blocking if missing) |

**No missing dependencies.** No external installs needed. Everything runs from stdlib + Windows built-ins.

---

## Project Constraints (from CLAUDE.md)

Extracted actionable directives from `studios/shorts/CLAUDE.md`:

1. **`shorts_naberal` 원본 수정 금지** (rule #6) — Harvest is READ-ONLY copy to `.preserved/harvested/`. harvest-importer MUST NOT open any file in `shorts_naberal/` with write intent.
2. **`skip_gates=True` 금지** (rule #1) — Blacklist has this covered (A-6). No new code should introduce this pattern.
3. **`TODO(next-session)` 금지** (rule #2) — Blacklist covers (A-5). New harvest_importer.py MUST be complete (no TODO markers).
4. **try-except 침묵 폴백 금지** (rule #3) — All exceptions in harvest_importer.py must either re-raise with context or emit structured error to audit_log and exit non-zero. No silent `except: pass`.
5. **Selenium 업로드 금지** (rule #5) — Not relevant to Phase 3, but blacklist regex includes `selenium` for defensive measure.
6. **파이프라인 GATE 규율** — Phase 3 is pre-GATE infrastructure, but the harvest-importer itself should emit structured audit events (one per stage completion) so later GATE-2 auditor can verify retroactively.

**Secondjob_naberal CLAUDE.md (parent project) directives that apply:**
- 품질 최우선 원칙 (memory `feedback_quality_first`) — prefer correctness over speed. `--quick` verify mode is acceptable post-commit, but `/gsd:verify-work 3` runs `--full` (diff + sha256 spot check).
- 백그라운드 발행 금지 (memory `feedback_no_background_publish`) — irrelevant here but general rule: harvest_importer.py runs foreground, not backgrounded.

---

## Common Pitfalls

### P1. Planner trusts HARVEST_SCOPE.md path mapping verbatim

**What goes wrong:** Importer attempts `shutil.copytree(".claude/theme-bible/")` → `FileNotFoundError`. 3 of 4 source paths are wrong.
**Root cause:** HARVEST_SCOPE.md was written before filesystem scan.
**Avoidance:** W0 MUST generate `path_manifest.json` from live `ls`-style scan. Never hardcode paths from prose documents.
**Warning sign:** Any task description that says "copy from `.claude/theme-bible/`" without `"per path_manifest.json"` caveat.

### P2. Lockdown applied before verification

**What goes wrong:** attrib +R runs first, then diff verify tries to open files — works for read, but any subsequent corruption fix requires unlock → attrib dance.
**Root cause:** Intuitive ordering (lock ASAP) vs. correct ordering (verify THEN lock).
**Avoidance:** DAG enforces W4 lockdown comes last. Plan tasks in strict wave order.
**Warning sign:** Task with `attrib +R` not in the final wave.

### P3. Overlooking `shorts_naberal/client_secret.json` and token files

**What goes wrong:** Naive copy includes OAuth tokens and client secrets into `.preserved/harvested/` → committed to git → credential exposure.
**Root cause:** HARVEST_SCOPE.md lists "what to copy" but not "what to NEVER copy."
**Avoidance:** `path_manifest.json` includes `global_ignore` list: `client_secret*.json`, `token_*.json`, `.env*`, `*.key`, `*.pem`.
**Warning sign:** Any raw dir target with no explicit ignore list.

### P4. harvest_importer.py grows to > 500 lines

**What goes wrong:** AGENT-07 enforces SKILL.md ≤ 500 lines, and AGENT.md for harvest-importer must be ≤ 500. The **Python script** has no line limit by harness rules, but the AGENT.md spec document does.
**Root cause:** Confusing script size with agent-spec size.
**Avoidance:** AGENT.md = minimal spec (inputs, outputs, invariants). Python script = unconstrained. Split implementation across multiple `.py` modules for readability but keep AGENT.md tight.
**Warning sign:** AGENT.md hitting 400+ lines with pseudocode pasted inside.

### P5. FAILURES merge doubles content on re-run

**What goes wrong:** Re-running harvest_importer concatenates orchestrator.md twice into `_imported_from_shorts_naberal.md`.
**Root cause:** Append-only logic with no idempotency check.
**Avoidance:** Before appending, grep for the `<!-- source: ... -->` comment. If present, skip this file. If re-import required, delete target and re-run.
**Warning sign:** `_imported_from_shorts_naberal.md` line count = 2 × 487 = 974.

### P6. HARVEST_DECISIONS.md not matching HARVEST_SCOPE.md §A format

**What goes wrong:** Planner picks different column headers, breaking planner-downstream-consumer expectation (Phase 4 Agent design reads both docs).
**Root cause:** "Use discretion" misread as "redesign format."
**Avoidance:** Copy the exact 5-column header row (`| ID | 드리프트 요약 | 판정 | 근거 | 실행 지시 |`) from HARVEST_SCOPE.md §A into HARVEST_DECISIONS.md top, then append rows for A-1..A-13 (copied from scope) + B-1..B-16 + C-1..C-10 (generated by 5-rule algo).
**Warning sign:** HARVEST_DECISIONS.md uses different column names like "Judgment" or "Source".

---

## Code Examples

### Core copy stage (reference implementation)

```python
# Source: Python 3.11 stdlib documentation — shutil.copytree, filecmp.dircmp
# https://docs.python.org/3/library/shutil.html#shutil.copytree

import json, shutil, subprocess
from pathlib import Path

def copy_raw(manifest_entry: dict, source_root: Path, dest_root: Path) -> dict:
    """Copy one raw directory per manifest entry. Returns audit record."""
    name = manifest_entry["dest"].split("/")[-1]  # e.g. 'theme_bible_raw'
    dest = dest_root / name
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=False)  # fail loudly if lockdown is already applied

    if manifest_entry.get("source"):
        # Whole-directory copy mode
        src = source_root / manifest_entry["source"]
        ignore = shutil.ignore_patterns(
            "node_modules", "__pycache__", "*.pyc", ".venv",
            "client_secret*.json", "token_*.json", ".env*"
        )
        shutil.copytree(src, dest, ignore=ignore, symlinks=False)
        return {"mode": "tree", "files_copied": sum(1 for _ in dest.rglob("*") if _.is_file())}

    elif manifest_entry.get("cherry_pick"):
        # Per-file mode for scattered sources
        dest.mkdir(parents=True, exist_ok=False)
        count = 0
        for rel in manifest_entry["cherry_pick"]:
            src = source_root / rel
            tgt = dest / Path(rel).name
            shutil.copy2(src, tgt)
            count += 1
        return {"mode": "cherry_pick", "files_copied": count}

    raise ValueError(f"Manifest entry {name} has neither source nor cherry_pick")
```

### Lockdown + verification (Windows-safe)

```python
# Source: Live-tested 2026-04-19 on Windows 11 26200 with Python 3.11.9
import subprocess
from pathlib import Path

def apply_lockdown(target: Path) -> None:
    win_path = str(target.resolve()).replace("/", "\\")
    cmd = ["cmd.exe", "/c", f"attrib +R /S /D {win_path}\\*"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"attrib failed: rc={result.returncode}, stderr={result.stderr!r}")

def verify_lockdown(target: Path) -> None:
    # Find any regular file under target and attempt write
    probe = next(target.rglob("*.md"), None)
    if probe is None:
        raise RuntimeError(f"No probe file found under {target}")
    try:
        probe.write_text("LOCKDOWN_VERIFY_TAMPER", encoding="utf-8")
    except PermissionError:
        return  # expected
    raise AssertionError(f"LOCKDOWN FAILED — write to {probe} succeeded")
```

### Blacklist parse (safe)

```python
# Source: Python stdlib ast.literal_eval docs
# https://docs.python.org/3/library/ast.html#ast.literal_eval
import ast, re
from pathlib import Path

def parse_blacklist(scope_md: Path) -> list[dict]:
    text = scope_md.read_text(encoding="utf-8")
    m = re.search(r"HARVEST_BLACKLIST\s*=\s*(\[.*?\n\])", text, re.DOTALL)
    if not m:
        raise ValueError("HARVEST_BLACKLIST not found in scope md")
    return ast.literal_eval(m.group(1))

# Returns list[dict] — each dict has one of: file, path, pattern, lines + mandatory 'reason'
```

---

## State of the Art

| Old approach | Current approach | When changed | Impact |
|--------------|------------------|--------------|--------|
| Inline bash `cp -r` + `chmod -w` | Python `shutil.copytree` + `cmd.exe //c attrib +R /S /D` | Windows platform constraint (2026-04-19 verification) | Cross-platform safe, deterministic error handling, no shell-glob pitfalls |
| `eval()` of blacklist dict | `ast.literal_eval()` | Security posture (agent discipline) | No code execution on markdown parse |
| Flat `diff -r src dst` | `filecmp.dircmp` recursive wrapper (Python) | Git Bash on Windows lacks `diff -r` by default | Portable, structured diff output |
| FAILURES glob `**/FAILURES.md` | Actual glob `.claude/failures/*.md` excluding README | Verified via `find` 2026-04-19 | Catches the real `orchestrator.md` filename |

**Deprecated patterns (blacklist re-confirmed):**
- `skip_gates=True` — orchestrate.py:1239, 1254, 1259, 1272, 1281, 1285, 1287, 1291 (8 occurrences, all in the same block)
- `TODO(next-session)` — orchestrate.py:520, 781, 1051, 1129 (4 occurrences, match HARVEST_SCOPE.md exactly)
- `selenium` pattern — AF-8 YouTube ToS violation

---

## Open Questions

1. **Does `.claude/channel_bibles/` contain enough channel-bible content to serve as Phase 4 anchor, or do we also need files from `.claude/agents/producers/`?**
   - What we know: 7 md files in `channel_bibles/` (documentary, humor, incidents, politics, trend, wildlife, README).
   - What's unclear: whether `.claude/agents/producers/<agent>/AGENT.md` files should also be harvested (they contain domain-specific rubric history).
   - Recommendation: Harvest `channel_bibles/` only in Phase 3 per HARVEST-01 literal wording. Phase 4 can cherry-pick from `.claude/agents/` as concept reference. Do NOT expand Phase 3 scope.

2. **Is there a root `FAILURES.md` that HARVEST_SCOPE.md anticipated but didn't materialize?**
   - What we know: no `FAILURES.md` at `shorts_naberal/` root (verified `test -f` returned non-zero).
   - What's unclear: whether a future shorts_naberal session will create one.
   - Recommendation: harvest_importer.py performs a conditional copy — if root `FAILURES.md` exists, include in merge; if not, log "not found, skipping" in audit.

3. **Should `scripts/orchestrator/hc_checks.py` tests be copied alongside the main file?**
   - What we know: `scripts/orchestrator/tests/test_hc_checks.py` exists.
   - What's unclear: Phase 5 orchestrator v2 rewrite may reference test expectations. Copying tests preserves them.
   - Recommendation: Copy both `hc_checks.py` and `tests/test_hc_checks.py` into `hc_checks_raw/` (2 files). Document in path_manifest.json.

4. **HARVEST-08's "39건 전수" — must HARVEST_DECISIONS.md also include A-class rows copied from scope, or only B/C new judgments?**
   - What we know: success criterion #3 reads "CONFLICT_MAP 39건(A:13/B:16/C:10) 각각에 대해 … 판단이 명시되어 있다."
   - Recommendation: Include all 39 in HARVEST_DECISIONS.md. A-class rows are verbatim from HARVEST_SCOPE.md §A. B/C rows are algorithm output. Single consolidated document.

---

## References

### Primary (HIGH confidence)

- **02-HARVEST_SCOPE.md** — `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (175 lines, locked 2026-04-19). A-class 13 judgments + Blacklist dict + 4-dir mapping + 5-rule algorithm.
- **03-CONTEXT.md** — `.planning/phases/03-harvest/03-CONTEXT.md` (110 lines, auto-generated 2026-04-19). Re-surfaces scope decisions.
- **CONFLICT_MAP.md** — `C:/Users/PC/Desktop/shorts_naberal/.planning/codebase/CONFLICT_MAP.md` (38,608 bytes, 2026-04-18). Source-of-truth for 13+16+10=39 drift entries. Heading format `### A-N. / B-N. / C-N.` verified by `grep -c`.
- **REQUIREMENTS.md** § HARVEST + § AGENT — HARVEST-01~08 + AGENT-06 (9 REQ total for Phase 3).
- **ROADMAP.md** § "Phase 3: Harvest" — 5 success criteria (all mapped to validation tests above).
- **02-VALIDATION.md** — format template for this phase's validation doc (12-test approach, framework-free).
- **CLAUDE.md** (`studios/shorts/CLAUDE.md`) — 8 domain absolute rules (rule #6 explicitly covers `shorts_naberal` read-only posture).

### Verified Live (2026-04-19)

- Filesystem scan of `C:/Users/PC/Desktop/shorts_naberal/` — confirms path remap necessity (§2 of Implementation Approaches).
- `cmd.exe //c attrib +R /S /D` lockdown test — verified Python `PermissionError` on write after lockdown.
- Git Bash attrib direct-call failure test — verified lockdown silently fails when shell glob is used instead of cmd.exe.
- CONFLICT_MAP.md heading count — `grep -cE "^### [ABC]-[0-9]+"` returns 39.
- `grep -cn skip_gates orchestrate.py` returns 8, `grep -cn 'TODO(next-session)' orchestrate.py` returns 4 — matches HARVEST_BLACKLIST.

### Secondary (MEDIUM confidence — Python stdlib docs, no live verification needed)

- [Python `shutil.copytree`](https://docs.python.org/3/library/shutil.html#shutil.copytree) — `ignore_patterns`, `symlinks`, `dirs_exist_ok` parameters.
- [Python `filecmp.dircmp`](https://docs.python.org/3/library/filecmp.html#filecmp.dircmp) — `left_only`, `right_only`, `diff_files`, `common_dirs`.
- [Python `ast.literal_eval`](https://docs.python.org/3/library/ast.html#ast.literal_eval) — safe evaluation of Python literal structures.
- [Microsoft `attrib` command](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/attrib) — `/S /D` recursion flags, `+R` read-only attribute.

### Context (Phase history)

- **Session #11~14** (STATE.md) — Phase 2 domain definition arc. Key output: HARVEST_SCOPE.md A-class 13 sealed + B/C 26 deferred to this phase.
- **Phase 2 consolidated commit** `f360e17` — 9 files, +449/-7. Establishes `.preserved/harvested/.gitkeep` scaffold which this phase populates.

---

## Metadata

**Confidence breakdown:**
- Implementation approaches: **HIGH** — stdlib-only, live-tested on target machine 2026-04-19.
- Validation architecture: **HIGH** — 11 commands, all runnable in Bash/Python/cmd.exe on Windows. No framework install.
- DAG / dependencies: **HIGH** — derived from HARVEST_SCOPE.md locked decisions + physical copy constraints.
- Edge cases: **HIGH** for E1-E7 (verified), **MEDIUM** for E8-E10 (defensive coverage, not triggered in current state).
- Path remapping (§2): **HIGH** — verified via live filesystem scan.

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days — stable Python stdlib APIs, stable Windows `attrib` behavior, source tree frozen for harvest duration). Earlier invalidation if:
- shorts_naberal source tree structure changes
- CONFLICT_MAP.md entry count changes from 39

**Estimated phase execution time:** 30-60 minutes (4-way parallel copy ~5 min, diff verify ~3 min, decisions build ~2 min, lockdown ~1 min, verify ~1 min; balance is planner/agent coordination).

---

*Research complete. Planner may proceed to `/gsd:plan-phase 3` with high confidence. Primary action item for planner: generate `path_manifest.json` in Wave 0 before any copy task — the HARVEST_SCOPE.md path mapping is stale.*
