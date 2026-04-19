# Requirements — naberal-shorts-studio

**Version:** v1 (창업)
**Last updated:** 2026-04-19 (Phase Traceability finalized by gsd-roadmapper)
**Derived from:** PROJECT.md (10 Active), research/SUMMARY.md (14 sections), NotebookLM (17 novel techniques)

---

## v1 Requirements

### INFRA — 하네스 상속 + 디렉토리 구조

- [ ] **INFRA-01**: `naberal_harness v1.0.1`을 `new_domain.py shorts`로 상속 완료 (Phase 1 완료 상태 확인)
- [x] **INFRA-02**: 3-Tier 위키 디렉토리 물리 생성
  - Tier 1: `naberal_harness/wiki/` (STRUCTURE.md schema bump 필요)
  - Tier 2: `studios/shorts/wiki/`
  - Tier 3: `studios/shorts/.preserved/harvested/`
- [ ] **INFRA-03**: Hook 3종(`pre_tool_use`, `post_tool_use`, `session_start`) 활성화 검증 + `settings.json` 적용
- [ ] **INFRA-04**: 공용 5 스킬(progressive-disclosure, drift-detection, gate-dispatcher, context-compressor, harness-audit) 상속 확인

### HARVEST — shorts_naberal 자산 이관 (Phase 3 전용)

- [x] **HARVEST-01**: `theme-bible` 전체를 `.preserved/harvested/theme_bible_raw/`로 복사 (읽기 전용) — ✅ 2026-04-19 (studio@fba21e4, 7 channel bibles byte-identical; path remapped from prose `.claude/theme-bible/` to actual `.claude/channel_bibles/` per path_manifest.json; diff_verifier mismatches=[])
- [x] **HARVEST-02**: Remotion `src/` 렌더 코드를 `.preserved/harvested/remotion_src_raw/`로 복사 — ✅ 2026-04-19 (studio@4bc7ece, 40 files / 0.161 MB, node_modules excluded)
- [x] **HARVEST-03**: `hc_checks` 작동 검증된 유틸을 `.preserved/harvested/hc_checks_raw/`로 복사
- [x] **HARVEST-04**: `FAILURES.md` 과거 학습 자산을 `.claude/failures/_imported_from_shorts_naberal.md`로 통합
- [x] **HARVEST-05**: Runway / Kling / ElevenLabs / Typecast API wrapper를 `.preserved/harvested/api_wrappers_raw/`로 복사 ✅ 2026-04-19 studio@aeac16b (5/5 byte-identical: elevenlabs_alignment.py + tts_generate.py + _kling_i2v_batch.py + runway_client.py + heygen_client.py)
- [x] **HARVEST-06**: `.preserved/harvested/` 전체를 `chmod -w` 잠금 (물리 immutable)
- [x] **HARVEST-07**: **Harvest Blacklist** — `orchestrate.py:1239-1291 skip_gates 블록` import 절대 금지 — ✅ 2026-04-19 (studio@c14ab95, 7-check blacklist grep audit across `.preserved/harvested/**` all 0 matches: skip_gates=0, TODO(next-session)=0, orchestrate.py=0, create-shorts SKILL.md=0, create-video=0, longform top-dir=0, selenium imports=0)
- [x] **HARVEST-08**: CONFLICT_MAP 39건 전수 확인 후 `HARVEST_DECISIONS.md` 기록 (A/B/C 등급별 승계·폐기 판단) — ✅ 2026-04-19 (studio@15b827f, 03-HARVEST_DECISIONS.md 39 rows: A:13 verbatim + B:16 + C:10 via 5-rule algorithm; verdict dist 승계=2/폐기=15/통합-재작성=20/cleanup=2; rule dist for B/C rule1=10/rule2=2/rule3=0/rule4=2/rule5=12)

### AGENT — 12~20명 통합 설계

