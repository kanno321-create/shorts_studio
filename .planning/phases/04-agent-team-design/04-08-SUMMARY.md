---
phase: 04-agent-team-design
plan: 08
subsystem: agents
tags: [producer, core, split3, filmagent, notebooklm, scripter, director, scene-planner, shot-planner, trend-collector, niche-classifier, researcher, script-polisher, metadata-seo, gan-separation, vqqa, channel-bible]

# Dependency graph
requires:
  - phase: 04-agent-team-design (Plan 04-01)
    provides: agent-template.md + rubric-schema.json + vqqa_corpus.md + korean_speech_samples.json + validate_all_agents.py
  - phase: 04-agent-team-design (Plans 02-07)
    provides: 8 Inspector names (structural/content/compliance/technical/style/media) — Producer prompts reference Inspector FAIL conditions via VQQA feedback loop (RUB-03)
  - phase: 03-harvest (Plan 03-03)
    provides: .preserved/harvested/theme_bible_raw/ — 7 channel bibles (incidents/wildlife/documentary/humor/politics/trend + README)
provides:
  - "9 Producer AGENT.md files: 6 core (trend-collector, niche-classifier, researcher, scripter, script-polisher, metadata-seo) + 3 split3 (director, scene-planner, shot-planner)"
  - "Producer pipeline contract: trend-collector → niche-classifier → researcher + director → scene-planner → shot-planner + scripter → script-polisher → metadata-seo"
  - "Producer 3단 분리 계약 (FilmAgent T6): Blueprint (director L1) → Scenes (scene-planner L2) → Shots (shot-planner L3)"
  - "RUB-03 VQQA feedback loop: all 9 producers accept --prior-vqqa for scene-level retry"
  - "RUB-06 GAN 분리 mirror: all 9 producers have 'inspector_prompt 읽기 금지' in MUST REMEMBER"
  - "3 pytest files: test_producer_core.py (7 tests) + test_producer_3split.py (7 tests) + test_scripter_rules.py (6 tests) = 20/20 PASS"
affects: [05-pipeline-orchestration, 06-notebooklm-wiring, 07-render-pipeline, 08-publish-pipeline, 50-script-quality-research]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Producer variant of agent-template.md (role=producer, category=core|split3, maxTurns=3)"
    - "VQQA feedback loop (RUB-03): prior_vqqa input → scene-level retry (not full rewrite)"
    - "Channel bible inline injection (CONTENT-03): niche-classifier matched_fields 10 fields inlined into 5 downstream producers"
    - "FilmAgent hierarchy (NotebookLM T6): director → scene-planner → shot-planner with prompt isolation (각 단계 하위 prompt 읽기 금지)"
    - "GAN separation mirror (RUB-06): producer MUST REMEMBER 'inspector_prompt 읽기 금지' parallels inspector MUST REMEMBER 'producer_prompt 읽기 금지'"
    - "1 Move Rule (NotebookLM T2): scene total_moves = camera_action 1 + subject_action 1 = 2"
    - "I2V only, T2V 금지 (NotebookLM T1): shot.anchor_frame_ref + camera_move + i2v_prompt; T2V self-check FAIL"

key-files:
  created:
    - ".claude/agents/producers/trend-collector/AGENT.md (126 lines)"
    - ".claude/agents/producers/niche-classifier/AGENT.md (135 lines)"
    - ".claude/agents/producers/researcher/AGENT.md (160 lines)"
    - ".claude/agents/producers/scripter/AGENT.md (210 lines)"
    - ".claude/agents/producers/script-polisher/AGENT.md (148 lines)"
    - ".claude/agents/producers/metadata-seo/AGENT.md (159 lines)"
    - ".claude/agents/producers/director/AGENT.md (136 lines)"
    - ".claude/agents/producers/scene-planner/AGENT.md (184 lines)"
    - ".claude/agents/producers/shot-planner/AGENT.md (194 lines)"
    - "tests/phase04/test_producer_core.py (145 lines, 7 tests)"
    - "tests/phase04/test_producer_3split.py (133 lines, 7 tests)"
    - "tests/phase04/test_scripter_rules.py (113 lines, 6 tests)"
  modified: []

