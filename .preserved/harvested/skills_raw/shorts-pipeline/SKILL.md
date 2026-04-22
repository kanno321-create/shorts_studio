---
name: shorts-pipeline
description: 쇼츠 영상 제작 파이프라인 아키텍처, 6-stage 흐름, Provider 시스템, 타이밍 싱크. 파이프라인 실행/수정/디버깅 시 반드시 참조.
metadata:
  tags: pipeline, orchestration, provider, timing, tts, stage
---

## When to use

파이프라인 관련 모든 작업 전에 이 스킬을 읽는다:
- orchestrate.py / harness.py / hc_checks.py 참조 시
  (**주의**: `run_pipeline_outsource_first` Python 단독 실행은 금지 — 메인 세션 Task() dispatch 필수. 아래 §Inspector Wiring Contract 참조)
- 새 에이전트 추가/수정 시
- TTS/영상소스/렌더 Provider 변경 시
- 타이밍 싱크 문제 디버깅 시
- 파이프라인 stage 순서 논의 시
- **검사관 게이트 관련 작업 — §Inspector Wiring Contract 반드시 준수**

---

## 🔴 최초공정 = NotebookLM 2-노트북 (쇼츠·롱폼 공통)

**쇼츠 제작의 시작도 shorts-researcher·shorts-scripter가 아니다.** 반드시 NLM 2개 노트북.
세션 70·77 대표님 확정. 1-노트북 방식은 컨텍스트 오염 → 2-노트북으로 발굴/제조 분리.

### Step 1: 사건 발굴 노트북 (주제 + 팩트)
**URL**: https://notebooklm.google.com/notebook/d9aa8c99-6b27-4797-b09a-8c3e509b1e11
- 역할: 채널 상황 맞춤 주제 선정 + 훅·반전·핵심 팩트 추출
- 에이전트: `producers/nlm-fetcher` (MCP 스킬) — 폴백은 `producers/researcher`

### Step 2: 대본 제조 노트북 (완성 대본)
**URL**: https://notebooklm.google.com/notebook/64bcab8f-b487-4089-a528-c243cc4b5382
- 역할: Step 1 팩트 + 채널 규칙 + 길이 사양으로 대본 생성
- 에이전트 체인: `nlm-fetcher` → `script-converter` → `script-polisher`
- 나베랄 역할 = **프롬프트 품질 설계** (리텐션/알고리즘/채널바이블 규칙을 프롬프트에 녹임). 대본 본문에는 손대지 않음

자세한 규약: `memory/reference_nlm_two_notebook_pipeline.md`.

---

## Pipeline Architecture (6-Stage Sequential)

```
주제 입력
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ Stage 1: RESEARCH  (NLM Step 1)                         │
│   nlm-fetcher → 사건 발굴 노트북 질의 → source.md         │
│   폴백: shorts-researcher (웹 크롤링, NLM 미사용 시만)     │
│   승인 게이트: 대표님 확인 후 다음 단계                     │
├─────────────────────────────────────────────────────────┤
│ Stage 2: BLUEPRINT                                      │
│   planner → blueprint.json                              │
│   도입부/본론/결론 구조 + 장면별 영상 지시                   │
├─────────────────────────────────────────────────────────┤
│ Stage 3: SCRIPT  (NLM Step 2)                           │
│   nlm-fetcher → 대본 제조 노트북 질의 → markdown          │
│   → script-converter → script.json                      │
│   → script-polisher (한국어 자연성·금지어·시그니처 교정)    │
│   폴백: shorts-scripter (NLM 실패 시만)                  │
│   승인 게이트: GATE 2 검사관 17명 병렬                     │
├─────────────────────────────────────────────────────────┤
│ Stage 4: ASSETS (parallel)                              │
│   ┌─ producers/voice → narration.mp3 (Typecast)        │
│   ├─ producers/video-sourcer → video clips + images    │
│   └─ producers/subtitle → subtitles (faster-whisper)   │
│   타이밍 싱크: TTS 실제 길이 측정 → config 자동 보정        │
├─────────────────────────────────────────────────────────┤
│ Stage 5: RENDER                                         │
│   producers/editor (Remotion) → final.mp4              │
│   ShortsVideo.tsx + TransitionSeries + OffthreadVideo   │
├─────────────────────────────────────────────────────────┤
│ Stage 6: QA                                             │
│   producers/qa → 42항목 체크리스트                        │
│   FAIL 시 Stage 3 또는 4로 롤백 (최대 2회)                │
└─────────────────────────────────────────────────────────┘
  │
  ▼
업로드 가능한 완성 영상
```

