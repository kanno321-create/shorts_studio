"""Wave 0 smoke — scripts.publisher.exceptions import surface (CD-02 hierarchy)."""
from __future__ import annotations


def test_all_five_exceptions_importable():
    from scripts.publisher.exceptions import (
        AIDisclosureViolation,
        GitHubRemoteError,
        PublishLockViolation,
        PublishWindowViolation,
        SmokeTestCleanupFailure,
    )

    for cls in (
        PublishLockViolation,
        PublishWindowViolation,
        AIDisclosureViolation,
        SmokeTestCleanupFailure,
        GitHubRemoteError,
    ):
        assert issubclass(cls, RuntimeError)


def test_publish_lock_violation_carries_remaining_min():
    from scripts.publisher.exceptions import PublishLockViolation

    err = PublishLockViolation(remaining_min=120)
    assert err.remaining_min == 120
    assert "120 min" in str(err)


def test_publish_window_violation_carries_weekday_hour():
    from scripts.publisher.exceptions import PublishWindowViolation

    err = PublishWindowViolation(weekday=3, hour=9)
    assert err.weekday == 3
    assert err.hour == 9
    assert "weekday=3" in str(err)
    assert "hour=9" in str(err)


def test_smoke_cleanup_failure_carries_video_id():
    from scripts.publisher.exceptions import SmokeTestCleanupFailure

    err = SmokeTestCleanupFailure(video_id="abc123", reason="network")
    assert err.video_id == "abc123"
    assert err.reason == "network"
    assert "abc123" in str(err)


def test_github_remote_error_carries_status_body():
    from scripts.publisher.exceptions import GitHubRemoteError

    err = GitHubRemoteError(status_code=500, body="x" * 500)
    assert err.status_code == 500
    # Full body preserved on attribute; message truncates at 200 chars.
    assert len(err.body) == 500
    assert str(err).startswith("GitHub API error 500: ")


def test_ai_disclosure_violation_is_runtimeerror():
    from scripts.publisher.exceptions import AIDisclosureViolation

    err = AIDisclosureViolation("test")
    assert isinstance(err, RuntimeError)
