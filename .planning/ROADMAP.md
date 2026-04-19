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
- [ ] **Phase 6: Wiki + NotebookLM + FAILURES Reservoir** — Tier 2 합성 + 2-노트북 세팅 + Continuity Bible Prefix + 저수지 패턴
- [ ] **Phase 7: Integration Test** — E2E mock asset + verify_all_dispatched() + harness-audit ≥ 80
- [ ] **Phase 8: Remote + Publishing + Production Metadata** — GitHub push + YouTube API v3 + AI disclosure 자동 ON + Reused content 증명
- [ ] **Phase 9: Documentation + KPI Dashboard + Taste Gate** — KPI 목표 설정 + 월 1회 대표님 taste 평가 회로 가동
- [ ] **Phase 10: Sustained Operations** — 주 3~4편 자동 발행 + 첫 1~2개월 SKILL patch 전면 금지 (D-2 저수지)

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
**Plans:** 11 plans
- [x] 06-01-PLAN.md — Wave 0 FOUNDATION: scripts/wiki/ + tests/phase06/ scaffold + phase06_acceptance.py — ✅ shipped 2026-04-19, studio@6690e12 (15/15 tests green, scripts.wiki imports OK, phase06_acceptance exits 1 gracefully at Wave 0, phase05 regression 329/329 preserved)
- [x] 06-02-PLAN.md — Wave 1 WIKI CONTENT: 5 ready nodes + 5 MOC checkbox flips + 3 test files
- [x] 06-03-PLAN.md — Wave 2 NOTEBOOKLM WRAPPER: scripts/notebooklm/query.py subprocess wrapper (D-6/D-7)
- [x] 06-04-PLAN.md — Wave 2 LIBRARY REGISTRATION: library.json channel-bible entry (D-8) + deferred-items.md
- [ ] 06-05-PLAN.md — Wave 2 FALLBACK CHAIN: 3-tier RAG -> grep -> defaults (D-5)
- [ ] 06-06-PLAN.md — Wave 3 CONTINUITY MODEL: ContinuityPrefix pydantic v2 (D-20) + prefix.json
- [ ] 06-07-PLAN.md — Wave 3 SHOTSTACK INJECTION: filter[0] continuity_prefix + D-17 tail preservation (D-9/D-19)
- [ ] 06-08-PLAN.md — Wave 4 HOOK EXTENSION: FAILURES append-only + SKILL_HISTORY backup (D-11/D-12/D-14) + 2 deprecated_patterns
- [ ] 06-09-PLAN.md — Wave 4 AGGREGATION CLI: 30-day dry-run (D-13)
- [ ] 06-10-PLAN.md — Wave 4 AGENT MASS UPDATE: 15 AGENT.md files + sha256 manifests (D-3/D-18)
- [ ] 06-11-PLAN.md — Wave 5 PHASE GATE: D-14 sha256 + acceptance E2E + 9-REQ traceability + VALIDATION flip

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
**Plans:** TBD

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
**Plans:** TBD
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
**Plans:** TBD

---

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
**Plans:** TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold | N/A | ✅ Completed | 2026-04-18 (session #10) |
| 2. Domain Definition | 6/6 | ✅ Complete | 2026-04-19 |
| 3. Harvest | 9/9 | ✅ Complete | 2026-04-19 |
| 4. Agent Team Design | 10/10 | Complete    | 2026-04-18 |
| 5. Orchestrator v2 | 10/10 | ✅ Complete | 2026-04-19 |
| 6. Wiki + NotebookLM + FAILURES | 3/11 | Executing | - |
| 7. Integration Test | 0/TBD | Not started | - |
| 8. Remote + Publishing | 0/TBD | Not started | - |
| 9. Docs + KPI + Taste Gate | 0/TBD | Not started | - |
| 10. Sustained Operations | 0/TBD | Not started (영구 지속) | - |

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
| **Total** | **96** | **96/96 mapped (100%)** |

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
