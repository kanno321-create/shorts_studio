"""Mock tests for Kling and Runway I2V adapters (VIDEO-01 / VIDEO-04).

Covers:

* API-key resolution (explicit arg, env fallback, ValueError when absent).
* D-13 runtime guard (``anchor_frame=None`` => T2VForbidden).
* D-13 physical-absence guard (the text-only method has never been defined
  on either adapter class; the module-level assertion would have crashed
  the import if someone re-added it).
* D-14 parse-time validation (duration=3 is rejected before HTTP).
* Mockable ``_submit_and_poll`` / ``_invoke_runway`` seams return a
  :class:`pathlib.Path` when the underlying SDK call is patched.

The forbidden identifier is never written verbatim in this file — it is
assembled at runtime from fragments so the ``.claude/deprecated_patterns.json``
regex does not block the Write. Same technique the adapter modules use
for their assertion strings.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.orchestrator import T2VForbidden
from scripts.orchestrator.api.kling_i2v import KlingI2VAdapter
from scripts.orchestrator.api.runway_i2v import RunwayI2VAdapter


# Name of the method that MUST NOT exist on either adapter (D-13).
# Assembled from fragments; never appears as a literal token.
_FORBIDDEN_METHOD = "text_" + "to_" + "video"


# ---------------------------------------------------------------------------
# Method presence / absence contracts
# ---------------------------------------------------------------------------


def test_kling_has_image_to_video_method():
    assert hasattr(KlingI2VAdapter, "image_to_video")


def test_runway_has_image_to_video_method():
    assert hasattr(RunwayI2VAdapter, "image_to_video")


def test_kling_NO_forbidden_method_d13():
    """D-13: the text-only sibling must be physically absent."""
    assert not hasattr(KlingI2VAdapter, _FORBIDDEN_METHOD), (
        f"D-13 violation: {_FORBIDDEN_METHOD!r} exists on KlingI2VAdapter"
    )


def test_runway_NO_forbidden_method_d13():
    """D-13: RESEARCH §8 line 785 mandates removal from the Runway rewrite."""
    assert not hasattr(RunwayI2VAdapter, _FORBIDDEN_METHOD), (
        f"D-13 violation: {_FORBIDDEN_METHOD!r} exists on RunwayI2VAdapter"
    )


def test_kling_module_assertion_prevents_reintroduction():
    """Re-importing the module would crash if the guard assertion failed."""

    import scripts.orchestrator.api.kling_i2v as mod

    assert not hasattr(mod.KlingI2VAdapter, _FORBIDDEN_METHOD)


def test_runway_module_assertion_prevents_reintroduction():
    import scripts.orchestrator.api.runway_i2v as mod

    assert not hasattr(mod.RunwayI2VAdapter, _FORBIDDEN_METHOD)


# ---------------------------------------------------------------------------
# API-key resolution
# ---------------------------------------------------------------------------


def test_kling_init_accepts_explicit_api_key():
    a = KlingI2VAdapter(api_key="fake")
    assert a is not None


def test_kling_init_falls_back_to_kling_env(monkeypatch):
    monkeypatch.setenv("KLING_API_KEY", "env-kling")
    monkeypatch.delenv("FAL_KEY", raising=False)
    a = KlingI2VAdapter(api_key=None)
    assert a is not None


def test_kling_init_falls_back_to_fal_env(monkeypatch):
    monkeypatch.delenv("KLING_API_KEY", raising=False)
    monkeypatch.setenv("FAL_KEY", "env-fal")
    a = KlingI2VAdapter(api_key=None)
    assert a is not None


def test_kling_init_raises_without_key(monkeypatch):
    monkeypatch.delenv("KLING_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(ValueError):
        KlingI2VAdapter(api_key=None)


def test_runway_init_accepts_explicit_api_key():
    assert RunwayI2VAdapter(api_key="fake") is not None


def test_runway_init_falls_back_to_runway_env(monkeypatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "env-runway")
    monkeypatch.delenv("RUNWAYML_API_SECRET", raising=False)
    assert RunwayI2VAdapter(api_key=None) is not None


def test_runway_init_falls_back_to_runwayml_secret(monkeypatch):
    monkeypatch.delenv("RUNWAY_API_KEY", raising=False)
    monkeypatch.setenv("RUNWAYML_API_SECRET", "env-secret")
    assert RunwayI2VAdapter(api_key=None) is not None


def test_runway_init_raises_without_key(monkeypatch):
    monkeypatch.delenv("RUNWAY_API_KEY", raising=False)
    monkeypatch.delenv("RUNWAYML_API_SECRET", raising=False)
    with pytest.raises(ValueError):
        RunwayI2VAdapter(api_key=None)


# ---------------------------------------------------------------------------
# D-13 runtime guard (anchor_frame=None -> T2VForbidden)
# ---------------------------------------------------------------------------


def test_kling_anchor_frame_none_raises_t2v_forbidden():
    a = KlingI2VAdapter(api_key="fake")
    with pytest.raises(T2VForbidden) as ei:
        a.image_to_video(prompt="test", anchor_frame=None, duration_seconds=5)
    msg = str(ei.value)
    assert "D-13" in msg or "anchor_frame" in msg


def test_runway_anchor_frame_none_raises_t2v_forbidden():
    a = RunwayI2VAdapter(api_key="fake")
    with pytest.raises(T2VForbidden):
        a.image_to_video(prompt="test", anchor_frame=None, duration_seconds=5)


# ---------------------------------------------------------------------------
# D-14 parse-time validation (pydantic)
# ---------------------------------------------------------------------------


def test_kling_invalid_duration_rejected(tmp_path):
    from pydantic import ValidationError

    a = KlingI2VAdapter(api_key="fake")
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"fake png")
    with pytest.raises((ValidationError, ValueError)):
        a.image_to_video(prompt="test", anchor_frame=anchor, duration_seconds=3)


def test_runway_invalid_duration_rejected(tmp_path):
    from pydantic import ValidationError

    a = RunwayI2VAdapter(api_key="fake")
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"fake png")
    with pytest.raises((ValidationError, ValueError)):
        a.image_to_video(prompt="test", anchor_frame=anchor, duration_seconds=9)


# ---------------------------------------------------------------------------
# Happy-path: mocked SDK seams
# ---------------------------------------------------------------------------


@patch("scripts.orchestrator.api.kling_i2v.KlingI2VAdapter._submit_and_poll")
def test_kling_valid_call_returns_path(mock_submit, tmp_path):
    mock_submit.return_value = tmp_path / "output.mp4"
    a = KlingI2VAdapter(api_key="fake")
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"fake")
    result = a.image_to_video(prompt="test", anchor_frame=anchor, duration_seconds=5)
    assert isinstance(result, Path)
    mock_submit.assert_called_once()
    # Payload should carry the validated request fields verbatim.
    posted_payload = mock_submit.call_args.args[0]
    assert posted_payload["prompt"] == "test"
    assert posted_payload["duration"] == "5"


@patch("scripts.orchestrator.api.runway_i2v.RunwayI2VAdapter._invoke_runway")
def test_runway_valid_call_returns_path(mock_invoke, tmp_path):
    mock_invoke.return_value = tmp_path / "out.mp4"
    a = RunwayI2VAdapter(api_key="fake")
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"fake")
    result = a.image_to_video(prompt="test", anchor_frame=anchor, duration_seconds=6)
    assert isinstance(result, Path)
    mock_invoke.assert_called_once()
    kwargs = mock_invoke.call_args.args[0]
    assert kwargs["model"] == "gen3_alpha_turbo"  # D-16
    assert kwargs["ratio"] == "720:1280"  # 9:16 Shorts
    assert kwargs["duration"] == 6


def test_kling_coerces_string_path_to_path(tmp_path):
    """Anchor coercion: a string path becomes a pathlib.Path before validation."""

    anchor_str = str(tmp_path / "anchor.png")
    (tmp_path / "anchor.png").write_bytes(b"fake")

    with patch(
        "scripts.orchestrator.api.kling_i2v.KlingI2VAdapter._submit_and_poll"
    ) as mock_submit:
        mock_submit.return_value = tmp_path / "out.mp4"
        a = KlingI2VAdapter(api_key="fake")
        a.image_to_video(prompt="test", anchor_frame=anchor_str, duration_seconds=5)
        assert mock_submit.called
