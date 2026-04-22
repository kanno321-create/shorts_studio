---
name: feedback_whisper_volume_normalize
description: Typecast emotion_preset="whisper" 는 볼륨을 급격히 낮춤 → 텐션 급락 체감. 사용 자제 또는 loudnorm 후처리 필수. 대안 = "tonedown" + 낮은 intensity.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
---

# feedback: whisper emotion 볼륨 급락 방지

## 대표님 v3.2 지적
- "1분 10초쯤 탐정의 나레이션의 텐션이 너무 급격하게 떨어져 목소리도 작아지고 그런데 이상하다"

## 규칙

1. Typecast `PresetPrompt(emotion_preset="whisper")` 는 **볼륨을 크게 낮춤** — 섹션 경계에서 갑작스러운 볼륨 drop 으로 "텐션 급락" 체감
2. whisper 사용 대신 **`tonedown` + `emotion_intensity=0.9`** 조합으로 대체 권장 (톤 낮추되 볼륨 유지)
3. 꼭 whisper 가 필요하면 **concat 후 ffmpeg loudnorm 필수**:
   ```bash
   ffmpeg -i narration.mp3 -af "loudnorm=I=-16:LRA=11:TP=-1.5" narration_normalized.mp3
   ```
4. 섹션 경계 전환도 loudnorm 으로 매끄럽게 됨

## 매핑 권장 (section emotion → TTS preset)

| section 의도 | 권장 preset | intensity | 비고 |
|-------------|-----------|-----------|------|
| hook (긴장) | tonedown | 0.9 | - |
| body (사실 전달) | tonedown | 0.9 | - |
| climax/reveal | ~~whisper~~ → tonedown | 0.8-0.9 | whisper 대신 |
| aftermath (슬픔) | sad | 1.0 | - |
| watson (의문) | angry (Guri ssfm-v21) | 1.0 | urgent 없음 |

## Cross-reference
- `feedback_typecast_ssml_literal_read.md` (SSML 금지)
- `project_tts_stack_typecast.md`
