---
name: reference_production_gap_map
description: shorts_naberal (production SSOT) vs 우리 파이프라인 격차 매핑. 2026-04-22 대표님 충격 사건 후 매핑. 다음 세션이 같은 실수 반복하지 않도록 박제.
type: reference
---

# Production Gap Map — shorts_naberal vs 우리

**Trigger 사건**: 2026-04-22 SESSION #31 final video (`outputs/ffmpeg_assembly/assembled_1776844680770.mp4`) 가 13초 720p 자막없음 자료없음 인트로없음 — 대표님 "이런 퀄리티로 어떻게 하노" 충격. 본질 누락 확인.

## Production SSOT 위치 (shorts_naberal/, 읽기 전용)

| 영역 | 경로 |
|---|---|
| **설계도** | `DESIGN_BIBLE.md`, `DESIGN_SPEC.md`, `NLM_PROMPT_GUIDE.md`, `VEO_PROMPT_GUIDE.md` |
| **채널바이블** | `.claude/channel_bibles/{incidents,humor,politics,trend,wildlife,documentary}.md` (v1.0 7개) |
| **Skills (관련)** | `.claude/skills/{shorts-pipeline,shorts-script,shorts-editor,shorts-rendering,shorts-research,shorts-qa,shorts-video-sourcer,shorts-designer,shorts-director,shorts-safety,shorts-upload,channel-incidents,channel-incidents-jp,create-shorts,create-video,naberal-coding-standards,naberal-identity,naberal-operations,nlm-claude-integration,remotion}/SKILL.md` |
| **Reference scripts** | `.claude/reference_scripts/{documentary,humor,incidents,politics,trend,wildlife}/` |
| **Remotion 합성** | `remotion/src/compositions/{ShortsVideo,LongformVideo,IntroCard,OutroCard,TitleCard,HighlightCard,BarChartCard,StatsCard,QuoteCard,ListCard,ComparisonCard}.tsx` + `components/{BracketCaption,crime/{ContextGraphicScene,ImpactCutScene,SpeakerSubtitle}}.tsx` + `lib/transitions/presentations/{glitch,rgbSplit,zoomBlur,lightLeak,clockWipe,pixelate,checkerboard,fade}.tsx` |
| **3-Pipeline scripts** | `scripts/{audio-pipeline,visual-pipeline,video-pipeline,thumbnail,research,curation,sourcing,multilingual,avatar,intelligence,batch,orchestrator,youtube,upload,audits,analytics}/` |
| **Output 레퍼런스** | `output/{zodiac-killer,roanoke-colony,nazca-lines,zodiac-killer-jp,roanoke-colony-jp,nazca-lines-jp}/final.mp4` (대표님 baseline 6편) |
| **자산 (캐릭터/시그니처/폰트/음원/효과음)** | `output/channel_art/`, `output/<topic>/sources/{character_detective.png,character_assistant.png,intro_signature.mp4,outro_signature.mp4,...}`, `assets/fonts/`, `music/library/`, `sfx/` |

## Production 파이프라인 (6-Stage)

```
RESEARCH (NLM #1 사건 발굴)
  → BLUEPRINT (planner → blueprint.json)
  → SCRIPT (NLM #2 대본 제조 → script-converter → script-polisher) ←★ 17 검사관 게이트
  → ASSETS (병렬 3-way: voice + video-sourcer + subtitle)
  → RENDER (Remotion ShortsVideo.tsx + TransitionSeries)
  → QA (42항목 체크리스트, FAIL 시 Stage 3/4 롤백 max 2회)
```

**핵심 원칙**: "**Narration Drives Timing**" — script 8.5자/초 → TTS → ffprobe 실측 → durationInFrames = sec × 30fps. 영상이 음성에 맞춤 (역전 금지).

## 우리 13 GATE vs Production 6-Stage 매핑