- [x] **AGENT-01**: Producer 에이전트 6개 배포 (trend-collector, niche-classifier, researcher, scripter, script-polisher, metadata-seo) — ✅ 04-08 (studio@8bcf052 Producer Core 6 AGENT.md)
- [x] **AGENT-02**: Producer 3단 분리 — **director** / **scene-planner** / **shot-planner** (NotebookLM T6) — ✅ 04-08 (studio@d1f4ade 3단 분리 3 AGENT.md)
- [x] **AGENT-03**: Producer 지원 5개 (voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher) — ✅ 04-09 (studio@7b089d8 5 Producer Support AGENT.md)
- [x] **AGENT-04**: Inspector 17명 / 6 카테고리 배포
  - Structural (3): `ins-blueprint-compliance`, `ins-timing-consistency`, `ins-schema-integrity`
  - Content (3): `ins-factcheck`, `ins-narrative-quality`, `ins-korean-naturalness`
  - Style (3): `ins-tone-brand`, `ins-readability`, `ins-thumbnail-hook`
  - Compliance (3): `ins-license`, `ins-platform-policy`, `ins-safety`
  - Technical (3): `ins-audio-quality`, `ins-render-integrity`, `ins-subtitle-alignment`
  - Media (2): `ins-mosaic`, `ins-gore`
- [x] **AGENT-05**: Supervisor(`shorts-supervisor`) 1명 — 재귀 위임 금지(1 depth) — ✅ 04-09 (studio@1497c94 shorts-supervisor AGENT.md + _delegation_depth guard)
- [x] **AGENT-06**: Harvest-importer (Phase 3 only)
- [x] **AGENT-07**: 모든 SKILL.md ≤ 500줄 검증 (harness-audit) — ✅ 04-01 (scripts/validate/validate_all_agents.py check_line_count)
- [x] **AGENT-08**: 모든 에이전트 description에 트리거 키워드 명시 (≤1024자) — ✅ 04-01 (check_description_chars + check_description_triggers)
- [x] **AGENT-09**: MUST REMEMBER 지시를 프롬프트 끝에 재배치 (RoPE 모델 Lost in the Middle 대응) — ✅ 04-01 (check_must_remember_position ratio_from_end ≤ 0.4)

### RUB — Reviewer Rubric 설계

- [x] **RUB-01**: LogicQA 패턴 — Main-Q + 5 Sub-Qs 다수결 (NotebookLM T15)
- [x] **RUB-02**: Reviewer는 O/X 평가만, 창작 금지 (NotebookLM T6)
- [x] **RUB-03**: **시맨틱 그래디언트 피드백 (VQQA)** — "팔이 녹아내림" 같은 자연어 → Producer 프롬프트 주입 (T7) — ✅ 04-01 (vqqa_corpus.md 5 VQQA samples) + 04-08 (Producer prompts `<prior_vqqa>` input block for retry loop)
- [x] **RUB-04**: rubric JSON Schema를 AGENT 설계와 **동시 정의** (나중 추가 = 커플링 깨짐) — ✅ 04-01 (.claude/agents/_shared/rubric-schema.json draft-07 + supervisor-rubric-schema.json)
- [x] **RUB-05**: maxTurns 표준 3 (예외: factcheck 10 / tone-brand 5 / regex 1)
- [x] **RUB-06**: 각 inspector는 별도 context (GAN 분리)

### ORCH — 오케스트레이터 v2

- [ ] **ORCH-01**: `scripts/orchestrator/shorts_pipeline.py` 작성 — **500~800줄 state machine**
- [x] **ORCH-02**: 12 GATE 구현: `IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE`
- [x] **ORCH-03**: `GateGuard.dispatch(gate, verdict)` 강제 — Reviewer FAIL 시 raise
- [x] **ORCH-04**: `verify_all_dispatched()` = COMPLETE 진입 조건
- [x] **ORCH-05**: Checkpointer — `state/{session_id}/gate_{n}.json`
- [x] **ORCH-06**: CircuitBreaker — 3회 실패 → 5분 cooldown
- [x] **ORCH-07**: **DAG 의존성 그래프** — 선행 GATE 미통과 시 후속 실행 차단 (NotebookLM T16)
- [x] **ORCH-08**: **`skip_gates` 파라미터 물리 제거** (존재 자체 금지) + regex 차단 (`pre_tool_use`)
- [x] **ORCH-09**: **TODO(next-session) 물리 차단** (`pre_tool_use` regex)
- [ ] **ORCH-10**: 영상/음성 완전 분리 합성 (NotebookLM T3) — Typecast 먼저 → 타임스탬프 매핑 → Shotstack 합성
- [ ] **ORCH-11**: Low-Res First 렌더 (720p) → AI 업스케일 (T4)
- [ ] **ORCH-12**: 재생성 루프 3회 hardcoded → FAILURES 저수지 → "정지 이미지 + 줌인" Fallback (T8)