### 핸드오프 체인

```
주제 → [NLM Step 1] → source.md → blueprint.json
     → [NLM Step 2] → script.json → narration.mp3 → subtitles → final.mp4
```

### 폐기된 구 파이프라인 (사용 금지)

| 구 | 신 | 폐기 사유 |
|----|----|----------|
| Stage 1 shorts-researcher 직접 호출 | NLM Step 1 → nlm-fetcher | 세션 70 NLM 품질 우위 |
| Stage 3 shorts-scripter 직접 호출 | NLM Step 2 → nlm-fetcher → script-converter → script-polisher | 세션 70 캐리 파버 대본 품질 우위 |

구 에이전트(`shorts-researcher`, `shorts-scripter`)는 **NLM 장애/한도초과 시 폴백**으로만 사용.

### 승인 게이트 (Human-in-the-Loop)

| 게이트 | 위치 | 조건 |
|--------|------|------|
| 리서치 승인 | Stage 1 → 2 | 대표님이 source.md 확인 |
| 대본 품질 | Stage 3 → 4 | GATE 2 검사관 17명 전원 PASS |
| QA 통과 | Stage 6 → 완성 | 42항목 전부 PASS |

---

## Core Principle: Narration Drives Timing

**음성이 영상 길이를 결정한다.** 영상이 음성에 맞추는 것이지, 반대가 아니다.

```
Script (255-330자, 8.5자/초) → TTS 생성 → ffprobe 실제 길이 측정
  → durationInFrames = seconds × 30fps
  → 영상 클립 속도 조절 → Remotion 렌더
```

### 한국어 TTS 파라미터

| 항목 | 값 |
|------|-----|
| 속도 | **8.5 chars/sec** (영어 150 WPM과 다름) |
| 목표 길이 | 30-45초 |
| 기본 길이 | 38초 (~~director.py~~ — 현재 Scripter AGENT.md 가 직접 제어) |
| 스크립트 글자 수 | 255-330자 |
| 검증 범위 | 28-45초 (script_schema.py) |

### 씬 구조 (Narration Density)

| 씬 | 길이 | 밀도 | 설명 |
|----|------|------|------|
| Hook | 3-5s | 80-90% | 즉각 시작, 호기심 유발 |
| Body ×3-4 | 7-10s each | 70-80% | 팩트 전달, 상황 설명 |
| CTA | 3-5s | 60-80% | 참여 유도, 여운 |

---

## Timing Sync Feedback Loop

TTS 엔진은 예상과 다른 길이를 생성한다. **렌더 전에 반드시 측정 후 보정:**

1. TTS 생성 (per-scene audio)
2. `ffprobe`로 실제 오디오 길이 측정 (`get_audio_duration_ffprobe()`)
3. config의 `durationInFrames`와 비교
4. 차이 시 자동 보정 + 1초 패딩
5. **Remotion 렌더 전에 반드시 실행**

```
짧은 씬: 30% 오차 가능 → 보정 필수
긴 씬: 10% 오차 → 보정 권장
```

---

## Provider System

교체 가능한 Provider 구조. Tier 순서대로 시도, 실패 시 다음 Tier.

### TTS Provider

| Tier | Provider | 특징 | 채널 매핑 |
|------|----------|------|-----------|
| 0 | **Typecast** | 메인. 한국어 특화 | humor:박창수(tempo=1.1), politics:필재, trend:카밀라 |
| 1 | Fish Audio | 보조 | — |
| 2 | ElevenLabs | 영어 특화 | — |
| 3 | EdgeTTS | 무료 최후 수단 (AI티 심함) | — |

### Visual Source Provider

