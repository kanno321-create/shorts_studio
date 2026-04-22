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

**Planning / Structure (B-tier)**
- See `FAIL-ARCH-01` in FAILURES.md — docs/ARCHITECTURE.md Phase status stale (2026-04-21 세션 #28)

**Agent Schema Standardization (B-tier, directive-authorized)**
- See `F-D2-EXCEPTION-01` in FAILURES.md — trend-collector JSON-only enforcement (Phase 11, 세션 #29)
- See `F-D2-EXCEPTION-02 Wave 2` in FAILURES.md — 13 Producer AGENT.md v1.2 batch (Phase 12, 세션 #29)
- See `F-D2-EXCEPTION-02 Wave 3` in FAILURES.md — 17 Inspector AGENT.md v1.1 batch (Phase 12, 세션 #29)

**Live Smoke / Pipeline Integrity (A-tier)**
- See `F-LIVE-SMOKE-JSON-NONCOMPLIANCE` in FAILURES.md — Claude CLI 자연어 반환 + nudge retry empty stdout (Phase 13 retry, 세션 #30) — **상태: open**
- See `F-SUPERVISOR-VERDICT-TYPE-MISMATCH` in FAILURES.md — state.Verdict Enum vs gate_guard.Verdict dataclass latent bug, skip-supervisor bypass 가 surface (세션 #31, 2026-04-22) — **상태: resolved**

**Meta / Infrastructure Wiring (A-tier)**
- See `F-META-HOOK-FAILURES-NOT-INJECTED` in FAILURES.md — 원칙 있어도 hook wiring 없으면 무의미 (세션 #30, 2026-04-22)

## Sources

- `_imported_from_shorts_naberal.md` — 500 lines, Phase 3 sha256-locked (D-14)
- `FAILURES.md` — Phase 6+ append-only (D-11)

## Update Protocol

1. New FAIL entry added to `FAILURES.md` (append-only via Hook)
2. Extract category keyword from entry
3. Append bullet under matching `### <Category>` heading here
4. Bullet format: `- See FAIL-NNN in FAILURES.md` (for Phase 6+ entries)
   or `- See FAIL-NNN in _imported_from_shorts_naberal.md` (for Phase 3 imported entries)
