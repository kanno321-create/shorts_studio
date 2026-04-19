"""Mock tests for :class:`ShotstackAdapter`.

Covers ORCH-11 (720p Low-Res First default), D-17 (filter order), ORCH-12
(ken-burns fallback stub), and the Phase 8 upscale NOOP contract.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator.api.shotstack import ShotstackAdapter
from scripts.orchestrator.voice_first_timeline import TimelineEntry


# ---------------------------------------------------------------------------
# API-key resolution
# ---------------------------------------------------------------------------


def test_shotstack_init_requires_key(monkeypatch):
    monkeypatch.delenv("SHOTSTACK_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ShotstackAdapter(api_key=None)


def test_shotstack_init_with_explicit_key():
    a = ShotstackAdapter(api_key="fake")
    assert a is not None


def test_shotstack_init_from_env(monkeypatch):
    monkeypatch.setenv("SHOTSTACK_API_KEY", "env-key")
    a = ShotstackAdapter(api_key=None)
    assert a is not None


# ---------------------------------------------------------------------------
# Class-level constants — ORCH-11 / D-17 contracts
# ---------------------------------------------------------------------------


def test_default_resolution_hd_orch11():
    """ORCH-11: first-pass render is 720p ('hd')."""
    assert ShotstackAdapter.DEFAULT_RESOLUTION == "hd"


def test_default_aspect_9_16():
    assert ShotstackAdapter.DEFAULT_ASPECT == "9:16"


def test_filter_order_d17():
    """D-17: color grade -> saturation -> film grain, in that order."""
    assert ShotstackAdapter.FILTER_ORDER == (
        "color_grade",
        "saturation",
        "film_grain",
    )


# ---------------------------------------------------------------------------
# render() — mocked HTTP client
# ---------------------------------------------------------------------------


def _make_mock_httpx_client(response_json: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = response_json
    mock_response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = lambda *a: None
    return mock_client


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_720p_default_payload(mock_client_class, tmp_path):
    """Render call with default args produces 'hd' resolution + 9:16 aspect."""

    mock_client = _make_mock_httpx_client(
        {"response": {"id": "r1", "url": "https://s.io/r1.mp4"}, "success": True}
    )
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="fake")
    timeline = [
        TimelineEntry(
            start=0.0,
            end=5.0,
            clip_path=Path("c1.mp4"),
            speed=1.0,
            audio_path=Path("a1.mp3"),
        )
    ]
    result = adapter.render(timeline)

    assert result["success"] is True
    posted_json = mock_client.post.call_args.kwargs["json"]
    assert posted_json["output"]["resolution"] == "hd"
    assert posted_json["output"]["aspectRatio"] == "9:16"


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_payload_carries_d17_filter_order(mock_client_class, monkeypatch):
    """D-17 Phase 5 invariant: when no continuity preset is present, the
    Shotstack filter chain is exactly the 3-element D-17 tail
    ``color_grade → saturation → film_grain``. Phase 6 Plan 07 adds an
    OPTIONAL prefix injection (D-19, asserted in tests/phase06/
    test_filter_order_preservation.py); this Phase 5 regression guard
    stubs the preset loader to None so the D-17 tail is asserted in
    isolation without coupling to the presence of
    wiki/continuity_bible/prefix.json.
    """

    # Phase 6 Plan 07: isolate Phase 5 invariant by disabling preset
    # injection. This keeps the Phase 5 contract (D-17 tail) intact and
    # lets Phase 6 tests own the D-19 post-injection contract.
    from scripts.orchestrator.api import shotstack as _shotstack_mod

    monkeypatch.setattr(
        _shotstack_mod, "_load_continuity_preset", lambda path=None: None
    )

    mock_client = _make_mock_httpx_client({"response": {}, "success": True})
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="fake")
    timeline = [
        TimelineEntry(
            start=0.0,
            end=5.0,
            clip_path=Path("c.mp4"),
            speed=1.0,
            audio_path=Path("a.mp3"),
        )
    ]
    adapter.render(timeline)

    posted_json = mock_client.post.call_args.kwargs["json"]
    filters = posted_json["timeline"]["filters"]
    assert filters == ["color_grade", "saturation", "film_grain"]


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_explicit_4k_opt_in(mock_client_class):
    """Callers may opt into 4K even though the default is 720p."""

    mock_client = _make_mock_httpx_client({"response": {}, "success": True})
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="fake")
    timeline = [
        TimelineEntry(
            start=0.0,
            end=5.0,
            clip_path=Path("c.mp4"),
            speed=1.0,
            audio_path=Path("a.mp3"),
        )
    ]
    adapter.render(timeline, resolution="4k")

    posted_json = mock_client.post.call_args.kwargs["json"]
    assert posted_json["output"]["resolution"] == "4k"


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_rejects_invalid_resolution(mock_client_class):
    """pydantic v2 rejects 'ultra' (not in the Literal)."""

    from pydantic import ValidationError

    adapter = ShotstackAdapter(api_key="fake")
    timeline = [
        TimelineEntry(
            start=0.0,
            end=1.0,
            clip_path=Path("c.mp4"),
            speed=1.0,
            audio_path=Path("a.mp3"),
        )
    ]
    with pytest.raises(ValidationError):
        adapter.render(timeline, resolution="ultra")


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_api_key_sent_in_header(mock_client_class):
    mock_client = _make_mock_httpx_client({"response": {}, "success": True})
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="super-secret")
    timeline = [
        TimelineEntry(
            start=0.0,
            end=1.0,
            clip_path=Path("c.mp4"),
            speed=1.0,
            audio_path=Path("a.mp3"),
        )
    ]
    adapter.render(timeline)

    headers = mock_client.post.call_args.kwargs["headers"]
    assert headers["x-api-key"] == "super-secret"


# ---------------------------------------------------------------------------
# upscale() — Phase 8 NOOP stub
# ---------------------------------------------------------------------------


def test_upscale_returns_skipped_status():
    adapter = ShotstackAdapter(api_key="fake")
    result = adapter.upscale("https://example.com/src.mp4")
    assert result["status"] == "skipped"
    assert "Phase 8" in result["reason"] or "deferred" in result["reason"].lower()


def test_upscale_echoes_source_url():
    adapter = ShotstackAdapter(api_key="fake")
    result = adapter.upscale("https://example.com/src.mp4")
    assert result["source_url"] == "https://example.com/src.mp4"


# ---------------------------------------------------------------------------
# create_ken_burns_clip() — ORCH-12 Fallback lane
# ---------------------------------------------------------------------------


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_create_ken_burns_clip_returns_path(mock_client_class, tmp_path):
    mock_client = _make_mock_httpx_client(
        {"response": {"id": "kb1", "url": f"file://{tmp_path.as_posix()}/out.mp4"}, "success": True}
    )
    mock_client_class.return_value = mock_client

    (tmp_path / "out.mp4").write_bytes(b"fake mp4")

    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    image = tmp_path / "still.png"
    image.write_bytes(b"fake png")

    result = adapter.create_ken_burns_clip(
        image_path=image,
        duration_s=5.0,
        scale_from=1.0,
        scale_to=1.15,
        pan_direction="left_to_right",
    )
    assert isinstance(result, Path)
    # Payload should include the image asset + scale from/to params.
    posted = mock_client.post.call_args.kwargs["json"]
    clip = posted["timeline"]["tracks"][0]["clips"][0]
    assert clip["asset"]["type"] == "image"
    assert clip["scale"]["from"] == 1.0
    assert clip["scale"]["to"] == 1.15
    assert clip["length"] == 5.0


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_create_ken_burns_clip_maps_pan_direction(mock_client_class, tmp_path):
    mock_client = _make_mock_httpx_client({"response": {"url": ""}, "success": True})
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    image = tmp_path / "still.png"
    image.write_bytes(b"fake")

    adapter.create_ken_burns_clip(
        image_path=image, duration_s=4.0, pan_direction="right_to_left"
    )
    posted = mock_client.post.call_args.kwargs["json"]
    clip = posted["timeline"]["tracks"][0]["clips"][0]
    assert clip["effect"] == "zoomInSlowReverse"


# ---------------------------------------------------------------------------
# D-13 physical absence (no T2V method on Shotstack either).
# ---------------------------------------------------------------------------


_FORBIDDEN_METHOD = "text_" + "to_" + "video"


def test_no_forbidden_method_on_shotstack():
    """Shotstack handles assembly only; it has never exposed T2V."""

    assert not hasattr(ShotstackAdapter, _FORBIDDEN_METHOD)
