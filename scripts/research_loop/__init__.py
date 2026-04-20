"""scripts.research_loop — Auto Research Loop (KPI-03 / KPI-04).

Phase 10 Plan 10-06 신규 네임스페이스.

월 1회 실행되어 이전 월 KPI aggregate (Plan 10-03) 결과와 NotebookLM retrospective
답변을 결합한 ``wiki/kpi/monthly_context_YYYY-MM.md`` 를 생성합니다. Producer AGENT.md
는 ``@wiki/kpi/monthly_context_latest.md`` 로 참조하여 다음 월 입력에 KPI 피드백을
반영합니다 (KPI-04 end-to-end cascade 는 D-2 Lock 해제 후 별도 Plan 에서 wikilink 추가).
"""
from __future__ import annotations

__all__: list[str] = []
