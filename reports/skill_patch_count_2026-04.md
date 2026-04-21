# D-2 Lock Skill Patch Counter — 2026-04

**Lock period:** 2026-04-20 ~ 2026-06-20
**Report generated:** 2026-04-21T15:04:09.990813+09:00
**Violation count:** 5 🚨 (목표: 0)

## Violations
| Hash | Date | File | Subject |
|------|------|------|---------|
| 60e1bea | 2026-04-21T08:09:30+09:00 | `.claude/hooks/pre_tool_use.py` | feat(12-05): extend check_failures_append_only with 500줄 cap + env whitelist |
| e57f891 | 2026-04-20T21:07:33+09:00 | `.claude/hooks/session_start.py` | docs(claude-md): slim to 96 lines + add Perfect Navigator (대표님 directive) |
| e57f891 | 2026-04-20T21:07:33+09:00 | `CLAUDE.md` | docs(claude-md): slim to 96 lines + add Perfect Navigator (대표님 directive) |
| 8172e9c | 2026-04-20T19:31:28+09:00 | `.claude/hooks/session_start.py` | fix(context): 세션 컨텍스트 단절 영구 수정 — memory 9종 + session_start Step 4-6 + FAILURES.md F-CTX-01 |
| 8172e9c | 2026-04-20T19:31:28+09:00 | `CLAUDE.md` | fix(context): 세션 컨텍스트 단절 영구 수정 — memory 9종 + session_start Step 4-6 + FAILURES.md F-CTX-01 |

## Scan coverage
- Lock window scanned: 2026-04-20 → 2026-06-20
- Forbidden paths checked: 4
- Regex: `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md`

## Notes
- Count > 0 시 `FAILURES.md` 에 `F-D2-NN` 엔트리가 자동 append 됩니다 (D-11).
- `directive-authorized` Pre-Phase10 commit 은 **투명하게 count 에 포함**합니다 — Whitelist 금지 (Risk #1 옵션 D, 2026-04-20 대표님 승인본).
