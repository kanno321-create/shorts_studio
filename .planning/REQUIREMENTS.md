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

- [x] **ORCH-01**: `scripts/orchestrator/shorts_pipeline.py` 작성 — **500~800줄 state machine**
- [x] **ORCH-02**: 12 GATE 구현: `IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE`
- [x] **ORCH-03**: `GateGuard.dispatch(gate, verdict)` 강제 — Reviewer FAIL 시 raise
- [x] **ORCH-04**: `verify_all_dispatched()` = COMPLETE 진입 조건
- [x] **ORCH-05**: Checkpointer — `state/{session_id}/gate_{n}.json`
- [x] **ORCH-06**: CircuitBreaker — 3회 실패 → 5분 cooldown
- [x] **ORCH-07**: **DAG 의존성 그래프** — 선행 GATE 미통과 시 후속 실행 차단 (NotebookLM T16)
- [x] **ORCH-08**: **`skip_gates` 파라미터 물리 제거** (존재 자체 금지) + regex 차단 (`pre_tool_use`)
- [x] **ORCH-09**: **TODO(next-session) 물리 차단** (`pre_tool_use` regex)
- [x] **ORCH-10**: 영상/음성 완전 분리 합성 (NotebookLM T3) — Typecast 먼저 → 타임스탬프 매핑 → Shotstack 합성
- [x] **ORCH-11**: Low-Res First 렌더 (720p) → AI 업스케일 (T4)
- [x] **ORCH-12**: 재생성 루프 3회 hardcoded → FAILURES 저수지 → "정지 이미지 + 줌인" Fallback (T8)

### WIKI — 지식 시스템 + NotebookLM RAG

- [x] **WIKI-01**: Tier 2 `studios/shorts/wiki/` — 도메인 특화 노드 (알고리즘/YPP/렌더/KPI) Obsidian 그래프
- [x] **WIKI-02**: **Continuity Bible** (색상 팔레트, 카메라 렌즈, 시각적 스타일) — 모든 API 호출 시 Prefix 자동 주입 (NotebookLM T12)
- [x] **WIKI-03**: NotebookLM 2-노트북 세팅
  - 일반 (shorts-production-pipeline-bible 재사용 or 신규)
  - 채널바이블 (Phase 3 Harvest 결과 기반)
- [x] **WIKI-04**: **NotebookLM Fallback Chain** — RAG 실패 시 → grep wiki → hardcoded defaults — Phase 6 Plan 05 Wave 2 FALLBACK CHAIN: scripts/notebooklm/fallback.py 3-tier (RAGBackend Tier 0 reuses query_notebook + GrepWikiBackend Tier 1 keyword intersection on wiki/**/*.md + HardcodedDefaultsBackend Tier 2 never-raises with D-10/D-5 canonical + NotebookLMFallbackChain returns (answer, tier_used)); 18 tests green [15 fallback_chain + 3 fallback_injection]; D-5 fault injection acceptance proven via monkeypatched subprocess rc=1 forcing tier>=1; RuntimeError('all NotebookLM fallback tiers exhausted') literal pinned; 2026-04-19 studio@25993bb
- [x] **WIKI-05**: 에이전트 프롬프트에서 wiki 노드 참조는 `@wiki/shorts/xxx.md` 형식 고정 — Phase 6 Plan 01 Wave 0 FOUNDATION: scripts.wiki.link_validator.validate_all_agent_refs() enforces @wiki/shorts/ prefix + status=ready; 2026-04-19 studio@6690e12
- [x] **WIKI-06**: SKILL.md는 ≤500줄 본문 + 나머지는 wiki 참조 (Lost in the Middle 완화) — Phase 6 Plan 01 Wave 0 FOUNDATION: validator scaffold ready for downstream SKILL line-count audit; 2026-04-19 studio@6690e12

### CONTENT — 콘텐츠 기능

