"""scripts.schedule — Phase 10 sustained operations scheduler.

Windows Task Scheduler PowerShell 스크립트 + 실패 알림 3채널 (stdout / SMTP / FAILURES append).
GH Actions cron 4종 (`.github/workflows/`) 과 조합하여 하이브리드 scheduling 을 제공합니다.

CLAUDE.md 도메인 절대 규칙 #8 (AF-1 / AF-11): 주 3~4편 페이스 enforce 는
`scripts/publisher/publish_lock.py` (48h+jitter) 가 수행합니다. 본 모듈은 트리거 등록만
담당하고 실제 페이스 gating 은 publish_lock 에 위임합니다.
"""
from __future__ import annotations

__all__: list[str] = []
