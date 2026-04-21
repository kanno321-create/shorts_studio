"""Phase 14 ADAPT-02 — elevenlabs adapter contract.

계약 축 (7축):
1. generate() 출력 = list[AudioSegment] (Plan 07 swap-compat with Typecast).
2. generate_with_timestamps() 가 ``words_by_scene`` 을 populate (word-level alignment).
3. _chars_to_words(D-10) 결정론 + 한국어 단어 경계 처리.
4. API-key dual env alias (ELEVENLABS_API_KEY + ELEVEN_API_KEY).
5. default_voice_id 3-tier resolution (kwarg > ELEVENLABS_DEFAULT_VOICE_ID env
   > module cache > API discovery). Constructor tier 1+2 부분 검증.
6. 빈 scene text 입력 → ValueError raise (침묵 폴백 금지, 금기 #3).
7. Phase 7 ElevenLabsMock().allow_fault_injection is False (D-3 invariant).

real elevenlabs SDK 호출 없음 — ``_invoke_tts`` + ``_get_audio_duration`` seam 을
monkeypatch. ``_resolve_default_voice_id`` tier (c) discover_korean_default_voice
는 본 test 에서 호출되지 않도록 scenes 에 voice_id 를 항상 명시.

대표님 지시 (RESEARCH §ADAPT-02):
    adapter 단독 unit gate — pipeline 변경 없이 schema + API-key + retry/fallback +
    fault injection 4 축을 60s 이내 검증.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestrator.api.elevenlabs import (
    ElevenLabsAdapter,
    _chars_to_words,
)
from scripts.orchestrator.voice_first_timeline import AudioSegment

pytestmark = pytest.mark.adapter_contract


def _stub_duration(self, path: Path) -> float:  # noqa: ARG001
    """Deterministic duration stub for mp3 fixtures — bypasses pydub/ffprobe."""
    return 1.0


def test_generate_returns_audio_segment_list(monkeypatch, _fake_env, tmp_path):
    """generate() 반환값은 list[AudioSegment]; scene_id 순 정렬 유지."""

    def _stub_invoke_tts(self, *, text, voice_id, language_code, model_id):  # noqa: ARG001
        return b"fake-mp3-bytes"

    monkeypatch.setattr(ElevenLabsAdapter, "_invoke_tts", _stub_invoke_tts)
    monkeypatch.setattr(ElevenLabsAdapter, "_get_audio_duration", _stub_duration)

    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)
    scenes = [
        {"scene_id": 1, "text": "안녕하세요", "voice_id": "v1"},
        {"scene_id": 2, "text": "반갑습니다", "voice_id": "v1"},
    ]
    result = adapter.generate(scenes)

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(s, AudioSegment) for s in result)
    # Scene ordering 유지 (D-10 alignment 계약).
    assert [s.index for s in result] == [1, 2]


def test_generate_with_timestamps_populates_words_by_scene(monkeypatch, _fake_env, tmp_path):
    """generate_with_timestamps — ``words_by_scene`` dict[int, list[dict]] populate.

    D-10 alignment 계약: character-level → word-level via _chars_to_words.
    """

    def _stub_invoke_tts_with_timestamps(
        self, *, text, voice_id, language_code, model_id  # noqa: ARG001
    ):
        alignment = {
            "characters": list("hi there"),
            "character_start_times_seconds": [
                0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,
            ],
            "character_end_times_seconds": [
                0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8,
            ],
        }
        return b"fake-mp3-bytes", alignment

    monkeypatch.setattr(
        ElevenLabsAdapter,
        "_invoke_tts_with_timestamps",
        _stub_invoke_tts_with_timestamps,
    )
    monkeypatch.setattr(ElevenLabsAdapter, "_get_audio_duration", _stub_duration)

    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)
    result = adapter.generate_with_timestamps(
        [{"scene_id": 1, "text": "hi there", "voice_id": "v1"}]
    )

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], AudioSegment)

    # words_by_scene 계약: dict[int, list[dict]] — scene_id key + word dict.
    assert isinstance(adapter.words_by_scene, dict)
    assert 1 in adapter.words_by_scene
    words = adapter.words_by_scene[1]
    assert isinstance(words, list)
    assert len(words) == 2
    assert words[0]["word"] == "hi"
    assert words[1]["word"] == "there"


def test_chars_to_words_round_trip():
    """D-10 _chars_to_words 결정론 — 동일 입력 → 동일 출력 + 한국어 word boundary."""
    chars = list("안녕 세계")
    starts = [0.0, 0.1, 0.2, 0.3, 0.4]
    ends = [0.1, 0.2, 0.3, 0.4, 0.5]

    a = _chars_to_words(chars, starts, ends)
    b = _chars_to_words(chars, starts, ends)

    assert a == b  # determinism
    assert isinstance(a, list)
    assert len(a) == 2
    assert a[0]["word"] == "안녕"
    assert a[1]["word"] == "세계"
    # start/end 타입 계약 (float).
    assert isinstance(a[0]["start"], float)
    assert isinstance(a[0]["end"], float)


def test_api_key_dual_env_alias(monkeypatch, tmp_path):
    """ELEVENLABS_API_KEY (primary) 와 ELEVEN_API_KEY (alias) 둘 다 수용.

    둘 다 부재 시 ValueError (침묵 폴백 금지, 금기 #3).
    """
    # Baseline wipe.
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)

    # Primary: ELEVENLABS_API_KEY.
    monkeypatch.setenv("ELEVENLABS_API_KEY", "primary-key")
    a1 = ElevenLabsAdapter(api_key=None, output_dir=tmp_path)
    assert getattr(a1, "_api_key", None) == "primary-key"

    # Alias: ELEVEN_API_KEY (primary 제거 후).
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setenv("ELEVEN_API_KEY", "alias-key")
    a2 = ElevenLabsAdapter(api_key=None, output_dir=tmp_path)
    assert getattr(a2, "_api_key", None) == "alias-key"

    # Neither → ValueError.
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVEN_API_KEY", raising=False)
    with pytest.raises(ValueError):
        ElevenLabsAdapter(api_key=None, output_dir=tmp_path)


def test_default_voice_3tier_resolution(monkeypatch, tmp_path):
    """default_voice_id — Tier 1 (kwarg) + Tier 2 (ELEVENLABS_DEFAULT_VOICE_ID env).

    Tier 3 (module cache) + Tier 4 (discover_korean_default_voice API) 는 lazy —
    _resolve_default_voice_id() 호출 시 network I/O. 본 test 는 constructor
    tier 만 검증 (Phase 5 test_elevenlabs_adapter.py 가 lazy resolution 은 cover).
    """
    monkeypatch.delenv("ELEVENLABS_DEFAULT_VOICE_ID", raising=False)

    # Tier 1: kwarg 우선.
    a1 = ElevenLabsAdapter(
        api_key="fake", default_voice_id="v-kwarg", output_dir=tmp_path
    )
    assert getattr(a1, "_default_voice_id", None) == "v-kwarg"

    # Tier 2: env snapshot (constructor 시점 capture).
    monkeypatch.setenv("ELEVENLABS_DEFAULT_VOICE_ID", "v-env")
    a2 = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)
    assert getattr(a2, "_default_voice_id", None) == "v-env"


def test_empty_text_raises_value_error(_fake_env, tmp_path):
    """빈 scene text 입력 → ValueError (generate + generate_with_timestamps 양쪽).

    침묵 폴백 금지 (금기 #3): empty string 은 즉시 명시적 raise.
    """
    adapter = ElevenLabsAdapter(api_key="fake", output_dir=tmp_path)

    with pytest.raises(ValueError):
        adapter.generate([{"scene_id": 1, "text": "", "voice_id": "v1"}])

    with pytest.raises(ValueError):
        adapter.generate_with_timestamps(
            [{"scene_id": 1, "text": "", "voice_id": "v1"}]
        )


def test_elevenlabs_mock_fault_injection_disabled_by_default():
    """D-3 Phase 7 invariant — ElevenLabsMock().allow_fault_injection is False.

    Production-safe default: mock 은 fault injection 이 꺼진 채로 구동되며
    fault 를 주입하려면 테스트가 명시적으로 True 로 바꿔야 한다.

    Phase 7 mocks 는 ``tests/phase07/mocks/`` 아래에 위치하지만 ``tests/`` 는
    의도적으로 Python package 가 아니므로 (Phase 7 Plan 07-03 D-13 결정), 본
    contract test 는 importlib.util.spec_from_file_location 을 사용해 직접
    load — sys.path 를 오염시키지 않는다.
    """
    import importlib.util
    import sys

    mock_path = (
        Path(__file__).resolve().parents[1]
        / "phase07"
        / "mocks"
        / "elevenlabs_mock.py"
    )
    assert mock_path.exists(), (
        f"tests/phase07/mocks/elevenlabs_mock.py 가 존재해야 함 "
        f"(D-3 Phase 7 mock): {mock_path}"
    )
    mod_name = "_phase07_elevenlabs_mock_contract"
    spec = importlib.util.spec_from_file_location(mod_name, mock_path)
    assert spec is not None and spec.loader is not None, (
        "importlib.util.spec_from_file_location 로부터 valid spec 획득 실패."
    )
    module = importlib.util.module_from_spec(spec)
    # @dataclass 의 field type resolution 은 ``sys.modules[cls.__module__]`` 를
    # 조회하므로 exec_module 전 등록 필수. 오염 최소화: 고유 prefix 사용.
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
        mock = module.ElevenLabsMock()
        assert mock.allow_fault_injection is False, (
            "ElevenLabsMock().allow_fault_injection 기본값이 False 여야 함 "
            "(D-3 Phase 7 production-safe default)."
        )
    finally:
        sys.modules.pop(mod_name, None)