- [x] **CONTENT-01**: **3초 한국어 hook** — 질문형 + 숫자/고유명사 패턴 하드코딩 (TS-2, NotebookLM 3-2) — ✅ 04-03 (ins-narrative-quality AGENT.md prompt body hardcodes `?` + `[0-9]{2,}|[가-힣]{2,}` regex in LogicQA q1/q2)
- [x] **CONTENT-02**: Duo dialogue (탐정 하오체 + 조수 해요체) 채널 정체성 — TS-12 — ✅ 04-03 (ins-narrative-quality + ins-korean-naturalness combined; speaker-specific register rules encoded in LogicQA)
- [x] **CONTENT-03**: High-Signal 마이크로 틈새 페르소나 (NotebookLM T9) — ✅ 04-08 (niche-classifier prompts references `.preserved/harvested/theme_bible_raw/<niche>.md` for persona injection; read-only path reference preserves attrib +R lockdown)
- [x] **CONTENT-04**: NotebookLM grounded research manifest per episode (DF-2) — ✅ 04-03 (ins-factcheck maxTurns=10 RUB-05 exception; LogicQA 5 sub_qs covering nlm_source presence, credibility tier, 2-source minimum, numeric accuracy, Fallback chain audit)
- [x] **CONTENT-05**: 9:16 / 1080×1920 / ≤59s 포맷 강제 (TS-1)
- [x] **CONTENT-06**: 한국어 자막 burn-in (24~32pt, 1~4 단어/라인, 중앙) — TS-3
- [x] **CONTENT-07**: 한국어 + 로마자 메타데이터 SEO — TS-6 — ✅ 04-08 (metadata-seo AGENT.md prompt body: 한국어 + 로마자 병기 키워드 생성; studio@8bcf052)

### VIDEO — 영상 생성

- [x] **VIDEO-01**: **T2V 금지 / I2V only** — Anchor Frame 강제 (NotebookLM T1)
- [x] **VIDEO-02**: **1 Move Rule** (1 카메라 워킹 + 1 피사체 액션) + 4~8초 클립 (T2)
- [x] **VIDEO-03**: Transition Shots 삽입 (소품 클로즈업 / 실루엣 / 배경) — T5
- [x] **VIDEO-04**: Kling 2.6 Pro primary, Runway Gen-3 Alpha Turbo backup
- [x] **VIDEO-05**: Shotstack 일괄 색보정 + 필터 — T14

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

- [x] **PUB-01**: **AI disclosure 토글 자동 ON** — 업로드 시 publisher가 강제 (A-P3 차단)
- [x] **PUB-02**: YouTube Data API v3 공식 사용 (Selenium 영구 금지 — AF-8)
- [x] **PUB-03**: 주 3~4편, **48시간+ 랜덤 간격**, 한국 피크 시간 (평일 20-23 / 주말 12-15 KST)
- [x] **PUB-04**: Production metadata 첨부 (Reused content 증명 — E-P2 차단)
- [x] **PUB-05**: 핀 댓글 + end-screen subscribe funnel (DF-9)

### COMPLY — 컴플라이언스 + 방어

- [x] **COMPLY-01**: 한국 법 위반 검사 (명예훼손 / 아동복지법 / 공소제기 전 보도규제) — `ins-platform-policy` — ✅ 04-05 (ins-platform-policy AGENT.md regex 명예훼손|아동복지법|공소제기 전 보도|초상권|모욕죄|허위사실|사생활 침해 + 초상권 동의/mosaic/blur 검사)
- [x] **COMPLY-02**: KOMCA + 방송사 저작권 필터 — 실사 뉴스 금지, 인물 mosaic 강제 (`ins-mosaic`)
- [x] **COMPLY-03**: **Inauthentic Content 방어** — 3 템플릿 변주 + Human signal 필수 (A-P1 차단, TS-10) — ✅ 04-05 (ins-platform-policy Inauthentic defense triple: 3 템플릿 변주 + Jaccard<0.7 + Human signal "대표님 얼굴 B-roll" 또는 "human_vo_insert"; production_metadata 4-field enforcement)
- [x] **COMPLY-04**: 실존 인물 voice cloning 금지 (AF-4) — ✅ 04-05 (ins-license af4_voice_clone blocklist via af_bank.json; 11/11 AF-4 FAIL entries 100% blocked; PASS 가상 캐릭터 no false-positive)
- [x] **COMPLY-05**: 실존 피해자 AI 얼굴 금지 (AF-5)
- [x] **COMPLY-06**: 문화 sensitivity 검사 (지역/세대/정치/젠더) — ✅ 04-05 (ins-safety 4-axis blocklist 38+ seed tokens: 지역 8 / 세대 9 / 정치 10 / 젠더 11; narrative-tone self-harm limit; ins-gore role boundary documented)

### FAIL — FAILURES 저수지 + 학습

