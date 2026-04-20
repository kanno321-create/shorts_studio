# Roadmap — naberal-shorts-studio

**Granularity:** fine (10 phases target)
**Mode:** yolo (autonomous execution where gates permit)
**Parallelization:** true
**Coverage:** 96/96 v1 requirements mapped (100%)
**Through-line:** shorts_naberal 39 drift conflict 재발 차단 + YPP 진입 궤도 확보
**Derived from:** PROJECT.md (10 Key Decisions D-1~D-10) + REQUIREMENTS.md (96 v1 REQ / 17 categories) + research/SUMMARY.md §10 Build Order

---

## Phases

- [x] **Phase 1: Scaffold** — naberal_harness v1.0.1 상속 + Hook 3종 자동 설치 (세션 #10 완료)
- [x] **Phase 2: Domain Definition** — 3-Tier 위키 물리 구조 생성 + 도메인 스코프 확정 (세션 #14 완료 2026-04-19, studio@f360e17)
- [x] **Phase 3: Harvest** — shorts_naberal 작동 자산 이관 + CONFLICT_MAP 39 전수 판정 + Tier 3 attrib +R 잠금 (세션 #15 완료 2026-04-19, verify_harvest --full 15/15 PASS)
- [x] **Phase 4: Agent Team Design** — 17 inspector + Producer 14 + Supervisor 1 = 32 에이전트 + rubric JSON Schema **동시 정의** (세션 #16 완료 2026-04-19, studio@62c0758)
- [x] **Phase 5: Orchestrator v2** — 500~800줄 state machine + 12 GATE + DAG + 영상/음성 분리 합성 (세션 #18 완료 2026-04-19, 329 pytest green + SC 1-6 PASS + 17/17 REQs complete)
- [x] **Phase 6: Wiki + NotebookLM + FAILURES Reservoir** — Tier 2 합성 + 2-노트북 세팅 + Continuity Bible Prefix + 저수지 패턴 (세션 #19 완료 2026-04-19, 236 pytest green + SC 1-6 PASS + 9/9 REQs complete + D-14 sha256 a1d92cc1... immutable)
- [x] **Phase 7: Integration Test** — E2E mock asset + verify_all_dispatched() 13 gates + CircuitBreaker 3×300s + Fallback ken-burns THUMBNAIL + harness-audit ≥ 80 (세션 #20 완료 2026-04-19, 177 Phase 7 tests + 809 regression = 986/986 green + SC 1-5 all PASS + 5/5 REQs complete + 3 Research Corrections anchored)
- [x] **Phase 8: Remote + Publishing + Production Metadata** — GitHub push + YouTube API v3 + AI disclosure 자동 ON + Reused content 증명 (세션 #22 완료 2026-04-19, 8/8 plans + 8/8 REQs + 6/6 SC PASS + 3 anchors permanent + 986 + Phase 8 regression green)
- [x] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — KPI 목표 설정 + 월 1회 대표님 taste 평가 회로 가동 (세션 #23 완료 2026-04-20, 6/6 plans + 4/4 SC PASS + 2/2 REQs)
- [x] **Phase 9.1: Production Engine Wiring** — producer/supervisor Claude SDK wiring + Nano Banana Pro adapter + CharRegistry + Ken-Burns FFmpeg 로컬 + Runway VALID_RATIOS_BY_MODEL + ElevenLabs voice 3-tier + Stage 2→4 smoke $0.29 (세션 #24 YOLO 완결 2026-04-20, 8/8 plans + 7/7 REQs + 15/15 decisions)
- [x] **Phase 10: Sustained Operations** — 주 3~4편 자동 발행 + 첫 1~2개월 SKILL patch 전면 금지 (D-2 저수지)
 (completed 2026-04-20)

- [ ] **Phase 11: Pipeline Real-Run Activation + Script Quality Mode** — D10-PIPELINE-DEF-01 5-item backlog 해결 + 영상 1편 실 발행 + D10-SCRIPT-DEF-01 옵션 확정 (planned 2026-04-21)

---

## Phase Details

### Phase 1: Scaffold

**Status:** ✅ COMPLETED (session #10, 2026-04-18)
**Goal:** naberal_harness v1.0.1 Layer 1 인프라를 `studios/shorts/`로 상속하고 Hook 3종을 활성화하여, 작업 시작 즉시 `skip_gates=True` / `TODO(next-session)` 등 deprecated 패턴이 물리 차단되는 상태로 만든다.
**Depends on:** Nothing (첫 phase)
**Requirements:** INFRA-01, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. `studios/shorts/` 디렉토리가 존재하고 `.claude/hooks/` 3종(`pre_tool_use.py`, `post_tool_use.py`, `session_start.py`)이 실행 가능 상태로 설치되어 있다
  2. `settings.json`에 Hook 3종이 등록되어 있어 신규 세션 시작 시 자동 감사가 발동된다
  3. 공용 5 스킬(progressive-disclosure, drift-detection, gate-dispatcher, context-compressor, harness-audit)이 `.claude/skills/`에 상속되어 호출 가능하다
  4. `skip_gates=True` 문자열을 포함한 커밋 시도가 pre_tool_use 훅에서 실제로 차단된다 (수동 검증 완료)
**Plans:** Complete (세션 #10 핸드오프 문서 기록됨)

---

### Phase 2: Domain Definition

**Goal:** 3-Tier 위키 디렉토리 물리 구조를 확정하고 도메인 스코프(콘텐츠 니치 승계, RPM 보수값, Harvest 범위)를 결정하여, Phase 3 Harvest 작업이 명확한 타겟 위에서 실행될 수 있는 상태를 만든다.
**Depends on:** Phase 1
**Requirements:** INFRA-02
**Success Criteria** (what must be TRUE):
  1. 3개 Tier 디렉토리가 모두 존재한다: `naberal_harness/wiki/`, `studios/shorts/wiki/`, `studios/shorts/.preserved/harvested/`
  2. `naberal_harness/STRUCTURE.md`가 Tier 1 wiki 추가를 반영하도록 schema bump 커밋되어 있다 (Whitelist 위반 없음)
  3. `CLAUDE.md`의 `{{TODO}}` 5종(ONE_LINE_DESCRIPTION, DOMAIN_GOAL, PIPELINE_FLOW, DOMAIN_ABSOLUTE_RULES, TRIGGER_PHRASES)이 모두 치환되어 "shorts_naberal 니치 승계 + 주 3~4편 + YPP 진입"이 문서로 선언되어 있다
  4. Harvest 범위 결정서(`HARVEST_SCOPE.md` 또는 동등 문서)가 존재하여 Phase 3이 무엇을 가져올지/버릴지 명확하다
**Plans:** 6/6 plans executed ✅ PHASE 2 COMPLETE 2026-04-19
- [x] 02-01-PLAN.md — harness STRUCTURE.md schema bump v1.0.0 to v1.1.0 (W1) — ✅ shipped 2026-04-19, harness@8a8c32b
- [x] 02-02-PLAN.md — Tier 1 harness/wiki/ + README.md (W2) — ✅ shipped 2026-04-19, harness@1ff2e34
- [x] 02-03-PLAN.md — Tier 2 studios/shorts/wiki/ 5 MOC + README + Tier 3 .preserved/harvested/ (W2) — ✅ shipped 2026-04-19 (content committed in consolidated f360e17)
- [x] 02-04-PLAN.md — studios/shorts/CLAUDE.md 5 TODO 치환 + line 7 typo fix (W3) — ✅ shipped 2026-04-19 (CLAUDE.md committed in consolidated f360e17)
- [x] 02-05-PLAN.md — 02-HARVEST_SCOPE.md (A급 13건 사전 판정 + Blacklist + B/C 위임) (W3) — ✅ shipped 2026-04-19 (175 lines; file committed in consolidated f360e17)
- [x] 02-06-PLAN.md — 12 VALIDATION tests + studio Phase 2 consolidated commit (W4) — ✅ shipped 2026-04-19 (studio@f360e17, 12/12 PASS, SC 4/4 achieved)

---

### Phase 3: Harvest

**Goal:** shorts_naberal의 작동 검증된 자산(theme-bible, Remotion src, hc_checks, FAILURES, API wrappers)을 `.preserved/harvested/`에 읽기 전용으로 이관하고 CONFLICT_MAP 39건을 전수 판정하여, Phase 4 Agent 설계가 "무엇을 승계하고 무엇을 폐기하는가"라는 질문 없이 진행될 수 있는 기반을 구축한다.
**Depends on:** Phase 2 (scope 결정 후 실행)
**Requirements:** HARVEST-01, HARVEST-02, HARVEST-03, HARVEST-04, HARVEST-05, HARVEST-06, HARVEST-07, HARVEST-08, AGENT-06
**Success Criteria** (what must be TRUE):
  1. `.preserved/harvested/` 하위에 4개 raw 디렉토리(theme_bible_raw, remotion_src_raw, hc_checks_raw, api_wrappers_raw)가 존재하고 각 파일이 원본과 diff 0 상태로 복사되어 있다
  2. `.preserved/harvested/` 전체가 `chmod -w` 적용되어 실제 수정 시도 시 OS 레벨에서 거부된다 (Tier 3 immutable 검증)
  3. `HARVEST_DECISIONS.md`가 존재하고 CONFLICT_MAP 39건(A:13/B:16/C:10) 각각에 대해 "승계"/"폐기"/"통합 후 재작성" 판단이 명시되어 있다
  4. `.claude/failures/_imported_from_shorts_naberal.md`가 생성되어 과거 학습 자산이 사용 가능한 상태로 통합되어 있다
  5. Harvest Blacklist 문서가 `orchestrate.py:1239-1291 skip_gates 블록`을 포함한 금지 import 목록을 명시하고 있으며, harvest-importer 에이전트가 이를 참조한다
**Plans:** 9/9 plans complete
- [x] 03-01-PLAN.md — harvest-importer AGENT.md + 7 Python stdlib modules (W0, AGENT-06)
- [x] 03-02-PLAN.md — path_manifest.json (filesystem-verified source mapping, W0, HARVEST-01/02/03/05/07) — ✅ shipped 2026-04-19, studio@609c3f8
- [x] 03-03-PLAN.md — theme_bible_raw copy (W1, HARVEST-01) — ✅ shipped 2026-04-19, studio@fba21e4 (7 md files byte-identical, diff_verifier mismatches=[], manifest-driven shutil.copytree)
- [x] 03-04-PLAN.md — remotion_src_raw copy, node_modules 제외 (W1, HARVEST-02) — ✅ shipped 2026-04-19, studio@4bc7ece (40 files / 0.161 MB, node_modules 758 MB excluded, diff_verifier mismatches=[], __pycache__/secret 0 hits)
- [x] 03-05-PLAN.md — hc_checks_raw cherry_pick (W1, HARVEST-03) — ✅ shipped 2026-04-19, studio@51205ba (hc_checks.py 1129 lines + test_hc_checks.py byte-identical, orchestrate.py blacklist enforced)
- [x] 03-06-PLAN.md — api_wrappers_raw cherry_pick 4+ wrappers (W1, HARVEST-05) — ✅ shipped 2026-04-19, studio@aeac16b (5/5 wrappers byte-identical: elevenlabs_alignment.py + tts_generate.py + _kling_i2v_batch.py + runway_client.py + heygen_client.py; 0 selenium imports; orchestrate.py absent)
- [x] 03-07-PLAN.md — diff_verifier --all + FAILURES merge (W2, HARVEST-04) — ✅ shipped 2026-04-19, studio@ad98b32 (Task 1 ALL_CLEAN across 4 raw dirs) + studio@1ff5768 (Task 2 _imported_from_shorts_naberal.md 500 lines, sha256=978bb9381fee..., idempotent SOURCES-locked merge)
- [x] 03-08-PLAN.md — 03-HARVEST_DECISIONS.md 39 rows + blacklist grep audit (W3, HARVEST-07/08) — ✅ shipped 2026-04-19, studio@15b827f (Task 1: decisions.md 39 rows A:13/B:16/C:10) + studio@c14ab95 (Task 2: 7-check blacklist audit PASS, 0 matches)
- [x] 03-09-PLAN.md — attrib +R lockdown + verify_harvest --full (W4, HARVEST-06) — ✅ shipped 2026-04-19, studio@8ae370e (Task 1: Tier 3 lockdown 55 files R-flagged, PermissionError probe PASS) + studio@d4fc5e4 (Task 2: verify_harvest --full 15/15 PASS, 03-VALIDATION.md frontmatter flipped complete/true/true). **PHASE 3 COMPLETE.**

---

### Phase 4: Agent Team Design

**Goal:** 17 inspector 6 카테고리 + Producer 팀(3단 분리: Director/ScenePlan/ShotPlan) + Supervisor를 rubric JSON Schema와 **동시에** 정의하여, Producer-Reviewer 이중 생성 파이프라인이 한국어 화법 / 컴플라이언스 / 채널 정체성 기준으로 자동 평가 가능한 상태를 만든다. 콘텐츠·음성·자막·컴플라이언스 규칙도 이 시점에서 에이전트 프롬프트에 결합된다.
**Depends on:** Phase 3 (Harvest 자산을 에이전트 prompt 참조용으로 사용)
**Requirements:** AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-07, AGENT-08, AGENT-09, RUB-01, RUB-02, RUB-03, RUB-04, RUB-05, RUB-06, CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, CONTENT-05, CONTENT-06, CONTENT-07, AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04, SUBT-01, SUBT-02, SUBT-03, COMPLY-01, COMPLY-02, COMPLY-03, COMPLY-04, COMPLY-05, COMPLY-06
**Success Criteria** (what must be TRUE):
  1. `.claude/agents/` 하위에 Producer 14명(Core 6 + 3단 분리 3 + 지원 5: trend-collector, niche-classifier, researcher, director, scene-planner, shot-planner, scripter, script-polisher, metadata-seo, voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher) + Inspector 17명(6 카테고리) + Supervisor 1명 = **총 32명** 존재한다. **SC1 reconciliation (Plan 10 Wave 5, 2026-04-19):** 원안 "12~20 사이"는 Phase 2 ROADMAP 초기 추정치였으며, REQUIREMENTS.md AGENT-01~05 및 Phase 4 RESEARCH.md Open Q1의 enumeration(Producer 14 + Inspector 17 + Supervisor 1 = 32)이 우선한다. Phase 2 대비 Producer re-enumeration(11→14) + SC1 범위 상향(20→32)은 Plan 10 reconciliation gate에서 공식 반영 완료. (D-9 PROJECT.md 경향: REQUIREMENTS.md 구체성 > ROADMAP SC 근사값.)
  2. 17 inspector 각각이 rubric JSON Schema에 맞는 `{verdict: PASS|FAIL, score, evidence[], semantic_feedback}` 구조를 반환한다 (VQQA 시맨틱 그래디언트 포함)
  3. 모든 SKILL.md가 500줄 이하이고 description 필드가 1024자 이하이며 MUST REMEMBER 지시가 프롬프트 **끝**에 배치되어 있다 (harness-audit 검증 통과)
  4. 테스트 입력으로 LogicQA Main-Q + 5 Sub-Qs 다수결이 실제로 작동하여 단일 inspector가 모순 시 FAIL을 반환한다 (maxTurns 표준 3, factcheck 예외 10)
  5. 한국어 화법 검사기(`ins-korean-naturalness`)가 존댓말/반말 혼용 샘플 10건 중 ≥ 9건을 교정 제안과 함께 FAIL 처리한다
  6. Compliance inspector 세트(`ins-license`, `ins-platform-policy`, `ins-safety`, `ins-mosaic`)가 AF-4(voice cloning real people), AF-5(real victim face), AF-13(K-pop 음원) 샘플을 100% 차단한다
**Plans:** 10/10 plans complete
- [x] 04-01-PLAN.md — W0 Wave 0 shared foundation: rubric-schema.json + agent-template.md + af_bank + korean_samples + 4 stdlib validators + pytest conftest — ✅ shipped 2026-04-19, studio@0dcb007+cd1d074+daca457+5a70504 (6 shared files + 5 validators + 14/14 pytest PASS; RUB-04 + AGENT-07/08/09 + COMPLY-01..06 + AUDIO-04 + SUBT-02 = 12 REQs satisfied; harness_audit score 95 on Wave 0 state)
- [x] 04-02-PLAN.md — W1 Inspector Structural 3 (ins-blueprint-compliance, ins-timing-consistency, ins-schema-integrity; maxTurns=1) — ✅ shipped 2026-04-19
- [x] 04-03-PLAN.md — W1 Inspector Content 3 (ins-factcheck maxTurns=10, ins-narrative-quality, ins-korean-naturalness) + 10/9+ FAIL regression — ✅ shipped 2026-04-19, studio@852ddca
- [x] 04-04-PLAN.md — W1 Inspector Style 3 (ins-tone-brand maxTurns=5, ins-readability, ins-thumbnail-hook) — ✅ shipped 2026-04-19, studio@df5a1b3
- [x] 04-05-PLAN.md — W2 Inspector Compliance 3 (ins-license, ins-platform-policy, ins-safety) + AF-4/13 100% 차단 — ✅ shipped 2026-04-19, studio@c53ccef
- [x] 04-06-PLAN.md — W2 Inspector Technical 3 (ins-audio-quality, ins-render-integrity, ins-subtitle-alignment) — ✅ shipped 2026-04-19, studio@3d0b250
- [x] 04-07-PLAN.md — W2 Inspector Media 2 (ins-mosaic, ins-gore) + AF-5 100% 차단 — ✅ shipped 2026-04-19, studio@6cea65f
- [x] 04-08-PLAN.md — W3 Producer Core 6 + 3단 분리 3 (trend-collector, niche-classifier, researcher, director, scene-planner, shot-planner, scripter, script-polisher, metadata-seo) — ✅ shipped 2026-04-19, studio@9a82729
- [x] 04-09-PLAN.md — W4 Producer 지원 5 + Supervisor 1 (voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher, shorts-supervisor) + _delegation_depth guard — ✅ shipped 2026-04-19, studio@90223c3
- [x] 04-10-PLAN.md — W5 Integration: harness-audit ≥ 80 + GAN contamination 0 + LogicQA schema 17/17 + SC1 reconciliation 32 canonical — ✅ shipped 2026-04-19, studio@778745a+62c0758 (harness_audit score 100, 244/244 pytest PASS, GAN_CLEAN 17/17, total=32 agents). **PHASE 4 COMPLETE.**

**Note on SC1 reconciliation (RESEARCH Open Q1) — RESOLVED 2026-04-19 by Plan 10:** Original SC1 "12~20 사이"는 Phase 2 초안이었다. Phase 4 RESEARCH.md의 REQUIREMENTS enumeration (Producer 14 + Inspector 17 + Supervisor 1 = 32)이 우선한다. Plan 10 Wave 5 (studio@62c0758)에서 SC1 문구를 32 canonical로 amend 완료. D-9 PROJECT.md 경향 적용: REQUIREMENTS.md 구체성 > ROADMAP SC 근사값. 이로써 Open Question 1은 공식 종결.

**UI hint:** no

---

### Phase 5: Orchestrator v2 Write

**Goal:** `scripts/orchestrator/shorts_pipeline.py`를 500~800줄 state machine으로 작성하여 12 GATE DAG + CircuitBreaker + Checkpointer + 영상/음성 분리 합성 + Low-Res First 렌더 파이프라인을 완성하고, `skip_gates` 파라미터를 물리적으로 제거함으로써 shorts_naberal 5166줄 drift의 재발을 구조적으로 차단한다. 영상 생성 기술 스택(Kling/Runway/Shotstack)도 이 오케스트레이터 호출 규격에 맞춰 wrapping 된다.
**Depends on:** Phase 4 (Producer/Reviewer 에이전트가 먼저 존재해야 오케스트레이터가 호출 가능)
**Requirements:** ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, ORCH-08, ORCH-09, ORCH-10, ORCH-11, ORCH-12, VIDEO-01, VIDEO-02, VIDEO-03, VIDEO-04, VIDEO-05
**Success Criteria** (what must be TRUE):
  1. `shorts_pipeline.py`가 500~800줄 사이이며 12 GATE(IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE)가 Python enum + 명시적 transition으로 선언되어 있다
  2. 소스 전체에 `skip_gates` 문자열이 0회 등장하고 pre_tool_use 훅이 해당 파라미터 추가 시도를 차단한다 (grep + 훅 실측 검증)
  3. `GateGuard.dispatch()`가 Reviewer FAIL 시 실제로 raise 하며, `verify_all_dispatched()`가 17 GATE 모두 호출 확인 후에만 COMPLETE로 전이한다
  4. CircuitBreaker가 3회 연속 실패 시 5분 cooldown으로 재시도 거부를 반환하고, 재생성 루프 3회 초과 시 FAILURES 기록 + "정지 이미지 + 줌인" Fallback 샷이 실행된다
  5. Kling 2.6 Pro primary → Runway Gen-3 Alpha Turbo backup 체인이 API 실패 시 자동 전환되며, T2V 호출은 코드 경로 자체에 존재하지 않는다 (I2V + Anchor Frame only)
  6. 영상/음성이 완전 분리 생성 후 타임스탬프 매핑으로 합성되며, 초안 렌더는 720p Low-Res First로 강제된 뒤 AI 업스케일이 적용된다
**Plans:** 10/10 plans executed ✅ PHASE 5 COMPLETE 2026-04-19
- [x] 05-01-PLAN.md — W1 FOUNDATION: scripts/orchestrator/ + scripts/hc_checks/ scaffolding + GateName IntEnum 15 members + GATE_DEPS DAG + 10-class exception hierarchy + deprecated_patterns.json + 3 validation CLIs — ✅ shipped 2026-04-19, studio@eebfe32 (ORCH-02/03/07/08/09)
- [x] 05-02-PLAN.md — W2 CircuitBreaker 3/300s state machine + 21 tests — ✅ shipped 2026-04-19, studio@c13c219+5ee9c19 (ORCH-06)
- [x] 05-03-PLAN.md — W2 Checkpointer atomic JSON + 19 tests — ✅ shipped 2026-04-19, studio@2135745 (ORCH-05)
- [x] 05-04-PLAN.md — W2 GateGuard dispatch/verify + 23 tests — ✅ shipped 2026-04-19, studio@8380421 (ORCH-03/04/07)
- [x] 05-05-PLAN.md — W3 VoiceFirstTimeline audio-first assembly — ✅ shipped 2026-04-19, studio@2a4cd49 (ORCH-10 + VIDEO-02/03)
- [x] 05-06-PLAN.md — W4 API adapters: models + kling_i2v + runway_i2v + typecast + elevenlabs + shotstack — ✅ shipped 2026-04-19, studio@ce8f4fe (VIDEO-01/02/04/05 + ORCH-10/11)
- [x] 05-07-PLAN.md — W5 shorts_pipeline.py 787-line ShortsPipeline keystone + fallback.py + 24 tests — ✅ shipped 2026-04-19, studio@16303f4 (ORCH-01/02/11/12)
- [x] 05-08-PLAN.md — W6 hc_checks regression port: 1176-line rewrite preserving 13 public signatures + 41 tests — ✅ shipped 2026-04-19, studio@6b3f744 (ORCH-01 reinforced)
- [x] 05-09-PLAN.md — W6 Hook enforcement regression: 5 subprocess test files / 31 tests proving Hook denies blacklist + allows canonical I2V — ✅ shipped 2026-04-19, studio@9c7d266 (ORCH-08/09 + VIDEO-01 Hook layer)
- [x] 05-10-PLAN.md — W7 FINAL VERIFICATION: 4 test files (33 tests) + 17-REQ TRACEABILITY.md + 05-VALIDATION.md flip to nyquist_compliant=true — ✅ shipped 2026-04-19, studio@a17f58f (329/329 pytest green, SC 1-6 PASS, 17/17 REQs covered). **PHASE 5 COMPLETE.**

---

### Phase 6: Wiki + NotebookLM Integration + FAILURES Reservoir

**Goal:** Tier 2 `studios/shorts/wiki/`를 도메인 특화 노드(알고리즘/YPP/렌더/KPI/Continuity Bible)로 채우고 NotebookLM 2-노트북(일반/채널바이블)을 세팅하여 source-grounded RAG 쿼리가 환각 방지와 함께 모든 에이전트에서 호출 가능하게 하며, FAILURES.md append-only 저수지 + SKILL_HISTORY 백업을 가동하여 학습 충돌을 방지한다.
**Depends on:** Phase 4 (agent prompts가 wiki 노드 참조 형식을 고정해야 wiki 구조가 결정됨)
**Requirements:** WIKI-01, WIKI-02, WIKI-03, WIKI-04, WIKI-05, WIKI-06, FAIL-01, FAIL-02, FAIL-03
**Success Criteria** (what must be TRUE):
  1. `studios/shorts/wiki/`에 Obsidian 그래프로 상호 연결된 도메인 노드(알고리즘, YPP, 렌더, KPI, Continuity Bible)가 존재하며 `@wiki/shorts/xxx.md` 참조가 에이전트 프롬프트에서 작동한다
  2. NotebookLM 2-노트북(일반 + 채널바이블)이 세팅되어 Phase 3 Harvest 산출물을 소스로 한 질의가 source citation과 함께 응답된다
  3. NotebookLM Fallback Chain이 실제로 가동: RAG 실패 → grep wiki → hardcoded defaults 순서로 자동 전환된다 (의도적 API fail 시뮬레이션 검증)
  4. Continuity Bible Prefix(색상 팔레트, 카메라 렌즈, 시각적 스타일)가 모든 영상 생성 API 호출에 자동 주입되어 샘플 3개 연속 생성 시 시각적 일관성이 관찰 가능하다
  5. `FAILURES.md`가 append-only로 동작하며 (Hook이 직접 편집 차단), `SKILL_HISTORY/{skill_name}/v{n}.md.bak` 백업이 SKILL 수정 시 자동 생성된다
  6. 30일 집계 로직이 패턴 ≥ 3회 발견 시 `SKILL.md.candidate`를 생성하고 7일 staged rollout 대기 상태로 진입한다 (드라이런 검증)
**Plans:** 11/11 plans executed ✅ PHASE 6 COMPLETE 2026-04-19
- [x] 06-01-PLAN.md — Wave 0 FOUNDATION: scripts/wiki/ + tests/phase06/ scaffold + phase06_acceptance.py — ✅ shipped 2026-04-19, studio@6690e12 (15/15 tests green, scripts.wiki imports OK, phase06_acceptance exits 1 gracefully at Wave 0, phase05 regression 329/329 preserved)
- [x] 06-02-PLAN.md — Wave 1 WIKI CONTENT: 5 ready nodes + 5 MOC checkbox flips + 3 test files
- [x] 06-03-PLAN.md — Wave 2 NOTEBOOKLM WRAPPER: scripts/notebooklm/query.py subprocess wrapper (D-6/D-7)
- [x] 06-04-PLAN.md — Wave 2 LIBRARY REGISTRATION: library.json channel-bible entry (D-8) + deferred-items.md
- [x] 06-05-PLAN.md — Wave 2 FALLBACK CHAIN: 3-tier RAG -> grep -> defaults (D-5) — ✅ shipped 2026-04-19, studio@25993bb (scripts/notebooklm/fallback.py 231 lines: QueryBackend Protocol + RAGBackend/GrepWikiBackend/HardcodedDefaultsBackend + NotebookLMFallbackChain; 18 tests green [15 fallback_chain + 3 fallback_injection]; D-5 fault injection via monkeypatched subprocess rc=1 proves tier>=1 activation; WIKI-04 satisfied)
- [x] 06-06-PLAN.md — Wave 3 CONTINUITY MODEL: ContinuityPrefix pydantic v2 (D-20) + prefix.json — ✅ shipped 2026-04-19, studio@f661fa7 (scripts/orchestrator/api/models.py 164 lines: HexColor Annotated alias + ContinuityPrefix BaseModel with 7 D-20 fields + extra='forbid'; wiki/continuity_bible/prefix.json normalised to canonical 7-field form [dropped 4 metadata keys, audience_profile = canonical Korean literal]; 33 tests green [26 schema boundary + 7 serialization/drift]; Phase 5 329/329 preserved; Phase 6 123/123; WIKI-02 data-model layer complete)
- [x] 06-07-PLAN.md — Wave 3 SHOTSTACK INJECTION: filter[0] continuity_prefix + D-17 tail preservation (D-9/D-19) — ✅ shipped 2026-04-19, studio@20cdeed (scripts/orchestrator/api/shotstack.py 369→397 lines: DEFAULT_CONTINUITY_PRESET_PATH + _load_continuity_preset lazy loader returning None on missing prefix.json + _build_timeline_payload prepends 'continuity_prefix' at filters_order[0] with idempotency guard + emits timeline.continuity_preset=preset.model_dump() | None; 17 tests green [11 unit test_shotstack_prefix_injection.py + 6 integration test_filter_order_preservation.py asserting D-19 `['continuity_prefix','color_grade','saturation','film_grain']` by EXACT list equality per Pitfall 4 defence]; Phase 5 test_render_payload_carries_d17_filter_order isolated via monkeypatch to preserve D-17 tail contract; Phase 5 329/329 preserved; Phase 6 140/140; WIKI-02 runtime-wiring complete — every Shotstack render now auto-carries channel visual DNA)
- [x] 06-08-PLAN.md — Wave 4 HOOK EXTENSION: FAILURES append-only + SKILL_HISTORY backup (D-11/D-12/D-14) + 2 deprecated_patterns — ✅ shipped 2026-04-19, studio@88a3ae5 (.claude/hooks/pre_tool_use.py 152→272 lines: check_failures_append_only [D-11 basename-exact match + Windows-path-safe + _imported exempt] + backup_skill_before_write [D-12 v<YYYYMMDD_HHMMSS>.md.bak via shutil.copy2]; .claude/deprecated_patterns.json 6→8 entries as audit trail; .claude/failures/FAILURES.md + FAILURES_INDEX.md seeded [10-field schema + category index by fail-ID, never modifies _imported_from_shorts_naberal.md]; SKILL_HISTORY/README.md convention; 30 new tests green [14 in-process unit + 7 subprocess + 9 backup]; Phase 5 hook regression 31 tests + verify_hook_blocks.py 5/5 preserved; FAIL-01 + FAIL-03 satisfied)
- [x] 06-09-PLAN.md — Wave 4 AGGREGATION CLI: 30-day dry-run (D-13) — ✅ shipped 2026-04-19, studio@921886e (scripts/failures/aggregate_patterns.py 164 lines stdlib-only: argparse + hashlib + json + re + Counter + pathlib; ENTRY_RE/TRIGGER_RE parse both imported + seeded FAILURES.md schemas; iter_entries with missing-file warn-and-continue; normalize_pattern_key sha256[:12] 48-bit collision-safe per RESEARCH Area 8 [lowercase + punctuation-strip + whitespace-collapse + Korean preserved + trigger[:80] truncated]; aggregate with threshold filter + examples cap at 3; main CLI --input repeatable required + --threshold default 3 + --dry-run store_true default=True without BooleanOptionalAction [D-13 disable-impossibility encoded in argparse surface] + --output JSON + UTF-8 ensure_ascii=False + sys.stdout.reconfigure Windows cp949 fallback; scripts/failures/__init__.py 7-line namespace; 31 tests green [21 unit test_aggregate_patterns.py + 10 subprocess test_aggregate_dry_run.py]; Phase 6 217/217 PASS; D-13 verified rglob 3-root scan zero SKILL.md.candidate; D-14 verified sha256 a1d92cc1... _imported_from_shorts_naberal.md byte-identical before/after full suite; sample: threshold=3 against imported → candidates=[] total=12, threshold=1 both files → 13 unique candidates each count=1; FAIL-02 satisfied)
- [x] 06-10-PLAN.md — Wave 4 AGENT MASS UPDATE: 15 AGENT.md files + sha256 manifests (D-3/D-18) — ✅ shipped 2026-04-19, studio@948c4d9 (15 of 33 AGENT.md files edited with 52 @wiki/shorts refs across 5 Plan 02 ready nodes [continuity_bible/channel_identity 14 refs / algorithm/ranking_factors 11 / render/remotion_kling_stack 11 / kpi/retention_3second_hook 4 / ypp/entry_conditions 3]; 18 non-target agents byte-identical per sha256 manifest diff; 16 tests green [8 ref validation + 8 byte-diff regression guard]; validate_all_agent_refs returns 0 problems; Phase 6 186/186 PASS; D-3 + D-18 surgical scope proven; WIKI-05 satisfied)
- [x] 06-11-PLAN.md — Wave 5 PHASE GATE: D-14 sha256 + acceptance E2E + 9-REQ traceability + VALIDATION flip — ✅ shipped 2026-04-19, studio@18bb414+b64fbbe+7373f4e+d9285d1 (19 new tests: 5 D-14 sha256 full-file immutability + 7 acceptance E2E wrapper + 7 traceability orphan guard; 06-TRACEABILITY.md 9-REQ x source/test/SC matrix mirroring Phase 5 format; 06-VALIDATION.md frontmatter status=complete + nyquist_compliant=true + wave_0_complete=true + completed=2026-04-19, all 24 task rows ✅ green, 6 sign-off checkboxes [x], Completion Summary appended; Phase 5 baseline updated 6->8 deprecated_patterns as documented contract evolution (production Hook behaviour unchanged); phase06_acceptance.py exit 0 with 6/6 SC PASS; regression sweep Phase 4 244/244 + Phase 5 329/329 + Phase 6 236/236 + combined 809/809; D-14 sha256 a1d92cc1... + line count 500 unchanged since Phase 3 freeze). **PHASE 6 COMPLETE.**

---

### Phase 7: Integration Test

**Goal:** Phase 4/5/6 구성품을 mock asset으로 E2E 파이프라인 1회 완주하여 실 API 비용 없이 verify_all_dispatched() 통과 + CircuitBreaker + Fallback 샷이 실측 작동함을 증명하고, harness-audit 점수 ≥ 80으로 다음 phase(실 운영 직전)의 품질 baseline을 확정한다.
**Depends on:** Phase 4, 5, 6 (에이전트 + 오케스트레이터 + 위키 모두 필요)
**Requirements:** TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. mock asset만 사용한 E2E 파이프라인이 TREND → COMPLETE까지 1회 완주하며, 실 API 호출 비용이 $0이다
  2. `verify_all_dispatched()`가 17 GATE(= 12 GATE + 5 sub-gate) 모두 호출 기록을 확인 후 COMPLETE 전이를 허용한다
  3. CircuitBreaker 3회 연속 실패 시나리오(의도적 mock fail 주입)에서 실제로 5분 cooldown이 발동되고 재시도가 거부된다
  4. 재생성 루프 3회 초과 시나리오에서 "정지 이미지 + 줌인" Fallback 샷이 렌더되어 파이프라인이 CIRCUIT_OPEN 없이 COMPLETE에 도달한다
  5. `harness-audit` 스킬 실행 결과 점수가 80 이상이며 A급 drift 0건 + SKILL 500줄 초과 0건이 보고서로 출력된다
**Plans:** 7/8 plans executed
- [x] 07-01-PLAN.md — Wave 0 FOUNDATION: tests/phase07/ scaffold + 6 zero-byte fixtures + harness_audit --json-out D-11 extension — ✅ shipped 2026-04-19, studio@3f1fd4f (eca0bfe RED smoke + c6044d3 GREEN scaffold + 8a88cbc RED harness + 3f1fd4f GREEN harness; 27/27 phase07 tests PASS; 809/809 regression preserved; 836/836 combined sweep; harness_audit score 90; conftest.py 93 lines with 6 D-13 independent fixtures; scripts/validate/harness_audit.py 122→284 lines additive; 6 new stdlib helpers; UTF-8 reconfigure for D-22 Windows cp949)
- [x] 07-02-PLAN.md — Wave 1 MOCK ADAPTERS (Kling / Runway / Typecast / ElevenLabs / Shotstack) — ✅ shipped 2026-04-19, studio@9959e69 (10 TDD commits: b99c89d→5de71ad kling + eda1fa9→4aaf359 runway + f32a66e→6a820b0 typecast + 8edc604→e6c9473 elevenlabs + c053d6a→9959e69 shotstack; 32 new W1 unit tests; 868/868 full sweep; D-3 production-safe default + Correction 2 RuntimeError-only enforcement)
- [x] 07-03-PLAN.md — Wave 2 E2E HAPPY PATH + NotebookLM tier 2 offline — ✅ shipped 2026-04-19, studio@38bb829 (3 commits: 73847dd RED E2E + 405febb GREEN E2E 6/6 + 38bb829 GREEN tier-2 6/6; 2 test files 12 tests; TEST-01 SC1 proven: dispatched_count == 13 + final_gate == COMPLETE + fallback_count == 0 + 14 checkpoint files + Korean cp949 round-trip; D-15 tier 2 only proven via reduced NotebookLMFallbackChain; parallel executor with Plan 07-04 — zero file overlap; 894/894 full sweep)
- [x] 07-04-PLAN.md — Wave 2 13 operational gates + verify_all_dispatched + checkpointer atomic — ✅ shipped 2026-04-19, studio@496056f (4 commits: 20cdf47 anchor 13-gate Correction 1 guard + 371ce1e verify_all_dispatched 12→False/13→True + IncompleteDispatch + 85e7e2b GateDependencyUnsatisfied DAG order ASSEMBLY/UPLOAD + 496056f Checkpointer 14 files atomic os.replace + no .tmp residue + resume()==14; 4 test files 31 tests added; triple-lock == 13 / != 17 / != 12 anchors RESEARCH Correction 1; _OPERATIONAL_GATES frozenset + GATE_INSPECTORS cross-validation; parallel executor with Plan 07-03 — zero file overlap; 911/911 full sweep)
- [x] 07-05-PLAN.md — Wave 3 CircuitBreaker 3× fault + 300s cooldown — ✅ shipped 2026-04-19, studio@95801cb (2 commits: 36324a0 test — 3x RuntimeError → OPEN → CircuitBreakerOpenError + Correction 2 anti-regression via split-literal hasattr check; 95801cb test — strict >300s cooldown boundary + HALF_OPEN probe success/failure paths; 2 test files / 14 tests added; stdlib-only determinism via unittest.mock.patch on time.monotonic; parallel executor with Plan 07-06 — zero file overlap; 941/941 full sweep)
- [x] 07-06-PLAN.md — Wave 3 Fallback ken-burns (THUMBNAIL only) + FAILURES append — ✅ shipped 2026-04-19, studio@31ccfb3 (2 commits: cbacaad test — THUMBNAIL 3xFAIL → ken-burns → COMPLETE + Correction 3 AST-based drift guard + 8 tests including target_is_thumbnail_not_assets anchor; 31ccfb3 test — failures.md append-only format with session marker + evidence + semantic feedback + Hook bypass-by-naming lowercase contract + 8 tests including structural fallback.py open('a')/no-open('w') grep; 2 test files / 16 tests added; TEST-04 SC4 proven: fallback_count == 1 + dispatched_count == 13 + ctx.retry_counts[THUMBNAIL] == 3 + no CircuitBreakerOpenError + shotstack.create_ken_burns_clip called exactly once standalone-POST per Correction 3; parallel executor with Plan 07-05 — zero file overlap; 941/941 full sweep)
- [x] 07-07-PLAN.md — Wave 4 harness-audit score ≥ 80 + 8 regex drift 0 + SKILL 500 lines check — ✅ shipped 2026-04-19, studio@d7c3b34 (6 dimension test files + 27 tests; harness_audit score 90; Rule 1 scanner scope fix: a_rank_drift_count 206→0; SKILL ≤500 double-entry; agent_count 33 filesystem invariant; description ≤1024 double-entry)
- [x] 07-08-PLAN.md — Wave 5 phase07_acceptance.py + 07-TRACEABILITY + 07-VALIDATION flip + 07-SUMMARY — ✅ shipped 2026-04-19, studio@812660d (5728261 phase07_acceptance.py SC 1-5 aggregator 173 lines + 77cab49 3 gate tests 18 tests total + 812660d 07-VALIDATION flip status=complete/nyquist_compliant=true; 07-TRACEABILITY.md 5-REQ × source × test × SC matrix + 3 Correction anchors + 8-plan table; 986/986 full sweep Phase 4+5+6+7; all 5 SC PASS via phase07_acceptance.py exit 0). **PHASE 7 COMPLETE.**

---

### Phase 8: Remote + Publishing + Production Metadata

**Goal:** GitHub Private 저장소(`kanno321-create/shorts_studio`)에 전체 프로젝트를 push하고 YouTube Data API v3 기반 발행 파이프라인(AI disclosure 자동 ON, 주 3~4편 48시간+ 랜덤 간격, 한국 피크 시간)을 활성화하여 실제 업로드가 가능한 상태로 전환한다. Reused Content 증명 production metadata 첨부로 YPP reject 리스크를 차단한다.
**Depends on:** Phase 7 (통합 테스트 통과 후에만 실 채널 업로드 권한 부여)
**Requirements:** PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, REMOTE-01, REMOTE-02, REMOTE-03
**Success Criteria** (what must be TRUE):
  1. `github.com/kanno321-create/shorts_studio` Private 저장소가 생성되고 `git push -u origin main`이 성공하여 원격 mirror가 존재한다
  2. `naberal_harness v1.0.1`이 submodule 또는 참조 경로(`../../harness/`)로 연결되어 있으며 신규 clone 시 함께 설정 가능하다
  3. publisher 에이전트가 YouTube Data API v3 호출 시 **AI disclosure 토글을 예외 없이 ON으로 강제**하고 Selenium 경로는 존재하지 않는다 (코드 grep 0건)
  4. publish lock이 48시간+ 랜덤 간격을 enforcement 하며 한국 피크 시간(평일 20-23 KST / 주말 12-15 KST) 윈도우 안에서만 업로드가 발동한다
  5. 업로드된 영상 metadata에 production_metadata(script_hash, assets_origin, pipeline_version)가 첨부되어 Reused Content 이의제기 시 증명 자료로 활용 가능하다
  6. 업로드 직후 publisher가 핀 댓글 + end-screen subscribe funnel을 자동 설정한다 (샘플 업로드 1회 실측)
**Plans:** 8/8 plans complete
- [x] 08-01-PLAN.md — Wave 0 FOUNDATION (tests/phase08 scaffold + MockYouTube/MockGitHub + scripts/publisher namespace + CD-02 5-class exceptions) — ✅ shipped 2026-04-19, studio@5fb2d38+501777d+b53d218 (3 atomic commits, 39/39 new tests + 986/986 regression preserved)
- [x] 08-02-PLAN.md — Wave 1 REMOTE (GitHub Private repo create + push main + submodule add) — ✅ shipped 2026-04-19, studio@763cbc1+97a27b3+ad29325 (3 atomic commits, 15/15 new tests — 4 REMOTE-01 + 5 REMOTE-02 + 6 REMOTE-03 + Pitfall 2/10 anchors + 986/986 phase04-07 regression preserved, parallel with 08-03)
- [x] 08-03-PLAN.md — Wave 2 OAUTH (InstalledAppFlow + refresh token) — ✅ shipped 2026-04-19, studio@95022d4+9d04c18+a6db395 (3 atomic commits, 11/11 new tests + 59/59 phase08 preserved)
- [x] 08-04-PLAN.md — Wave 3 LOCK+WINDOW+DISCLOSURE (publish_lock + kst_window + ai_disclosure) — ✅ shipped 2026-04-19, studio@8c2d9bf+dbe0f61+f48ade1+6d06bee+b601e86+a3809ab (6 atomic TDD commits, 41 new tests — 11 publish_lock + 13 kst_weekday + 9 kst_weekend + 9 ANCHOR A + 986/986 phase04-07 regression preserved + 106/106 phase08 isolated + ANCHOR A containsSyntheticMedia=True AST-anchor permanent; parallel boundary with 08-05 preserved)
- [x] 08-05-PLAN.md — Wave 4 METADATA+FUNNEL+UPLOADER (production_metadata + youtube_uploader + pinned comment) — ✅ shipped 2026-04-19, studio@98b4e46+79e38c5+51e5332+8531475+73c5eb3+7cb1caa (6 atomic TDD commits, 42 new tests — 10 schema + 6 HTML comment + 4 pin + 5 ANCHOR B + 11 ANCHOR C + 12 E2E + 986/986 phase04-07 regression preserved + 148/148 phase08 isolated + ANCHOR B captions.insert/endScreen/end_screen_subscribe_cta 0 hits + ANCHOR C selenium/webdriver/playwright 0 imports AST-anchor permanent; Pitfall 5/6/7 corrections applied at body-build boundary)
- [x] 08-06-PLAN.md — Wave 5 SMOKE-GATE (code shipping only — smoke_test.py CLI + test_smoke_cleanup.py MockYouTube coverage) — ✅ shipped 2026-04-19, studio@63464ca+d9509f8 (2 atomic commits, 15 new tests — happy + public/private ValueError + cleanup=False + delete-fail + wait fast-path + wait timeout + plan invariants + --dry-run + --no-cleanup + real-path precondition + 986/986 phase04-07 regression preserved + 163/163 phase08 isolated; real YouTube API execution deferred to orchestrator per user-approved D-11 Option A gate, 대표님 confirmed config/client_secret.json + youtube_token.json in place)
- [x] 08-07-PLAN.md — Wave 6 E2E+REGRESSION (full phase08_acceptance.py + regression sweep) — ✅ shipped 2026-04-19, studio@8b9c790+6656e07+feaa0f3 (acceptance aggregator SC 1-6 + test_phase08_acceptance.py wrapper 8 tests + test_regression_986_green.py 5 tests + test_full_publish_chain_mocked.py 6 tests; Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 177 = 986/986 preserved; Phase 8 169 fast sweep + 19 Wave 6 additions)
- [x] 08-08-PLAN.md — Wave 7 PHASE GATE (TRACEABILITY + VALIDATION flip) — ✅ shipped 2026-04-19, studio@2f8a7c8+<final-flip> (08-TRACEABILITY.md 8-REQ × source × test × SC matrix mirroring Phase 7 format + 3 anchors A/B/C + 2 Pitfall 6/7 corrections + 8-plan audit trail + tests/phase08/test_traceability_matrix.py 23 orphan-guard tests; 08-VALIDATION.md frontmatter status=complete/nyquist_compliant=true/wave_0_complete=true/completed=2026-04-19; 24 rows ✅ green; 6 sign-off checkboxes [x]; Completion Summary appended). **PHASE 8 COMPLETE.**
**UI hint:** no

---

### Phase 9: Documentation + KPI Dashboard + Taste Gate

**Goal:** `docs/ARCHITECTURE.md` + `WORK_HANDOFF.md` + KPI 목표 문서화를 완료하고 월 1회 대표님이 직접 상위 3 / 하위 3 영상을 평가하는 Taste Gate 회로를 가동하여, 자동화 taste filter 0 문제(B-P4)를 구조적으로 방어한다. Phase 10 지속 운영으로 넘어가기 전 인간 감독 체계의 마지막 게이트가 설치된다.
**Depends on:** Phase 8 (실제 발행 가능 상태가 되어야 KPI 측정 및 taste gate 대상 영상이 존재)
**Requirements:** KPI-05, KPI-06
**Success Criteria** (what must be TRUE):
  1. `docs/ARCHITECTURE.md`가 12 GATE state machine + 17 inspector 카테고리 + 3-Tier 위키 구조를 다이어그램과 함께 문서화하여 신규 세션 온보딩이 30분 이내 가능하다
  2. KPI 목표(3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초)가 `wiki/shorts/kpi_log.md` 템플릿에 선언되고 측정 방식이 명시되어 있다
  3. Taste Gate 프로토콜이 문서화되어 있으며 월 1회 대표님이 상위 3 / 하위 3 영상을 평가하는 실제 피드백 폼이 존재한다 (첫 회 dry-run 완료)
  4. Taste Gate 평가 결과가 `FAILURES.md`로 흘러드는 경로가 연결되어 있으며, 다음 월 Producer 입력에 반영될 수 있음이 샘플로 검증된다
**Plans:** 6/6 plans complete
- [x] 09-00-foundation-PLAN.md — Wave 0 FOUNDATION (test scaffolding + conftest fixtures + acceptance RED stub)
- [x] 09-01-architecture-PLAN.md — Wave 1 ARCHITECTURE.md (3 Mermaid diagrams + reading time markers + TL;DR + 12 GATE state + 17 inspector categories + 3-Tier wiki)
- [x] 09-02-kpi-log-PLAN.md — Wave 1 kpi_log.md Hybrid (Part A Target Declaration + Part B Monthly Tracking + YouTube Analytics v2 contract) — KPI-06
- [x] 09-03-taste-gate-docs-PLAN.md — Wave 1 taste_gate_protocol.md + taste_gate_2026-04.md dry-run — KPI-05 docs layer
- [x] 09-04-record-feedback-PLAN.md — Wave 2 scripts/taste_gate/record_feedback.py (parse + D-13 filter + D-12 Hook-safe append) — KPI-05 runtime
- [x] 09-05-e2e-phase-gate-PLAN.md — Wave 3 E2E synthetic dry-run flip + phase09_acceptance ALL_PASS + 09-TRACEABILITY + 09-VALIDATION flip. **PHASE 9 COMPLETE.**

---

### Phase 09.1: Production Engine Wiring (INSERTED)

**Goal:** Phase 5 오케스트레이터의 `NotImplementedError` 3슬롯을 Claude Agent SDK 실 호출로 교체하고, Nano Banana Pro scene adapter + Ken-Burns FFmpeg 로컬 adapter + CharacterRegistry util + `RunwayI2VAdapter.VALID_RATIOS_BY_MODEL` + ElevenLabs `voice_id` 3-tier discovery 를 추가하여 Stage 2→4 (Nano Banana → Runway) 1회 스모크 테스트로 end-to-end 검증한다. 9.1 완료 시 Phase 10 첫 실 콘텐츠 production 진입 준비 완료.
**Requirements:** REQ-091-01, REQ-091-02, REQ-091-03, REQ-091-04, REQ-091-05, REQ-091-06, REQ-091-07
**Depends on:** Phase 9
**Success Criteria** (what must be TRUE):
  1. `shorts_pipeline.py` 의 `_default_producer_invoker` / `_default_supervisor_invoker` / `_default_asset_sourcer` 3 슬롯에서 `NotImplementedError` 가 제거되고 Claude Agent SDK factory 로 교체되어 있다
  2. 4개 신규 adapter (`NanoBananaAdapter` / `KenBurnsLocalAdapter` / `ClaudeAgentProducerInvoker` / `ClaudeAgentSupervisorInvoker`) 가 import 가능하며 `CircuitBreaker` 로 wrap 되어 있다
  3. `shorts_pipeline.py` 는 800 lines 이하 (Pitfall 8 invariant)
  4. `scripts/smoke/phase091_stage2_to_4.py --dry-run` 이 `manifest.json` (`cost_cap_usd=1.0`) 과 placeholder 산출물을 생성하며 exit 0
  5. Hook 3종 (`skip_gates` / `TODO(next-session)` / silent-except) 가 9.1 신규 6 파일에서 0 hits
  6. Korean-first 에러 메시지 — 모든 신규 raise 에 한글 포함
  7. `CharacterRegistry().load().get_reference_path("channel_profile")` 이 실파일로 resolve
**Plans:** 7/7 plans complete

Plans:
- [x] 09.1-00-foundation-PLAN.md — Wave 0 FOUNDATION (17 test RED stubs + conftest + anchor PNG + Wave 0 acceptance banner)
- [x] 09.1-01-nanobanana-adapter-PLAN.md — Wave 1 NanoBananaAdapter (google-genai SDK, SAFETY softening retry) — REQ-091-02
- [x] 09.1-02-character-registry-PLAN.md — Wave 1 CharacterRegistry + CharacterEntry pydantic v2 + seed manifest (channel_profile) — REQ-091-03
- [x] 09.1-03-ken-burns-adapter-PLAN.md — Wave 1 KenBurnsLocalAdapter (ffmpeg subprocess) + Shotstack `create_ken_burns_clip` DeprecationWarning — REQ-091-04
- [x] 09.1-04-runway-ratios-voice-PLAN.md — Wave 1 `VALID_RATIOS_BY_MODEL` + `voice_discovery.py` + ElevenLabs default_voice_id 3-tier — REQ-091-05 + REQ-091-06
- [x] 09.1-05-claude-sdk-invokers-PLAN.md — Wave 2 `invokers.py` (Producer/Supervisor/AGENT.md loader) + `shorts_pipeline.py` wiring (NotImplementedError slots replaced) — REQ-091-01
- [x] 09.1-06-stage2-4-smoke-PLAN.md — Wave 3 `scripts/smoke/phase091_stage2_to_4.py` CLI + $1 cost cap + live run $0.29 + hook hygiene GREEN — REQ-091-07
- [x] 09.1-07-phase-gate-PLAN.md — Wave 4 `phase091_acceptance.py` SC1-7 aggregator + `09.1-TRACEABILITY.md` + VALIDATION flip + ROADMAP + STATE. **PHASE 9.1 COMPLETE.**

### Phase 10: Sustained Operations

**Goal:** 주 3~4편 자동 발행을 지속하면서 **첫 1~2개월은 SKILL patch를 전면 금지**하고 FAILURES/KPI 데이터만 축적하여 D-2 저수지 규율을 실증한다. 월 1회 harness-audit + drift scan + FAILURES batch 리뷰로 A급 drift 0건을 유지하며, Auto Research Loop가 YouTube Analytics 시그널을 NotebookLM RAG에 피드백하여 다음 달 Producer 입력이 데이터 기반으로 갱신되는 학습 회로를 완성한다. 본 phase는 영구 지속되며 종료 시점은 YPP 진입 + 외부 수익 발생이다.
**Depends on:** Phase 9 (KPI 대시보드 + Taste Gate 설치 후 장기 운영 진입)
**Requirements:** FAIL-04, KPI-01, KPI-02, KPI-03, KPI-04, AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04
**Success Criteria** (what must be TRUE):
  1. 첫 1~2개월 운영 기간 중 `SKILL.md` 본문 수정 커밋이 **0건**이며 모든 피드백은 `FAILURES.md` append-only로만 누적된다 (git log grep 검증)
  2. YouTube Analytics 일일 수집 cron이 가동되어 시청자 유지율/CTR/평균 시청 시간 데이터가 `wiki/shorts/kpi_log.md`에 월 1회 자동 집계된다
  3. `session_start.py`가 매 세션 감사 점수를 출력하며 30일 평균 점수가 ≥ 80을 유지한다
  4. `drift_scan.py`가 주 1회 실행되어 `deprecated_patterns.json` 전수 스캔 결과 A급 drift가 **0건**으로 유지된다 (drift 발견 시 다음 작업 phase 차단이 실제 발동)
  5. Auto Research Loop가 월 1회 성공 패턴(상위 3 영상)을 NotebookLM RAG에 업데이트하고 다음 월 Producer 입력에 KPI 반영이 관찰된다
  6. YouTube 채널 구독자 트래젝토리 + Shorts 뷰 누적이 월별로 기록되어 YPP 진입 궤도(1000구독 + 10M views/년)까지의 진행률이 visible 하다
**Plans:** 8/8 plans complete

- [x] 10-01-skill-patch-counter-PLAN.md — D-2 Lock SKILL patch counter CLI (FAIL-04) — Wave 1
- [x] 10-02-drift-scan-phase-lock-PLAN.md — drift_scan wrapper + deprecated_patterns grade 확장 + STATE.md phase_lock (AUDIT-03, AUDIT-04) — Wave 1
- [x] 10-03-youtube-analytics-fetch-PLAN.md — YouTube Analytics v2 daily fetch + monthly_aggregate + oauth scope 확장 (KPI-01, KPI-02) — Wave 2
- [x] 10-04-scheduler-hybrid-PLAN.md — 4 GH Actions workflows + Windows Task Scheduler ps1 + notify_failure (Scheduler all) — Wave 2
- [x] 10-05-session-audit-rolling-PLAN.md — session_audit_rollup 30-day rolling (AUDIT-01) — Wave 3
- [x] 10-06-research-loop-notebooklm-PLAN.md — monthly research loop + NotebookLM subprocess + 3-tier fallback (KPI-03, KPI-04) — Wave 3
- [x] 10-07-ypp-trajectory-PLAN.md — YPP trajectory scaffold + 3-milestone gate appender (SC#6 structural) — Wave 3
- [x] 10-08-rollback-docs-PLAN.md — ROLLBACK.md 3 시나리오 runbook + stop_scheduler CLI (FAIL-04 지원) — Wave 4

---

### Phase 11: Pipeline Real-Run Activation + Script Quality Mode

**Goal:** v1.0.1 milestone 의 구조 완결 상태에서 **실 운영 작동 확보** + **대본 품질 옵션 확정**. 세션 #28 대표님 smoke test 2026-04-21 에서 발견된 5 에러 chain (D10-PIPELINE-DEF-01: relative import / .env auto-load 부재 / Shotstack eager instantiation / claude CLI invoker argv 불일치) 을 해결하여 Full pipeline end-to-end real-run 을 가동한다. 첫 실 영상 1편 발행 + 대표님 품질 평가를 근거로 D10-SCRIPT-DEF-01 대본 NLM-direct 재설계 (옵션 A/B/C) 를 확정한다. D10-01-DEF-02 skill_patch_counter idempotency 결함을 2026-05-20 첫 월간 scheduler 실행 전 해결한다. 본 phase 완결 시 대표님의 Core Value (외부 수익) 경로가 실제로 열림.
**Depends on:** Phase 10 (구조 완결 + v1.0.1 audit PASSED)
**Requirements:** PIPELINE-01, PIPELINE-02, PIPELINE-03, PIPELINE-04, SCRIPT-01, AUDIT-05
**Success Criteria** (what must be TRUE):
  1. Full pipeline end-to-end smoke (1 session, GATE 0→13) 실 Claude CLI + 실 외부 API 호출로 완주 — no mock invoker
  2. 영상 1편 실 발행 (YouTube Shorts 업로드 완료) + 대표님 품질 평가 → D10-SCRIPT-DEF-01 옵션 (A 현 시스템 유지 / B NLM 2-step 재설계 / C Shorts/Longform 2-mode 분리) 확정
  3. `scripts/audit/skill_patch_counter.py` idempotency — 동일 git state 에서 2회 연속 실행 시 첫 회만 FAILURES.md append, 2회차는 skip. Regression test `test_idempotency_skip_existing` GREEN
  4. `shorts_pipeline.py` 또는 orchestrator `__init__` 에 `load_dotenv()` 통합으로 `.env` 자동 로드 — PowerShell 추가 env 주입 없이 더블클릭 wrapper 로 실행 가능
  5. `run_pipeline.ps1` 또는 `.bat` wrapper 생성 — 관리자 권한 불필요, `.env` 자동 로드 + `--session-id $(Get-Date -Format yyyyMMdd_HHmmss)` 자동 주입 + pause (창 안 꺼짐)
  6. (선택) Phase 04/08 retrospective VERIFICATION.md 작성 — Phase 04 (33 agent filesystem invariant) + Phase 08 (smoke upload 2 evidence) 증거 체인 공식화
**Plans:** 5/6 plans executed

- [x] 11-01-invoker-stdin-fix-PLAN.md — _invoke_claude_cli stdin piping (PIPELINE-01) — Wave 1
- [x] 11-02-dotenv-loader-PLAN.md — zero-dep .env loader at package __init__ (PIPELINE-02) — Wave 1
- [x] 11-03-adapter-graceful-degrade-PLAN.md — 7 adapter uniform wrap via _try_adapter helper + argparse --session-id optional (PIPELINE-03 + PIPELINE-04 tie-in) — Wave 1
- [x] 11-04-wrapper-cmd-ps1-PLAN.md — run_pipeline.cmd + run_pipeline.ps1 double-click wrapper (PIPELINE-04) — Wave 2
- [x] 11-05-idempotency-counter-PLAN.md — skill_patch_counter commit-hash-set idempotency (AUDIT-05, D-22 2026-05-20 deadline) — Wave 2
- [ ] 11-06-full-smoke-script-decision-PLAN.md — Full 0→13 GATE live smoke + SCRIPT_QUALITY_DECISION.md template + REQUIREMENTS.md D-19 amendment (PIPELINE-01 SC#1 validation + SCRIPT-01 SC#2) — Wave 3

---

### Phase 12: Agent Standardization + Skill Routing + FAILURES Protocol

**Goal:** Phase 11 라이브 smoke 1차 실패 (trend-collector JSON 미준수, F-D2-EXCEPTION-01) 에서 노출된 하네스 품질 gap 해소. 30명 에이전트 (13 producer + 17 inspector) AGENT.md 전수 표준화 + Agent × Skill 매핑 매트릭스 (wiki/agent_skill_matrix.md) 작성 + FAILURES.md 500줄 상한 rotation 정책 + `<mandatory_reads>` 블록으로 각 에이전트가 본인 업무 관련 FAILURES entry 전수 읽기 (샘플링 금지 — 대표님 session #29 지시). 본 phase 완결 시 에이전트 재호출 루프 / 출력 형식 drift / 도구 오용 3대 고질 해소 예상.
**Depends on:** Phase 11 (라이브 smoke 완결 + SCRIPT-01 verdict locked)
**Requirements:** AGENT-STD-01, AGENT-STD-02, SKILL-ROUTE-01, FAIL-PROTO-01, FAIL-PROTO-02
**Success Criteria:**
  1. 13 producer + 17 inspector 전체 AGENT.md 가 표준 schema 준수 (`<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>` 5섹션)
  2. `wiki/agent_skill_matrix.md` 생성 — 30 × 8 매트릭스 (에이전트 × 스킬)
  3. FAILURES.md 500줄 상한 enforcement — 초과 시 `.claude/failures/_archive/YYYY-MM.md` 자동 이관; 현행 버전은 에이전트가 전수 읽기 가능한 크기 유지
  4. `<mandatory_reads>` 블록이 모든 AGENT.md 의 첫 블록에 존재 — FAILURES.md + channel_bible + 해당 에이전트 관련 스킬 참조
  5. Phase 11 에서 실패했던 trend-collector JSON 미준수 패턴 재현 불가 (regression test 추가)
  6. skill_patch_counter 는 Phase 12 의 30+ 파일 patch 를 "directive-authorized batch" 로 단일 F-D2-EXCEPTION-02 entry 처리 (중복 기록 없음 — Phase 11 AUDIT-05 idempotency 활용)
**Plans:** TBD — /gsd:discuss-phase 12 이후 확정

- [ ] 12-XX-agent-md-standard-schema-PLAN.md — 표준 5섹션 schema + template
- [ ] 12-XX-producer-13-migration-PLAN.md — 13 producer AGENT.md 전수 전환
- [ ] 12-XX-inspector-17-migration-PLAN.md — 17 inspector AGENT.md 전수 전환
- [ ] 12-XX-skill-matrix-PLAN.md — wiki/agent_skill_matrix.md + validation
- [ ] 12-XX-failures-rotation-PLAN.md — FAILURES.md 500줄 rotation + _archive/
- [ ] 12-XX-mandatory-reads-enforcement-PLAN.md — AGENT.md `<mandatory_reads>` 블록 + regression test

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold | N/A | ✅ Completed | 2026-04-18 (session #10) |
| 2. Domain Definition | 6/6 | ✅ Complete | 2026-04-19 |
| 3. Harvest | 9/9 | ✅ Complete | 2026-04-19 |
| 4. Agent Team Design | 10/10 | Complete    | 2026-04-18 |
| 5. Orchestrator v2 | 10/10 | ✅ Complete | 2026-04-19 |
| 6. Wiki + NotebookLM + FAILURES | 11/11 | ✅ Complete | 2026-04-19 |
| 7. Integration Test | 8/8 | ✅ Complete | 2026-04-19 |
| 8. Remote + Publishing | 8/8 | Complete    | 2026-04-19 |
| 9. Docs + KPI + Taste Gate | 6/6 | ✅ Complete | 2026-04-20 |
| 9.1. Production Engine Wiring | 7/7 | ✅ Complete | 2026-04-20 |
| 10. Sustained Operations | 8/8 | Complete    | 2026-04-20 |
| 11. Pipeline Real-Run Activation | 5/6 | In Progress|  |
| 12. Agent Standardization | 0/6 | 📋 Planned | - |

---

## Coverage Summary

| Category | Count | Phase Distribution |
|----------|------:|--------------------|
| INFRA | 4 | Phase 1 (3) + Phase 2 (1) |
| HARVEST | 8 | Phase 3 (8) |
| AGENT | 9 | Phase 3 (1: AGENT-06) + Phase 4 (8) |
| RUB | 6 | Phase 4 (6) |
| ORCH | 12 | Phase 5 (12) |
| WIKI | 6 | Phase 6 (6) |
| CONTENT | 7 | Phase 4 (7) |
| VIDEO | 5 | Phase 5 (5) |
| AUDIO | 4 | Phase 4 (4) |
| SUBT | 3 | Phase 4 (3) |
| PUB | 5 | Phase 8 (5) |
| COMPLY | 6 | Phase 4 (6) |
| FAIL | 4 | Phase 6 (3) + Phase 10 (1: FAIL-04) |
| KPI | 6 | Phase 9 (2: KPI-05/06) + Phase 10 (4: KPI-01~04) |
| TEST | 4 | Phase 7 (4) |
| AUDIT | 4 | Phase 10 (4) |
| REMOTE | 3 | Phase 8 (3) |
| **v1 Total** | **96** | **96/96 mapped (100%)** |
| PIPELINE (Phase 11) | 4 | Phase 11 (4) |
| SCRIPT (Phase 11) | 1 | Phase 11 (1) |
| AUDIT-05 (Phase 11 ext.) | 1 | Phase 11 (1) |
| AGENT-STD (Phase 12) | 2 | Phase 12 (2) |
| SKILL-ROUTE (Phase 12) | 1 | Phase 12 (1) |
| FAIL-PROTO (Phase 12) | 2 | Phase 12 (2) |
| **Phase 11+12 Total** | **11** | **11/11 mapped** |
| **Grand Total (v1 + Phase 11 + 12)** | **107** | **107/107 mapped (100%)** |

---

## Critical Success Factors (from SUMMARY §10)

1. **Phase 3 Harvest를 건너뛰지 말 것** — CONFLICT_MAP 39 전수 확인 없이 Phase 4 Agent 설계 진입 시 drift 재발
2. **Phase 4 rubric JSON Schema 동시 정의** — 나중 추가 = 커플링 깨짐
3. **Phase 6 NotebookLM Fallback Chain 필수** — RAG 단독 의존 = 운영 중단 리스크
4. **Phase 10 첫 1~2개월 SKILL patch 전면 금지** — D-2 저수지 규율 실증, 학습 충돌 방지

---

## Hard Constraints (불변)

- `skip_gates=True` 및 `TODO(next-session)`은 pre_tool_use Hook으로 **물리 차단됨** — 회피 수단 존재하지 않음
- 모든 SKILL.md ≤ 500줄, description ≤ 1024자, 에이전트 총합 **32명** (Producer 14 + Inspector 17 + Supervisor 1, Phase 4 Plan 10 canonical per REQUIREMENTS AGENT-01~05; 원안 "12~20" amended 2026-04-19)
- 오케스트레이터 500~800줄 (5166줄 드리프트 재발 금지)
- 32 inspector 전수 이식 금지 (AF-10) — 17 inspector 6 카테고리 통합만
- `shorts_naberal` 원본 수정 금지 — Harvest는 읽기만 허용
- 영상 T2V 금지 (NotebookLM T1) — I2V + Anchor Frame only
- K-pop 트렌드 음원 직접 사용 금지 (AF-13) — KOMCA + Content ID 위험
- Selenium 업로드 영구 금지 (AF-8) — YouTube Data API v3 공식만

---

*Generated 2026-04-19 by gsd-roadmapper based on PROJECT.md + REQUIREMENTS.md (96 v1 REQ) + research/SUMMARY.md §10 Build Order + DOMAIN_CHECKLIST 10-phase skeleton*
