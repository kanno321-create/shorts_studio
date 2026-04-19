"""Unit tests for ShotstackMock — covers render, upscale, create_ken_burns_clip."""
from __future__ import annotations

import sys
from pathlib import Path

_PHASE07_ROOT = Path(__file__).resolve().parent
if str(_PHASE07_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE07_ROOT))

from mocks.shotstack_mock import ShotstackMock  # noqa: E402


def test_render_returns_v2_envelope():
    mock = ShotstackMock()
    resp = mock.render({"timeline": {"tracks": []}})
    assert resp["success"] is True
    assert resp["status"] == "done"
    assert resp["response"]["message"] == "Created"
    assert resp["response"]["id"].startswith("mock_shotstack_")
    assert resp["response"]["url"].startswith("file://")


def test_render_call_count_increments():
    mock = ShotstackMock()
    mock.render({})
    mock.render({})
    mock.render({})
    assert mock.render_call_count == 3


def test_render_payload_captured():
    mock = ShotstackMock()
    payload = {"timeline": {"background": "#000", "tracks": []}}
    mock.render(payload)
    assert mock.last_render_payload == payload


def test_upscale_is_noop():
    mock = ShotstackMock()
    resp = mock.upscale()
    assert resp == {"status": "skipped", "reason": "mock upscale NOOP"}
    assert mock.upscale_call_count == 1


def test_create_ken_burns_clip_returns_path():
    mock = ShotstackMock()
    result = mock.create_ken_burns_clip(
        image_path=Path("/tmp/still.jpg"),
        duration_s=5.0,
    )
    assert isinstance(result, Path)
    assert result.name == "mock_shotstack.mp4"
    assert mock.ken_burns_call_count == 1


def test_create_ken_burns_clip_captures_args():
    mock = ShotstackMock()
    mock.create_ken_burns_clip(
        image_path=Path("/tmp/img.jpg"),
        duration_s=3.5,
        scale_from=1.0,
        scale_to=1.2,
        pan_direction="right_to_left",
    )
    args = mock.last_ken_burns_args
    assert args["duration_s"] == 3.5
    assert args["scale_to"] == 1.2
    assert args["pan_direction"] == "right_to_left"


def test_production_safe_default():
    assert ShotstackMock().allow_fault_injection is False


def test_render_accepts_timeline_list_signature():
    """Real ShotstackAdapter.render takes timeline as first positional arg.
    Mock accepts payload as dict — both shapes via *args, **kwargs."""
    mock = ShotstackMock()
    resp = mock.render([{"clip": "x"}])
    assert resp["success"] is True
