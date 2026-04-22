---
name: feedback_agents_require_visual_analysis
description: 🔴 영구 INVARIANT Rule 3 — 크롤링/제작/검사 에이전트는 Claude Opus 4.7 subagent 를 spawn 해 key frame 을 Read 로 시각 판정. 외부 vision API 금지, 메인 세션 직접 Read 금지 (context 보호).
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
priority: critical
---

# 🔴 INVARIANT Rule 3 — 시각 분석은 Claude Opus 4.7 Subagent 가 수행

## 대표님 원문 (verbatim)

2026-04-23 세션 #34:
> "자료크롤링하는 에이전트와, 영상작업 에이전트, 검사에이전트는 반드시 본인들 작업시 크롤링시, 영상제작시 시각능력을 이용하여 본인이 다루고있는 자료를 시각적으로 분석을할수있어야한다. 그래야지만 올바른 영상제작, 올바른 자료크롤링이 가능하다. 그리고 올바른 검사가 가능해진다."

2026-04-23 직후 수정 지시 (vision provider 지정):
> "gemini로 이미지를 분석할필요없다 지금 claude code 4.7opus가 성능최고다."

2026-04-23 재차 수정 (메인 vs subagent):
> "크롤링하는 에이전트를 claude 4.7 opus로 지정하면 에이전트선에서 가능한지 알아보고 가능하면 에이전트선에서 하라고해라 너가하면곤란해"

## 규칙

**크롤링·제작·검사 단계는 Claude Opus 4.7 subagent 가 key frame 을 Read 로 직접 보고 판정.** 메인 세션 (Claude) 이 직접 Read 금지. 외부 vision API (Gemini / GPT-4o / TwelveLabs) 호출 금지.

### 3 적용 영역

| 에이전트군 | 시각 판정 대상 | 판정 내용 |
|-----------|---------------|----------|
| **Agent 1 Asset Sourcer** | 다운로드된 candidate 의 key frame (shot × rank) | shot.visual_requirement / markers 와 일치 여부 → best candidate 선정 + reject 사유 |
| **Agent 2 Video Producer** | Kling I2V 생성물 / ffmpeg trim 결과의 mid-frame | 대본 shot.text 맥락 일치 확인 → pass / retry (max 2) |
| **Agent 4 Inspector (Vision)** | 최종 final.mp4 각 shot 구간 mid-frame | 대본-영상 매칭 + 시각 오염 (텍스트 artifact / 호스트 얼굴 / clip 반복 / outro 조기) 검출 |

### 구현 패턴

```python
# 메인 세션 (orchestrator) 코드
from_the_main_session = Agent(
    subagent_type="general-purpose",  # 또는 기존 asset-sourcer agent
    model="opus",                      # Claude Opus 4.7 명시
    prompt=f"""
    reads: {EPISODE_DIR}/script_v*.json (첫 행위)
    shot_id: {shot_id}
    visual_requirement_ko: {shot.visual_requirement_ko}
    emotion/situation/motion markers: ...

    key frames to Read:
    - candidate 1: {keyframes_dir}/{shot_id}_c1_<src>.jpg
    - candidate 2: {keyframes_dir}/{shot_id}_c2_<src>.jpg
    - candidate 3: {keyframes_dir}/{shot_id}_c3_<src>.jpg

    Task: Read each candidate's key frame image. Compare visually against
    shot.visual_requirement_ko + markers. Select best candidate.
    Reject others with specific visual reason.

    Output JSON:
    {{
      "selected_candidate": 1 | 2 | 3,
      "reason": "shot 과 일치하는 구체 시각 요소 설명 (한국어)",
      "rejects": [{{"c": N, "reason": "..."}}, ...]
    }}
    """,
    description="Visual candidate gate for shot"
)
```

### 메인 세션 Read 금지 이유

- 쇼츠 1편 = 22 shots × 3 candidates × 1 key frame = **66 이미지** 를 Agent 1 에서 판정
- Agent 2 retry 로 추가 22 images
- Agent 4 Inspector 로 추가 22 images
- 합계 **100+ 이미지** 를 메인 세션 context 에 올리면 token 폭증 + 후속 단계 속도 급락
- Subagent 는 **별도 context** — 판정 결과 JSON 만 메인에 리턴, 이미지 데이터는 subagent context 안에서 소비 후 폐기

### 외부 vision API 금지 이유

- 추가 API key 관리 복잡도
- Claude Code Max 구독 (ANTHROPIC_API_KEY 불필요, 금기 #Claude API key) 로 Opus 4.7 직접 호출 가능
- 대표님 판단: "claude code 4.7opus가 성능최고다"

### 구현 강제 수단

1. **asset-sourcer / video-producer / 신규 ins-visual-coherence AGENT.md** — subagent spawn 로직 포함
2. **vision 판정 없는 단계는 `feedback_video_sourcing_specific_keywords` 만으로 text 매칭 금지** (text 매칭은 1차 필터만)
3. **각 subagent 호출 로그** — `agent spawn subagent_type=general-purpose model=opus shot=<id>` 기록

## Why

Ryan Waller v3.2 7지적 중 #4 "my disk" 텍스트 노출 / #3 병원 복도 반복 / 여자 유튜버 얼굴 반복 등은 **title/description 기반 text 매칭만** 으로는 원천 차단 불가. 시각 내용을 직접 확인해야만 검출 가능.

대표님 세션 #34 3단계 반복 지시 — 1) 시각 능력 필수 → 2) Gemini 말고 Claude Opus 4.7 → 3) 메인 말고 subagent. 최종 결론: **subagent vision**.

## How to apply

### Asset Sourcer (Agent 1)
```
1. Python: candidate 다운로드 + ffmpeg 로 key frame 추출
2. 메인: Agent tool 로 subagent spawn (model=opus)
3. Subagent: Read 로 frames 보고 판정 → JSON 리턴
4. 메인: manifest 에 selected_candidate 기록 + 나머지 reject
```

### Video Producer (Agent 2)
```
1. Python: selected candidate → trim 또는 Kling I2V
2. Python: 결과 mp4 의 mid-frame 추출
3. 메인: Agent tool 로 subagent spawn (verification)
4. Subagent: Read 로 대본 맥락 일치 확인 → pass / retry_prompt
5. Retry 시 Python 에 개선 prompt 전달, max 2 retry
```

### Vision Inspector (Agent 4)
```
1. Python: final.mp4 의 22 shot 각 mid-frame 추출
2. 메인: Agent tool 로 subagent spawn (final inspection)
3. Subagent: Read 전수 + 오염 검출 + 대본-영상 매칭 리포트
4. 메인: inspect_report_v4.md 에 요약 기록
```

## 검증

```bash
# 각 subagent 호출 로그 확인 (각 shot 에 대해 최소 1회)
grep -E "subagent_type.*model=opus" logs/*.log | wc -l  # 22+ expected
```

## Cross-reference

- `feedback_every_agent_reads_script_first.md` (Rule 1)
- `feedback_script_markers_absolute_compliance.md` (Rule 2)
- `project_script_driven_agent_pipeline_v1.md` (전체 pipeline SSOT)
- CLAUDE.md 금기 #9 (33 에이전트 초과 금지) — `general-purpose` subagent 활용, 신규 agent 생성 회피
- `project_claude_code_max_no_api_key.md` (ANTHROPIC_API_KEY 금지, 구독 활용)
