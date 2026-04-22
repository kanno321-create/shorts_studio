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

## Reference (외부 리소스 위치)
- [reference_harvested_full_index](reference_harvested_full_index.md) — **🔴 옵션 A 즉시 도입 진입 자료**: `.preserved/harvested/` 9폴더 153파일 인덱스 + 다음 세션 5-Step 진입 순서 + Phase A1~A4 작업 로드맵 (2026-04-22 옵션 A 결정 후)
- [reference_production_gap_map](reference_production_gap_map.md) — **🔴 shorts_naberal production SSOT vs 우리 격차 매핑 + 11 누락 컴포넌트 + 복구 옵션 A/B/C** (2026-04-22 충격 사건 후 박제)
- [reference_api_keys_location](reference_api_keys_location.md) — `.env` 경로 + 각 key 용도 매핑 (API key 재질문 금지)
- [reference_shorts_naberal_voice_setup](reference_shorts_naberal_voice_setup.md) — 11 채널 Typecast voice 매트릭스 + 숨은 규약 6개
- [reference_signature_and_character_assets](reference_signature_and_character_assets.md) — **🔴 Phase 16 자산 SSOT**: 인트로 v4 시그니처 + 캐릭터 4종 PNG 실물 위치 + 아웃로 미해결 + episode 표준 구조 (2026-04-22 세션 #33 매핑)
