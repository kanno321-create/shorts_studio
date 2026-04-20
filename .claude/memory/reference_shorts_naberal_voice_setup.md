---
name: reference_shorts_naberal_voice_setup
description: shorts_naberal 11 채널 Typecast/ElevenLabs voice 매트릭스 + 숨은 규약 6개 (ZWSP silence, auto_punctuation_pause, emotion_intensity 등)
type: reference
---

# shorts_naberal Voice 세트업 — 11 채널 매트릭스

**포팅 완료**: 세션 #26 2차 batch, `feedback_clean_slate_rebuild` §예외 경로 (declarative config 허용).

## 파일 위치

- `config/voice-presets.json` (611줄) — 11 채널 × Typecast + ElevenLabs voice 매트릭스
- `config/channels.yaml` (693줄) — 채널별 preset 매핑 (PROVENANCE header 포함)
- `config/PROVENANCE.md` — import 이력 + 비 이관 자산 13건 분류

## 숨은 규약 6개 (포팅 시 발견)

shorts_naberal 에서 암묵적으로 작동하던 TTS 튜닝 규약:

1. **ZWSP (Zero-Width Space) silence 삽입** — 긴 문장 중간 자연 호흡 삽입
2. **auto_punctuation_pause** — 마침표 0.4s / 쉼표 0.2s / 물음표 0.5s
3. **emotion_intensity 0.0~1.0** — 채널별 톤 튜닝 (예: incidents 0.6 / study 0.3)
4. **speed_range 0.9~1.1** — Shorts 포맷 템포 (59초 제약)
5. **pitch offset ±3 semitones** — voice 자연 변주
6. **emphasis_word markup** — `<emphasis level="strong">` SSML 하위호환

## 11 채널 스코프 (shorts_studio 적용 대상 4~5채널)

shorts_studio 는 **주 3~4편/주 페이스**라 11채널 전부는 과포화. Phase 10 진입 시 대표님이 우선순위 선별 (Go Criteria #2).

## 대표님 증언

- "Typecast 계속 사용해왔던거다" (세션 #26) — UAT #2-a `passed_by_attestation` 근거
- "api key는 shorts_naberal" — 원본 레지스트리 위치 확증

## 포팅 판정 (feedback_clean_slate_rebuild §예외)

- ✅ **재구현 비용**: voice_id 는 Typecast 외부 API 상수 — 새로 만들어도 동일 값
- ✅ **원본 불변성**: shorts_naberal/ 는 건드리지 않고 복사만
- ✅ **백지 설계 불가**: "어떤 로직" 이 아니라 "어떤 값" 의 문제

## Related

- [project_tts_stack_typecast](project_tts_stack_typecast.md) — 3-tier 스택 (포팅 후 결과)
- [feedback_clean_slate_rebuild](feedback_clean_slate_rebuild.md) — §예외 확장 근거
- D091-DEF-02 #8 — voice_discovery.py Typecast 확장 (backlog)
