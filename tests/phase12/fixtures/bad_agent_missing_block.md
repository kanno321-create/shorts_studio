---
name: bad-fixture-missing-block
version: 0.0
role: producer
category: test-fixture
---

# bad-fixture-missing-block

<role>
Bad fixture — no `<mandatory_reads>` block at all. Proves
verify_mandatory_reads_prose.verify_file returns ok=False with the
"(no <mandatory_reads> block — Plan 02/03 migration 필요)" message.
</role>

<output_format>
N/A — test fixture only.
</output_format>

<skills>
- `gate-dispatcher` (required)
</skills>

<constraints>
Test fixture — not a real agent.
</constraints>
