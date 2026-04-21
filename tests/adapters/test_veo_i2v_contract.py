"""Phase 14 ADAPT-01 — veo_i2v adapter contract.

계약 축 (6축):
1. pydantic I2VRequest schema 준수 (prompt min_length=1, anchor_frame Path,
   duration_seconds [4, 8], move_count Literal[1]).
2. API-key 3-tier resolution (constructor > VEO_API_KEY > FAL_KEY > ValueError).
3. anchor_frame=None 시 T2VForbidden raise (CLAUDE.md 금기사항 #4 강제).
4. image_to_video 출력은 pathlib.Path (``_submit_and_poll`` seam monkeypatch).
5. production adapter 에 fault-injection toggle 부재 (D-3 mock-only invariant).
6. 모듈 source 에 금기 토큰 (t2v / text_to_video / text2video) 0 회 — Wave 1
   에서 이관된 physical-absence guard invariant 재확인.

real fal.ai API 호출 없음 — ``_submit_and_poll`` seam 을 monkeypatch.

대표님 지시 (RESEARCH §ADAPT-01 + Wave 1 Task 14-02-01):
    veo_i2v.py 의 모듈-footer assert 가 blacklist grep 과 self-reference 를
    일으켰기에 삭제됐고, 물리 부재 guarantee 는 3 중 layer 로 이관됨:
    (1) blacklist grep (tests/phase05/test_blacklist_grep.py),
    (2) pre_tool_use.py deprecated_patterns.json,
    (3) 본 contract test (test_no_text_only_method).
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.orchestrator.api.models import I2VRequest
from scripts.orchestrator.api.veo_i2v import VeoI2VAdapter
from scripts.orchestrator.gates import T2VForbidden

pytestmark = pytest.mark.adapter_contract


# ADAPT-01 축 6: source 에 금기 토큰 부재 regex (Phase 5 test_blacklist_grep 과 동일).
T2V_BLACKLIST = re.compile(
    r"(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video"
)


def test_no_text_only_method():
    """Physical absence guard — Wave 1 에서 이관된 module-level assert 의 대체.

    VeoI2VAdapter 는 image_to_video 단 하나의 public 생성 메서드만 보유한다
    (D-13 / VIDEO-01 / 금기사항 #4). 모듈 source 에도 금기 토큰이 남아있지
    않아야 하며 (blacklist grep 과 self-reference 회피), 본 contract test 가
    그 invariant 를 승계·검증한다.
    """
    # Physical absence — class 에 text-only 메서드 없음.
    assert not hasattr(VeoI2VAdapter, "image_to_video_text_only"), (
        "VeoI2VAdapter.image_to_video_text_only 가 정의되어 있음 "
        "(D-13 / 금기사항 #4 위반)."
    )
    assert not hasattr(VeoI2VAdapter, "text_to_video"), (
        "VeoI2VAdapter.text_to_video 가 정의되어 있음 (D-13 / 금기사항 #4 위반)."
    )

    # Source-level blacklist — 금기 토큰 출현 0회.
    source = inspect.getsource(VeoI2VAdapter)
    assert T2V_BLACKLIST.search(source) is None, (
        "VeoI2VAdapter class source 에 T2V 금기 토큰 발견. "
        "금기사항 #4 위반 (CLAUDE.md)."
    )


def test_i2v_request_schema_compliance(tmp_path):
    """pydantic I2VRequest 기본 schema (D-13 anchor REQUIRED + D-14 duration 4-8)."""
    anchor = tmp_path / "frame.png"
    anchor.write_bytes(b"fake-png")

    # Happy path — 기본 schema.
    req = I2VRequest(prompt="test prompt", anchor_frame=anchor, duration_seconds=5)
    assert req.prompt == "test prompt"
    assert req.anchor_frame == anchor
    assert req.duration_seconds == 5
    assert req.move_count == 1  # D-14 invariant (Literal[1])

    # Negative 1: prompt 빈 문자열 → ValidationError (min_length=1).
    with pytest.raises(ValidationError):
        I2VRequest(prompt="", anchor_frame=anchor, duration_seconds=5)

    # Negative 2: duration 범위 밖 (D-14 4-8 bound).
    with pytest.raises(ValidationError):
        I2VRequest(prompt="ok", anchor_frame=anchor, duration_seconds=10)


def test_missing_anchor_raises_t2v_forbidden(_fake_env, tmp_path):
    """금기 #4 — anchor_frame=None 입력 시 T2VForbidden raise (D-13 / VIDEO-01)."""
    adapter = VeoI2VAdapter(api_key="fake", output_dir=tmp_path)
    with pytest.raises(T2VForbidden):
        adapter.image_to_video(prompt="test", anchor_frame=None, duration_seconds=5)


def test_api_key_3tier_resolution(monkeypatch, tmp_path):
    """kwarg > VEO_API_KEY > FAL_KEY > ValueError (3-tier resolution chain).

    VeoI2VAdapter 는 self._api_key 에 resolved value 를 저장 (private).
    """
    # Baseline wipe — 모든 env 제거.
    monkeypatch.delenv("VEO_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)

    # Tier 1: kwarg 우선 — env 둘 다 있어도 kwarg 채택.
    monkeypatch.setenv("VEO_API_KEY", "env-should-be-ignored")
    monkeypatch.setenv("FAL_KEY", "fal-should-be-ignored")
    a1 = VeoI2VAdapter(api_key="kwarg-key", output_dir=tmp_path)
    assert getattr(a1, "_api_key", None) == "kwarg-key"

    # Tier 2: kwarg None + VEO_API_KEY 우선.
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.setenv("VEO_API_KEY", "veo-env")
    a2 = VeoI2VAdapter(api_key=None, output_dir=tmp_path)
    assert getattr(a2, "_api_key", None) == "veo-env"

    # Tier 3: VEO_API_KEY 부재 + FAL_KEY fallback.
    monkeypatch.delenv("VEO_API_KEY", raising=False)
    monkeypatch.setenv("FAL_KEY", "fal-env")
    a3 = VeoI2VAdapter(api_key=None, output_dir=tmp_path)
    assert getattr(a3, "_api_key", None) == "fal-env"

    # Tier 4: 모두 부재 → ValueError (침묵 폴백 금지, 금기 #3).
    monkeypatch.delenv("VEO_API_KEY", raising=False)
    monkeypatch.delenv("FAL_KEY", raising=False)
    with pytest.raises(ValueError):
        VeoI2VAdapter(api_key=None, output_dir=tmp_path)


def test_output_is_path(monkeypatch, _fake_env, tmp_path):
    """image_to_video 반환값 = pathlib.Path (``_submit_and_poll`` seam monkeypatch)."""
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(b"fake-png")
    fake_output = tmp_path / "veo_stub.mp4"

    def _stub_submit_and_poll(self, payload):  # noqa: ARG001
        fake_output.write_bytes(b"fake-mp4")
        return fake_output

    monkeypatch.setattr(VeoI2VAdapter, "_submit_and_poll", _stub_submit_and_poll)
    adapter = VeoI2VAdapter(api_key="fake", output_dir=tmp_path)
    result = adapter.image_to_video(
        prompt="test", anchor_frame=anchor, duration_seconds=5
    )
    assert isinstance(result, Path)
    assert result == fake_output
    assert result.exists()


def test_production_adapter_has_no_fault_injection_attr(_fake_env, tmp_path):
    """D-3 invariant — fault-injection toggle 은 Phase 7 mock 전용.

    Production VeoI2VAdapter 에는 allow_fault_injection 속성이 부재해야 한다
    — 해당 속성은 tests/phase07/mocks/ 의 mock 클래스가 독점적으로 보유한다.
    (Veo 는 Phase 7 mock 이 없으므로 Phase 15 추가 예정이며, 그때도 production
    adapter 는 건드리지 않는다.)
    """
    adapter = VeoI2VAdapter(api_key="fake", output_dir=tmp_path)
    assert not hasattr(adapter, "allow_fault_injection"), (
        "Production VeoI2VAdapter 에 allow_fault_injection 속성 발견. "
        "해당 속성은 tests/phase07/mocks/ 전용이어야 함 (D-3 Phase 7)."
    )
