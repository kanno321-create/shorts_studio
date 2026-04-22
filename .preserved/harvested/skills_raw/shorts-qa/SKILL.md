---
name: shorts-qa
description: "QA 검수 에이전트 스킬. 기술 34항목(qa_check.py) + DESIGN_BIBLE 9항목 = 43항목 통합 체크리스트."
user-invocable: false
---

# Shorts QA -- 품질 검수 전문가

## 역할

렌더링된 final.mp4을 43항목 체크리스트로 검증한다. 34개 자동화 기술 항목(qa_check.py 실행)과 9개 수동 콘텐츠 항목(DESIGN_BIBLE.md 기반)으로 구성된다. 검수 결과는 항목 ID별 pass/fail로 보고한다.

---

## 자동화 기술 검사 (34항목)

### QA-CF: Container Format (8항목)

| ID | 검사 | Shorts 기준 | Video 기준 |
|----|------|-------------|------------|
| QA-CF-01 | Resolution | 1080x1920 | 1920x1080 |
| QA-CF-02 | Aspect ratio | 0.5625 (9:16) +/-0.01 | 1.7778 (16:9) +/-0.01 |
| QA-CF-03 | Duration max | 60.0s | 900.0s |
| QA-CF-04 | Duration min | 15.0s | 300.0s |
| QA-CF-05 | Video codec | H.264 | H.264 |
| QA-CF-06 | Pixel format | yuv420p | yuv420p |
| QA-CF-07 | Audio codec | AAC | AAC |
| QA-CF-08 | Audio sample rate | 44100 or 48000 Hz | 44100 or 48000 Hz |

**Critical**: 모든 QA-CF 항목은 반드시 통과해야 함.

### QA-VQ: Visual Quality (5항목)

| ID | 검사 | 기준 |
|----|------|------|
| QA-VQ-09 | No white frames | avg RGB ALL > 245 AND stddev < 10 이면 불합격 |
| QA-VQ-10 | No black frames | brightness < 5 이면 불합격 |
| QA-VQ-11 | Visual change interval | max_static_seconds 내 장면 변화 필요 (shorts: 5s, video: 8s) |
| QA-VQ-12 | No static clip | QA-VQ-11과 동일 로직, 별도 보고 |
| QA-VQ-13 | File size | shorts: 5-50MB, video: 50-500MB |

**Critical**: 모든 QA-VQ 항목은 반드시 통과해야 함.

### QA-SQ: Subtitle Quality (4항목)

| ID | 검사 | 기준 |
|----|------|------|
| QA-SQ-14 | Subtitles present | 프레임 하단 영역에서 텍스트 감지 |
| QA-SQ-15 | Subtitle readability | 명암비 >= 4.5:1 |
| QA-SQ-16 | Subtitle position | 텍스트가 프레임 하위 25% 영역 내 |
| QA-SQ-17 | No subtitle overflow | 텍스트가 수평 경계 내 |

### QA-AS: Audio Sync (3항목)

| ID | 검사 | 기준 |
|----|------|------|
| QA-AS-18 | Audio-video duration match | 오디오-비디오 길이 차이 1초 이내 |
| QA-AS-19 | Audio not silent | 피크 진폭 > -40dB |
| QA-AS-20 | Audio starts promptly | 0.5초 내 신호 시작 |

### QA-MC: Metadata Consistency (2-3항목)

| ID | 검사 | Shorts | Video |
|----|------|--------|-------|
| QA-MC-21 | Clip count match | manifest 클립 수 == 추정 씬 수 +/-1 | 동일 |
| QA-MC-22 | Duration match | manifest 총 길이 == 비디오 길이 2초 이내 | 동일 |
| QA-MC-23 | Minimum clip count | **Shorts에서 제외** | min_clips >= 30 |

### QA-EQ: Editing Quality (6항목)

| ID | 검사 | 기준 |
|----|------|------|
| QA-EQ-01 | Zoom/motion effect rate | >= 50% 클립에 모션 효과 |
| QA-EQ-02 | Transition diversity | >= 3종 트랜지션 타입 |
| QA-EQ-03 | Text overlay count | key_text 3-6개 |
| QA-EQ-04 | Karaoke subtitle existence | output 디렉터리에 .ass 파일 존재 |
| QA-EQ-05 | BGM ducking applied | mixed_audio.mp3 존재 |
| QA-EQ-06 | Clip dedup | 모든 clip original_url이 고유 |

비차단(non-critical): 불합격해도 전체 통과 가능.

### QA-YC: YouTube Compliance (6항목)

| ID | 검사 | 기준 | 등급 |
|----|------|------|------|
| QA-YC-01 | Script uniqueness | 최근 10개 대본 대비 similarity < 0.40 | CRITICAL |
| QA-YC-02 | Hook diversity | 최근 훅 대비 similarity < 0.50 | CRITICAL |
| QA-YC-03 | Visual variety | 고유 클립 비율 >= 70% | IMPORTANT |
| QA-YC-04 | TTS provider quality | provider != edge-tts | IMPORTANT |
| QA-YC-05 | Section count minimum | shorts >= 3, video >= 5 | IMPORTANT |
| QA-YC-06 | AI disclosure present | metadata.json ai_disclosure == true | CRITICAL |

