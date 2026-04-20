"""ElevenLabs voice discovery utility (REQ-091-06, Phase 9.1).

Resolves the default Korean voice for 대표님's ElevenLabs account via
``GET /v1/voices``. 3-tier priority:

    1. ``labels.language == 'ko'``  (Korean-labelled voice)
    2. ``category == 'premade'``   (safe default)
    3. first voice in the list     (last resort)

D-13 rationale: the hardcoded ``detective_hao`` default in
:class:`~scripts.orchestrator.api.elevenlabs.ElevenLabsAdapter` is not
registered on 대표님's account (2026-04-20 실측 FAIL). Discovery via
``GET /v1/voices`` with the 3-tier filter is the source of truth.

Pitfall 9: if the account has no Korean voice, Tier 2/3 would return an
English voice that synthesises broken Korean. Callers should set
``ELEVENLABS_DEFAULT_VOICE_ID`` env or request 대표님 to add a Korean
voice. Detection of Tier-2/3 fallback belongs to the caller
(:class:`ElevenLabsAdapter`) — this module is a pure discovery function.
"""
from __future__ import annotations

import os

import httpx

__all__ = ["discover_korean_default_voice"]

_ELEVENLABS_VOICES_URL = "https://api.elevenlabs.io/v1/voices"
_HTTP_TIMEOUT_S = 30


def discover_korean_default_voice(api_key: str | None = None) -> str:
    """Return the most appropriate voice_id for Korean dialogue synthesis.

    Parameters
    ----------
    api_key:
        Optional explicit key. Falls back to ``$ELEVENLABS_API_KEY`` then
        ``$ELEVEN_API_KEY``.

    Returns
    -------
    str
        A valid voice_id registered on the caller's ElevenLabs account.

    Raises
    ------
    ValueError
        No API key resolvable.
    RuntimeError
        Account has zero voices.
    httpx.HTTPError
        Network / HTTP-level failure (propagated — no silent except per
        CLAUDE.md Hook 3종 차단).
    """
    key = (
        api_key
        or os.environ.get("ELEVENLABS_API_KEY")
        or os.environ.get("ELEVEN_API_KEY")
    )
    if not key:
        raise ValueError(
            "ElevenLabs API 키 미설정 — 대표님 .env 확인 필요 "
            "(ELEVENLABS_API_KEY 또는 ELEVEN_API_KEY)"
        )

    resp = httpx.get(
        _ELEVENLABS_VOICES_URL,
        headers={"xi-api-key": key, "accept": "application/json"},
        timeout=_HTTP_TIMEOUT_S,
    )
    resp.raise_for_status()
    voices = resp.json().get("voices", [])

    # Tier 1: Korean-labelled voice.
    for v in voices:
        if v.get("labels", {}).get("language") == "ko":
            return v["voice_id"]
    # Tier 2: premade voice (safe English default that still vocalises Korean).
    for v in voices:
        if v.get("category") == "premade":
            return v["voice_id"]
    # Tier 3: first available voice.
    if voices:
        return voices[0]["voice_id"]

    raise RuntimeError(
        "대표님 ElevenLabs 계정에 사용 가능한 voice 가 없습니다 — "
        "대시보드에서 voice 추가 또는 ELEVENLABS_DEFAULT_VOICE_ID env 설정 필요"
    )
