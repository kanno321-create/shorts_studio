# Domain Pitfalls — naberal-shorts-studio

**Domain:** AI-automated YouTube Shorts production studio (Korean market, YPP-targeted)
**Researched:** 2026-04-19
**Confidence:** HIGH (direct evidence from shorts_naberal CONFLICT_MAP + 2026 policy sources)
**Evidence base:** CONFLICT_MAP.md 39 incidents (A:13 / B:16 / C:10) + 2025-07 ~ 2026-01 YouTube policy enforcement waves

---

## Overview

이 문서는 "일반적인 조심하라" 수준의 조언이 아니다. **shorts_naberal에서 실제 발생하여 39건의 drift 충돌로 누적된 구체 패턴** + **2026년 YouTube 정책 집행 물결에서 수천 채널을 demonetize시킨 실제 실패 모드**를 기록한다.

예방 기준:
- 각 pitfall은 **shorts_naberal CONFLICT_MAP ID 참조** (재발 방지용) 또는 **2026 외부 사례 참조**
- 탐지 가능한 조기 경보 신호 (vague "be careful" 금지)
- Phase 1~10 매핑 (어느 phase에서 구조적으로 차단할지)
- Severity: **Blocker** (파이프라인 실패/YPP 리젝/채널 제재) / **Major** (품질 붕괴/수익 절반 손실) / **Minor** (신뢰 저하)

---

## Category A — YouTube Platform Pitfalls

### A-P1. Inauthentic Content 정책 위반 — YPP 영구 박탈

**Severity:** Blocker
**Warning signs (탐지):**
- 업로드 20개 중 3개 이상이 동일 템플릿 구조 (동일 훅 공식 + 동일 B-roll 풀 + 동일 엔딩)
- "자동 생성된 뉴스/리스트/팩트 Shorts" 니치
- 비디오 간 variation이 primary subject(주제만) 뿐 — 구조·보이스·편집 동일
- 시청자 댓글에서 "AI slop", "robot voice" 언급 비율 증가

**What goes wrong:**
2025년 7월 YouTube는 "repetitious content" 정책을 "inauthentic content"로 개명, 2026년 1월 대규모 집행 시작. **16개 메이저 채널이 47억 뷰 + 연 $10M 수익을 YPP에서 박탈**. 수천 개의 faceless AI 채널이 단일 patterns — "synthetic voiceover with no tonal variation, stock footage with no original editing, templated scripts" — 로 일괄 차단됨.

**Prevention (actionable):**
1. **템플릿 변주 최소 3종 강제**: hook 공식 A/B/C, 엔딩 C1/C2/C3, B-roll 소스 최소 3 풀 rotation — 오케스트레이터가 지난 10개 영상 분석 후 동일 조합 금지 (phase-5 기능)
2. **"Human signal" 증거 주입 의무화**: 각 영상에 (a) 손글씨 오버레이 또는 (b) 대표님 육성 훅 5초 또는 (c) 원본 사진/영상 1컷 이상 포함 — producer가 강제 선택
3. **"Recent 20 uploads" 감사 스크립트**: 최근 20개 메타데이터 diff → 유사도 70%+ 발견 시 다음 영상 publish 차단
4. **CONFLICT_MAP A-1 교훈 적용**: Runway 6~8개 + Veo 5개 + Kling으로 소스 다각화 (단일 엔진 전용 금지)

