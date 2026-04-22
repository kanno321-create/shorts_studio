# MEMORY Index — shorts_studio

> 로컬 메모리 인덱스. `.claude/hooks/session_start.py` Step 6이 매 세션 전체 주입.
> 각 메모리는 `name` / `description` / `type` 필드 frontmatter 포함 (auto memory 규약).

## Project (기술 결정 + 파이프라인 상태)
- [project_image_stack_gpt_image2](project_image_stack_gpt_image2.md) — 정지 이미지 anchor·썸네일 = gpt-image-2 primary, Nano Banana 폴백 (2026-04-22 실측 판정)
- [project_video_stack_kling26](project_video_stack_kling26.md) — I2V 영상 스택: Kling 2.6 Pro primary + Veo 3.1 Fast fallback
- [project_claude_code_max_no_api_key](project_claude_code_max_no_api_key.md) — Claude Code Max 구독 활용, ANTHROPIC_API_KEY 영구 금지
- [project_shorts_production_pipeline](project_shorts_production_pipeline.md) — 4-stage 영상 제작 chain (Script → Image → Voice → Video)
- [project_tts_stack_typecast](project_tts_stack_typecast.md) — TTS 스택: Typecast primary + ElevenLabs fallback + EdgeTTS 최종 폴백
- [project_server_infrastructure_plan](project_server_infrastructure_plan.md) — 현재 Windows PC (임시), 향후 Mac Mini 이관. cron 은 launchd/crontab 전환
- [project_video_sourcing_skill_v1](project_video_sourcing_skill_v1.md) — **🆕 멀티소스 영상 수급 스킬 prototype**: YouTube Data API + Wikimedia Commons + ranking + yt-dlp. scripts/orchestrator/video_sourcing/ 6 파일 모듈. (세션 #34 신설)
- [project_script_driven_agent_pipeline_v1](project_script_driven_agent_pipeline_v1.md) — **🔴 Script-Driven 3-Agent Pipeline v1 SSOT**: Agent 0 shot breakdown → Agent 1 asset sourcer (subagent vision) → Agent 2 video producer (subagent verify) → Agent 3 TTS → Agent Subtitle → Agent Spec → Agent 5 render → Agent 4 Inspector (subagent vision). INVARIANT 3-rule 적용. 향후 모든 영상 템플릿. (세션 #34 확립)

## Feedback (대표님 지시 + 검증된 접근)
- [feedback_no_mockup_no_empty_files](feedback_no_mockup_no_empty_files.md) — **절대 금지**: 목업/스텁/placeholder/빈 파일 생성. 모든 산출물 production-ready 실 콘텐츠 (2026-04-22 절대 규칙)
- [feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md) — I2V 3원칙: Camera Lock / Anatomy Positive Persistence / Micro Verb (+ VEO_PROMPT_GUIDE 활용 규칙)
- [feedback_clean_slate_rebuild](feedback_clean_slate_rebuild.md) — shorts_naberal 원본 수정 금지, 신 구축 원칙 + 예외 (declarative config 포팅 허용)
- [feedback_session_evidence_first](feedback_session_evidence_first.md) — UAT 작성 전 output/ + SESSION_LOG + commit 전수 점검 의무
- [feedback_notebooklm_paste_only](feedback_notebooklm_paste_only.md) — **🔴 NLM 입력 paste 전용** (typing 시 중간 enter 가 submit trigger, 쿼리 잘림). 추가질문도 동일. 2026-04-22 세션 #33 대표님 직접 피드백.
- [feedback_typecast_ssml_literal_read](feedback_typecast_ssml_literal_read.md) — **🔴 Typecast ssfm-v30 SSML 미지원**. `<break time="Xs"/>` 주입 시 literal 낭독. `_inject_punctuation_breaks` 호출 금지. (세션 #33 FAIL-1/2 박제)
- [feedback_harvest_missing_korean_welsh_corgi](feedback_harvest_missing_korean_welsh_corgi.md) — **🔴 incidents 조수 = 한국판 웰시 코기** (shorts_naberal/output/zodiac-killer/sources/). `_jp_` suffix 는 일본판, 사용 금지. (세션 #33 FAIL-3 박제)
- [feedback_kling_i2v_required_not_ken_burns](feedback_kling_i2v_required_not_ken_burns.md) — **🔴 b-roll motion = Kling 2.6 Pro I2V 필수**. Ken Burns 단독 금지. 금기 #11 은 Veo 금지이지 I2V 전체 금지 아님. (세션 #33 FAIL-4 박제)
- [feedback_duo_cta_both_required](feedback_duo_cta_both_required.md) — **🔴 aftermath = 탐정 CTA + 왓슨 CTA 양쪽 필수**. Hook duo 대칭. 한쪽만 = 구조 미완성. (세션 #33 FAIL-5 박제)
- [feedback_narration_text_only_no_meta](feedback_narration_text_only_no_meta.md) — **🔴 script.json text 필드 = 발화 텍스트만**. 감정/비주얼/citation/SSML 혼입 금지, 별도 필드에 분리. (세션 #33 FAIL-1 보조 박제)
- [feedback_script_section_paragraph_not_sentences](feedback_script_section_paragraph_not_sentences.md) — **🔴 script.json = sections[] flat array + narration 문단** (reference 모방). sentences[] 분해 금지 — TTS 조각 호출로 로봇 낭독 유발. (세션 #34 v2→v3 박제)
- [feedback_hook_context_30s_rule](feedback_hook_context_30s_rule.md) — **🔴 hook 에 날짜·장소·인원·숫자 구체 fact ≥3개 필수**. 30초 안에 사건 파악 불가하면 이탈. (세션 #34 v2 FAIL — "뭘 말하려나 모르겠다")
- [feedback_subtitle_short_chunks_2_4_words](feedback_subtitle_short_chunks_2_4_words.md) — **🔴 자막 cue = 2-4 단어 / ≤12자**. sentence-level (20-30자) 는 68pt 폰트 × 1080 폭에서 2-line wrap. (세션 #34 v2 FAIL — "자막 2줄로 내려와 못 읽겠다")
- [feedback_kling_duration_10s_not_5s](feedback_kling_duration_10s_not_5s.md) — **🔴 Kling I2V 기본 10s** (fal.ai 는 {5,10} 만, 우리 validator le=8 충돌 시 experiment 스크립트에서 직접 호출). v2 5s 는 scene 평균 10s 대비 freeze. (세션 #34 v2 FAIL)
- [feedback_multi_source_video_search_required](feedback_multi_source_video_search_required.md) — **🔴 영상 수급 = YouTube + Wikimedia ≥2 source**. 단일 source 금지. (세션 #34 대표님 직접 지시)
- [feedback_script_video_sync_via_visual_directing](feedback_script_video_sync_via_visual_directing.md) — **🔴 script.json 모든 section 에 visual_directing 필드 필수**. 영상 매핑 SSOT — 없으면 대본-영상 따로 놈. (세션 #34 v2 FAIL — "대본이랑 영상이랑 따로놀잖아")

## 🔴 INVARIANT 3-Rule (영구 — 모든 영상 작업 필수 준수, 세션 #34)

- [feedback_every_agent_reads_script_first](feedback_every_agent_reads_script_first.md) — **🔴 Rule 1 — 모든 에이전트는 대본을 반드시 보면서 작업한다**. 향후 모든 영상/채널/에이전트 (Producer 15 + Inspector 17 + 조율자) 필수. (대표님 2026-04-23 "이번 뿐만이아니라 앞으로 하는 모든 영상작업에 필수다")
- [feedback_script_markers_absolute_compliance](feedback_script_markers_absolute_compliance.md) — **🔴 Rule 2 — 대본 표현 (emotion/situation/motion) 그대로 반영, 대본 밖 요소 추가 금지**. script schema 에 markers 배열 필수. (대표님 2026-04-23 "절대원칙이 대본에적힌 감정표현, 상황표현, 움직임에관한표현등을 보고 제작하고, 절대 벗어나는 작업은 하지 않는다")
- [feedback_agents_require_visual_analysis](feedback_agents_require_visual_analysis.md) — **🔴 Rule 3 — 크롤링/제작/검사 에이전트는 Claude Opus 4.7 subagent 를 Agent tool 로 spawn 해 key frame Read 시각 판정**. 외부 vision API 금지, 메인 세션 직접 Read 금지. (대표님 2026-04-23 "claude code 4.7opus가 성능최고다" + "에이전트선에서 가능한지 알아보고 가능하면 에이전트선에서 하라고해라 너가하면곤란해")

## v4 보조 원칙 (세션 #34)

- [feedback_shot_level_asset_1to1_mapping](feedback_shot_level_asset_1to1_mapping.md) — shot ↔ asset 1:1, clip 재사용 금지. (v3.2 지적 #1·#3)
- [feedback_outro_signature_must_be_last_clip](feedback_outro_signature_must_be_last_clip.md) — outro 는 반드시 visual_spec clips 의 last. (v3.2 지적 #6)
- [feedback_whisper_volume_normalize](feedback_whisper_volume_normalize.md) — Typecast whisper preset 볼륨 급락 → tonedown 대체 + loudnorm. (v3.2 지적 #7)
- [feedback_shot_filename_label_explicit](feedback_shot_filename_label_explicit.md) — 다운로드·생성 파일명에 shot_id 라벨 명시. (대표님 v4 "어떤씬에 쓰일건지 정확하게 파일이름에")
- [feedback_assistant_never_appears_visually](feedback_assistant_never_appears_visually.md) — **🔴 조수(왓슨) 영상 등장 금지**. 상단 overlay 로만 존재, scene clip 배치 금지. 직전 narrative clip 연장. (세션 #34 v3 FAIL)
- [feedback_shot_level_context_sync](feedback_shot_level_context_sync.md) — **🔴 대본 문장별 shot 매핑** — section-level 단일 clip 금지. 10s+ section 은 2-4 shots 로 분할. (세션 #34 v3 "담배 발화면 담배 영상")
- [feedback_subtitle_meaning_chunks_not_mechanical](feedback_subtitle_meaning_chunks_not_mechanical.md) — **🔴 자막 = 의미 덩어리** (수식어+명사, 서술어+목적어, 고유명사 유지). 공백 기반 2-4 단어 mechanic split 금지. (세션 #34 v3 "두 단어 같이 보여야 이해")
- [feedback_video_sourcing_specific_keywords](feedback_video_sourcing_specific_keywords.md) — **🔴 영상 수급 query 는 고유명사 (Dateline / Waller / Carver / mugshot)** — 일반 "police interrogation night" 같은 generic query 는 Noir stock 만. (세션 #34 v3 "이상한것만 붙여놨다")
- [feedback_hook_visual_brief_not_extended](feedback_hook_visual_brief_not_extended.md) — **🔴 hook 의 한 visual ≤ 3s**. 10초 내내 같은 장면 (크리스마스 집) 금지, 다중 shot 필수. (세션 #34 v3 "하루종일 틀고있노")

## Reference (외부 리소스 위치)
- [reference_harvested_full_index](reference_harvested_full_index.md) — **🔴 옵션 A 즉시 도입 진입 자료**: `.preserved/harvested/` 9폴더 153파일 인덱스 + 다음 세션 5-Step 진입 순서 + Phase A1~A4 작업 로드맵 (2026-04-22 옵션 A 결정 후)
- [reference_production_gap_map](reference_production_gap_map.md) — **🔴 shorts_naberal production SSOT vs 우리 격차 매핑 + 11 누락 컴포넌트 + 복구 옵션 A/B/C** (2026-04-22 충격 사건 후 박제)
- [reference_api_keys_location](reference_api_keys_location.md) — `.env` 경로 + 각 key 용도 매핑 (API key 재질문 금지)
- [reference_shorts_naberal_voice_setup](reference_shorts_naberal_voice_setup.md) — 11 채널 Typecast voice 매트릭스 + 숨은 규약 6개
- [reference_signature_and_character_assets](reference_signature_and_character_assets.md) — **🔴 Phase 16 자산 SSOT**: 인트로 v4 시그니처 + 캐릭터 4종 PNG 실물 위치 + 아웃로 미해결 + episode 표준 구조 (2026-04-22 세션 #33 매핑)


## Phase 16-01 Imprinted (2026-04-22)

### Channel Bibles (6)
- [incidents v1.0 (production_active)](project_channel_bible_incidents_v1.md) — 사건기록부 v1.0 SSOT 박제. Phase 16 production-active 채널 (렌더링 통합). 10 규칙 섹션 + FAIL-SCR 매핑 6건 + 12 feedback 참조 + Hook signature 9.0s 하드 고정.
- [wildlife (reference_only)](project_channel_bible_wildlife_ref.md) — 야생 WildCamera 채널 reference-only (Phase 18+). Attenborough BBC 스타일.
- [humor (reference_only)](project_channel_bible_humor_ref.md) — 유머 박창수 채널 reference-only (Phase 18+). 충청도 사투리 썰.
- [politics (reference_only)](project_channel_bible_politics_ref.md) — 한입정치 필재 채널 reference-only (Phase 18+). 풍자·비꼼 우파.
- [trend (reference_only)](project_channel_bible_trend_ref.md) — 트렌드 카밀라 채널 reference-only (Phase 18+). MZ 카톡 톤.
- [documentary (reference_only)](project_channel_bible_documentary_ref.md) — HistoryMoment 채널 reference-only (Phase 18+). Ken Burns 4-Act.

### Script / Dialogue feedbacks (4)
- [feedback_script_tone_seupnida](feedback_script_tone_seupnida.md) — 종결어미 습니다/입니다/였죠 만 (FAIL-SCR-016 방어).
- [feedback_duo_natural_dialogue](feedback_duo_natural_dialogue.md) — 왓슨 키워드 >=60% 탐정 답변 첫 문장 포함 (FAIL-SCR-004 방어).
- [feedback_dramatization_allowed](feedback_dramatization_allowed.md) — 핵심 사실 엄격, 장면 디테일 각색 허용.
- [feedback_info_source_distinction](feedback_info_source_distinction.md) — 라고 합니다 전달형 vs 직관 구분.

### Subtitle feedbacks (2)
- [feedback_subtitle_semantic_grouping](feedback_subtitle_semantic_grouping.md) — 자막 6~12자, 동사 종결.
- [feedback_number_split_subtitle](feedback_number_split_subtitle.md) — 1,701통 숫자+단위 한 단어 유지.

### Visual feedbacks (2)
- [feedback_video_clip_priority](feedback_video_clip_priority.md) — 영상:이미지 >= 30%.
- [feedback_veo_supplementary_only](feedback_veo_supplementary_only.md) — I2V 보조용, 실제 이미지 최우선 (금기 #11 보강).

### Outro / CTA feedbacks (4)
- [feedback_outro_signature](feedback_outro_signature.md) — 탐정 정면 -> 뒤돌아 걸어감 패턴.
- [feedback_series_ending_tiers](feedback_series_ending_tiers.md) — 시리즈 Part 1/2/3 CTA 차등.
- [feedback_detective_exit_cta](feedback_detective_exit_cta.md) — 탐정 퇴장 10 pool, 뵙겠습니다 금지.
- [feedback_watson_cta_pool](feedback_watson_cta_pool.md) — 왓슨 CTA 10 pool.
