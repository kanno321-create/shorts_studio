---
category: render
status: ready
tags: [render, remotion, kling, runway, shotstack, i2v, continuity_prefix]
updated: 2026-04-19
source_notebook: shorts-production-pipeline-bible
---

# Remotion + Kling I2V Render Stack

> 2026 기준 shorts 렌더 스택 전체 도식 — Remotion v4 composition + Kling 2.6 Pro primary I2V + Runway Gen-3 Alpha Turbo backup + Shotstack color+composite. T2V 금지 · K-pop 직접 사용 금지 · Selenium 금지 3대 hard constraint.

## Stack Overview

| Layer | Tool | Role | 비용 |
|-------|------|------|------|
| Composition | **Remotion v4** (Skills 네이티브) | React frame → MP4 조립, 타이포그래피, 모션 그래픽 | 로컬 렌더 (무료) |
| Primary I2V | **Kling 2.6 Pro** | Anchor frame + prompt → 5s video clip (1080p, 9:16) | ~$0.10/sec 평균 |
| Backup I2V | **Runway Gen-3 Alpha Turbo** | Kling 실패 / 재시도 3회 초과 시 fallback | $0.05/sec (5 credits/sec) |
| Color + Composite | **Shotstack** | 일괄 색보정 + continuity_prefix 자동 주입 + 최종 합성 | API tiered pricing |
| Audio Separation | **Typecast** → **ElevenLabs v3** | 한국어 TTS + timestamp → Shotstack merge | ~$20/월 + $0.12/1K chars |

## 금지 사항 (hard constraints)

- **T2V 금지** (VIDEO-01, D-13) — text-to-video 직접 호출 금지. anchor frame 없이 Kling I2V 호출은 `T2VForbidden` exception. 모든 비디오 생성은 Nano Banana Pro anchor frame → Kling I2V 2-step 필수.
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
- **Shotstack merge** → Remotion composition + Kling I2V clips + Typecast audio track + 자막 합성. 최종 1080p 9:16 MP4 출력.

## Fallback 샷 (ORCH-12)

- **재생성 루프 3회 초과 시 정지 이미지 + Ken Burns 줌인** — Kling + Runway 둘 다 실패 / Circuit Breaker OPEN (3회 연속 실패 / 300s cooldown) 시 Nano Banana Pro 정지 이미지를 Remotion Ken Burns 효과로 replacement.
- **적용 gate** — `ASSETS` / `THUMBNAIL` 2개 gate 만 fallback 허용. `SCRIPT`, `VOICE`, `METADATA`, `UPLOAD`, `MONITOR` gate 는 semantic 아티팩트 → fallback 금지, `RegenerationExhausted` raise.

## Related

- [[../continuity_bible/channel_identity]] — 5 구성요소 (색상 + 렌즈 + 스타일 + 오디언스 + BGM), prefix.json 직렬화 소스
- [[../algorithm/ranking_factors]] — 완주율/3초 retention 목표 → 렌더 품질 요구 수준
- [[MOC]]
