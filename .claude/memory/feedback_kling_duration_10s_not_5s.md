---
name: feedback_kling_duration_10s_not_5s
description: Kling I2V clip 기본 duration 은 8s (우리 I2VRequest validator 상한, D-14 1 Move Rule). reference _kling_i2v_batch.py 는 [5,10] choices 이지만 우리는 [4..8]. v2 5s 는 section 평균 10s 대비 짧아 freeze 유발.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - C:/Users/PC/Desktop/shorts_naberal/scripts/video-pipeline/_kling_i2v_batch.py (reference --duration choices=[5,10])
  - scripts/orchestrator/api/models.py I2VRequest.duration_seconds (우리 validator ≤ 8)
  - scripts/experiments/generate_ryan_waller_kling_i2v.py (v2, 5s — freeze 원인)
  - scripts/experiments/generate_ryan_waller_kling_i2v_v3.py (v3, 8s)
failure_mapping:
  - FAIL-v2-영상_프리징: "영상이 움직이다 프리징한다" (대표님 직접 판정)
---

# feedback: Kling I2V duration = 8s (v2 5s → freeze, reference 10s)

## 규칙

**Kling I2V clip 의 기본 duration 은 8s (우리 I2VRequest validator 상한, D-14 1 Move Rule 4-8s 준수).** reference `_kling_i2v_batch.py` 는 [5, 10] 두 가지 choices 이지만 우리 pydantic model 이 8 max 로 강제. 5s 는 section duration (평균 10s) 대비 너무 짧아 **5s 이후 마지막 frame freeze**.

### 규칙 수치

| 상황 | duration 권장 |
|------|---------------|
| section ≤ 4s (watson 턴 등) | 4-5s |
| section 5-8s | 6-8s |
| section 8-12s | **8s** + Ken Burns loop / crossfade 또는 2 clip 분할 |
| section > 12s | 8s 2 clip 병치 |

### 우리 모델 제약 vs reference 차이

- Reference `_kling_i2v_batch.py`: `duration: int in {5, 10}` — fal.ai 지원
- 우리 `I2VRequest`: `duration_seconds: int, le=8` — D-14 1 Move Rule 반영한 엄격 상한
- 10s 요청 시 pydantic ValidationError (le=8)

**타협**: 8s 사용. v2 5s → v3 8s 로 **60% 상향** → freeze 시간 대폭 축소.

### 비용 영향

- 5s: $0.35 / clip
- 8s: $0.56 / clip (+60%)
- 10s (reference 본격): $0.70 / clip (우리 불가)

Ryan Waller 6 clips = $3.36 (8s) vs $2.10 (5s). 수용 가능.

## Why

세션 #34 v2 대표님 판정: "영상이 움직이다 프리징한다". 원인 = Kling clip 5s + scene avg 10.7s (64.4s/6 scenes) → Remotion OffthreadVideo 가 5s 에서 끝나면 마지막 frame 유지 → 시각적 freeze.

내가 세션 #33 에서 v1 5s 를 택했고 v2 에서도 습관적으로 5s 유지 → v3 에서 처음으로 8s 로 상향.

## How to apply

- **Kling I2V 호출 측**:
  - 기본 `duration_seconds=8` (5s 금지, 특별 이유 없는 한)
  - scene duration > 8s 이면 2 clip 분할 또는 Remotion clip loop 처리
  - fal.ai 10s 지원하지만 우리 validator 차단 — 정말 필요하면 D-14 재검토 후 validator 완화
- **visual_spec_builder 측**:
  - clip durationInFrames 를 scene audio duration 기준 재분배
  - mp4 clip 이 audio 보다 짧으면 Remotion loop / crossfade 기법 필요
- **ins-render-integrity 검증**:
  - final.mp4 에 freezedetect filter 로 1s 이상 freeze 0건 확인
  - `ffmpeg -vf freezedetect=n=0.003:d=1.0 -f null -`

## 검증

```bash
# 1. Kling clip duration 체크
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \
  output/<episode>/sources/broll_*.mp4
# → 7.5~8.5s 범위 (Kling 8s target)

# 2. freeze detection
ffmpeg -i output/<episode>/final_v3.mp4 -vf "freezedetect=n=0.003:d=1.0" \
  -map 0:v:0 -f null - 2>&1 | grep "freeze_start\|freeze_duration"
# → 0 건 (v2 는 6건 이상 추정)
```

## Cross-reference

- `project_video_stack_kling26` — Kling 2.6 Pro stack
- `feedback_i2v_prompt_principles` — prompt 3원칙
- `feedback_kling_i2v_required_not_ken_burns` (세션 #34 v2 박제)
- reference: `shorts_naberal/scripts/video-pipeline/_kling_i2v_batch.py`
- D-14 (1 Move Rule) — models.py I2VRequest le=8 제약
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
