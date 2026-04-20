---
name: project_tts_stack_typecast
description: Stage 3 TTS 스택 — Typecast primary (주 채널), ElevenLabs v3 fallback, EdgeTTS 최종 폴백, Fish Audio dead code
type: project
---

# TTS 스택 (Stage 3)

**확정**: 세션 #26 2차 batch (2026-04-20), 대표님 증언 "Typecast 계속 사용해왔던거다" + shorts_naberal settings port.

## 3-Tier 구조

| Tier | 모델 | 용도 | 비용 |
|------|------|------|------|
| **Primary** | Typecast | 한국 채널 전부 (주 채널) | API 과금 |
| **Fallback** | ElevenLabs v3 | 영어 채널 primary / 한국 채널 fallback | $0.12/1K chars |
| **Final** | EdgeTTS | 완전 무료 최종 폴백 (품질 희생) | $0 |

## 제거 사항

- **Fish Audio** — dead code 확증 (shorts_naberal 에서 모든 `reference_id = PENDING_VOICE_SELECTION` 으로 Tier 1 실제 미작동). shorts_studio 는 3-tier 로 단순화 (D091-DEF-02 #9).
- **VOICEVOX** (로컬 서버) — incidents-jp 채널 전용, shorts_studio scope 외

## 구현 파일

- `scripts/io/voice_discovery.py` — speaker_name → voice_id 자동 resolve (Typecast 확장 pending: D091-DEF-02 #8)
- `config/voice-presets.json` (611줄) — 11 채널 × Typecast + ElevenLabs voice matrix
- `config/channels.yaml` (693줄) — 채널별 voice preset 매핑

## UAT 상태

- **UAT #2-a** (Typecast primary) — `passed_by_attestation` (세션 #26, 대표님 증언)
- **UAT #2-b** (ElevenLabs 한국어 fallback) — `deferred_phase_10` (primary 안정 시 실 호출 희귀, D091-DEF-02 #8)

## Related

- [reference_shorts_naberal_voice_setup](reference_shorts_naberal_voice_setup.md) — 11 채널 매트릭스 + 숨은 규약
- [reference_api_keys_location](reference_api_keys_location.md) — TYPECAST_API_KEY, ELEVENLABS_API_KEY 위치