### WIKI — 지식 시스템 + NotebookLM RAG

- [ ] **WIKI-01**: Tier 2 `studios/shorts/wiki/` — 도메인 특화 노드 (알고리즘/YPP/렌더/KPI) Obsidian 그래프
- [ ] **WIKI-02**: **Continuity Bible** (색상 팔레트, 카메라 렌즈, 시각적 스타일) — 모든 API 호출 시 Prefix 자동 주입 (NotebookLM T12)
- [ ] **WIKI-03**: NotebookLM 2-노트북 세팅
  - 일반 (shorts-production-pipeline-bible 재사용 or 신규)
  - 채널바이블 (Phase 3 Harvest 결과 기반)
- [ ] **WIKI-04**: **NotebookLM Fallback Chain** — RAG 실패 시 → grep wiki → hardcoded defaults
- [ ] **WIKI-05**: 에이전트 프롬프트에서 wiki 노드 참조는 `@wiki/shorts/xxx.md` 형식 고정
- [ ] **WIKI-06**: SKILL.md는 ≤500줄 본문 + 나머지는 wiki 참조 (Lost in the Middle 완화)

### CONTENT — 콘텐츠 기능

- [x] **CONTENT-01**: **3초 한국어 hook** — 질문형 + 숫자/고유명사 패턴 하드코딩 (TS-2, NotebookLM 3-2) — ✅ 04-03 (ins-narrative-quality AGENT.md prompt body hardcodes `?` + `[0-9]{2,}|[가-힣]{2,}` regex in LogicQA q1/q2)
- [x] **CONTENT-02**: Duo dialogue (탐정 하오체 + 조수 해요체) 채널 정체성 — TS-12 — ✅ 04-03 (ins-narrative-quality + ins-korean-naturalness combined; speaker-specific register rules encoded in LogicQA)
- [x] **CONTENT-03**: High-Signal 마이크로 틈새 페르소나 (NotebookLM T9) — ✅ 04-08 (niche-classifier prompts references `.preserved/harvested/theme_bible_raw/<niche>.md` for persona injection; read-only path reference preserves attrib +R lockdown)
- [x] **CONTENT-04**: NotebookLM grounded research manifest per episode (DF-2) — ✅ 04-03 (ins-factcheck maxTurns=10 RUB-05 exception; LogicQA 5 sub_qs covering nlm_source presence, credibility tier, 2-source minimum, numeric accuracy, Fallback chain audit)
- [x] **CONTENT-05**: 9:16 / 1080×1920 / ≤59s 포맷 강제 (TS-1)
- [x] **CONTENT-06**: 한국어 자막 burn-in (24~32pt, 1~4 단어/라인, 중앙) — TS-3
- [x] **CONTENT-07**: 한국어 + 로마자 메타데이터 SEO — TS-6 — ✅ 04-08 (metadata-seo AGENT.md prompt body: 한국어 + 로마자 병기 키워드 생성; studio@8bcf052)

### VIDEO — 영상 생성

- [ ] **VIDEO-01**: **T2V 금지 / I2V only** — Anchor Frame 강제 (NotebookLM T1)
- [ ] **VIDEO-02**: **1 Move Rule** (1 카메라 워킹 + 1 피사체 액션) + 4~8초 클립 (T2)
- [ ] **VIDEO-03**: Transition Shots 삽입 (소품 클로즈업 / 실루엣 / 배경) — T5
- [ ] **VIDEO-04**: Kling 2.6 Pro primary, Runway Gen-3 Alpha Turbo backup
- [ ] **VIDEO-05**: Shotstack 일괄 색보정 + 필터 — T14

### AUDIO — 음성/음악

