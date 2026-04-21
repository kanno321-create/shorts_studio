---
name: bad-fixture-orphan-skill
version: 0.0
role: producer
category: test-fixture
---

# bad-fixture-orphan-skill

<role>
Bad fixture — declares a SKILL.md path that does NOT exist on disk
(`.claude/skills/nonexistent-skill-xyz/SKILL.md`). Proves the validator's
on-disk existence check catches AGENT.md → skills/ drift.
</role>

<mandatory_reads>
## 필수 읽기 (매 호출마다 전수 읽기, 샘플링 금지)

1. `.claude/failures/FAILURES.md` — 과거 실패 전수 인지.
2. `wiki/continuity_bible/channel_identity.md` — 채널 정체성.
3. `.claude/skills/nonexistent-skill-xyz/SKILL.md` — DRIFT (파일 없음).

**NOTE**: validator 가 declared SKILL.md path 의 disk 존재를 교차검증하는지 확인.
</mandatory_reads>

<output_format>
N/A — test fixture only.
</output_format>

<skills>
- `nonexistent-skill-xyz` (required) — 존재하지 않는 skill
</skills>

<constraints>
Test fixture — not a real agent.
</constraints>
