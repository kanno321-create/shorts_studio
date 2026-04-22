---
category: kpi
status: dry-run
tags: [taste-gate, monthly-review, dry-run]
month: 2026-04
reviewer: 대표님
selected_at: 2026-04-01T09:00:00+09:00
selection_method: semi-auto (top3 + bottom3 by 3sec_retention over last 30 days)
updated: 2026-04-20
---

# Taste Gate 2026-04 — 월간 상/하위 3 영상 평가

> ⚠️ **DRY-RUN (D-10 synthetic sample)** — 실 데이터는 Phase 10 Month 1에서 수집. 이 파일은 포맷 검증용. 실제 2026-04 업로드 영상과 무관.

## 📖 평가 방법

6개 영상 각각에 대해 3개 컬럼 작성:
- **품질 (1-5):** 전반적 영상 완성도 (5 = 대표님 기준 이상적)
- **한줄 코멘트:** 느낀 점 (한국어 자유 서술)
- **태그 (선택):** 재사용 / 재생산 / 폐기 / 후속편 후보 등

작성 완료 후 CLI 실행:

```
python scripts/taste_gate/record_feedback.py --month 2026-04
```

필터: 품질 3 이하 항목만 `.claude/failures/FAILURES.md`로 승급. 4-5점은 [[kpi_log]] "유지" 기록만.

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

## 기대 승급 결과 (D-13 dry-run 검증)

이 dry-run은 Plan 09-05 E2E 테스트가 **정확히 3건 승급**을 확인하도록 설계됨:

- **jkl012 (score 3)** → FAILURES.md 승급 (D-13 경계선 포함)
- **mno345 (score 2)** → FAILURES.md 승급
- **pqr678 (score 1)** → FAILURES.md 승급

상위 3 (score 4-5) + 하위 3 중 score 3 위는 FAILURES.md 승급 없음. 점수 분포 `[5, 4, 4, 3, 2, 1]`.

## Related

- [[taste_gate_protocol]] — 평가 회로 문서 (Plan 09-03 protocol 본체)
- [[kpi_log]] — 월별 KPI 추적 companion (Plan 09-02)

---

*Created: 2026-04-20 (Phase 9 Plan 09-03)*
*Status: dry-run (Phase 10 Month 1 첫 실 데이터 수집 전 포맷 검증용)*
