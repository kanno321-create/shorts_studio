---
name: reference_harvested_full_index
description: .preserved/harvested/ 전체 인덱스 + 다음 세션 진입 가이드. 옵션 A 즉시 도입 결정 후 2026-04-22 추가 harvest 완료. 9개 폴더 (기존 4 + 신규 5) read-only.
type: reference
---

# Harvested 전수 인덱스 (옵션 A 즉시 도입 진입 자료)

**Trigger**: 2026-04-22 대표님 옵션 A 결정 — Remotion + word_subtitle + intro_signature + 채널바이블 등 production 핵심을 `.preserved/harvested/` 로 read-only 복사 후 ASSEMBLY 재배선 진입.

**Read-only 잠금**: `attrib +R /S /D` (Windows) + `chmod -R a-w` (POSIX) 양쪽 적용. CLAUDE.md 금기 #6 mirror — shorts_naberal 원본 절대 수정 금지, .preserved/ 는 read-only.

## 폴더 인덱스 (9개)

### 기존 (Phase 3 harvest, 변경 없음)

| 폴더 | 파일 수 | 핵심 자산 |
|---|---|---|
| `theme_bible_raw/` | 7 | documentary/humor/incidents/politics/trend/wildlife.md + README. **incidents.md = 사건기록부 v1.0 SSOT** |
| `remotion_src_raw/` | 40 | Root.tsx + index.ts + compositions/11 + components/{crime,longform,BracketCaption,CTAOverlay} + lib/{fonts,props-schema,transitions/,test data} |
| `api_wrappers_raw/` | 5 | _kling_i2v_batch.py, elevenlabs_alignment.py, heygen_client.py, runway_client.py, tts_generate.py |
| `hc_checks_raw/` | (legacy) | Health check 패턴 |

### 신규 (2026-04-22 옵션 A 추가)

| 폴더 | 파일 수 | 핵심 자산 |
|---|---|---|
| `audio_pipeline_raw/` | 10 | **word_subtitle.py**(시청유지율 핵심 — faster-whisper word-level), ja_subtitle.py(일본 자막), subtitle_generate.py, longform_subtitle.py, multi_speaker_tts.py, dialogue_generate.py, en_caption_translate.py, pronunciation.py, tts_generate.py, elevenlabs_alignment.py |
| `video_pipeline_raw/` | 12 | **generate_intro_signature.py**(인트로 시그니처), remotion_render.py(Remotion CLI 호출), _build_render_props_v2.py(props 빌더), auto_highlight.py, qa_check.py, scene_evaluator.py, sentence_splitter.py, smart_crop_916.py, face_mosaic.py, shorts_extractor.py, design_engine.py, ai_visual_generate.py |
| `visual_pipeline_raw/` | 8 | i2v_generate.py, t2i_generate.py, clip_timing.py, prompt_builder.py, reference_image.py, shot_planner.py, pipeline_runner.py, __init__.py |
| `design_docs_raw/` | 4 | **DESIGN_BIBLE.md**(영상 제작 절대 기준), **DESIGN_SPEC.md**(레이아웃 픽셀 사양), **NLM_PROMPT_GUIDE.md**(NLM 프롬프트 작성), VEO_PROMPT_GUIDE.md(Veo 프롬프트 — Veo 자체 안 쓰지만 Kling 응용용) |
| `skills_raw/` | 20 SKILL.md | shorts-{pipeline,script,editor,rendering,research,qa,video-sourcer,designer,director,safety,upload}, channel-{incidents,incidents-jp}, create-{shorts,video}, naberal-{coding-standards,identity,operations}, nlm-claude-integration, remotion |
| `baseline_specs_raw/` | 54 | 6편 (zodiac-killer, roanoke-colony, nazca-lines + 각 -jp) × {visual_spec.json, subtitles_remotion.{ass,json,srt}, blueprint.json, scene-manifest.json, script.json, metadata.json, source.md, _upload_script.json, section_timing.json, sources_metadata.json}. **mp4 본 영상 제외** (대용량) — 대표님 직접 `shorts_naberal/output/<topic>/final.mp4` 참조 |

## 다음 세션 진입 순서 (필수 읽기)

### Step 1 — 콘텐츠 형식 SSOT 흡수 (1순위)
1. `.preserved/harvested/theme_bible_raw/incidents.md` (사건기록부 v1.0 — 4단계 구조, 종결어미, CTA, 시그니처)
2. `.preserved/harvested/skills_raw/channel-incidents/SKILL.md`
3. `.preserved/harvested/skills_raw/channel-incidents-jp/SKILL.md` (일본 채널)
4. `.preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json` (Remotion props 실제 예)
5. `.preserved/harvested/baseline_specs_raw/zodiac-killer/subtitles_remotion.ass` (자막 형식 예)

