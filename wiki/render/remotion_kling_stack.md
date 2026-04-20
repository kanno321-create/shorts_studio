---
category: render
status: ready
tags: [render, remotion, runway, gen3a_turbo, kling, shotstack, i2v, continuity_prefix]
updated: 2026-04-20
source_notebook: shorts-production-pipeline-bible
---

# Remotion + Runway Gen-3a Turbo I2V Render Stack

> 2026 기준 shorts 렌더 스택 전체 도식 — Remotion v4 composition + **Runway Gen-3a Turbo primary I2V** + Kling 2.5-turbo Pro backup + Shotstack color+composite. T2V 금지 · K-pop 직접 사용 금지 · Selenium 금지 3대 hard constraint.
>
> **2026-04-20 세션 #24 재결정:** 이전 "Kling 2.6 Pro primary / Runway Gen-3 Alpha Turbo backup" 체제를 3-way 실측 비교 후 교체. Runway Gen-3a Turbo 를 primary (경제성 + 품질 충분), Kling 2.5-turbo Pro 를 backup 으로 반전. Gen-4.5 는 품질 우위이나 비용 2.4배 + 지연 6배로 기각 (자동 경로에서 제외; flagship 수동 승격만 가능). 파일명 `remotion_kling_stack.md` 는 초기 결정 흔적 — Phase 10 rename batch 대상.

## Stack Overview

| Layer | Tool | Role | 비용 |
|-------|------|------|------|
| Composition | **Remotion v4** (Skills 네이티브) | React frame → MP4 조립, 타이포그래피, 모션 그래픽 | 로컬 렌더 (무료) |
| Primary I2V | **Runway Gen-3a Turbo** (`gen3a_turbo`, 768:1280) | Anchor frame + prompt → 5s video clip (9:16 vertical) | **$0.05/sec (5 credits/sec, $0.25/5s clip)** |
| Backup I2V | **Kling 2.5-turbo Pro** (fal.ai) | Runway 실패 / 재시도 3회 초과 시 fallback | ~$0.07/sec ($0.35/5s clip) |
| Flagship I2V (수동) | **Runway Gen-4.5** (`gen4.5`, 720:1280) | 월간 tier-1 영상 수동 승격 시만 | $0.12/sec ($0.60/5s clip) |
| Image Generation | **Nano Banana Pro** (`nano-banana-pro-preview` via Google genai SDK) | 캐릭터 레퍼런스 기반 scene image 생성 (stage 2 of 4-stage chain) | ~$0.04/image (2026-04 추정) |
| Color + Composite | **Shotstack** | 일괄 색보정 + continuity_prefix 자동 주입 + 최종 합성 | API tiered pricing |
| Audio Separation | **Typecast** → **ElevenLabs v3** | 한국어 TTS + timestamp → Shotstack merge | ~$20/월 + $0.12/1K chars |

### 2026-04-20 실측 비교 (동일 anchor + 동일 복합 prompt, 5s clip)

| Model | File size | Wall time | Cost | 판정 |
|-------|-----------|-----------|------|------|
| Kling 2.5-turbo Pro (fal.ai) | 14.9 MB | 96.9 s | $0.35 | backup (품질 OK, 비용 중간) |
| Runway Gen-4.5 | 2.5 MB | 129.2 s | $0.60 | flagship 전용 (품질 최고, 비용 최고) |
| **Runway Gen-3a Turbo** | **2.2 MB** | **21.2 s** | **$0.25** | **primary (품질 충분, 경제성 최고)** |

Anchor: `shorts_naberal/output/channel_art/profile_kr_bright.png` (1056×1056).
Prompt: 3 sequential actions (hand→face→hair / smile+head tilt / eyes down→up) + 1 parallel ambient (candlelight flicker + breeze).
대표님 판정 (세션 #24): Runway 품질 우위 → Gen-3a Turbo 단일 primary 확정.

## 금지 사항 (hard constraints)

- **T2V 금지** (VIDEO-01, D-13) — text-to-video 직접 호출 금지. anchor frame 없이 Runway/Kling I2V 호출은 `T2VForbidden` exception. 모든 비디오 생성은 **Nano Banana Pro anchor frame → Runway Gen-3a Turbo I2V 2-step 필수** (4-stage chain 의 stage 2→4).
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
- **Shotstack merge** → Remotion composition + Runway Gen-3a Turbo I2V clips + Typecast audio track + 자막 합성. 최종 1080p 9:16 MP4 출력.

## Fallback 샷 (ORCH-12)

- **재생성 루프 3회 초과 시 정지 이미지 + Ken Burns 줌인** — Runway + Kling backup 둘 다 실패 / Circuit Breaker OPEN (3회 연속 실패 / 300s cooldown) 시 Nano Banana Pro 정지 이미지를 Remotion Ken Burns 효과로 replacement.
- **Ken Burns 구현**: 로컬 FFmpeg pan/zoom (shorts_naberal 방식). Shotstack 클라우드 의존 제거 예정 (Phase 10 재설계 대상 — 현재 `shotstack.create_ken_burns_clip()` 사용 중은 drift).
- **적용 gate** — `ASSETS` / `THUMBNAIL` 2개 gate 만 fallback 허용. `SCRIPT`, `VOICE`, `METADATA`, `UPLOAD`, `MONITOR` gate 는 semantic 아티팩트 → fallback 금지, `RegenerationExhausted` raise.

## 모델별 valid ratios (adapter 재설계 대상)

| Model | Valid ratios (Runway API 실측) |
|-------|-------------------------------|
| `gen3a_turbo` | `"16:9"`, `"9:16"`, `"768:1280"`, `"1280:768"` |
| `gen4.5` | `"720:1280"` (Gen-3a 와 호환 안 됨) |
| `gen4_turbo` / `gen4` | TBD (Phase 10 확인) |

**adapter drift** (Phase 10 재설계): `RunwayI2VAdapter.DEFAULT_RATIO` 는 단일 상수 — 모델 교체 시 ratio 자동 조정 로직 필요. 현재 `gen3a_turbo` 기준 `768:1280` 하드코드.

## Related

- [[../continuity_bible/channel_identity]] — 5 구성요소 (색상 + 렌즈 + 스타일 + 오디언스 + BGM), prefix.json 직렬화 소스
- [[../algorithm/ranking_factors]] — 완주율/3초 retention 목표 → 렌더 품질 요구 수준
- [[MOC]]
- memory `project_video_stack_runway_gen4_5` — 2026-04-20 Gen-3a Turbo primary 확정 기록
- memory `project_shorts_production_pipeline` — 4-stage chain (레퍼런스 → Nano Banana Pro → NLM → Runway)