| 우선순위 | 소스 | 설명 |
|----------|------|------|
| 1 | **실제 관련 영상** | 커뮤니티/SNS 원본 (Reddit, TikTok, DC, FM코리아) |
| 2 | **관련 인물 영상/사진** | 정치인→해당 인물, 사건→현장 |
| 3 | **커뮤니티 캡처** | 게시글/댓글 스크린샷 (텍스트 스크린샷 금지) |
| 4 | **AI 생성 (Veo 3.1 Lite)** | 4-8초 클립, 9:16, 720p |
| 5 | 일러스트 | 만화풍, 상황 묘사 |
| ~~6~~ | ~~스톡~~ | **Pexels/Pixabay 완전 금지** — 실제 영상/크롤링/이전 클립/Veo AI 로 대체 (메모리 feedback_pexels_banned) |

### Render Engine

| Engine | 용도 |
|--------|------|
| **Remotion** (primary) | ShortsVideo.tsx, TransitionSeries |
| FFmpeg (utility) | 오디오 처리, ffprobe 측정 |

### Subtitle Engine

| Engine | 용도 |
|--------|------|
| **faster-whisper** | 단어 단위 타이밍 (스크립트 타이밍 추정 금지) |

---

## 🔴 script.json Schema 계약 (세션 43 추가)

**script.json 의 구조는 파이프라인 입력 계약이다**. Scripter Agent 가 "의미론적으로 더 명확하다" 는 이유로 구조를 변경하면 파이프라인이 깨진다.

### 고정 구조 (7 섹션)

```json
{
  "metadata": { "pipeline_type": "shorts", "channel": "...", "character_count": N },
  "title": { "line1": "...", "line2": "...", "accent_color": "...", "accent_words": [...] },
  "series": { "part": N, "total": M },
  "sections": [
    {"id": "hook", "type": "hook", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "<body_1>", "type": "body", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "<body_2>", "type": "body", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "<body_3>", "type": "body", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "<body_4>", "type": "body", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "<body_5>", "type": "body", "narration": "...", "emotion": "...", "duration_s": N},
    {"id": "cta",  "type": "cta",  "narration": "...", "emotion": "...", "duration_s": N}
  ]
}
```

### 🚫 금지 (세션 43 v12 FAIL 패턴)

```json
{
  "hook": { "narration": "..." },       // ❌ top-level 분리 금지
  "sections": [act1, act2, ..., act5],  // ❌ body 만 있으면 안 됨
  "cta":  { "narration": "..." }        // ❌ top-level 분리 금지
}
```

**이유**: `scripts/audio-pipeline/tts_generate.py:86` 이 `for section in script["sections"]` 로만 순회. `hook` / `cta` 를 top-level 로 분리하면 **TTS 가 통째로 무시**. 세션 43 에 Hook 48 자 + CTA 71 자 누락 사건 발생 (대표님 재생 중 "스토리 흐름 이상 + 다음 편 예고 빼먹음" 감지).

### Schema 검증 (파이프라인 진입 전 필수)

```python
import json
d = json.load(open("output/{episode}/script.json", encoding="utf-8"))
assert len(d["sections"]) == 7, f"sections must be 7, got {len(d['sections'])}"
assert d.get("hook") is None, "hook must be inside sections, not top-level"
assert d.get("cta") is None, "cta must be inside sections, not top-level"
assert d["sections"][0]["id"] == "hook" or d["sections"][0].get("type") == "hook"
assert d["sections"][-1]["id"] == "cta" or d["sections"][-1].get("type") == "cta"
# character_count 실측 검증
total_actual = sum(len(s["narration"]) for s in d["sections"])
total_stated = d["metadata"]["character_count"]
assert total_actual == total_stated, f"character_count mismatch: stated {total_stated}, actual {total_actual}"
print(f"[PASS] schema contract: 7 sections, total {total_actual} chars")
```

이 검증은 TTS 생성 **직전** 에 반드시 실행. 실패 시 Scripter 재소환 또는 Orchestrator 가 구조 복구 (세션 43 v12.3 사례: hook/cta 를 sections 배열에 병합).

### character_count 는 Python `len()` 실측

Scripter LLM 은 문자열 산술을 못 한다 (세션 42/43 에 2 회 연속 동일 오류). 생성 직후 Orchestrator 가 실측 재계산:

