# FAILURES.md — Append-Only Reservoir

> **D-11:** Append-only via `check_failures_append_only` in `.claude/hooks/pre_tool_use.py`.
>          Modification of existing lines is physically blocked (deny). Only Write with
>          existing-content-as-prefix or new-entry append is allowed.
> **D-14:** Separate from `_imported_from_shorts_naberal.md` (Phase 3 sha256-locked).
>          This file never modifies or duplicates that file — only accumulates Phase 6+ entries.
> **D-2 저수지 원칙:** New failures accumulate here. 30-day aggregation (Plan 09) scans both
>                     this file and `_imported_from_shorts_naberal.md` to surface patterns
>                     (recurrence ≥ 3 → `SKILL.md.candidate` dry-run).

## Entry Schema

```
### FAIL-NNN: [one-line summary]
- **Tier**: A/B/C/D
- **발생 세션**: YYYY-MM-DD 세션 N
- **재발 횟수**: 1
- **Trigger**: [what triggers this failure]
- **무엇**: [what went wrong, observable symptom]
- **왜**: [root cause, invariant violated]
- **정답**: [correct behavior, invariant restored]
- **검증**: [how to verify the fix holds — grep/test/metric]
- **상태**: [observed | resolved | recurring]
- **관련**: [links to other FAIL-IDs, FAILURES_INDEX.md category, wiki nodes]
```

## Entries

(none yet — first Phase 6+ entry goes below this header line; do NOT modify the
above schema or any existing entry once added — append-only Hook will deny.)
