---
category: kpi
status: ready
tags: [taste-gate, monthly-review, protocol]
updated: 2026-04-20
---

# Taste Gate Protocol — 월 1회 대표님 평가 회로

> B-P4 (자동화 taste filter 0) 구조적 방어. 인간 감독 게이트의 마지막 설치.
> 자동 파이프라인만으로는 포착 불가능한 채널 정체성 드리프트 + 품질 드리프트를
> 대표님의 직접 평가로 한 달에 한 번 바로잡는다. KPI-05 충족.

## 1. Purpose (KPI-05)

매월 1회 대표님이 지난 30일 업로드 영상 중 **상위 3 / 하위 3**을 직접 평가하여
자동 파이프라인만으로는 포착 불가능한 **채널 정체성 드리프트 + 품질 드리프트**를 감지한다.

- **왜 필요한가:** 자동 inspector 17종은 "measurable" 품질만 검사. "대표님이 보기에 좋은가"는 측정 불가.
- **왜 월 1회:** 매일 평가는 피로 누적 → 드리프트 감지 실패. 월 1회가 피로 vs 감도의 sweet spot.
- **왜 대표님 sole reviewer:** 채널 정체성의 단일 권위자. 분산 평가는 drift 가속.

## 2. Cadence (D-11)

- **Trigger:** **매월 1일 KST 09:00** (한국 표준시 09:00 정각)
- **Automation status:** Phase 9 문서화만. **Phase 10에서 cron으로 자동화** 예정.
- **Reviewer:** 대표님 (sole reviewer, 위임 불가)
- **Max review time:** **30분** (6 영상 × 5분 상한)
- **Grace period:** 매월 1일 ~ 5일 (5일 경과 시 Slack/Discord 알림 재전송 예정 — Phase 10 구현)

> ⚠️ 리뷰 skip 금지 — 해당 월 기록이 누락되면 kpi_log.md 월간 트렌드가 깨짐.
> 바쁜 경우 최소한 상위 3만 평가 후 하위 3는 "보류" 태그로 차월로 이월.

## 3. Selection Method (D-08, semi-automated)

1. 지난 30일 업로드 영상 전수 → YouTube Analytics v2 `audienceWatchRatio[3]` 조회
2. **3sec_retention** 기준 정렬 → **상위 3 + 하위 3** 자동 선별
3. Phase 10 `scripts/analytics/fetch_kpi.py`가 결과를 `wiki/kpi/taste_gate_YYYY-MM.md` 표로 pre-fill
4. 대표님은 평가 컬럼 3개만 작성 (자동 선별 결과는 수정 금지 — 감정 개입 차단)

**선별 기준이 3초 retention인 이유:**
- ROADMAP KPI-01 목표값이 3초 hook > 60% (가장 critical signal)
- 완주율/평균 시청보다 알고리즘 feedback 속도가 빠름
- `audienceWatchRatio` 배열의 4번째 요소(index 3 = 3초 지점)가 해당 지표

## 4. Evaluation Form (D-09, Markdown single file)

- **Path:** `wiki/kpi/taste_gate_YYYY-MM.md` (월별 1개 파일)
- **Format:** **Markdown 단일 파일** (Google Form 거부)
- **Editor:** VSCode 또는 Obsidian
- **Editor 허용 이유:** git 추적 / offline / privacy / 외부 의존 0

**왜 Google Form 거부:**
- 외부 dep: Google 계정 + 인증 flow 필요
- privacy: 제3자 서버에 평가 데이터 저장됨
- git-untracked: 평가 이력이 저장소에 남지 않음 → 후속 세션 참조 불가
- 검색 불가: `grep -r` 로 평가 기록 뒤질 수 없음

**3 평가 컬럼 (대표님이 작성):**
- **품질 (1-5):** 전반적 영상 완성도 (5 = 대표님 기준 이상적)
- **한줄 코멘트:** 느낀 점 (한국어 자유 서술, 1문장 권장)
- **태그 (선택):** 재사용 / 재생산 / 폐기 / 후속편 후보 / 유지 등

