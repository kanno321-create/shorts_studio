---
name: feedback_typecast_ssml_literal_read
description: Typecast ssfm-v30 는 SSML 미지원 — `<break time="Xs"/>` 주입 시 literal 낭독 ("브레이크 타임 제로쩜삼오 에스"). _inject_punctuation_breaks 호출 금지.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/narration.mp3 (116.04s, 세션 #33 v1 실패작, SSML literal 오염)
  - scripts/orchestrator/api/typecast.py:106 (호출 지점)
  - scripts/orchestrator/api/typecast.py:189-213 (문제 함수)
failure_mapping:
  - FAIL-1-v1: 대본의 감정선/슬래시/괄호 그대로 낭독
  - FAIL-2-v1: 감정 없는 국어책 낭독 (자연 pause 파괴로 emotion 파라미터 무력화)
---

# feedback: Typecast SSML 리터럴 낭독 금지

## 규칙

**Typecast `ssfm-v30` 모델은 SSML 미지원.** Text 입력에 `<break time="0.35s"/>` 또는 `<emphasis>` 같은 SSML 태그를 삽입하면 TTS 엔진이 태그를 plain text 로 오인하여 literal 낭독한다. 대표님 귀로 "슬래시/괄호까지 다 읽는 국어책 낭독" 으로 들림.

### 위반 위치

- `scripts/orchestrator/api/typecast.py:106` — `prepared_text = self._inject_punctuation_breaks(req.text)` 호출
- `scripts/orchestrator/api/typecast.py:189-213` — 문제 함수 `_inject_punctuation_breaks` (regex 로 `([.!?])(\s+)` → `<break time="0.35s"/>` 삽입)

### 교정

1. L106 호출을 **제거** 또는 `prepared_text = req.text` 로 바이패스.
2. Pause 는 Typecast config `auto_punctuation_pause:true` 가 **네이티브로 담당** — 기능 손실 없음.
3. 문장 간 추가 pause 가 필요하면 `silence_after_ms` (script.json 의 per-sentence 필드) 를 segment 결합 단계에서 실제 silence 로 변환해 삽입 (audio-level pause, SSML 아님).

## Why (왜)

Typecast 는 Anthropic 계 Claude TTS 가 아니라 ssfm-v30 (self-supervised flow matching v30). SDK docs 에 SSML 지원 명시 없음. 내가 `_inject_punctuation_breaks` 를 harvest 에서 그대로 포팅하면서 기존 (harvested 시절) 모델이 SSML 을 지원했는지 검증하지 않은 것이 실수. 세션 #33 Ryan Waller v1 에서 대표님이 직접 "슬래시 괄호까지 낭독" 으로 감지.

## How to apply (언제 적용)

- **voice-producer / Typecast 어댑터 호출 전 항상 확인** — `prepared_text` 가 plain text 인지, SSML 태그가 섞였는지.
- `grep -n "break time\|<emphasis\|<prosody" outputs/typecast/**/*.txt` 로 생성 전 검증.
- **다른 TTS 로 전환 시 재검토** — ElevenLabs 나 Edge TTS 는 SSML 지원 가능성 있음. 전환 시 per-provider 명시적 플래그 (예: `enable_ssml=True`) 로 opt-in.
- 새 feature 로 "문장 간 pause 길이 동적 제어" 가 필요하면 SSML 이 아니라 `silence_after_ms` (script.json 필드) 를 concatenation 단계에서 실제 silent AudioSegment 삽입으로 처리.

## 검증

```bash
# 1. 호출 지점 비활성화 확인
grep -n "_inject_punctuation_breaks" scripts/orchestrator/api/typecast.py
# → L106 이 주석 처리 또는 제거되어야 함. L189-213 정의 자체는 남겨도 무방 (dead code).

# 2. 재생성 후 ear-verify (3-4초 샘플)
ffmpeg -i output/ryan-waller/narration.mp3 -t 5 -ss 10 -acodec copy /tmp/sample.mp3
# → 재생해서 SSML literal 낭독 없음을 확인.

# 3. 생성된 오디오에 "브레이크 타임" 발음 0건
# (자동 검증 어려움 — 대표님 직접 ear-verify 필수)
```

## Cross-reference

- `project_tts_stack_typecast` — TTS 스택 SSOT
- `reference_shorts_naberal_voice_setup` — Typecast voice 매트릭스
- 세션 #33 Ryan Waller v1 실패작 = `output/ryan-waller/final.mp4` (교훈 자료)
