---
name: feedback_i2v_prompt_principles
description: I2V 영상 생성 프롬프트 3원칙 — Camera Lock 명시 + Anatomy Positive Persistence + Micro Verb. Template A/B/C 검증됨
type: feedback
---

# I2V Prompt 3원칙

**박제 trigger**: 세션 #24 Deep Research (18개 소스, Tier 1/2/3 HIGH confidence) + 실측 3-way 검증.
**연구 보고서**: `.planning/research/runway_i2v_prompt_engineering_2026_04.md`

## 3원칙

### 원칙 1: Camera Lock 명시
- **Why**: I2V 모델은 기본적으로 카메라 움직임을 추가하려는 bias. anchor frame 구도 유지가 shorts 세로 포맷에서 필수.
- **How to apply**: prompt 에 `"camera holds still"` 또는 `"static shot"` 문구 명시. 모든 Template 공통.

### 원칙 2: Anatomy Positive Persistence (negative prompt 절대 금지)
- **Why**: negative prompt("no extra arms", "no duplication") 는 오히려 해당 구조를 활성화. Kling/Veo 모두 positive-only 로 작동.
- **How to apply**: "팔 복제 금지" 대신 **"natural single arm, anatomically stable posture"** 같이 **긍정형**으로 표현. NEG_PROMPT 하드코드 재검토 필요 (D091-DEF-02 의 KlingI2VAdapter 이슈).

### 원칙 3: Micro Verb
- **Why**: 큰 동작 verb ("lifts", "raises") 는 30%+ 확대/팔복제 유발. Shorts I2V 는 **미세 움직임**이 품질 기준.
- **How to apply**: `"gently brings"`, `"slowly tilts"`, `"softly moves"` 같은 micro verb + adverb 조합. "lifts" NOT 허용.

## Templates (세션 #24 실측 검증)

- **Template A** (27단어, 3원칙 내재화) — smoke CLI 에 영구 박제 (`scripts/smoke/phase091_stage2_to_4.py`)
- **Template B** — 복합 motion (확장 예정)
- **Template C** — cinematic (Veo fallback 특화)

## 실측 증거 (3-way, 동일 anchor)

- Gen-3a Turbo: Template A 적용에도 ❌ 팔 복제 (원칙 3 한계 초과)
- Gen-4.5: ✅ "그나마 괜찮네"
- **Kling 2.6 Pro: ✅ 우수 + 얼굴 회전 자연** ← Pareto-dominant

## Fallback 조건 (Kling → Veo)

3원칙 적용해도 Kling 실패 시 Veo 전환:
- 얼굴 micro-expression, 손가락 articulation, 머리카락 simulation, 미세 light

## Related

- [project_video_stack_kling26](project_video_stack_kling26.md) — Fallback 트리거 상세
- `wiki/render/i2v_prompt_engineering.md` — 실 문서 (Templates + fallback 규칙)