- [x] **FAIL-01**: `FAILURES.md` append-only (즉시 SKILL 수정 금지) — D-2 저수지 원칙 (Phase 6 Plan 08 — studio@88a3ae5: check_failures_append_only Hook helper + 14 unit + 7 subprocess tests + FAILURES.md/FAILURES_INDEX.md seed; basename-exact match; _imported_from_shorts_naberal.md exempt per D-14)
- [x] **FAIL-02**: 30일 집계 → 패턴 ≥ 3회 → `SKILL.md.candidate` → 7일 staged rollout → 승격
- [x] **FAIL-03**: `SKILL_HISTORY/` 디렉토리 — SKILL 수정 시 기존 버전 `v{n}.md.bak` 백업 (Phase 6 Plan 08 — studio@88a3ae5: backup_skill_before_write Hook helper + 9 unit tests + SKILL_HISTORY/README.md convention; v<YYYYMMDD_HHMMSS>.md.bak format; first-time create silent skip; OSError→deny via main)
- [x] **FAIL-04**: **Phase 10 첫 1~2개월 SKILL patch 전면 금지** — 데이터 수집만

### KPI — 성과 지표 + 피드백 루프

- [x] **KPI-01**: YouTube Analytics 일일 수집 cron (시청자 유지율 / CTR / 평균 시청 시간)
- [x] **KPI-02**: 월 1회 `wiki/shorts/kpi_log.md` 자동 생성
- [x] **KPI-03**: Auto Research Loop — 성공 패턴 → NotebookLM RAG 업데이트 (T17)
- [x] **KPI-04**: 다음 달 Producer 입력에 KPI 반영 (DF-4 기본 틀)
- [x] **KPI-05**: 월 1회 Taste gate — 대표님이 직접 상위 3 / 하위 3 영상 평가 (B-P4 차단)
- [x] **KPI-06**: 목표 지표 — 3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초

### TEST — 통합 테스트

- [x] **TEST-01**: E2E mock asset 파이프라인 1회 성공 (실 API 비용 회피)
- [x] **TEST-02**: `verify_all_dispatched()` 통과 + 13 operational gate 모두 호출 확인 (Correction 1: 13, NOT 17) — Plan 07-04 (studio@496056f)
- [x] **TEST-03**: Circuit Breaker 3회 발동 시나리오 테스트 — Plan 07-05 (studio@36324a0 + 95801cb)
- [x] **TEST-04**: Fallback 샷(정지 이미지 + 줌인) 테스트 — Plan 07-06 (studio@cbacaad + 31ccfb3): THUMBNAIL 3×FAIL → ken-burns → COMPLETE + append-only FAILURES + Correction 3 AST anchor + Hook bypass-by-naming

### AUDIT — 감사

- [x] **AUDIT-01**: `session_start.py` 매 세션 자동 감사 (점수 ≥ 80)
- [x] **AUDIT-02**: `harness-audit` 월 1회 통합 감사 (SKILL 500줄, 에이전트 12~20, description 1024자)
- [x] **AUDIT-03**: `drift_scan.py` 주 1회 `deprecated_patterns.json` 전수 스캔 → A급 drift 0 유지
- [x] **AUDIT-04**: A급 drift 발견 시 Phase 차단 (다음 작업 불가)

### REMOTE — GitHub 원격 (Phase 8)

- [x] **REMOTE-01**: GitHub Private 저장소 생성 — `kanno321-create/shorts_studio`
- [x] **REMOTE-02**: `git remote add origin` + `git push -u origin main`
- [x] **REMOTE-03**: naberal_harness v1.0.1을 submodule or 참조로 연결 (경로: `../../harness/`)

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
| Phase 11 (PIPELINE + SCRIPT + AUDIT-05) | 6 |
| Phase 12 (AGENT-STD + SKILL-ROUTE + FAIL-PROTO) | 5 |
| **v1 + Phase 11 + Phase 12 전체** | **107 requirements** |
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

---

## Phase 11 신규 REQ (v1.0.1 → v1.0.2 bridge)

세션 #28 2026-04-21 — v1.0.1 audit PASSED 직후 대표님 smoke test 에서 발견된 D10-PIPELINE-DEF-01 (5 에러 chain) + D10-SCRIPT-DEF-01 (대본 품질 NLM-direct) + D10-01-DEF-02 (skill_patch_counter idempotency) 해결을 위한 Phase 11 신규 6 REQ.