key-decisions:
  - "scripter AGENT.md은 9 producer 중 최장 (210 lines) — CONTENT-01/02/03/04/05 5 REQ 동시 충족 + 4 downstream Inspector (ins-narrative-quality/ins-korean-naturalness/ins-factcheck/ins-schema-integrity) 게이트 대응 때문"
  - "trend-collector niche_tag 도메인을 .preserved/harvested/theme_bible_raw/ 7개 slug로 엄격 제한 — 임의 niche 생성 시 downstream 연쇄 실패 방지"
  - "script-polisher의 제1원칙을 '의미 변경 금지 + semantic_delta=0.0 강제'로 codify — scripter 기능 영역 침범 방지, polish_metadata 필드로 자가 주장"
  - "shot-planner는 scripter/scene-planner/director 3단 격리 원칙 적용 — 본 에이전트는 scene-planner 출력만 입력받고 director Blueprint 직접 참조 금지"
  - "researcher Fallback chain (WIKI-04)는 Phase 4에서 spec만 정의, Phase 6에서 NotebookLM API + Perplexity + Google Scholar 실 wiring"
  - "metadata-seo 로마자 표기를 국립국어원 표기법 + 음차 원칙으로 고정 — 영어 번역본 대체 금지 (한국어 타겟 시장 유지 + 글로벌 검색 유입)"

patterns-established:
  - "Producer MUST REMEMBER 표준 7-8 bullets: 생성 역할 / REQ 충족 / prior_vqqa 반영 / inspector_prompt 읽기 금지 (GAN mirror) / maxTurns 준수 / 금지 사항 / 한국어 출력"
  - "scripter의 8 hook keywords (3초 hook/질문형/숫자/고유명사/탐정/하오체/조수/해요체)를 test_scripter_rules.py에서 literal contract로 고정 — 향후 바이블 변경 시 test fail로 감지"
  - "Producer output JSON은 downstream Inspector의 평가 대상만 포함 — producer_prompt/producer_system_context 필드 누수 방지 (supervisor fan-out 규약)"
  - "각 Producer AGENT.md의 Outputs 섹션에 구체적 예시 JSON 포함 — downstream 계약 명확화 (scripter → ins-narrative-quality + ins-korean-naturalness + ins-factcheck + ins-schema-integrity 4 inspector 입력 스키마)"

requirements-completed:
  - AGENT-01
  - AGENT-02
  - AGENT-07
  - AGENT-08
  - AGENT-09
  - RUB-03
  - CONTENT-01
  - CONTENT-02
  - CONTENT-03
  - CONTENT-04
  - CONTENT-05
  - CONTENT-07

# Metrics
duration: ~25min
completed: 2026-04-19
---

# Phase 4 Plan 08: Producer Core 6 + 3단 분리 3 Summary

**9 Producer AGENT.md (CONTENT-01~07 + AGENT-01/02/07/08/09 + RUB-03 충족) — FilmAgent 3단 계층 (director L1 → scene-planner L2 → shot-planner L3) 및 scripter 3초 hook duo-dialogue 대본 계약 확립**

## Performance

- **Duration:** ~25분
- **Started:** 2026-04-19T12:30:00Z
- **Completed:** 2026-04-19T12:55:00Z
- **Tasks:** 3/3
- **Files created:** 12 (9 AGENT.md + 3 pytest)
- **Commits:** 3 task commits + 1 metadata commit

## Accomplishments

