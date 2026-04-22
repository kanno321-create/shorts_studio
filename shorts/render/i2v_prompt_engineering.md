---
category: render
status: ready
tags: [render, i2v, prompt, kling, veo, runway, templates]
updated: 2026-04-20
source_notebook: shorts-production-pipeline-bible
---

# I2V Prompt Engineering — 3원칙 + Templates A/B/C

> 2026-04-20 세션 #24 박제. Image-to-Video (Kling 2.6 Pro / Veo 3.1 Fast / Runway) 영상 생성에서 **prompt 가 품질의 결정 요소** (대표님 원칙 ≈ 100%). Kling adapter 교체나 비용 절감보다 prompt 3원칙 준수가 실패율을 결정한다. Research 6개 이상 소스 triangulate + 3-way 실측 검증.
>
> **Single source of truth**: memory `feedback_i2v_prompt_principles`. 이 wiki 는 Tier 2 render 카테고리에 공개 레퍼런스 복사본 — 원칙 개정 시 memory + 이 파일 동시 업데이트.

## 3원칙

### 원칙 1 — Camera Lock 명시 필수

카메라 motion 을 명시하지 않으면 모델이 **임의로 zoom/pan 추가** → depth/scale drift.

**Why**: 세션 #24 실측에서 "camera holds still" 없는 prompt 가 컵 30% 확대 유발 (Gen-3a Turbo 실패 케이스).

**How to apply**:

- 명시 문구: `"The camera holds still"`, `"static camera"`, `"camera locked"`, `"no camera motion"`
- 의도적 카메라 이동 시: `"slow dolly left"`, `"gentle push-in"` 같이 방향 + 속도 명시
- 의도 없으면 항상 lock

### 원칙 2 — Anatomy Positive Persistence (negative prompt 금지)

기존 anatomy 유지는 **positive state persistence** 로만. Negative prompt 는 **역효과**.

**Why**: Runway 공식 docs 원문 — *"Including a negative prompt may result in the opposite happening."* `"no extra arms"` 같은 지시가 extra arms 를 오히려 생성. Kling / Veo 도 동일 주의 적용 (Veo 3.1 Fast 는 명시 권고 없으나 동일 risk 추정 — research 기반 예방 조치).

**How to apply**:

| 패턴 | 예시 | 판정 |
|------|------|------|
| ✅ 유지 (positive persistence) | `"both hands remaining on the mug"` | 사용 |
| ✅ 유지 (positive persistence) | `"her left arm stays at her side"` | 사용 |
| ✅ 유지 (positive persistence) | `"preserving original finger positions"` | 사용 |
| ❌ 금지 (negative) | `"no extra arms"` | 역효과 유발 |
| ❌ 금지 (negative) | `"without duplication"` | 역효과 유발 |
| ❌ 금지 (negative) | `"avoid hand artifacts"` | 역효과 유발 |

### 원칙 3 — Micro Verb / Bounded Motion

Open-ended 동사 (lift, move, transform) 는 모델이 **end state 를 과장**. Micro verb 로 motion 범위를 암묵 제한.

**Why**: 세션 #24 실측 대조:

- `"lifts coffee cup toward camera"` → 컵이 코/이마 위까지 상승 ❌
- `"gently brings the cup upward toward her lips"` → lips 선에서 정확히 멈춤 ✅

**권장 micro verb**:

- `gently brings`, `softly tilts`, `slightly raises`, `barely shifts`
- `slowly turns`, `subtly adjusts`, `delicately holds`
- 방향/위치 수식어 동반: `toward her lips`, `a few degrees`, `just enough to`

**금지 verb**:

- `lifts`, `moves`, `raises`, `rotates`, `transforms` (boundary 없음)
- `runs`, `jumps`, `leaps` (짧은 clip 에서 실패율 높음)
- `suddenly`, `quickly`, `rapidly` (temporal discontinuity 유발)

## Verified Templates (세션 #24 3-way 실측)

### Template A — 보수적 (양손 유지 + 부드러운 컵 들어올리기)

```
The camera holds still as she gently brings the cup upward toward her lips,
both hands remaining on the mug. Her smile stays soft and natural throughout.
```

- 27 단어
- 3원칙 전부 적용 (camera lock + positive anatomy + micro verb)
- 실측: **Kling 2.6 Pro / Runway Gen-4.5 전부 합격**, Gen-3a Turbo 실패
- **smoke CLI default** — `scripts/smoke/phase091_stage2_to_4.py` MOTION_PROMPT
- 쓰임: 인물 양손 유지가 중요한 장면 (커피잔, 마이크, 책)

### Template B — 한 손 전환 (Sequential Prompting)

```
The camera holds still. Her left hand relaxes to her knee while her right
hand carefully guides the cup toward her lips. She takes a slow, gentle sip.
```

- 29 단어
- Sequential Prompting 활용 (3개 action 순차)
- 한 손 grip 으로 anatomy 복잡도 감소
- 쓰임: 한 손에서 다른 손으로 자연스러운 전환이 필요한 장면

### Template C — Micro-motion 전용 (가장 안전)

```
Static camera. She softly tilts the cup a few degrees toward herself,
both hands still holding it.
```

- 17 단어
- 가장 낮은 실패율
- 컷당 시각 변화 최소 — 여러 컷 조합 시 유용
- 쓰임: 제품 소개 컷, reaction shot, cutaway