- [x] **AUDIO-01**: Typecast primary (한국어), ElevenLabs fallback — ✅ 04-09 (voice-producer AGENT.md Typecast primary + ElevenLabs fallback chain; studio@7b089d8)
- [x] **AUDIO-02**: **하이브리드 오디오** — 트렌딩 3~5초 → 무료(royalty-free) crossfade (T11) — ✅ 04-09 (asset-sourcer AGENT.md royalty-free crossfade rule)
- [x] **AUDIO-03**: 감정 스타일 파라미터 동적 설정 (T13) — 콘텐츠 톤앤매너에 맞게 — ✅ 04-09 (voice-producer AGENT.md emotion_style 파라미터 dynamic binding)
- [x] **AUDIO-04**: K-pop 트렌드 음원 직접 사용 금지 (KOMCA + Content ID) — ✅ 04-05 (ins-license AGENT.md K-pop regex bank 19 artists + 19 titles + royalty-free whitelist + AF-13 100% block verified)

### SUBT — 자막

- [x] **SUBT-01**: WhisperX + `kresnik/wav2vec2-large-xlsr-korean` 통합
- [x] **SUBT-02**: 한국어 화법 검사기 — 존댓말/반말 혼용 감지 + 교정 (`ins-korean-naturalness`, T10) — ✅ 04-03 (ins-korean-naturalness AGENT.md full §5.3 regex bank: 하오체/해요체/반말/호칭/외래어; rule_simulator 10/10 FAIL neg + 10/10 PASS pos)
- [x] **SUBT-03**: 타임스탬프 정렬 정확도 ±50ms

### PUB — 발행

- [ ] **PUB-01**: **AI disclosure 토글 자동 ON** — 업로드 시 publisher가 강제 (A-P3 차단)
- [ ] **PUB-02**: YouTube Data API v3 공식 사용 (Selenium 영구 금지 — AF-8)
- [ ] **PUB-03**: 주 3~4편, **48시간+ 랜덤 간격**, 한국 피크 시간 (평일 20-23 / 주말 12-15 KST)
- [ ] **PUB-04**: Production metadata 첨부 (Reused content 증명 — E-P2 차단)
- [ ] **PUB-05**: 핀 댓글 + end-screen subscribe funnel (DF-9)

### COMPLY — 컴플라이언스 + 방어

- [x] **COMPLY-01**: 한국 법 위반 검사 (명예훼손 / 아동복지법 / 공소제기 전 보도규제) — `ins-platform-policy` — ✅ 04-05 (ins-platform-policy AGENT.md regex 명예훼손|아동복지법|공소제기 전 보도|초상권|모욕죄|허위사실|사생활 침해 + 초상권 동의/mosaic/blur 검사)
- [x] **COMPLY-02**: KOMCA + 방송사 저작권 필터 — 실사 뉴스 금지, 인물 mosaic 강제 (`ins-mosaic`)
- [x] **COMPLY-03**: **Inauthentic Content 방어** — 3 템플릿 변주 + Human signal 필수 (A-P1 차단, TS-10) — ✅ 04-05 (ins-platform-policy Inauthentic defense triple: 3 템플릿 변주 + Jaccard<0.7 + Human signal "대표님 얼굴 B-roll" 또는 "human_vo_insert"; production_metadata 4-field enforcement)
- [x] **COMPLY-04**: 실존 인물 voice cloning 금지 (AF-4) — ✅ 04-05 (ins-license af4_voice_clone blocklist via af_bank.json; 11/11 AF-4 FAIL entries 100% blocked; PASS 가상 캐릭터 no false-positive)
- [x] **COMPLY-05**: 실존 피해자 AI 얼굴 금지 (AF-5)
- [x] **COMPLY-06**: 문화 sensitivity 검사 (지역/세대/정치/젠더) — ✅ 04-05 (ins-safety 4-axis blocklist 38+ seed tokens: 지역 8 / 세대 9 / 정치 10 / 젠더 11; narrative-tone self-harm limit; ins-gore role boundary documented)

### FAIL — FAILURES 저수지 + 학습

- [ ] **FAIL-01**: `FAILURES.md` append-only (즉시 SKILL 수정 금지) — D-2 저수지 원칙
- [ ] **FAIL-02**: 30일 집계 → 패턴 ≥ 3회 → `SKILL.md.candidate` → 7일 staged rollout → 승격
- [ ] **FAIL-03**: `SKILL_HISTORY/` 디렉토리 — SKILL 수정 시 기존 버전 `v{n}.md.bak` 백업
- [ ] **FAIL-04**: **Phase 10 첫 1~2개월 SKILL patch 전면 금지** — 데이터 수집만

