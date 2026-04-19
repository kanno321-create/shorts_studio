"""YouTube Data API v3 uploader — Phase 8 PUB-02 + PUB-05 D-09.

Orchestrates the end-to-end publish path: publish_lock → KST window →
AI disclosure hardcoded True → ``videos.insert`` resumable upload →
``thumbnails.set`` → ``commentThreads.insert`` pinned comment →
``record_upload`` lock write.

Three deviations from the Phase 4 publisher AGENT.md are RESEARCH-anchored
and corrected HERE at the body-build boundary, not at the agent prompt
layer::

- **Pitfall 5 (snippet.defaultAudioLanguage)** — NOT a writable snippet
  field per the Data API v3 official docs. AGENT.md may emit it upstream;
  ``build_insert_body`` drops it silently with an inline comment.
- **Pitfall 6 (ai_disclosure.syntheticMedia custom key)** — AGENT.md
  uses a non-canonical key; the canonical Data API v3 field name is
  ``status.containsSyntheticMedia`` (added 2024-10-30). Translation
  happens via :func:`scripts.publisher.ai_disclosure.build_status_block`
  which hardcodes the flag to literal ``True`` (D-05 physical-removal).
- **Pitfall 7 (funnel.end_screen_subscribe_cta / captions.insert)** —
  End-screens are NOT writable via Data API v3 (YouTube Studio UI only);
  ``captions.insert`` is for subtitles, not end-screens. We implement
  the funnel intent via pinned comment + description CTA ONLY (D-09).

Selenium / playwright / webdriver are NEVER imported (AF-8 perma-ban);
the ANCHOR C test asserts this by grep + AST. The resumable-upload loop
introspects errors by attribute lookup on ``exc.resp.status`` without
importing googleapiclient errors, so the module stays test-isolated.

Lazy imports for ``googleapiclient.http.MediaFileUpload`` are used so
tests can pass sentinel objects via the ``_media_body`` / ``_thumb_body``
plan hooks without requiring the real google client library.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path
from typing import Any, Protocol

from scripts.publisher import kst_window as _kst_window
from scripts.publisher import publish_lock as _publish_lock
from scripts.publisher.ai_disclosure import (
    assert_synthetic_media_true,
    build_status_block,
)
from scripts.publisher.production_metadata import (
    PIPELINE_VERSION,
    compute_checksum,
    inject_into_description,
)


# UTF-8 safeguard for Windows cp949 per Phase 6 STATE #28 + RESEARCH Pitfall 3.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


RETRIABLE_STATUS_CODES = (500, 502, 503, 504)
MAX_RETRIES = 10

# YouTube Data API v3 hard limits (per official docs 2026-04)
_TITLE_MAX_CHARS = 100
_DESCRIPTION_MAX_CHARS = 5000

# Default pinned-comment CTA when plan omits one (D-09 funnel substrate).
_DEFAULT_PIN_TEXT = "구독해주세요!"


class YouTubeClient(Protocol):
    """Structural type for the googleapiclient discovery client.

    Matches the surface used by ``MockYouTube`` (tests/phase08/mocks/) so
    the real ``googleapiclient.discovery.build("youtube","v3",...)`` and
    the mock are drop-in interchangeable.
    """

    def videos(self) -> Any: ...
    def thumbnails(self) -> Any: ...
    def commentThreads(self) -> Any: ...


def build_insert_body(plan: dict[str, Any]) -> dict[str, Any]:
    """Translate a Phase 4 publisher upload plan JSON → Data API v3 body.

    Corrections applied here (not at agent-prompt layer):

    - ``snippet.title`` truncated to 100 chars (Data API v3 hard cap).
    - ``snippet.description`` truncated to 5000 chars.
    - ``snippet.defaultAudioLanguage`` **silently dropped** — Pitfall 5:
      NOT a writable snippet field per official Data API v3 spec.
      AGENT.md may emit it; we filter at this boundary.
    - ``status.containsSyntheticMedia`` hardcoded ``True`` via
      :func:`build_status_block` (D-05 physical-removal). Pitfall 6:
      AGENT.md's ``ai_disclosure.syntheticMedia`` custom key is NOT
      canonical; the real field is ``status.containsSyntheticMedia``.
    - ``plan['funnel']['end_screen_subscribe_cta']`` is NOT mapped to
      any API call — Pitfall 7: end-screens are YouTube Studio UI only.
      The funnel intent is satisfied via pinned comment + description
      CTA in :func:`publish` (D-09).

    Parameters
    ----------
    plan
        Phase 4 publisher upload plan JSON. Required keys:
        ``snippet`` (title/description/tags/categoryId/defaultLanguage),
        ``status`` (privacyStatus). Missing keys default to sensible
        public-Shorts values.

    Returns
    -------
    dict
        Body shape for ``youtube.videos().insert(part="snippet,status",
        body=<this>)``. Only ``snippet`` + ``status`` keys — no extras.
    """
    snippet_in = plan.get("snippet", {})
    snippet = {
        "title": snippet_in.get("title", "")[:_TITLE_MAX_CHARS],
        "description": snippet_in.get("description", "")[:_DESCRIPTION_MAX_CHARS],
        "tags": snippet_in.get("tags", []),
        "categoryId": snippet_in.get("categoryId", "24"),
        "defaultLanguage": snippet_in.get("defaultLanguage", "ko"),
        # NOTE: defaultAudioLanguage intentionally NOT copied — Pitfall 5:
        # it is NOT a writable snippet field per YouTube Data API v3 docs.
        # AGENT.md may emit it from the Phase 4 plan; we drop at this
        # boundary so the upstream spec stays descriptive (not normative).
    }

    status_in = plan.get("status", {})
    status = build_status_block(
        privacy_status=status_in.get("privacyStatus", "public"),
        embeddable=status_in.get("embeddable", True),
        public_stats_viewable=status_in.get("publicStatsViewable", True),
    )
    # Runtime last-line defence — ai_disclosure module hardcodes True,
    # but if an attacker ever dict.update()s it away we want to crash
    # BEFORE the insert hits YouTube servers. Strict `is True` identity.
    assert_synthetic_media_true(status)

    # Pitfall 7 ref: plan['funnel']['end_screen_subscribe_cta'] is NOT an
    # API call — Data API v3 has no endScreen body field. The funnel
    # intent is implemented in publish() via commentThreads.insert
    # (pinned comment) + description CTA text (D-09). Silently ignored
    # here so AGENT.md can continue to emit it as a plan-level intent.
    return {"snippet": snippet, "status": status}


def resumable_upload(insert_request: Any) -> str:
    """Drive a resumable upload request to completion; return ``videoId``.

    Exponential backoff on retriable HTTP status codes (500/502/503/504)
    via ``getattr(exc.resp, 'status', None)`` introspection — we do NOT
    import ``googleapiclient.errors.HttpError`` so the module stays
    importable without the google client library installed (tests rely
    on this).

    Parameters
    ----------
    insert_request
        The object returned by ``youtube.videos().insert(...)``. Must
        expose ``.next_chunk() -> tuple[status|None, response|None]``.
        Real Data API and ``MockYouTube._InsertRequest`` both satisfy.

    Returns
    -------
    str
        The ``response["id"]`` — YouTube videoId (11-char base64url).

    Raises
    ------
    RuntimeError
        On retry-budget exhaustion (``MAX_RETRIES=10``) OR on unexpected
        response shape (missing ``"id"`` key).
    Exception
        Non-retriable upstream errors propagate unchanged — we do NOT
        swallow them (Hook-enforced no-silent-except policy).
    """
    response: Any = None
    retry = 0
    while response is None:
        try:
            _status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    return response["id"]
                raise RuntimeError(f"Unexpected upload response: {response}")
        except Exception as exc:   # noqa: BLE001 — classified below via status
            status_code = getattr(getattr(exc, "resp", None), "status", None)
            if status_code not in RETRIABLE_STATUS_CODES:
                raise   # non-retriable — propagate to caller
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError(
                    f"MAX_RETRIES={MAX_RETRIES} exceeded "
                    f"(last status={status_code})"
                ) from exc
            time.sleep(random.random() * (2 ** retry))
    # Unreachable — loop only exits via return or raise. Satisfies mypy.
    raise RuntimeError("resumable_upload: unreachable")


def publish(
    youtube: YouTubeClient,
    plan: dict[str, Any],
    video_path: Path,
    thumbnail_path: Path,
    channel_id: str,
) -> str:
    """End-to-end publish orchestrator — returns uploaded ``videoId``.

    Execution order (5-gate chain, enforced by :func:`publish_call_order`
    test in :mod:`tests.phase08.test_uploader_mocked_e2e`):

    1. ``assert_can_publish()`` — 48h+jitter filesystem lock (PUB-03).
    2. ``assert_in_window()`` — KST weekday 20-23 / weekend 12-15 (PUB-03).
    3. ``inject_into_description()`` + checksum compute (PUB-04).
    4. ``build_insert_body`` → ``videos.insert`` resumable upload (PUB-02).
    5. ``thumbnails.set`` (custom thumbnail) → ``commentThreads.insert``
       (pinned CTA, PUB-05 D-09) → ``record_upload()``.

    No step is retried outside the resumable loop — if the lock check
    fails we never touch YouTube; if the insert succeeds but the
    thumbnail/pin steps fail, the video is up but the funnel is
    incomplete (caller responsibility to surface for manual fixup).

    Parameters
    ----------
    youtube
        ``googleapiclient.discovery.build("youtube","v3",credentials=...)``
        or a structurally-compatible ``MockYouTube``.
    plan
        Phase 4 upload plan JSON. See :func:`build_insert_body` for the
        required/optional keys. May include ``_media_body`` and
        ``_thumb_body`` sentinels for tests to skip the lazy
        ``MediaFileUpload`` construction.
    video_path
        Path to the mp4 artefact. Used for sha256 checksum AND media
        upload.
    thumbnail_path
        Path to the PNG thumbnail.
    channel_id
        Our own YouTube channel id — required for the pinned-comment
        body (``snippet.channelId``).

    Returns
    -------
    str
        The YouTube videoId of the uploaded Short.
    """
    # Gate 1 — 48h+jitter lock. Raises PublishLockViolation.
    # Call through module so tests can monkeypatch publish_lock.assert_can_publish.
    _publish_lock.assert_can_publish()
    # Gate 2 — KST peak window. Raises PublishWindowViolation.
    # Call through module so tests can monkeypatch kst_window.assert_in_window.
    _kst_window.assert_in_window()

    # Gate 3 — inject production_metadata into description.
    pm_in = plan.get("production_metadata", {})
    meta = {
        "script_seed": pm_in.get("script_seed", ""),
        "assets_origin": pm_in.get("assets_origin", ""),
        "pipeline_version": PIPELINE_VERSION,
        "checksum": compute_checksum(video_path),
    }
    if "snippet" not in plan:
        plan["snippet"] = {}
    plan["snippet"]["description"] = inject_into_description(
        plan["snippet"].get("description", ""),
        meta,
    )

    # Gate 4 — build body + resumable insert. Raises AIDisclosureViolation
    # inside build_insert_body if containsSyntheticMedia ever drifts from
    # literal True (runtime last-line-defence; static anchor elsewhere).
    body = build_insert_body(plan)

    media_body = plan.get("_media_body")
    if media_body is None:
        from googleapiclient.http import MediaFileUpload   # lazy — test isolation
        media_body = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype="video/mp4",
        )

    insert_req = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media_body,
    )
    video_id = resumable_upload(insert_req)

    # Gate 5a — thumbnails.set (50 quota).
    thumb_body = plan.get("_thumb_body")
    if thumb_body is None:
        from googleapiclient.http import MediaFileUpload   # lazy — test isolation
        thumb_body = MediaFileUpload(str(thumbnail_path), mimetype="image/png")
    youtube.thumbnails().set(videoId=video_id, media_body=thumb_body).execute()

    # Gate 5b — pinned comment (D-09). funnel.end_screen_subscribe_cta is
    # a plan-level intent (Pitfall 7 — no API support); implemented here
    # via commentThreads.insert ONLY.
    pin_text = plan.get("funnel", {}).get("pinned_comment", _DEFAULT_PIN_TEXT)
    youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "channelId": channel_id,
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {"textOriginal": pin_text},
                },
            },
        },
    ).execute()

    # Gate 5c — persist 48h+jitter lock for the NEXT publish attempt.
    # Call through module so tests can monkeypatch publish_lock.record_upload.
    _publish_lock.record_upload()
    return video_id


__all__ = [
    "MAX_RETRIES",
    "RETRIABLE_STATUS_CODES",
    "YouTubeClient",
    "build_insert_body",
    "publish",
    "resumable_upload",
]
