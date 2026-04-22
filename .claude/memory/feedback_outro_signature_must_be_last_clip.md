---
name: feedback_outro_signature_must_be_last_clip
description: outro_signature.mp4 는 반드시 visual_spec clips 배열의 마지막 요소. 중간 배치 + 뒤에 추가 shot 배치 금지. 탐정 CTA + 왓슨 CTA 완결 후에만 outro.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
---

# feedback: outro_signature = 반드시 last clip

## 대표님 v3.2 지적
- "1분37초쯤 아웃트로에 나오는 건데 너무 일찍 나오고, 끝난 뒤는 검은 화면에서 조수의 CTA 가 나온다"

## 규칙

1. **visual_spec clips 배열의 `[-1]` 요소 src == `outro_signature.mp4`**
2. outro 앞 shot = aftermath (narrator CTA) + watson_cta (왓슨 CTA) 완결 후
3. 왓슨 CTA 구간에 outro 가 먼저 나오면 "검은 화면 + 왓슨 음성" 으로 체감 → 시청 완결성 파괴
4. build_visual_spec 단계 assertion: `assert clips[-1]['src'].endswith('outro_signature.mp4')`
5. aftermath_watson section 의 durationInFrames = 왓슨 CTA TTS duration (outro 전에 완결)

## 구조 순서

```
intro_signature → hook shots → body shots → reveal shots → aftermath_detective (탐정 CTA)
→ aftermath_watson (왓슨 CTA) → outro_signature
```

## Cross-reference
- `feedback_detective_exit_cta.md` (탐정 CTA pool)
- `feedback_watson_cta_pool.md` (왓슨 CTA pool)
- `feedback_duo_cta_both_required.md` (duo CTA)
- `reference_signature_and_character_assets.md` (outro 파일 위치)