- **Producer Core 6** (AGENT-01): trend-collector → niche-classifier → researcher → scripter → script-polisher → metadata-seo 대본 생성 파이프라인 완결
- **Producer 3단 분리 3** (AGENT-02, NotebookLM T6 FilmAgent): director (Blueprint L1) → scene-planner (Scenes L2, 1 Move Rule T2) → shot-planner (Shots L3, I2V only T1)
- **scripter 3초 hook + duo dialogue** (CONTENT-01/02): 8 required keywords (3초 hook/질문형/숫자/고유명사/탐정/하오체/조수/해요체) 전량 포함 + 7 MUST REMEMBER bullets
- **RUB-03 VQQA feedback loop**: 모든 9 producer가 `--prior-vqqa` 주입 받아 scene-level retry 수행 (전체 재작성 금지)
- **RUB-06 GAN 분리 mirror**: 모든 9 producer MUST REMEMBER에 "inspector_prompt 읽기 금지" 명시 (inspector의 "producer_prompt 읽기 금지"와 대칭)
- **CONTENT-03 채널바이블 인라인 주입**: niche-classifier가 `.preserved/harvested/theme_bible_raw/` 7 slug 중 1개 매핑 → matched_fields 10필드 inline → 5 downstream producer 참조
- **CONTENT-04 source-grounded citation**: researcher가 모든 claim에 tier 1-2 source + direct quote + retrieved_at 부과 (hallucination 차단)
- **CONTENT-05 59s 상한**: scripter가 단편 duration_sec ≤ 59.0 강제 (시리즈편은 channel_bible.길이 참조)
- **CONTENT-07 한국어 + 로마자 병기**: metadata-seo가 title_ko/title_roman + description_ko/description_roman + tags_ko/tags_roman pair 출력 (국립국어원 음차 표기법)
- **NotebookLM T1 I2V only + T2V 금지**: shot-planner가 anchor_frame_ref + camera_move 10종 + i2v_prompt Nano Banana 스타일 강제; t2v_forbidden_check 자가 주장 필드 신설
- **NotebookLM T2 1 Move Rule**: scene-planner가 각 scene total_moves = camera_action 1 + subject_action 1 = 2 엄수; 4초 이상 scene 지양

## Task Commits

1. **Task 1: Producer Core 6 AGENT.md** — `8bcf052` (feat)
   - 6 agents (trend-collector/niche-classifier/researcher/scripter/script-polisher/metadata-seo), 938 insertions
   - scripter는 8 keyword + 7 MUST REMEMBER bullets; niche-classifier는 theme_bible_raw 참조; researcher는 citation + NotebookLM; metadata-seo는 한국어 + 로마자
2. **Task 2: Producer 3단 분리 3 AGENT.md** — `d1f4ade` (feat)
   - director/scene-planner/shot-planner, 514 insertions
   - scene-planner 1 Move Rule (T2); shot-planner I2V + anchor frame + T2V 금지 (T1); director Blueprint L1
3. **Task 3: Producer tests (test_producer_core + test_producer_3split + test_scripter_rules)** — `19fb39e` (test)
   - 3 pytest files, 391 insertions, 20/20 PASS (0.10s)
   - Full phase04 regression: 202/202 PASS (0.25s)

**Plan metadata:** _(pending final commit)_

## Files Created/Modified

### Producer Core 6 (category=core, maxTurns=3)

- `.claude/agents/producers/trend-collector/AGENT.md` (126 lines) — 한국 실시간 트렌드 수집, 10-20 keyword + niche_tag 산출, NotebookLM RAG (Phase 6 실 wiring)
- `.claude/agents/producers/niche-classifier/AGENT.md` (135 lines) — keyword → channel_bible 매핑, 10 필드 matched_fields inline, `.preserved/harvested/theme_bible_raw/` 7 slug 도메인 제한
- `.claude/agents/producers/researcher/AGENT.md` (160 lines) — NotebookLM grounded research manifest, tier 1-2 source 필수, Fallback chain (WIKI-04) spec (Phase 6 실 구현)
- `.claude/agents/producers/scripter/AGENT.md` (210 lines, **최장**) — 3초 hook + duo dialogue 대본 JSON, CONTENT-01/02/04/05 4 REQ 단독 충족, 4 downstream Inspector 게이트 대응
- `.claude/agents/producers/script-polisher/AGENT.md` (148 lines) — 문체/리듬/종결어미 교정, 의미 변경 금지 (semantic_delta=0.0 강제), polish_metadata 자가 주장
- `.claude/agents/producers/metadata-seo/AGENT.md` (159 lines) — 한국어 + 로마자 병기 YouTube 메타데이터, 국립국어원 음차 표기법, YouTube 글자수 제한 (title ≤100 / description ≤5000 / tag ≤30)