**Phase:** Phase 3 (agent design — producer 다양성 강제 규칙), Phase 5 (QA gate — 유사도 검사), Phase 8 (publish gate)
**References:** [ScaleLab 2026](https://scalelab.com/en/why-youtube-is-cracking-down-on-ai-generated-content-in-2026), [Flocker 2026 Enforcement Wave](https://flocker.tv/posts/youtube-inauthentic-content-ai-enforcement/)

---

### A-P2. 급속 업로드 버스트 → 알고리즘 suppression

**Severity:** Major
**Warning signs:**
- 단일 세션에서 5개+ publish 시도
- 12시간 내 3개+ 업로드 (채널 baseline이 주 3~4편인데)
- 최근 baseline 대비 engagement rate가 50% 이하

**What goes wrong:**
"Publishing significantly more content than your established baseline in a short period can trigger suppression" (Fliki 2026). 실제 사례: 한 크리에이터가 새 채널 12개에 2일간 수십 개 영상 업로드 → **전체 0뷰** suppression. 스팸 필터가 즉시 작동.

**Prevention:**
1. **주 3~4편 cadence 강제 (CLAUDE.md D-10 결정)**: 오케스트레이터에 minimum 48시간 publish interval lock. `SKIP_INTERVAL_LOCK=True` 같은 우회 경로 금지 (CONFLICT_MAP A-6 skip_gates 교훈 적용)
2. **feedback_publish_interval 메모리 승계**: secondjob_naberal의 "60~180분 랜덤 간격, 1시간 1개 금지" 원칙을 Shorts에 맞게 재조정 (48시간+ 랜덤)
3. **baseline 모니터 agent**: 직전 30일 engagement rate 기준 이하 영상 publish 전 pause → 대표님 승인 요청

**Phase:** Phase 5 (orchestrator state machine — publish lock), Phase 8 (publisher agent)
**CONFLICT_MAP ref:** A-6 (skip_gates=True 우회 경로가 이런 lock도 깰 수 있음 — 물리 차단 필요)

---

### A-P3. AI disclosure label 누락 → 영구 demonetize

**Severity:** Blocker
**Warning signs:**
- 실사 인물·장소·이벤트가 AI로 생성/변조되었으나 upload 시 synthetic content label 체크 안 함
- Runway/Veo로 생성된 "실제 같은" 장면이 disclose 플래그 없이 publish
- 뉴스/사건 재현 콘텐츠에 AI 이미지 사용 + 미표기

**What goes wrong:**
"Failure to disclose 'altered or synthetic' content now results in permanent demonetisation" (Onewrk 2025/2026). 반복 누락 시 YPP 영구 suspension. faceless 채널(motion graphics, quiz)은 disclosure 불필요하나 **"realistic human/event depiction"은 필수**.

**Prevention:**
1. **publisher agent에 disclose-classifier 삽입**: scene-manifest에 `realistic_depiction: true` 플래그가 하나라도 있으면 upload form의 synthetic content 토글을 자동 ON
2. **conservative default**: 의심 시 disclose (YouTube 공식 "disclosing when not strictly required is safer default")
3. **A-1 교훈 적용**: Runway primary 전환 결정(2026-04-17)에 따라 Runway 사용 시 자동 disclose (video-sourcer AGENT에 `requires_ai_disclosure: true` 필드 추가)

**Phase:** Phase 8 (publisher agent design)
**References:** [YouTube Help — Synthetic Content Disclosure](https://support.google.com/youtube/answer/14328491), [Onewrk 2025 Guide](https://onewrk.com/youtubes-ai-disclosure-requirements-the-complete-2025-guide/)

---

### A-P4. Hook 3초 미확보 → 조회수·retention·수익 붕괴

**Severity:** Major
**Warning signs:**
- 영상 후반 3초 retention이 40% 미만
- 첫 3초가 긴 intro/logo/"구독 부탁" 반복
- hook이 텍스트 오버레이 없이 voiceover만
- CONFLICT_MAP A-8 교훈 누락: 중간편에 "놓지 않았습니다" 시그니처 삽입 = hook 무력화

**What goes wrong:**
"50-60% of viewers drop off in the first 3 seconds" (Miraflow 2026). Shorts 알고리즘은 "intro retention" (3초 통과율) 기준 priority 분배. Hook 실패 = 알고리즘 강제 push 중단 = 조회수 기본값.

**Prevention:**
1. **ins-hook inspector 필수화** (RESEARCH_REPORT 2.4 통합안 채택): 0~3초 훅 강도 0.0~1.0 rubric 평가 + 0.7 미만 FAIL → scripter 재소환
2. **"layered hook" rule**: visual + auditory + textual 3요소 중 최소 2개 동시 — 단일 요소 hook 차단
3. **pattern interrupt 5초 이내 강제**: 화면/소리/텍스트 중 하나 급변 → +23% retention (Terra Market Group)
4. **CONFLICT_MAP A-8 적용**: "놓지 않았습니다" 시그니처는 Part 1/마지막편만 (ins-structure 조건부 규칙). 중간편 삽입 시 hook 직후 이탈 유발

**Phase:** Phase 3 (ins-hook inspector 정의), Phase 5 (GATE-2 script 검증)
**CONFLICT_MAP ref:** A-8 (시그니처 조건부)

---

### A-P5. Shorts Fund 없음 / 수익 구조 오해

**Severity:** Major (budget planning)
**Warning signs:**
- "Shorts Fund로 수익 생길 것" 가정 → planning
- 조회수 × CPM 계산으로 수익 예측 (Shorts는 view-based 아님)

**What goes wrong:**
YouTube Shorts Fund는 **2023년 종료**. 현재는 YPP 내 "Shorts ad revenue sharing" 모델 — 광고는 Shorts feed 사이사이에 pool 형태로 노출, 창작자에게 pool의 45% 분배 (롱폼 55%와 다름). RPM이 **롱폼 대비 10~20% 수준**. 10M views/year YPP 기준은 Shorts만으로는 어렵고 롱폼 혼합이 현실.

**Prevention:**
1. **KPI 설정 시 명시**: 목표는 "구독 + 노출" (algorithm trust building), 수익은 secondary until 10M annual views
2. **REQ-08 주 3~4편 cadence는 롱폼과 병행 필요성 시사** — Phase 11+ v2에서 longform_hive 재검토 (Out of Scope 유지하되 경로는 확보)
3. **D-9 Core Value 재확인**: "YPP 진입 궤도"가 기준 — 수익 숫자가 아니라 **알고리즘 신뢰 축적**

**Phase:** Phase 2 (scope decisions), Phase 9 (KPI dashboard)
**References:** [Ssemble 2026](https://www.ssemble.com/blog/youtube-shorts-monetization-2026)

---

### A-P6. 동일 썸네일·제목 패턴 → 크로스-영상 shadow ban

**Severity:** Major
**Warning signs:**
- 썸네일이 동일 템플릿 (같은 폰트 + 같은 배치) 20회+ 연속
- 제목이 "이것을 모르면..." 같은 공식 반복
- CTR이 2% 미만 지속

**What goes wrong:**
Shorts 썸네일은 공식 설정 불가이나 첫 프레임이 feed 썸네일로 사용됨. 동일 패턴 반복은 "mass-produced template content" 시그널로 inauthentic 분류 위험.

**Prevention:**
1. **thumbnail-diversity inspector**: 최근 10개 첫 프레임 hash 비교 → 유사도 70%+ FAIL
2. **제목 템플릿 4~6종 rotation** (CONFLICT_MAP A-1 primary engine rotation 패턴을 제목에도 적용)
3. **Korean 특화**: 한국 feed는 "충격!" "실화!" 반복 민감 — 감정어 빈도 monitor

**Phase:** Phase 3 (ins-thumbnail-diversity), Phase 7 (metadata agent)

---

## Category B — AI-Production Pitfalls

### B-P1. AI 음성 "tells" — Korean 억양·자연스러움 붕괴

**Severity:** Major
**Warning signs:**
- 댓글에 "AI 목소리", "로봇 같다", "부자연스러움" 키워드 증가
- 종결어미 ("~습니다", "~해요") 이상 강세
- 쉼표 pause가 기계적 (250ms 고정)
- 존댓말/반말 혼재 (한국어 컨텍스트 인지 실패)
- CONFLICT_MAP A-7 재발: Morgan tempo 0.93 vs 0.97 불일치로 길이 계산 오차 40~50초

**What goes wrong:**
ElevenLabs Korean은 Gyeongsang-do + Seoul mix 같은 synthetic 억양. "keeping similarity at or below 75-80% prevents artifacts" (ElevenLabs 공식). 한국 시청자는 AI 음성에 **영어권 대비 민감도 2배 이상** (한국어는 억양/존댓말/띄어쓰기가 의미 변화 유발).

**Prevention:**
1. **음성 A/B 테스트 mandatory** (Phase 4): ElevenLabs Korean + Typecast + VOICEVOX nemo(JP 채널) 3종 blind test → 채널별 고정
2. **CONFLICT_MAP A-7 해결 상속**: voice-presets.json의 Morgan tempo 단일 소스 — `presets` vs `voice_pools` 이중화 금지. 신규 프로젝트는 `voice_pools` 만 사용
3. **쉼표 pause 가변화** (CONFLICT_MAP B-2): 고정 250ms 대신 문맥별 200~400ms 범위. incidents 채널은 300~400ms
4. **존댓말 일관성 검사관** (ins-korean-grammar, RESEARCH_REPORT 7.5 제안): 한 영상 내 "-습니다/해요/반말" 혼용 감지 FAIL
5. **CONFLICT_MAP A-9 교훈**: 탐정-조수 호명 규칙 (조수는 탐정님 호명 금지) 이런 세부 규칙이 누적되어 "자연스러움" 차이 유발 → 메모리/FAILURES에 강제 기록

**Phase:** Phase 3 (voice agent + ins-korean-grammar), Phase 4 (voice preset migration from shorts_naberal)
**CONFLICT_MAP ref:** A-7, A-9, B-2, B-3 (incidents_jp voice 3계층 충돌 — 재발 금지)

---

### B-P2. Visual AI character drift — multi-shot 일관성 붕괴

**Severity:** Major
**Warning signs:**
- 동일 캐릭터가 shot 2~3 이후 얼굴/의상/나이 변화
- Runway regenerate credit 폭증 (10개 shot을 위해 30+ 생성)
- scene-manifest에 동일 캐릭터인데 prompt가 매번 다른 text로 기술

**What goes wrong:**
"Character drift happens when the AI video generator loses track of your subject's details, causing their face, age, or clothing to morph into someone else as the camera moves" (VeedAI 2026). Shorts는 15~60초지만 **6~8개 shot 연결 시 drift 발생**.

**Prevention:**
1. **Reference image pipeline 필수** (Kling Subject Library / Veo Ingredients 모델 차용): 캐릭터 등장 영상은 reference image 1회 생성 → 모든 후속 shot에서 참조
2. **CONFLICT_MAP A-1 적용**: Runway primary, Kling child 전용, Veo signature only (최대 2개) — 엔진 혼재가 drift 가속 → 단일 캐릭터 영상은 단일 엔진 강제
3. **shot count 상한**: Shorts 단편 6shot, 시리즈 8shot 초과 금지 (drift 발생률 급증 지점)
4. **ins-character-consistency inspector** (신규 추가 검토): scene-manifest에서 동일 캐릭터 ID 탐지 → reference image 첨부 여부 검증 FAIL

**Phase:** Phase 3 (inspector 정의), Phase 5 (GATE-3 visual QA)

---

### B-P3. AI 스크립트 generic-ness — LLM 기본 verbose 스타일

**Severity:** Major
**Warning signs:**
- 모든 영상이 "오늘은 ~에 대해 알아보겠습니다" 같은 인트로
- 한 문장 길이 40자 초과 빈도 높음 (TTS에서 단조로움)
- "여러분", "꼭", "반드시" 같은 filler word 밀도 높음
- CONFLICT_MAP A-8 재발: "놓지 않았습니다" 시그니처 같은 상투적 엔딩 남용

**What goes wrong:**
LLM 기본 출력은 "safe verbose" — Shorts 60초에 맞는 punch 없음. "AI slop"의 1/3 원인. 결과: 완주율 저하 → 알고리즘 push 중단.

**Prevention:**
1. **Script-polisher agent 필수** (D-3 Producer-Reviewer 패턴 공식화): scripter 초안 → ins-hook/ins-punch FAIL → script-polisher 재작성 사이클
2. **문장 길이 상한 강제**: 30자 초과 문장 금지 (CONFLICT_MAP B-13 교훈 — 길이 검증 함수 단일화)
3. **Filler word blacklist**: "여러분", "한 번 보실까요", "어떠신가요" 등 빈도 1 영상당 3회 상한
4. **"Morgan 채널 레퍼런스 스크립트" 승계**: shorts_naberal DESIGN_BIBLE DB-01~05의 실증된 스타일 guide harvest (REQ-02)

**Phase:** Phase 3 (scripter + polisher + ins-punch), Phase 5 (GATE-2)
**CONFLICT_MAP ref:** A-8, B-13 (길이 상한 모순)

---

### B-P4. Over-automation — 인간 taste filter 0 = 대량 boring

**Severity:** Blocker (장기적 채널 정체성 붕괴)
**Warning signs:**
- 대표님이 완성 영상을 본 뒤 "이게 정말 내 채널이야?" 의문 제기 빈도 증가
- 월 리뷰에서 "기억에 남는 영상 없음"
- 구독자 증가율 0이지만 기술 품질 지표는 all-green

**What goes wrong:**
학계도 경고 — "LLM이 피드백을 스스로 제공할 수 있는가?"가 Anthropic Evaluator-Optimizer 2조건 중 하나. 자기 검증만으로는 **창의성 최저값 수렴**. shorts_naberal이 32 inspector 과포화에도 drift가 누적된 이유가 이것 — 기계적 PASS/FAIL만으로는 "재미있는가?" 측정 불가.

**Prevention:**
1. **D-2 FAILURES.md 저수지 + 월 1회 batch 리뷰**: 대표님 피드백은 즉시 SKILL 수정 금지, 월 1회 집계 → 패턴 추출 → SKILL 업데이트 (학습 충돌 방지)
2. **Taste gate (월 1회)**: 대표님이 월 12~16 영상 중 "상위 3 / 하위 3" 직접 선정 → KPI 분석과 교차 → 다음 월 producer 입력으로 반영 (REQ-09)
3. **Human signal 강제** (A-P1에 언급): 매 영상 최소 1개 비-AI 요소
4. **"AI slop" detector** (자가 검사): 최종 영상을 대표님이 아닌 제3자 샘플(예: Fiverr reviewer $5 무작위 1명)에게 월 1회 시청 테스트 → 정성 피드백

**Phase:** Phase 6 (feedback loop 설계), Phase 9 (월간 리뷰 자동화)

---

### B-P5. Runway credit 폭증 — 비용 관리 실패

**Severity:** Major (budget blocker)
**Warning signs:**
- 영상 1편당 Runway 호출 10회 초과 (regenerate 지옥)
- 월 API 비용이 예상 대비 3배+
- "일단 생성해보고 안 좋으면 다시" 패턴

**What goes wrong:**
"Multi-clip projects often require dozens of regenerations to get consistent character appearance" (Veed 2026). 또한 CONFLICT_MAP A-1 (Runway 6~8개 권장) × A-13 (Veo 5개 + Runway 6~8개 병행) = 영상당 AI 영상 10+개 생성 가능. CONFLICT_MAP A-6 skip_gates=True 같은 디버그 경로가 "일단 돌려보자" 문화 조성.

**Prevention:**
1. **GATE-1 Blueprint 완결성 강제** (RESEARCH_REPORT 5.4 plan-validate-execute): Blueprint JSON이 승인되기 전 video generation API 호출 금지 — circuit breaker (3회 실패 시 인간 에스컬레이션)
2. **Cost budget per video hard cap**: Runway 6개 + Veo 2개 = 최대 8생성 상한, 초과 시 hook-scripter 재소환 (shot 개수 자체 줄이기)
3. **reference image 재활용**: B-P2 해결책이 비용도 해결
4. **CONFLICT_MAP A-13 통일**: "Runway routine + Veo signature only (최대 2)" B안 채택 (config hint)

**Phase:** Phase 5 (orchestrator circuit breaker), Phase 8 (cost monitor)
**CONFLICT_MAP ref:** A-1, A-13, A-6

---

## Category C — Multi-Agent Orchestration Pitfalls (CONFLICT_MAP 핵심)

### C-P1. 32 inspector 과포화 — 루프·중복·비용 3중 실패

**Severity:** Blocker (shorts_naberal에서 실제 발생)
**Warning signs:**
- inspector 2개가 동일 scene-manifest에 반대 평결 (PASS/FAIL)
- 재소환 루프 3회+
- "왜 매번 다른 inspector가 FAIL하지?" 대표님 질문
- CONFLICT_MAP A-4 재발 징후

**What goes wrong:**
CONFLICT_MAP A-4 실제 사례: ins-matching "unique ≥80%" PASS / ins-duplicate "unique 100%" FAIL / video-sourcer "unique 100% 목표" → 85% scene-manifest가 **inspector 2종 상반 평결로 오케스트레이터 결정 불가 → video-sourcer 재소환 무한 루프**. Anthropic sweet spot은 3~5명, 10명 초과 시 비용 증가만 (RESEARCH_REPORT Area 1.3).

**Prevention:**
1. **REQ-03 12~20명 통합 설계**: RESEARCH_REPORT 2.4 제안 구조 채택 — structural 3~4 + content 4~5 + style 3~4 + compliance 3~4 + technical 2~3
2. **Rubric 강제 structured output** (JSON Schema `InspectorVerdict`): 주관적 "looks good" 금지, score 0.0~1.0 + specific issues
3. **역할 중복 검사**: 두 inspector가 동일 필드 검증 금지 (CONFLICT_MAP B-14 ins-duplicate vs ins-license 교훈)
4. **maxTurns 규칙 문서화** (CONFLICT_MAP B-7): 신규 inspector README.md에 maxTurns 산정 기준 필수
5. **단일 진실(single-source) 원칙**: unique 기준은 duplicate만 판정, matching은 다른 축 (소스 채널 다양성)

**Phase:** Phase 3 (inspector 통합 설계 — 핵심 phase)
**CONFLICT_MAP ref:** A-4 (unique 기준 3중), B-7 (maxTurns 규칙 없음), B-14 (역할 겹침)

---

### C-P2. TODO(next-session) 미연결 — "자동" 거짓말

**Severity:** Blocker
**Warning signs:**
- 문서에 "자동 실행됨" 명시, 코드에 "TODO: wire here"
- 대표님 체감 "GATE가 스킵된다"
- `grep -rn "TODO(next-session)" scripts/` 결과 > 0

**What goes wrong:**
CONFLICT_MAP A-5 실제 사례: `orchestrate.py:520, 781, 1051, 1129` 4곳에 `TODO(next-session): wire ins-narration GATE 3a check here` — CLAUDE.md는 "자동 실행" 선언. 나베랄(AI)이 CLAUDE.md 신뢰 → 실제 경로는 해당 GATE 생략 → 품질 회귀 미탐지. **"에이전트가 GATE를 스킵한다"의 근본 원인**.

**Prevention:**
1. **REQ-04 state machine 오케스트레이터**: 텍스트 체크리스트 완전 폐기, 각 GATE는 `harness.gate_dispatch(...)` 실제 호출 — TODO 주석 물리 차단
2. **pre_tool_use hook**: `grep -rn "TODO(next-session)"` 커밋 시 차단 (D-6 3중 방어선)
3. **CI test**: `test_gate_wiring.py`에 "TODO(next-session) in orchestrate.py" grep FAIL 처리
4. **Phase commit gate**: GSD 정식 — phase별 commit 없이 다음 phase 진입 불가 (CLAUDE.md constraints)

**Phase:** Phase 4 (orchestrator 재작성), Phase 10 (harness-audit 스킬)
**CONFLICT_MAP ref:** A-5 (직접 인용)

---

### C-P3. skip_gates=True 디버그 경로 상주 → 우회 합법화

**Severity:** Blocker
**Warning signs:**
- 테스트 코드나 오케스트레이터에 `skip_gates=True` 호출
- "임시로" 주석과 함께 프로덕션 상주
- `grep -rn "skip_gates=True" scripts/` 결과 > 0 (테스트 외)

**What goes wrong:**
CONFLICT_MAP A-6 실제 사례: `orchestrate.py:1239-1291` `run_pipeline_outsource_first(skip_gates=True)` 분기가 세션 72 도입, 디버그 주석만 있고 **물리 제거 안 됨**. HC-4 "GATE 1~5 전부 실행" 규칙 우회 경로 상시 존재 → 점점 "빨리 돌리기 위한 당연한 선택지"로 변질.

**Prevention:**
1. **완전 제거 (A안 채택)**: v2에서 skip_gates 파라미터 자체 삭제, GSD 강제 실행만
2. **환경 변수 게이트도 금지**: "SHORTS_DEBUG_SKIP_GATES=1" 같은 우회도 금지
3. **pre_tool_use hook**: `grep "skip_gates=True"` 발견 시 commit 차단
4. **"Broken Window" 원칙**: 한 번 우회 경로 허용 = 영구 상주 → 문화 자체가 품질 회귀

**Phase:** Phase 4 (orchestrator — 아예 해당 파라미터 없이 설계)
**CONFLICT_MAP ref:** A-6 (직접 인용)

---

### C-P4. Researcher/Scripter 진입점 충돌 — create-shorts vs NLM

**Severity:** Blocker
**Warning signs:**
- 동일 스테이지에 2개 진입점 문서
- 구 스킬이 여전히 `@shorts-researcher` 호출, 신 스킬은 NLM 우선
- "어느 쪽을 따를지 몰라 스킵하거나 루프"

**What goes wrong:**
CONFLICT_MAP A-3 실제 사례: 세션 77 CLAUDE.md 업데이트 "최초공정은 NLM 2-노트북, shorts-researcher/scripter는 폴백" — 하지만 `.claude/skills/create-shorts/SKILL.md:233, 253` 가 여전히 `@shorts-researcher` + `@shorts-scripter` 직접 디스패치. 실제 실행 경로는 **구형 스킬 따라감** → NLM 신형 주장은 거짓말.

**Prevention:**
1. **REQ-07 NotebookLM 스킬 통합 + Tier 2 위키 RAG**: NLM primary 확정 (A안), 폴백 경로는 별도 agent로 격리
2. **단일 진입점 원칙**: 각 stage는 1개 agent — researcher/scripter/nlm-fetcher 3명 동시 허용 금지
3. **create-video 스킬 완전 삭제** (CONFLICT_MAP A-12 A안): 중복 진입점 제거
4. **D-7 state machine**: 오케스트레이터가 stage별 진입 agent를 **코드로 고정** — 스킬 문서에서 호명 금지

**Phase:** Phase 3 (agent 구조), Phase 4 (orchestrator state machine)
**CONFLICT_MAP ref:** A-3 (직접 인용), A-12 (create-video 중복)

---

### C-P5. Lost in the Middle — 500+줄 SKILL.md의 중간 지시 누락

**Severity:** Major
**Warning signs:**
- SKILL.md > 500줄 (REQ-10 위반)
- 에이전트가 중간 섹션 규칙을 "읽었으나 무시"
- 동일 에이전트가 실행마다 다른 결정

**What goes wrong:**
Liu et al. 2023: 20-doc context에서 position 10 이동 시 **30%+ 정확도 감소**. RoPE 모델이 시작·끝 우선, 중간 약화. System prompt drift: 30분+ 세션에서 system prompt 영향력 점진 감소 — 1시간 후 "prompt 없는 것처럼" 행동 (RESEARCH_REPORT 4.1~4.2).

**Prevention:**
1. **REQ-10 SKILL.md 500줄 상한** (Anthropic hard rule): 초과 시 references/로 분리 (progressive disclosure)
2. **1-level deep only**: references는 1단계만 — 중첩 금지
3. **MUST REMEMBER 섹션 끝 배치** (RESEARCH_REPORT 3.2 템플릿): 중요 규칙은 문서 끝 (RoPE 끝 우선 활용)
4. **Structured Output 강제 (JSON Schema)** — 성공률 0.92 (RESEARCH_REPORT 4.3)
5. **"Consistent Terminology" glossary** (CLAUDE.md 3-Tier 위키 D-1): "API endpoint", "field" 같은 용어 혼용 금지 — drift 원인

**Phase:** Phase 3 (agent design template), Phase 10 (harness-audit — 500줄 검증)
**RESEARCH_REPORT ref:** 4.1~4.5

---

### C-P6. Description 애매함 → 잘못된 에이전트 호출

**Severity:** Major
**Warning signs:**
- Description이 "Helps with X" 같은 vague 표현
- 1024자 초과 또는 100자 미만
- 사용자 발화 키워드가 description에 없음
- 에이전트가 호명되지 않는 상황 빈번

**What goes wrong:**
Anthropic 공식: description은 agent 호출 **트리거 키워드** — "does X. Use when Y + specific triggers" 패턴. vague = 호출 안 됨 = 기능 있어도 skip. shorts_naberal 32명 inspector 중 일부가 이 이유로 활성화 안 됐을 가능성.

**Prevention:**
1. **Description 템플릿 강제** (RESEARCH_REPORT 4.4):
   `"{3인칭 동작}. Use when {사용자가 Y 발화 또는 Z 조건 해당}."`
2. **트리거 키워드 명시적 포함**: 사용자 발화 예상 단어 (한국어 예: "영상 만들어", "쇼츠 검증", "블루프린트 확인")
3. **1024자 상한 + 100자 하한** CI 검증
4. **주기 전수 감사** (REQ-10): harness-audit 스킬이 모든 에이전트 description 품질 점수화

**Phase:** Phase 3 (agent definition template)
**RESEARCH_REPORT ref:** 4.4

---

### C-P7. Harvest contamination — drift 패턴 무의식 포팅

**Severity:** Major (shorts_studio 고유 리스크)
**Warning signs:**
- shorts_naberal에서 파일을 그대로 복사 후 수정 없이 사용
- "어차피 작동했으니까" 가정으로 구 drift 온존
- A급 13건 충돌 중 미해결 항목이 신 프로젝트에 재출현

**What goes wrong:**
D-8 "Harvest, not Fork" 전략의 함정 — 작동 자산만 골라 harvest해야 하는데, **paired drift**(A-1 Runway vs Kling)도 함께 포팅될 위험. 예: video-sourcer AGENT.md harvest 시 Kling 잔존 문자열도 함께. 결과: 신 프로젝트 Phase 3 시작부터 drift 재시작.

**Prevention:**
1. **REQ-02 Harvest 절차 명문화**: 읽기만 허용, 수정 금지, copy 시 **source hash + date 주석 필수**
2. **Harvest gate**: `.preserved/harvested/` 에 모든 harvest 대상을 먼저 복사 → diff review → 실제 프로젝트 디렉토리로 승격 (3단계)
3. **CONFLICT_MAP 39건 전수 확인**: harvest 대상 파일이 CONFLICT_MAP에 언급됐는지 검색 → 언급 시 "정답 확정" 버전 확인 필수
4. **Harvest blacklist**: 파일별 harvest 금지 목록 유지 (예: `orchestrate.py:1239-1291` skip_gates 블록)
5. **Second System Effect 회피** (RESEARCH_REPORT SI-1): 기능 확장 금지, 아키텍처 정리만

**Phase:** Phase 2 (Harvest 전략 수립), Phase 3 (실제 harvest 실행)
**RESEARCH_REPORT ref:** SI-1, CONFLICT_MAP ref: 전체 39건

---

### C-P8. FAILURES.md / SKILL 학습 충돌

**Severity:** Major
**Warning signs:**
- CONFLICT_MAP A-8 재발: 같은 규칙이 3개 문서에 3가지 버전
- 피드백 받을 때마다 SKILL.md 즉시 수정 → 다음 세션에 반대 방향 수정
- producer와 inspector가 FAILURES에 서로 다른 금지 규칙

**What goes wrong:**
CONFLICT_MAP A-8 실례: "놓지 않았습니다" 시그니처가 **권장(DESIGN_BIBLE) → 금지(FAIL-SCR-010) → 조건부(ins-structure Part1/마지막만)** 3단 진화. scripter는 DESIGN_BIBLE 읽고 Part2에 삽입 → ins-structure FAIL → 재소환 루프. 학습이 누적되며 서로 모순.

**Prevention:**
1. **D-2 FAILURES.md 저수지 + 월 1회 batch 리뷰**: 피드백 → FAILURES에만 즉시 추가, SKILL 수정은 월 1회 consolidation
2. **D-5 SKILL.md 버저닝 + `SKILL_HISTORY/`**: 모든 SKILL 수정은 history 백업 + .candidate staging → rollback 보장
3. **단일 진실(single source) 원칙**: 규칙별 canonical 문서 1개 지정 (예: 시그니처 규칙 → ins-structure), 다른 문서는 링크만
4. **규칙 충돌 CI**: "same rule ≠ different values" 자동 검사 (CONFLICT_MAP A-4 unique 3값 검출 같은 방식)

**Phase:** Phase 6 (SKILL 버저닝 + FAILURES 저수지 구축)
**CONFLICT_MAP ref:** A-8 (3단 진화 사례), A-4 (3값 충돌), B-5 (듀오 비율 4값)

---

## Category D — Korean Market Pitfalls

### D-P1. KOMCA 음악 저작권 — 배경음악 자동 검출

**Severity:** Blocker (Copyright strike)
**Warning signs:**
- 한국 대중음악을 BGM으로 사용 (보컬/비보컬 무관)
- "저작권 free" 사이트에서 한국 작곡가 작품 사용 (별도 KOMCA 관리)
- YouTube Content ID 매칭 Strike

**What goes wrong:**
KOMCA는 국내 130만+ 곡 관리, Content ID로 자동 매칭. 2023년 KOMCA 공정거래위 과징금 3.4억 사례처럼 **협회 집행력 매우 강함**. Strike 3회 시 채널 제재, YPP 박탈.

**Prevention:**
1. **배경음악 whitelist 고정**: YouTube Audio Library 한국어 호환 트랙만 (commercial-safe)
2. **외부 음원 사용 금지**: NCS, Artlist 같은 "저작권 free" 사이트도 한국 작곡가 작품은 KOMCA 중복 관리 가능 → license 문서 수집 필수
3. **ins-license 역할 강화** (CONFLICT_MAP B-14): 음악 소스 license 필드 검증 — ID/증명 없으면 FAIL
4. **AI 음악 생성 대안**: Suno / Udio / MusicGen — 단 YouTube Music Rights 정책 변동 중이므로 월 1회 재확인

**Phase:** Phase 3 (ins-license 재정의), Phase 8 (publisher pre-check)
**CONFLICT_MAP ref:** B-14 (ins-duplicate vs ins-license 역할 분리)

---

### D-P2. 한국 방송사·뉴스 자료 사용 — 방송 저작권 + 초상권

**Severity:** Blocker
**Warning signs:**
- 사건/사고/이슈 영상에 KBS/MBC/SBS 뉴스 클립 사용
- "공익 보도"라고 자체 판단 (fair use 한국 규정 매우 좁음)
- 실존 인물 얼굴 노출

**What goes wrong:**
한국 저작권법은 미국 fair use보다 **사적/공적 이용 범위 훨씬 좁음**. 방송사는 소규모 사용도 즉시 Content ID 이의신청. 초상권은 별도 민사 청구 가능. shorts_naberal incidents 채널이 "사건 재현" 니치인데 이게 직접 위험.

**Prevention:**
1. **실사 뉴스 클립 전면 금지**: 모든 사건 영상은 AI 재현(Runway/Veo) 또는 일러스트로만
2. **초상권 마스킹**: 실존 인물 얼굴은 블러/모자이크 (ins-mosaic 역할)
3. **실명 사용 신중**: 유명 사건은 가명화 또는 "사건 A" 익명 처리
4. **CONFLICT_MAP A-13 + D-P1 복합 적용**: 영상 소스 우선순위에서 "뉴스캡처" 제거 (17일 변경에 이미 반영됨 — 정착 필요)

**Phase:** Phase 3 (ins-mosaic + ins-license 강화), Phase 5 (GATE-4 compliance)
**CONFLICT_MAP ref:** A-13 (Veo vs Runway 우선순위), 17일 "뉴스캡처" 제거 반영

---

### D-P3. 한국어 자막 자동 생성 품질 — Whisper 한계

**Severity:** Major
**Warning signs:**
- 띄어쓰기 오류 (한국어는 띄어쓰기 = 의미 변화)
- 고유명사 오탈자 ("삼성"을 "성"으로)
- 외래어 표기 불일치 ("유튜브" vs "YouTube")
- 존댓말 자동 구분 실패

**What goes wrong:**
Whisper 한국어 WER 3위 수준(우수) BUT 고유명사/도메인 용어는 여전히 오탈자. 띄어쓰기는 Whisper 기본 지원 약함. CONFLICT_MAP A-9 "탐정님 호명" 같은 디테일이 자막에서도 발생.

**Prevention:**
1. **WhisperX 필수** (RESEARCH_REPORT 6.3): 단순 Whisper 아닌 WhisperX (word-level alignment)
2. **Prompt hint**: 도메인 특화 단어/고유명사를 prompt 파라미터로 전달 (Whisper 공식 기능)
3. **후처리 ins-korean-grammar**: 띄어쓰기 + 존댓말 일관성 + 외래어 표기 통일 검사
4. **Glossary 고정** (RESEARCH_REPORT 4.4 "Consistent Terminology"): 채널별 고유명사/용어 사전 유지 — Whisper + 후처리 양쪽에서 참조

**Phase:** Phase 3 (ins-korean-grammar), Phase 5 (GATE-3 subtitle alignment)

---

### D-P4. 문화 민감도 — 세대/지역/정치/젠더

**Severity:** Major
**Warning signs:**
- 특정 지역(예: "전라도", "경상도") 스테레오타입
- 세대 갈등 ("MZ", "꼰대") 과도 사용
- 정치 이슈 (좌/우파, 특정 정당) 언급
- 성차별 표현

**What goes wrong:**
한국 시청자는 영어권보다 문화 민감 이슈에 **댓글 폭증 속도 빠름**. 한 번 "문제 영상" 낙인 → 알고리즘 노출 저하 + 채널 identity 훼손. AI 스크립트는 이런 뉘앙스 탐지 약함.

**Prevention:**
1. **ins-cultural-sensitivity inspector 추가**: 지역명 + 세대어 + 정치 키워드 + 젠더 단어 탐지 → 컨텍스트 분류 (중립/위험)
2. **Forbidden topics list**: shorts_naberal 승계 + 확장 — 특정 사건/인물 블랙리스트
3. **월 1회 taste gate에 포함**: 대표님이 리뷰 시 "이번 달 위험 표현 0건" 체크
4. **FAILURES.md 카테고리 분리**: "cultural" 태그로 누적 → 패턴 학습

**Phase:** Phase 3 (inspector 추가), Phase 9 (taste gate)

---

### D-P5. 네이버 vs YouTube 플래그 차이 무시

**Severity:** Minor (shorts_studio는 YouTube 전용이나 승계 고려)
**Warning signs:**
- 네이버에서 문제없던 표현이 YouTube에서 demonetize
- 역방향도 성립

**What goes wrong:**
네이버(웹툰/블로그)는 한국 법 기준, YouTube는 글로벌 기준 + AI 검출. secondjob_naberal (블로그) 승계 자산 중 네이버 기준 "안전" 콘텐츠가 YouTube에서는 "sensitive content" 플래그 가능.

**Prevention:**
1. **REQ-02 harvest 시 플랫폼 타겟 필터**: secondjob_naberal 블로그 콘텐츠를 Shorts 재활용 시 YouTube 기준 재검증
2. **YouTube Community Guidelines glossary** 유지 — 한국어 번역 포함

**Phase:** Phase 2 (harvest scope), Phase 8 (publisher)

---

## Category E — Business Model Pitfalls (YPP-Specific)

### E-P1. 조회수만 본 planning — retention 누락

**Severity:** Major
**Warning signs:**
- KPI에 조회수만 추적, retention·완주율 미추적
- "1만 뷰 영상" 기념하지만 평균 시청 시간 15초
- YPP 검토 시 reject 사유 "low quality signal"

**What goes wrong:**
YPP 1000구독 + 10M views/year 요건은 **raw view count 아님** — "authentic engagement" + retention 기준. 조회수 높아도 retention 30% 미만 영상 많으면 YPP reject 가능 (inauthentic 분류).

**Prevention:**
1. **REQ-09 KPI 정의 재검토**:
   - Primary: **3초 retention** (> 60%), **완주율** (> 40%), **평균 시청 시간** (> 25초)
   - Secondary: 조회수, 좋아요, 구독 전환율
2. **kpi_log.md 필수 필드**: 3초/완주/평균시청 3종 무조건 기록
3. **월간 producer feedback**: 상위/하위 영상의 retention curve 분석 → hook 패턴 추출
4. **A-P4 교훈 연결**: hook 개선이 곧 retention — ins-hook inspector 점수와 KPI 상관성 trace

**Phase:** Phase 9 (KPI dashboard + feedback loop)

---

### E-P2. Reused content policy — 자체 제작 증명 실패

**Severity:** Blocker
**Warning signs:**
- 타 채널 영상 재편집 + 본인 해설 추가만
- 원본 vs 변경 비율에서 "meaningful original creative contribution" 불명
- CONFLICT_MAP A-3 잔재: 구 researcher가 외부 콘텐츠 stitching 패턴

**What goes wrong:**
"Reused content" reject 사유는 **"self-production evidence 불충분"**. 타 채널 클립 + voiceover 같은 패턴. 2026년 reviewer는 AI voice + reused clips 조합을 즉각 reject.

**Prevention:**
1. **100% 자체 생성 원칙**: 텍스트(LLM)+ 음성(TTS) + 영상(Runway/Veo) 모두 자체 파이프라인. 외부 클립 사용 금지 (B-roll도 Storyblocks 라이선스 보유 전제)
2. **production evidence 자동 생성**: 각 영상에 "blueprint → script → voice → render" 파이프라인 로그 attached (YPP 검토 제출용)
3. **D-P2와 연동**: 뉴스 클립 전면 금지가 이 정책과 일치

**Phase:** Phase 8 (publisher에 production metadata 첨부)

---

### E-P3. Collaboration with ghost/AI channels — 연좌 제재

**Severity:** Major
**Warning signs:**
- 다른 AI 생성 채널과 cross-promotion
- "AI channel network" 참여
- 동일 템플릿 사용 채널끼리 구독 교환

**What goes wrong:**
2026년 1월 YouTube 집행 사례: **"네트워크" 탐지 — 16개 메이저 채널이 동시 terminate**. 단일 채널 품질이 좋아도 ghost network 연결 시 연좌.

**Prevention:**
1. **Cross-promotion 정책 명문화**: 검증된 human-run 채널과만 협업
2. **동일 template 공유 금지**: 다른 AI 채널에서 우리 프로젝트 스크립트/보이스 패턴 사용 허용 안 함
3. **Channel fingerprint monitoring**: 우리 채널 content fingerprint이 타 채널에 복사되는지 월 1회 검색

**Phase:** Phase 9 (ops monitoring)

---

### E-P4. 수익 예측 오산 — RPM 오해

**Severity:** Minor (budget planning)
**Warning signs:**
- 조회수 × $0.01~0.03 CPM 공식 사용 (잘못된 계산)
- 월 목표 수익을 조회수로 역산

**What goes wrong:**
Shorts RPM은 롱폼 대비 10~20% 수준. 10M views가 $1K~$3K 정도 (지역별 편차 큼, 한국 viewer 비중 높으면 더 낮음). planning에서 과대 추정 시 Phase 11+ scope 결정 오류.

**Prevention:**
1. **conservative RPM 가정**: $0.20 per 1K views (한국 Shorts 보수값)
2. **Phase 11 v2 판단 기준**: YPP 진입 후 3개월 실측 RPM으로 scope 재산정
3. **D-9 재확인**: Core Value = YPP 진입 궤도 (수익 숫자 아님)

**Phase:** Phase 2 (budget planning)

---

## Top 10 Most Critical Pitfalls

**shorts_naberal 실측 + 2026 YouTube 집행** 기준 우선순위:

| # | Pitfall | Severity | Phase | shorts_naberal 참조 |
|---|---------|----------|-------|---------------------|
| 1 | C-P2 TODO(next-session) 미연결 — "자동" 거짓말 | Blocker | 4 | **CONFLICT_MAP A-5** (직접 인용) |
| 2 | A-P1 Inauthentic Content 정책 위반 | Blocker | 3,5,8 | 2026-01 집행 16 채널 termination |
| 3 | C-P3 skip_gates=True 디버그 경로 상주 | Blocker | 4 | **CONFLICT_MAP A-6** (직접 인용) |
| 4 | C-P1 32 inspector 과포화 — 루프·중복 | Blocker | 3 | **CONFLICT_MAP A-4, B-7, B-14** |
| 5 | C-P4 Researcher/Scripter 진입점 충돌 | Blocker | 3,4 | **CONFLICT_MAP A-3** (직접 인용) |
| 6 | A-P3 AI disclosure label 누락 | Blocker | 8 | 2026 영구 demonetize 정책 |
| 7 | D-P2 한국 방송사·뉴스 자료 무단 사용 | Blocker | 3,5 | KOMCA + 방송사 집행력 |
| 8 | E-P2 Reused content — 자체 제작 증명 실패 | Blocker | 8 | YPP 2026 reject 패턴 |
| 9 | C-P7 Harvest contamination — drift 포팅 | Major | 2,3 | **CONFLICT_MAP 39건 전체** |
| 10 | B-P4 Over-automation — 인간 taste filter 0 | Blocker | 6,9 | D-2 FAILURES.md 월 1회 batch |

---

## Phase Mapping Summary

| Phase | 핵심 Pitfall 차단 책임 |
|-------|------------------------|
| **Phase 1** (초기화) | — |
| **Phase 2** (scope + budget) | A-P5 Shorts Fund 오해, C-P7 Harvest contamination (계획), E-P4 RPM 오해 |
| **Phase 3** (agent design — **critical**) | C-P1 inspector 과포화, C-P4 진입점 충돌, C-P6 description, B-P1 voice, B-P2 character drift, B-P3 generic script, D-P3 자막 품질, D-P4 문화 민감도, A-P4 hook, A-P6 thumbnail |
| **Phase 4** (orchestrator 재작성 — **critical**) | C-P2 TODO 미연결, C-P3 skip_gates, C-P5 Lost in Middle |
| **Phase 5** (GATE 설계) | A-P1 inauthentic (유사도 검사), B-P5 cost circuit breaker, 각 GATE별 compliance |
| **Phase 6** (FAILURES + SKILL 버저닝) | C-P8 학습 충돌, B-P4 over-automation |
| **Phase 7** (metadata + SEO) | A-P6 썸네일 다양성, D-P1 음악 license |
| **Phase 8** (publisher) | A-P2 업로드 버스트, A-P3 AI disclosure, E-P2 reused content, D-P1/D-P2 license |
| **Phase 9** (KPI + taste gate) | E-P1 retention, B-P4 taste, E-P3 ghost network |
| **Phase 10** (harness-audit) | C-P2/C-P3/C-P5 전수 검증 (SKILL 500줄 + TODO grep + skip_gates grep) |

---

## 재발 방지 체크리스트 (shorts_studio commit gate)

모든 phase 진입 전 자동 검증:

```bash
# 1. TODO(next-session) 검출 (CONFLICT_MAP A-5 재발 차단)
grep -rn "TODO(next-session)" scripts/ && exit 1

# 2. skip_gates=True 검출 (CONFLICT_MAP A-6 재발 차단)
grep -rn "skip_gates=True" scripts/ --exclude-dir=tests && exit 1

# 3. 단일 값 3중화 검출 (CONFLICT_MAP A-4 재발 차단)
# unique 기준, tempo, duration 등 숫자 단일 진실 검증

# 4. SKILL.md 500줄 상한 (REQ-10 + Anthropic hard rule)
find .claude/skills -name "SKILL.md" -exec wc -l {} + | awk '$1 > 500 {exit 1}'

# 5. description 길이 + 3인칭 (C-P6)
# 각 agent frontmatter description 파싱

# 6. Kling/Runway primary 단일화 (CONFLICT_MAP A-1 재발 차단)
grep -rn "Kling.*[Pp]rimary\|Kling 3\.0.*PRIMARY" && exit 1

# 7. "놓지 않았습니다" 시그니처 조건부 (CONFLICT_MAP A-8)
# Part 1/마지막만 허용 — 중간편 검출 시 FAIL

# 8. 탐정님 호명 금지 (CONFLICT_MAP A-9)
grep -rn "탐정님" producers/assistant/ && exit 1

# 9. inspector 개수 (REQ-03 12~20)
ls .claude/agents/inspectors/ | wc -l # must be 12~20

# 10. 오케스트레이터 줄수 (REQ-04 500~800)
wc -l scripts/orchestrator/orchestrate_v2.py # must be 500~800
```

---

## Sources

- shorts_naberal CONFLICT_MAP.md (2026-04-18, 39 incidents)
- shorts_naberal RESEARCH_REPORT.md (2026-04-18, Area 1~7 + SI-1~4)
- [YouTube Inauthentic Content Policy Enforcement Wave 2026](https://flocker.tv/posts/youtube-inauthentic-content-ai-enforcement/)
- [ScaleLab — YouTube AI Crackdown 2026](https://scalelab.com/en/why-youtube-is-cracking-down-on-ai-generated-content-in-2026)
- [Miraflow — Shorts Shadowban 2026](https://miraflow.ai/blog/youtube-shorts-shadowban-2026-how-to-tell-fix)
- [Miraflow — Shorts Best Practices 2026](https://miraflow.ai/blog/youtube-shorts-best-practices-2026-complete-guide)
- [Ssemble — Shorts Monetization 2026](https://www.ssemble.com/blog/youtube-shorts-monetization-2026)
- [YouTube Help — Synthetic Content Disclosure](https://support.google.com/youtube/answer/14328491)
- [Onewrk — YouTube AI Disclosure Guide](https://onewrk.com/youtubes-ai-disclosure-requirements-the-complete-2025-guide/)
- [VeedAI / Veo4 — AI Video Model Comparison 2026](https://veo4.dev/kling-vs-runway)
- [GLBGPT — Kling Character Consistency Guide 2026](https://www.glbgpt.com/hub/kling-ai-character-consistency-explained)
- [Terra Market Group — Short-Form Video Hooks](https://www.terramarketgroup.com/digital-marketing-2/short-form-video-hooks-7-formulas-for-70-retention/)
- [KOMCA 한국음악저작권협회](https://www.komca.or.kr/)
- [나무위키 — YouTube Shorts 저질·도용·양산형 콘텐츠 문제](https://namu.wiki/w/YouTube%20Shorts/%EC%A0%80%EC%A7%88%C2%B7%EB%8F%84%EC%9A%A9%C2%B7%EC%96%91%EC%82%B0%ED%98%95%20%EC%BD%98%ED%85%90%EC%B8%A0%20%EB%AC%B8%EC%A0%9C)
- [ElevenLabs Korean Voices](https://elevenlabs.io/text-to-speech/korean)
- Anthropic "Building agents with the Claude Agent SDK" (공식 블로그, 2025)
- Fred Brooks, *The Mythical Man-Month* (1975) — Second System Effect
- Joel Spolsky, "Things You Should Never Do, Part I" (2000) — rewrite from scratch 경고
- Liu et al. (2023) — "Lost in the Middle" Stanford
- arXiv: FilmAgent, Mind-of-Director, Omniagent, MAViS (RESEARCH_REPORT Area 1 인용)
