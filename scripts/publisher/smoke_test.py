"""Phase 8 Wave 5 smoke test — one-shot real YouTube upload + cleanup.

⚠️ USER APPROVAL REQUIRED. Per CONTEXT D-11 + User Option A:
- Uploads ``tests/phase08/fixtures/sample_shorts.mp4`` with
  ``privacyStatus="unlisted"`` (HARDCODED — no public/private code path).
- Waits up to 30s for ``processingStatus == "succeeded"`` polling
  ``videos.list(id=<vid>, part="status")`` every 2s (Pattern: RESEARCH Area 1).
- Calls ``videos.delete(id=<vid>).execute()`` — channel history cleanup,
  leaves zero public artefacts.
- Raises :class:`SmokeTestCleanupFailure` on non-2xx delete (manual delete
  via Studio required; the video_id is preserved on the exception).

Run once per Wave 5 gate to prove end-to-end chain: OAuth → build_insert_body →
publish → delete. All subsequent publishing goes through the normal
:func:`scripts.publisher.youtube_uploader.publish` orchestrator.

Usage
-----

Real API (post Wave 5 SMOKE-GATE approval)::

    python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup

MockYouTube dry-run (safe, no network)::

    python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup --dry-run

Preconditions (BLOCKING — checked before any API call)
------------------------------------------------------
- ``config/client_secret.json`` must exist (Google Cloud Console OAuth 2.0
  Desktop client download). Absent → :class:`FileNotFoundError` with
  instruction for 대표님.
- ``config/youtube_token.json`` is expected to already exist with a valid
  ``refresh_token``; :func:`scripts.publisher.oauth.get_credentials` will
  otherwise bootstrap via ``InstalledAppFlow.run_local_server`` — acceptable
  first-run fallback but NOT the smoke-test happy path.

Exit codes
----------
- ``0`` on clean cleanup.
- Non-zero on upload failure OR :class:`SmokeTestCleanupFailure` (cleanup
  non-2xx — manual delete required; video_id logged to stdout).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from scripts.publisher.exceptions import SmokeTestCleanupFailure
from scripts.publisher.oauth import CLIENT_SECRET_PATH, TOKEN_PATH, get_credentials
from scripts.publisher.youtube_uploader import publish


SMOKE_VIDEO_PATH = Path("tests/phase08/fixtures/sample_shorts.mp4")
PROCESSING_WAIT_SECONDS = 30
_POLL_INTERVAL_SECONDS = 2


def _build_smoke_plan() -> dict:
    """Minimal plan for smoke test — privacy=unlisted hardcoded.

    Mirrors the Phase 4 publisher upload plan shape consumed by
    :func:`scripts.publisher.youtube_uploader.publish` but with reach
    disabled (``embeddable=False``, ``publicStatsViewable=False``) and a
    timestamped title so channel history searches are trivial if cleanup
    ever fails.

    The ``ai_disclosure.syntheticMedia`` key is preserved per D-05 intent
    (AGENT.md plan schema) even though the canonical API field is
    translated by ``build_insert_body`` → ``status.containsSyntheticMedia``.
    """
    return {
        "snippet": {
            "title": f"SMOKE_TEST_{int(time.time())}",
            "description": "Phase 8 Wave 5 automated smoke test. Delete immediately.",
            "tags": ["smoke", "test"],
            "categoryId": "24",
            "defaultLanguage": "ko",
        },
        "status": {
            "privacyStatus": "unlisted",  # HARDCODED unlisted (D-11 safety)
            "embeddable": False,
            "publicStatsViewable": False,
        },
        "ai_disclosure": {"syntheticMedia": True},
        "production_metadata": {
            "script_seed": "smoke_test",
            "assets_origin": "smoke:test",
        },
        "funnel": {"pinned_comment": "smoke test — delete immediately"},
    }


def _wait_for_processing(
    youtube,
    video_id: str,
    *,
    seconds: int = PROCESSING_WAIT_SECONDS,
) -> None:
    """Poll ``videos.list`` until ``processingStatus=="succeeded"`` or timeout.

    Parameters
    ----------
    youtube
        The YouTube client (real Data API v3 or MockYouTube).
    video_id
        The uploaded video id returned by :func:`publish`.
    seconds
        Total wait budget. Default ``PROCESSING_WAIT_SECONDS`` (30).

    Semantics
    ---------
    - On timeout: return silently. Cleanup (videos.delete) MUST still run —
      the video exists on the channel whether processed or not, so cleanup
      is non-negotiable.
    - 2-second polling interval (YouTube API rate-friendly).
    """
    deadline = time.time() + seconds
    while time.time() < deadline:
        resp = youtube.videos().list(part="status", id=video_id).execute()
        items = resp.get("items", [])
        if items and items[0].get("status", {}).get("processingStatus") == "succeeded":
            return
        time.sleep(_POLL_INTERVAL_SECONDS)
    # Timeout: fall through — caller proceeds to delete regardless.


def _delete_video(youtube, video_id: str) -> None:
    """``videos.delete`` with any error → :class:`SmokeTestCleanupFailure`.

    The exception carries the ``video_id`` verbatim so the caller (orchestrator
    or stdout consumer) can surface it for manual cleanup via YouTube Studio.
    """
    try:
        youtube.videos().delete(id=video_id).execute()
    except Exception as exc:  # noqa: BLE001 — classified and re-raised
        raise SmokeTestCleanupFailure(video_id, str(exc)) from exc


def run_smoke_test(
    *,
    youtube=None,
    channel_id: str = "UCsmoke",
    privacy: str = "unlisted",
    cleanup: bool = True,
) -> str:
    """Orchestrate one smoke cycle; return the uploaded ``video_id``.

    Parameters
    ----------
    youtube
        Optional pre-built client (real or mock). When ``None`` the function
        builds a real ``googleapiclient.discovery`` client via
        :func:`get_credentials` — BLOCKING precondition: ``client_secret.json``
        must exist (RESEARCH Environment Availability).
    channel_id
        Channel id for the pinned comment. Default ``"UCsmoke"``.
    privacy
        Privacy status — MUST be ``"unlisted"``. Any other value raises
        :class:`ValueError` (D-11 safety: smoke test MUST NOT leave public
        artefacts).
    cleanup
        When True (default): wait 30s for processing + call ``videos.delete``.
        When False: upload only, leave the unlisted video on the channel
        (caller responsibility).

    Returns
    -------
    str
        The YouTube video id. Already-deleted when ``cleanup=True`` returns.

    Raises
    ------
    ValueError
        When ``privacy != "unlisted"``.
    FileNotFoundError
        When ``youtube is None`` and ``config/client_secret.json`` is missing.
    SmokeTestCleanupFailure
        When ``cleanup=True`` and ``videos.delete`` returns non-2xx.
    """
    if privacy != "unlisted":
        raise ValueError(
            "Smoke test MUST use privacyStatus='unlisted' (D-11 safety); "
            f"got {privacy!r}"
        )
    if youtube is None:
        # Precondition check (BLOCKING per RESEARCH Environment Availability).
        if not CLIENT_SECRET_PATH.exists():
            raise FileNotFoundError(
                f"{CLIENT_SECRET_PATH} missing — "
                "대표님 Google Cloud Console OAuth 2.0 Desktop client "
                "생성 후 config/client_secret.json 배치 필요"
            )
        creds = get_credentials()
        from googleapiclient.discovery import build  # lazy — test isolation
        youtube = build("youtube", "v3", credentials=creds)

    plan = _build_smoke_plan()
    # NOTE: publish() handles the full 5-gate chain (publish_lock → kst_window
    # → production_metadata → videos.insert → thumbnails.set →
    # commentThreads.insert → record_upload). SMOKE_VIDEO_PATH is reused as
    # the thumbnail path — the 1-byte fixture is accepted by thumbnails.set
    # as raw bytes (real-API thumbnail will fail validation but that is an
    # expected-warning path per Pitfall 9; the video upload itself succeeds).
    video_id = publish(
        youtube,
        plan,
        SMOKE_VIDEO_PATH,
        SMOKE_VIDEO_PATH,
        channel_id,
    )
    if cleanup:
        _wait_for_processing(youtube, video_id)
        _delete_video(youtube, video_id)
    return video_id


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Only ``--privacy=unlisted`` is accepted (argparse ``choices``). The
    ``--cleanup`` flag defaults to True; opt-out is explicit via
    ``--no-cleanup`` (argparse standard).
    """
    parser = argparse.ArgumentParser(
        description="Phase 8 Wave 5 smoke test — one-shot real YouTube upload + delete cleanup.",
    )
    parser.add_argument(
        "--privacy",
        default="unlisted",
        choices=["unlisted"],  # literally the only allowed value (D-11)
        help="privacyStatus (unlisted only — D-11 safety)",
    )
    parser.add_argument(
        "--cleanup",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Delete the smoke video after processing (default: enabled)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use MockYouTube instead of real Data API v3 (no network, no auth)",
    )
    args = parser.parse_args(argv)

    if args.dry_run:
        # Lazy import of the tests/phase08 mock so production `scripts/`
        # imports stay free of test-package dependencies.
        sys.path.insert(0, str(Path("tests/phase08").resolve()))
        from mocks.youtube_mock import MockYouTube  # noqa: E402
        yt = MockYouTube()
    else:
        yt = None

    vid = run_smoke_test(youtube=yt, privacy=args.privacy, cleanup=args.cleanup)
    print(f"SMOKE_VIDEO_ID: {vid}")
    print(
        "SMOKE_STATUS: cleanup-complete"
        if args.cleanup
        else "SMOKE_STATUS: upload-only"
    )
    return 0


if __name__ == "__main__":
    # Windows cp949 guard (Phase 6 STATE #28 + RESEARCH Pitfall 3).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())


__all__ = [
    "PROCESSING_WAIT_SECONDS",
    "SMOKE_VIDEO_PATH",
    "main",
    "run_smoke_test",
]
