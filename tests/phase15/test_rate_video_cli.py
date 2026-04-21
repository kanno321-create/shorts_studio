"""UFL-04 rate_video.py CLI contract (Phase 15 Plan 05 Task 01).

대표님 영상 품질 subjective rating CLI 의 7+ contract 테스트.

검증 대상:
    - argparse 인자 계약 (--video-id, --rating, --feedback, --session-id, --niche)
    - rating 1~5 범위 validation (ValueError + 대표님 존댓말)
    - Markdown H2 append format (YYYY-MM-DD VIDEO_ID + 4 필드 + keywords)
    - 한국어 UTF-8 보존 (대표님 호칭 + 한국어 feedback)
    - Keywords 자동 추출 (top-3 빈도)
    - Seed file 자동 생성 (d2_exception frontmatter)
    - 기존 entry 보존 (append-only)

Reference: .planning/phases/15-.../15-05-PLAN.md Task 01 behavior block.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.smoke.rate_video import (
    append_rating,
    ensure_seed,
    extract_keywords,
    format_entry,
    main,
)


class TestAppendRating:
    def test_valid_args_appends_h2_entry(self, tmp_path):
        mem = tmp_path / "feedback.md"
        append_rating(
            memory_path=mem,
            video_id="abc12345xyz",
            rating=4,
            feedback="좋습니다",
        )
        content = mem.read_text(encoding="utf-8")
        assert "## " in content
        assert "abc12345xyz" in content
        assert "rating: 4/5" in content

    def test_rating_below_range(self, tmp_path):
        with pytest.raises(ValueError, match=r"1~5"):
            append_rating(
                memory_path=tmp_path / "f.md",
                video_id="v",
                rating=0,
                feedback="x",
            )

    def test_rating_above_range(self, tmp_path):
        with pytest.raises(ValueError, match=r"대표님"):
            append_rating(
                memory_path=tmp_path / "f.md",
                video_id="v",
                rating=6,
                feedback="x",
            )

    def test_rating_not_integer_raises(self, tmp_path):
        with pytest.raises(ValueError):
            append_rating(
                memory_path=tmp_path / "f.md",
                video_id="v",
                rating="3",  # type: ignore[arg-type]
                feedback="x",
            )

    def test_feedback_korean_utf8_preserved(self, tmp_path):
        mem = tmp_path / "f.md"
        append_rating(
            memory_path=mem,
            video_id="v",
            rating=3,
            feedback="조명이 어두움, 음성 톤이 단조로움 (대표님)",
        )
        content = mem.read_text(encoding="utf-8")
        assert "대표님" in content
        assert "조명이 어두움" in content

    def test_preserves_existing_entries_on_append(self, tmp_path):
        mem = tmp_path / "f.md"
        append_rating(memory_path=mem, video_id="v1", rating=5, feedback="첫번째")
        append_rating(memory_path=mem, video_id="v2", rating=2, feedback="두번째")
        content = mem.read_text(encoding="utf-8")
        assert "v1" in content and "v2" in content
        assert content.count("## ") == 2

    def test_empty_feedback_raises(self, tmp_path):
        with pytest.raises(ValueError, match=r"feedback"):
            append_rating(
                memory_path=tmp_path / "f.md",
                video_id="v",
                rating=3,
                feedback="",
            )

    def test_empty_video_id_raises(self, tmp_path):
        with pytest.raises(ValueError, match=r"video_id"):
            append_rating(
                memory_path=tmp_path / "f.md",
                video_id="",
                rating=3,
                feedback="x",
            )


class TestExtractKeywords:
    def test_extracts_top_n_korean_nouns(self):
        kw = extract_keywords("조명이 어둡고 조명이 나쁩니다 음성이 좋습니다")
        assert isinstance(kw, list)
        assert len(kw) <= 3
        # "조명이" 가 가장 빈도 높은 토큰
        assert any("조명" in w for w in kw)

    def test_handles_no_korean(self):
        assert extract_keywords("no korean at all") == []

    def test_handles_empty_string(self):
        assert extract_keywords("") == []


class TestFormatEntry:
    def test_includes_all_required_fields(self):
        out = format_entry(
            today="2026-04-22",
            video_id="abc12345xyz",
            session_id="sess_01",
            niche="incidents",
            rating=3,
            feedback="조명 어두움",
        )
        assert "## 2026-04-22 abc12345xyz" in out
        assert "session_id: sess_01" in out
        assert "niche: incidents" in out
        assert "rating: 3/5" in out
        assert "feedback: 조명 어두움" in out
        assert "keywords:" in out

    def test_handles_missing_optional_fields(self):
        out = format_entry(
            today="2026-04-22",
            video_id="v",
            session_id=None,
            niche=None,
            rating=1,
            feedback="n",
        )
        assert "(미지정)" in out


class TestSeedFile:
    def test_missing_memory_creates_seed(self, tmp_path):
        mem = tmp_path / "new_feedback.md"
        assert not mem.exists()
        append_rating(memory_path=mem, video_id="v", rating=3, feedback="t")
        content = mem.read_text(encoding="utf-8")
        assert "d2_exception: true" in content
        assert "F-D2-EXCEPTION" in content

    def test_ensure_seed_noop_when_exists(self, tmp_path):
        mem = tmp_path / "f.md"
        mem.write_text("original content\n", encoding="utf-8")
        ensure_seed(mem, today="2026-04-22")
        assert mem.read_text(encoding="utf-8") == "original content\n"


class TestMainCLI:
    def test_main_exits_0_on_success(self, tmp_path, capsys):
        mem = tmp_path / "f.md"
        exit_code = main(
            [
                "--video-id", "abc12345xyz",
                "--rating", "3",
                "--feedback", "ok",
                "--memory-path", str(mem),
            ]
        )
        assert exit_code == 0
        assert mem.exists()

    def test_main_with_session_and_niche(self, tmp_path, capsys):
        mem = tmp_path / "f.md"
        exit_code = main(
            [
                "--video-id", "xyz",
                "--rating", "5",
                "--feedback", "훌륭합니다",
                "--session-id", "sess_20260422",
                "--niche", "incidents",
                "--memory-path", str(mem),
            ]
        )
        assert exit_code == 0
        content = mem.read_text(encoding="utf-8")
        assert "sess_20260422" in content
        assert "incidents" in content
