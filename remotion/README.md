# shorts-remotion — Phase 16-02

Remotion 4.x TypeScript 프로젝트. `scripts/orchestrator/api/remotion_renderer.py` (Python bridge) 가 `npx remotion render src/index.ts ShortsVideo out.mp4 --props=...` 호출.

## Environment verified (2026-04-22)
- Node: v22.18.0 (>=16 required, >=18 recommended)
- npm: 11.5.2
- npx: 11.5.2
- Remotion: installed via `npm install` (Wave 0 Task 16-02-W0-NPM-INSTALL)
- ffmpeg: 8.0.1 (system PATH)
- ffprobe: 8.0.1 (system PATH)

## 이식 출처
- `.preserved/harvested/remotion_src_raw/` (TypeScript 소스, 1:1 복사)
- `.preserved/harvested/video_pipeline_raw/remotion_render.py` (Python bridge 참고, 1162 lines)
- CLAUDE.md 금기 #11: Veo API 신규 호출 금지 (기존 자산 재사용만)

## Smoke 렌더

```bash
cd remotion
npm run render:smoke
```

smoke_props.json 은 `fixtures/smoke_props.json` 에 존재 — zodiac-killer visual_spec 복사본.

## 주요 상수 (수정 절대 금지 — DESIGN_SPEC.md SSOT)
- VIDEO_W = 1080
- VIDEO_H = 1920
- TOP_BAR_H = 320 (캐릭터 좌우 원형 오버레이 + 타이틀)
- BOTTOM_BAR_H = 333 (구독/좋아요 + seriesPart)
- FPS = 30
- codec = h264
