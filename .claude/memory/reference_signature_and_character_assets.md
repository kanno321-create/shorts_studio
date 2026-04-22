---
name: reference_signature_and_character_assets
description: Incidents 채널의 인트로 시그니처 + 캐릭터 PNG + outro 처리 미해결 항목 실물 위치 맵. Phase 16 production integration 의 asset 조달 SSOT.
type: reference
---

# Incidents 채널 Signature + Character 자산 실물 매핑

**작성**: 2026-04-22 세션 #33, Phase 16 research 중 file mapping
**검증**: 실 파일 시스템 확인 (ls / stat)
**Veo 방침**: CLAUDE.md 금기 #11 엄수 — 이 파일들은 **기존 자산 참조·복사만**, 신규 Veo API 호출 금지.

---

## 1. 인트로 시그니처 (v4 확정)

**실물 위치**: `C:/Users/PC/Desktop/shorts_naberal/output/_shared/signatures/`

| 버전 | 파일 | 크기 | 상태 |
|------|------|------|------|
| v1 | `incidents_intro_v1_desk.mp4` | 2.44 MB | 기각 (SKILL.md: "분위기만 좋음") |
| v2 | `incidents_intro_v2_silhouette.mp4` | 1.43 MB | 기각 (SKILL.md: "동작 없음") |
| v3 | `incidents_intro_v3_turning_glare.mp4` | 1.87 MB | 기각 (SKILL.md: "분위기 약함") |
| **v4** | **`incidents_intro_v4_silent_glare.mp4`** | **1.70 MB** | **✅ 채택 — production 표준** |

**v4 제원** (channel-incidents/SKILL.md 기반):
- Veo 3.1 Lite, 8초, 9:16
- 탐정 3/4 back → 수첩 → 몸 회전 → 고개 숙인 채 눈만 위로 올려 카메라 직시
- 1940s 누아르 (트렌치 코트, 검정 중절모)
- 어두운 사무실, 원거리 창문 rim light, 미드나잇 블루 배경, 비 내리는 창문
- 담배·텍스트·로고·현대 요소 없음
- 생성 스크립트: `.preserved/harvested/video_pipeline_raw/generate_intro_signature.py` (4814 bytes, 재실행은 Veo API 호출 필요 → 금지)

**Phase 16-03 처리**:
- Task 1: `_shared/signatures/incidents_intro_v4_silent_glare.mp4` 를 `.preserved/harvested/video_pipeline_raw/signatures/` 로 추가 harvest (현재 mp4 는 harvest 되지 않음, 바이너리 대용량으로 이전 제외)
- Task 2: `output/<episode>/sources/intro_signature.mp4` 로 episode-level 복사 로직 — `asset-sourcer` 또는 `remotion_renderer.py` 책임 (Plan 16-02/16-04 에서 결정)
- Task 3: Hook clip duration 9.0s 하드 고정 (channel-incidents/SKILL.md §"시그니처 재생성" 규칙 준수)

---

## 2. 캐릭터 PNG (탐정 + 왓슨)

**실물 위치**: `C:/Users/PC/Desktop/shorts_naberal/output/_shared/characters/`

| 캐릭터 | 파일 | 용도 |
|--------|------|------|
| 탐정 (사건기록부 주인공) | `incidents_detective_longform_a.png` | 기본 variant A |
| 탐정 (대체) | `incidents_detective_longform_b.png` | variant B (감정/각도 차이 시) |
| 왓슨 (조수, human) | `incidents_assistant_jp_a.png` | TopBar 오른쪽 오버레이 |
| 즌다 (시추견, mascot) | `incidents_zunda_shihtzu_a.png` | 대체 오버레이 (대표님 지시 시: "즌다 과다 등장 몰입 방해" — 제한적 사용) |

**Phase 16-04 처리**:
- `asset-sourcer` 가 episode 생성 시 `_shared/characters/` 에서 `output/<episode>/sources/character_detective.png` + `character_assistant.png` 로 복사.
- Remotion props `characterLeftSrc` / `characterRightSrc` 매핑 (visual_spec.json:18~19 참조).
- 원형 크롭 + border + face zoom 은 `ShortsVideo.tsx` 측에서 처리 (Python 에서 이미지 변환 금지).

---

## 3. 아웃로 시그니처 — ✅ RESOLVED (2026-04-23 세션 #34 v3)

**결론 (옵션 C 입증)**: `_shared/signatures/` 에는 부재하지만, 각 에피소드의 `sources/` 에 **`outro_signature.mp4` 가 episode-local 자산으로 배치됨**. incidents 채널은 공용 outro 한 개를 각 에피소드에 복사해 사용.

**실물 위치 전수 (확인)**:
- `shorts_naberal/output/zodiac-killer/sources/outro_signature.mp4` (2,082,298 bytes)
- `shorts_naberal/output/db-cooper/sources/outro_signature.mp4`
- `shorts_naberal/output/dyatlov-pass/sources/outro_signature.mp4`
- `shorts_naberal/output/elisa-lam/sources/outro_signature.mp4`
- `shorts_naberal/output/mary-celeste/sources/outro_signature.mp4`
- 기타 incidents 에피소드 공통