```python
for s in d["sections"]:
    s["character_count"] = len(s["narration"])
d["metadata"]["character_count"] = sum(len(s["narration"]) for s in d["sections"])
```

---

## Key Files

| 파일 | 역할 |
|------|------|
| `scripts/orchestrator/orchestrate.py` | step_3~7 Python 함수 + `build_gate_envelope()` + `run_pipeline_outsource_first(skip_gates=True)` 디버그용. **Python 단독 실행 금지** — 메인 세션이 호출 |
| `scripts/orchestrator/harness.py` | `GATE_INSPECTORS` dict + `write_inspector_result()` + `append_gate_entry()` + `aggregate_inspector_results()` — 세션 72 검사관 군단 오케스트레이션 helper |
| `scripts/orchestrator/hc_checks.py` | HC-1~10 + HC-13/14 자동 검증 (HC-4 R2 가드: gates.json Auto-approved/deferred 0건 강제) |
| `scripts/orchestrator/inspector_schema.py` | `InspectorResult` Pydantic v2 (verdict/tools_used/evidence/failures) + `parse_inspector_output()` |
| `scripts/orchestrator/qa_checklist.py` | QA 12항목 검수 (INSPECTOR_CHECKLIST.md 가 진실 원천) |
| `scripts/video-pipeline/remotion_render.py` | Remotion 렌더 래퍼 |
| `scripts/video-pipeline/script_schema.py` | 스크립트 검증 (8.5자/초) |
| `scripts/audio-pipeline/tts_generate.py` | TTS 생성 + 4-tier 폴백 |
| `scripts/sourcing/web_source.py` | 커뮤니티 크롤링 |
| `config/voice-presets.json` | 보이스 프리셋 |

**Deprecated (절대 사용 금지)**:
- ~~`scripts/orchestrator/director.py`~~ — Planner AGENT.md 가 블루프린트 직접 생성 (메모리 `feedback_orchestrate_banned` 중 기계적 실행 금지 유지)

---

## Inspector Wiring Contract (세션 72 D-72-01 — 진실원천)

### 철학

**오케스트레이터 = 메인 Claude 세션.** 별도 `.claude/agents/orchestrator/AGENT.md` 파일 없음. 메인 세션이 묵시적으로 담당하며 Task tool을 통해 서브에이전트(producer 12명 + inspector 30+명)를 분기.

검사관 자체는 강력하지만(ins-fun 6-sample 실증 median 5/10 FAIL 정확히 잡음 — 세션 72) **호출하지 않으면 아무 의미 없다.** Phase 47이 정확히 이 패턴으로 실패: 검사관 발화 없이 `--auto mode`로 deferred 목록 남긴 채 통과 → 대표님 E2E 후 "재미없음" 최종 판정.

### 정상 실행 프로토콜

각 pipeline step 완료 후 **반드시** 다음 시퀀스를 메인 세션 한 턴 안에서 수행:

```python
# Step 1: Python 함수 호출 (파일 생성)
script_path = step_3_script_nlm(slug, blueprint, source_md, output_dir, channel)

# Step 2: envelope dict 생성
from scripts.orchestrator.orchestrate import build_gate_envelope
env = build_gate_envelope(
    step_name="step_3_script_nlm",
    primary_artifact=script_path,
    gate="script",
    output_dir=output_dir,
)
# env = {"gate_id": "GATE-2", "gate_inspectors": [ins-structure, ..., ins-fun, ...], ...}
```

이 지점에서 메인 세션은 **parallel Task() 분기**:

```
# 메인 세션이 한 번의 턴에서 Task tool을 env["gate_inspectors"] 갯수만큼 동시 호출.
# 각 Task는 subagent_type=검사관이름, prompt="script.json 경로 + 채널 + 판정 지시"
# 결과: 각 Task의 JSON 응답
```

그 후 집계 + 영속화 + 분기:

