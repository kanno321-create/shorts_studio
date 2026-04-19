"""Wave 4 PUB-05 — commentThreads.insert payload validation.

Per Plan 08-05 Task 8-05-02 + CONTEXT D-09:
The funnel pinned-comment path is the ONLY API mechanism we use for a
subscribe call-to-action; ``end_screen_subscribe_cta`` is plan-level
intent ONLY (RESEARCH Pitfall 7 — end-screens are NOT writable via Data
API v3, Studio UI only). These tests exercise ``publish()`` end-to-end
against ``MockYouTube`` and pin down the commentThreads.insert body
shape (channelId, videoId, topLevelComment.snippet.textOriginal).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tests/phase08/mocks/ — no package __init__ to avoid Phase 4/5/6/7 collision
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mocks.youtube_mock import MockYouTube   # type: ignore[import-not-found]

from scripts.publisher.youtube_uploader import publish


@pytest.fixture
def base_plan():
    return {
        "snippet": {
            "title": "탐정 시로 Ep.007",
            "description": "미제사건 추리 쇼츠",
            "tags": ["미제사건", "추리"],
            "categoryId": "24",
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",   # Pitfall 5 — should be dropped
        },
        "status": {"privacyStatus": "public"},
        "ai_disclosure": {"syntheticMedia": True},
        "production_metadata": {
            "script_seed": "s",
            "assets_origin": "kling:primary",
        },
        "funnel": {
            "pinned_comment": "구독해주세요 대표님!",
            "end_screen_subscribe_cta": True,
        },
        "_media_body": object(),
        "_thumb_body": object(),
    }


def test_pinned_comment_recorded_in_mock(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    """Monday 21:00 KST + no prior lock → publish proceeds; pinned comment set."""
    from scripts.publisher import kst_window
    monkeypatch.setattr(kst_window, "assert_in_window", lambda **kw: None)

    m = MockYouTube()
    video_id = publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    assert video_id.startswith("mock_video_id_")
    assert video_id in m._pinned_comments
    assert m._pinned_comments[video_id] == "구독해주세요 대표님!"


def test_default_pin_text_when_funnel_omitted(
        sample_mp4_path, monkeypatch, tmp_publish_lock):
    from scripts.publisher import kst_window
    monkeypatch.setattr(kst_window, "assert_in_window", lambda **kw: None)
    plan = {
        "snippet": {"description": ""},
        "status": {"privacyStatus": "public"},
        "production_metadata": {"script_seed": "s", "assets_origin": "kling:primary"},
        "_media_body": object(),
        "_thumb_body": object(),
    }
    m = MockYouTube()
    vid = publish(m, plan, sample_mp4_path, sample_mp4_path, "c1")
    assert m._pinned_comments[vid] == "구독해주세요!"


def test_comment_includes_channel_and_video_ids(
        sample_mp4_path, base_plan, monkeypatch, tmp_publish_lock):
    from scripts.publisher import kst_window
    monkeypatch.setattr(kst_window, "assert_in_window", lambda **kw: None)

    captured = []
    m = MockYouTube()

    # Spy on commentThreads() — wrap the real Stub so we record the body.
    real_comment_threads = m.commentThreads

    class _SpyThreads:
        def insert(self, *, part, body):
            captured.append({"part": part, "body": body})
            return real_comment_threads().insert(part=part, body=body)

    monkeypatch.setattr(m, "commentThreads", lambda: _SpyThreads())

    publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_XYZ")
    assert len(captured) == 1
    body = captured[0]["body"]
    assert body["snippet"]["channelId"] == "channel_XYZ"
    assert body["snippet"]["videoId"].startswith("mock_video_id_")
    assert body["snippet"]["topLevelComment"]["snippet"]["textOriginal"]


def test_comment_part_is_snippet(
        sample_mp4_path, base_plan, monkeypatch, tmp_publish_lock):
    """commentThreads.insert requires part='snippet' per Data API v3."""
    from scripts.publisher import kst_window
    monkeypatch.setattr(kst_window, "assert_in_window", lambda **kw: None)

    captured = []
    m = MockYouTube()
    real_comment_threads = m.commentThreads

    class _SpyThreads:
        def insert(self, *, part, body):
            captured.append(part)
            return real_comment_threads().insert(part=part, body=body)

    monkeypatch.setattr(m, "commentThreads", lambda: _SpyThreads())
    publish(m, base_plan, sample_mp4_path, sample_mp4_path, "c1")
    assert captured == ["snippet"]