### KPI — 성과 지표 + 피드백 루프

- [ ] **KPI-01**: YouTube Analytics 일일 수집 cron (시청자 유지율 / CTR / 평균 시청 시간)
- [ ] **KPI-02**: 월 1회 `wiki/shorts/kpi_log.md` 자동 생성
- [ ] **KPI-03**: Auto Research Loop — 성공 패턴 → NotebookLM RAG 업데이트 (T17)
- [ ] **KPI-04**: 다음 달 Producer 입력에 KPI 반영 (DF-4 기본 틀)
- [ ] **KPI-05**: 월 1회 Taste gate — 대표님이 직접 상위 3 / 하위 3 영상 평가 (B-P4 차단)
- [ ] **KPI-06**: 목표 지표 — 3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초

### TEST — 통합 테스트

- [ ] **TEST-01**: E2E mock asset 파이프라인 1회 성공 (실 API 비용 회피)
- [ ] **TEST-02**: `verify_all_dispatched()` 통과 + 17 GATE 모두 호출 확인
- [ ] **TEST-03**: Circuit Breaker 3회 발동 시나리오 테스트
- [ ] **TEST-04**: Fallback 샷(정지 이미지 + 줌인) 테스트

### AUDIT — 감사

- [ ] **AUDIT-01**: `session_start.py` 매 세션 자동 감사 (점수 ≥ 80)
- [ ] **AUDIT-02**: `harness-audit` 월 1회 통합 감사 (SKILL 500줄, 에이전트 12~20, description 1024자)
- [ ] **AUDIT-03**: `drift_scan.py` 주 1회 `deprecated_patterns.json` 전수 스캔 → A급 drift 0 유지
- [ ] **AUDIT-04**: A급 drift 발견 시 Phase 차단 (다음 작업 불가)

### REMOTE — GitHub 원격 (Phase 8)

- [ ] **REMOTE-01**: GitHub Private 저장소 생성 — `kanno321-create/shorts_studio`
- [ ] **REMOTE-02**: `git remote add origin` + `git push -u origin main`
- [ ] **REMOTE-03**: naberal_harness v1.0.1을 submodule or 참조로 연결 (경로: `../../harness/`)

---

## v2 Requirements (Deferred)

v1 검증 완료 후 또는 수익 발생 후 활성화.

- [ ] **DEF-01**: 일 5편+ 양산 모델 (현재 주 3~4편 → 수익 검증 후 재평가)
- [ ] **DEF-02**: YouTube Analytics 완전 KPI feedback loop 고도화 (DF-4)
- [ ] **DEF-03**: Twelve Labs Marengo 시맨틱 B-roll (DF-5)
- [ ] **DEF-04**: Hook/CTA A/B 변주 시드 테스트 (DF-7)
- [ ] **DEF-05**: 멀티 플랫폼 확장 (TikTok/Instagram 적응 cross-post)
- [ ] **DEF-06**: 멀티 언어 자동 번역 (영문/일문 등)
- [ ] **DEF-07**: Long-form 영상 스튜디오 (별도 longform_hive 프로젝트)
- [ ] **DEF-08**: 신규 채널 0구독 초기 성장 전략 (현재는 기존 채널 활용)
- [ ] **DEF-09**: 대안 수익원 (쿠팡파트너스 / 블로그 유입 / 브랜드 딜)
- [ ] **DEF-10**: Community Tab 성장 funnel 활성화 (500구독 unlock 이후)

---

## Out of Scope (Anti-Features — DO NOT BUILD)

**전부 명시적 금지**. 각 AF는 `deprecated_patterns.json` 또는 `ins-*` 에이전트 규칙으로 강제.

