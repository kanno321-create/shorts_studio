"""scripts.publisher exceptions — Phase 8 CD-02 hierarchy.

Mirrors the scripts/orchestrator/ exception style (CircuitBreakerOpenError +
OrchestratorError): RuntimeError subclasses with structured attributes carried
through __init__ + a narrative message suitable for journalling.

SeleniumForbidden already lives in pre_tool_use.py Hook enforcement layer —
NOT duplicated here per CONTEXT CD-02.
"""
from __future__ import annotations


class PublishLockViolation(RuntimeError):
    """48h+ jitter window not yet elapsed. Carries remaining_min: int."""

    def __init__(self, remaining_min: int) -> None:
        self.remaining_min = remaining_min
        super().__init__(f"Publish lock active, {remaining_min} min remaining")


class PublishWindowViolation(RuntimeError):
    """Outside KST weekday 20-23 or weekend 12-15 window (CONTEXT D-07)."""

    def __init__(self, weekday: int, hour: int) -> None:
        self.weekday = weekday
        self.hour = hour
        super().__init__(f"Outside KST window (weekday={weekday} hour={hour})")


class AIDisclosureViolation(RuntimeError):
    """containsSyntheticMedia not hardcoded True (PUB-01 anchor failure).

    Raised when upload payload builder emits a body where
    ``status.containsSyntheticMedia`` is not literal True. The anchor test
    (Plan 08-05 Task 8-05-04) also enforces this statically via AST — this
    exception is the runtime last-line defense.
    """


class SmokeTestCleanupFailure(RuntimeError):
    """videos.delete after unlisted upload failed (Wave 5 cleanup).

    Carries the YouTube video_id so callers can surface it for manual
    cleanup if the automated delete path fails.
    """

    def __init__(self, video_id: str, reason: str) -> None:
        self.video_id = video_id
        self.reason = reason
        super().__init__(f"Smoke cleanup failed for {video_id}: {reason}")


class GitHubRemoteError(RuntimeError):
    """GitHub REST API non-2xx non-422 response.

    Carries HTTP status_code + response body (truncated at 200 chars in the
    message but the full body is preserved on the attribute for logging).
    """

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"GitHub API error {status_code}: {body[:200]}")


__all__ = [
    "PublishLockViolation",
    "PublishWindowViolation",
    "AIDisclosureViolation",
    "SmokeTestCleanupFailure",
    "GitHubRemoteError",
]
