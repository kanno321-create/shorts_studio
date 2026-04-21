---
name: bad-fixture-missing-channel-bible
version: 0.0
role: producer
category: test-fixture
---

# bad-fixture-missing-channel-bible

<role>
Bad fixture — omits the canonical channel_identity.md path to prove
verify_mandatory_reads_prose.verify_file returns ok=False when element 2
is absent. Used only by tests/phase12/test_mandatory_reads_prose.py.
</role>

<mandatory_reads>
## 필수 읽기 (매 호출마다 전수 읽기, 샘플링 금지)

1. `.claude/failures/FAILURES.md` — 과거 실패 전수 인지.
2. `wiki/ypp/channel_bible.md` — legacy path (DOES NOT EXIST).
3. `.claude/skills/gate-dispatcher/SKILL.md` — GATE dispatch.

**NOTE**: 이 fixture 는 canonical channel-identity 경로 (`wiki/` SSOT
path) 를 의도적으로 누락. validator 가 Plan 01 SUMMARY deviation #2 에서
rectified 된 정확 경로 literal 만 수용함을 증명.
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
