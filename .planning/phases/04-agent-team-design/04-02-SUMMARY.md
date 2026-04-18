---
phase: 04-agent-team-design
plan: 02
subsystem: inspector-structural
tags: [inspector, structural, logicqa, rubric-schema, shorts-format, content-05, maxTurns-1, agent-04]

requires:
  - phase: 04-agent-team-design
    plan: 01
    provides: agent-template.md + rubric-schema.json + scripts/validate/* + tests/phase04/conftest.py
provides:
  - ins-blueprint-compliance/AGENT.md — Blueprint JSON 5 필수 필드 (tone/high-level structure/target_emotion/channel_bible_ref/scene_count 5-10) regex 검증
  - ins-timing-consistency/AGENT.md — scene t_start/t_end monotonic + 겹침 없음 + sum ≤59.5s + 개수 4-8 + 첫 scene t_start=0.0 (CONTENT-05 연동)
  - ins-schema-integrity/AGENT.md — upstream JSON schema 준수 + 9:16 / 1080×1920 / ≤59s Shorts format enforcement (CONTENT-05 단일 관문)
  - tests/phase04/test_inspector_structural.py — 6 pytest 컴플라이언스 (name/frontmatter/LogicQA/MUST REMEMBER/Inputs RUB-06/CONTENT-05 body)
affects:
  - Wave 1b (Inspector Content 3) — 동일 category 폴더 병렬 패턴 사용
  - Wave 1c (Inspector Style 3), Wave 1d (Compliance 4), Wave 1e (Technical 2), Wave 1f (Media 2)
  - Wave 4 shorts-supervisor — 본 3 inspector rubric을 17 inspector 집합의 structural 하위 카테고리로 수집

tech-stack:
  added:
    - (없음 — Wave 0 scripts.validate.* + pytest 인프라 그대로 사용)
  patterns:
    - Inspector AGENT.md 규격 확립: 8 섹션 (H1 header, Purpose, Inputs with RUB-06 note, Outputs rubric JSON, Prompt with LogicQA + VQQA, References, Contract with callers, MUST REMEMBER)
    - LogicQA 블록 구조 확정: `<main_q>...</main_q>` + `<sub_qs>q1: ... q2: ... q3: ... q4: ... q5: ...</sub_qs>` + "5 sub-q 중 3+ N → main_q=N → FAIL" 다수결 규칙
    - Shorts format enforcement 단일 관문화: aspect_ratio=9:16 / resolution=1080×1920 (or 1080x1920 ASCII allowed) / duration_sec≤59.5를 ins-schema-integrity에서 결정론적으로 검사
    - MUST REMEMBER 자가 준수 패턴: 파일 마지막 섹션 고정, 각 inspector 7~9개 불변조건 (RUB-02, RUB-06, RUB-01, RUB-05, RUB-04, AGENT-05, VQQA 한국어, AGENT-09 위치)

key-files:
  created:
    - .claude/agents/inspectors/structural/ins-blueprint-compliance/AGENT.md (133 lines)
    - .claude/agents/inspectors/structural/ins-timing-consistency/AGENT.md (131 lines)
    - .claude/agents/inspectors/structural/ins-schema-integrity/AGENT.md (144 lines)
    - tests/phase04/test_inspector_structural.py (136 lines, 6 tests)
  modified: []

decisions:
  - Inspector frontmatter에 `role: inspector`, `category: structural`, `maxTurns: 1` 세 키를 필수로 확립 (test_frontmatter_role_category_maxturns가 자동 enforce)
  - Inputs 테이블은 `--producer-output`과 `--rubric-schema` 두 Flag만 허용. `producer_prompt`/`producer_system_context`는 table row로 **절대** 등장 금지 (RUB-06 GAN 분리). MUST REMEMBER 본문에서는 'producer_prompt' 문자열이 RUB-06 negation 형태로 반드시 등장 (Test 4가 enforce)
  - CONTENT-05 Shorts format은 ins-schema-integrity에 집약 (ins-timing-consistency는 59.5s sum 검사만 담당). aspect_ratio와 resolution은 ins-schema-integrity 단일 관문에서 enforcement
  - resolution 문자열은 `1080×1920` (U+00D7 MULTIPLICATION SIGN) 및 `1080x1920` (ASCII x) 둘 다 허용 — 하위 Producer가 키보드 입력 편의로 ASCII x를 쓸 수 있도록 완화. 그러나 `1920×1080`(가로 해상도)이나 `16:9`는 FAIL
  - LogicQA 다수결 판정식: 5 sub-q 중 3+ "N"일 때 main_q=N → verdict=FAIL. 단일 질문 판정 금지. 각 inspector가 q1~q5 5개를 빠짐없이 평가하도록 본 규칙을 prompt body에 명시
  - 본 plan 실행은 Wave 1a 병렬 실행 컨텍스트 (04-03 ~ 04-07과 동시 실행). 파일 경로 충돌 없음 (category 폴더 격리) + `tests/phase04/` 내 파일명 충돌 없음 (`test_inspector_structural.py` 단독 점유)

metrics:
  duration: ~5 minutes
  completed_date: 2026-04-19
  tasks_completed: 2
  tasks_total: 2
  files_created: 4
  files_modified: 0
  tests_passed: 6
  tests_total: 6
  deviations: 0
---

# Phase 4 Plan 02: Structural Inspector 3인 Summary

**One-liner:** Wave 1a의 Structural 카테고리 3인(ins-blueprint-compliance, ins-timing-consistency, ins-schema-integrity)을 maxTurns=1 regex/schema 검사관 형태로 생성하고, 6개 pytest로 자가 준수(AGENT-04/07/08/09, RUB-01/02/04/05/06, CONTENT-05)를 자동 enforce.

## Scope Delivered

### Task 1 — 3 Structural Inspector AGENT.md 생성 (커밋 `a0f7ab2`)

`.claude/agents/inspectors/structural/{ins-*}/AGENT.md` 경로에 3개 파일을 생성했다. 모두 Wave 0에서 확립한 `agent-template.md`의 Inspector variant를 상속하며, 각 파일은 다음을 공통 준수한다:

- **Frontmatter**: `role: inspector`, `category: structural`, `maxTurns: 1`, `description ≤ 1024자` (트리거 키워드 3+ 포함).
- **8 섹션 구조**: H1 → 본문 한 문단 role summary → Purpose (REQ 명시) → Inputs (RUB-06 negation note) → Outputs (rubric-schema.json 구조) → Prompt (LogicQA 5 sub-qs + VQQA 형식 예시) → References (schemas/template/research/validators) → Contract with callers → MUST REMEMBER (파일 END).
- **파일 길이**: 각 131~144 lines (≤500 제한의 30% 이하, 타이트한 스펙). `validate_all_agents.py --path .claude/agents/inspectors/structural` → `OK: 3 agent(s) validated`.

#### ins-blueprint-compliance (133 lines)

director 산출 Blueprint JSON 5 필수 필드 검증:
1. `tone` 비어있지 않은 문자열
2. `high-level structure` ≥ 3 단계
3. `target_emotion ∈ {neutral, tense, sad, happy, urgent, mysterious, empathetic}`
4. `channel_bible_ref` 가 `.preserved/harvested/theme_bible_raw/` 로 시작 (CONTENT-03 연동)
5. `scene_count` 정수 5~10 범위

#### ins-timing-consistency (131 lines)

scripter/scene-planner 산출 JSON의 `scenes[]` 배열 timing 5종 계약:
1. 각 scene에서 `t_start < t_end`
2. 인접 scene 간 `scene[i].t_end ≤ scene[i+1].t_start` (겹침 금지)
3. `sum(t_end - t_start) ≤ 59.5` (CONTENT-05 59초 제약을 timing 관점에서 검증)
4. scene 개수 4~8 범위
5. `scenes[0].t_start == 0.0` (hook 시작점 강제)

#### ins-schema-integrity (144 lines)

Producer 전 파이프라인 output JSON의 schema + Shorts format 5종 계약 (CONTENT-05 단일 관문):
1. 필수 JSON 필드 누락 없음 (scenes/shots/script/speaker/duration_sec/aspect_ratio/resolution 등)
2. `duration_sec ≤ 59.5`
3. `aspect_ratio == "9:16"` AND `resolution == "1080×1920"` (또는 ASCII `1080x1920`)
4. `speaker ∈ {detective, assistant}`
5. `citations` 배열 존재 + fact scene마다 `nlm_source` 포함

본 inspector는 9:16, 1080×1920, 59 세 문자열을 본문에 명시적으로 포함 — 테스트 6(`test_ins_schema_integrity_content_05`)가 자동 enforce.

### Task 2 — tests/phase04/test_inspector_structural.py (커밋 `6c55d9c`)

TDD-style 6 테스트. 모든 3 inspector AGENT.md에 대해 다음을 병렬 검증:

| # | Test | Enforces |
|---|------|----------|
| 1 | `test_exactly_3_structural_inspectors` | AGENT-04 — 정확히 3개 (name set 일치) |
| 2 | `test_frontmatter_role_category_maxturns` | RUB-05 — `role=inspector`/`category=structural`/`maxTurns=1` |
| 3 | `test_logicqa_block_present` | RUB-01 — `<main_q>` + `<sub_qs>` + q1~q5 전부 |
| 4 | `test_must_remember_contains_rub_violations` | RUB-02 ("창작 금지") + RUB-06 ("producer_prompt") |
| 5 | `test_inputs_no_producer_prompt_or_system_context` | RUB-06 GAN 분리 — Inputs table에 producer_prompt/producer_system_context Flag 금지 |
| 6 | `test_ins_schema_integrity_content_05` | CONTENT-05 — 9:16 + (1080×1920 or 1080x1920) + 59 문자열 존재 |

**결과**: `pytest tests/phase04/test_inspector_structural.py -v` → **6 passed in 0.07s** (0 skip, 0 xfail, 0 error).

## Verification Results

```
$ py -3.11 -m scripts.validate.validate_all_agents --path .claude/agents/inspectors/structural
OK: 3 agent(s) validated

$ py -3.11 -m pytest tests/phase04/test_inspector_structural.py --tb=short
============================== 6 passed in 0.07s ==============================
```

**AGENT-07/08/09 검증 합계**:
- AGENT-07 (≤500 lines): 모두 통과 (133, 131, 144 lines)
- AGENT-08 (description ≤1024자 + 트리거 ≥3): 모두 통과 (쉼표 분리 트리거 키워드 각 10+)
- AGENT-09 (MUST REMEMBER ratio_from_end ≤0.4): 모두 통과 (각 파일 END 섹션 고정)

## Decisions Made

1. **Inspector frontmatter 3-키 필수화** — `role/category/maxTurns` 세 키를 Structural 3 파일 공통 규격으로 고정. Test 2가 자동 enforce. 이후 Wave 1b~1f 및 Wave 4 Supervisor가 동일 규격 상속.
2. **RUB-06 이중 방어** — (a) Inputs 테이블에서 producer_prompt/producer_system_context Flag 금지 (Test 5), (b) MUST REMEMBER 본문에 "producer_prompt 읽기 금지" 명시 (Test 4). Supervisor fan-out 시 실수 누수 발생해도 inspector 자체가 무시하도록 prompt body에 처리 규칙 포함.
3. **CONTENT-05 단일 관문 = ins-schema-integrity** — 9:16 / 1080×1920 / ≤59s 중 aspect_ratio와 resolution은 ins-schema-integrity 단독 enforcement. ins-timing-consistency는 59.5s `sum` 검사만 책임 (CONTENT-05 ∩ timing 부분집합). 중복 책임 제거.
4. **resolution 문자열 두 형태 허용** — `1080×1920` (U+00D7) 및 `1080x1920` (ASCII x) 둘 다 PASS. 하위 Producer가 키보드 입력 편의로 ASCII를 쓸 가능성 고려. 단 `1920×1080` (가로) / `16:9` / `9×16` 는 FAIL.
5. **LogicQA 다수결 규칙** — "5 sub-q 중 3+ N → main_q=N → verdict=FAIL" 판정식을 각 inspector prompt body에 명시. 단일 질문 판정 금지. q1~q5를 전부 평가해야 `logicqa_sub_verdicts` 5 items 제출 가능 (rubric-schema.json의 `logicqa_sub_verdicts.minItems==5`와 정합).

## Deviations from Plan

**None** — plan 04-02의 Task 1 + Task 2 본문, verify 명령, done criteria 모두 그대로 실행됨. Rule 1~4 발동 없음.

- Auto-fix bugs (Rule 1): 없음
- Auto-add missing critical functionality (Rule 2): 없음
- Auto-fix blocking issues (Rule 3): 없음
- Architectural decisions (Rule 4): 없음

**Scope boundary 준수** — 본 plan은 Structural 3 inspector + 대응 테스트에 한정. Wave 1b~1f의 다른 14 inspector는 건드리지 않음 (04-03 ~ 04-07이 병렬 실행 중).

## Known Stubs

**None** — 본 plan은 AGENT.md 스펙 파일(프롬프트 텍스트)과 pytest 검증 파일만 산출. 실제 rubric JSON을 생성하는 Claude Code sub-agent는 Phase 4 후반 Wave 5에서 Claude Task tool로 래핑됨. 현 단계는 "프롬프트 스펙 확정"이 목표이며, stub/placeholder/TODO 없음.

## Next

Wave 1a 병렬 실행 중 완료: 04-02 (Structural, 본 plan). 병렬 중:
- 04-03 Content 3인 (ins-korean-naturalness, ins-cbt-rythm, ins-theme-bible)
- 04-04 Style 3인
- 04-05 Compliance 4인
- 04-06 Technical 2인
- 04-07 Media 2인

Wave 1 완료 후 Wave 2 (Producer Core 6), Wave 3 (split3 + support 5), Wave 4 (Supervisor 1), Wave 5 (harness-audit final) 진행.

## Commits

| Task | Hash | Type | Message |
|------|------|------|---------|
| 1 | `a0f7ab2` | feat | add 3 Structural Inspector AGENT.md files |
| 2 | `6c55d9c` | test | add Structural Inspector compliance pytest (6 tests) |

## Self-Check: PASSED

All claimed artifacts verified on disk and in git log.
