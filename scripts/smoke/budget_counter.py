"""Phase 13 Budget Counter — SMOKE-05 $5 cap enforcement SSOT.

Phase 9.1 ``_check_cost_cap`` (phase091_stage2_to_4.py) 의 file-persisted 확장.
본 모듈은 Wave 1~4 가 공통으로 import 하는 단일 SSOT — 모든 실 API 과금은
이 counter 를 경유해야 $5 cap 이 유효하게 enforced.

Contract (13-01-PLAN.md interfaces 블록):
    class BudgetExceededError(RuntimeError): ...
    class BudgetCounter:
        def __init__(self, cap_usd: float, evidence_path: Path) -> None: ...
        @property
        def total_usd(self) -> float: ...
        def charge(self, provider: str, amount_usd: float,
                   metadata: dict | None = None) -> None: ...
        def persist(self) -> Path: ...

CLAUDE.md 금기사항 #3 (try/except 침묵 폴백) 준수 — 초과 시 명시적
``BudgetExceededError`` raise, 상위 호출자가 ``except BudgetExceededError`` 로만
좁게 catch 할 수 있도록 named class 로 분리.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class BudgetExceededError(RuntimeError):
    """예산 상한 초과 — 대표님 중단.

    CLAUDE.md 금기 #3 (try/except 침묵 폴백) 위반 방지용 named class. 상위
    호출자가 ``except BudgetExceededError`` 로만 잡을 수 있도록 좁힘. 일반
    ``RuntimeError`` 를 상속하므로 기존 Phase 9.1 ``_check_cost_cap`` 패턴과
    호환.
    """


class BudgetCounter:
    """In-memory ledger + evidence JSON persistence.

    SMOKE-05 요구사항:
      - ``charge()`` 가 cap 초과 projected total 을 detect → BudgetExceededError
      - ``entries[]`` 에 provider + amount_usd + cumulative_usd + timestamp +
        metadata 기록
      - ``persist()`` 가 ``.planning/phases/13-*/evidence/budget_usage.json`` 등
        evidence_path 에 ensure_ascii=False 로 write (한국어 metadata readable)

    Attributes:
        cap_usd: 하드 상한 (USD). 초과 시 RuntimeError.
        evidence_path: ``persist()`` 대상 JSON 파일 경로. parent dir 은
            ``persist()`` 시점에 mkdir.
        entries: 누적 ledger — source of truth. ``total_usd`` 는 이 리스트
            합계의 property view.

    Design notes:
        - ``total_usd`` 는 property — 중간에 mutable state 로 두지 않아
          entries[] 와 총합이 drift 할 수 없도록 함.
        - round(..., 4) — float epsilon drift 방지 (e.g. 0.1 + 0.2 = 0.3000001).
        - ``charge()`` 는 실패 시 entries 에 append 하지 않음 (atomic) — Test 3.
    """

    def __init__(self, cap_usd: float, evidence_path: Path) -> None:
        self.cap_usd = float(cap_usd)
        self.evidence_path = Path(evidence_path)
        self.entries: list[dict] = []

    @property
    def total_usd(self) -> float:
        """현재 누적 합계 (entries[] view)."""
        return round(sum(e["amount_usd"] for e in self.entries), 4)

    def charge(
        self,
        provider: str,
        amount_usd: float,
        metadata: dict | None = None,
    ) -> None:
        """Charge 1건 기록 + cap 초과 시 즉시 RuntimeError.

        Args:
            provider: e.g. ``"kling"``, ``"typecast"``, ``"claude_cli"``.
            amount_usd: 비용 (USD). $0.00 허용 (Max 구독 ledger 완전성 — Test 4).
            metadata: 부가 컨텍스트 (optional). 한국어 value 허용.

        Raises:
            BudgetExceededError: projected total (현재 합 + amount_usd) >
                ``cap_usd``. entries 는 변경되지 않음 (atomic).
        """
        projected = self.total_usd + float(amount_usd)
        if projected > self.cap_usd:
            raise BudgetExceededError(
                f"예산 상한 초과 ${projected:.2f} > ${self.cap_usd:.2f} "
                f"대표님 중단 (직전: {provider} ${amount_usd:.2f})"
            )
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "amount_usd": round(float(amount_usd), 4),
            "cumulative_usd": round(projected, 4),
            "metadata": metadata or {},
        })

    def persist(self) -> Path:
        """Evidence JSON 파일 write.

        Returns:
            write 대상 경로 (``evidence_path``).

        Side effects:
            - parent dir 생성 (``parents=True, exist_ok=True``)
            - ``ensure_ascii=False`` + ``indent=2`` — 한국어 readable +
              human-diffable.

        Schema (SMOKE-05 evidence shape):
            {
              "cap_usd": float,
              "total_usd": float,
              "breached": bool,
              "entry_count": int,
              "entries": [ {timestamp, provider, amount_usd, cumulative_usd,
                            metadata}, ... ]
            }
        """
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "cap_usd": self.cap_usd,
            "total_usd": self.total_usd,
            "breached": self.total_usd > self.cap_usd,
            "entry_count": len(self.entries),
            "entries": self.entries,
        }
        self.evidence_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.evidence_path
