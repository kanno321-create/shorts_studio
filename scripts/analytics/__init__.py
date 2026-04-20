"""scripts.analytics — YouTube Analytics v2 + 월간 집계. Phase 10 신규 (KPI-01/02).

Modules:
    - fetch_kpi          : daily YouTube Analytics v2 fetch CLI (KPI-01)
    - monthly_aggregate  : month-end aggregator + kpi_log.md Part B appender (KPI-02)

Stdlib-only + googleapiclient. pandas 미사용 (RESEARCH Plan 3 Open Q4 결정).
"""
from __future__ import annotations

__all__ = []
