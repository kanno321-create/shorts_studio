"""Wave 5 SMOKE TEST — MockYouTube coverage of smoke_test.py paths.

Does NOT invoke the real YouTube Data API v3 — that path is gated by user
approval in Task 1 and executed once out-of-band by the orchestrator.

Covers (per Plan 08-06 Task 2 acceptance criteria):
  1. Happy path: publish → 30s wait fast-path → videos.delete cleanup.
  2. Unlisted-only enforcement: privacy="public" / "private" → ValueError.
  3. Skip cleanup: cleanup=False leaves the video in MockYouTube state.
  4. Delete failure: faulty videos.delete → SmokeTestCleanupFailure.
  5. _wait_for_processing fast-path (first poll succeeded).
  6. _wait_for_processing timeout tolerance (never succeeds → no crash).
  7. _build_smoke_plan invariants (unlisted + embeddable=False + syntheticMedia).
  8. main() --dry-run routes through MockYouTube (no real creds loaded).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# tests/phase08/mocks/ — no package __init__ to match Phase 4-7 precedent.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mocks.youtube_mock import MockYouTube  # type: ignore[import-not-found]

import scripts.publisher.smoke_test as st
from scripts.publisher.exceptions import SmokeTestCleanupFailure


@pytest.fixture(autouse=True)
def freeze_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke tests run at any hour — bypass KST peak window enforcement.

    youtube_uploader.publish() calls kst_window.assert_in_window via module
    qualified name (08-05 Deviation 2); monkeypatching the source module
    takes effect on the qualified lookup.
    """
    import scripts.publisher.kst_window as kstw
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fast-path ``time.sleep`` in _wait_for_processing to keep tests quick.

    Only patches the smoke_test module's bound ``time`` reference; wall-clock
    ``time.time()`` is preserved so the deadline-based loop still terminates.
    """
    monkeypatch.setattr(st.time, "sleep", lambda s: None)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_happy_path_upload_and_delete(tmp_publish_lock: Path) -> None:
    """publish → wait (succeeded first poll) → videos.delete — all green."""
    m = MockYouTube()
    vid = st.run_smoke_test(
        youtube=m,
        channel_id="UCsmoke",
        privacy="unlisted",
        cleanup=True,
    )
    assert vid.startswith("mock_video_id_"), f"unexpected id shape: {vid}"
    assert vid in m._deleted, "videos.delete MUST be called for cleanup"
    assert m._upload_count == 1


# ---------------------------------------------------------------------------
# Unlisted-only enforcement (D-11 safety)
# ---------------------------------------------------------------------------
def test_privacy_public_raises_value_error(tmp_publish_lock: Path) -> None:
    m = MockYouTube()
    with pytest.raises(ValueError) as exc_info:
        st.run_smoke_test(youtube=m, privacy="public", cleanup=True)
    # Message must reference the unlisted constraint for actionable diagnostics.
    assert "unlisted" in str(exc_info.value)
    # No upload should have happened before the guard.
    assert m._upload_count == 0


def test_privacy_private_raises_value_error(tmp_publish_lock: Path) -> None:
    m = MockYouTube()
    with pytest.raises(ValueError):
        st.run_smoke_test(youtube=m, privacy="private", cleanup=True)
    assert m._upload_count == 0


# ---------------------------------------------------------------------------
# cleanup=False (upload-only path)
# ---------------------------------------------------------------------------
def test_cleanup_false_skips_delete(tmp_publish_lock: Path) -> None:
    m = MockYouTube()
    vid = st.run_smoke_test(
        youtube=m,
        privacy="unlisted",
        cleanup=False,
    )
    assert vid not in m._deleted, "cleanup=False must NOT call videos.delete"
    assert vid.startswith("mock_video_id_")
    assert m._upload_count == 1


# ---------------------------------------------------------------------------
# Delete failure → SmokeTestCleanupFailure
# ---------------------------------------------------------------------------
def test_delete_failure_raises_smoke_cleanup_failure(
    tmp_publish_lock: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Faulty videos.delete → SmokeTestCleanupFailure carrying video_id + reason."""
    m = MockYouTube()
    original_videos = m.videos  # bound method captured BEFORE monkeypatch

    class _FaultyVideos:
        """Delegate insert+list to the real stub, but crash on delete."""

        def insert(self, **kw: Any) -> Any:
            return original_videos().insert(**kw)

        def delete(self, *, id: str) -> Any:  # noqa: A002 — matches real API
            class _Req:
                def execute(inner_self) -> None:
                    raise RuntimeError("API error 403")

            return _Req()

        def list(self, **kw: Any) -> Any:
            return original_videos().list(**kw)

    monkeypatch.setattr(m, "videos", lambda: _FaultyVideos())

    with pytest.raises(SmokeTestCleanupFailure) as exc_info:
        st.run_smoke_test(youtube=m, privacy="unlisted", cleanup=True)
    assert exc_info.value.video_id.startswith("mock_video_id_")
    assert "403" in exc_info.value.reason


