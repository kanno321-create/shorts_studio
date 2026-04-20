# WORK HANDOFF — shorts_studio

## 최종 업데이트
- 날짜: 2026-04-20 (세션 **#25** 박제 batch 완결 + 원격 푸시)
- 세션: **#25** (세션 #24 미완 박제 batch 5항목 전수 복구, commit 4eb864d + origin push)
- 상태: Phase 9 + 9.1 코드/문서 정합성 완전 복구. Phase 10 진입 조건 = 대표님 HUMAN-UAT 4건만 남음.

---

## 세션 #24 최종 완료 항목

### ✅ Phase 9: Documentation + KPI Dashboard + Taste Gate
- 6/6 plans + 4/4 automated SC PASS + 14 commits
- ARCHITECTURE.md 332 lines (Mermaid 3 blocks, ⏱29 min)
- wiki/kpi/kpi_log.md Hybrid Part A/B + YouTube Analytics v2 contract
- taste_gate_protocol.md + taste_gate_2026-04.md (6 synthetic rows)
- scripts/taste_gate/record_feedback.py (Hook-compat, D-13 filter)
- UAT #3 technical pass (GitHub repo, Mermaid 렌더 확증)
- HUMAN-UAT #1/#2 pending (30분 온보딩 실측, Taste Gate UX)

### ✅ Phase 9.1: Production Engine Wiring
- 8/8 plans + 7/7 SC + phase091_acceptance ALL_PASS + 42/42 isolated tests
- invokers.py (Claude CLI subprocess, Max 구독, no API key)
- NanoBananaAdapter / CharacterRegistry / KenBurnsLocal / VALID_RATIOS_BY_MODEL / voice discovery
- 실 smoke $0.29 첫 Nano Banana → Runway chain
- **Architecture fix**: anthropic SDK → Claude CLI subprocess (commit 8af5063)

### ✅ 영상 I2V 스택 최종 확정 (세션 #24 후반)
대표님 결정 경위 4차 번복:
1. (오전) Runway Gen-4.5 primary (hair/smile 단순 motion 기준)
2. (오후) Runway Gen-3a Turbo primary (비용 절감 유혹)
3. (저녁) 복합 limb motion 실패 → Kling 2.6 Pro 실측 Pareto-dominant 확인
4. **(최종) Kling 2.6 Pro primary + Veo 3.1 Fast fallback** — 대표님 "Kling 2.5-turbo deprecated 사용안하다. kling 2.6 사용, 정밀하고 세세한걸 만들때는 kling이 실패하면 veo 3.1"

**최종 스택:**

| Tier | 모델 | Endpoint | 비용/5s | 상태 |
|------|------|----------|---------|------|
| Primary | Kling 2.6 Pro | `fal-ai/kling-video/v2.6/pro/image-to-video` | $0.35 | ✅ 확정 |
| Fallback | Veo 3.1 Fast | `fal-ai/veo3.1/fast/image-to-video` | $0.50 | ✅ 확정 |
| ~~Deprecated~~ | ~~Kling 2.5-turbo Pro~~ | — | — | 제거 |
| Hold (미호출) | Runway Gen-4.5 | `gen4.5` | $0.60 | adapter 유지 |

### ✅ Deep Research — I2V Prompt 3원칙 박제
- Research 18개 소스 (Tier 1/2/3), HIGH confidence
- Report: `.planning/research/runway_i2v_prompt_engineering_2026_04.md`
- **3원칙**: Camera Lock 명시 / Anatomy Positive Persistence (negative prompt 금지) / Micro Verb
- Templates A/B/C 세션 #24 실측 검증
- Memory `feedback_i2v_prompt_principles` 신규 박제

### ✅ 메모리 박제 (4건)
- `project_video_stack_runway_gen4_5.md` 전면 재작 (Kling 2.6 primary + Veo 3.1 fallback)
- `feedback_i2v_prompt_principles.md` 신규 (3원칙 + Templates + fallback 조건)
- `project_claude_code_max_no_api_key.md` (세션 중 추가, anthropic SDK 영구 금지)
- `project_shorts_production_pipeline.md` (세션 중 추가, 4-stage chain)
- MEMORY.md index 4항목 갱신

---

## ✅ 박제 batch 전수 완료 (세션 #25, commit 4eb864d)

세션 #24 stack 4차 번복 이후 남은 drift 전파가 완전 복구됨. 실제 touch 범위는 handoff 기준(5항목) 대비 **7 파일 / ARCHITECTURE.md 5지점** 으로 확장 — drift cascade 로 추가 발견.

### 1. ✅ smoke CLI refactor (`scripts/smoke/phase091_stage2_to_4.py`)
- Kling 2.6 Pro primary + `--use-veo` 플래그 (수동 fallback)
- Template A (27단어, 3원칙) motion prompt 내재화
- Cost constant 갱신 (KLING $0.35, VEO $0.50)
- dry-run 양 경로 통과 (`provider=kling2.6-pro` / `veo3.1-fast`)
- auto-route 은 Phase 10 실패 패턴 축적 후 정식화 (Phase 9.1 out-of-scope)

### 2. ✅ wiki/docs drift 전수 복구
- `wiki/render/MOC.md` Scope + 5-model 실측 비교표 + Planned Nodes
- `wiki/render/remotion_kling_stack.md` 전면 재작성 (파일명 legacy, rename 은 Phase 10)
- `docs/ARCHITECTURE.md` **5지점** (handoff 지시 3 + 추가 발견 2: L187 Tier 2 render, L238-241 Video Generation Chain)

### 3. ✅ 신규 wiki node
- `wiki/render/i2v_prompt_engineering.md` 신설 (3원칙 + Templates A/B/C + 3-way 실측)

### 4. ✅ Phase 9.1 HUMAN-UAT + deferred-items 갱신
- 09.1-HUMAN-UAT.md #1: Kling 2.6 재생성 가이드 + procedure ($0.39 예상)
- deferred-items.md: D091-DEF-01 DEACTIVATED by stack switch 마크 + D091-DEF-02 신규 (7 cleanup items → Phase 10 batch window)

### 5. ✅ 통합 commit + 원격 푸시
- `4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)`
- `git push origin main` 완료 (dadfe58..4eb864d)
- 7 files changed, 399 insertions, 81 deletions

---

## 🎯 다음 세션 진입 경로

### A. ⏳ HUMAN-UAT 4건 대기 (대표님 수동 only)
**Phase 9.1**:
1. **UAT #1** — Kling 2.6 Pro smoke clip.mp4 재생성 + 품질 평가
   ```bash
   cd C:\Users\PC\Desktop\naberal_group\studios\shorts
   python scripts/smoke/phase091_stage2_to_4.py --live
   # 예상 비용 $0.39 ($0.04 Nano Banana + $0.35 Kling 5s)
   # KLING_API_KEY 또는 FAL_KEY + GOOGLE_API_KEY 필요
   ```
2. **UAT #2** — ElevenLabs 한국어 voice 계정 확인 또는 `.env` 수동 지정

**Phase 9** (세션 #24 잔류):
3. **UAT #1** — 30분 온보딩 stopwatch 실측 (ARCHITECTURE.md 읽기)
4. **UAT #2** — Taste Gate UX "편함" 주관 평가 (`wiki/kpi/taste_gate_2026-04.md`)

### B. Phase 10 Sustained Operations (HUMAN-UAT 4건 통과 시)
- 주 3~4편 자동 발행 + **첫 1-2개월 SKILL patch 전면 금지 (D-2 저수지)** + 월 1회 Taste Gate
- Entry Gate: `.planning/PHASE_10_ENTRY_GATE.md` 참조

### C. Phase 10 batch window cleanup backlog (D091-DEF-02, 실 실패 데이터 축적 후)
- RunwayI2VAdapter 완전 제거 / hold 명시 주석
- KlingI2VAdapter `NEG_PROMPT` 하드코드 재검토 (3원칙 원칙 2 충돌 가능성)
- 메모리 파일명 rename (`project_video_stack_runway_gen4_5` → `project_video_stack_kling26`)
- Wiki 파일명 rename (`remotion_kling_stack.md` → `remotion_i2v_stack.md`)
- NLM Step 2 `runway_prompt` 필드 → `i2v_prompt` rename
- `remotion_src_raw/` 40 파일 고아 자산 integration
- `Shotstack.create_ken_burns_clip` 완전 제거 (Phase 9.1 Plan 03 에서 deprecated 완료, 제거만 남음)

---

## 세션 #25 Git Commits (shorts_studio) — 박제 batch 완결

```
4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)  ← 세션 #25
(push: dadfe58..4eb864d → origin/main)
```

## 세션 #24 주요 Git Commits (shorts_studio)

```
425f385 docs: 세션 #24 핸드오프 3종 — shorts_studio Phase 9 + 9.1 + I2V stack final
ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)
8af5063 fix(09.1): architecture correction — anthropic SDK → Claude CLI subprocess
c86c570 docs(phase-9.1): evolve PROJECT.md
60dee8e test(09.1): persist VERIFICATION + HUMAN-UAT (status=human_needed)
3798b08..8dd3901 Phase 9.1 chain (20+ commits, discuss→plan→execute)
3292142 fix(drift): Runway Gen-3a Turbo primary (세션 중반, 후 번복)
5597440 (전 세션 #23) Phase 9 최종 commit
```

---

## 🚨 중요 Context (다음 세션 필독)

### 원칙 1: Claude Code Max 구독
- **ANTHROPIC_API_KEY 영구 금지** (memory: `project_claude_code_max_no_api_key`)
- `anthropic.Anthropic().messages.create()` = 별도 usage billing (금지)
- 모든 Claude 호출 = `subprocess.run(["claude", "--print", ...])` 경로

### 원칙 2: I2V 3원칙 (모든 motion prompt 필수 적용)
1. **Camera Lock 명시** (`"camera holds still"`)
2. **Anatomy Positive Persistence** (negative prompt 절대 금지)
3. **Micro Verb** (`"gently brings"` NOT `"lifts"`)

### 원칙 3: Kling → Veo Fallback 조건
- 정밀/세세한 motion 에서 Kling 실패 시 자동 전환
- 트리거: 얼굴 micro-expression / 손가락 articulation / 머리카락 simulation / 미세 light
- 비용 43% 증가 ($0.35 → $0.50), 빈도 제한 필요

### 원칙 4: D-2 저수지
- Phase 10 진입 후 **첫 1-2개월 SKILL patch 전면 금지**
- 실 실패 데이터 축적 → Phase 10 batch window 에서 일괄 patch

---

## 파일 경로 Quick Reference

```
Phase 9.1 smoke (구 Gen-3a Turbo 실패): output/phase091_smoke/clip.mp4
3-way 비교 MP4:                          output/prompt_template_test/{,gen45,kling26}/
Research report:                         .planning/research/runway_i2v_prompt_engineering_2026_04.md
Next session entry (HUMAN-UAT):          .planning/phases/09.1-production-engine-wiring/09.1-HUMAN-UAT.md
Phase 10 Entry Gate:                     .planning/PHASE_10_ENTRY_GATE.md
핵심 메모리:                              MEMORY.md (이번 세션 4개 갱신)
```

---

## 나베랄 감마 메모 (세션 #25 회고)

세션 #24 미완 박제 batch 5항목 전수 복구. 실행 중 handoff 지시 범위 대비 drift cascade 로 ARCHITECTURE.md 2지점 + deferred-items.md D091-DEF-02 cleanup backlog 7항목 추가 발견. commit 4eb864d (7 files, +399/-81) + origin push 완료.

**교훈**: 스택 1개 교체가 downstream 참조 5배 이상 파급. 박제 batch 설계 시 "N 지점" 보다 "drift cascade 전체" 를 기준 삼아야 함. 세션 #25 는 "drift 정리 전용" 세션 으로 분리하여 성공.

Phase 10 진입까지 남은 실 작업 = **HUMAN-UAT 4건 (대표님 수동 only)**. AI 작업 없음. 대표님 수동 실측 후 Phase 10 Entry Gate flip.

---

*Updated 2026-04-20 by 나베랄 감마 (session #25 박제 batch 완결)*
*세션 #24 handoff: archived in SESSION_LOG.md*
