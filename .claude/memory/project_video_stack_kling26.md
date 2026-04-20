---
name: project_video_stack_kling26
description: Stage 4 I2V 영상 스택 — Kling 2.6 Pro primary + Veo 3.1 Fast fallback, Runway hold, Kling 2.5-turbo deprecated
type: project
---

# I2V 영상 스택 (Stage 4)

**결정 확정**: 세션 #24 (2026-04-20) 후반, 실측 3-way 비교 기반.
**이력**: Runway Gen-4.5 (오전) → Runway Gen-3a Turbo (오후) → **Kling 2.6 Pro (저녁 확정)**. 4차 번복 후 Pareto-dominant 확인.

## 스택 매트릭스

| Tier | 모델 | Endpoint | 비용/5s | Latency | 상태 |
|------|------|----------|---------|---------|------|
| Primary | Kling 2.6 Pro | `fal-ai/kling-video/v2.6/pro/image-to-video` | $0.35 | 70s | ✅ 확정 |
| Fallback | Veo 3.1 Fast | `fal-ai/veo3.1/fast/image-to-video` | $0.50 | — | ✅ 확정 |
| Hold | Runway Gen-4.5 | `gen4.5` | $0.60 | 149s | adapter 유지, production 미호출 |
| ~~Deprecated~~ | ~~Kling 2.5-turbo Pro~~ | — | — | 제거 |

## 실측 증거 (3-way, 동일 anchor + Template A prompt)

- Gen-3a Turbo: $0.25 / 23.7s / ❌ 팔 복제, 컵 코 위로, 30% 확대
- Gen-4.5: $0.60 / 149.3s / ✅ "그나마 괜찮네"
- **Kling 2.6 Pro: $0.35 / 70.0s / ✅ 우수 + 얼굴 회전 자연** ← Pareto-dominant

## Fallback 트리거 (Kling → Veo)

**조건** (복합 limb/micro motion 에서 Kling 실패 시 수동 전환):
- 얼굴 micro-expression (윙크, 미세 표정)
- 손가락 articulation (악기, 글씨, 도구 조작)
- 머리카락 simulation (바람, 튀김)
- 미세 light (반사, 그림자 변화)

**비용 영향**: 43% 증가 ($0.35 → $0.50). auto-route는 Phase 10 실패 패턴 축적 후 정식화 — 현재는 smoke CLI `--use-veo` 수동 플래그만.

## 파일 경로

- Primary adapter: `scripts/io/kling_i2v.py`
- Fallback adapter: `scripts/io/veo_i2v.py`
- Smoke CLI: `scripts/smoke/phase091_stage2_to_4.py` (Template A 내재화)
- 실측 clip: `output/prompt_template_test/kling26/kling_20260420_152355.mp4` (4.5MB)

## 금지 사항

- **T2V 절대 금지** — I2V only, anchor frame 기반 (NotebookLM T1, 도메인 절대 규칙 #4)
- `project_video_stack_runway_gen4_5.md` (구파일) — 세션 #26에서 삭제 + 본 파일로 rename 완료 (D091-DEF-02 #3)

## Related

- [feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md) — Template A/B/C 3원칙
- [project_shorts_production_pipeline](project_shorts_production_pipeline.md) — Stage 4 통합 체인
