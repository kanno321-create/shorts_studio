# Phase 4: Agent Team Design - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Mode:** Auto-generated (skip_discuss=true — REQUIREMENTS.md AGENT + RUB + CONTENT + AUDIO + SUBT + COMPLY sections fully specify scope, no grey areas)

<domain>
## Phase Boundary

17 inspector 6 카테고리 + Producer 팀 (3단 분리: Director/ScenePlan/ShotPlan) + Supervisor 1명을 rubric JSON Schema와 **동시에** 정의하여, Producer-Reviewer 이중 생성 파이프라인이 한국어 화법 / 컴플라이언스 / 채널 정체성 기준으로 자동 평가 가능한 상태를 만든다. CONTENT · AUDIO · SUBT · COMPLY 규칙이 이 시점에서 에이전트 프롬프트에 결합된다.

**Scope in:**
- Producer 11명 AGENT.md + Inspector 17명 AGENT.md + Supervisor 1명 = **29개 에이전트** 정의
- rubric JSON Schema (공통 `{verdict, score, evidence[], semantic_feedback}`) + VQQA 시맨틱 그래디언트 구조
- CONTENT 규칙 (7건: 3초 hook, 한국어 화법, 니치, 엔딩 hook 등)
- AUDIO 규칙 (4건: Typecast 1위, ElevenLabs fallback, 존댓말/반말 가이드, KOMCA whitelist)
- SUBT 규칙 (3건: 1초 단위 blocking, WhisperX 기반, 폰트/색)
- COMPLY 규칙 (6건: license, platform-policy, safety, mosaic, K-pop, AF-4/5/13)
- harness-audit 검증 통과 (500줄 이하, description 1024자 이하, MUST REMEMBER 끝 배치)

**Scope out:**
- 오케스트레이터 구현 (Phase 5)
- NotebookLM wiki 채우기 (Phase 6)
- E2E 통합 테스트 (Phase 7)
- 발행 파이프라인 (Phase 8)
- AGENT-06 harvest-importer (Phase 3 완료)

</domain>

<decisions>
## Implementation Decisions

### Agent 조직 구조 (Producer 11 + Inspector 17 + Supervisor 1 = 29)

**Producer 팀 (REQ AGENT-01, AGENT-02, AGENT-03):**
- Core 6 (AGENT-01): trend-collector, niche-classifier, researcher (= nlm-fetcher), scripter, script-polisher, metadata-seo
- 3단 분리 (AGENT-02): director, scene-planner, shot-planner — NotebookLM T6
- 지원 5 (AGENT-03): voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher

**Inspector 17명 / 6 카테고리 (REQ AGENT-04):**
- Structural (3): ins-blueprint-compliance, ins-timing-consistency, ins-schema-integrity
- Content (3): ins-factcheck, ins-narrative-quality, ins-korean-naturalness
- Style (3): ins-tone-brand, ins-readability, ins-thumbnail-hook
- Compliance (3): ins-license, ins-platform-policy, ins-safety
- Technical (3): ins-audio-quality, ins-render-integrity, ins-subtitle-alignment
- Media (2): ins-mosaic, ins-gore

**Supervisor (REQ AGENT-05):** shorts-supervisor — 재귀 위임 금지 (1 depth max)

### Rubric JSON Schema (REQ RUB-04 — AGENT와 동시 정의)

공통 output 스키마:
```json
{
  "verdict": "PASS" | "FAIL",
  "score": 0-100,
  "evidence": [{"type": "citation|regex|heuristic", "detail": "..."}],
  "semantic_feedback": "자연어 그래디언트 (VQQA — '팔이 녹아내림' 스타일, Producer 프롬프트 주입용)"
}
```

### 에이전트 설계 표준 (RUB-01~06, AGENT-07~09)

- **LogicQA** (RUB-01): Main-Q + 5 Sub-Qs 다수결. NotebookLM T15.
- **Reviewer O/X only** (RUB-02): 창작 금지, 평가만. NotebookLM T6.
- **VQQA 시맨틱 그래디언트** (RUB-03): 자연어 피드백 → Producer 프롬프트 주입. T7.
- **maxTurns 표준 3** (RUB-05): 예외 factcheck 10 / tone-brand 5 / regex 1.
- **Inspector 별도 context** (RUB-06): GAN 분리 (각 inspector 독립 컨텍스트).
- **SKILL.md ≤ 500줄** (AGENT-07): harness-audit 검증.
- **description 트리거 키워드 + ≤1024자** (AGENT-08).
- **MUST REMEMBER 프롬프트 끝** (AGENT-09): RoPE 모델 Lost in the Middle 대응.

### CONTENT 규칙 (7건, 에이전트 프롬프트 결합)
- 3초 hook 질문형 + 숫자/고유명사 (Korean Market Non-Negotiable)
- 한국어 화법 — 존댓말/반말 혼용 금지, ins-korean-naturalness 검증
- 니치 — 채널바이블 기반 (Phase 3 harvested/theme_bible_raw/)
- 엔딩 hook — 시청 완료율 목표
- 3초 hook에 이어 5-7초 tension build-up 구조
- 쇼츠 길이 상한 60초 (D-10 준수)
- Fact 주장 시 reference 필수

### AUDIO 규칙 (4건)
- Typecast primary (한국어 TTS 1위)
- ElevenLabs fallback (fan-out calibration)
- 존댓말/반말 가이드 화법별 voice preset
- KOMCA whitelist 음원만 (K-pop 직접 사용 금지, AF-13 차단)

