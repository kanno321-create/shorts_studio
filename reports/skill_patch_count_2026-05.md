# D-2 Lock Skill Patch Counter — 2026-05

**Lock period:** 2026-04-20 ~ 2026-06-20
**Report generated:** 2026-05-01T09:39:32.743159+09:00
**Violation count:** 10 🚨 (목표: 0)

## Violations
| Hash | Date | File | Subject |
|------|------|------|---------|
| 5abd0f2 | 2026-04-23T00:43:26+09:00 | `CLAUDE.md` | docs(33): session #33 handoff — Ryan Waller v1 fail + 5 root causes + 세션 종료 |
| 5a1c391 | 2026-04-22T21:25:10+09:00 | `CLAUDE.md` | feat(16): phase 16 production integration option A — planning artifacts |
| ad8b3b7 | 2026-04-22T15:35:31+09:00 | `.claude/hooks/session_start.py` | chore(handoff): session #30 tail wiring — FAILURES auto-injection + lenient retry principle |
| ad8b3b7 | 2026-04-22T15:35:31+09:00 | `CLAUDE.md` | chore(handoff): session #30 tail wiring — FAILURES auto-injection + lenient retry principle |
| 4d916a9 | 2026-04-21T20:06:22+09:00 | `.claude/hooks/pre_tool_use.py` | feat(14-04): pre_tool_use.py ADAPT-06c warn-only Hook + .gitignore wiring |
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