**나머지 6 컬럼 (자동 pre-fill):**
- `#` / `video_id` / `title` / `3sec_retention` / `완주율` / `평균 시청`
- 자동 선별 결과이므로 대표님이 수정하지 않음 (D-08 원칙)

## 5. Feedback Flow (D-12, D-13)

작성 완료 후 CLI 실행:

```bash
python scripts/taste_gate/record_feedback.py --month 2026-04
```

**파서 동작 (Plan 09-04 구현 예정):**

1. `wiki/kpi/taste_gate_YYYY-MM.md` 파싱 → 6개 평가 entry 추출
2. 각 entry에 대해 D-13 필터 적용:
   - **score <= 3** → `.claude/failures/FAILURES.md` 하단에 `### [taste_gate] YYYY-MM 리뷰 결과` 섹션으로 append
   - **score 4 또는 5** → `wiki/kpi/kpi_log.md` Part B에만 "유지" 태그로 기록, FAILURES.md 승격 없음
3. append 방식은 Phase 6 D-11 hook (append-only 검증) 재사용 — 기존 엔트리 불변

**D-13 필터 rationale:**
- **상위 3 (score 4-5):** 유지/재생산 가치. Producer 입력에 "모범 사례"로만 활용.
- **하위 3 중 score > 3:** 평균 이하지만 고쳐야 할 만큼 나쁘지 않음 (노이즈). kpi_log.md에만 기록.
- **하위 3 중 score <= 3:** 명백한 실패. FAILURES.md 승격 → 차월 Producer 입력에 반영 (Phase 10).

**예상 월간 승급 건수:** 1~3건 (하위 3의 일부). 6건 전부 승급 시 채널 전반 위기 신호.

## 6. Dry-run Strategy (D-10, D-14)

- **Phase 9 first dry-run:** `wiki/kpi/taste_gate_2026-04.md` (synthetic sample 6 + `status=dry-run` 프론트매터)
- **Purpose:** 대표님이 "평가 포맷이 편한가" UX 검증만. 실 영상 데이터 없음.
- **Synthetic video IDs:** **6-char obviously-fake** (abc123, def456, ghi789, jkl012, mno345, pqr678)
- **Persona:** **shorts_naberal 탐정/조수 승계** — 현실적 제목 사용 ("탐정이 조수에게 묻다...", "100억 갑부..." 등)
- **금지 문구:** "테스트용 쇼츠", "샘플 영상 1", 기타 placeholder 제목 — Pitfall 3 (후속 세션이 dry-run을 실 데이터로 오인)

**DRY-RUN 배너:**
`taste_gate_YYYY-MM.md` 첫 본문 라인에 반드시 포함:

```markdown
> ⚠️ **DRY-RUN (D-10 synthetic sample)** — 실 데이터는 Phase 10 Month 1에서 수집.
> 이 파일은 포맷 검증용. 실제 YYYY-MM 업로드 영상과 무관.
```

**E2E 검증 (D-14, Plan 09-05):**
합성 dry-run → `record_feedback.py` 실행 → FAILURES.md에 정확히 3건 승급 (score 3, 2, 1) 확인.

## 7. Related

- [[kpi_log]] — KPI targets + monthly tracking companion (Plan 09-02 target)
- [[taste_gate_2026-04]] — first dry-run (Phase 9 Plan 09-03 target)
- [[MOC]] — KPI 카테고리 노드 맵
- `.claude/failures/FAILURES.md` — append-only sink (Phase 6 D-11 Hook-enforced)
- `scripts/taste_gate/record_feedback.py` — CLI appender (Phase 9 Plan 09-04 target)
- `scripts/analytics/fetch_kpi.py` — auto selection script (Phase 10 target)

---

*Created: 2026-04-20 (Phase 9 Plan 09-03)*
*First auto-trigger: Phase 10 Month 1 cron (매월 1일 KST 09:00)*
*Reviewer: 대표님 (sole authority)*
