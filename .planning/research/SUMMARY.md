# Research Synthesis — naberal-shorts-studio

**Synthesized:** 2026-04-19
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md, NOTEBOOKLM_RAW.md (52 inline Gemini citations)
**Consumer:** REQUIREMENTS.md (next) + ROADMAP.md (Phase 1~10)
**Through-line:** shorts_naberal의 39 drift conflict (A:13 / B:16 / C:10) **재발 차단**이 모든 결정의 1차 기준.

---

## 1. Executive TL;DR

naberal-shorts-studio는 **naberal_harness v1.0.1 Layer 1을 상속**하여 한국어 YouTube Shorts를 주 3~4편 자율 제작·발행하는 첫 Layer 2 도메인 스튜디오다. 차별점은 **세 가지의 구조적 결합**: (1) state machine 오케스트레이터 500~800줄로 5166줄 + skip_gates 우회를 물리 차단, (2) 32 inspector 과포화를 17 inspector 6 카테고리로 통합 + LogicQA Main-Q/Sub-Qs 다수결로 PASS/FAIL 모순 제거, (3) NotebookLM RAG로 source-grounded 환각 방지 + Producer-Reviewer 이중 생성으로 단일 패스 품질 한계 돌파. **Core risk = 2026-01 YouTube Inauthentic Content 집행 물결(16 채널 47억 뷰 termination)**, defense = **Producer-Reviewer + 3중 방어선(Hook/Dispatcher/Audit) + T2V 금지·I2V 강제**. **YPP 진입 궤도(1000구독 + 10M Shorts views/년)는 운영 시작 후 3~6개월 minimum** — 이 기간 SKILL 패치 없이 데이터 수집만 하는 D-2 저수지 규율이 핵심.

---

## 2. Stack — Locked Choices

| 계층 | 선택 | 근거 |
|------|------|------|
| **Orchestration** | Claude Agent SDK (Python) on **naberal_harness v1.0.1** | STACK §1, ARCHITECTURE §1.1 — 검증 완료, 대체 비용 0 |
| **LLM Producer** | **Claude Sonnet 4.6** (`claude-sonnet-4-6-20260301`) | STACK §1 — 한국어 창작 1위 |
| **LLM Reviewer** | **Claude Opus 4.6** (`claude-opus-4-6-20260320`) — critical gate만 | STACK §1, ARCHITECTURE §6.4 — 비대칭 비용 통제 |
| **Visual primary** | **Kling 2.6 Pro** (9:16, 한국인 얼굴 우위, $0.07~0.14/sec) | STACK §1 |
| **Visual backup** | **Runway Gen-3 Alpha Turbo** ($0.05/sec) | STACK §1 |
| **영상 모드** | **I2V only — T2V 금지** (Anchor Frame 강제) | NOTEBOOKLM T1 |
| **클립 길이** | **4~8초 / 1 Move Rule** | NOTEBOOKLM T2 |
| **TTS primary** | **Typecast** (한국어 감정·존댓말 자연성 1위) | STACK §1 |
| **TTS fallback** | **ElevenLabs Multilingual v3** | STACK §1 |
| **자막 정렬** | **WhisperX + `kresnik/wav2vec2-large-xlsr-korean`** | STACK §1, TS-11, D-P3 |
| **썸네일** | **Nano Banana Pro (Gemini 3 Pro Image)** — 한국어 94~96% | STACK §1 |
| **영상 조립** | **Remotion v4** (Claude Code Skills 네이티브) | STACK §1 |
| **컬러 그레이딩** | **Shotstack** (프로그래매틱 일괄 색보정) | NOTEBOOKLM T14 |
| **음성/영상 합성** | **완전 분리 후 타임스탬프 매핑** | NOTEBOOKLM T3 |
| **렌더** | **Low-Res First (720p) → AI 업스케일** | NOTEBOOKLM T4 |
| **RAG** | **NotebookLM 스킬** (2-노트북 분리) | STACK §1, ARCHITECTURE §5.3 |
| **업로드** | **YouTube Data API v3 공식만** (Selenium 영구 금지) | STACK §1, AF-8 |

**월 운영비 표준: ~$128/월** (Sonnet $12 + Opus $9 + Kling $86.4 + Typecast $20 + Nano Banana $0.64)
**비용 방어:** Circuit Breaker 3회 실패 → 5분 cooldown + 월 예산 120% PostToolUse 차단 + Kling→Runway→인간 fallback

