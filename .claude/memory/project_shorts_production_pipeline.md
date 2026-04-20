---
name: project_shorts_production_pipeline
description: 4-stage 영상 제작 체인 — Script → Image(Nano Banana) → Voice(Typecast) → Video(Kling 2.6 Pro I2V + Veo 3.1 fallback)
type: project
---

# shorts 제작 파이프라인 (4-Stage Chain)

**확정**: 세션 #24 (Stage 구조) + 세션 #26 (Stage 4 drift 복구 — Runway Gen-4.5 → Kling 2.6 Pro 반영).

## Stage 구조

| Stage | 역할 | 주력 도구 | Fallback | 비용 기준 |
|-------|------|---------|---------|---------|
| **1. Script** | 대본 생성 | Claude Sonnet 4.6 (CLI subprocess) | Opus 4.6 (critical gate) | ~$0.02/편 |
| **2. Image (Anchor)** | 앵커 프레임 | Nano Banana Pro (Gemini 3 Pro Image) | DALL-E 3 | $0.04/img |
| **3. Voice** | 한국어 TTS | Typecast | ElevenLabs v3 → EdgeTTS | ~$0.50/편 |
| **4. Video (I2V)** | 영상 생성 | **Kling 2.6 Pro** (`fal-ai/kling-video/v2.6/pro/image-to-video`) | **Veo 3.1 Fast** | $0.35/5s (Kling) |

## 중요 규율

- **T2V 금지 — I2V only** (모든 영상은 Stage 2 anchor frame 기반, 도메인 절대 규칙 #4)
- **Claude 호출은 CLI subprocess만** — anthropic SDK 직접 호출 금지 ([project_claude_code_max_no_api_key](project_claude_code_max_no_api_key.md))
- **Stage 4 prompt 는 3원칙 필수** ([feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md))

## 오케스트레이터

- `scripts/orchestrator/shorts_pipeline.py` (Phase 5 구현, 500~800줄 state machine)
- GATE: IDLE → TREND → NICHE → RESEARCH_NLM → BLUEPRINT → SCRIPT → POLISH → VOICE → ASSETS → ASSEMBLY → THUMBNAIL → METADATA → UPLOAD → MONITOR → COMPLETE

## 드리프트 이력 (세션 #26 복구)

- 세션 #24 오전 시점 Stage 4 = Runway Gen-4.5 primary 로 기록
- 세션 #24 저녁 Kling 2.6 으로 번복 but 본 메모리 업데이트 누락
- 세션 #26 에서 본 메모리 Stage 4 전면 재작성 (commit `05a00f3`)

## Related

- [project_video_stack_kling26](project_video_stack_kling26.md) — Stage 4 스택 세부
- [project_tts_stack_typecast](project_tts_stack_typecast.md) — Stage 3 세부
- [feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md) — Stage 4 prompt 규율
