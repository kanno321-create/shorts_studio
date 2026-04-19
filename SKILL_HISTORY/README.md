# SKILL_HISTORY — Pre-Write Backup Archive (D-12 / FAIL-03)

Auto-managed backup directory for `.claude/skills/<name>/SKILL.md` edits.

## Invariant

Every Write/Edit/MultiEdit to any file whose basename is `SKILL.md` triggers a
pre-tool-use backup via `backup_skill_before_write` in
`.claude/hooks/pre_tool_use.py`. The existing content is copied — _before_ the
new content is written — to:

```
SKILL_HISTORY/<skill_name>/v<YYYYMMDD_HHMMSS>.md.bak
```

where `<skill_name>` is the parent directory name
(e.g. `.claude/skills/notebooklm/SKILL.md` -> `SKILL_HISTORY/notebooklm/v*.md.bak`).

## Why

Phase 6 D-2 저수지 원칙 + FAIL-04 (Phase 10 first 1-2 months SKILL patch
freeze) require recoverability. If an over-eager SKILL edit erases a working
prompt, we restore from the most recent `.bak`.

## Restore

```bash
# Find recent backups of a skill
ls -lt SKILL_HISTORY/<skill_name>/

# Restore the latest
cp SKILL_HISTORY/<skill_name>/v<timestamp>.md.bak .claude/skills/<skill_name>/SKILL.md
```

## First-Time Create

`backup_skill_before_write` is a silent no-op when the target `SKILL.md` does
not yet exist — first-time skill creation does not produce a `.bak`.

## Never Modify Manually

This directory is machine-managed. Do not delete or rename files here — Phase
10 pattern aggregation (`scripts/failures/aggregate_patterns.py`) reads history
to correlate SKILL drift with failure recurrence.

## Related

- `.claude/hooks/pre_tool_use.py` — `backup_skill_before_write` helper
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-CONTEXT.md` §D-12
- `.claude/failures/_imported_from_shorts_naberal.md` — Phase 3 imported FAIL-04
