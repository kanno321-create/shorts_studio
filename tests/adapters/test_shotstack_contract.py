"""Phase 14 ADAPT-03 — shotstack adapter contract.

계약 축 (8축):
1. pydantic ShotstackRenderRequest schema (timeline_entries min_length=1,
   resolution Literal, aspect_ratio Literal, filters_order default D-17).
2. DEFAULT_RESOLUTION == 'hd' (ORCH-11 720p first-pass render).
3. DEFAULT_ASPECT == '9:16' (Shorts TS-1 강제).
4. FILTER_ORDER == ('color_grade', 'saturation', 'film_grain') (D-17).
5. continuity_prefix 는 FILTER_ORDER[0] 위치 anchor (D-19 invariant, filter[0]
   == 'color_grade' — continuity_preset 존재 시 그 앞에 injection).
6. upscale() 는 Phase 5 RESEARCH §7 NOOP stub — {'status': 'skipped', ...}.
7. create_ken_burns_clip() 호출 시 DeprecationWarning 발생 (D-11 physical
   removal deferred to Phase 10).
8. Phase 7 ShotstackMock().allow_fault_injection is False (D-3 invariant).

real Shotstack API 호출 없음 — ``httpx.Client`` 를 MagicMock 으로 대체.

대표님 지시 (RESEARCH §ADAPT-03):
    ShotstackRenderRequest schema drift 감지 + D-17/D-19 invariant 보존 +
    ORCH-11 720p default + D-3 mock-safe default.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.orchestrator.api.models import ShotstackRenderRequest
from scripts.orchestrator.api.shotstack import ShotstackAdapter

pytestmark = pytest.mark.adapter_contract


# ---------------------------------------------------------------------------
# Schema + class-level constants
# ---------------------------------------------------------------------------


def test_shotstack_render_request_schema():
    """pydantic ShotstackRenderRequest schema — 필드 drift 감지.

    ``timeline_entries`` + ``resolution`` + ``aspect_ratio`` + ``filters_order``
    4 필드가 존재하고 default 값이 D-17/ORCH-11 과 일치해야 한다.
    """
    field_names = set(ShotstackRenderRequest.model_fields.keys())
    required = {"timeline_entries", "resolution", "aspect_ratio", "filters_order"}
    assert required.issubset(field_names), (
        f"ShotstackRenderRequest 필수 필드 drift: "
        f"expected {required}, actual {field_names}."
    )

    # Default 값 검증 — timeline_entries 는 min_length=1 이므로 placeholder 제공.
    req = ShotstackRenderRequest(
        timeline_entries=[{"kind": "clip", "start": 0.0, "end": 5.0}]
    )
    assert req.resolution == "hd"  # ORCH-11
    assert req.aspect_ratio == "9:16"  # TS-1
    assert req.filters_order == ["color_grade", "saturation", "film_grain"]  # D-17


def test_default_resolution_hd_orch11():
    """ORCH-11 invariant: first-pass render 는 720p ('hd')."""
    assert ShotstackAdapter.DEFAULT_RESOLUTION == "hd"


def test_default_aspect_9_16():
    """TS-1 invariant: Shorts 는 항상 9:16 vertical."""
    assert ShotstackAdapter.DEFAULT_ASPECT == "9:16"


def test_filter_order_d17():
    """D-17 invariant — color_grade → saturation → film_grain (tuple, 순서 고정)."""
    assert ShotstackAdapter.FILTER_ORDER == (
        "color_grade",
        "saturation",
        "film_grain",
    )


def test_continuity_prefix_anchor_is_filter_zero():
    """D-19 invariant — FILTER_ORDER[0] 이 continuity_prefix injection anchor.

    shotstack.py::_build_timeline_payload 는 preset 존재 시
    ``filters_order = ['continuity_prefix', *filters_order]`` 로 FILTER_ORDER[0]
    (color_grade) 앞에 prepend 한다. 즉 continuity_prefix 는 filter list 의
    0 번 위치에 위치하며, 기존 D-17 순서는 [1:] 로 밀린다. 본 test 는
    FILTER_ORDER[0] 이 color_grade 임을 확인하여 anchor position 을 잠근다.
    """
    assert ShotstackAdapter.FILTER_ORDER[0] == "color_grade", (
        "D-19 invariant 위반: FILTER_ORDER[0] 이 color_grade 가 아니면 "
        "continuity_prefix injection anchor 가 drift됨."
    )
    # D-17 2·3 번째 위치도 불변.
    assert ShotstackAdapter.FILTER_ORDER[1] == "saturation"
    assert ShotstackAdapter.FILTER_ORDER[2] == "film_grain"


# ---------------------------------------------------------------------------
# upscale NOOP + ken_burns deprecation
# ---------------------------------------------------------------------------


def test_upscale_is_noop(_fake_env, tmp_path):
    """Phase 5 RESEARCH §7 — upscale() 은 NOOP stub ('skipped' status).

    Shotstack native upscale endpoint 부재 + Topaz Video AI 유료 + Real-ESRGAN
    속도 부족 → 720p 가 shipping asset. upscale 은 Phase 8 deferred.
    """
    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    result = adapter.upscale("file:///tmp/in.mp4")

    assert isinstance(result, dict)
    assert result.get("status") == "skipped", (
        f"upscale() 은 'skipped' status 반환해야 함 (Phase 5 RESEARCH §7): {result}"
    )
    # source_url round-trip — 입력 echo.
    assert result.get("source_url") == "file:///tmp/in.mp4"


def test_create_ken_burns_clip_emits_deprecation_warning(_fake_env, tmp_path):
    """D-11 — create_ken_burns_clip 호출 시 DeprecationWarning 발생.

    Phase 9.1 D-11 에서 KenBurnsLocalAdapter 로 대체되었으나 Phase 7 fallback
    regression 보존 위해 당장 제거 않고 DeprecationWarning 으로 physical removal
    유예 (Phase 10 scope). 본 test 는 경고가 실제로 발생하는지 검증.
    """
    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    fake_image = tmp_path / "hero.png"
    fake_image.write_bytes(b"fake-png")

    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # _post_render seam 을 차단하여 network I/O 회피. warnings.warn 은
        # method body 서두에서 발생하므로 _post_render 가 raise 해도 캡처됨.
        with patch.object(
            ShotstackAdapter,
            "_post_render",
            side_effect=RuntimeError("blocked — contract test should not hit network"),
        ):
            with pytest.raises(RuntimeError):
                adapter.create_ken_burns_clip(
                    fake_image,
                    duration_s=3.0,
                    scale_from=1.0,
                    scale_to=1.15,
                    pan_direction="left_to_right",
                )

        deprecation_found = any(
            issubclass(w.category, DeprecationWarning) for w in warning_list
        )
        assert deprecation_found, (
            "create_ken_burns_clip 호출 시 DeprecationWarning 이 발생해야 함 (D-11). "
            "physical removal 은 Phase 10 batch window 로 유예."
        )


# ---------------------------------------------------------------------------
# API-key resolution + mock D-3 invariant
# ---------------------------------------------------------------------------


def test_api_key_resolution_and_value_error(monkeypatch, tmp_path):
    """kwarg > SHOTSTACK_API_KEY env > ValueError (침묵 폴백 금지, 금기 #3)."""
    monkeypatch.delenv("SHOTSTACK_API_KEY", raising=False)

    # Tier 1: kwarg 우선.
    a1 = ShotstackAdapter(api_key="kwarg-key", output_dir=tmp_path)
    assert getattr(a1, "_api_key", None) == "kwarg-key"

    # Tier 2: env var.
    monkeypatch.setenv("SHOTSTACK_API_KEY", "env-key")
    a2 = ShotstackAdapter(api_key=None, output_dir=tmp_path)
    assert getattr(a2, "_api_key", None) == "env-key"

    # Tier 3: 부재 → ValueError.
    monkeypatch.delenv("SHOTSTACK_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ShotstackAdapter(api_key=None, output_dir=tmp_path)


def test_shotstack_mock_fault_injection_disabled_by_default():
    """D-3 Phase 7 invariant — ShotstackMock().allow_fault_injection is False.

    Production-safe default: mock 은 fault injection 이 꺼진 채로 구동되며
    fault 를 주입하려면 테스트가 명시적으로 True 로 바꿔야 한다.

    tests/ 가 Python package 가 아니므로 (Phase 7 Plan 07-03 D-13),
    importlib.util.spec_from_file_location 로 mock 을 직접 load — sys.path
    오염 없음. @dataclass 의 cls.__module__ resolution 을 위해 sys.modules
    에 고유 prefix 로 임시 등록 후 try/finally 로 cleanup.
    """
    import importlib.util
    import sys

    mock_path = (
        Path(__file__).resolve().parents[1]
        / "phase07"
        / "mocks"
        / "shotstack_mock.py"
    )
    assert mock_path.exists(), (
        f"tests/phase07/mocks/shotstack_mock.py 가 존재해야 함 "
        f"(D-3 Phase 7 mock): {mock_path}"
    )
    mod_name = "_phase07_shotstack_mock_contract"
    spec = importlib.util.spec_from_file_location(mod_name, mock_path)
    assert spec is not None and spec.loader is not None, (
        "importlib.util.spec_from_file_location 로부터 valid spec 획득 실패."
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
        mock = module.ShotstackMock()
        assert mock.allow_fault_injection is False, (
            "ShotstackMock().allow_fault_injection 기본값이 False 여야 함 "
            "(D-3 Phase 7 production-safe default)."
        )
    finally:
        sys.modules.pop(mod_name, None)


# ---------------------------------------------------------------------------
# render httpx seam + FILTER_ORDER integration
# ---------------------------------------------------------------------------


@patch("scripts.orchestrator.api.shotstack.httpx.Client")
def test_render_uses_httpx_client_seam(mock_client_class, _fake_env, tmp_path):
    """render() 는 httpx.Client seam 을 통해 POST — 실 network 호출 차단 가능.

    ShotstackRenderRequest default (resolution='hd', aspect='9:16') 가 payload
    output 에 반영되는지 integration 검증.
    """
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": {"id": "r_001", "url": "file:///tmp/out.mp4", "message": "Created"},
        "success": True,
    }
    mock_response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client.__enter__ = lambda self: self
    mock_client.__exit__ = lambda *a: None
    mock_client_class.return_value = mock_client

    adapter = ShotstackAdapter(api_key="fake", output_dir=tmp_path)
    # Pre-built dict timeline (실 TimelineEntry 의존 최소화).
    timeline = [
        {
            "kind": "clip",
            "start": 0.0,
            "end": 5.0,
            "clip_path": "tmp/scene1.mp4",
            "speed": 1.0,
            "audio_path": "tmp/scene1.mp3",
        }
    ]
    result = adapter.render(timeline)

    # httpx.Client 가 실제 호출되었는지 (실 network 아님 — mock).
    assert mock_client.post.called, "httpx.Client.post 가 호출되어야 함."
    # Response envelope 구조 — ShotstackMock 계약과 동일.
    assert result == mock_response.json.return_value

    # Payload output 구조 검증 — ORCH-11 (hd) + TS-1 (9:16) default.
    posted_payload = mock_client.post.call_args.kwargs["json"]
    assert posted_payload["output"]["resolution"] == "hd"
    assert posted_payload["output"]["aspectRatio"] == "9:16"