---

## 3. Feature Scope — v1 Must-Haves (12 Table Stakes)

| ID | 한 줄 | Complexity | Phase 차단 |
|----|------|------------|-----------|
| **TS-1** | 9:16 / 1080×1920 / ≤59s | XS | Phase 3 Harvest |
| **TS-2** | **3초 한국어 hook** — 질문형 + 숫자/고유명사 (NotebookLM 3-2) | S | Phase 4 ins-narrative-quality |
| **TS-3** | 한국어 자막 burn-in (24~32pt, 1~4 단어, 중앙) | S | Phase 4 ins-readability |
| **TS-4** | **하이브리드 오디오** (트렌딩 3~5초 → royalty-free crossfade) | S | Phase 4 audio agent (NotebookLM 3-3) |
| **TS-5** | 커스텀 썸네일 (1~2 한글 글자, 하단 30% 회피) | XS | Phase 7 |
| **TS-6** | 한국어 + 로마자 메타데이터 SEO | S | Phase 7 metadata-seo |
| **TS-7** | 주 3~4편 / 48시간+ 랜덤 / 한국 피크 시간 | XS | Phase 5 publish lock |
| **TS-8** | AI disclosure 토글 자동 ON | XS | Phase 8 publisher |
| **TS-9** | 한국 법 compliance (명예훼손/아동복지법/공소제기 전 보도규제) + voice-clone 금지 | M | Phase 4 ins-platform-policy |
| **TS-10** | **Inauthentic Content 방어** (3 템플릿 변주 + Human signal) | M | Phase 5 GATE 유사도 검사 |
| **TS-11** | WhisperX word-level + **한국어 화법 검사기** (NotebookLM T10) | S | Phase 4 ins-korean-naturalness |
| **TS-12** | Duo dialogue (탐정+조수) — 채널 정체성 | S | Phase 4 scripter |

**NotebookLM refinement:** TS-2 (한국어 3초 hook), TS-4 (하이브리드 오디오), TS-9 (voice-clone 자동검출 대응), TS-11 (존댓말/반말 강제 교정)

---

## 4. Feature Scope — v1 Differentiators (9)

| ID | 차별점 | v1 등급 |
|----|--------|---------|
| **DF-1** | 채널 바이블 강제 일관성 | v1 mandatory |
| **DF-2 ★** | **NotebookLM RAG 기반 episode별 research manifest** | **v1 critical** |
| **DF-3 ★** | **Producer-Reviewer 이중 생성 + rubric structured JSON** | **v1 critical** |
| **DF-4** | YouTube Analytics → Producer 입력 (KPI loop) | v1.5 |
| **DF-5** | Twelve Labs Marengo 시맨틱 B-roll | v1.5 실험 |
| **DF-6 ★** | **한국어 grammar + 존댓말 일관성 inspector** | **v1 critical** |
| **DF-7** | Hook/CTA A/B 변주 시드 테스트 | v2 deferral |
| **DF-8** | (DF-6에 통합) | - |
| **DF-9** | 핀 댓글 + end-screen subscribe funnel | v1 mandatory |

**★ = v1 MUST. DF-2/DF-3/DF-6는 REQUIREMENTS에서 critical 명시.**

---

## 5. Anti-Features — DO NOT BUILD (15)

| ID | 1줄 사유 |
|----|----------|
| **AF-1** 일 5편+ 양산 | 2025-07 Inauthentic 직격 |
| **AF-2** 미끼 클릭베이트 | theqoo/FMKorea 시간 단위 망신 |
| **AF-3** TikTok/IG 비-적응 cross-post | 양 플랫폼 모두 손실 |
| **AF-4** **실존 인물 voice cloning** | 2026 likeness 자동 검출 + 형사 책임 |
| **AF-5** 실존 피해자 AI 얼굴 | 트라우마 착취 |
| **AF-6** **AI narration over stock footage** | YouTube 명시 프로토타입 |
| **AF-7** 본문 대부분 템플릿 동일 | "intro/outro만 동일" OK, 본문 위반 |
| **AF-8** Selenium 업로드 | ToS ban 위험 |
| **AF-9** 타 채널 reused | Reused Content demonetization |
| **AF-10** **32 inspector 전수 이식** | Anthropic sweet spot × 6 초과 |
| **AF-11** 일일 업로드 | retention > volume |
| **AF-12** en/ja 자동 번역 멀티마켓 | v1 한국 전용 |
| **AF-13** K-pop 트렌드 음원 | Content ID + KOMCA strike |
| **AF-14** **`skip_gates=True` / `TODO(next-session)`** | A-5/A-6 직접 원인 |
| **AF-15** Community Tab v1 성장 의존 | 500구독 unlock |