| 우리 GATE | Production Stage | 차이 |
|---|---|---|
| TREND + NICHE | (Stage 0 — 채널 선택은 사람) | 우리는 자동화 시도 |
| RESEARCH_NLM | Stage 1 RESEARCH (NLM #1) | 우리는 1-노트북, production 은 2-노트북 |
| BLUEPRINT | Stage 2 BLUEPRINT | OK |
| SCRIPT + POLISH | Stage 3 SCRIPT (NLM #2 + script-converter + script-polisher) | 우리는 NLM #2 누락 |
| VOICE | Stage 4 ASSETS (voice 부분) | 병렬화 안 됨 |
| ASSETS | Stage 4 ASSETS (video-sourcer + subtitle 부분) | **자막 트랙 자체 누락** |
| ASSEMBLY | Stage 5 RENDER (Remotion) | 우리는 ffmpeg concat — Remotion 호출 자체 누락 |
| THUMBNAIL | (Stage 5 의 일부) | OK |
| METADATA + UPLOAD | Stage 6 직후 publisher | OK |
| MONITOR + COMPLETE | (외부) | OK |

## 누락 컴포넌트 (우선순위순)

1. **🔴 Critical**: Remotion 합성 경로 (`ShortsVideo.tsx` + 11 Cards + 7 transitions). 콘텐츠 architecture 자체.
2. **🔴 Critical**: faster-whisper word-level 자막 (`audio-pipeline/word_subtitle.py`). 시청유지율 핵심.
3. **🔴 Critical**: 채널바이블 7개 v1.0 박제 (`incidents.md` 등). 콘텐츠 형식 SSOT.
4. **🔴 Critical**: 60~120초 영상 길이 (현재 13초). "Narration drives timing" 강제.
5. **🟡 High**: 인트로/아웃로 시그니처 (`generate_intro_signature.py` + IntroCard/OutroCard).
6. **🟡 High**: 캐릭터 오버레이 (TopBar 좌·우 캐릭터 PNG).
7. **🟡 High**: 자료 수집 우선순위 6단계 (실제영상 → 인물사진 → 커뮤니티 → AI생성 → 일러스트 → 스톡).
8. **🟡 High**: 일본 채널 변환 (일본 네이티브 자막 + 일본 TTS + JP 캐릭터).
9. **🟢 Medium**: feedback 메모리 12+ 박제 (`feedback_script_tone_seupnida`, `feedback_duo_natural_dialogue`, `feedback_subtitle_semantic_grouping`, `feedback_video_clip_priority`, `feedback_outro_signature`, `feedback_series_ending_tiers`, `feedback_detective_exit_cta`, `feedback_watson_cta_pool`, `feedback_dramatization_allowed`, `feedback_info_source_distinction`, `feedback_veo_supplementary_only`, `feedback_number_split_subtitle`).
10. **🟢 Medium**: 42항목 QA 체크리스트 (현재 17 inspector → 25 추가 필요).
11. **🟢 Medium**: Human-in-the-Loop 승인 게이트 3개.

## 콘텐츠 형식 (incidents.md v1.0 핵심)

- **타겟**: 30~50대 남성, 영화 《살인의 추억》《세븐》 톤
- **길이**: 단편 50~60초 / 시리즈 90~120초 / 상한 120초
- **목표**: 감정 1개 + 정보 1개 (둘 다 1개씩만)
- **톤**: 탐정 1인칭 독백 + **왓슨**(조수) 시청자 대리 질문. "습니다/입니다/였죠"만
- **4단계 구조**: Hook(0-5s, 탐정 현장 도착) → 갈등·오해(5-30s, 왓슨 첫 질문) → 핵심 3포인트(30-90s, 증거/프로파일링/현장 관찰) → 반전·정리(2-5s, 인간적 공허 + 다음편 예고)
- **자막**: 6~12자, 동사 종결, 의미단위 그룹핑. 숫자 쪼개짐 금지
- **영상**: 영상:이미지 ≥ 30%, 텍스트 스크린샷 자동 제거
- **CTA**: 구독 강요 금지. 시리즈 끝맺음 3단계. 탐정 퇴장 문구 풀 10개 + 왓슨 CTA 풀 10개
- **엔딩 시그니처**: 탐정 정면 → 뒤돌아 걸어감

## I2V 사용 정책 (incidents.md §9, 우리 정책 역전 필요)

**Production**: 이미지 기반 (Ken Burns) 우선 + I2V 보조용만 (`feedback_veo_supplementary_only`)
**우리 현재**: I2V primary
**필요 조정**: 자료 수집 6단계 우선순위 적용 — 실제영상(1) → 인물영상/사진(2) → 커뮤니티 캡처(3) → AI 생성(4, Kling I2V) → 일러스트(5) → 스톡(6, 최후)

## 다국어 (일본 채널)

- **영상 재사용**: 한국 영상 그대로 (대표님 명시)
- **템플릿 교체**: 하단 일본어 채널명/구독, 상단 일본 캐릭터 (남자 탐정 + 여자 조수)
- **TTS 교체**: 일본 전용 TTS (Typecast 아님)
- **자막**: 한국어 번역 X → **일본 네이티브로 새로 작성** (`scripts/audio-pipeline/ja_subtitle.py`)

## 다음 세션 시작 시 체크리스트

1. ✅ 이 메모리 + `feedback_no_mockup_no_empty_files` 자동 로드 확인
2. ⏳ 대표님이 복구 옵션 A/B/C 중 어느 길 선택했는지 확인 (`WORK_HANDOFF.md` 또는 직접 질의)
3. ⏳ 옵션 결정되면 해당 stage 부터 진행 (절대 spec 게이트만 통과로 "완료" 보고 금지)
4. ⏳ Production baseline 6편 (`shorts_naberal/output/{zodiac-killer,...}/final.mp4`) 정량/정성 비교를 매 산출물에 강제

## 절대 금지 (이 세션 학습)

- ❌ "spec 통과" = "production 완료" 라고 보고하지 않는다
- ❌ 13초 영상을 "60초 baseline" 과 비교 없이 "OK" 처리하지 않는다
- ❌ 자막·인트로·아웃로·캐릭터 오버레이 누락된 영상을 production 으로 인정하지 않는다
- ❌ shorts_naberal 원본 수정 (CLAUDE.md 금기 #6 mirror) — 읽기만, 박제는 우리 `.claude/memory/` 또는 `.preserved/harvested/`