## 3-way 실측 증거 (2026-04-20 세션 #24)

Anchor: `shorts_naberal/output/channel_art/profile_kr_bright.png` (1056×1056, 한국 여성, 양손 커피잔).
Prompt: Template A (27단어).
MP4 비교 파일: `output/prompt_template_test/{,gen45,kling26}/` — 동일 anchor + 동일 prompt 로 3 모델 생성.

| 모델 | 비용/5s | 지연 | 결과 |
|------|---------|------|------|
| Runway Gen-3a Turbo | $0.25 | 22s | ❌ 컵 30% 확대 + 코/이마 상승 + 뒤로 tilt (limb duplication 초기 실패) |
| Runway Gen-4.5 | $0.60 | 149s | ✅ "그나마 괜찮네" — lips 정확, 크기 유지, tilt 자연, 양손 유지 |
| **Kling 2.6 Pro** | **$0.35** | **~70s** | **✅ 우수** — Gen-4.5 5/5 기준 + 얼굴 측면→정면 subtle 회전 보너스 |

대표님 판정: **Kling 2.6 Pro 단일 primary 확정**. Veo 3.1 Fast 는 "정밀/세세한" motion 실패 시 fallback 역할 배치 (세션 #24 당시 3-way 에는 Veo 미포함 — Phase 10 필요 시 실측 추가).

## 모델별 Prompt 미묘한 차이

| 요소 | Kling 2.6 Pro | Veo 3.1 Fast | Runway (hold) |
|------|---------------|--------------|----------------|
| Negative prompt | ⚠️ 역효과 경고 (실측) | ❓ 미검증 (예방 조치로 미주입) | ✗ 공식 역효과 |
| Camera motion | 명시 필수 | 명시 필수 | 명시 필수 |
| 한국어 prompt | 품질 저하 경향 | ❓ 미검증 | 영어 권장 |
| Prompt 길이 | 20-40 단어 sweet spot | ❓ 미검증 | 20-40 단어 sweet spot |
| 얼굴 회전 자연성 | ✅ 우수 (측면↔정면) | ❓ 미검증 | ✅ (Gen-4.5) / ❌ (Gen-3a Turbo) |

## Fallback 규칙 (대표님 세션 #24 지침)

> "정밀하고 세세한걸 만들때 kling이 실패하면 veo 3.1로하면된다."

**Kling 2.6 Pro → Veo 3.1 Fast 전환 조건**:

1. 얼굴 micro-expression 시뮬레이션 필요
2. 손가락 articulation (펜 쥐기, 타이핑, 컵 손잡이 각도)
3. 머리카락 simulation (바람, 물, 젖은 머리)
4. 세밀한 light interaction (촛불, 반사, 역광 실루엣)
5. 3회 재시도 실패

비용 영향: $0.35 → $0.50 (43% 상승). 실패 빈도 모니터링 → Phase 10 batch patch window 에서 auto-route threshold 조정.

**Phase 9.1 구현 상태**:

- smoke CLI `scripts/smoke/phase091_stage2_to_4.py` 는 `--use-veo` 플래그로 **수동 전환**만 제공
- auto-route (Circuit Breaker + motion-type detector) 은 Phase 10 실패 패턴 축적 후 정식화 예정 (memory `project_video_stack_kling26` 참조)

## Workflow (NLM Step 2 → Kling/Veo)

1. **NLM Step 2** (scripter → NotebookLM 2-notebook RAG) 에서 scene 별 motion 기획
2. scene 복잡도 따라 Template A/B/C 선택 → `i2v_prompt` 필드 작성
3. **Kling 2.6 Pro** 기본 호출 (Template default = A)
4. 정밀 motion 요구 scene 에서 품질 미달 시 **Veo 3.1 Fast** fallback 전환
5. 실패 케이스는 `.claude/failures/FAILURES.md` append (D-13 30일 집약 파이프라인)
6. Phase 10 batch window 에서 prompt template 진화 / auto-route threshold 조정

## 원칙 개정 절차

이 3원칙은 세션 #24 실측 증거 기반. 개정 조건:

- Phase 10 운영 중 **3회 이상 3원칙 적용 prompt 가 실패**
- 또는 2026-06 이후 신규 I2V 모델 등장 시 재검증
- 개정 시 memory `feedback_i2v_prompt_principles` + 이 wiki 파일 **동시** 업데이트 (drift 방지)

## Related

- memory `feedback_i2v_prompt_principles` — 이 wiki 의 source of truth
- memory `project_video_stack_kling26` — 스택 전체 (Kling 2.6 primary + Veo 3.1 fallback, 세션 #26 rename)
- memory `project_shorts_production_pipeline` — 4-stage chain (Stage 4 motion prompt 가 이 3원칙 적용)
- memory `project_nlm_notebooks` — Step 2 `i2v_prompt` 필드 소비처
- [[remotion_kling_stack]] — 렌더 스택 overview + filter chain order + fallback 샷
- [[MOC]]
- `scripts/smoke/phase091_stage2_to_4.py` — Template A + Kling primary + `--use-veo` 플래그 reference 구현
- `output/prompt_template_test/{,gen45,kling26}/` — 3-way 실측 MP4 (동일 anchor + Template A)