### PIPELINE — Pipeline Real-Run Activation (신규 카테고리)

- [x] **PIPELINE-01**: Full pipeline end-to-end smoke — 1 session GATE 0→13 실 Claude CLI + 실 외부 API 호출 완주. mock invoker 금지. `invokers.py:141` argv/stdin 형식 Claude CLI 2.1.112 호환 수정.
- [x] **PIPELINE-02**: `.env` 자동 로드 — `shorts_pipeline.py` 또는 orchestrator `__init__` 에 `from dotenv import load_dotenv; load_dotenv()` 통합. PowerShell `set -a && source .env` 추가 주입 없이 `py -3.11 -m scripts.orchestrator.shorts_pipeline` 실행 가능.
- [x] **PIPELINE-03**: Adapter graceful degrade 전면 — Kling/Runway/Typecast/ElevenLabs/Shotstack 5개 adapter 모두 Phase 9.1 nanobanana/ken_burns 와 동일한 `try/except + logger.warning + self.X = None` 패턴 적용. 사용 안 하는 adapter 의 env 부재가 `__init__` 을 막지 않음.
- [x] **PIPELINE-04**: 더블클릭 wrapper UX — `run_pipeline.ps1` 또는 `.bat` 작성. `.env` 자동 로드 + `--session-id $(timestamp)` 자동 주입 + pause (창 안 꺼짐). 대표님이 관리자 권한 불필요하게 더블클릭 1회로 실행 가능.

### SCRIPT — 대본 품질 옵션 확정 (신규 카테고리)

- [ ] **SCRIPT-01**: D10-SCRIPT-DEF-01 옵션 확정 — 영상 1편 실 발행 (Option A 베이스라인 산출물) + 대표님 품질 평가를 근거로 옵션 A (현 `scripter` agent 유지) / B (NLM 2-step 호출 모드 재설계, `scripts/notebooklm/query.py` 2-notebook 호출 구조) / C (Shorts/Longform 2-mode 분리, channel_bible.길이 기반 routing) 중 1개 확정. A 선택 시 Phase 11 에서 완료. B/C 선택 시 Phase 12 (NLM 2-Step Scripter Redesign) 에서 구현 후 완료 — Phase 11 verification-gate 는 SCRIPT_QUALITY_DECISION.md 내 verdict letter 확정 + (B/C 시) Phase 12 spawn trigger 로 충족.

### AUDIT 확장

- [x] **AUDIT-05**: skill_patch_counter idempotency — 동일 git state 에서 2회 연속 실행 시 첫 회만 `FAILURES.md` append, 2회차는 기존 entry grep 후 skip. `tests/phase10/test_skill_patch_counter.py` 에 `test_idempotency_skip_existing` 케이스 추가. 2026-05-20 첫 월간 scheduler (Plan 10-04 `skill-patch-count-monthly.yml`) 실행 전 완료 필수.

### Phase 11 Traceability

| REQ-ID | Phase |
|--------|-------|
| PIPELINE-01 | 11 |
| PIPELINE-02 | 11 |
| PIPELINE-03 | 11 |
| PIPELINE-04 | 11 |
| SCRIPT-01 | 11 |
| AUDIT-05 | 11 |

**Phase 11 Coverage**: 6 신규 REQ — v1.0.1 96 REQ 와 합쳐 102 REQ 전체 mapping.

---

