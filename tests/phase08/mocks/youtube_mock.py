"""Deterministic YouTube Data API v3 resource double for Phase 8.

Mirrors the surface used by scripts/publisher/youtube_uploader.py (Wave 4) +
scripts/publisher/smoke_test.py (Wave 5):

* videos().insert(part=, body=, media_body=)  resumable upload request
* videos().delete(id=)                         cleanup after smoke test
* videos().list(part=, id=)                    processingStatus query
* thumbnails().set(videoId=, media_body=)      custom thumbnail
* commentThreads().insert(part=, body=)        pinned comment (PUB-05)

Per CONTEXT D-10 + Phase 7 Correction 2 default safety inheritance:
``allow_fault_injection`` defaults to **False**. Fault injection is a strict
opt-in and is driven by the instance attribute ``_fault_mode``; with the
default off, even a non-None ``_fault_mode`` value must NOT raise.

The adapter library (googleapiclient) is imported lazily inside the fault
path so unit tests without the library installed still pass cleanly.
"""
from __future__ import annotations

from typing import Any, Optional


class MockYouTube:
    """Mock for googleapiclient.discovery.build("youtube", "v3", credentials=...).

    Contract:
    - allow_fault_injection=False (default): all methods succeed deterministically.
    - allow_fault_injection=True + _fault_mode set: first videos().insert().next_chunk()
      call raises the configured fault class.
    """

    def __init__(self, *, allow_fault_injection: bool = False) -> None:
        self._allow_fault_injection = allow_fault_injection
        self._fault_mode: Optional[str] = None
        self._upload_count: int = 0
        self._video_ids: list[str] = []
        self._deleted: list[str] = []
        self._pinned_comments: dict[str, str] = {}

    # Top-level resource accessors ------------------------------------------------
    def videos(self) -> "_VideosStub":
        return _VideosStub(self)

    def thumbnails(self) -> "_ThumbnailsStub":
        return _ThumbnailsStub(self)

    def commentThreads(self) -> "_CommentThreadsStub":
        return _CommentThreadsStub(self)


# ---------------------------------------------------------------------------
# videos() sub-resource
# ---------------------------------------------------------------------------
class _VideosStub:
    def __init__(self, parent: MockYouTube) -> None:
        self.parent = parent

    def insert(
        self,
        *,
        part: str,
        body: dict[str, Any],
        media_body: Any,
    ) -> "_InsertRequest":
        return _InsertRequest(self.parent, part=part, body=body, media_body=media_body)

    def delete(self, *, id: str) -> "_DeleteRequest":  # noqa: A002 - matches real API
        return _DeleteRequest(self.parent, video_id=id)

    def list(self, *, part: str, id: str) -> "_ListRequest":  # noqa: A002 - matches real API
        return _ListRequest(self.parent, part=part, video_id=id)


class _InsertRequest:
    def __init__(
        self,
        parent: MockYouTube,
        *,
        part: str,
        body: dict[str, Any],
        media_body: Any,
    ) -> None:
        self.parent = parent
        self.part = part
        self.body = body
        self.media_body = media_body
        self._consumed = False

    def next_chunk(self) -> tuple[None, dict[str, Any]]:
        """Resumable upload — one-shot success on first call.

        Fault-injection opt-in: when parent._allow_fault_injection is True and
        parent._fault_mode is set, raise the corresponding error class. Lazy
        imports keep the mock usable without google-api-python-client installed.
        """
        if self._consumed:
            # Real API returns None when already completed; we mirror by returning
            # the last response shape for idempotent callers.
            vid = self.parent._video_ids[-1]
            return None, {"id": vid}
        if self.parent._allow_fault_injection and self.parent._fault_mode:
            mode = self.parent._fault_mode
            if mode == "http_500":
                # Lazy import — raise HttpError with 500 resp
                try:
                    from googleapiclient.errors import HttpError  # type: ignore

                    class _Resp:
                        status = 500
                        reason = "Internal Server Error"

                    raise HttpError(_Resp(), b"{\"error\":\"server\"}")
                except ImportError:
                    # Library missing — surface a generic retriable error.
                    raise RuntimeError("HttpError status=500 (googleapiclient missing)")
            if mode == "httplib2":
                try:
                    import httplib2  # type: ignore

                    raise httplib2.HttpLib2Error("socket reset")
                except ImportError:
                    raise RuntimeError("HttpLib2Error (httplib2 missing)")
            # Unknown mode — fall through to default RuntimeError
            raise RuntimeError(f"Unknown fault mode: {mode}")

        # Happy path — successful one-shot resumable upload.
        self.parent._upload_count += 1
        vid = f"mock_video_id_{self.parent._upload_count:03d}"
        self.parent._video_ids.append(vid)
        self._consumed = True
        return None, {"id": vid}


class _DeleteRequest:
    def __init__(self, parent: MockYouTube, *, video_id: str) -> None:
        self.parent = parent
        self.video_id = video_id

    def execute(self) -> dict[str, Any]:
        self.parent._deleted.append(self.video_id)
        return {}


class _ListRequest:
    def __init__(self, parent: MockYouTube, *, part: str, video_id: str) -> None:
        self.parent = parent
        self.part = part
        self.video_id = video_id

    def execute(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "id": self.video_id,
                    "status": {
                        "processingStatus": "succeeded",
                        "uploadStatus": "processed",
                    },
                }
            ]
        }


# ---------------------------------------------------------------------------
# thumbnails() sub-resource
# ---------------------------------------------------------------------------
class _ThumbnailsStub:
    def __init__(self, parent: MockYouTube) -> None:
        self.parent = parent

    def set(self, *, videoId: str, media_body: Any) -> "_ThumbnailSetRequest":  # noqa: N803
        return _ThumbnailSetRequest(self.parent, video_id=videoId, media_body=media_body)


class _ThumbnailSetRequest:
    def __init__(self, parent: MockYouTube, *, video_id: str, media_body: Any) -> None:
        self.parent = parent
        self.video_id = video_id
        self.media_body = media_body

    def execute(self) -> dict[str, Any]:
        return {
            "kind": "youtube#thumbnailSetResponse",
            "items": [
                {"videoId": self.video_id, "default": {"url": f"file://mock_thumb_{self.video_id}"}}
            ],
        }


# ---------------------------------------------------------------------------
# commentThreads() sub-resource — PUB-05 pinned comment
# ---------------------------------------------------------------------------
class _CommentThreadsStub:
    def __init__(self, parent: MockYouTube) -> None:
        self.parent = parent

    def insert(self, *, part: str, body: dict[str, Any]) -> "_CommentThreadInsertRequest":
        return _CommentThreadInsertRequest(self.parent, part=part, body=body)


class _CommentThreadInsertRequest:
    def __init__(self, parent: MockYouTube, *, part: str, body: dict[str, Any]) -> None:
        self.parent = parent
        self.part = part
        self.body = body

    def execute(self) -> dict[str, Any]:
        snippet = self.body.get("snippet", {})
        video_id = snippet.get("videoId", "")
        top = snippet.get("topLevelComment", {}).get("snippet", {})
        text = top.get("textOriginal", "")
        if video_id:
            self.parent._pinned_comments[video_id] = text
        return {
            "id": "mock_comment_id",
            "kind": "youtube#commentThread",
            "snippet": snippet,
        }


__all__ = ["MockYouTube"]
