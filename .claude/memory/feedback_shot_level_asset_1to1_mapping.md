---
name: feedback_shot_level_asset_1to1_mapping
description: 자료와 영상은 shot 단위 1:1 매핑. 한 clip 을 여러 shot 에 재사용 금지. 파일명에 shot_id 라벨로 소유 관계 명시.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
---

# feedback: shot ↔ asset 1:1 매핑 + 파일명에 shot_id 명시

## 대표님 v3.2 지적 (root cause)
- "8초쯤 사용된 영상이 너무 여러번 반복된다"
- "1분17초쯤 사용된 병원 복도가 자주반복된다"

## 규칙

1. **shot 당 고유 `<shot_id>_final.mp4`** — 같은 Kling anchor 나 real video 라도 shot 마다 **별도 trim/생성** 결과물 보존
2. **파일명에 shot_id 라벨** — `hook_s01_phoenix_night_yt_<slug>.mp4`, `reveal_s02_fleeing_kling_broll04.mp4` 식. 파일만 봐도 "어떤 shot 용" 즉각 파악
3. **한 raw asset (예: Full Interrogation 65분) → 여러 shot 에 사용 가능** 하지만 **각 shot 의 `<shot_id>_final.mp4` 는 독립 파일** (시각 / duration / trim 구간 별도)
4. **visual_spec clips 배열의 src 중복 0 검증** — coverage_report 단계 assertion

## Why
v3.2 는 6 Kling anchor 의 생성물을 9 section 에 중복 배치 → 같은 영상이 여러 번 등장. shot-level 독립 trim 결과물을 만들면 자연스럽게 1:1 유지.

## Cross-reference
- Rule 1 (script 읽기) + Rule 2 (markers 준수) + Rule 3 (vision) 과 함께 shot-level 아키텍처 완성
- `feedback_shot_level_context_sync.md` (전단계)