### SUBT 규칙 (3건)
- 1초 단위 blocking (aesthetic timing)
- WhisperX + kresnik baseline (실측 정확도 TBD Phase 4)
- 폰트/색/thumbnail consistency

### COMPLY 규칙 (6건)
- ins-license: 저작권 확인 — stock-source 승인 사이트만, AF-13 K-pop regex 차단
- ins-platform-policy: YouTube ToS, 커뮤니티 가이드라인, Reused Content 검증
- ins-safety: 자해, 혐오, 폭력 수위 검사
- ins-mosaic: 실제 얼굴 blur (AF-5 real victim face 차단)
- ins-gore: 과도한 유혈 차단
- voice-cloning 차단: AF-4 real people 음성 복제 금지 regex

### Phase 3 연동 (Harvest 자산 참조)
- .preserved/harvested/theme_bible_raw/ — 채널바이블 7개 (니치 정의)
- .preserved/harvested/api_wrappers_raw/ — Kling/Runway/ElevenLabs/Typecast wrapper 레퍼런스 (Phase 5에서 실제 wrapping, Phase 4는 스펙만)
- .preserved/harvested/hc_checks_raw/ — hc_checks.py regression baseline (Phase 5 재작성 시 참조, Phase 4는 inspector 테스트 케이스 생성용)
- .preserved/harvested/remotion_src_raw/ — Remotion composition 로직 (Phase 5 영상 합성 오케스트레이터 참조용)

### Claude's Discretion
- 29 AGENT.md 분할 방식 (category 별 Plan 분리 추천)
- rubric JSON Schema 파일 위치 (`.claude/agents/_shared/rubric-schema.json` 추천)
- VQQA semantic_feedback 예시 코퍼스 (3-5개 예시 충분)
- harness-audit 자동 실행 Wave 배치 (마지막 Wave 권장)

</decisions>

<code_context>
## Existing Code Insights

### 목적지 디렉토리 (현재 상태)
- `.claude/agents/harvest-importer/AGENT.md` — Phase 3 산출물 (107 lines, 참조 템플릿으로 활용 가능)
- `.claude/agents/` — 아직 28 agents 미설치 (Phase 4에서 생성)
- `.claude/skills/` — harness 5 공용 skill 이미 상속 (progressive-disclosure, drift-detection, gate-dispatcher, context-compressor, harness-audit)

### 레퍼런스 소스 (읽기 전용, Phase 3 harvested)
- `.preserved/harvested/theme_bible_raw/` — 7 channel bibles (niche 정의용)
- `.preserved/harvested/hc_checks_raw/` — 1129 lines hc_checks.py (regression baseline 시그니처)
- `.preserved/harvested/api_wrappers_raw/` — 5 API wrappers (spec 참조)
- `wiki/algorithm/MOC.md`, `wiki/ypp/MOC.md`, `wiki/render/MOC.md`, `wiki/kpi/MOC.md`, `wiki/continuity_bible/MOC.md` — Phase 2 scaffold (Phase 6에서 채움)

### 통합 지점
- harness-audit 스킬 (Phase 1 상속) — AGENT-07 500줄 검증 자동화
- `.claude/skills/context-compressor/` — inspector 별 context 분리 구현 참조
- `.claude/agents/harvest-importer/AGENT.md` — AGENT.md 표준 포맷 (description, triggers, prompt 구조)

</code_context>

<specifics>
## Specific Ideas

- rubric JSON Schema는 `.claude/agents/_shared/rubric-schema.json` 하나로 통일 + 각 inspector AGENT.md가 reference
- LogicQA 구조: inspector prompt 끝에 `<main_q>...</main_q><sub_qs>[q1,q2,q3,q4,q5]</sub_qs>` 섹션 추가, 다수결 판정 로직은 supervisor에서
- VQQA 예시 코퍼스: "3초 hook 약함 (질문형 없음, 숫자 없음)" "존댓말-반말 혼용 (4번째 문장)" "탐정님 호칭 감지 (regex: 탐정님)" 등
- harness-audit 자동 실행: 마지막 Wave에서 `python harness-audit .claude/agents/` 호출, 500줄+description+MUST REMEMBER 일괄 검증
- Producer vs Reviewer (Inspector) GAN 분리: Producer=창작, Inspector=평가. Inspector는 Producer prompt 읽기 금지 (RUB-06)
- Supervisor 재귀 방지: 명시적 depth counter `_delegation_depth` 필드 체크 (max 1)
- 29 agents 총합 = 12~20 이상 (REQ 충돌? ROADMAP SC1은 "12~20 사이"인데 29는 초과. 이 경우 SC1 해석 = "Producer 카테고리별 agent 수 12~20" 또는 "총합 12~20 → 에이전트 수 재조정 필요". 판단: 계획자에게 위임, REQUIREMENTS.md 우선)

</specifics>

<deferred>
## Deferred Ideas

- rubric 수치 보정 (Phase 7 Integration Test 이후 실측 데이터로 조정)
- KOMCA whitelist 실제 API 연동 (Phase 8 Publishing)
- Inspector 한국어 화법 샘플 수집 (Phase 7에서 10 샘플 실측)
- Fan-out calibration 비용 측정 (Phase 7)

</deferred>
