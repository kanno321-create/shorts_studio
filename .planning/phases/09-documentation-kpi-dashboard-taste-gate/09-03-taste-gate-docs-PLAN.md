---
plan: 09-03
phase: 9
wave: 1
depends_on: [09-00]
files_modified:
  - wiki/kpi/taste_gate_protocol.md
  - wiki/kpi/taste_gate_2026-04.md
files_read_first:
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
  - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
  - tests/phase09/test_taste_gate_form_schema.py
  - tests/phase09/conftest.py
  - wiki/kpi/MOC.md
autonomous: true
requirements: [KPI-05]
tasks_addressed: [9-03-01, 9-03-02]
success_criteria: [SC#3]
estimated_commits: 2
parallel_boundary: parallel with 09-01 and 09-02 (disjoint files — docs/ARCHITECTURE.md vs wiki/kpi/kpi_log.md vs wiki/kpi/taste_gate_*.md)

must_haves:
  truths:
    - "wiki/kpi/taste_gate_protocol.md exists with monthly cadence declaration (매월 1일 KST 09:00)"
    - "taste_gate_protocol.md declares top-3/bottom-3 selection method via 3sec_retention"
    - "wiki/kpi/taste_gate_2026-04.md exists with frontmatter status=dry-run"
    - "taste_gate_2026-04.md has DRY-RUN banner warning at top (Pitfall 3)"
    - "taste_gate_2026-04.md contains 6 synthetic rows with video_ids abc123/def456/ghi789/jkl012/mno345/pqr678"
    - "taste_gate_2026-04.md score column labeled '품질 (1-5)'"
    - "taste_gate_2026-04.md has '한줄 코멘트' column"
    - "pytest tests/phase09/test_taste_gate_form_schema.py exits 0"
  artifacts:
    - path: "wiki/kpi/taste_gate_protocol.md"
      provides: "Monthly Taste Gate protocol — D-08 semi-automated selection + D-09 Markdown form + D-10 dry-run strategy + D-11 매월 1일 KST 09:00 cadence"
      min_lines: 80
    - path: "wiki/kpi/taste_gate_2026-04.md"
      provides: "First dry-run evaluation file (D-10 synthetic sample 6, 탐정/조수 페르소나, status=dry-run)"
      min_lines: 40
      contains: "status: dry-run"
  key_links:
    - from: "wiki/kpi/taste_gate_protocol.md"
      to: "scripts/taste_gate/record_feedback.py"
      via: "Protocol references CLI invocation `python scripts/taste_gate/record_feedback.py --month YYYY-MM` (Plan 09-04 target)"
      pattern: "record_feedback\\.py|scripts/taste_gate"
    - from: "wiki/kpi/taste_gate_2026-04.md"
      to: "tests/phase09/conftest.py synthetic_taste_gate_april fixture"
      via: "Same 6 synthetic rows + persona titles must match Wave 0 fixture body byte-compatible for parser tests"
      pattern: "탐정이 조수에게 묻다|100억 갑부"
    - from: "wiki/kpi/taste_gate_protocol.md"
      to: "wiki/kpi/kpi_log.md (Plan 09-02)"
      via: "Cross-reference link — top-3 goes to kpi_log, bottom-3 (score <= 3) goes to FAILURES.md via record_feedback.py"
      pattern: "kpi_log|\\[\\[kpi_log\\]\\]"
---

<objective>
Write two wiki files establishing the Taste Gate protocol + first dry-run.

1. `wiki/kpi/taste_gate_protocol.md` (~80-120 lines) — Permanent protocol doc. Declares D-08 semi-automated top-3/bottom-3 selection by 3-sec retention, D-09 Markdown single-file form (Google Form rejected), D-10 synthetic dry-run strategy, D-11 매월 1일 KST 09:00 auto-trigger cadence (Phase 10 cron target, Phase 9 documents only). Explains 대표님 fills only 3 columns (품질 1-5 / 한줄 코멘트 / 태그).

2. `wiki/kpi/taste_gate_2026-04.md` (~40-60 lines) — First dry-run evaluation file. Frontmatter `status: dry-run`. DRY-RUN banner warning (Pitfall 3: prevents future Phase 10 readers from mistaking for real data). 6 synthetic rows (3 top + 3 bottom) with 탐정/조수 페르소나 titles and obviously-fake 6-char video_ids (abc123/def456/ghi789/jkl012/mno345/pqr678). Scores pre-filled [5, 4, 4, 3, 2, 1] so Plan 09-04 parser tests find 3 escalations per D-13.

Purpose: Target SC#3 — "Taste Gate 프로토콜이 문서화 + 첫 회 dry-run 완료" — and KPI-05 (월 1회 평가 회로). The dry-run content must byte-match `synthetic_taste_gate_april` fixture in tests/phase09/conftest.py so Plan 09-04 parser tests have consistent input.

Output: 2 wiki files + test_taste_gate_form_schema.py green.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md
@.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md
@tests/phase09/test_taste_gate_form_schema.py
@tests/phase09/conftest.py
@wiki/kpi/MOC.md

<interfaces>
## taste_gate_protocol.md required sections (D-08 ~ D-11)

```markdown
---
category: kpi
status: ready
tags: [taste-gate, monthly-review, protocol]
updated: 2026-04-20
---

# Taste Gate Protocol — 월 1회 대표님 평가 회로

> B-P4 (자동화 taste filter 0) 구조적 방어. 인간 감독 게이트의 마지막 설치.

## 1. Purpose (KPI-05)

매월 1회 대표님이 지난 30일 영상 중 상위 3 / 하위 3을 직접 평가하여 자동 파이프라인만으로는 포착 불가능한 **채널 정체성 드리프트 + 품질 드리프트**를 감지한다.

## 2. Cadence (D-11)

- **Trigger:** 매월 1일 KST 09:00
- **Automation status:** Phase 9 문서화만. Phase 10에서 cron으로 자동화 예정.
- **Reviewer:** 대표님 (sole reviewer)
- **Max review time:** 30분 (6 영상 × 5분)

## 3. Selection Method (D-08, semi-automated)

1. 지난 30일 업로드 영상 전수 → YouTube Analytics v2 `audienceWatchRatio[3]` 조회
2. 3sec_retention 기준 정렬 → 상위 3 + 하위 3 자동 선별
3. Phase 10 `scripts/analytics/fetch_kpi.py`가 결과를 `wiki/kpi/taste_gate_YYYY-MM.md` 표로 pre-fill
4. 대표님은 평가 컬럼 3개만 작성 (자동 선별 결과는 수정 금지)

## 4. Evaluation Form (D-09, Markdown single file)

- **Path:** `wiki/kpi/taste_gate_YYYY-MM.md`
- **Format:** Markdown 단일 파일 (Google Form 거부 — external dep + privacy + git-untracked)
- **Editor:** VSCode 또는 Obsidian
- **3 평가 컬럼:**
  - **품질 (1-5):** 전반적 영상 완성도 (5 = 대표님 기준 이상적)
  - **한줄 코멘트:** 느낀 점 (한국어 자유 서술)
  - **태그 (선택):** 재사용 / 재생산 / 폐기 / 후속편 후보

## 5. Feedback Flow (D-12, D-13)

작성 완료 후 CLI 실행:

```bash
python scripts/taste_gate/record_feedback.py --month 2026-04
```

- **D-13 필터:** score <= 3 항목만 `.claude/failures/FAILURES.md` 하단에 `### [taste_gate] YYYY-MM 리뷰 결과` 섹션으로 append
- **상위 3 (score 4-5):** `wiki/kpi/kpi_log.md` Part B에만 "유지" 태그로 기록, FAILURES.md 승격 없음
- **하위 3 중 score > 3:** 해당 월 kpi_log.md에만 기록 (노이즈 필터)
- **하위 3 중 score <= 3:** FAILURES.md 승격 → 다음 월 Producer 입력에 반영 (Phase 10)

## 6. Dry-run Strategy (D-10, D-14)

- **Phase 9 first dry-run:** `wiki/kpi/taste_gate_2026-04.md` (synthetic sample 6 + status=dry-run)
- **Purpose:** 대표님이 "평가 포맷이 편한가" UX 검증만. 실 영상 데이터 없음.
- **Synthetic video IDs:** 6-char obviously-fake (abc123 ...) — Pitfall 3 방어
- **Persona:** shorts_naberal 탐정/조수 승계 — 현실적 제목 사용, "테스트용 쇼츠" 같은 placeholder 절대 금지

## 7. Related

- [[kpi_log]] — KPI targets + monthly tracking companion
- [[taste_gate_2026-04]] — first dry-run (Phase 9 Plan 09-03 target)
- [[MOC]] — KPI 카테고리 노드 맵
- `.claude/failures/FAILURES.md` — append-only sink (Phase 6 D-11 Hook-enforced)
- `scripts/taste_gate/record_feedback.py` — CLI appender (Phase 9 Plan 09-04 target)

---

*Created: 2026-04-20 (Phase 9 Plan 09-03)*
*First auto-trigger: Phase 10 Month 1 cron (매월 1일 KST 09:00)*
```

## taste_gate_2026-04.md required content (D-10 synthetic dry-run)

```markdown
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

## Related

- [[taste_gate_protocol]] — 평가 회로 문서
- [[kpi_log]] — 월별 KPI 추적 companion

---

*Created: 2026-04-20 (Phase 9 Plan 09-03)*
*Status: dry-run (Phase 10 Month 1 첫 실 데이터 수집 전 포맷 검증용)*
```

**CRITICAL:** Video titles and comments in taste_gate_2026-04.md MUST byte-match tests/phase09/conftest.py `synthetic_taste_gate_april` fixture so Plan 09-04 E2E tests use consistent data source.
</interfaces>
</context>

<tasks>

<task id="9-03-01">
  <action>
Create `wiki/kpi/taste_gate_protocol.md` with EXACTLY the content shown in the first `<interfaces>` block (7 sections: Purpose / Cadence / Selection Method / Evaluation Form / Feedback Flow / Dry-run Strategy / Related).

Literal requirements:

1. **Frontmatter:** `category: kpi`, `status: ready`, `tags: [taste-gate, monthly-review, protocol]`, `updated: 2026-04-20`
2. **H1 title:** `# Taste Gate Protocol — 월 1회 대표님 평가 회로`
3. **Section 2 Cadence MUST contain:**
   - `매월 1일 KST 09:00` (D-11 literal trigger time)
   - `Phase 9 문서화만. Phase 10에서 cron으로 자동화` (phase boundary clarity)
   - `30분` (max review time)
4. **Section 3 Selection Method MUST contain:**
   - `지난 30일` literal window
   - `audienceWatchRatio[3]` metric
   - `상위 3` AND `하위 3` (both top-3 and bottom-3)
   - `3sec_retention` column name
   - `scripts/analytics/fetch_kpi.py` (Phase 10 future reference)
5. **Section 4 Evaluation Form MUST contain:**
   - `Markdown 단일 파일` (D-09 anchor)
   - `Google Form 거부` (D-09 rejection rationale)
   - `VSCode` and `Obsidian` (editor options)
   - `품질 (1-5)`, `한줄 코멘트`, `태그 (선택)` three column names
6. **Section 5 Feedback Flow MUST contain:**
   - `python scripts/taste_gate/record_feedback.py --month 2026-04` CLI invocation
   - `score <= 3` (D-13 threshold)
   - `FAILURES.md` reference
   - `### [taste_gate] YYYY-MM 리뷰 결과` section heading format (D-12 tag)
7. **Section 6 Dry-run Strategy MUST contain:**
   - `wiki/kpi/taste_gate_2026-04.md` (first dry-run target)
   - `status=dry-run` frontmatter mention
   - `6-char obviously-fake` (Pitfall 3 defense)
   - `shorts_naberal 탐정/조수 승계` (persona anchor)
   - Forbid "테스트용 쇼츠" explicitly
8. **Section 7 Related:**
   - `[[kpi_log]]`
   - `[[taste_gate_2026-04]]`
   - `[[MOC]]`
   - `.claude/failures/FAILURES.md`
   - `scripts/taste_gate/record_feedback.py`

MUST NOT contain: `skip_gates`, `TODO(next-session)`, try/except-pass. Korean prose allowed and encouraged.
  </action>
  <read_first>
    - tests/phase09/test_taste_gate_form_schema.py (the 2 tests this file must satisfy: test_protocol_doc checks monthly cadence / KST 09:00 / 상위 3 / 하위 3 / 3sec_retention)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md §D-08 ~ §D-14 (all 4 Taste Gate + 3 FAILURES decisions)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Pattern 5 (form design rationale) + §Don't Hand-Roll (FAILURES append-only Hook reuse)
  </read_first>
  <acceptance_criteria>
    - `test -f wiki/kpi/taste_gate_protocol.md` exits 0
    - `wc -l < wiki/kpi/taste_gate_protocol.md` outputs a number >= 80
    - `grep -q '^category: kpi$' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q '^status: ready$' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q '매월 1일' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'KST 09:00' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q '상위 3' wiki/kpi/taste_gate_protocol.md && grep -q '하위 3' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -qE '3sec_retention|3초 retention' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'Markdown 단일 파일' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'Google Form' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q '품질 (1-5)' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q '한줄 코멘트' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'scripts/taste_gate/record_feedback.py' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'score <= 3' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'FAILURES.md' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'taste_gate' wiki/kpi/taste_gate_protocol.md` exits 0
    - `grep -q 'skip_gates' wiki/kpi/taste_gate_protocol.md` must return 1 (not found — Hook 3종 차단)
    - `grep -q 'TODO(next-session)' wiki/kpi/taste_gate_protocol.md` must return 1
  </acceptance_criteria>
  <automated>python -c "import pathlib; p=pathlib.Path('wiki/kpi/taste_gate_protocol.md'); t=p.read_text(encoding='utf-8'); checks=['매월 1일','KST 09:00','상위 3','하위 3','품질 (1-5)','한줄 코멘트','Markdown 단일 파일','scripts/taste_gate/record_feedback.py','score <= 3','FAILURES.md']; [s for s in checks if s not in t] and (_ for _ in ()).throw(AssertionError([s for s in checks if s not in t])) or print('OK')"</automated>
  <task_type>impl</task_type>
</task>

<task id="9-03-02">
  <action>
Create `wiki/kpi/taste_gate_2026-04.md` with EXACTLY the content shown in the second `<interfaces>` block.

Literal requirements:

1. **Frontmatter MUST include all 8 fields:**
   - `category: kpi`
   - `status: dry-run`
   - `tags: [taste-gate, monthly-review, dry-run]`
   - `month: 2026-04`
   - `reviewer: 대표님`
   - `selected_at: 2026-04-01T09:00:00+09:00`
   - `selection_method: semi-auto (top3 + bottom3 by 3sec_retention over last 30 days)`
   - `updated: 2026-04-20`
2. **DRY-RUN banner** — first body line after H1 must be:
   `> ⚠️ **DRY-RUN (D-10 synthetic sample)** — 실 데이터는 Phase 10 Month 1에서 수집. 이 파일은 포맷 검증용. 실제 2026-04 업로드 영상과 무관.`
   (Pitfall 3: prevents future mistaking for real data)
3. **6 synthetic rows — EXACT video_ids + titles + scores (MUST byte-match tests/phase09/conftest.py synthetic_taste_gate_april fixture):**

   상위 3 table:
   - `| 1 | abc123 | "탐정이 조수에게 묻다: 23살 범인의 진짜 동기?" | 68% | 42% | 27초 | 5 | 완성도 우수 | 재생산 |`
   - `| 2 | def456 | "100억 갑부가 딱 한 번 울었던 순간" | 64% | 41% | 26초 | 4 | 훌륭함 | 유지 |`
   - `| 3 | ghi789 | "3번째 편지의 의미를 아시나요?" | 61% | 40% | 25초 | 4 | 좋음 | 유지 |`

   하위 3 table:
   - `| 4 | jkl012 | "조수가 놓친 단서" | 48% | 28% | 19초 | 3 | hook 약함 | 재제작 |`
   - `| 5 | mno345 | "5번 방문한 이유" | 45% | 25% | 17초 | 2 | 지루함 | 폐기 |`
   - `| 6 | pqr678 | "범인의 마지막 말" | 42% | 24% | 16초 | 1 | 결말 처참 | 폐기 |`

4. **Score distribution [5, 4, 4, 3, 2, 1]** — so D-13 filter produces exactly 3 escalations (scores 3, 2, 1). This is critical: Plan 09-04 test_score_threshold_filter.py and Plan 09-05 test_e2e_synthetic_dry_run.py expect exactly 3 FAILURES entries from this file.
5. **Score column header:** `품질 (1-5)` literal (with space and parentheses)
6. **Comment column header:** `한줄 코멘트`
7. **Tag column header:** `태그`
8. **CLI invocation block** — must include:
   ```
   python scripts/taste_gate/record_feedback.py --month 2026-04
   ```
9. **Related section:**
   - `[[taste_gate_protocol]]`
   - `[[kpi_log]]`
10. **Status line at bottom:** `Status: dry-run (Phase 10 Month 1 첫 실 데이터 수집 전 포맷 검증용)`

MUST NOT contain: `테스트용 쇼츠`, `skip_gates`, `TODO(next-session)`.

After both files exist, run the full Phase 9 sweep to confirm Wave 1 parallelism:

```
python -m pytest tests/phase09/test_taste_gate_form_schema.py -q --no-cov
python -m pytest tests/phase09/ --collect-only -q --no-cov
```

Both MUST exit 0.

Run Phase 4-8 collection sweep:

```
python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov
```

MUST exit 0.
  </action>
  <read_first>
    - tests/phase09/test_taste_gate_form_schema.py (the 5+ tests this file must satisfy: test_dry_run_exists / test_six_evaluation_rows / test_score_column_1_to_5 / test_comment_column / test_persona_titles_not_placeholder)
    - tests/phase09/conftest.py §synthetic_taste_gate_april (Plan 09-00 fixture body — must byte-match)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-CONTEXT.md §D-10 (synthetic sample strategy) + §D-14 (sample validation)
    - .planning/phases/09-documentation-kpi-dashboard-taste-gate/09-RESEARCH.md §Pattern 5 (taste_gate_YYYY-MM.md format) + §Pitfall 3 (DRY-RUN banner + 6-char fake IDs)
  </read_first>
  <acceptance_criteria>
    - `test -f wiki/kpi/taste_gate_2026-04.md` exits 0
    - `wc -l < wiki/kpi/taste_gate_2026-04.md` outputs a number >= 40
    - `grep -q '^status: dry-run$' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q '^month: 2026-04$' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q 'DRY-RUN' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q '포맷 검증용' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -c '^| [0-9]' wiki/kpi/taste_gate_2026-04.md` outputs `>= 6` (6 data rows)
    - All 6 video_ids present:
      - `grep -q 'abc123' wiki/kpi/taste_gate_2026-04.md`
      - `grep -q 'def456' wiki/kpi/taste_gate_2026-04.md`
      - `grep -q 'ghi789' wiki/kpi/taste_gate_2026-04.md`
      - `grep -q 'jkl012' wiki/kpi/taste_gate_2026-04.md`
      - `grep -q 'mno345' wiki/kpi/taste_gate_2026-04.md`
      - `grep -q 'pqr678' wiki/kpi/taste_gate_2026-04.md`
    - `grep -q '탐정이 조수에게 묻다' wiki/kpi/taste_gate_2026-04.md` exits 0 (persona title #1)
    - `grep -q '100억 갑부' wiki/kpi/taste_gate_2026-04.md` exits 0 (persona title #2)
    - `grep -q '품질 (1-5)' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q '한줄 코멘트' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q '태그' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q 'scripts/taste_gate/record_feedback.py --month 2026-04' wiki/kpi/taste_gate_2026-04.md` exits 0
    - `grep -q '테스트용 쇼츠' wiki/kpi/taste_gate_2026-04.md` must return 1 (forbidden placeholder)
    - `grep -q 'skip_gates' wiki/kpi/taste_gate_2026-04.md` must return 1
    - `python -m pytest tests/phase09/test_taste_gate_form_schema.py -x --no-cov` exits 0 (5+ tests PASS)
    - `python -m pytest tests/phase09/ --collect-only -q --no-cov` exits 0
    - `python -m pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --co -q --no-cov` exits 0
  </acceptance_criteria>
  <automated>python -m pytest tests/phase09/test_taste_gate_form_schema.py -x --no-cov</automated>
  <task_type>impl</task_type>
</task>

</tasks>

<verification>
1. `wiki/kpi/taste_gate_protocol.md` ships with 7 sections + monthly cadence + 3 evaluation columns + CLI invocation.
2. `wiki/kpi/taste_gate_2026-04.md` ships with frontmatter status=dry-run + DRY-RUN banner + 6 synthetic rows with exact video_ids + scores [5,4,4,3,2,1].
3. Dry-run file byte-matches tests/phase09/conftest.py synthetic_taste_gate_april fixture for downstream parser compatibility.
4. All tests in test_taste_gate_form_schema.py PASS.
5. Phase 4-8 986+ collection preserved.
6. No 테스트용 쇼츠 placeholder, no skip_gates, no TODO(next-session).
</verification>

<success_criteria>
Plan 09-03 is COMPLETE when:
- `wiki/kpi/taste_gate_protocol.md` + `wiki/kpi/taste_gate_2026-04.md` both shipped.
- taste_gate_protocol.md declares D-08 + D-09 + D-10 + D-11 protocol fully (semi-auto selection, Markdown single file, synthetic dry-run, 매월 1일 KST 09:00).
- taste_gate_2026-04.md contains 6 synthetic rows with exact video_ids + scores producing 3 D-13 escalations (scores <= 3) for Plan 09-04 test compatibility.
- test_taste_gate_form_schema.py all tests PASS.
- Phase 4-8 986+ collection preserved (wiki-only change).
- SC#3 (Taste Gate 프로토콜 문서화 + dry-run 완료) and KPI-05 (월 1회 평가 회로 설치) textually satisfied.
- Dry-run content byte-compatible with Wave 0 fixture — downstream Plan 09-04/05 E2E tests will succeed.
</success_criteria>

<output>
Create `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-03-SUMMARY.md` documenting:
- 2 files created (taste_gate_protocol.md + taste_gate_2026-04.md with line counts)
- Score distribution [5,4,4,3,2,1] documented → 3 escalations expected in Plan 09-04 tests
- Fixture byte-compatibility confirmed (Wave 0 conftest matches dry-run)
- test_taste_gate_form_schema.py result
- Phase 4-8 regression collection result
- Commit hash
</output>