### Step 2 — Pipeline architecture 흡수 (2순위)
6. `.preserved/harvested/skills_raw/shorts-pipeline/SKILL.md` (6-Stage 전체)
7. `.preserved/harvested/design_docs_raw/DESIGN_BIBLE.md` (절대 기준)
8. `.preserved/harvested/design_docs_raw/DESIGN_SPEC.md` (픽셀 사양)
9. `.preserved/harvested/design_docs_raw/NLM_PROMPT_GUIDE.md` (NLM 프롬프트)

### Step 3 — Render 구현 흡수 (3순위)
10. `.preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx` (메인 합성)
11. `.preserved/harvested/remotion_src_raw/compositions/{IntroCard,OutroCard,TitleCard,HighlightCard}.tsx`
12. `.preserved/harvested/remotion_src_raw/lib/props-schema.ts` (props zod schema)
13. `.preserved/harvested/video_pipeline_raw/remotion_render.py` (Remotion CLI 호출)
14. `.preserved/harvested/video_pipeline_raw/_build_render_props_v2.py` (props 빌드)
15. `.preserved/harvested/video_pipeline_raw/generate_intro_signature.py` (인트로 시그니처)

### Step 4 — Subtitle/TTS 통합 흡수 (4순위)
16. `.preserved/harvested/audio_pipeline_raw/word_subtitle.py` (faster-whisper word-level)
17. `.preserved/harvested/audio_pipeline_raw/subtitle_generate.py`
18. `.preserved/harvested/audio_pipeline_raw/ja_subtitle.py` (일본 네이티브)
19. `.preserved/harvested/audio_pipeline_raw/tts_generate.py`

### Step 5 — Visual asset 통합 흡수 (5순위)
20. `.preserved/harvested/visual_pipeline_raw/{i2v_generate,prompt_builder,reference_image,shot_planner}.py`
21. `.preserved/harvested/api_wrappers_raw/_kling_i2v_batch.py`

## 다음 세션 작업 로드맵

### Phase A1: 콘텐츠 형식 박제 (1~2 세션)
- 채널바이블 7개 → `.claude/memory/project_channel_bibles_v1.md` 박제
- production feedback 메모리 12+ → 우리 `.claude/memory/feedback_*.md` 매핑/포팅
- 4단계 구조 + 왓슨 CTA + 시그니처 등 콘텐츠 형식 박제

### Phase A2: ASSEMBLY 재배선 (2~3 세션)
- `scripts/orchestrator/api/remotion_renderer.py` 신규 작성 — `video_pipeline_raw/remotion_render.py` 패턴 미러
- `scripts/orchestrator/shorts_pipeline.py` 의 ASSEMBLY 단계 분기 추가: shotstack → ffmpeg(legacy) → **remotion(primary)**
- props builder: `_build_render_props_v2.py` 패턴으로 우리 timeline → Remotion props 변환

### Phase A3: Subtitle/Intro/Outro 통합 (1~2 세션)
- `scripts/orchestrator/api/word_subtitle.py` 신규 — faster-whisper 도입
- `scripts/orchestrator/api/intro_outro_signature.py` 신규
- `audio-pipeline` 의 ja_subtitle.py 참조해 일본 채널 분기 준비

### Phase A4: visual_spec.json 생성 + sources/ 디렉토리 구조 (1~2 세션)
- asset-sourcer 가 visual_spec.json 산출하도록 스키마 확장
- sources/ 디렉토리에 anchor 이미지·자료 사진·캐릭터·intro/outro 통합 배치

## 절대 준수 (이 메모리 + reference_production_gap_map + feedback_no_mockup_no_empty_files 결합)

- ❌ 13초 영상을 production 으로 인정 금지 (목표 60~120초)
- ❌ 자막 없는 영상을 production 으로 인정 금지
- ❌ 인트로/아웃로 없는 영상을 production 으로 인정 금지
- ❌ 캐릭터 오버레이 없는 영상을 production 으로 인정 금지
- ❌ 스펙 게이트 통과 = production 완료 라고 보고 금지 (대표님 충격 사건 재발 방지)
- ❌ 빈 출력 / 목업 / placeholder 산출물 금지 (CLAUDE.md 금기 #10)
- ❌ Veo 호출 금지 — Kling 단독 + VEO_PROMPT_GUIDE 는 Kling 응용용 참조만
- ❌ shorts_naberal 원본 수정 금지 (CLAUDE.md 금기 #6) — `.preserved/harvested/` 는 read-only

## Cross-reference

- `feedback_no_mockup_no_empty_files` — 절대 금지 (목업/빈파일)
- `reference_production_gap_map` — 11 누락 컴포넌트 + 우리 13 GATE vs production 6-Stage 매핑
- `project_image_stack_gpt_image2` — 정지 이미지 = gpt-image-2 primary (옵션 A 진입 후에도 유효)
- `project_video_stack_kling26` — I2V = Kling 2.6 Pro single (Veo 금지)
- `feedback_i2v_prompt_principles` — I2V 3원칙 + VEO_PROMPT_GUIDE → Kling 응용 규칙
- CLAUDE.md 🔴 금기사항 #6 (shorts_naberal 수정 금지) + #10 (목업 금지) + #11 (Veo 금지)
