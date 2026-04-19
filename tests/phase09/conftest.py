"""Phase 9 documentation + KPI + Taste Gate shared fixtures.

D-13 independence from phase05/06/07/08 conftests per Phase 7 precedent.
Per 09-CONTEXT.md D-10 (synthetic sample 6) + D-12 (FAILURES append-only) + D-14 (synthetic E2E).

Fixtures provided
-----------------
- synthetic_taste_gate_april : Path to tmp wiki/kpi/taste_gate_2026-04.md seeded with D-10
                               synthetic sample 6 (탐정/조수 페르소나 titles, fake 6-char video_ids
                               abc123/def456/ghi789/jkl012/mno345/pqr678; scores [5,4,4,3,2,1]).
- tmp_failures_md            : Path to tmp FAILURES.md seeded with Phase 6 prefix. Optionally
                               monkeypatches scripts.taste_gate.record_feedback.FAILURES_PATH if
                               the module is importable (Wave 0 RED state — no-op otherwise).
- freeze_kst_2026_04_01      : Monkeypatches datetime.now(KST) inside scripts.taste_gate.record_feedback
                               to return 2026-04-01T09:00:00+09:00 (deterministic build_failures_block
                               timestamps for E2E tests). No-op if module not importable.
"""
from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# UTF-8 safeguard for Windows cp949 per Phase 6 Plan 06-09 STATE #28 + Research Pitfall 7
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# tests/phase09/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
KST = ZoneInfo("Asia/Seoul")

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


_SYNTHETIC_APRIL_CONTENT = """---
category: kpi
status: dry-run
tags: [taste-gate, monthly-review, dry-run]
month: 2026-04
reviewer: 대표님
selected_at: 2026-04-01T09:00:00+09:00
selection_method: semi-auto (top3 + bottom3 by 3sec_retention over last 30 days)
---

# Taste Gate 2026-04 — 월간 상/하위 3 영상 평가 (DRY-RUN)

> ⚠️ **DRY-RUN (D-10 synthetic sample)** — 실 데이터는 Phase 10 Month 1에서 수집. 이 파일은 포맷 검증용.

## 상위 3 (3초 retention 기준)

| # | video_id | title | 3sec_retention | 완주율 | 평균 시청 | 품질 (1-5) | 한줄 코멘트 | 태그 |
|---|----------|-------|---:|---:|---:|:---:|:---|:---|
| 1 | abc123 | "탐정이 조수에게 묻다: 23살 범인의 진짜 동기?" | 68% | 42% | 27초 | 5 | 완성도 우수 | 재생산 |
| 2 | def456 | "100억 갑부가 딱 한 번 울었던 순간" | 64% | 41% | 26초 | 4 | 훌륭함 | 유지 |
| 3 | ghi789 | "3번째 편지의 의미를 아시나요?" | 61% | 40% | 25초 | 4 | 좋음 | 유지 |

## 하위 3

| # | video_id | title | 3sec_retention | 완주율 | 평균 시청 | 품질 (1-5) | 한줄 코멘트 | 태그 |
|---|----------|-------|---:|---:|---:|:---:|:---|:---|
| 4 | jkl012 | "조수가 놓친 단서" | 48% | 28% | 19초 | 3 | hook 약함 | 재제작 |
| 5 | mno345 | "5번 방문한 이유" | 45% | 25% | 17초 | 2 | 지루함 | 폐기 |
| 6 | pqr678 | "범인의 마지막 말" | 42% | 24% | 16초 | 1 | 결말 처참 | 폐기 |
"""


_SEED_FAILURES_MD = """---
schema: failures-reservoir-v1
locked_by_sha256: placeholder
---

# FAILURES.md — 실패 저수지

> Append-only per Phase 6 D-11. Prior entries are immutable (Hook enforced).

## Failures

### FAIL-000: seed placeholder
- **Tier**: C
- **발생 세션**: 2026-04-01T00:00:00+09:00
- **재발 횟수**: 1
- **Trigger**: Phase 9 conftest seed (test-only)
- **무엇**: Phase 9 tmp_failures_md fixture prefix anchor
- **왜**: Hook append-only 검증을 위한 선행 엔트리
- **정답**: N/A — fixture
- **검증**: tests/phase09/test_failures_append_only.py
- **상태**: observed
"""


@pytest.fixture
def synthetic_taste_gate_april(tmp_path: Path) -> Path:
    """D-10 synthetic sample 6 based on shorts_naberal 탐정/조수 페르소나.

    Writes tmp_path/wiki/kpi/taste_gate_2026-04.md with status=dry-run + 6 evaluated rows.
    Video IDs are obviously-fake 6-char (abc123, def456, ghi789, jkl012, mno345, pqr678)
    per Research Pitfall 3. Scores are [5, 4, 4, 3, 2, 1] per D-13 (3 escalate: 3/2/1).
    """
    wiki_kpi = tmp_path / "wiki" / "kpi"
    wiki_kpi.mkdir(parents=True, exist_ok=True)
    path = wiki_kpi / "taste_gate_2026-04.md"
    path.write_text(_SYNTHETIC_APRIL_CONTENT, encoding="utf-8")
    return path


@pytest.fixture
def tmp_failures_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirects FAILURES_PATH to tmp_path/FAILURES.md seeded with existing Phase 6 prefix.

    So the append-only Hook contract is testable in isolation. Must preserve prior content.

    Wave 0 RED state: scripts.taste_gate.record_feedback is not yet implemented (Plan 09-04
    target). We attempt a best-effort monkeypatch on the module's FAILURES_PATH attribute if
    importable; otherwise the fixture is a no-op besides seeding the file on disk — downstream
    tests that need the monkeypatch guard will themselves `pytest.importorskip(...)` the module.
    """
    failures = tmp_path / "FAILURES.md"
    failures.write_text(_SEED_FAILURES_MD, encoding="utf-8")
    try:
        rf = importlib.import_module("scripts.taste_gate.record_feedback")
    except ModuleNotFoundError:
        # Plan 09-04 not yet shipped — fixture only seeds disk; downstream tests skip via importorskip.
        return failures
    if hasattr(rf, "FAILURES_PATH"):
        monkeypatch.setattr(rf, "FAILURES_PATH", failures)
    return failures


@pytest.fixture
def freeze_kst_2026_04_01(monkeypatch: pytest.MonkeyPatch):
    """Freezes datetime.now(KST) to 2026-04-01T09:00:00+09:00 for deterministic
    build_failures_block timestamps in E2E tests.

    Implementation: replaces the module-level `datetime` reference inside
    scripts.taste_gate.record_feedback with a subclass whose .now() returns the frozen moment.
    No-op if the module is not yet importable (Plan 09-04 target).
    """
    frozen = datetime(2026, 4, 1, 9, 0, 0, tzinfo=KST)

    class _FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            if tz is None:
                return frozen.replace(tzinfo=None)
            return frozen.astimezone(tz)

    try:
        rf = importlib.import_module("scripts.taste_gate.record_feedback")
    except ModuleNotFoundError:
        return frozen
    if hasattr(rf, "datetime"):
        monkeypatch.setattr(rf, "datetime", _FrozenDateTime)
    return frozen
