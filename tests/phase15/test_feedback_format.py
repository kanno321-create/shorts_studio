"""UFL-04 verify_feedback_format.py validator contract (Phase 15 Plan 05 Task 02).

Markdown H2 entry + 4 required fields (session_id, niche, rating, feedback)
+ rating format 1-5/5 검증.

Reference: .planning/phases/15-.../15-05-PLAN.md Task 02 behavior block.
"""
from __future__ import annotations

import pytest

from scripts.validate.verify_feedback_format import (
    main,
    parse_entries,
    validate_entry,
)


GOOD = """---
d2_exception: true
---

# 영상 품질 피드백 로그

## 2026-04-22 abc12345xyz
- session_id: sess_01
- niche: incidents
- rating: 3/5
- feedback: 좋습니다
- keywords: ['좋습니다']
"""

MISSING_RATING = """# header

## 2026-04-22 abc12345xyz
- session_id: sess_01
- niche: incidents
- feedback: 좋습니다
"""

MALFORMED_HEADER = """# header

## not_a_date abc
- session_id: sess_01
- niche: incidents
- rating: 3/5
- feedback: 좋습니다
"""

RATING_OUT_OF_RANGE = """# header

## 2026-04-22 abc12345xyz
- session_id: sess_01
- niche: incidents
- rating: 9/5
- feedback: 좋습니다
"""

MULTIPLE_ENTRIES = """# header

## 2026-04-22 v1
- session_id: s1
- niche: incidents
- rating: 5/5
- feedback: 첫번째

## 2026-04-23 v2
- session_id: s2
- niche: mystery
- rating: 2/5
- feedback: 두번째
"""


class TestValidator:
    def test_validates_correct_format(self, tmp_path):
        p = tmp_path / "f.md"
        p.write_text(GOOD, encoding="utf-8")
        assert main(["--path", str(p)]) == 0

    def test_detects_missing_rating_field(self, tmp_path, capsys):
        p = tmp_path / "f.md"
        p.write_text(MISSING_RATING, encoding="utf-8")
        exit_code = main(["--path", str(p)])
        assert exit_code == 1
        out = capsys.readouterr().out
        assert "rating" in out

    def test_detects_malformed_h2_heading_skips_entry(self, tmp_path, capsys):
        p = tmp_path / "f.md"
        p.write_text(MALFORMED_HEADER, encoding="utf-8")
        exit_code = main(["--path", str(p)])
        # Malformed H2 — entry 로 잡히지 않아 0 entry 검증 → 0 exit.
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "전체" in out or "0" in out

    def test_empty_seed_file_passes(self, tmp_path):
        p = tmp_path / "f.md"
        p.write_text(
            "---\nd2_exception: true\n---\n\n# header\n",
            encoding="utf-8",
        )
        assert main(["--path", str(p)]) == 0

    def test_detects_rating_out_of_range(self, tmp_path, capsys):
        p = tmp_path / "f.md"
        p.write_text(RATING_OUT_OF_RANGE, encoding="utf-8")
        exit_code = main(["--path", str(p)])
        assert exit_code == 1
        out = capsys.readouterr().out
        assert "rating" in out or "9/5" in out

    def test_missing_file_exits_1(self, tmp_path, capsys):
        exit_code = main(["--path", str(tmp_path / "nonexistent.md")])
        assert exit_code == 1


class TestParseEntries:
    def test_parses_multiple_entries(self):
        entries = parse_entries(MULTIPLE_ENTRIES)
        assert len(entries) == 2
        assert entries[0]["_fields"]["rating"] == "5/5"
        assert entries[1]["_fields"]["niche"] == "mystery"

    def test_parses_no_entries_in_header_only(self):
        assert parse_entries("# just header\n") == []


class TestValidateEntry:
    def test_missing_fields_yields_errors(self):
        entry = {
            "_line": 3,
            "_header": "## 2026-04-22 v1",
            "_fields": {"session_id": "s"},
        }
        errors = validate_entry(entry)
        # niche, rating, feedback 누락 → 최소 3 errors.
        assert len(errors) >= 3
        assert any("niche" in e for e in errors)
        assert any("rating" in e for e in errors)
        assert any("feedback" in e for e in errors)

    def test_valid_entry_no_errors(self):
        entry = {
            "_line": 3,
            "_header": "## 2026-04-22 v1",
            "_fields": {
                "session_id": "s",
                "niche": "incidents",
                "rating": "3/5",
                "feedback": "좋습니다",
            },
        }
        assert validate_entry(entry) == []
