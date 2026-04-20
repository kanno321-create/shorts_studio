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

## Session #25 — 2026-04-20 (박제 batch 전수 복구 + origin push)

### 진행 범위 (단일 세션, 연속 로드)
- 세션 #24 미완 박제 batch 5항목 전부 완결
- 실 touch 범위는 handoff 기준 대비 **7 파일 / ARCHITECTURE.md 5지점** 으로 확장 (drift cascade 추가 발견)
- 통합 commit 4eb864d (7 files, +399 / -81)
- `git push origin main` 완료 (dadfe58..4eb864d, github.com/kanno321-create/shorts_studio)

### 완결 항목
1. **smoke CLI refactor** (`scripts/smoke/phase091_stage2_to_4.py`) — Runway Gen-3a Turbo → Kling 2.6 Pro primary + `--use-veo` 플래그 + Template A (27단어, 3원칙) motion prompt 내재화. dry-run 양 경로 통과.
2. **wiki/render/MOC.md** — Scope 재작성 + 5-model 실측 비교표 + Planned Nodes (i2v_prompt_engineering checked, kling/veo node placeholders 신설)
3. **wiki/render/remotion_kling_stack.md** — 전면 재작성 (파일명 legacy, Phase 10 rename 대상)
4. **wiki/render/i2v_prompt_engineering.md** — **신규** (3원칙 + Templates A/B/C + 3-way 실측 + fallback 규칙)
5. **docs/ARCHITECTURE.md** — 5지점 drift 수정 (handoff 지시 3 + 추가 발견 2: L187 Tier 2 render + L238-241 Video Generation Chain)
6. **09.1-HUMAN-UAT.md** — Test #1 Kling 2.6 Pro 재생성 가이드 + procedure ($0.39 예상, KLING_API_KEY + GOOGLE_API_KEY)
7. **deferred-items.md** — D091-DEF-01 상태 Medium → Low (DEACTIVATED by stack switch) + D091-DEF-02 신규 (7 cleanup items → Phase 10 batch window)

### 핵심 결정 / 발견
1. **"Deactivated" vs "Resolved" 구분** — 코드 bug 는 그대로지만 실패 경로에서 이탈한 경우 "해결" 표시는 거짓. "Deactivated by stack switch" 가 정직한 상태. Phase 10 Runway adapter 완전 제거 시 최종 "Resolved" flip.
2. **auto-route 는 Phase 9.1 out-of-scope** — memory 명시: "Phase 10 실패 패턴 누적 후 auto-route 규칙 정식 확정". smoke CLI 는 `--use-veo` 수동 플래그만 제공.
3. **Template A 의 코드 내재화** — 단순 문자열 교체가 아니라 3원칙을 prompt 에 영구 박제. 향후 smoke 실행하는 누구든 자동으로 품질 기준 따름 (failure-mode-by-construction).
4. **Drift cascade 전형** — 스택 1개 교체로 downstream 참조 5배 이상 파급. 박제 batch 설계 시 "N 지점" 보다 "드리프트 cascade 전체" 를 기준 삼아야 함.

### Git Commit (세션 #25)
```
4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)
(origin push: dadfe58..4eb864d → main)
```

### 미완료 (HUMAN-UAT 4건, 대표님 수동 only)
Phase 9.1:
1. UAT #1 — Kling 2.6 Pro smoke clip.mp4 재생성 + 품질 평가 ($0.39)
2. UAT #2 — ElevenLabs 한국어 voice 계정 확인

Phase 9 (세션 #24 잔류):
3. UAT #1 — 30분 온보딩 stopwatch 실측
4. UAT #2 — Taste Gate UX "편함" 주관 평가

### 다음 세션 진입점
- Phase 10 진입 = HUMAN-UAT 4건 모두 PASS 후
- AI 쪽 추가 작업 없음 — 대표님 수동 검증 대기
- Phase 10 batch window cleanup backlog 는 실 실패 데이터 축적 후 (D-2 저수지 1-2개월)