---

## 6. Architecture — The 3-Layer Defense Pattern

### Layer 1 — Harness (읽기 전용)
- **Hook (`pre_tool_use.py`)**: deprecated_patterns.json regex — `skip_gates=True`, `TODO(next-session)`, `except: pass`, `segments[]`, `@shorts-researcher`, `Kling.*[Pp]rimary`, `mascot:`, `탐정님`
- **Dispatcher (`gate-dispatcher` 스킬)**: GATE 미통과 시 진입 차단
- **Audit (`harness-audit`, `session_start.py`)**: 점수 < 80 경고

### Layer 2 — Orchestrator State Machine (500~800줄)
12 GATE: `IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE`
- Python enum + transitions, 텍스트 체크리스트 **전면 폐기 (D-7)**
- `GateGuard.dispatch(gate, verdict)` 강제 — Reviewer FAIL raise
- `verify_all_dispatched()` = COMPLETE 진입 조건
- Checkpoint `state/{session_id}/gate_{n}.json`
- CircuitBreaker 3회 → 5분
- **DAG 의존성 그래프** (NotebookLM T16)

### Layer 3 — Audit (월 1회 + 매 세션)
- SKILL ≤ 500줄, description 1024자, agent 12~20 검증
- FAILURES 30일 집계 → 패턴 ≥ 3회 → `.candidate.md` → 7일 staged rollout

---

## 7. Agent Team — 17 Inspectors in 6 Categories

**Producers (sequential):** trend-collector, niche-classifier, researcher(NLM), **director**, **scene-planner**, **shot-planner** (NotebookLM T6 3단 분리), scripter + script-polisher, voice-producer (감정 스타일 동적 T13), asset-sourcer, assembler (Shotstack T14), thumbnail-designer, metadata-seo, publisher

**Reviewers — 17 inspectors / 6 categories (Fan-out, rubric-based):**

- **Structural (3):** `ins-blueprint-compliance`, `ins-timing-consistency`, `ins-schema-integrity`
- **Content (3):** `ins-factcheck`, `ins-narrative-quality`, `ins-korean-naturalness`
- **Style (3):** `ins-tone-brand` (Continuity Bible Prefix T12), `ins-readability`, `ins-thumbnail-hook`
- **Compliance (3):** `ins-license` (unique ≥80% 단일 기준 A-4 해결), `ins-platform-policy`, `ins-safety`
- **Technical (3):** `ins-audio-quality`, `ins-render-integrity`, `ins-subtitle-alignment`
- **Media (2):** `ins-mosaic`, `ins-gore`

**Reviewer 패턴:**
- O/X 평가만, 창작 금지 (NotebookLM T6)
- **시맨틱 그래디언트 피드백** (T7) — "팔이 녹아내림" 같은 자연어 → Producer 프롬프트에 주입
- **LogicQA Main-Q + Sub-Qs 다수결** (T15) — 1 inspector가 메인 + 5 파생 평가
- 별도 context (GAN 분리)
- maxTurns 표준 3, 예외: factcheck 10 / tone-brand 5 / regex 1

**Supervisor (1):** shorts-supervisor — 재귀 위임 금지 (1 depth)
**Harvest (Phase 3 only):** harvest-importer

---

## 8. Top 10 Critical Pitfalls (Blocker)

| # | Pitfall | Phase 차단 | 참조 |
|---|---------|-----------|------|
| 1 | **C-P2 TODO(next-session) 미연결** | Phase 4/5 (Hook + state machine) | **A-5** |
| 2 | **A-P1 Inauthentic Content** | Phase 4/5/8 (3 템플릿 변주 + Human signal) | 2026-01 16 채널 termination |
| 3 | **C-P3 skip_gates=True** | Phase 5 (파라미터 제거 + regex) | **A-6** |
| 4 | **C-P1 32 inspector 과포화** | Phase 4 (17 + rubric) | **A-4, B-7, B-14** |
| 5 | **C-P4 Researcher/Scripter 진입점 충돌** | Phase 4/5 | **A-3** |
| 6 | **A-P3 AI disclosure 누락** | Phase 8 publisher 자동 토글 | 2026 demonetize |
| 7 | **D-P2 한국 방송사·뉴스 무단** | Phase 4/5 (실사 뉴스 금지 + ins-mosaic) | KOMCA + 방송사 |
| 8 | **E-P2 Reused content 증명 실패** | Phase 8 production metadata | YPP 2026 reject |
| 9 | **C-P7 Harvest contamination** | Phase 2/3 (blacklist + 39 전수 확인) | **39 전체** |
| 10 | **B-P4 Over-automation taste filter 0** | Phase 6/9 (D-2 저수지 + 월 taste gate) | 자가 검증 한계 |

