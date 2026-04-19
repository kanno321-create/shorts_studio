"""MockYouTube contract tests — Phase 7 Correction 2 default safety inheritance.

Per CONTEXT D-10: allow_fault_injection defaults to False; fault injection is a
strict opt-in. Tests verify:
- default safety: fault mode set but allow_fault_injection=False → no raise
- explicit opt-in: allow_fault_injection=True + _fault_mode → raises
- happy path resource shapes (videos/thumbnails/commentThreads)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Per Phase 7 Plan 07-02 precedent — sys.path insertion so `from mocks.X import Y`
# resolves without requiring a tests/ package (`tests/__init__.py` would alter
# Phase 4/5/6/7 resolution and is out of scope).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mocks.youtube_mock import MockYouTube  # noqa: E402


def test_default_allow_fault_injection_is_false():
    m = MockYouTube()
    assert m._allow_fault_injection is False, (
        "D-10 + Phase 7 Correction 2 default: production-safe mocks MUST NOT "
        "inject faults by default"
    )


def test_videos_insert_resumable_happy_path():
    m = MockYouTube()
    req = m.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": "t"}},
        media_body=object(),
    )
    status, resp = req.next_chunk()
    assert status is None
    assert resp["id"].startswith("mock_video_id_")
    assert m._upload_count == 1


def test_videos_insert_increments_on_consecutive_calls():
    m = MockYouTube()
    for _ in range(3):
        m.videos().insert(part="snippet", body={}, media_body=object()).next_chunk()
    assert m._upload_count == 3
    assert len(m._video_ids) == 3
    assert m._video_ids[0] != m._video_ids[1]


def test_videos_delete_records():
    m = MockYouTube()
    m.videos().delete(id="vid_123").execute()
    assert "vid_123" in m._deleted


def test_videos_list_returns_succeeded_processing():
    m = MockYouTube()
    resp = m.videos().list(part="status", id="vid_123").execute()
    assert resp["items"][0]["status"]["processingStatus"] == "succeeded"
    assert resp["items"][0]["status"]["uploadStatus"] == "processed"


def test_thumbnails_set_returns_shape():
    m = MockYouTube()
    resp = m.thumbnails().set(videoId="vid_123", media_body=object()).execute()
    assert resp["kind"] == "youtube#thumbnailSetResponse"
    assert resp["items"][0]["videoId"] == "vid_123"


def test_comment_threads_insert_records_pin():
    m = MockYouTube()
    body = {
        "snippet": {
            "channelId": "chan",
            "videoId": "vid_123",
            "topLevelComment": {"snippet": {"textOriginal": "구독!"}},
        }
    }
    m.commentThreads().insert(part="snippet", body=body).execute()
    assert m._pinned_comments["vid_123"] == "구독!"


def test_fault_injection_explicit_opt_in_raises():
    m = MockYouTube(allow_fault_injection=True)
    m._fault_mode = "httplib2"
    with pytest.raises(Exception):
        m.videos().insert(part="snippet", body={}, media_body=object()).next_chunk()


def test_fault_injection_default_off_does_not_raise():
    m = MockYouTube()
    # Even with _fault_mode set, allow_fault_injection defaults False → no raise.
    m._fault_mode = "httplib2"
    status, resp = m.videos().insert(
        part="snippet", body={}, media_body=object()
    ).next_chunk()
    assert "id" in resp


def test_fault_injection_http_500_mode():
    m = MockYouTube(allow_fault_injection=True)
    m._fault_mode = "http_500"
    with pytest.raises(Exception):
        m.videos().insert(part="snippet", body={}, media_body=object()).next_chunk()