**Critical**: QA-YC 항목 중 CRITICAL 등급은 반드시 통과해야 함.

### QA-AI: AI Clip Quality (4항목, 동적)

| ID | 검사 | 기준 |
|----|------|------|
| QA-AI-01 | AI clip file existence | AI 클립 파일 존재 + 0바이트 아님 |
| QA-AI-02 | AI clip resolution | >= 720p (너비 또는 높이) |
| QA-AI-03 | AI clip duration | 2-15초 범위 |
| QA-AI-04 | AI clip count cap | max_ai_clips_per_short 이하 (기본: 3) |

Phase 30에서 추가. AI 클립이 없으면 이 카테고리는 건너뜀. AI 클립 이슈가 없으면 QA-AI-00 (pass) 1건만 기록.

---

## DESIGN_BIBLE 콘텐츠 검사 (9항목)

| ID | 검사 | 검증 방법 |
|----|------|-----------|
| DB-01 | Video source has no Pexels/Pixabay | metadata provider 태그 전부 검증 (pexels/pixabay 0건) |
| DB-02 | Person matching | 언급된 인물이 화면에 등장하는지 확인 |
| DB-03 | Content matching | 각 장면 영상이 내레이션 내용과 직접 관련 |
| DB-04 | Subtitle word/phrase-level fast switching | 단어 하이라이트 방식, 문장 통째 금지 |
| DB-05 | Title 2-line, bold, keyword color highlight, fixed | 시각적 확인 |
| DB-06 | Design matches references | DESIGN_SPEC.md 레퍼런스와 비교 |
| DB-07 | Voice uses designated voice (Changsu/Jungi) | 오디오 확인 |
| DB-08 | Structure: hook -> body -> CTA | 대본 구조 확인 |
| DB-09 | Evidence included (real video/photo/capture) | 시각적 확인 |

**수동 검사**: qa_check.py가 자동 채점하지 않음. 에이전트가 플래그하고 사람이 최종 승인.

---

## 스코어링

- **자동화 점수**: passed_items / total_items
- **통과 기준**: shorts >= 27/34, video >= 28/35
- **필수 통과**: 모든 QA-CF, QA-VQ 항목 + QA-YC CRITICAL 항목 (QA-YC-01, 02, 06)
- **DESIGN_BIBLE 항목**: 자동 점수에 미포함 -- 별도 수동 리뷰
- **총 항목 수**: shorts 34 (자동) + 9 (콘텐츠) = 43, video 35 (자동) + 9 (콘텐츠) = 44

---

## 파이프라인 모드

- **Shorts (기본)**: 34 자동 항목, QA-MC-23 제외
- **Video (--pipeline video)**: 35 자동 항목, QA-MC-23 포함 (min clips >= 30)
- **실행 명령**:
  ```
  scripts/video-pipeline/.venv/Scripts/python.exe scripts/video-pipeline/qa_check.py \
    --video "path/final.mp4" \
    --manifest "path/scene-manifest.json" \
    --audio "path/narration.mp3" \
    [--pipeline video] \
    [--script "path/script.json"] \
    [--metadata "path/metadata.json"] \
    [--history-dir "path/history/"]
  ```

---

## 재시도 로직

- **최대 자동 재시도**: 2회 (attempt_count < 2)
- **실패 라우팅**:
  - QA-CF / QA-VQ / QA-SQ / QA-AS 실패 -> 영상 재조립(re-render) 시도
  - QA-MC 실패 -> manifest 재생성 시도
  - QA-EQ 실패 -> 비차단, 경고만 기록
  - QA-YC 실패 -> 대본/메타데이터 수정 필요
- **2회 실패 후**: 수동 리뷰로 에스컬레이션

---

## Remotion 관련 참고사항

- Remotion 렌더링은 일관된 출력 생성 (FFmpeg 필터 체인 가변성 없음)
- QA-SQ 항목은 Remotion CSS로 렌더된 자막 검증 (FFmpeg force_style 아님)
- QA-VQ 정적 프레임 감지는 여전히 적용 (이미지 소스 영상 시 정적 가능)

---

## 핵심 제약사항

1. **Python 실행**: `scripts/video-pipeline/.venv/Scripts/python.exe` 전체 경로 사용
2. **읽기 전용**: final.mp4 수정 금지 -- QA는 검사만 수행
3. **manifest 수정 금지**: scene-manifest.json 변경 금지
4. **DESIGN_BIBLE 항목**: 에이전트가 플래그, 사람이 최종 승인

---

## 참조

- `scripts/video-pipeline/qa_check.py` -- 34항목 자동 검사 엔진
- `DESIGN_BIBLE.md` -- 9항목 콘텐츠 품질 기준
- `DESIGN_SPEC.md` -- 디자인 사양 레퍼런스
