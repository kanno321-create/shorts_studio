"""KST peak window enforcement — Phase 8 PUB-03 D-07.

CONTEXT D-07 contract:
- Weekday (Monday-Friday, ``weekday() in 0..4``): 20:00-22:59 KST
  (lower bound inclusive, upper bound exclusive → ``20 <= hour < 23``)
- Weekend (Saturday-Sunday, ``weekday() in 5..6``): 12:00-14:59 KST
  (lower bound inclusive, upper bound exclusive → ``12 <= hour < 15``)

Source of truth = ``zoneinfo.ZoneInfo("Asia/Seoul")``. The ``pytz`` library is
deprecated (RESEARCH Anti-Patterns) and forbidden here — only Python 3.9+
stdlib ``zoneinfo`` is used.

Raises ``PublishWindowViolation`` (with ``weekday`` + ``hour`` attributes per
CD-02 exception hierarchy) on every out-of-window call. The publisher caller
is expected to either sleep until the next window or abort the upload.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.publisher.exceptions import PublishWindowViolation


KST = ZoneInfo("Asia/Seoul")

logger = logging.getLogger(__name__)


def assert_in_window(*, now_kst: datetime | None = None) -> None:
    """Raise :class:`PublishWindowViolation` if ``now_kst`` is outside the window.

    Parameters
    ----------
    now_kst
        Inject a frozen clock for deterministic tests. Must already be
        localised to ``KST``. Defaults to ``datetime.now(KST)`` in production.

    Semantics
    ---------
    - weekday in 0..4 (Mon-Fri): ``20 <= hour < 23`` passes.
    - weekday in 5..6 (Sat-Sun): ``12 <= hour < 15`` passes.
    - Anything else raises with the offending ``weekday`` + ``hour`` attached.
    """
    # Session #31 — smoke / off-peak 검증 경로 bypass. 운영에는 절대 금지
    # (AF-11). 환경 변수 명시 지정 + logger.warning 로 explicit surface.
    if os.environ.get("SHORTS_KST_WINDOW_BYPASS") == "1":
        logger.warning(
            "[kst_window] SHORTS_KST_WINDOW_BYPASS=1 — 업로드 윈도우 게이트 우회 (대표님 smoke only)",
        )
        return
    now = now_kst or datetime.now(KST)
    weekday = now.weekday()
    hour = now.hour
    is_weekday = weekday < 5
    if is_weekday:
        ok = 20 <= hour < 23
    else:
        ok = 12 <= hour < 15
    if not ok:
        raise PublishWindowViolation(weekday=weekday, hour=hour)


__all__ = ["KST", "assert_in_window"]