**추가:** B-P3 voice cloning real people (AF-4), D-P1 KOMCA 음악.

---

## 9. Korean Market Specifics (Non-Negotiable)

| 항목 | 규칙 |
|------|------|
| **시장** | 87.1% 한국 short-form = YouTube Shorts (v1 단일 플랫폼 정당화) |
| **3초 hook** | **질문형 + 숫자/고유명사** ("왜 [이 사람]은 사라졌을까?", "1997년 서울 23세 여대생") — Western 번역 금지 |
| **존댓말/반말** | 혼용 = AI tell 즉시 감지 (한국 sensitivity 영어권 2배) |
| **NLP 검증** | WhisperX + kresnik + ins-korean-naturalness (regex + LLM 강제 교정) |
| **하이브리드 오디오** | 트렌딩 3~5초 → royalty-free crossfade (T11) |
| **저작권** | KOMCA 130만+ 곡 + 방송사 즉시 이의신청 (한국 fair use 좁음) |
| **법 landmine** | 명예훼손/아동복지법/공소제기 전 보도규제 |
| **피크 시간** | 평일 20-23 KST, 주말 12-15 KST |
| **fact-check** | DC/theqoo/FMKorea 시간 단위 → DF-2 grounded research = 평판 방어 |
| **duo dialogue** | 탐정(하오체) + 조수(해요체) — 채널 정체성 |
| **문화 sensitivity** | 지역/세대/정치/젠더 — ins-cultural-sensitivity |
| **TTS 1위** | Typecast (한국 토종) |

---

## 10. Build Order Implications for Roadmap

### Phase 1 — Scaffold (반나절)
harness pull + new_domain.py + Hook 3종 자동 설치 → 즉시 deprecated_patterns 차단

### Phase 2 — Domain Definition (반나절)
CLAUDE.md {{TODO}} 치환, DOMAIN_CHECKLIST 1~2, **scope 결정** (A-P5 Shorts Fund 오해, E-P4 RPM 보수값 $0.20/1K KR, C-P7 Harvest scope)

### Phase 3 — Harvest (1~2일) ⭐ **AGENT 설계 전 반드시**
- `.preserved/harvested/` 읽기 전용 복사 (theme_bible_raw, hc_checks_raw, FAILURES_history, remotion_src_raw)
- **Tier 3 lockdown** (chmod -w)
- **Harvest blacklist**: orchestrate.py:1239-1291 skip_gates 블록 절대 import 금지
- **CONFLICT_MAP 39 전수 확인**

### Phase 4 — Agent Team Design (3~5일) ⭐ **rubric 동시 정의**
- 17 inspector + Producer/Supervisor
- **rubric JSON Schema 동시 정의** (나중 추가 = 커플링 깨짐)
- description 템플릿 강제 (1024/100자)
- SKILL ≤ 500줄 + MUST REMEMBER 끝 배치
- Producer 3단 분리 (Director/ScenePlan/ShotPlan)
- **차단:** C-P1, C-P4, C-P5, C-P6, A-P4, B-P1, B-P2, B-P3, D-P3, D-P4

### Phase 5 — Orchestrator v2 Write (2~3일)
- `shorts_pipeline.py` 500~800줄
- ShortsStateMachine + GateGuard + CircuitBreaker + Checkpointer
- **`skip_gates` 파라미터 자체 제거**
- DAG 의존성 그래프 (T16) + 영상/음성 분리 합성 (T3) + Low-Res First (T4)
- publish lock 48h+ + 한국 피크 시간
- **차단:** C-P2, C-P3, A-P2, A-P1 유사도, B-P5

### Phase 6 — 3-Tier Wiki + NotebookLM (2~3일)
- Tier 2 합성 + 2-노트북 세팅 (일반/채널바이블)
- **NotebookLM fallback chain 필수** (RAG → grep → hardcoded)
- **Continuity Bible Prefix 자동 주입** (T12)
- FAILURES append-only + SKILL_HISTORY/
- **차단:** C-P8, B-P4 부분

