# SESSION LOG — shorts

## Session #1 — 2026-04-18 (스튜디오 창업)

### 핵심 결정
1. naberal_harness v1.0 기반 신규 스튜디오 창업

## Session #24 — 2026-04-20 (YOLO 6세션 연속, Phase 9 + 9.1 + I2V stack final)

### 진행 범위 (단일 세션)
- Phase 9: Documentation + KPI Dashboard + Taste Gate — 14 commits, ALL_PASS
- Phase 9.1: Production Engine Wiring (decimal phase insertion) — 20+ commits, ALL_PASS
- Architecture fix: anthropic SDK → Claude CLI subprocess (Max 구독 정합)
- I2V stack 3회 번복 후 Kling 2.6 Pro + Veo 3.1 Fast 2-tier 최종 확정
- Deep research 18개 소스 (Runway I2V prompt engineering)
- 메모리 박제 4건 신규/갱신

### 핵심 결정 (이번 세션)
1. **Claude Code Max 구독** 활용 — `anthropic` Python SDK 직접 호출 영구 금지
2. **I2V Primary = Kling 2.6 Pro** (`fal-ai/kling-video/v2.6/pro/image-to-video`, $0.35/5s, 70s latency)
3. **I2V Fallback = Veo 3.1 Fast** (`fal-ai/veo3.1/fast/image-to-video`, $0.50/5s, 정밀/세세 motion)
4. **Kling 2.5-turbo Pro deprecated**, endpoint 2.6 으로 교체
5. **I2V Prompt 3원칙** 영구 박제: Camera Lock / Anatomy Positive Persistence / Micro Verb
6. Phase 9.1 HUMAN-UAT 2건 pending (clip.mp4 재생성 평가 + ElevenLabs Korean voice)

### 실측 증거 (3-way I2V 비교)
동일 anchor + Template A prompt:
- Gen-3a Turbo: $0.25 / 23.7s / ❌ 팔 복제, 컵 코 위로, 30% 확대
- Gen-4.5: $0.60 / 149.3s / ✅ "그나마 괜찮네"
- **Kling 2.6 Pro: $0.35 / 70.0s / ✅ 우수 + 얼굴 회전 자연** ← Pareto-dominant

### Git Commit 주요 (세션 #24, shorts_studio)
```
ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)
8af5063 fix(09.1): architecture correction — anthropic SDK → Claude CLI subprocess
c86c570 docs(phase-9.1): evolve PROJECT.md
60dee8e test(09.1): persist VERIFICATION + HUMAN-UAT
3798b08..8dd3901 Phase 9.1 chain (20+ commits)
3292142 fix(drift): Runway Gen-3a Turbo primary (후 번복)
Phase 9: 14 commits (7708e3b → 5597440)
```

### 미완료 박제 batch (다음 세션 최우선)
1. smoke CLI refactor (Kling primary + Veo fallback + Template A default)
2. wiki/render/MOC.md + remotion_kling_stack.md drift 복구
3. docs/ARCHITECTURE.md 3지점 drift 복구
4. 신규 wiki/render/i2v_prompt_engineering.md
5. 09.1-HUMAN-UAT.md + deferred-items.md 갱신
6. 통합 commit

### 메모리 박제 신규/갱신 (4건)
- `project_video_stack_runway_gen4_5.md` 전면 재작 (Kling 2.6 + Veo 3.1)
- `feedback_i2v_prompt_principles.md` 신규 (3원칙 + Templates)
- `project_claude_code_max_no_api_key.md` 신규 (ANTHROPIC_API_KEY 금지)
- `project_shorts_production_pipeline.md` 신규 (4-stage chain)

### 다음 세션 진입점
- `WORK_HANDOFF.md` §"미완료 박제 batch" 5항목부터
- `/clear` 후 MEMORY.md 로 context 복원, WORK_HANDOFF.md 로 작업 상태 복원
- Phase 10 착수는 박제 batch + HUMAN-UAT 2건 완료 후