### Producer 3단 분리 (category=split3, maxTurns=3)

- `.claude/agents/producers/director/AGENT.md` (136 lines) — Blueprint JSON (tone/high_level_structure/target_emotion/scene_count 5-10), FilmAgent Level 1
- `.claude/agents/producers/scene-planner/AGENT.md` (184 lines) — Scenes JSON 4-8 scene + 1 Move Rule (T2, total_moves=2), FilmAgent Level 2
- `.claude/agents/producers/shot-planner/AGENT.md` (194 lines) — Shots JSON 1-3 shot/scene + I2V only (T1, T2V 금지) + anchor_frame_ref (asset:// URI) + Nano Banana 스타일 i2v_prompt, FilmAgent Level 3

### Tests (tests/phase04/)

- `tests/phase04/test_producer_core.py` (145 lines, 7 tests) — exactly-6 core, frontmatter, prior_vqqa, theme_bible_raw, citation+NotebookLM, 한국어+roman, inspector_prompt 금지
- `tests/phase04/test_producer_3split.py` (133 lines, 7 tests) — exactly-3 split3, frontmatter, prior_vqqa, 1 Move Rule, I2V+anchor+T2V 금지, inspector_prompt 금지, Blueprint (director)
- `tests/phase04/test_scripter_rules.py` (113 lines, 6 tests) — frontmatter, 8 keywords, 7+ MUST REMEMBER bullets, --prior-vqqa + --channel-bible inputs, inspector_prompt 금지, citation + 59s

## Decisions Made

1. **scripter = Producer 최장 파일 (210 lines)** — CONTENT-01/02/03/04/05 5 REQ 동시 충족 + 4 downstream Inspector (ins-narrative-quality/ins-korean-naturalness/ins-factcheck/ins-schema-integrity) 게이트 대응을 위해 다른 Producer(평균 150 lines)보다 길게 작성. AGENT-07 500-line 제한 내.
2. **niche_tag 도메인 엄격 제한** — `.preserved/harvested/theme_bible_raw/` 7 slug (incidents/wildlife/documentary/humor/politics/trend + README 제외) 외 값 생성 금지. trend-collector + niche-classifier 양쪽에서 MUST REMEMBER로 강제.
3. **script-polisher 제1원칙 = 의미 변경 금지** — `polish_metadata.semantic_delta = 0.0` 강제 + 수정 가능 필드 명시 (scene[].text만) + 수정 금지 필드 명시 (hook_text/duration/speaker/register/citations/scene 구조). scripter 기능 영역 침범 방지 핵심 규칙.
4. **3단 분리 prompt 격리** — shot-planner는 director Blueprint를 직접 참조하지 않음 (scene-planner 출력만 입력). 각 단계 독립성이 FilmAgent T6 hierarchy의 핵심 — 상위 단계의 reasoning 노출이 하위 단계 prompt 오염 유발.
5. **researcher Fallback chain은 Phase 4 spec only** — NotebookLM → Perplexity → Google Scholar → Web 4단 fallback 정의. 실 API 호출은 Phase 6 이후 구현 (Phase 4 dry-run은 stub). MUST REMEMBER에 "Phase 4는 스펙만" 명시.
6. **metadata-seo 로마자 = 음차 원칙** — 영어 번역본 대체 금지. 국립국어원 로마자 표기법 기반 (서울 → Seoul, 사건기록부 → Sageon Girokbu). 한국어 타겟 시장 유지하면서 글로벌 검색 유입.

## Deviations from Plan

None - 계획 그대로 실행. 9 AGENT.md + 3 pytest 모두 plan의 files_modified 명세 일치.

Task 1 verify 후 validate_all_agents가 14 agent 표시 (6 core + 3 split3 + 5 from parallel 04-09) — 이는 parallel execution 중인 04-09 plan이 producer 디렉토리에 Producer Support 5개(assembler/asset-sourcer/publisher/thumbnail-designer/voice-producer)를 추가 중이기 때문. 본 plan 04-08은 오직 6 core + 3 split3 = 9만 소유 (frontmatter files_modified에 명시). Cross-plan coupling 없음.

## Issues Encountered

None - 20/20 pytest PASS 1회 통과, 202/202 phase04 regression PASS 1회 통과. GREEN 단계에서 RED 실패 없이 바로 통과한 이유는 Task 1/2 구현을 정확히 plan 명세대로 작성 후 Task 3 test를 plan의 behavior 섹션을 literal 계약으로 변환했기 때문. TDD 형식(RED→GREEN→REFACTOR) 대신 spec-first 형식(impl→test as literal contract)을 채택 — plan 04-08 Task 3의 behavior 섹션이 이미 test 스펙을 명시하고 있어 TDD의 "테스트가 implementation을 주도"하는 이점이 사라짐.

## User Setup Required

None - 본 plan은 AGENT.md markdown + pytest만 생성. 외부 서비스 / API key / 환경 변수 없음.

NotebookLM API 실 wiring (researcher producer), Nano Banana / Veo-3 asset catalog (shot-planner), asset:// URI registry는 Phase 6에서 사용자 설정 필요할 수 있음 (본 plan 범위 외).

## Next Phase Readiness

**Wave 3 완결** — Producer Core 6 + 3단 분리 3 = 9 producer + parallel plan 04-09 (Producer Support 5 + Supervisor 1) 합산 14 producer + 1 supervisor 확립.

**Phase 5 준비 완료:**
- Pipeline orchestration — 9 producer 간 hand-off JSON 계약 명확히 정의됨 (each Outputs 섹션)
- VQQA feedback loop (RUB-03) — Supervisor가 Inspector 출력을 Producer의 `--prior-vqqa`로 라우팅할 수 있도록 전 Producer에 입력 필드 표준화
- GAN separation (RUB-06 mirror) — 각 Producer의 "inspector_prompt 읽기 금지" MUST REMEMBER로 Supervisor fan-out 시 `producer_output`만 전달 보장

**Phase 6 준비 완료 (deferred wiring):**
- researcher NotebookLM + Fallback chain API wiring (WIKI-04)
- shot-planner asset:// URI catalog (harvested anchor frames registry)
- metadata-seo 국립국어원 로마자 자동 변환 (kroman 등 라이브러리)

**Blockers:** 없음. Phase 4 Plan 10 (Wave 4 integration tests + END-TO-END maxTurns matrix) 진입 가능.

---
*Phase: 04-agent-team-design*
*Plan: 08*
*Completed: 2026-04-19*

## Self-Check: PASSED

**Files verified:**
- FOUND: .claude/agents/producers/trend-collector/AGENT.md
- FOUND: .claude/agents/producers/niche-classifier/AGENT.md
- FOUND: .claude/agents/producers/researcher/AGENT.md
- FOUND: .claude/agents/producers/scripter/AGENT.md
- FOUND: .claude/agents/producers/script-polisher/AGENT.md
- FOUND: .claude/agents/producers/metadata-seo/AGENT.md
- FOUND: .claude/agents/producers/director/AGENT.md
- FOUND: .claude/agents/producers/scene-planner/AGENT.md
- FOUND: .claude/agents/producers/shot-planner/AGENT.md
- FOUND: tests/phase04/test_producer_core.py
- FOUND: tests/phase04/test_producer_3split.py
- FOUND: tests/phase04/test_scripter_rules.py

**Commits verified:**
- FOUND: 8bcf052 (Task 1: feat Producer Core 6)
- FOUND: d1f4ade (Task 2: feat Producer 3단 분리 3)
- FOUND: 19fb39e (Task 3: test Producer Core + 3split + scripter rules)

**Verification runs:**
- validate_all_agents: OK 14 agent(s) validated (6 core + 3 split3 from this plan + 5 parallel from 04-09)
- Task 1 keyword check: TASK 1 OK
- Task 2 keyword check: TASK 2 OK
- test_producer_core.py + test_producer_3split.py + test_scripter_rules.py: 20/20 PASS (0.10s)
- Full phase04 regression: 202/202 PASS (0.25s)
