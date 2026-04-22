---
category: render
status: ready
tags: [render, remotion, kling, veo, shotstack, i2v, continuity_prefix]
updated: 2026-04-20
source_notebook: shorts-production-pipeline-bible
---

# Remotion + Kling 2.6 Pro I2V Render Stack (Veo 3.1 Fast Fallback)

> 2026 기준 shorts 렌더 스택 전체 도식 — Remotion v4 composition + **Kling 2.6 Pro primary I2V** + **Veo 3.1 Fast fallback** + Shotstack color+composite. T2V 금지 · K-pop 직접 사용 금지 · Selenium 금지 3대 hard constraint.
>
> **2026-04-20 세션 #24 최종 확정 (4차 번복 후):**
>
> 1. (오전) Runway Gen-4.5 primary (단순 hair/smile motion 기준)
> 2. (오후) Runway Gen-3a Turbo primary (비용 58% 절감 유혹)
> 3. (저녁) 복합 limb motion (커피잔 lift) 테스트에서 Gen-3a Turbo 실패 → Gen-4.5 "그나마 괜찮네" → Kling 2.6 Pro 실측 **Pareto-dominant** 확인 → Kling 2.6 primary
> 4. **(최종) Kling 2.6 Pro primary + Veo 3.1 Fast fallback** — 대표님 지침: "Kling 2.5-turbo deprecated 사용안하다. kling 2.6 사용, 정밀하고 세세한걸 만들때는 kling이 실패하면 veo 3.1로하면된다"
>
> 파일명 `remotion_kling_stack.md` 는 초기 결정 흔적(legacy). 내용은 최신 상태. Phase 10 정리 window 에 `remotion_i2v_stack.md` 로 rename 권장.

## Stack Overview

| Layer | Tool | Role | 비용 |
|-------|------|------|------|
| Composition | **Remotion v4** (Skills 네이티브) | React frame → MP4 조립, 타이포그래피, 모션 그래픽 | 로컬 렌더 (무료) |
| **Primary I2V** | **Kling 2.6 Pro** (fal.ai `kling-video/v2.6/pro/image-to-video`) | Anchor frame + prompt → 5s video clip (9:16 vertical). 한국인 얼굴·신체 움직임·립싱크 강점. | **$0.35/5s (~$0.07/sec)** |
| **Fallback I2V** | **Veo 3.1 Fast** (fal.ai `veo3.1/fast/image-to-video`) | Kling 실패 시 정밀/세세한 motion (얼굴 micro / 손가락 / 머리카락 / 미세 light). | **$0.50/5s ($0.10/sec)** |
| Hold (미호출) | Runway Gen-4.5 (`gen4.5`, 720:1280) | production path 제외. adapter 유지. flagship 수동 승격 여지. | $0.60/5s |
| Hold (미호출) | Runway Gen-3a Turbo (`gen3a_turbo`, 768:1280) | production path 제외. 복합 limb motion 실패 실증. | $0.25/5s |
| ~~Deprecated~~ | ~~Kling 2.5-turbo Pro~~ | fal.ai 에서 2.6 동가격 업그레이드 — 사용 금지 | — |
| Image Generation | **Nano Banana Pro** (`nano-banana-pro-preview` via Google genai SDK) | 캐릭터 레퍼런스 기반 scene image 생성 (stage 2 of 4-stage chain) | ~$0.04/image (2026-04 추정) |
| Color + Composite | **Shotstack** | 일괄 색보정 + continuity_prefix 자동 주입 + 최종 합성 | API tiered pricing |
| Audio Separation | **Typecast** → **ElevenLabs v3** | 한국어 TTS + timestamp → Shotstack merge | ~$20/월 + $0.12/1K chars |

### 2026-04-20 실측 비교 (동일 anchor + 동일 Template A prompt, 5s clip)

Anchor: `shorts_naberal/output/channel_art/profile_kr_bright.png` (1056×1056).
Prompt: Template A (27단어, 3원칙 적용) — `wiki/render/i2v_prompt_engineering.md` 참조.

| 모델 | File size | Wall time | Cost | 판정 |
|------|-----------|-----------|------|------|
| Runway Gen-3a Turbo | 2.2 MB | 21.2 s | $0.25 | ❌ 컵 30% 확대 + 코/이마 상승 + limb duplication |
| Runway Gen-4.5 | 2.5 MB | 149.3 s | $0.60 | ✅ "그나마 괜찮네" — lips 정확, 크기 유지 |
| **Kling 2.6 Pro** | **14.9 MB** | **~70 s** | **$0.35** | **✅ 우수 (Gen-4.5 5/5 기준 + 얼굴 측면↔정면 subtle 회전 보너스)** |