**내용** (video 추정): 탐정 정면 → 뒤돌아 걸어감 (feedback_outro_signature 스타일 가이드 준수)

**copy 방법**: 새 에피소드 제작 시 script 초반에 복사
```bash
cp "C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/sources/outro_signature.mp4" \
   "output/<episode>/sources/outro_signature.mp4"
```

**visual_spec 반영**: `sources_manifest["outro_signature"] = "outro_signature.mp4"` → `visual_spec_builder.build()` 가 자동으로 마지막 clip 으로 append (Option A programmatic OutroCard 대신 실 mp4 사용).

**세션 #34 v3 교훈 (대표님 직접 지적 "아웃드로 시그니처 영상은 왜 안가져오노")**:
- v2 까지는 "outro_signature=None" 으로 Option A (programmatic) 택했으나, 실 영상 시그니처 존재를 인지 못함
- v3 에서 zodiac-killer 에서 복사 → visual_spec 의 마지막 clip 으로 자동 배치

---

## 4. 에피소드 표준 구조 (zodiac-killer 기준)

**경로**: `C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/`

| 파일 | 역할 |
|------|------|
| `final.mp4` | Remotion 합성 완료 출력 (~60~130초, 1080×1920) |
| `narration.mp3` | TTS 산출 (Typecast Morgan preset) |
| `scene-manifest.json` | 씬 구조 (scripter→assembler 중간 산출) |
| `script.json` | 대본 (Hook/Body/CTA 구조 + section[].narration) |
| `source.md` | NotebookLM 1차 자료 (source-grounded) |
| `sources/` | 자료 이미지 폴더 (b-roll, 사건 자료 photos — 영상:이미지 ≥30% 강제) |
| `subtitles_remotion.ass` | 단어단위 자막 (Aegisub v4+ 포맷) |
| `subtitles_remotion.json` | 단어단위 JSON (Remotion 직접 import) |
| `subtitles_remotion.srt` | 호환성 SubRip (백업) |
| `subtitles_remotion/` | 자막 생성 중간 산출물 디렉토리 |
| `visual_spec.json` | **Remotion props** (channelName, titleLine1/2, subtitleHighlightColor, characterLeftSrc/RightSrc, clips[], audioSrc, durationInFrames, transitionType) |
| `blueprint.json` | Pre-script blueprint (우리 BLUEPRINT GATE 산출 대응) |
| `metadata.json` | YouTube 메타 (title/description/tags) |
| `_upload_script.json` | 업로드 설정 (privacy, AI disclosure, thumbnail path) |
| `_run_tts.py` | TTS 실행 one-shot 스크립트 (에피소드 전용 wrapper) |

**Phase 16 Plan 매핑**:
- 16-01 영향 없음 (채널바이블만)
- 16-02 — `final.mp4` 를 렌더하는 Remotion 진입점 + Python 래퍼 `remotion_renderer.py` 책임
- 16-03 — `subtitles_remotion.{ass,json,srt}` + intro/outro 시그니처 + 캐릭터 오버레이 책임
- 16-04 — `visual_spec.json` + `scene-manifest.json` + `sources/` 디렉토리 생성 책임 (`asset-sourcer` 확장)

---

## 5. Harvest 확장 액션 (Phase 16-03 Task 1 에서 실행)

**필요 추가 harvest** (현재 `.preserved/harvested/` 에 없음, 대용량 바이너리):

```
shorts_naberal/output/_shared/signatures/
  incidents_intro_v4_silent_glare.mp4    (1.70 MB) ← 필수
  (선택) documentary_intro/outro.mp4, wildlife_intro/outro.mp4 ← 향후 Phase 17+
shorts_naberal/output/_shared/characters/
  incidents_detective_longform_a.png      ← 필수
  incidents_detective_longform_b.png      ← variant
  incidents_assistant_jp_a.png            ← 필수
  incidents_zunda_shihtzu_a.png           ← 제한적
```

**복사 대상**: `.preserved/harvested/video_pipeline_raw/signatures/` + `.preserved/harvested/video_pipeline_raw/characters/`
**복사 후**: `attrib +R /S /D` 적용 (Windows 읽기전용) + `chmod -R a-w` (POSIX)
**원본 shorts_naberal 수정 없음** — 단방향 복사만 (CLAUDE.md 금기 #6 준수).

---

## 6. Cross-reference

- `.claude/memory/reference_production_gap_map.md` — 11 누락 컴포넌트 중 "인트로/아웃로 시그니처" + "탐정·왓슨 오버레이" 가 이 파일의 (1), (2), (3) 에 대응.
- `.claude/memory/reference_harvested_full_index.md` — harvest 인덱스 (Phase 16-03 Task 1 완료 후 이 파일도 갱신 필요).
- `.planning/phases/16-production-integration-option-a/16-RESEARCH.md` — Phase 16 research 원본 (1259줄).
- `.preserved/harvested/skills_raw/channel-incidents/SKILL.md` — Hook 시그니처 재사용 패턴 상세 (lines 558~645).
