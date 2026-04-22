# .preserved/harvested/video_pipeline_raw/signatures/

Phase 16-03 harvest 확장. Incidents 채널 인트로 시그니처 자산 아카이브.

## 포함 파일

| 파일 | 크기 | 용도 |
|------|------|------|
| `incidents_intro_v4_silent_glare.mp4` | 1.70 MB | **production 채택** — Veo 3.1 Lite, 8s, 9:16, 1940s 누아르 탐정 (3/4 back → turning glare) |

## 제원 (channel-incidents/SKILL.md 기반)

- Veo 3.1 Lite, 8초 (Hook 시그니처 고정 9.0s — 약간의 freeze-frame 여유 포함), 9:16 (1080×1920 crop)
- 탐정 3/4 back → 수첩 → 몸 회전 → 고개 숙인 채 눈만 위로 올려 카메라 직시
- 1940s 누아르 (트렌치 코트, 검정 중절모, 담배·텍스트·로고·현대 요소 없음)
- 어두운 사무실, 원거리 창문 rim light, 미드나잇 블루 배경, 비 내리는 창문
- 생성 스크립트: `.preserved/harvested/video_pipeline_raw/generate_intro_signature.py` (재실행 시 Veo API 호출 발생 → **절대 금지**)

## 정책

- **Veo API 재호출 금지** (CLAUDE.md 금기 #11) — 본 파일 **재사용만 허용**. 복사/참조 only.
- **One-way harvest** (CLAUDE.md 금기 #6) — Source `shorts_naberal/output/_shared/signatures/` 는 **절대 수정 금지**. 본 디렉토리로 복사만, 역방향 write-back 금지.
- **Read-only attribute** — `attrib +R` (Windows) + `chmod -w` (POSIX) 적용 예정 (pytest 검증 시점).

## Source

`C:/Users/PC/Desktop/shorts_naberal/output/_shared/signatures/incidents_intro_v4_silent_glare.mp4`

## Harvest Manifest

`.preserved/harvested/video_pipeline_raw/harvest_extension_manifest.json` — sha256 + size 박제.

## Phase 16 Usage

- Plan 16-02 `remotion_renderer.py`: episode 생성 시 이 파일을 `output/<episode>/sources/intro_signature.mp4` 로 복사.
- Plan 16-03 subtitle-producer: Hook 9.0s 구간과 동기화 (자막 균등 분배).
- Plan 16-04 asset-sourcer: visual_spec.clips[0] 에 intro_signature.mp4 삽입 (type=video, duration 270 frames @ 30fps).

---

*Phase 16-03 harvest extension — 2026-04-22 / 나베랄 감마.*