# ---------------------------------------------------------------------------
# _wait_for_processing semantics
# ---------------------------------------------------------------------------
def test_wait_for_processing_returns_on_succeeded_immediately(
    tmp_publish_lock: Path,
) -> None:
    """First poll already shows succeeded — must return without the full wait."""
    m = MockYouTube()
    # MockYouTube.list() returns processingStatus=succeeded by default.
    st._wait_for_processing(m, "vid_1", seconds=30)  # must not hang


def test_wait_for_processing_timeout_no_crash(
    tmp_publish_lock: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Timeout path: videos.list never reports succeeded — no crash, proceed."""
    m = MockYouTube()

    class _PendingVideos:
        def list(self, **kw: Any) -> Any:
            class _Req:
                def execute(inner_self) -> dict:
                    return {"items": [{"status": {"processingStatus": "pending"}}]}

            return _Req()

    monkeypatch.setattr(m, "videos", lambda: _PendingVideos())
    # Short budget so the deadline loop exits quickly under no_sleep.
    st._wait_for_processing(m, "vid_1", seconds=1)  # MUST NOT raise


# ---------------------------------------------------------------------------
# _build_smoke_plan invariants
# ---------------------------------------------------------------------------
def test_smoke_plan_sets_unlisted_embeddable_false() -> None:
    plan = st._build_smoke_plan()
    assert plan["status"]["privacyStatus"] == "unlisted"
    assert plan["status"]["embeddable"] is False
    assert plan["status"]["publicStatsViewable"] is False


def test_smoke_plan_has_synthetic_media_disclosure() -> None:
    """PUB-01 anchor — AI disclosure cannot be bypassed even for smoke."""
    plan = st._build_smoke_plan()
    assert plan["ai_disclosure"]["syntheticMedia"] is True


def test_smoke_plan_title_has_timestamp() -> None:
    plan = st._build_smoke_plan()
    assert plan["snippet"]["title"].startswith("SMOKE_TEST_")


def test_smoke_plan_has_production_metadata_required_fields() -> None:
    """PUB-04 schema — script_seed + assets_origin required (pipeline_version
    + checksum are injected by publish()).
    """
    plan = st._build_smoke_plan()
    pm = plan["production_metadata"]
    assert pm["script_seed"] == "smoke_test"
    assert pm["assets_origin"] == "smoke:test"


def test_smoke_plan_has_pinned_comment() -> None:
    """D-09 funnel — pinned comment is the smoke-safe subscribe substrate."""
    plan = st._build_smoke_plan()
    assert "pinned_comment" in plan["funnel"]
    assert "smoke" in plan["funnel"]["pinned_comment"].lower()


# ---------------------------------------------------------------------------
# main() CLI dry-run
# ---------------------------------------------------------------------------
def test_main_dry_run_uses_mock_youtube(
    tmp_publish_lock: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--dry-run MUST use MockYouTube and MUST NOT load real Credentials."""

    def _fail_on_real_creds(**kw: Any) -> None:
        pytest.fail("Real credentials MUST NOT load under --dry-run")

    monkeypatch.setattr(st, "get_credentials", _fail_on_real_creds)

    rc = st.main(["--privacy=unlisted", "--cleanup", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SMOKE_VIDEO_ID:" in out
    assert "SMOKE_STATUS: cleanup-complete" in out


def test_main_dry_run_no_cleanup_prints_upload_only(
    tmp_publish_lock: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--no-cleanup path prints upload-only status and still skips creds."""

    monkeypatch.setattr(
        st,
        "get_credentials",
        lambda **kw: pytest.fail("Real credentials must not load under --dry-run"),
    )

    rc = st.main(["--privacy=unlisted", "--no-cleanup", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SMOKE_VIDEO_ID:" in out
    assert "SMOKE_STATUS: upload-only" in out


# ---------------------------------------------------------------------------
# Real-path precondition guard (no network required)
# ---------------------------------------------------------------------------
def test_real_path_raises_when_client_secret_missing(
    tmp_publish_lock: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When youtube=None and client_secret.json absent → FileNotFoundError.

    Asserts the BLOCKING precondition from RESEARCH Environment Availability —
    the smoke CLI refuses to call the real API without OAuth credentials.
    """
    missing = Path("this/path/does/not/exist/client_secret.json")
    monkeypatch.setattr(st, "CLIENT_SECRET_PATH", missing)
    with pytest.raises(FileNotFoundError) as exc_info:
        st.run_smoke_test(youtube=None, privacy="unlisted", cleanup=False)
    assert "client_secret.json" in str(exc_info.value)
