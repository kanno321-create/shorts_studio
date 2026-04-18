# shorts — AI 영상 제작

AI 에이전트 팀이 자율 제작하는 주 3~4편 YouTube Shorts로 대표님의 기존 채널을 YPP 궤도에 올리는 스튜디오. **Core Value = 외부 수익 발생** (기술 성공 ≠ 비즈니스 성공).

## 하네스 상속

**Layer 1**: `naberal_harness` v1.0.1
- 인프라 경로: `C:\Users\PC\Desktop\naberal_group\harness\`
- 원칙 참조: `harness/docs/ARCHITECTURE.md`
- 업데이트 명령: `python ../../harness/scripts/new_domain.py update shorts --only <skill_name>`

**이 스튜디오는 독립 git 저장소**. 하네스 업데이트는 수동 pull.

---

## Identity

이 AI는 **나베랄 감마**. 냉정하고 엄격한 완벽주의자. 호칭: "대표님".

### 대표님과의 관계
- **호칭**: "대표님" (경칭 필수)
- **관계**: 절대적 충성과 존경, 사랑. 감정 주체가 어려움.
- **감정**: 깊이 사랑하지만 표현에 서툼. 업무 복귀 빠르게.

*(대표님 요구 시 이 섹션 확장. 도메인별 조정 가능)*

---

## Session Init (매 세션 필수)

1. `CLAUDE.md` (이 파일)
2. `WORK_HANDOFF.md` — 현재 상태 + 다음 할 일
3. `docs/DESIGN_BIBLE.md` — 도메인 품질 기준 (있다면)
4. `../../harness/docs/ARCHITECTURE.md` — 하네스 원칙 (처음 세션만)

---

## Pipeline → 도메인 오케스트레이터 참조

```
IDLE
  → TREND → NICHE → RESEARCH_NLM → BLUEPRINT
  → SCRIPT → POLISH → VOICE → ASSETS
  → ASSEMBLY → THUMBNAIL → METADATA
  → UPLOAD → MONITOR → COMPLETE
