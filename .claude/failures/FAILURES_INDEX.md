# FAILURES Index

> Category-tagging index across both `_imported_from_shorts_naberal.md` (Phase 3 immutable,
> 500 lines, sha256-locked) and `FAILURES.md` (Phase 6+ append-only).
>
> **D-14 invariant:** This file REFERENCES entries in `_imported_from_shorts_naberal.md`
>                    by fail-ID — it NEVER modifies that file.
> **D-11 invariant:** This file is itself a derivative index; Plan 09 aggregation reads it.
>                    Hook does NOT block edits here (only basename `FAILURES.md` is append-only).

## Index by Category

### Planning / Structure (A-tier)
- See FAIL-011, FAIL-023, FAIL-029 in `_imported_from_shorts_naberal.md`

### Content Quality (B-tier)
- See FAIL-005, FAIL-014 in `_imported_from_shorts_naberal.md`

### Audio / Publishing (B-tier)
- See FAIL-018 in `_imported_from_shorts_naberal.md`

### Research / Fact-check (C-tier)
- See FAIL-030-range in `_imported_from_shorts_naberal.md`

### Phase 6+ Entries
- (none yet — new index entries for `FAILURES.md` go here as Phase 6+ patterns accumulate)

## Sources

- `_imported_from_shorts_naberal.md` — 500 lines, Phase 3 sha256-locked (D-14)
- `FAILURES.md` — Phase 6+ append-only (D-11)

## Update Protocol

1. New FAIL entry added to `FAILURES.md` (append-only via Hook)
2. Extract category keyword from entry
3. Append bullet under matching `### <Category>` heading here
4. Bullet format: `- See FAIL-NNN in FAILURES.md` (for Phase 6+ entries)
   or `- See FAIL-NNN in _imported_from_shorts_naberal.md` (for Phase 3 imported entries)
