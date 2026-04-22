"""Phase 16-03 — subtitle producer package (faster-whisper large-v3 + 3종 출력).

subtitle-producer 에이전트의 핵심 구현. word_subtitle.py 는 1:1 harvested port —
FAIL-EDT-008 (Korean word timestamp drift) 방어 파이프라인 (clamp/merge/fallback) 보전.
"""

__all__ = ["word_subtitle"]