대표님 판정 (세션 #24): Kling 2.6 Pro 단일 primary 확정, Veo 3.1 Fast 를 "정밀/세세한" motion 전용 fallback 으로 배치.

### Veo 3.1 Fast fallback 발동 조건 (대표님 지침)

Kling 2.6 Pro 가 다음 케이스에서 실패 시 수동 `--use-veo` 플래그 또는 Phase 10 auto-route 로 전환:

1. **얼굴 micro-expression** — 입꼬리 미세 변화, 눈 깜빡임 리듬
2. **손가락 articulation** — 펜 쥐기, 타이핑, 컵 손잡이 각도
3. **머리카락 simulation** — 바람, 물, 젖은 머리
4. **세밀한 light interaction** — 촛불 flicker, 유리 반사, 역광 실루엣

비용 영향: $0.35 → $0.50 (43% 증가). 실패 빈도 모니터링 → Phase 10 batch window 에서 threshold 조정.

## 금지 사항 (hard constraints)

- **T2V 금지** (VIDEO-01, D-13) — text-to-video 직접 호출 금지. anchor frame 없이 Kling/Veo/Runway I2V 호출은 `T2VForbidden` exception. 모든 비디오 생성은 **Nano Banana Pro anchor frame → Kling 2.6 Pro I2V 2-step 필수** (4-stage chain 의 stage 2→4).
- **K-pop 직접 사용 금지** (AF-13) — KOMCA whitelist 외 음원 직접 포함 금지. 트렌딩 3~5초 sampling → royalty-free crossfade hybrid audio pipeline (T11).
- **Selenium 업로드 금지** (AF-8) — YouTube Data API v3 공식만. Selenium import 자체가 `pre_tool_use.py` regex 차단 대상.

## Filter chain order (D-17 Phase 5 + D-19 Phase 6)

Shotstack adapter가 `filters` 배열 빌드 시 다음 순서 엄격 준수:

1. **`continuity_prefix`** (first, D-19 LOCK) — channel_identity 색상 팔레트 + 카메라 렌즈 + 시각 스타일 주입. 순서 위반 시 pytest 실패.
2. **`color_grade`** — 장면별 톤 조정 (Shotstack ColorFilter).
3. **`saturation`** — 한국 시니어 skew (D-16) 채도 낮춤 (default -10%).
4. **`film_grain`** — 최종 질감 부여 (cinematic visual_style LOCK 시 강도 +5%).

## 영상/음성 분리 합성 (ORCH-10)

- **Typecast 호출** → 한국어 TTS + word-level timestamp JSON 반환
- **WhisperX forced alignment** → 자막 타이밍 정밀 ±50ms 이내 보정
- **Shotstack merge** → Remotion composition + **Kling 2.6 Pro I2V clips** + Typecast audio track + 자막 합성. 최종 1080p 9:16 MP4 출력.

## Fallback 샷 (ORCH-12)

- **재생성 루프 3회 초과 시 정지 이미지 + Ken Burns 줌인** — Kling primary + Veo fallback 둘 다 실패 / Circuit Breaker OPEN (3회 연속 실패 / 300s cooldown) 시 Nano Banana Pro 정지 이미지를 Remotion Ken Burns 효과로 replacement.
- **Ken Burns 구현**: 로컬 FFmpeg pan/zoom (shorts_naberal 방식, `scripts/orchestrator/api/ken_burns.py` KenBurnsLocal). Shotstack 클라우드 의존 제거 완료 (Phase 9.1 Plan 03).
- **적용 gate** — `ASSETS` / `THUMBNAIL` 2개 gate 만 fallback 허용. `SCRIPT`, `VOICE`, `METADATA`, `UPLOAD`, `MONITOR` gate 는 semantic 아티팩트 → fallback 금지, `RegenerationExhausted` raise.

## 모델별 입력 parameters (adapter 계약)

| Model | Endpoint | Aspect ratio | Negative prompt |
|-------|----------|--------------|------------------|
| Kling 2.6 Pro | `fal-ai/kling-video/v2.6/pro/image-to-video` | anchor 종횡비 자동 | 지원 (현재 adapter 내장 하드코드, i2v 3원칙 역효과 주의 — Phase 10 재검토) |
| Veo 3.1 Fast | `fal-ai/veo3.1/fast/image-to-video` | anchor 종횡비 자동 | 지원 불명확, 미주입 (research: negative prompt 역효과 경고 적용) |
| Runway Gen-4.5 (hold) | `gen4.5` | `"720:1280"` | 공식 역효과 경고 |
| Runway Gen-3a Turbo (hold) | `gen3a_turbo` | `"768:1280"`, `"1280:768"` | 공식 역효과 경고 |

**Adapter drift (Phase 10 batch window 정리 대상)**:

- `RunwayI2VAdapter.VALID_RATIOS_BY_MODEL` — `gen3a_turbo` 에 `"16:9"`, `"9:16"` 광고되나 실제 API 400 reject (deferred-items.md D091-DEF-01). production path 에서 Runway 를 미호출하므로 실패 경로 영향 없음 → **drift 비활성화 상태**.
- `KlingI2VAdapter.NEG_PROMPT` — 모듈 상수 하드코드. i2v_prompt_engineering 3원칙 "negative prompt 역효과" 와 상충 가능. Phase 10 에서 제거 / 조정 검토.
- 파일명 `remotion_kling_stack.md` → `remotion_i2v_stack.md` rename.
- NLM Step 2 output field `runway_prompt` → `i2v_prompt` rename.

## Related

- [[i2v_prompt_engineering]] — I2V prompt 3원칙 + Templates A/B/C + 3-way 실측 레퍼런스 (2026-04-20 세션 #24 신설)
- [[../continuity_bible/channel_identity]] — 5 구성요소 (색상 + 렌즈 + 스타일 + 오디언스 + BGM), prefix.json 직렬화 소스
- [[../algorithm/ranking_factors]] — 완주율/3초 retention 목표 → 렌더 품질 요구 수준
- [[MOC]]
- memory `project_video_stack_kling26` — 2026-04-20 Kling 2.6 Pro primary + Veo 3.1 Fast fallback 최종 확정 (세션 #26 rename, D091-DEF-02 #3 resolved)
- memory `project_shorts_production_pipeline` — 4-stage chain (레퍼런스 → Nano Banana Pro → NLM → Kling 2.6 Pro)
- memory `feedback_i2v_prompt_principles` — 3원칙 + Templates + fallback 조건 상세
