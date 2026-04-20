# MEMORY Index — shorts_studio

> 로컬 메모리 인덱스. `.claude/hooks/session_start.py` Step 6이 매 세션 전체 주입.
> 각 메모리는 `name` / `description` / `type` 필드 frontmatter 포함 (auto memory 규약).

## Project (기술 결정 + 파이프라인 상태)
- [project_video_stack_kling26](project_video_stack_kling26.md) — I2V 영상 스택: Kling 2.6 Pro primary + Veo 3.1 Fast fallback
- [project_claude_code_max_no_api_key](project_claude_code_max_no_api_key.md) — Claude Code Max 구독 활용, ANTHROPIC_API_KEY 영구 금지
- [project_shorts_production_pipeline](project_shorts_production_pipeline.md) — 4-stage 영상 제작 chain (Script → Image → Voice → Video)
- [project_tts_stack_typecast](project_tts_stack_typecast.md) — TTS 스택: Typecast primary + ElevenLabs fallback + EdgeTTS 최종 폴백

## Feedback (대표님 지시 + 검증된 접근)
- [feedback_i2v_prompt_principles](feedback_i2v_prompt_principles.md) — I2V 3원칙: Camera Lock / Anatomy Positive Persistence / Micro Verb
- [feedback_clean_slate_rebuild](feedback_clean_slate_rebuild.md) — shorts_naberal 원본 수정 금지, 신 구축 원칙 + 예외 (declarative config 포팅 허용)
- [feedback_session_evidence_first](feedback_session_evidence_first.md) — UAT 작성 전 output/ + SESSION_LOG + commit 전수 점검 의무

## Reference (외부 리소스 위치)
- [reference_api_keys_location](reference_api_keys_location.md) — `.env` 경로 + 각 key 용도 매핑 (API key 재질문 금지)
- [reference_shorts_naberal_voice_setup](reference_shorts_naberal_voice_setup.md) — 11 채널 Typecast voice 매트릭스 + 숨은 규약 6개