- **AF-1** 일 5편+ 양산 — 2025-07 Inauthentic 집행 직격 위험
- **AF-2** 미끼 클릭베이트 — theqoo/FMKorea 시간 단위 망신, 채널 reputation 파괴
- **AF-3** TikTok/IG 비-적응 cross-post — 양 플랫폼 모두 알고리즘 패널티
- **AF-4** 실존 인물 voice cloning — 2026 likeness 자동 검출 + 형사 책임
- **AF-5** 실존 피해자 AI 얼굴 — 트라우마 착취 윤리 위반
- **AF-6** AI narration over stock footage — YouTube Inauthentic 명시 프로토타입
- **AF-7** 본문 대부분 템플릿 동일 — intro/outro만 동일 OK, 본문은 위반
- **AF-8** Selenium 업로드 — YouTube ToS 위반, 채널 ban 위험
- **AF-9** 타 채널 reused content — Reused Content demonetization
- **AF-10** 32 inspector 전수 이식 — Anthropic sweet spot × 6 초과
- **AF-11** 일일 업로드 — retention > volume (알고리즘 선호 정반대)
- **AF-12** en/ja 자동 번역 멀티마켓 — v1 한국 전용 집중
- **AF-13** K-pop 트렌드 음원 직접 사용 — Content ID + KOMCA strike
- **AF-14** `skip_gates=True` / `TODO(next-session)` — A-5/A-6 직접 원인, 물리 차단
- **AF-15** Community Tab v1 성장 의존 — 500구독 unlock 전제 조건

---

## Requirement Counts

| Category | Count |
|----------|------:|
| INFRA | 4 |
| HARVEST | 8 |
| AGENT | 9 |
| RUB | 6 |
| ORCH | 12 |
| WIKI | 6 |
| CONTENT | 7 |
| VIDEO | 5 |
| AUDIO | 4 |
| SUBT | 3 |
| PUB | 5 |
| COMPLY | 6 |
| FAIL | 4 |
| KPI | 6 |
| TEST | 4 |
| AUDIT | 4 |
| REMOTE | 3 |
| **v1 총계** | **96 requirements** |
| v2 deferred | 10 |
| Out of Scope (AF) | 15 |

---

## Phase Traceability

**Finalized by gsd-roadmapper on 2026-04-19. 96/96 v1 REQ mapped (100% coverage, no orphans).**

### Phase → REQ-IDs (Forward mapping)

| Phase | REQ-IDs | Count |
|-------|---------|------:|
| **Phase 1: Scaffold** ✅ | INFRA-01, INFRA-03, INFRA-04 | 3 |
| **Phase 2: Domain Definition** | INFRA-02 | 1 |
| **Phase 3: Harvest** | HARVEST-01, HARVEST-02, HARVEST-03, HARVEST-04, HARVEST-05, HARVEST-06, HARVEST-07, HARVEST-08, AGENT-06 | 9 |
| **Phase 4: Agent Team Design** | AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-07, AGENT-08, AGENT-09, RUB-01, RUB-02, RUB-03, RUB-04, RUB-05, RUB-06, CONTENT-01, CONTENT-02, CONTENT-03, CONTENT-04, CONTENT-05, CONTENT-06, CONTENT-07, AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04, SUBT-01, SUBT-02, SUBT-03, COMPLY-01, COMPLY-02, COMPLY-03, COMPLY-04, COMPLY-05, COMPLY-06 | 34 |
| **Phase 5: Orchestrator v2** | ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, ORCH-08, ORCH-09, ORCH-10, ORCH-11, ORCH-12, VIDEO-01, VIDEO-02, VIDEO-03, VIDEO-04, VIDEO-05 | 17 |
| **Phase 6: Wiki + NotebookLM + FAILURES** | WIKI-01, WIKI-02, WIKI-03, WIKI-04, WIKI-05, WIKI-06, FAIL-01, FAIL-02, FAIL-03 | 9 |
| **Phase 7: Integration Test** | TEST-01, TEST-02, TEST-03, TEST-04 | 4 |
| **Phase 8: Remote + Publishing** | PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, REMOTE-01, REMOTE-02, REMOTE-03 | 8 |
| **Phase 9: Docs + KPI + Taste Gate** | KPI-05, KPI-06 | 2 |
| **Phase 10: Sustained Operations** | FAIL-04, KPI-01, KPI-02, KPI-03, KPI-04, AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04 | 9 |
| **Total** | | **96** |

### REQ → Phase (Reverse mapping for quick lookup)

