"""Wave 4 PUB-02 + PUB-05 — End-to-end publish() against MockYouTube.

Exercises the full 5-gate chain:
  1. assert_can_publish  (48h+jitter filesystem lock)
  2. assert_in_window    (KST weekday 20-23 / weekend 12-15)
  3. inject_into_description + checksum
  4. build_insert_body → videos.insert → resumable_upload
  5. thumbnails.set → commentThreads.insert → record_upload

Every test freezes kst_window (monkeypatch on the source module, which
youtube_uploader calls through by module reference so the patch takes
effect) and uses tmp_publish_lock for per-test isolation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# tests/phase08/mocks/ — no package __init__ to avoid Phase 4-7 collision.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mocks.youtube_mock import MockYouTube   # type: ignore[import-not-found]

import scripts.publisher.kst_window as kstw
import scripts.publisher.publish_lock as pl
from scripts.publisher.youtube_uploader import build_insert_body, publish


@pytest.fixture
def base_plan():
    return {
        "snippet": {
            "title": "탐정 시로 Ep.007 — 범인의 결정적 실수",
            "description": "미제사건 추리 쇼츠",
            "tags": ["미제사건", "추리"],
            "categoryId": "24",
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",   # Pitfall 5 — should be dropped
        },
        "status": {
            "privacyStatus": "public",
            "embeddable": True,
            "publicStatsViewable": True,
        },
        "ai_disclosure": {"syntheticMedia": True, "generated_by_ai": True},
        "production_metadata": {
            "script_seed": "det_ep007_2026",
            "assets_origin": "kling:primary",
        },
        "funnel": {
            "pinned_comment": "다음 에피소드 예고편: 구독!",
            "end_screen_subscribe_cta": True,
        },
        "_media_body": object(),
        "_thumb_body": object(),
    }


def test_build_insert_body_sets_contains_synthetic_media_true(base_plan):
    body = build_insert_body(base_plan)
    assert body["status"]["containsSyntheticMedia"] is True


def test_build_insert_body_drops_default_audio_language(base_plan):
    body = build_insert_body(base_plan)
    assert "defaultAudioLanguage" not in body["snippet"], (
        "Pitfall 5: defaultAudioLanguage must be dropped"
    )


def test_build_insert_body_truncates_title_to_100(base_plan):
    base_plan["snippet"]["title"] = "x" * 200
    body = build_insert_body(base_plan)
    assert len(body["snippet"]["title"]) == 100


def test_build_insert_body_truncates_description_to_5000(base_plan):
    base_plan["snippet"]["description"] = "y" * 10000
    body = build_insert_body(base_plan)
    assert len(body["snippet"]["description"]) == 5000


def test_build_insert_body_only_snippet_and_status(base_plan):
    body = build_insert_body(base_plan)
    assert set(body.keys()) == {"snippet", "status"}


def test_publish_end_to_end_counts_three_api_calls(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)
    m = MockYouTube()
    vid = publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    assert m._upload_count == 1
    assert len(m._pinned_comments) == 1
    assert vid in m._pinned_comments


def test_publish_records_lock_after_upload(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)
    m = MockYouTube()
    publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    assert tmp_publish_lock.exists()
    data = json.loads(tmp_publish_lock.read_text(encoding="utf-8"))
    assert "last_upload_iso" in data
    assert "jitter_applied_min" in data


def test_publish_injects_metadata_with_correct_checksum(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    """Verifies the sha256 streaming implementation produces the expected
    hash for the 1-byte fixture (b'0' → 5feceb66...).
    """
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)

    captured_body: dict = {}
    m = MockYouTube()
    real_videos = m.videos

    class _SpyVideos:
        def insert(self, *, part, body, media_body):
            captured_body.update(body)
            return real_videos().insert(part=part, body=body, media_body=media_body)

    monkeypatch.setattr(m, "videos", lambda: _SpyVideos())

    publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    desc = captured_body["snippet"]["description"]
    assert "<!-- production_metadata" in desc
    # sha256 of b"0" = 5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9
    assert (
        "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9"
        in desc
    )


def test_publish_call_order_lock_window_insert(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    """assert_can_publish MUST be called BEFORE assert_in_window which MUST
    be called BEFORE videos.insert. Proves 5-gate chain ordering.
    """
    order: list[str] = []
    monkeypatch.setattr(pl, "assert_can_publish",
                        lambda **kw: order.append("lock"))
    monkeypatch.setattr(kstw, "assert_in_window",
                        lambda **kw: order.append("window"))
    m = MockYouTube()
    real_videos = m.videos

    class _Spy:
        def insert(self, **kw):
            order.append("insert")
            return real_videos().insert(**kw)

    monkeypatch.setattr(m, "videos", lambda: _Spy())
    publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    assert order[0] == "lock"
    assert order[1] == "window"
    assert order[2] == "insert"


def test_publish_raises_when_lock_active(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    """Existing lock within 48h must block publish() — PublishLockViolation
    propagates out unchanged.
    """
    from datetime import datetime, timedelta, timezone

    tmp_publish_lock.write_text(json.dumps({
        "last_upload_iso": (
            datetime.now(timezone.utc) - timedelta(hours=10)
        ).isoformat(),
        "jitter_applied_min": 0,
        "_schema": 1,
    }), encoding="utf-8")
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)
    m = MockYouTube()
    from scripts.publisher.exceptions import PublishLockViolation
    with pytest.raises(PublishLockViolation):
        publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")


def test_publish_raises_when_outside_kst_window(
        sample_mp4_path, base_plan, tmp_publish_lock):
    """No kst_window monkeypatch — assert_in_window may fail depending on
    when the test runs. We explicitly call through to the real assertion
    with a frozen clock outside the window to prove propagation.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from scripts.publisher.exceptions import PublishWindowViolation

    # 03:00 KST Monday — deep outside any valid window.
    outside = datetime(2026, 4, 20, 3, 0, 0, tzinfo=ZoneInfo("Asia/Seoul"))

    # Patch datetime.now within kst_window to return 'outside'.
    import scripts.publisher.kst_window as kstw_mod

    class _FakeDateTime:
        @staticmethod
        def now(tz=None):
            return outside.astimezone(tz) if tz else outside

    import datetime as _dt_mod
    original_datetime = kstw_mod.datetime
    try:
        kstw_mod.datetime = _FakeDateTime   # type: ignore[assignment]
        m = MockYouTube()
        with pytest.raises(PublishWindowViolation):
            publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
    finally:
        kstw_mod.datetime = original_datetime   # type: ignore[assignment]


def test_publish_raises_on_ai_disclosure_violation(
        sample_mp4_path, base_plan, tmp_publish_lock, monkeypatch):
    """If build_status_block is corrupted to emit something other than
    literal True, assert_synthetic_media_true must propagate
    AIDisclosureViolation BEFORE any API call.
    """
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)

    import scripts.publisher.youtube_uploader as uploader_mod
    from scripts.publisher.exceptions import AIDisclosureViolation

    def _bad_status_block(**_kw):
        return {
            "privacyStatus": "public",
            "containsSyntheticMedia": False,   # CORRUPT
            "embeddable": True,
            "publicStatsViewable": True,
            "selfDeclaredMadeForKids": False,
            "license": "youtube",
        }

    monkeypatch.setattr(uploader_mod, "build_status_block", _bad_status_block)
    m = MockYouTube()
    with pytest.raises(AIDisclosureViolation):
        publish(m, base_plan, sample_mp4_path, sample_mp4_path, "channel_1")
