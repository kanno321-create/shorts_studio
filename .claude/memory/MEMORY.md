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

## Feedback (대표님 지시 + 검증된 접근)
- [feedback_no_mockup_no_empty_files](feedback_no_mockup_no_empty_files.md) — **절대 금지**: 목업/스텁/placeholder/빈 파일 생성. 모든 산출물 production-ready 실 콘텐츠 (2026-04-22 절대 규칙)
- [feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md) — I2V 3원칙: Camera Lock / Anatomy Positive Persistence / Micro Verb (+ VEO_PROMPT_GUIDE 활용 규칙)
- [feedback_clean_slate_rebuild](feedback_clean_slate_rebuild.md) — shorts_naberal 원본 수정 금지, 신 구축 원칙 + 예외 (declarative config 포팅 허용)
- [feedback_session_evidence_first](feedback_session_evidence_first.md) — UAT 작성 전 output/ + SESSION_LOG + commit 전수 점검 의무
- [feedback_notebooklm_paste_only](feedback_notebooklm_paste_only.md) — **🔴 NLM 입력 paste 전용** (typing 시 중간 enter 가 submit trigger, 쿼리 잘림). 추가질문도 동일. 2026-04-22 세션 #33 대표님 직접 피드백.

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
