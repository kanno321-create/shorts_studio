"""Phase 13 Provider Rates — SMOKE-05 budget cap 단가 SSOT.

Research §SMOKE-05 Provider unit prices table (13-RESEARCH.md L320-332) 를 코드
SSOT 로 anchoring. Wave 4 ``phase13_live_smoke.py`` 가 실 adapter 호출 후
``counter.charge(provider, PROVIDER_RATES_USD[provider] * units)`` 형태로 import
하여 사용 — 드리프트 시 본 모듈이 단일 수정 포인트.

사용 예:
    >>> from scripts.smoke.budget_counter import BudgetCounter
    >>> from scripts.smoke.provider_rates import (
    ...     PROVIDER_RATES_USD, estimate_adapter_cost,
    ... )
    >>> counter = BudgetCounter(cap_usd=5.00, evidence_path=...)
    >>> counter.charge("kling", estimate_adapter_cost("kling", 8))  # $2.80
    >>> counter.charge("typecast", estimate_adapter_cost("typecast"))  # $0.12

**Research metadata**: confidence MEDIUM, valid_until 2026-05-21. Wave 0 Preflight
재실행 시 본 표 drift 재확인 권장 (FAL/Typecast dashboard 공시 단가 대조).

**CLAUDE.md 금기 #3 준수**: unknown provider 요청 시 ``raise KeyError`` —
silent $0 fallback 은 오기 버그 (e.g. "klin" 오타) 은폐 위험이므로 명시적
실패. 상위 호출자는 ``try/except KeyError`` 로만 좁혀 잡아야 하며, 과금 코드
경로에서 provider 오타는 GATE 로 기록 후 즉시 중단 (필수 #8 증거 기반).
"""
from __future__ import annotations


# Research §SMOKE-05 Provider unit prices table (13-RESEARCH.md L322-331).
# Lowercase + snake_case keys — grep 검색 용이성 + 금기 #3 silent fallback 방지.
# Values 를 수정하려면 반드시 13-RESEARCH.md 의 Source column 근거를 함께 갱신.
PROVIDER_RATES_USD: dict[str, float] = {
    # Max 구독 inclusive — MEMORY.project_claude_code_max_no_api_key
    "claude_cli": 0.00,
    # Max 구독 inclusive — Google One NotebookLM
    "notebooklm": 0.00,
    # Free within 10K/day quota — smoke run ≈ 1651 units
    "youtube_api": 0.00,
    # per image — Phase 9.1 Plan 06 live smoke manifest 실측
    "nanobanana": 0.04,
    # per 5s clip — FAL rate ≈ $0.07/sec (project_video_stack_kling26.md)
    "kling": 0.35,
    # per 5s clip fallback — Phase 9.1 Plan 06 live smoke $0.25 실측
    "runway": 0.25,
    # per 1K chars — project_tts_stack_typecast.md creator tier
    "typecast": 0.12,
    # per 1K chars fallback — 공시 ElevenLabs Creator tier
    "elevenlabs": 0.30,
}


def estimate_adapter_cost(provider: str, units: float = 1.0) -> float:
    """Compute adapter cost given provider key + units consumed.

    Args:
        provider: ``PROVIDER_RATES_USD`` 의 key. 대소문자·공백 정규화 없음 —
            grep 가능성 보장을 위해 호출자가 lowercase snake_case 로 전달.
        units: 사용량 배수 (default 1.0). 예: Kling 8 cuts → ``units=8``,
            Typecast 1.5K chars → ``units=1.5``.

    Returns:
        ``PROVIDER_RATES_USD[provider] * units`` (USD, 소수점 4자리 반올림).

    Raises:
        KeyError: provider 가 rates table 에 미등록 시. CLAUDE.md 금기 #3
            (try-except 침묵 폴백) 준수 — silent $0 fallback 으로 오타 은폐
            방지.
    """
    if provider not in PROVIDER_RATES_USD:
        raise KeyError(
            f"unknown provider '{provider}' — "
            f"Research §SMOKE-05 rates table 미등록 (대표님: provider_rates.py "
            f"수정 필요)"
        )
    return round(PROVIDER_RATES_USD[provider] * float(units), 4)


def all_known_providers() -> list[str]:
    """Return sorted list of provider keys for audit/logging.

    Wave 4 ``phase13_live_smoke.py`` 의 startup banner + 감사 로그에서 사용 —
    과금 가능한 adapter 전수를 명시적으로 로깅하여 drift detection 용이.
    """
    return sorted(PROVIDER_RATES_USD.keys())