### Phase 7 — Integration Test (1~2일)
- mock asset E2E (실 API 비용 회피)
- verify_all_dispatched() 통과 + harness-audit ≥ 80

### Phase 8 — Remote + Git (반나절)
- github.com/kanno321-create/shorts_studio push
- AI disclosure 자동 토글 + production metadata 첨부
- **차단:** A-P3, E-P2

### Phase 9 — Docs 마감 (반나절)
- ARCHITECTURE, WORK_HANDOFF
- KPI dashboard (3초 retention > 60%, 완주율 > 40%, 평균 시청 > 25초)
- Taste gate 월 1회 (대표님 상위 3 / 하위 3)
- **차단:** E-P1, B-P4, E-P3

### Phase 10 — 지속 운영 ⭐ **첫 달 데이터 수집만**
- 주 3~4편 자동 발행
- **첫 1~2개월 SKILL patch 금지** (D-2 저수지)
- 월 1회 harness-audit + FAILURES batch → `.candidate.md` → 7일 staged
- Auto Research Loop (T17) — YouTube Analytics → RAG 업데이트
- **차단:** C-P2/C-P3/C-P5 전수 검증

**총 2~3주 집중 (Phase 1~9), Phase 10 영구 운영**

**Critical Success Factors:**
1. Phase 3 Harvest 건너뛰지 말기
2. Phase 4 rubric 동시 정의
3. Phase 6 NotebookLM fallback 필수
4. **Phase 10 첫 달 데이터 수집만, SKILL patch 금지**

---

## 11. Cost & Timeline Reality

| 항목 | 수치 |
|------|------|
| **월 운영비 표준** | **~$128/월** |
| **MVP 최소** | ~$63/월 |
| **프리미엄** | ~$222/월 |
| **Build time** | **2~3주 집중** |
| **YPP timeline** | **3~6개월 minimum** (10M views/년, KR RPM ~$0.20/1K ≈ $2K/년) |
| **재시도율** | 20% (Producer-Reviewer 포함) |

**Non-negotiable defenses:**
- Circuit Breaker 3회 → 5분
- 월 예산 120% PostToolUse 차단
- **재생성 루프 3회 hardcoded** → FAILURES 저수지 → "정지 이미지 + 줌인" Fallback (T8)
- Kling → Runway → 인간 fallback (무한 재시도 금지)

**D-9 재확인:** Core Value = YPP 진입 궤도 (수익 숫자 아님) — 알고리즘 신뢰 축적 1차. Shorts Fund 2023 종료, pool 45%, RPM 롱폼 대비 10~20%. Phase 11+ longform_hive v2 재검토.

---

## 12. Open Questions (Phase별 deferred)

| Question | Defer to |
|----------|----------|
| 기존 채널 현황 (구독/히스토리/니치) | Phase 3 Harvest |
| WhisperX + kresnik 실측 정확도 | Phase 4 |
| NotebookLM 프로그래매틱 API + rate limits | Phase 6 |
| KOMCA whitelist + AI 음악 정책 | Phase 5 |
| Runway vs Kling 한국 사용자 실측 | Phase 4 |
| transitions 라이브러리 vs 수동 | Phase 5 |
| 17 inspector 총 비용 (Fan-out) | Phase 5 calibration |
| YouTube Analytics 일일 한도 + cron | Phase 10 |
| Shotstack vs Remotion-only 색보정 | Phase 5 |

---

## 13. Key Decision Confirmations (D-1 ~ D-10 with Refinement)

| D# | Decision | 검증 | Refinement |
|----|----------|------|------------|
| **D-1** | 3-Tier 위키 | ✓ | **Continuity Bible Prefix 자동 주입** 추가 |
| **D-2** | FAILURES 저수지 + 월 batch | ✓ | **첫 1~2개월 SKILL patch 금지** 명시 |
| **D-3 ★** | Producer-Reviewer | ✓ Refined | **3단 Producer 분리 + VQQA 시맨틱 그래디언트** (T6, T7) |
| **D-4** | NotebookLM = Tier 2 RAG | ✓ | **2-노트북 분리 + fallback chain** |
| **D-5** | SKILL 버저닝 + Staged | ✓ | 7일 candidate |
| **D-6** | 3중 방어선 | ✓ | deprecated_patterns.json 7+ regex 명시 |
| **D-7 ★** | state machine | ✓ Refined | **DAG 의존성 그래프 추가** (T16) |
| **D-8** | Harvest, not Fork | ✓ | CONFLICT_MAP 39 전수 + blacklist |
| **D-9** | Core Value = YPP 궤도 | ✓ | 3~6개월 minimum + retention KPI |
| **D-10** | 주 3~4편 | ✓ | 48h+ 랜덤 + 한국 피크 시간 |