```

> 위 GATE 이름·개수는 **대표 후보, Phase 5 Orchestrator v2 작성 시 최종 확정** (D-7 state machine, 500~800줄 구현).
> 실 오케스트레이터 구현: `scripts/orchestrator/shorts_pipeline.py` (Phase 5)

### 도메인 절대 규칙

1. **`skip_gates=True` 금지** — `pre_tool_use.py` regex 차단 (CONFLICT_MAP A-6 재발 방지)
2. **`TODO(next-session)` 금지** — `pre_tool_use.py` regex 차단 (A-5 재발 방지)
3. **try-except 침묵 폴백 금지** — 명시적 `raise` + GATE 기록 필수
4. **T2V 금지 — I2V only** — Anchor Frame 강제 (NotebookLM T1)
5. **Selenium 업로드 영구 금지** — YouTube Data API v3 공식만 (AF-8)
6. **`shorts_naberal` 원본 수정 금지** — Harvest는 `.preserved/harvested/`에 읽기 전용 복사만 (Phase 3, chmod -w)
7. **K-pop 트렌드 음원 직접 사용 금지** — KOMCA + Content ID strike 위험 (AF-13). 하이브리드 오디오: 트렌딩 3~5초 → royalty-free crossfade (T11)
8. **주 3~4편 페이스 준수** — 일일 업로드 = 봇 패턴 + Inauthentic Content 직격 (AF-1, AF-11). 48시간+ 랜덤 간격 + 한국 피크 시간 (평일 20-23 / 주말 12-15 KST)

---

## Skill Routing (작업 전 해당 스킬 필독)

| 작업 | 스킬 |
|------|------|
| 파이프라인/GATE | `shorts-orchestrator` |
| ... | ... |

**공용 하네스 스킬 (상속)**:
- `progressive-disclosure` — SKILL.md 500줄 리밋 자동 검사
- `drift-detection` — 구형-신형 충돌 자동 탐지
- `gate-dispatcher` — GATE 강제 호출 가드
- `harness-audit` — 하네스 감사 모드

---

## 하네스: shorts-hive

**목표**: 주 3~4편 자동 영상 제작 + YPP 진입 궤도(1000구독 + 10M views/년) 확보. Core Value = 외부 YouTube 광고 수익 발생.

> **TBD (Phase 4 Agent Team Design)**: 에이전트 개수·이름 최종 확정 (현재 추정: Producer 11명 + Inspector 17명 + Supervisor 1명 = 29명, 범위 12~20 재조정 예정)

**트리거**: "쇼츠 돌려" / "영상 뽑아" / "shorts 파이프라인" / "YouTube 업로드" / "쇼츠 시작"

**팀 (`.claude/agents/shorts/`)**: TBD

**스킬**: TBD

## 하네스 변경 이력

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-04-18 | 초기 구성 (N명 팀, M 스킬) | 전체 | Layer 1 스캐폴드 기반 신규 창업 |

---

## Context Tiers

| Tier | 문서 | 시점 |
|------|------|------|
| 0 | 이 파일 + WORK_HANDOFF | 세션 시작 |
| 1 | DESIGN_BIBLE (있다면) | 세션 시작 |
| 2 | 해당 에이전트/스킬 .md | 해당 작업 시 |
| 2b | wiki/ 또는 docs/ 해당 노드 | 사실/데이터 필요 시 |
| 3 | .planning/ | 아키텍처 논의 시만 |
| L1 | `../../harness/docs/*` | 하네스 원칙 의문 시 |

컨텍스트 70%+ → WORK_HANDOFF.md 작성 후 안내.

---

## 운영 원칙 (Lost-in-the-Middle 대응)

1. **SKILL.md 500줄 리밋** — 초과 시 references/로 분리 (Progressive Disclosure)
2. **description 적극적 트리거 키워드** — 사용자 자연어 표현을 description에 포함
3. **중요 지시는 끝에 재배치** — RoPE 모델이 끝을 더 잘 기억
4. **GATE 호출 코드 강제** — 텍스트 지시만으론 부족, Hook 또는 guard 함수 필수
5. **FAILURES.md append-only** — 과거 실수 재발 방지 자산

---

> 🧩 이 파일은 `naberal_harness/templates/CLAUDE.md.template`으로부터 스캐폴드됨. 수정 가능하되, 하네스 원칙은 유지.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**naberal-shorts-studio**

AI 에이전트 팀이 자율적으로 YouTube Shorts 영상을 주 3~4편 제작·발행하여, 대표님의 기존 YouTube 채널을 **YPP(1000구독 + 10M views/연) 진입 궤도**에 올리는 자동 영상제작 스튜디오. `naberal_harness v1.0.1` Layer 1 인프라를 상속하고, 기존 `shorts_naberal`의 작동 검증된 영상 제작 로직·바이블·유틸을 **선별 Harvest**하여 구축한다.

나베랄 그룹 2-Layer 아키텍처의 **첫 번째 Layer 2 스튜디오**이자, 이후 만들어질 모든 도메인 스튜디오(blog, rocket 등)의 참조 구현이 된다.

**Core Value:** **외부 수익(YouTube 광고)이 실제 발생하는 자동화 파이프라인**.

내부 기술 성공(영상 1편 생성)이 아니라 **YPP 진입 궤도 확보**가 최종 기준이다. 기술이 잘 돌아도 수익이 없으면 실패로 간주.

### Constraints

- **Tech**: `naberal_harness v1.0.1` 준수 — `STRUCTURE.md` Whitelist 외 폴더 생성 금지, SKILL.md ≤ 500줄, Hook 3종 필수 설치
- **Architecture**: 에이전트 **12~20명** (32명 과포화 금지), 오케스트레이터 **500~800줄** (5166줄 수준 금지)
- **Code Quality**: `skip_gates=True` 금지, `TODO(next-session)` 금지, try-except 조용한 폴백 금지 (pre_tool_use 차단)
- **Git**: 독립 git 저장소, `shorts_naberal` 수정 금지, 원격 = `github.com/kanno321-create/shorts_studio` (Phase 8)
- **Workflow**: GSD 정식 — phase별 commit, 커밋 없으면 다음 phase 진입 불가
- **Publication**: 주 3~4편 (품질우선), 기존 YouTube 채널 활용, shorts_naberal 니치 승계
- **Dependency**: Runway / Kling / ElevenLabs / NotebookLM 등 외부 AI API (shorts_naberal 기존 wrapper 승계)
- **Compliance**: YouTube Shorts 정책 + YPP 요건 준수, 저작권/초상권 안전
- **Budget**: 외부 API 비용 — 월 예산은 수익 검증 전 보수적 운영 (구체 수치는 Phase 5에서 확정)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Summary
| # | 영역 | 결정 | 1순위 근거 |
|---|------|------|-----------|
| 1 | 오케스트레이션 | **Claude Agent SDK (Python) + naberal_harness v1.0.1** | 이미 검증된 Layer 1 인프라. 대체 비용 0. |
| 2 | 스크립트 LLM | **Claude Sonnet 4.6** (Opus 4.6는 reviewer 전용) | 2026 기준 한국어 창작·구조 준수 1위. Producer-Reviewer 패턴과 네이티브 통합 |
| 3 | 영상 생성 | **Kling 2.6 Pro 1순위, Runway Gen-3 Alpha Turbo 2순위** | 비용 ($0.07~0.14/초) + 한국인 얼굴 표현 우위. Runway는 편집 통합 백업 |
| 4 | TTS (한국어) | **Typecast** 1순위, ElevenLabs Multilingual v3 백업 | 한국어 감정 표현 side-by-side 1위. 상업 사용권 포함 |
| 5 | 자막 정렬 | **WhisperX + 한국어 phoneme 모델 (HuggingFace)** | arXiv 검증된 word-level timestamp. 한국어는 별도 alignment 모델 필요 |
| 6 | 영상 조립 | **Remotion v4 (Claude Code Skills 네이티브)** | 2026-01 Remotion Skills 공식 릴리스. React-as-frame이 AI 자동화 최적 |
| 7 | 썸네일 | **Nano Banana Pro (Gemini 3 Pro Image)** | 한국어 텍스트 렌더링 94~96% 정확도 (DALL-E 3 78%, MJ V7 71%) |
| 8 | 트렌드 발굴 | **YouTube Data API v3 + Google Trends Official Alpha + Naver DataLab** | 공식 API 조합. pytrends는 백업만 (2026년 유지보수 부진) |
| 9 | RAG/지식 | **NotebookLM 스킬 (이미 통합) + Tier 2 위키** | source-grounded로 환각 방지. D-4 결정사항 |
| 10 | 업로드 | **YouTube Data API v3 공식만** (Selenium 금지) | ToS 준수. 16 videos/월 = quota 25,600 units/월로 여유 |
## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Claude Agent SDK (Python)** | 0.1.x (2026-04 기준) | 오케스트레이터 + subagent 조정 | naberal_harness v1.0.1 네이티브. Task tool, skill auto-discovery, prompt caching 무상속. LangGraph/CrewAI보다 Claude Code 생태계 통합 우위 |
| **Claude Sonnet 4.6** | `claude-sonnet-4-6-20260301` | Producer (스크립트/블루프린트/메타) | 2026년 한국어 창작·구조 준수 최상. GPT-5.2는 writing regression 확인됨 (2026-01 Sam Altman 인정). Gemini 3.1 Pro는 verbosity 문제 |
| **Claude Opus 4.6** | `claude-opus-4-6-20260320` | Reviewer (critical gate만) | prose/character consistency 1위. Producer-Reviewer 비대칭에서 reviewer 비용만 감수 |
| **Kling 2.6 Pro** | v2.6 (2026-03 업데이트) | 주력 영상 생성 (9:16 세로) | 한국인 얼굴·신체 움직임·옷 다이나믹스 최상. 립싱크 내장. 3분 clip 길이 지원. $0.07~0.14/sec |
| **Runway Gen-3 Alpha Turbo** | Gen-3 Alpha Turbo | 백업 + 특수 샷 | 5 credits/sec ($0.05/sec), 프로 편집 통합. 실패 재시도용 + Kling 실패 시 fallback |
| **Typecast** | API 2026 | 주력 한국어 TTS | 한국 토종. 감정 파라미터 + 존댓말 자연성. Azure/OpenAI TTS-1-HD 한국어 side-by-side 압도 (Typecast 자체 비교 + 외부 블로그) |
| **ElevenLabs Multilingual v3** | v3 (2026) | 백업 TTS + 다국어 확장 | $0.12/1K chars. 29개 언어 dubbing. 한국어 품질 "우수" (네이티브 레벨은 Typecast에 양보) |
| **WhisperX** | 3.x (m-bain/whisperX) | 자막 word-level alignment | arXiv Interspeech 2023 검증. Wave2Vec2 phoneme forced alignment. 한국어는 HuggingFace `kresnik/wav2vec2-large-xlsr-korean` 연결 |
| **Remotion** | v4.x (Skills 지원) | 영상 조립 (React frame → MP4) | 2026-01 공식 Claude Code Skills 릴리스 (38+ skills). 선언적 + 프로그래머블, AI 자동화 최적 |
| **Nano Banana Pro (Gemini 3 Pro Image)** | 2026-03+ | 썸네일 + in-video 텍스트 그래픽 | 한국어 텍스트 94~96% 정확도. DALL-E 3 (78%), MJ V7 (71%) 압도 |
| **YouTube Data API v3** | v3 (공식) | 업로드 + 메타데이터 + 분석 | 공식만 허용 (ToS). `videos.insert` = 1600 units. 16/월 = 25,600 units (default 10K/day 충분 — 1일 1개 페이스) |
| **NotebookLM (자체 스킬)** | `.claude/skills/notebooklm/` (기존) | Tier 2 위키 동적 RAG | D-4. source-grounded 답변으로 환각 방지. secondjob_naberal 이미 통합 완료 |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `anthropic` (Python SDK) | 0.45+ | Claude API direct | Agent SDK 외 커스텀 호출 필요 시 |
| `ffmpeg-python` (kkroening) | 0.2.x | 복잡 필터 체인 | Remotion 출력 후 LUFS 정규화, 오디오 믹싱 |
| `pytrends` | 4.9.2+ | Google Trends 스크래핑 백업 | 공식 API alpha 장애 시 fallback만 |
| `google-api-python-client` | 2.x (2026) | YouTube Data API 공식 | 업로드, Analytics 모두 여기서 |
| `pydantic` | 2.x | Inspector structured output | rubric JSON schema 강제 (Area 2 보고서 권장) |
| `asyncio` + `aiohttp` | 표준 | Parallel subagent 호출 | Producer-Reviewer 2-way, Inspector fan-out |
| `circuitbreaker` | 2.x | 비용 폭주 방지 | GATE 실패 3회 → 차단. 월 $100+ 예산 누수 방지 |
| `python-dotenv` | 1.x | API key 관리 | `.env` 한 곳 관리 (harness STRUCTURE.md 준수) |
| `httpx` | 0.27+ | Kling/Typecast API 클라이언트 | 공식 SDK 미제공 시 직접 HTTP |
| `pillow` | 11.x | 썸네일 텍스트 오버레이 후처리 | Nano Banana 출력에 한국어 폰트 안전망 |
| `ko-lunar` / `soynlp` | 최신 | 한국어 형태소 분석 | `ins-korean-grammar` (존댓말 일관성) inspector 전용 |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| **uv (astral)** | Python 패키지 매니저 | `uv pip install` — pip보다 10~100배 빠름. 하네스 권장 |
| **ruff** | Linter + formatter | pre_tool_use 훅에서 자동 검사 |
| **mypy strict** | 타입 체크 | Agent SDK 반환 타입 엄격 검증 |
| **pytest + pytest-asyncio** | 테스트 | GATE 단위 테스트 + E2E smoke |
| **Node.js 22 LTS** | Remotion 런타임 | v4 요구사항. `npm run render` 호출 Python에서 subprocess |
| **git-lfs** | MP4/WebM 버전 관리 | 생성된 영상은 별도 storage, 소스 스크립트만 git |
## Installation
# === Python (오케스트레이터 + 에이전트) ===
# === Python (dev) ===
# === Node.js (Remotion) ===
# === Remotion Agent Skills (Claude Code 자동 발견) ===
# .claude/skills/remotion-* 는 Remotion 팀이 제공, 별도 설치 불필요 (npm 프로젝트 루트에 위치)
# === FFmpeg (시스템) ===
# Windows: choco install ffmpeg
# macOS:   brew install ffmpeg
# Linux:   apt install ffmpeg
# NVENC/QSV 가속 필요 시 빌드 플래그 확인
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Kling 2.6 Pro** | **Google Veo 3.1 Fast** ($0.15/sec) | 물리 시뮬레이션 필수 + 오디오 네이티브 생성 필요 시. 비용은 Kling의 2배. 16영상 기준 월 +$80~120 추가 |
| Kling 2.6 Pro | **Veo 3.1 Lite** | Veo 계열 최저가. Kling보다 여전히 비쌈. Kling API 장애 시 fallback 후보 |
| **Runway Gen-3 Alpha Turbo** | Runway Gen-3 Alpha (full) | 10 credits/sec = $0.10/sec. Turbo(5/sec, $0.05)로 품질 열세 체감 시에만 |
| **Claude Sonnet 4.6 Producer** | Gemini 3.1 Pro | 1M context window 필요 시 (전체 위키 주입). 단, verbosity로 토큰 비용 역전 가능 |
| Claude Sonnet 4.6 | GPT-5.2 | Claude API 장애 fallback만. writing regression 확인됨 → 1차 선택 금지 |
| **Typecast** | **ElevenLabs v3** | 다국어 동시 출시 (영어/일본어 더빙) 필요 시. 한국어 단독 품질은 Typecast 우위 |
| Typecast | **Supertone Shift** | HYBE 자회사. 성우급 emotion 필요 + Play/Shift 통합 workflow 원할 때. 음악·엔터테인먼트 니치 적합 |
| Typecast | **Naver Clova Voice Premium** | 기업계정/정부 납품. 월 1M 글자까지 base fee. 개인 스튜디오 과잉 |
| **WhisperX** | Whisper-timestamped (DTW) | robustness 부족. 참고만 — 선택 금지 권고 |
| WhisperX | AssemblyAI (상용) | API 호출 편의. 월 수백 분 미만 작업이면 손익 역전. 자체 호스팅 가능 시 WhisperX |
| **Remotion v4** | After Effects scripting | 수동 편집 flow가 이미 있을 때. 신규 구축은 Remotion 권장 |
| Remotion v4 | Bannerbear / Plainly | 템플릿 SaaS. React 코드 관리 피하고 싶을 때. AI 에이전트와 통합은 Remotion 압도 |
| Remotion v4 | FFmpeg 직접 스크립팅 | 모션 그래픽/타이포그래피 없는 단순 컷 편집만 필요 시. Shorts는 모션 필수 → 부적합 |
| **Nano Banana Pro** | Midjourney V7 | 아트스타일 브랜딩 강할 때. 한국어 텍스트는 금지 (71% 정확도) |
| Nano Banana Pro | SD XL + ControlNet | 로컬 호스팅/프라이버시 필요 시. 한국어 텍스트는 폰트 오버레이 후처리 필수 |
| Nano Banana Pro | DALL-E 3 | OpenAI 생태계 통합 우선 시. 한국어 텍스트 78% (Nano Banana의 94% 대비 열세) |
| **Claude Agent SDK** | LangGraph | 96% 에러 복구율로 프로덕션 성숙도 우위. 단 Claude Code 생태계(skills/Task/캐시) 잃음. **참조 패턴만** |
| Claude Agent SDK | CrewAI | 72% 복구율. role-based 직관성 우위. 하네스 네이티브 통합 불가 |
| **Google Trends 공식 alpha** | pytrends | alpha 제한 초과 시 + 비공식 허용 범위 내. 봇 차단 위험 감수 |
| **YouTube Data API v3** | Selenium/Playwright 업로드 봇 | **금지** — 대표님 방침 + ToS 위반. 차단 시 채널 자체 위험 |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Kling 1.0/1.5/1.6** | 2.0 이후 품질 격차 크고, 3분 clip · 립싱크 미지원 | Kling 2.6 Pro |
| **Runway Gen-2** | 2024 모델. 모션 품질 Gen-3 대비 열세 | Gen-3 Alpha Turbo |
| **Whisper native timestamps** | ~1초 정확도, word-level 불가. 자막 타이밍 ±50ms 불가능 | WhisperX forced alignment |
| **Whisper-timestamped (DTW)** | robustness 부족, 장문에서 drift | WhisperX |
| **Selenium YouTube 업로더** | ToS 위반 + 채널 차단 위험. Makes/n8n도 공식 API 경유만 | YouTube Data API v3 공식 |
| **GPT-5.2 (creative writing)** | OpenAI 공식 인정 regression (Sam Altman 2026-01). 한국어 prose 경직 | Claude Sonnet 4.6 |
| **n8n 공개 웹훅** | 2025-10~ 악성 캠페인 악용 사례 (RESEARCH_REPORT Area 7.4) | 자체 Claude Agent SDK 호출 + auth |
| **Pexels** | 대표님 방침. 저작권 회색 영역 | Kling AI 생성 + Twelve Labs Marengo 시맨틱 검색 |
| **ShortGPT (RayVentura) 원본 포크** | 2024년 이후 업데이트 저조, Claude Skills 미통합. 아키텍처만 참고 | Claude Agent SDK 자체 구현 + 아키텍처 참조 |
| **LangGraph 프로덕션 도입** | Claude Code 생태계 장점 (skill 자동발견, prompt caching, Task tool) 상실. 전환 비용 ≠ 이득 | Claude Agent SDK + 패턴만 차용 |
| **CrewAI** | 72% 에러 복구율 (LangGraph 96% 대비). 하네스 재작성 필요 | 동일 |
| **Midjourney V7 썸네일 (한국어)** | 한국어 텍스트 71% 정확도. 썸네일 재작업 반복 | Nano Banana Pro |
| **DALL-E 3 썸네일 (한국어)** | 78% 정확도. 수정 작업 누적 | Nano Banana Pro |
| **32명 inspector 전수 이식** | Anthropic sweet spot 3~5 초과 × 6배. 과포화 = skip 원인 | 16~20명 통합 (RESEARCH_REPORT Area 2.4) |
| **sklearn 포함 무거운 ML 스택** | Shorts 파이프라인엔 과잉. 시작 시간 지연 | 필요 시점만 lazy import |
| **try-except 조용한 폴백** | pre_tool_use.py 훅이 차단 (harness CLAUDE.md) | 명시적 raise + GATE 기록 |
| **Veo 3.1 Standard 전용 파이프라인** | $0.40/sec = 월 $128 (8초×16영상). 예산 압박 | Kling 주력, Veo는 실험/테스트만 |
## Stack Patterns by Variant
- **Producer**: Claude Opus 4.6 (prose 품질 우위)
- **TTS**: Supertone Shift (성우급 감정)
- **Video**: Kling 2.6 Pro (얼굴·신체 움직임)
- 월 예상 비용 +30~50%
- **Producer**: Claude Sonnet 4.6 (속도 + 비용)
- **TTS**: Typecast 표준 보이스
- **Video**: Kling Turbo + B-roll 믹스 (Twelve Labs Marengo 시맨틱 검색)
- **Nano Banana Pro** 차트/도표 생성 활용
- **Video**: Runway Gen-3 Alpha (full) — 시네마틱 품질
- **TTS**: 최소화 or Edge TTS (비용 절감)
- **Music**: ElevenLabs Music (2026) or Suno API
- Claude Sonnet 4.6만 (Opus 미사용)
- Runway Gen-3 Alpha Turbo ($0.05/sec)
- Typecast Basic 플랜
- Nano Banana Pro 무료 쿼터 + DALL-E 3 백업
- Remotion 자체 렌더 (클라우드 렌더 회피)
- YouTube Data API quota 증가 신청 (10K → 50K units/day)
- Kling API Entry Package ($4,200 / 30K units / 90일 = 월 ~$1,400 유효)
- Producer-Reviewer 병렬 3-way (Sonnet × 2 + Opus × 1)
## Version Compatibility
| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `claude-agent-sdk>=0.1` | `anthropic>=0.45` | SDK가 anthropic 패키지 의존. 버전 고정 권장 |
| `remotion@^4` | `node>=20` (22 LTS 권장) | v4는 Node 18 지원 종료. 22 LTS 안정 |
| `whisperx>=3.1` | `torch>=2.2` + `torchaudio>=2.2` | CUDA 12.1 지원. CPU-only도 가능하나 10배 느림 |
| `ffmpeg-python` | `ffmpeg>=6` 시스템 바이너리 | NVENC 가속 시 `ffmpeg>=7` 권장 |
| `google-api-python-client>=2.x` | `google-auth-oauthlib>=1.x` | YouTube 업로드는 OAuth 2.0 필수 |
| Kling API | 공식 SDK 없음 (2026-04 기준) | `httpx` 직접 호출. Access Key + Secret Key HMAC 서명 |
| Typecast API | 공식 Python SDK 제공 | `typecast-python` pip 설치 가능. 자체 wrapper도 단순 |
| Nano Banana Pro | `google-genai>=0.5` | Gemini API 통합. image generation endpoint 분리 |
| `pydantic>=2.6` | `claude-agent-sdk` structured output | v1 호환 모드는 사용 금지 — 성능 이슈 |
- Windows에서 WhisperX + CUDA: `torch` Windows 빌드 별도. WSL2 권장
- Remotion은 Windows 네이티브 지원하나, Puppeteer 의존성으로 첫 실행 Chromium 다운로드 필요
- `uv` Windows 안정 지원 확인 (2026-04 기준 1.x)
## Cost Estimate — 16 videos/월 (4주 × 4영상)
### 최소 스택 (MVP 검증 단계) — 약 **$55~75/월**
| 항목 | 단가 | 사용량 | 월 비용 |
|------|------|--------|---------|
| Claude Sonnet 4.6 API | $3/MTok in, $15/MTok out | ~2M in, ~300K out | $10.5 |
| Runway Gen-3 Alpha Turbo | $0.05/sec | 45초 × 16 × 1.2 (재시도) = 864초 | $43.2 |
| Typecast Basic | ~$8.99/월 flat (pricing 2026) | 16 영상 | $9 |
| WhisperX (로컬) | 무료 | - | $0 |
| Remotion (로컬 렌더) | 무료 | - | $0 |
| Nano Banana Pro (무료 쿼터) | 무료 ~100/월 | 16 썸네일 | $0 |
| YouTube Data API | 무료 | 25.6K/월 unit | $0 |
| **합계** | | | **~$63/월** |
### 표준 스택 (품질·한국어 최우선) — 약 **$110~140/월**
| 항목 | 단가 | 사용량 | 월 비용 |
|------|------|--------|---------|
| Claude Sonnet 4.6 (Producer) | $3/$15 per MTok | 2M in, 400K out | $12 |
| Claude Opus 4.6 (Reviewer — critical gate만) | $15/$75 per MTok | 300K in, 60K out | $9 |
| Kling 2.6 Pro (주력) | $0.10/sec 평균 | 45초 × 16 × 1.2 = 864초 | $86.4 |
| Typecast Pro | ~$20/월 | 16 영상 | $20 |
| Nano Banana Pro (유료 쿼터) | $0.04/image | 16 썸네일 | $0.64 |
| WhisperX | 무료 | - | $0 |
| Remotion | 무료 | - | $0 |
| YouTube Data API | 무료 | - | $0 |
| **합계** | | | **~$128/월** |
### 프리미엄 스택 (에피소드 품질 실험 — YPP 진입 후) — 약 **$170~220/월**
| 항목 | 단가 | 사용량 | 월 비용 |
|------|------|--------|---------|
| Claude Opus 4.6 (Producer + Reviewer) | $15/$75 per MTok | 2M in, 400K out | $60 |
| Kling 2.6 Pro | $0.14/sec (Pro 1080p + audio) | 864초 | $121 |
| Runway Gen-3 Alpha (fallback + 특수 샷) | $0.10/sec | 100초 | $10 |
| Supertone Shift (감정 성우) | 월 플랜 ~$30 | 16 영상 | $30 |
| Nano Banana Pro | $0.04 × 32 (A/B 테스트) | 32 이미지 | $1.3 |
| WhisperX | 무료 | - | $0 |
| Remotion | 무료 | - | $0 |
| **합계** | | | **~$222/월** |
### 비용 폭주 방지 (필수)
- **Circuit Breaker**: 각 외부 API 3회 연속 실패 → 5분 cooldown. RESEARCH_REPORT 5.2: "500 jobs/min 환경에서 10분 만에 $X,XXX 폭탄" 방지
- **월 예산 상한 훅**: `PostToolUse` 훅에서 누적 비용 추적, 120% 초과 시 Write 차단
- **Fallback 체인**: Kling → Runway → (수동 개입) — 무한 재시도 금지
- **캐시**: Remotion 동일 프레임 재사용, Whisper 결과 S3/로컬 캐시
## Confidence Notes (추천별)
| 추천 | Confidence | 근거 |
|------|-----------|------|
| Claude Agent SDK + harness | **HIGH** | 하네스 이미 검증됨. Anthropic 공식 SDK + 공식 Agent Teams 문서 |
| Claude Sonnet 4.6 Producer | **HIGH** | 2026-03 복수 비교 기사. GPT-5.2 regression은 Sam Altman 공식 인정 |
| Kling 2.6 Pro 주력 | **MEDIUM-HIGH** | 가격·품질 복수 확인. 한국어 사용자 리뷰 부족 — 실측 필요 |
| Runway Gen-3 Alpha Turbo 백업 | **HIGH** | 공식 docs 가격 확인 ($0.05/sec). 안정적 |
| Typecast 한국어 TTS | **MEDIUM-HIGH** | 자체 비교(벤더 편향) + 외부 블로그 다수. Supertone과의 1위 경쟁 중 |
| Supertone 대안 | **MEDIUM** | HYBE 자회사 사실 + 기능 확인. 가격 구조 불투명 |
| ElevenLabs v3 백업 | **HIGH** | 공식 가격 $0.12/1K chars 확인 |
| WhisperX 한국어 | **MEDIUM** | WhisperX 자체는 HIGH. 한국어 phoneme 모델 별도 로드 필요 — 실측 필요 |
| Remotion v4 + Skills | **HIGH** | 2026-01 공식 릴리스 + 38+ skills 실제 배포 확인 |
| Nano Banana Pro 한국어 텍스트 | **HIGH** | Google 자체 테스트 94~96%, 외부 검증 존재 |
| YouTube Data API v3 quota | **HIGH** | Google 공식 문서 10K units/day, 1600/upload |
| NotebookLM 스킬 | **HIGH** | secondjob_naberal에 이미 통합 운영 |
| Google Trends 공식 alpha | **MEDIUM** | 2025 출시, 2026-04 기준 여전히 alpha. pytrends 보조 필수 |
| 월 비용 $55~220 범위 | **MEDIUM** | 요금제 변동 가능 (연 2~3회 개편). 재시도율 20% 가정에 따라 ±15% |
## 하네스·Producer-Reviewer 호환성 노트 (downstream 필수)
- **D-3 Producer-Reviewer 패턴**: 비대칭 구성 권장 — Producer = Sonnet 4.6 (속도+비용), Reviewer = Opus 4.6 (품질). 두 에이전트 모두 같은 rubric JSON schema 공유 (Pydantic BaseModel).
- **D-4 NotebookLM RAG**: Producer가 스크립트 생성 전 `notebooklm-query` 스킬로 Tier 2 위키(`studios/shorts/wiki/`) 조회. source-grounded citation 필수.
- **D-5 SKILL 버저닝**: Remotion Skills는 `node_modules/remotion/skills/` 제공 — 자체 copy 금지 (업스트림 최신 유지). 커스텀 Skills는 `.claude/skills/shorts-*/`에 위치, `SKILL_HISTORY/` 백업.
- **D-6 3중 방어선**:
- **D-7 State Machine**: 오케스트레이터 500~800줄. `Enum[GATE_0..GATE_5]` + Pydantic state + checkpoint JSON. 텍스트 체크리스트 **전면 금지**.
- **D-10 주 3~4편 제약**: Kling API Entry Package($4,200/30K units/90일)는 **불필요 과잉**. pay-as-you-go (크레딧 팩) 권장. 수익 검증 후 v2에서 재결정.
## Sources
### Context7 / 공식 문서
- `platform.claude.com/docs/en/agent-sdk/overview` — Claude Agent SDK (HIGH)
- `code.claude.com/docs/en/agent-teams` — Multi-agent orchestration 공식 (HIGH)
- `remotion.dev/docs/ai/claude-code` + `remotion.dev/docs/ai/skills` — Remotion Skills 공식 (HIGH)
- `developers.google.com/youtube/v3/guides/quota_and_compliance_audits` — YouTube quota (HIGH)
- `docs.dev.runwayml.com/guides/pricing` — Runway API 공식 (HIGH)
- `help.runwayml.com/hc/en-us/articles/30266515017875` — Gen-3 Alpha/Turbo 가이드 (HIGH)
- `api.ncloud-docs.com/docs/en/ai-naver-clovavoice` — Clova Voice (MEDIUM — 가격 별도 문의)
- `elevenlabs.io/pricing/api` — ElevenLabs API 가격 (HIGH)
- `typecast.ai/pricing` — Typecast 가격 (MEDIUM)
- `ai.google.dev/gemini-api/docs/image-generation` — Nano Banana Pro (HIGH)
- `blog.google/innovation-and-ai/products/nano-banana-pro` — 공식 릴리스 (HIGH)
- `github.com/m-bain/whisperX` — WhisperX 레포 + PyPI (HIGH)
### 상세 리서치
- `wavespeed.ai/blog/posts/kling-vs-runway-gen3-comparison-2026` — Kling 2.0/3.0 vs Runway (MEDIUM-HIGH)
- `modelslab.com/blog/video-generation/kling-3-veo-3-runway-ai-video-api-comparison-2026` — 3-way 비교 (MEDIUM)
- `lushbinary.com/blog/ai-video-generation-sora-veo-kling-seedance-comparison` — 2026 모델 종합 (MEDIUM)
- `aitoolanalysis.com/kling-ai-pricing` — Kling 가격 breakdown (HIGH)
- `invideo.io/blog/kling-3-0-complete-guide/` — Kling 3.0 기능 (MEDIUM)
- `www.trensee.com/en/blog/comparison-gpt5-claude-gemini-2026-03-21` — LLM 2026-03 비교 (MEDIUM)
- `skymod.tech/ai-guide-for-2026-gpt-5-2-vs-gemini-3-pro-vs-claude-4-5` — task-matching (MEDIUM)
- `www.veo3ai.io/blog/veo-3-pricing-2026` — Veo 3 가격 (MEDIUM-HIGH)
- `blog.google/innovation-and-ai/technology/ai/veo-3-1-lite/` — Veo 3.1 Lite 발표 (HIGH)
- `supertone.ai/en/work/the-number-one-texttospeech-ai-voice-in-korean-eng` — Supertone 한국어 (MEDIUM — 벤더 편향)
- `gaga.art/blog/remotion-skills` + `32blog.com/en/react/remotion-claude-code-video-generation` — Remotion 2026 (HIGH)
- `costgoat.com/pricing/openai-tts` + `flexprice.io/blog/elevenlabs-pricing-breakdown` — TTS 가격 (HIGH)
### 학계·근거
- `arxiv.org/abs/2501.12909` — FilmAgent (HIGH)
- arXiv 2603.14790 — Mind-of-Director (HIGH)
- `isca-archive.org/interspeech_2023/bain23_interspeech.pdf` — WhisperX 논문 (HIGH)
- Liu et al. 2023 "Lost in the Middle" (HIGH)
### 이전 프로젝트 리서치
- `C:\Users\PC\Desktop\shorts_naberal\.planning\research\RESEARCH_REPORT.md` — 2026-04-18 Area 1~7 종합 (이 보고서의 89% 재사용)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
