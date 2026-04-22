---
name: feedback_harvest_missing_korean_welsh_corgi
description: 조수 캐릭터 (incidents 채널) 는 한국판 웰시 코기 — `.preserved/harvested/` 에는 일본판 `_jp_` 만 존재. episode-specific source 사용 필수.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/sources/character_assistant.png (1.38 MB, 한국판 웰시 코기 SSOT)
  - .preserved/harvested/video_pipeline_raw/characters/incidents_assistant_jp_a.png (일본판 검은 머리 인간 — 잘못 사용하면 안 됨)
  - output/ryan-waller/sources/character_assistant.png (659 KB, v1 잘못된 파일)
failure_mapping:
  - FAIL-3-v1: 조수 캐릭터가 일본판 (검은 머리 인간) — 한국판 웰시 코기여야 함
---

# feedback: incidents 조수 = 한국판 웰시 코기 (일본판 사용 금지)

## 규칙

**incidents 채널 (한국어판) 조수 캐릭터는 웰시 코기 + 셜록 스타일 모자 + 돋보기 + 책장 배경.** 일본판 (mary-celeste-jp 등) 은 검은 머리 인간 조수 — **다른 캐릭터**. 혼용 금지.

### 파일 위치 SSOT (한국판)

```
C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/sources/character_assistant.png
  — 1,382,150 bytes (1.38 MB), 2026-04-14 생성
  — 한국 이 채널의 레퍼런스 episode (Zodiac Killer) source 에 유일 존재
```

### harvest 누락 구조

`.preserved/harvested/video_pipeline_raw/characters/` 에는:
- `incidents_detective.png` ✅ 탐정 OK
- `incidents_assistant_jp_a.png` 🔴 **일본판** (`_jp_` suffix — 검은 머리 인간)
- `incidents_assistant_jp_b.png` 🔴 일본판 variant

한국판 웰시 코기는 `_shared/characters/` 에 **harvest 되지 않았다** — `zodiac-killer/sources/` episode-specific 폴더에만 존재.

### 교정 (즉시 조치)

```bash
cp "C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/sources/character_assistant.png" \
   "output/ryan-waller/sources/character_assistant.png"
```

### 재발 방지 (Phase 17)

Phase 17 에 episode-source harvest 보강 Plan 추가:
- `.preserved/harvested/video_pipeline_raw/characters/incidents_assistant_ko.png` 로 한국판 캐노니컬 복사
- sha256 manifest 에 등록
- `reference_signature_and_character_assets.md` 메모리 업데이트 (한국판 SSOT 경로 추가)

## Why (왜)

Phase 16-03 W0-HARVEST 가 `_shared/characters/` 4개 파일만 매핑. 원래 shorts_naberal 의 캐릭터 자산 구조는 episode 별로 중복 배치 (mary-celeste-jp 은 일본판, zodiac-killer 는 한국판). Harvest 스크립트가 `_shared/` 만 스캔했기 때문에 episode-specific 캐릭터 (한국판 웰시 코기) 가 누락.

세션 #33 Ryan Waller v1 에서 내가 `.preserved/harvested/video_pipeline_raw/characters/incidents_assistant_jp_a.png` 를 "incidents 조수" 로 오인 사용 → 대표님이 첫 검수에서 "한국어버전은 상단 좌측 조수는 웰시코기임" 지적.

## How to apply (언제 적용)

- **모든 새 에피소드 제작 시작 시**: `output/<episode>/sources/character_assistant.png` 를 `shorts_naberal/output/zodiac-killer/sources/character_assistant.png` 에서 복사. **`_shared/characters/_jp_*` 은 일본판 에피소드 전용**.
- asset-sourcer / thumbnail-designer / director 에이전트가 "incidents 조수 캐릭터" 참조 시 이 메모리를 로드하여 경로 확인.
- Phase 17 harvest 보강 완료되면 경로가 `.preserved/harvested/video_pipeline_raw/characters/incidents_assistant_ko.png` 로 이동 — SSOT 경로 업데이트 예정.

## 검증

```bash
# 1. 파일 크기 체크 (한국판 웰시 코기는 1.38 MB)
stat -c "%s" output/ryan-waller/sources/character_assistant.png
# → 1382150 (1.38 MB) 이어야 함. 659797 (일본판 인간) 이면 실패.

# 2. 시각 검수 (대표님 ear/eye verify)
# 한국판 = 웰시 코기 + 탐정 모자 + 돋보기, 일본판 = 검은 머리 인간
```

## Cross-reference

- `reference_signature_and_character_assets` — Phase 16 자산 SSOT (🔴 한국판 경로 추가 필요)
- `project_channel_bible_incidents_v1` — 채널바이블 조수 캐릭터 스펙
- 세션 #33 Ryan Waller v1 FAIL-3
