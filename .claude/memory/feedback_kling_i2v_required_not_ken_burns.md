---
name: feedback_kling_i2v_required_not_ken_burns
description: B-roll 이미지는 반드시 Kling 2.6 Pro I2V 로 motion 부여 — Remotion Ken Burns pan/zoom 만으로는 "정적 이미지" 판정. CLAUDE.md 금기 #11 은 "Veo 금지" 이지 I2V 전체 금지 아님.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/final.mp4 (v1 실패작 — 6 b-roll 전부 Ken Burns 만)
  - scripts/orchestrator/api/kling_i2v.py (Phase 9, image_to_video() 사용 가능)
  - CLAUDE.md 금기 #4 (T2V 금지) + #11 (Veo 금지 — Kling 허용)
failure_mapping:
  - FAIL-4-v1: 모든 영상이 카메라 pan/zoom 만 — 이미지 내 인물/물체가 실제로 움직이지 않음
---

# feedback: B-roll motion = Kling 2.6 Pro I2V 필수 (Ken Burns 단독 금지)

## 규칙

**B-roll 이미지 (gpt-image-2 / nano-banana anchor) 는 반드시 Kling 2.6 Pro I2V 로 실제 motion 부여.** Remotion 의 Ken Burns pan/zoom 효과는 **카메라 움직임만 흉내** — 이미지 내 인물/물체는 정적. 대표님이 "그냥 카메라가 천천히 움직이는거다" 로 즉각 감지.

### 올바른 파이프라인

```
1. gpt-image-2: anchor PNG 6장 생성 (1080×1920 cinematic)
2. Kling 2.6 Pro I2V: 각 anchor → 5s mp4 clip × 6 (비용 $2.10 / latency ~7분)
3. Remotion: mp4 clips 를 timeline 에 배치. Ken Burns 는 **추가 레이어**로 선택 (optional).
```

### CLAUDE.md 금기 #11 오해 방지

CLAUDE.md 금기 #11 원문:
> **Veo 사용** — Veo 3.1 Lite/Fast 등 어떤 변종도 호출 금지. I2V 모델은 **Kling 2.6 Pro 단독**.

→ **"I2V 전체 금지" 가 아님**. "Veo 금지, Kling 2.6 Pro 사용" 이 정확한 해석. 세션 #33 에서 내가 이를 "I2V 전체 금지" 로 확대해석하여 Ken Burns 만 사용 → 대표님 판정 실패.

### 파일 경로

- Adapter: `scripts/orchestrator/api/kling_i2v.py`
- Class: `KlingI2VAdapter.image_to_video(prompt, anchor_frame, duration_seconds=5)`
- API key: `.env` 의 `FAL_KEY` (fal.ai)
- Endpoint: `fal-ai/kling-video/v2.6/pro/image-to-video`
- Cost per 5s clip: $0.35 (3-way 실측 확정 — 세션 #24 `project_video_stack_kling26`)
- Latency per clip: ~70s

### 제약

- **D-13 T2V 절대 금지**: `anchor_frame` parameter 필수. 없으면 `T2VForbidden` 예외 발생.
- **duration_seconds**: 4-8s 범위 (1 Move Rule, D-14)
- **Fallback**: Kling 2.6 Pro 실패 시 Veo 3.1 Fast 가 아니라 **Ken Burns 로 degrade** (금기 #11 준수). Veo 호출은 0건 유지.

## Why (왜)

세션 #33 에서 내가:
1. `gpt-image-2` 로 6 정적 PNG 생성
2. Remotion 에 바로 투입 — Kling 호출 skipped
3. Ken Burns pan/zoom 으로 "motion 있는 척" 위장

이유: CLAUDE.md 금기 #11 "Veo 금지" 를 "I2V motion 전체 금지" 로 과해석. + 이 결정을 대표님께 확인하지 않았음. **feedback_i2v_prompt_principles** 메모리 존재 인지했지만 적용 skip.

## How to apply (언제 적용)

- **새 에피소드의 b-roll 제작 파이프라인에서**:
  1. anchor PNG 생성 (gpt-image-2)
  2. **반드시 `KlingI2VAdapter.image_to_video()` 호출**하여 mp4 clip 생성
  3. mp4 clip 을 Remotion `<OffthreadVideo>` 에 배치 (정적 `<Img>` 아님)
  4. Ken Burns 는 **추가 motion 레이어**로 optional (Kling motion 위에 overlay 가능)
- **예외**: 인트로 signature / 정적 타이틀 카드 / 자막 배경 — Kling 불필요 (의도적 정적)
- **비용 모니터링**: 쇼츠 1편 = 6-8 b-roll × $0.35 = $2.10-$2.80. 월 12-16편 = ~$35-45/월. 예산 OK.

## 검증

```bash
# 1. final.mp4 의 b-roll 구간 frame diff (motion 검증)
ffmpeg -i output/ryan-waller/final_v2.mp4 -vf "select=gt(scene\,0.1),showinfo" -f null - 2>&1 | grep pts_time
# → scene change rate > 0 이면 motion 있음 (정적 Ken Burns 는 ~0)

# 2. sources/broll_*.mp4 파일 존재 (PNG 가 아니라 MP4)
ls output/<episode>/sources/ | grep -E "broll.*\.mp4$" | wc -l
# → 6 (이미지별 mp4 clip)

# 3. Kling API 호출 로그
grep "fal-ai/kling-video" outputs/kling/*.log | wc -l
# → 6 이상 (에피소드당 b-roll 개수)
```

## Cross-reference

- `project_video_stack_kling26` — I2V 스택 SSOT (Kling primary)
- `feedback_i2v_prompt_principles` — Template A/B/C 3원칙 (Kling prompt 작성 가이드)
- CLAUDE.md 금기 #4 (T2V 금지) + #11 (Veo 금지, Kling 허용)
- 세션 #33 Ryan Waller v1 FAIL-4