| REQ-ID | Phase | REQ-ID | Phase |
|--------|-------|--------|-------|
| INFRA-01 | 1 | RUB-01 | 4 |
| INFRA-02 | 2 | RUB-02 | 4 |
| INFRA-03 | 1 | RUB-03 | 4 |
| INFRA-04 | 1 | RUB-04 | 4 |
| HARVEST-01 | 3 | RUB-05 | 4 |
| HARVEST-02 | 3 | RUB-06 | 4 |
| HARVEST-03 | 3 | ORCH-01 | 5 |
| HARVEST-04 | 3 | ORCH-02 | 5 |
| HARVEST-05 | 3 | ORCH-03 | 5 |
| HARVEST-06 | 3 | ORCH-04 | 5 |
| HARVEST-07 | 3 | ORCH-05 | 5 |
| HARVEST-08 | 3 | ORCH-06 | 5 |
| AGENT-01 | 4 | ORCH-07 | 5 |
| AGENT-02 | 4 | ORCH-08 | 5 |
| AGENT-03 | 4 | ORCH-09 | 5 |
| AGENT-04 | 4 | ORCH-10 | 5 |
| AGENT-05 | 4 | ORCH-11 | 5 |
| AGENT-06 | 3 | ORCH-12 | 5 |
| AGENT-07 | 4 | WIKI-01 | 6 |
| AGENT-08 | 4 | WIKI-02 | 6 |
| AGENT-09 | 4 | WIKI-03 | 6 |
| CONTENT-01 | 4 | WIKI-04 | 6 |
| CONTENT-02 | 4 | WIKI-05 | 6 |
| CONTENT-03 | 4 | WIKI-06 | 6 |
| CONTENT-04 | 4 | VIDEO-01 | 5 |
| CONTENT-05 | 4 | VIDEO-02 | 5 |
| CONTENT-06 | 4 | VIDEO-03 | 5 |
| CONTENT-07 | 4 | VIDEO-04 | 5 |
| AUDIO-01 | 4 | VIDEO-05 | 5 |
| AUDIO-02 | 4 | SUBT-01 | 4 |
| AUDIO-03 | 4 | SUBT-02 | 4 |
| AUDIO-04 | 4 | SUBT-03 | 4 |
| COMPLY-01 | 4 | PUB-01 | 8 |
| COMPLY-02 | 4 | PUB-02 | 8 |
| COMPLY-03 | 4 | PUB-03 | 8 |
| COMPLY-04 | 4 | PUB-04 | 8 |
| COMPLY-05 | 4 | PUB-05 | 8 |
| COMPLY-06 | 4 | REMOTE-01 | 8 |
| FAIL-01 | 6 | REMOTE-02 | 8 |
| FAIL-02 | 6 | REMOTE-03 | 8 |
| FAIL-03 | 6 | TEST-01 | 7 |
| FAIL-04 | 10 | TEST-02 | 7 |
| KPI-01 | 10 | TEST-03 | 7 |
| KPI-02 | 10 | TEST-04 | 7 |
| KPI-03 | 10 | AUDIT-01 | 10 |
| KPI-04 | 10 | AUDIT-02 | 10 |
| KPI-05 | 9 | AUDIT-03 | 10 |
| KPI-06 | 9 | AUDIT-04 | 10 |

**Coverage check:** 96 REQ-IDs → 96 phase assignments (1:1 correspondence, no orphans, no duplicates). ✅

---

## Core Value Validation

이 96개 v1 REQ는 **Core Value = "YouTube 광고 수익 발생 (YPP 진입 궤도)"**와 직접 연결되는지?

- **직접 연결 (수익 가능성 창출)**: CONTENT, VIDEO, AUDIO, SUBT, PUB, COMPLY (36 REQ) — 이게 없으면 영상 자체가 발행 불가
- **간접 연결 (품질/안정성)**: AGENT, RUB, ORCH, WIKI, FAIL, TEST, AUDIT (48 REQ) — 이게 없으면 재시도 비용·drift로 회사 조기 실패
- **기반 연결 (운영 전제)**: INFRA, HARVEST, REMOTE, KPI (21 REQ) — 이게 없으면 시작 불가 or 학습 불가

**확인**: 모든 v1 REQ는 Core Value에 기여. 순수 "nice to have" 없음. Out of Scope 15개가 그 경계선.

---

*Last updated: 2026-04-19 — Phase Traceability finalized by gsd-roadmapper (96/96 REQ mapped, 0 orphans). Previous update: Research 합성 완료 (commit 7a9b16d).*
