---
phase: 11-pipeline-real-run-activation-script-quality-mode
plan: 05
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/audit/skill_patch_counter.py
  - tests/phase10/test_skill_patch_counter.py
autonomous: true
requirements: [AUDIT-05]
must_haves:
  truths:
    - "Running skill_patch_counter twice on identical git state produces only ONE FAILURES.md append (second run detects existing commit-hash set, skips append, preserves exit code semantics)"
    - "F-D2-NN entry format unchanged — existing F-D2-01 from commit 2026-04-21 preserved byte-exact after second run"
    - "Third run with a NEW violation commit appends a new F-D2-NN entry containing ONLY the new violation (existing ones filtered out)"
    - "Exit code contract preserved: violations present → rc=1; violations absent → rc=0; even if second run writes no new entry, rc=1 still reflects 'violations exist in the lock window'"
    - "2026-05-20 first monthly scheduler execution (Plan 10-04 skill-patch-count-monthly.yml) runs on idempotent code (D-22 entry gate)"
    - "Signature design: commit short-hash set (option (a) per RESEARCH §Pattern 5) — resilient to subject-line edits, fragile only to re-formatting of the `- `7hex` ...` line marker"
  artifacts:
    - path: "scripts/audit/skill_patch_counter.py"
      provides: "_existing_violation_hashes helper + main() grep-before-append guard"
      contains: "_existing_violation_hashes, re.finditer, existing_hashes"
    - path: "tests/phase10/test_skill_patch_counter.py"
      provides: "test_idempotency_skip_existing D-24 regression"
      contains: "def test_idempotency_skip_existing"
  key_links:
    - from: "skill_patch_counter.main"
      to: "_existing_violation_hashes(failures_text)"
      via: "called before append_failures() — violations filtered by hash set"
      pattern: "existing_hashes"
    - from: "_existing_violation_hashes"
      to: "re.match regex for ^- `{7-hex}`"
      via: "per-line grep across F-D2-NN entries"
      pattern: "^- `\\(\\[0-9a-f\\]\\{7\\}\\)`"
---

<objective>
AUDIT-05 / D-22 / D-23 / D-24: Add idempotency guard to `scripts/audit/skill_patch_counter.py::main` so that running the counter twice on an unchanged git state produces exactly ONE FAILURES.md entry. Root cause of D10-01-DEF-02: counter currently unconditionally appends on every invocation, and Phase 10 execution ran the counter 5 times → F-D2-01~F-D2-05 were duplicates.

Hard deadline per D-22: 2026-05-20 first monthly scheduler execution (`.github/workflows/skill-patch-count-monthly.yml` from Plan 10-04). Phase 11 is the entry gate for that scheduler.

