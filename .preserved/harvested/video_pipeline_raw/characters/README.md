# .preserved/harvested/video_pipeline_raw/characters/

Phase 16-03 harvest 확장. Incidents 채널 캐릭터 오버레이 PNG 아카이브. Phase 9.1 `CharacterRegistry` 통합 대상.

## 포함 파일 (4)

| 캐릭터 | 파일 | 크기 | 용도 |
|--------|------|------|------|
| 탐정 (주인공) | `incidents_detective_longform_a.png` | 715 KB | **기본 variant A** — TopBar 오른쪽 (characterRightSrc) |
| 탐정 (대체) | `incidents_detective_longform_b.png` | 718 KB | variant B — 감정/각도 차이 시 |
| 왓슨 (조수) | `incidents_assistant_jp_a.png` | 644 KB | **TopBar 왼쪽 (characterLeftSrc)** |
| 즌다 (시추견) | `incidents_zunda_shihtzu_a.png` | 751 KB | **제한 사용** — 몰입 방해 우려 (대표님 지시) |

## 배치 규칙 (Phase 16 Q4 locked)

- **좌 (characterLeftSrc) = 왓슨/assistant** — 질문자 역할, 왼쪽 위치 고정.
- **우 (characterRightSrc) = 탐정/detective** — 답변자 역할, 오른쪽 위치 고정.
- **좌우 반전 금지** — 시청자 인지 부하 최소화.
- **즌다 사용 시**: 탐정 정면 컷 대체 제한. "몰입 방해 최소화" 원칙 준수.

## 렌더링 규칙 (Plan 16-02 `ShortsVideo.tsx` 담당)

- **원형 크롭** — circle mask with border
- **Face zoom** — 얼굴 중심 zoom 2x
- **Border** — accentColor (incidents = `#FF3B30`) 2~4 px
- **Python 에서 이미지 변환 금지** — 포팅은 Remotion 측에서만.

## 정책

- **One-way harvest** (CLAUDE.md 금기 #6) — Source `shorts_naberal/output/_shared/characters/` **절대 수정 금지**.
- **Read-only attribute** — `attrib +R` (Windows) + `chmod -w` (POSIX) 적용.
- **CharacterRegistry 통합** — Phase 9.1 registry 는 episode 마다 어떤 variant 를 사용했는지 기록 (persona 연속성 보전).

## Source

`C:/Users/PC/Desktop/shorts_naberal/output/_shared/characters/*.png`

## Harvest Manifest

`.preserved/harvested/video_pipeline_raw/harvest_extension_manifest.json` — sha256 + size 박제.

## Phase 16 Usage

- Plan 16-04 asset-sourcer: episode 생성 시 `character_detective.png` + `character_assistant.png` 2 파일을 `output/<episode>/sources/` 로 선택적 복사 (variant 결정은 CharacterRegistry 조회 결과).
- Plan 16-02 `remotion_renderer.py` `_inject_character_props`: episode sources 에서 본 PNG 를 읽어 Remotion props 주입 (characterLeftSrc / characterRightSrc).

---

*Phase 16-03 harvest extension — 2026-04-22 / 나베랄 감마.*
