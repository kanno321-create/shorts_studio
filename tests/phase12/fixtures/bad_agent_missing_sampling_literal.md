---
name: bad-fixture-missing-sampling
version: 0.0
role: producer
category: test-fixture
---

# bad-fixture-missing-sampling

<role>
Bad fixture — omits the 샘-플-링 (space-split) Korean literal to prove
verify_mandatory_reads_prose.verify_file returns ok=False when element 4
is absent. Used only by tests/phase12/test_mandatory_reads_prose.py.
</role>

<mandatory_reads>
## 필수 읽기

1. `.claude/failures/FAILURES.md` — 과거 실패 전수 인지.
2. `wiki/continuity_bible/channel_identity.md` — 채널 정체성.
3. `.claude/skills/gate-dispatcher/SKILL.md` — GATE dispatch.

**NOTE**: 이 fixture 는 의도적으로 '샘플링<SPLIT>금지' Korean literal 을 누락.
(위 split 는 validator 가 정확 매칭만 허용함을 증명하기 위한 fixture.)
</mandatory_reads>

<output_format>
N/A — test fixture only.
</output_format>

<skills>
- `gate-dispatcher` (required)
</skills>

<constraints>
Test fixture — not a real agent.
</constraints>