**★ = research가 정밀화한 refined decisions (D-3, D-7)**

---

## 14. References

### Source files (`.planning/research/`)
- STACK.md — 12 core technologies, $128/월 표준
- FEATURES.md — 12 TS / 9 DF / 15 AF
- ARCHITECTURE.md — 17 inspectors, 12 GATE state machine, 3-Tier wiki
- PITFALLS.md — 28 pitfalls (10 Blocker) / 5 categories / CONFLICT_MAP cross-refs
- NOTEBOOKLM_RAW.md — **52 inline Gemini citations** + 17 novel techniques

### NotebookLM 17 Novel Techniques (Integration Map)

| ID | 기법 | 적용 |
|----|------|------|
| T1 | T2V → I2V + Anchor Frame | §2, Phase 4 shot-planner |
| T2 | 1 Move Rule + 4~8초 | §2, Phase 4 prompt |
| T3 | 영상/음성 완전 분리 | §2, Phase 5 |
| T4 | Low-Res First + 업스케일 | §2, Phase 5 render |
| T5 | Transition Shots | Phase 4 storyboard |
| T6 | Director/ScenePlan/ShotPlan 3단 | §7, Phase 4 |
| T7 | VQQA 시맨틱 그래디언트 | §7, Phase 4 rubric |
| T8 | 3회 → FAILURES → Fallback 샷 | Phase 5 |
| T9 | High-Signal 마이크로 틈새 | Phase 2 |
| T10 | 한국어 화법 검사기 | §9, Phase 4 |
| T11 | 하이브리드 오디오 | §3 TS-4, Phase 4 |
| T12 | Continuity Bible Prefix | §6 D-1, Phase 6 |
| T13 | 감정 스타일 동적 | Phase 4 voice |
| T14 | Shotstack 일괄 색보정 | §2, Phase 5 |
| T15 | LogicQA Main-Q + Sub-Qs 다수결 | §7, Phase 4 |
| T16 | DAG 의존성 그래프 | §6 D-7, Phase 5 |
| T17 | Auto Research Loop | Phase 10 |

### Predecessor evidence
- shorts_naberal CONFLICT_MAP.md — 39 incidents (A:13/B:16/C:10) — through-line
- shorts_naberal RESEARCH_REPORT.md — FilmAgent/Mind-of-Director 89% 일치

### Architecture
- naberal_harness v1.0.1 — Hook 3, Skills 5, CLI 4
- Anthropic "Building Effective Agents" — 6 patterns + Evaluator-Optimizer
- FilmAgent (arXiv 2501.12909), Mind-of-Director (arXiv 2603.14790), Omniagent (OpenReview 2025)
- Liu et al. 2023 "Lost in the Middle"

---

## Synthesis Confidence

**Overall: HIGH**

| 영역 | 확신 | 사유 |
|------|------|------|
| Stack 주요 선택 | HIGH | naberal_harness 검증 + Anthropic 공식 |
| Stack 가격 | MEDIUM | 연 2~3회 개정 |
| Features (12 TS) | HIGH (9), MEDIUM (3) | shorts_naberal 실측 근거 |
| Architecture 패턴 | HIGH | FilmAgent/MoD/Omniagent 89% 일치 |
| NotebookLM API 통합 | MEDIUM | 프로그래매틱 API 미확인 (browser 자동화만) |
| Pitfalls | HIGH | CONFLICT_MAP 39 직접 증거 |
| YPP 타임라인 | MEDIUM | 채널 현황 미파악 |

---

## Next Step

**SUMMARY 승인 완료 → Requirements 정의 진입.**

REQUIREMENTS.md는 이 SUMMARY + PROJECT.md의 Active 10개 REQ를 기반으로, 각 REQ를 REQ-ID 카테고리별로 세분화 + v1/v2 스코핑 + traceability 섹션 초기화.

Roadmap은 그 다음 Phase 1~10 GSD 매핑 (DOMAIN_CHECKLIST 10단계와 1:1 대응).
