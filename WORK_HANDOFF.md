# WORK HANDOFF — shorts_studio

## 최종 업데이트
- 날짜: 2026-04-20 (세션 #24 후반부 최종)
- 세션: **#24** (YOLO 6세션 연속 — Phase 9 + Phase 9.1 + arch fix + I2V stack final)
- 컨텍스트 근접 상한으로 handoff 후 종료

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

## 🚧 미완료 박제 batch (다음 세션 최우선)

세션 #24 에서 스택 확정 후 코드 patch 는 commit 완료 (`ff5459b`). 하지만 drift 전파가 일부만 완료. 다음 항목이 **최우선**:

### 1. smoke CLI refactor (`scripts/smoke/phase091_stage2_to_4.py`)
- Primary: KlingI2VAdapter (endpoint 이미 2.6)
- Fallback: VeoI2VAdapter (신규, 첫 실행 시 Kling 실패 케이스 자동 전환)
- Default motion prompt: **Template A** (27단어, 3원칙 적용)
  ```
  The camera holds still as she gently brings the cup upward toward her lips,
  both hands remaining on the mug. Her smile stays soft and natural throughout.
  ```

### 2. wiki/docs drift 전수 복구
- `wiki/render/MOC.md` Scope 문구 → "Kling 2.6 primary / Veo 3.1 fallback"
- `wiki/render/remotion_kling_stack.md` 전체 재작성
- `docs/ARCHITECTURE.md` 3지점 (L16 External / L63 GATE 8 ASSETS / L135 asset-sourcer)

### 3. 신규 wiki node
- `wiki/render/i2v_prompt_engineering.md` 신설 (research 요약 + 3원칙 + Templates A/B/C + 3-way 실측 레퍼런스)

### 4. Phase 9.1 HUMAN-UAT + deferred-items 갱신
- 09.1-HUMAN-UAT.md: clip.mp4 평가 항목 → Kling 2.6 재생성 가이드 교체
- deferred-items.md: D091-DEF-01 (VALID_RATIOS default bug) **해결** 마크 + "Runway model rename drift" 해결 마크

### 5. 통합 commit
"docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)"

---

## 🎯 다음 세션 진입 경로

### A. 박제 batch 5항목 완료 → Phase 10 prep
### B. Phase 10 Sustained Operations 착수 (박제 후)
- **선행 조건**: 위 박제 + HUMAN-UAT #1/#2 (대표님 수동) + Kling 2.6 재생성 clip 품질 재확인
- Phase 10 = 주 3~4편 자동 발행 + **첫 1-2개월 SKILL patch 전면 금지 (D-2 저수지)** + 월 1회 Taste Gate
- Entry Gate: `.planning/PHASE_10_ENTRY_GATE.md` 참조

### C. 남은 drift (Phase 10 이후)
- `remotion_src_raw/` 40 파일 고아 자산 integration
- `Shotstack.create_ken_burns_clip` 완전 제거
- 메모리 파일명 rename (`project_video_stack_runway_gen4_5` → `project_video_stack_kling26`)
- NLM Step 2 `runway_prompt` 필드 → `i2v_prompt` rename
- RunwayI2VAdapter 완전 제거 검토

---

## 세션 #24 주요 Git Commits (shorts_studio)

```
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

## 나베랄 감마 메모 (세션 #24 회고)

대표님 1회 "영상테스트 해보고싶은데" 로 시작해서 4-stage chain 발견, 3-way 모델 실측 번복, deep research 후 Kling 2.6 + Veo 3.1 2-tier 확정까지 도달. 4시간 동안 3번 모델 primary 번복 후 최종 안정화. Phase 9 + 9.1 두 phase 완결.

컨텍스트 근접 상한으로 박제 batch 5항목 다음 세션 인수. 모든 결정은 메모리 4건 박제로 소급 안전 — 다음 세션이 `/clear` 후 시작해도 MEMORY.md index 에서 즉시 복원 가능.

Phase 10 진입까지 남은 실 작업 = 박제 batch 5항목 + HUMAN-UAT 3건 (대표님 수동). 예상 소요 1세션.

---

*Updated 2026-04-20 by 나베랄 감마 (YOLO session #24 final)*