*Phase 11 REQ 추가: 2026-04-21 (세션 #28) — D10-PIPELINE-DEF-01 + D10-SCRIPT-DEF-01 + D10-01-DEF-02 deferred items 를 공식 REQ 로 승격. /gsd:discuss-phase 11 + /gsd:plan-phase 11 로 세부 plan 결정 예정.*

---

## Phase 12 신규 REQ (v1.0.2 bridge — Agent Standardization + Skill Routing + FAILURES Protocol)

세션 #29 2026-04-21 — Phase 11 라이브 smoke 1차 실패 (trend-collector JSON 미준수, F-D2-EXCEPTION-01) 에서 노출된 하네스 품질 gap 해소를 위한 Phase 12 신규 5 REQ. **대표님 session #29 직접 승인 ("둘다" — Option D + Phase 12 발의 양쪽 모두).**

### AGENT — 에이전트 표준화 + mandatory reads

- [x] **AGENT-STD-01**: 30명 에이전트 (13 producer + 17 inspector) AGENT.md 표준 5섹션 schema 준수 — `<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>`. Phase 12 에서 표준 template + 전수 migration. Phase 11 에서 노출된 출력 형식 drift / 도구 오용 / 재호출 루프 3대 고질 해소.
- [x] **AGENT-STD-02**: 각 AGENT.md 첫 블록에 `<mandatory_reads>` 명시 — `.claude/failures/FAILURES.md` (500줄 내 전수 읽기, 샘플링 금지 — 대표님 session #29 지시) + `wiki/ypp/channel_bible.md` (관련 niche 매핑) + 해당 에이전트 관련 스킬 (예: gate-dispatcher, progressive-disclosure). 매 호출마다 fresh read 필수 — system prompt 캐시 유무 불문.
- [x] **AGENT-STD-03**: Supervisor invoker (`ClaudeAgentSupervisorInvoker.__call__`) 가 producer_output 을 summary-only 모드로 압축하여 Claude CLI 에 주입 — 현재 full JSON 을 `--append-system-prompt` body 에 dump 해 '프롬프트가 너무 깁니다' (rc=1) 를 유발. 요약 형식: `{gate, verdict, decisions[], error_codes[]}` 만 추출 (verbose prose drop). Phase 11 verification gap closure — 2026-04-21 live smoke 2차 attempt GATE 2 에서 노출된 context limit 한계 해소. **출처**: Phase 11 11-VERIFICATION.md Gap #1 + 대표님 session #29 'a' 응답 (Phase 12 scope expansion 승인).

### SKILL-ROUTE — Agent × Skill 매핑 매트릭스

- [x] **SKILL-ROUTE-01**: `wiki/agent_skill_matrix.md` 생성 — 30 × 6 매트릭스 (에이전트 × 5 공용 skill + 1 additional 컬럼). Row: 13 producer + 17 inspector. Column: progressive-disclosure, gate-dispatcher, drift-detection, context-compressor, harness-audit, additional. 각 cell (공용 5): required / optional / n/a. additional 컬럼: agent-specific skill freeform (예: ins-factcheck "notebooklm-query*"). Pytest validation: `scripts/validate/verify_agent_skill_matrix.py` — 매트릭스 entry 와 실제 AGENT.md `<skills>` 블록 bidirectional reciprocity (`--fail-on-drift`). **Note**: 기존 "8 column" 초안 은 2026-04-21 실측 시 `.claude/skills/` 5 공용 skill dir 만 존재 확인 → RESEARCH §Open Question Q1 Option A 채택 (D-2 Lock 2026-04-20~06-20 기간 신규 SKILL.md 생성 금지 보존; 본 정정은 스코프 조정이며 D-2 Lock 위반 아님). Phase 12 Plan 04 Task 1.

### FAIL-PROTO — FAILURES.md 500줄 rotation + directive-authorized batch

- [x] **FAIL-PROTO-01**: FAILURES.md 500줄 상한 enforcement — 초과 시 `.claude/failures/_archive/YYYY-MM.md` 자동 이관. 현행 version 은 에이전트가 `<mandatory_reads>` 로 전수 읽기 가능한 크기 유지. 이관 스크립트: `scripts/audit/failures_rotate.py`. Hook: `check_failures_append_only` 수정하여 500줄 초과 커밋 차단 + rotation 안내 메시지.
- [x] **FAIL-PROTO-02**: Phase 12 의 30+ 파일 patch 를 skill_patch_counter 가 단일 "directive-authorized batch" entry (F-D2-EXCEPTION-02) 로 처리 — Phase 11 AUDIT-05 idempotency 활용. F-D2-EXCEPTION 계열은 대표님 직접 지시 가정하에 일괄 처리 (단일 FAILURES entry, 중복 기록 없음). Phase 11 F-D2-EXCEPTION-01 (trend-collector) 은 이 정책의 prototype.

### Phase 12 Traceability

| REQ-ID | Phase |
|--------|-------|
| AGENT-STD-01 | 12 |
| AGENT-STD-02 | 12 |
| AGENT-STD-03 | 12 |
| SKILL-ROUTE-01 | 12 |
| FAIL-PROTO-01 | 12 |
| FAIL-PROTO-02 | 12 |

**Phase 12 Coverage**: 6 신규 REQ — v1.0.1 96 REQ + Phase 11 6 REQ + Phase 12 6 REQ = **108 REQ 전체 mapping** (AGENT-STD-03 added 2026-04-21 post-Phase-11 verification gap analysis).

---

## Milestone v1.0.2 신규 REQ (Production Readiness — Live Smoke + Adapter Remediation)

v1.0.2 밀스톤 초기화 — 2026-04-21. Phase 11 `complete_with_deferred` SC#1/SC#2 해소 (Phase 13) + phase05/06/07 pre-existing adapter drift 15 failures 청산 (Phase 14). 대표님 v1.0.2 범위 확정.

### SMOKE — Live Smoke 재도전 (Phase 13)

- [x] **SMOKE-01**: Real Claude CLI producer 호출 1회 성공 — `ClaudeAgentProducerInvoker` 가 실 Anthropic API 경유 producer agent (scripter or director) 1명 이상 호출, JSON 출력 schema 준수 + producer_output 파일 anchor (`.planning/phases/13-*/evidence/`). Phase 11 SC#1 deferred 해소.
- [x] **SMOKE-02**: Real Claude CLI supervisor 호출 1회 성공 — `ClaudeAgentSupervisorInvoker` 가 17 inspector fan-out 시도 후 rubric JSON 반환 (Phase 12 AGENT-STD-03 압축 적용 상태에서 '프롬프트가 너무 깁니다' rc=1 재현 없음). Evidence: supervisor_output.json + inspector_count >= 1.
- [x] **SMOKE-03**: YouTube 과금 환경 smoke 업로드 1회 성공 — `scripts/publisher/smoke_test.py --privacy=unlisted --cleanup` 실 API 경유, video_id 수신 + 업로드 후 자동 삭제 검증. privacy=public 시도 시 ValueError (Phase 8 PUB-04 invariant preserved). Phase 11 SC#2 deferred 해소.
- [x] **SMOKE-04**: production_metadata HTML comment 업로드 description 첨부 + video_id anchor — 4 필수 필드 (script_seed, assets_origin, pipeline_version, checksum) 업로드된 description 에 실제 존재 확인 (YouTube API get videoId readback). evidence 파일 `.planning/phases/13-*/evidence/smoke_upload_YYYYMMDD.json`.
- [x] **SMOKE-05**: Budget cap $5 검증 — smoke run 전 `BUDGET_CAP_USD=5.00` enforcement, run 종료 시 `budget_usage.json` 기록 + 초과 시 RuntimeError. Claude API + YouTube API + Kling/Typecast 등 유료 API 합산. Anthropic token 사용량 포함 (input+output × model unit price).
- [x] **SMOKE-06**: Full pipeline E2E smoke (TREND → COMPLETE) 1회 성공 — 실 API 전체 경유, 모든 13 GATE dispatched, 최종 MP4 생성 + 업로드 + cleanup. Evidence: `smoke_e2e_YYYYMMDD.json` with 13 gate timestamps + final_video_id + total_cost_usd. SMOKE-01~05 의 최종 통합 검증.

### ADAPT — API Adapter Remediation (Phase 14)

- [x] **ADAPT-01**: veo_i2v adapter drift 청산 — 현재 pytest failure N건 (Phase 09.1 era stub→adapter 전환 잔재) 전수 녹색 전환. adapter contract test `tests/adapters/test_veo_i2v_contract.py` 신설, `scripts/api/veo_i2v.py` (존재 시) 또는 단순 non-Kling I2V fallback 검증.
- [x] **ADAPT-02**: elevenlabs adapter drift 청산 — elevenlabs voice generation adapter pytest failure 전수 녹색 전환. contract test `tests/adapters/test_elevenlabs_contract.py`. Typecast primary + ElevenLabs fallback 구조 (voice-producer AGENT.md 참조) 유지.
- [x] **ADAPT-03**: shotstack adapter drift 청산 — shotstack render adapter pytest failure 전수 녹색 전환. contract test `tests/adapters/test_shotstack_contract.py`. Phase 5 ORCH-10 영상/음성 분리 합성 경로 보존.
- [x] **ADAPT-04**: Full phase05/06/07 regression 0 failures — `pytest tests/phase05 tests/phase06 tests/phase07` 전체 green. Phase 7 기준 986/986 (Phase 4 244 + Phase 5 329 + Phase 6 236 + Phase 7 177) regression preserved + 15 adapter failures 제거.
- [x] **ADAPT-05**: Adapter contract 문서 `docs/adapter_contracts.md` (또는 `wiki/render/adapter_contracts.md`) 신설 — 각 adapter (kling / runway / veo_i2v / typecast / elevenlabs / shotstack / whisperx) 의 입력/출력 schema + retry/fallback 규칙 + fault injection 지원 여부 정리. Phase 7 mock adapter 기준 계약과 real adapter 실측 차이 문서화.
- [x] **ADAPT-06**: Drift 재발 방지 — (a) pytest marker `@pytest.mark.adapter_contract` 도입하여 adapter contract test 카테고리 분리, (b) CI/local `pytest -m adapter_contract` 별도 게이트 제공, (c) pre_tool_use hook 또는 validator 로 adapter 파일 수정 시 contract test 자동 요구 (optional, Phase 14 scope 내 trade-off 결정).

### Milestone v1.0.2 Traceability

**Phase → REQ-IDs (Forward mapping)**

| Phase | REQ-IDs | Count |
|-------|---------|------:|
| **Phase 13: Live Smoke 재도전** | SMOKE-01, SMOKE-02, SMOKE-03, SMOKE-04, SMOKE-05, SMOKE-06 | 6 |
| **Phase 14: API Adapter Remediation** | ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04, ADAPT-05, ADAPT-06 | 6 |
| **v1.0.2 Total** | | **12** |

**REQ → Phase (Reverse mapping)**

| REQ-ID | Phase |
|--------|-------|
| SMOKE-01 | 13 |
| SMOKE-02 | 13 |
| SMOKE-03 | 13 |
| SMOKE-04 | 13 |
| SMOKE-05 | 13 |
| SMOKE-06 | 13 |
| ADAPT-01 | 14 |
| ADAPT-02 | 14 |
| ADAPT-03 | 14 |
| ADAPT-04 | 14 |
| ADAPT-05 | 14 |
| ADAPT-06 | 14 |

**v1.0.2 Coverage**: 12 신규 REQ (SMOKE 6 + ADAPT 6, 대표님 multiSelect 확정 2026-04-21). 전체 mapping: v1.0.1 96 REQ + Phase 11 6 REQ + Phase 12 6 REQ + v1.0.2 12 REQ = **120 REQ** (100% mapped, 0 orphans).

---

*Phase 12 REQ 추가: 2026-04-21 (세션 #29) — Phase 11 라이브 smoke 1차 실패로 노출된 하네스 품질 gap 해소. 대표님 직접 승인 (Option D + Phase 12 발의 양쪽 모두). /gsd:discuss-phase 12 + /gsd:plan-phase 12 로 세부 plan 결정 예정.*

*Milestone v1.0.2 REQ 추가: 2026-04-21 — SMOKE 6 + ADAPT 6 (사용자 multiSelect 전체 채택). SMOKE = Phase 11 SC#1/SC#2 deferred 해소 + 실 환경 validation. ADAPT = phase05/06/07 15 failures 청산 + contract 재정의. Research skipped (brownfield remediation). /gsd:plan-phase 13 + 14 로 진행.*

---

## Phase 15 신규 REQ (SYSTEM-PROMPT-COMPRESSION + USER-FEEDBACK-LOOP)

**Phase 13 live smoke 2026-04-22 attempt 에서 노출된 invokers.py → Claude CLI 경로 rc=1 문제** 의 근본 해소 + **대표님 피드백 loop 을 통한 영상 재작업/수정 인터페이스** 구축. Phase 11 SC#1 defer + Phase 12 AGENT-STD-03 compression 의 scope 밖이었던 supervisor AGENT.md body 자체 크기 + 인코딩 문제를 완결.

**대표님 직접 승인 (2026-04-22)**: "어떻게해서든 내가 명령할수있는기능을 만들어야지 그렇지않으면 절대안되... 한동안은 내 피드백을 받으면서 영상을 제작 수정 재재작해야 너가 진짜 퀄리티좋은 영상을 만들수있다."

### SPC — System Prompt Compression (Claude CLI 경로 root cause fix)

- [x] **SPC-01**: `invokers.py _invoke_claude_cli_once` 의 Windows cp949 ↔ UTF-8 인코딩 경로 root cause 진단 + 수정. `subprocess.Popen` 의 `text=True, encoding='utf-8', errors='replace'` 조합이 Korean text in `--append-system-prompt` argument 전달 시 10KB+ 구간에서 rc=1 유발. bash 경로는 동일 body 에 성공 → Python-specific encoding 문제. 수정안: stdin bytes 모드 또는 `encoding='utf-8', errors='strict'` + 명시적 encoding validation.
- [x] **SPC-02**: `shorts-supervisor` AGENT.md body 압축 (Progressive Disclosure) — 10591자 → 6000자 목표. verbose reference 블록을 `references/` 로 분리. 기존 Phase 12 AGENT-STD 검증 (`verify_agent_md_schema.py` 31/31) 재통과 필수.
- [x] **SPC-03**: Producer 14명 AGENT.md 평균 크기 audit — 10000자 초과 시 Progressive Disclosure 강제. 장기 drift 방지를 위해 `verify_agent_md_size.py` 신설 (pytest marker `adapter_contract` 와 유사하게 상한 enforcement).
- [x] **SPC-04**: `--system-prompt-file <path>` 옵션 조사 — Claude CLI 가 system_prompt 를 argument 가 아닌 파일 경로로 받을 수 있는지 확인. 가능 시 argv 크기 제한 회피 부가 방어선.
- [x] **SPC-05**: `invokers.py` contract test 신설 — `tests/adapters/test_invokers_encoding_contract.py`. 10KB+ AGENT.md body + Korean text 전수 통과 검증 (mock subprocess).
- [ ] **SPC-06**: Phase 13 live smoke 재시도 — `phase13_live_smoke.py --live --topic "해외범죄,..." --niche incidents` 실 완주 + 13 gate 전수 dispatched + evidence 5 files anchor. SPC-01~05 완결 이후 empirical 검증.

### UFL — User Feedback Loop (대표님 영상 재작업 인터페이스)

- [x] **UFL-01**: `--revision` flag 추가 — 기존 영상의 script/assets/metadata 중 하나를 대표님 피드백으로 교체 후 특정 gate 부터 재실행. 예: `phase13_live_smoke.py --live --revision-from SCRIPT --feedback "hook 이 약함, 질문형으로 변경"` → SCRIPT gate 부터 재생성, VOICE/ASSETS/ASSEMBLY 등 하류 재실행. ✅ Plan 15-04 (2026-04-21, studio@cbd3c96).
- [x] **UFL-02**: `--revise-script <path>` flag — 대표님이 수동으로 작성한 대본 파일을 주입. scripter 에이전트 skip, script-polisher 에이전트만 실행 후 VOICE gate 부터 정상 pipeline. ✅ Plan 15-04 (2026-04-21, studio@b1ef29a).
- [x] **UFL-03**: 각 gate 의 producer_output 을 대표님이 review + approve/reject 할 수 있는 checkpoint 모드 — `--pause-after <GATE>` flag. 지정 gate 완료 후 pipeline 일시중지, 대표님 signal 대기, 승인 시 재개. ✅ Plan 15-04 (2026-04-21, studio@b42f72d).
- [ ] **UFL-04**: 영상 품질 평가 회로 — 업로드 후 대표님 subjective rating (1-5) 수집 CLI. `scripts/smoke/rate_video.py --video-id <id> --rating 3 --feedback "조명이 어두움"` → `.claude/memory/feedback_video_quality.md` append. 차후 영상 생성 시 이 피드백을 researcher/director 에이전트에 주입.

### Phase 15 Traceability

| REQ-ID | Phase |
|--------|-------|
| SPC-01 | 15 |
| SPC-02 | 15 |
| SPC-03 | 15 |
| SPC-04 | 15 |
| SPC-05 | 15 |
| SPC-06 | 15 |
| UFL-01 | 15 |
| UFL-02 | 15 |
| UFL-03 | 15 |
| UFL-04 | 15 |

**Phase 15 Coverage**: 10 신규 REQ (SPC 6 + UFL 4). 전체 mapping: v1.0.1 96 + Phase 11 6 + Phase 12 6 + v1.0.2 12 + Phase 15 10 = **130 REQ**.

---

*Phase 15 REQ 추가: 2026-04-22 — Phase 13 live smoke 실 재시도에서 노출된 invokers.py encoding 경로 root cause 해소 + 대표님 피드백 loop 인터페이스 구축. 대표님 직접 승인 (Option B 채택, "어떻게해서든 내가 명령할수있는기능을 만들어야지"). /gsd:plan-phase 15 로 진행.*
