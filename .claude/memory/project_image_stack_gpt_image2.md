---
name: project_image_stack_gpt_image2
description: 정지 이미지 anchor 생성 = OpenAI gpt-image-2 (ChatGPT Images 2.0 "ducktape") primary. Nano Banana 대체 확정 (2026-04-22 대표님 판정)
type: project
---

# 정지 이미지 스택: gpt-image-2 Primary

**결정일**: 2026-04-22
**결정자**: 대표님
**대체 대상**: Nano Banana (Gemini 2.5 Flash Image) — 기존 primary, 이번 교체로 **보조/폴백**으로 강등

## 결정 사항

Shorts 파이프라인의 **anchor frame 생성 + 썸네일 생성**에 쓰이는 정지 이미지 모델을 **OpenAI `gpt-image-2`** 로 전환한다.

- API endpoint: `openai.images.edit(model="gpt-image-2", image=..., prompt=..., quality="medium", size="1024x1024")`
- 권장 티어: **medium** ($0.034/장) — 일상 anchor
- 썸네일 고가치건: **high** ($0.21/장) — 월 4편 기준 $0.84
- reference 전달: reference PNG bytes + prompt (image-to-image editing)

## 근거 (실험 결과, 2026-04-22 기록)

**실험 스크립트**: `scripts/experiments/compare_image_models.py` (50장 비교 매트릭스)
**결과 경로**: `outputs/compare_ducktape_vs_nanobanana/`
**Kling I2V 검증**: `scripts/experiments/kling_compare_i2v.py` → `kling_videos/kling26_{gpt_image2,nanobanana}_*.mp4`

**대표님 관찰 요약**:
1. gpt-image-2 의 그래픽 퀄리티(cinematic photorealism · 조명 · 질감)가 Nano Banana 를 **압도**
2. Nano Banana 는 캐릭터 identity 재현(각도·표정 자연 변화)에서 약간 우위
3. gpt-image-2 는 reference face-lock 이 강해 "복제" 경향 — 다만 **prompt 조정으로 완화 가능**
4. 어좁이 현상은 reference 이미지가 close-up 포트레이트라 생긴 파생효과 — 모델 자체 한계 아님
5. **Kling 2.6 Pro I2V 에 anchor 투입 시 그래픽 퀄리티 차이가 영상에 그대로 전이** — 검증 완료

## 핵심 논리

**"I2V 는 anchor 퀄리티를 증폭한다. 일관성은 후공정 가능, 퀄리티는 불가역."**

- Kling 2.6 Pro 는 anchor 의 photorealism·조명·질감을 보존·증폭 → anchor 품질이 영상 품질 상한 결정
- Shorts Core Value = "외부 수익 발생" = CTR·시청유지율 = 시각적 임팩트 → 그래픽 퀄리티가 수익 축 직결
- 일관성 문제는 prompt engineering (`"natural pose variation, dynamic angle"` 추가) 으로 완화 가능
- 그래픽 퀄리티는 모델 특성이라 prompt 로 극복 불가

## 비용 비교 (월 4편 anchor 8장 기준)

| 스택 | 월 비용 | 퀄리티 |
|---|---|---|
| 기존 (NB $0.039) | $1.24 | flat |
| **신규 (gpt medium $0.034)** | **$1.09** | cinematic (+30% 저렴) |
| 신규 (gpt high $0.21) | $6.72 | photorealism 극대 |

## 보완 필요사항

1. **prompt 완화** — 기존 `"preserve exact face"` 같은 강제 키워드 제거, `"natural pose variation, dynamic angle, identity consistency"` 로 교체
2. **reference 선택 규칙** — close-up 포트레이트 사용 시 어좁이 발생 → 전신/상반신 ref 권장
3. **`asset-sourcer` 에이전트 업데이트** — primary provider 교체, fallback chain: gpt-image-2 → Nano Banana → raise
4. **`ins-license` whitelist 등록** — OpenAI Images API 를 royalty-free whitelist 에 추가 (AUDIO-04 mirror)

## Next Action (별도 세션)

- [ ] `scripts/orchestrator/api/gpt_image2.py` adapter 작성 (NanoBananaAdapter 패턴 미러)
- [ ] `asset-sourcer` 에이전트 프롬프트 업데이트
- [ ] `thumbnail-designer` 에이전트 프롬프트 업데이트 (high 티어 명시)
- [ ] 기존 `nanobanana.py` fallback 으로 유지 (삭제 금지)
- [ ] Phase 회귀 테스트: 985+ 테스트 중 image provider 참조 부분 업데이트

## 보안 Note

OpenAI API key 는 2026-04-22 세션 중 대표님이 채팅에 평문 전송 → `.env` 등록됨. **revoke 후 재생성 필요** — OpenAI 콘솔 → API keys → 해당 key 비활성화 → 신규 발급 → `.env` 교체.

## 참고 자료

- OpenAI 공식 공지 (2026-04-21): https://community.openai.com/t/introducing-gpt-image-2-available-today-in-the-api-and-codex/1379479
- TechCrunch: https://techcrunch.com/2026/04/21/chatgpts-new-images-2-0-model-is-surprisingly-good-at-generating-text/
- 과금 구조: input image $8/M tokens, output image $30/M tokens (대략 low $0.006 / medium $0.034 / high $0.21 per 1024² image)