Design per RESEARCH §Pattern 5:
- Signature: commit short-hash set (sorted tuple of 7-hex hashes grep'd from existing F-D2-NN entries)
- Grep regex: `r"^- `([0-9a-f]{7})`"` — matches current append format at `skill_patch_counter.py:220-224`
- Algorithm: read FAILURES.md → parse existing hashes → filter violations → skip append if no new → preserve exit code (1 if violations in window, 0 otherwise)
- F-D2-01 from commit 2026-04-21 MUST survive second-run byte-for-byte (strict prefix invariant, D-25)

Output:
- `scripts/audit/skill_patch_counter.py` with `_existing_violation_hashes()` helper + main() integration
- `tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing` (new test case, D-24)
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md
@.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md
@scripts/audit/skill_patch_counter.py
@tests/phase10/test_skill_patch_counter.py
@.planning/phases/10-sustained-operations/deferred-items.md

<interfaces>
<!-- Current append_failures + main flow in skill_patch_counter.py -->

From scripts/audit/skill_patch_counter.py:
- L187-237: `append_failures(violations, repo_root, now)` — writes F-D2-NN entries to FAILURES.md via `open('a')` (hook-bypass comment at L192-197)
- L220-224: per-violation line format:
  ```python
  body.append(
      f"- `{short_hash}` {v.get('date') or ''} — "
      f"`{v.get('violating_file') or ''}` ({v.get('subject') or ''})"
  )
  ```
  where `short_hash = (v.get("hash") or "")[:7]`
- L240+: `main()` — argparse + collect violations + call append_failures + return 1 if violations else 0

Test fixture (from tests/phase10/conftest.py — used by existing 11 tests):
- `tmp_git_repo` — initializes .git/ in tmp_path with seed commit
- `make_commit(files, message)` — returns 40-hex commit hash
- `repo_root` — real repo root (for reports/.gitkeep test)

Plan 10-04 scheduler artifact:
- `.github/workflows/skill-patch-count-monthly.yml` — triggers counter monthly; first execution 2026-05-20
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Wave 0 — add test_idempotency_skip_existing to existing test file (RED)</name>
  <files>tests/phase10/test_skill_patch_counter.py</files>
  <read_first>
    - tests/phase10/test_skill_patch_counter.py (FULL FILE — understand existing 11 tests + conftest fixtures used)
    - tests/phase10/conftest.py (fixtures: tmp_git_repo, make_commit, repo_root, seed_failures_md if exists)
    - scripts/audit/skill_patch_counter.py (L187-287 — append_failures + main)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 5 (L314-381 test template)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-22, D-23, D-24, D-25
    - .planning/phases/10-sustained-operations/deferred-items.md §D10-01-DEF-02 (root cause)
  </read_first>
  <behavior>
    - NEW test: `test_idempotency_skip_existing` — 3-phase assertion:
      - Phase A (1st run, fresh violation): seed a violation commit → run main → rc=1 → FAILURES.md grows by exactly 1 F-D2-NN entry
      - Phase B (2nd run, identical state): run main again → rc=1 (still violations exist) → FAILURES.md byte-exact unchanged (no new append)
      - Phase C (3rd run, new violation): seed a new violation commit → run main → rc=1 → FAILURES.md grows by 1 more entry; original entry preserved byte-exact (strict prefix)
    - Reuses existing `tmp_git_repo` + `make_commit` fixtures from conftest
    - Does NOT change any existing test (11 existing tests still GREEN)
  </behavior>
  <action>
    APPEND this test function at the end of `tests/phase10/test_skill_patch_counter.py`. Do not modify existing tests (preserve the "11 existing GREEN" baseline).

    First read the existing conftest to confirm fixture names (`tmp_git_repo`, `make_commit`, maybe `seed_failures_md`). If `seed_failures_md` fixture doesn't exist in conftest, this test inlines the seeding.

    EXACT APPEND (after the last existing test function):

    ```python


    # ---------------------------------------------------------------------------
    # AUDIT-05 (Phase 11 Plan 11-05) — idempotency guard regression test (D-24).
    # ---------------------------------------------------------------------------


    def test_idempotency_skip_existing(tmp_git_repo: Path, make_commit) -> None:
        """D-24: counter run twice on same state MUST append only once.

        Phase A: fresh hook-file violation → rc=1 + 1 F-D2-NN entry appended.
        Phase B: identical state, run again → rc=1 but FAILURES.md byte-exact.
        Phase C: new violation → rc=1 + 1 more entry; Phase A entry preserved.
        """
        from scripts.audit.skill_patch_counter import main

        # Seed FAILURES.md so append_failures has a target
        failures_path = tmp_git_repo / "FAILURES.md"
        failures_path.write_text(
            "# FAILURES — append-only\n\n"
            "## F-D1-00 — 박제\n\n"
            "Pre-Phase10 seed entry (strict prefix preserved).\n\n",
            encoding="utf-8",
        )

        # Phase A: one hook-file violation
        make_commit({".claude/hooks/example.py": "# modified\n"}, "fix(hook): example edit")
        rc1 = main([
            "--repo", str(tmp_git_repo),
            "--since", "2026-04-20",
            "--until", "2026-06-20",
        ])
        assert rc1 == 1, f"Phase A: violations present → rc=1 (got {rc1})"
        post1 = failures_path.read_text(encoding="utf-8")
        assert post1.count("## F-D2-") == 1, (
            f"Phase A: exactly 1 F-D2 entry expected, got {post1.count('## F-D2-')}"
        )

        # Phase B: same git state, run again — MUST NOT append
        rc2 = main([
            "--repo", str(tmp_git_repo),
            "--since", "2026-04-20",
            "--until", "2026-06-20",
        ])
        assert rc2 == 1, f"Phase B: violations still exist → rc=1 (got {rc2})"
        post2 = failures_path.read_text(encoding="utf-8")
        assert post2 == post1, (
            "Phase B: FAILURES.md must be byte-exact unchanged on second run"
        )
        assert post2.count("## F-D2-") == 1, "Phase B: still exactly 1 F-D2 entry"

        # Phase C: new violation → append ONLY the new one
        make_commit({"CLAUDE.md": "# mod\n"}, "docs(test): second violation")
        rc3 = main([
            "--repo", str(tmp_git_repo),
            "--since", "2026-04-20",
            "--until", "2026-06-20",
        ])
        assert rc3 == 1, f"Phase C: violations present → rc=1 (got {rc3})"
        post3 = failures_path.read_text(encoding="utf-8")
        assert post3.count("## F-D2-") == 2, (
            f"Phase C: 2 F-D2 entries expected (A preserved + new), got {post3.count('## F-D2-')}"
        )
        assert post3.startswith(post1), (
            "Phase C: Phase A content preserved byte-exact as strict prefix (D-25)"
        )
    ```

    Run it RED:
    ```
    pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -v
    ```
    Expected RED: Phase B assertion fails — `post2 != post1` because current code appends a duplicate F-D2-02 entry.

    Also run the existing 11 tests to confirm no regression from the APPEND:
    ```
    pytest tests/phase10/test_skill_patch_counter.py -v
    ```
    Expected: 11 GREEN + 1 new RED.
  </action>
  <verify>
    <automated>pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -v 2>&1 | tail -15</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "def test_idempotency_skip_existing" tests/phase10/test_skill_patch_counter.py` returns 1
    - Test is RED: `pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -v 2>&1 | grep -E "FAILED|AssertionError"` returns ≥1
    - Existing 11 tests still GREEN: `pytest tests/phase10/test_skill_patch_counter.py -v 2>&1 | grep -E "11 passed|11 failed"` — 11 passed (only new test fails)
  </acceptance_criteria>
  <done>New test appended, RED, ready for GREEN in Task 2; existing 11 tests unaffected.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Implement _existing_violation_hashes guard in main() — GREEN 12 total</name>
  <files>scripts/audit/skill_patch_counter.py</files>
  <read_first>
    - scripts/audit/skill_patch_counter.py (FULL FILE — especially L187-287)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-RESEARCH.md §Pattern 5 (L316-381 algorithm)
    - tests/phase10/test_skill_patch_counter.py (new test from Task 1)
    - .planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md D-23
  </read_first>
  <behavior>
    - `test_idempotency_skip_existing` GREEN
    - 11 existing Phase 10 tests still GREEN (12/12 total)
    - Existing F-D2-NN entry format unchanged — `append_failures` body format preserved byte-for-byte
    - Exit code contract preserved (rc=1 if violations exist in window, rc=0 if none — even if no append happened this run)
    - `_existing_violation_hashes` is a module-level helper (private, underscore-prefix)
    - Logger info message on skip with Korean diagnostic + 대표님 appellation
  </behavior>
  <action>
    Edit `scripts/audit/skill_patch_counter.py`:

    **Step 1:** Add `_existing_violation_hashes` helper function immediately BEFORE `append_failures` (around L186). Insert:

    ```python
    def _existing_violation_hashes(failures_text: str) -> set[str]:
        """Parse F-D2-NN entries and return the union of commit short-hashes.

        Recognized line format (matches ``append_failures`` at L220-224):
            ``- `7-hex` YYYY-MM-DD — `file.ext` (subject)``

        Returns a set of 7-hex short hashes. Used by :func:`main` to skip
        duplicate appends (AUDIT-05 / D-23). Format coupling with
        ``append_failures`` is tested by
        ``tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing``.
        """
        hashes: set[str] = set()
        # Match F-D2-NN entries (greedy until next F-D or EOF)
        entry_re = re.compile(r"^## F-D2-\d{2}.*?(?=^## F-|\Z)", re.MULTILINE | re.DOTALL)
        line_re = re.compile(r"^- `([0-9a-f]{7})`")
        for entry_match in entry_re.finditer(failures_text):
            for line in entry_match.group(0).splitlines():
                m = line_re.match(line)
                if m:
                    hashes.add(m.group(1))
        return hashes
    ```

    **Step 2:** Modify `main()` to call the guard before `append_failures`. Locate the section in main() that calls `append_failures(violations, ...)` (near L280+). BEFORE that call, insert:

    ```python
        # AUDIT-05 (D-23): skip append when all violations already recorded.
        failures_path = repo_root / "FAILURES.md"
        if failures_path.exists():
            existing_text = failures_path.read_text(encoding="utf-8")
            existing_hashes = _existing_violation_hashes(existing_text)
        else:
            existing_hashes = set()
        new_violations = [
            v for v in violations
            if (v.get("hash") or "")[:7] not in existing_hashes
        ]
        if violations and not new_violations:
            logger.info(
                "[skill_patch_counter] 신규 violation 없음 — 기존 F-D2-NN 에 %d건 "
                "이미 기록 (대표님, 재실행 skip)",
                len(violations),
            )
            # Skip FAILURES.md append; report file still written.
            # Preserve exit code contract: violations exist in window → rc=1
        else:
            append_failures(new_violations, repo_root, now)
    ```

    Note: This MODIFIES the call from `append_failures(violations, ...)` to conditional append with `new_violations` (which may be a subset). If no existing append_failures call is present in the control flow shown above (because it's currently unconditional at end of main), adapt by REPLACING the unconditional `append_failures(violations, repo_root, now)` with the conditional block above.

    **Step 3:** Verify `logger` is defined in the module (it is — `skill_patch_counter.py` uses logger throughout).

    **Step 4:** Verify `import re` is already present at top (it is — L48 uses re).

    **Step 5:** Run tests:
    ```
    pytest tests/phase10/test_skill_patch_counter.py -v          # 12 GREEN
    pytest tests/phase10/ -q                                       # Phase 10 regression — 95+ GREEN
    pytest tests/phase04/ -q                                       # 244/244 baseline
    ```

    **Step 6:** Confirm no regex regression — manually test the helper:
    ```
    python -c "
    from scripts.audit.skill_patch_counter import _existing_violation_hashes
    sample = '''## F-D2-01 — test
    **증상**: test.
    - \`abc1234\` 2026-04-21 — \`.claude/hooks/x.py\` (fix)
    - \`def5678\` 2026-04-21 — \`.claude/hooks/y.py\` (fix)

    ## F-D2-02 — second
    - \`111aaaa\` 2026-04-22 — \`CLAUDE.md\` (docs)
    '''
    hashes = _existing_violation_hashes(sample)
    print(sorted(hashes))
    assert hashes == {'abc1234', 'def5678', '111aaaa'}, hashes
    print('PASS')
    "
    ```
    Expected output: `['111aaaa', 'abc1234', 'def5678']` then `PASS`.
  </action>
  <verify>
    <automated>pytest tests/phase10/test_skill_patch_counter.py -v 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -n "def _existing_violation_hashes" scripts/audit/skill_patch_counter.py` returns 1 match
    - `grep -c "existing_hashes" scripts/audit/skill_patch_counter.py` returns ≥2 matches (declaration + usage filter)
    - `grep -n "신규 violation 없음" scripts/audit/skill_patch_counter.py` returns 1 match (Korean skip log)
    - `grep -n "대표님" scripts/audit/skill_patch_counter.py` returns ≥1 match in the skip-log vicinity
    - `pytest tests/phase10/test_skill_patch_counter.py -v` → 12 passed (11 existing + 1 new)
    - `pytest tests/phase04/ -q` → 244/244 passed
    - Direct invocation `python -c` snippet for `_existing_violation_hashes` prints `PASS`
  </acceptance_criteria>
  <done>12 Phase 10 counter tests GREEN + 244/244 phase04 preserved + 2026-05-20 scheduler deadline met for idempotent counter.</done>
</task>

</tasks>

<verification>
**Per-plan verify:**
```bash
pytest tests/phase10/test_skill_patch_counter.py -v    # 12/12 GREEN
pytest tests/phase04/ -q                                # 244/244
pytest tests/phase10/ -q                                # Phase 10 regression (excluding known pre-existing drifts per D10-01-DEF-01)
```

**AUDIT-05 / SC#3 linkage:** `pytest tests/phase10/test_skill_patch_counter.py::test_idempotency_skip_existing -x → GREEN` is the automated signal.

**Deadline:** 2026-05-20 first monthly scheduler execution. Phase 11 completion before this date closes the D-22 entry gate.
</verification>

<success_criteria>
- [ ] `_existing_violation_hashes` helper defined in skill_patch_counter.py
- [ ] main() filters violations against existing hash set before append_failures call
- [ ] Skip log with Korean diagnostic + 대표님 appellation
- [ ] Exit code contract preserved (rc=1 if violations exist in window, even if no append)
- [ ] 12/12 Phase 10 counter tests GREEN (11 existing + 1 new)
- [ ] 244/244 phase04 baseline preserved
- [ ] F-D2-01 byte-exact preservation verified by test Phase C
</success_criteria>

<output>
After completion, create `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-05-SUMMARY.md` with:
- Files modified + net line delta on skill_patch_counter.py (~+20)
- Test count: 11 → 12 Phase 10 counter tests; Phase 11 total cumulative: 274 → 275
- Confirmation that 2026-05-20 scheduler will now run idempotent code
- Grep evidence that signature algorithm uses commit short-hash set (option (a))
</output>