```python
from scripts.orchestrator.inspector_schema import parse_inspector_output
from scripts.orchestrator.harness import (
    aggregate_inspector_results, write_inspector_result, append_gate_entry,
)
from scripts.orchestrator.orchestrate import InspectorGateFailure

# 각 Task 결과 파싱 (dict 또는 JSON 문자열)
parsed = [parse_inspector_output(task_output) for task_output in task_outputs]

# 집계
gate = aggregate_inspector_results("script", parsed)  # PASS if 모두 PASS else FAIL

# 영속화 (HC-10 / HC-4 입력)
for r in parsed:
    write_inspector_result(r, output_dir)
append_gate_entry(
    gate_id=env["gate_id"],
    verdict=gate.verdict,
    inspector_results=parsed,
    output_dir=output_dir,
    retry_count=retry_count,
)

# 분기
if gate.verdict == "FAIL":
    if retry_count >= 3:
        raise InspectorGateFailure(env["gate_id"], retry_count, gate.failures)
    # weakest_axis + evidence_quotes 정보 담아 producer 재소환
    retry_count += 1
    # ... (재소환 + step_3_script_nlm 재호출 + 검사관 재발화 loop)
```

### GATE별 검사관 배치 (GATE_INSPECTORS in harness.py)

| 게이트 | artifact key | 검사관 수 | 검사관 이름 |
|--------|-------------|-----------|-------------|
| GATE 1 | `blueprint` | 1 | ins-blueprint |
| **GATE 2** | `script` | **17** | structure / style / duo / emotion / creativity (Phase 47 baseline 5) + hook-strength / rhythm / pattern-interrupt / conclusion-unity / abstract-overuse / evidence-density / forbidden-words / channel-voice / korean-naturalness / bible-fit / fun / tension (Phase 50-03 new 12) |
| GATE 3 | `assets` | 5 | narration / typo / sync / matching / duplicate |
| GATE 4 | `video` | 2 | format / visual |
| GATE 5 | `director` | 1 | director (프레임 추출 + 직접 시청) |
| GATE-5 meta | `meta` | 2 | meta-chain (artifact 해시) + fun-summary (재미 총평) |

미등록 4명 (디스크엔 존재, GATE_INSPECTORS 미등록 — 다음 플랜 `d-*.md`에서 처리):
- ins-license (실사 라이선스)
- ins-mosaic (얼굴/번호판)
- ins-gore (사망 직접장면)
- ins-longform-continuity (롱폼 시리즈 연속성)

### 금지 (R2 가드 — HC-4 자동 차단)

`gates.json` 내 gate-level `verdict` 에 다음 문자열 금지:
- `Auto-approved` / `auto_approved`
- `deferred`
- `SKIP` / `skipped`
- `pending`
- `NA` / `N/A` / `TBD` / `TODO`

이 패턴은 Phase 47 `47-E2E-RESULTS.md`가 E2E 미실행을 "통과 처리"한 구조적 우회로. HC-4가 1건이라도 감지하면 `status="qa_failed"` 전환.

SKIP은 개별 inspector-level verdict (InspectorResult) 안에서만 허용, gate-level에서는 절대 금지.

### 쉽먼 재렌더 / 일본어 버전 순서

1. `step_4_voice(script, output_dir, "incidents")` → narration.mp3
2. GATE 3 ins-narration (단독) — 괄호문 음독 / 보이스 프리셋 검증
3. `step_5_sourcing(blueprint, script, output_dir, "incidents")` → sources/ + **scene-manifest.json (deterministic draft)** + **sources_metadata.json** (Phase 50-F). Twelve Labs hits는 `tl_clip_extractor.extract_tl_clips`로 slug/sources/에 ffmpeg 추출된 후 manifest에 편입. manifest 이미 존재 시 덮어쓰지 않음 (video-sourcer refinement 보존).
4. GATE 3 ins-matching + ins-duplicate (2명 병렬)
5. `step_6_subtitle(narration_path, script, output_dir, language="ko")` → subtitles
6. GATE 3 ins-typo + ins-sync (2명 병렬)
7. `step_7_render(...)` → final.mp4
8. GATE 4 ins-format + ins-visual (2명 병렬)
9. GATE 5 ins-director (단독, ffmpeg 프레임 추출)
10. GATE-5 meta ins-meta-chain + ins-fun-summary (2명 병렬)

일본어 버전: `language="ja"` + channel `"incidents-jp"` — Fish Audio TTS + 일본어 자막 + 대표님 수동 업로드 (memory `feedback_jp_no_auto_upload`).
