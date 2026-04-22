---
name: feedback_shot_filename_label_explicit
description: 다운로드·생성 영상 파일명에 shot_id 를 명시적으로 포함. "어떤 씬에 쓰이는지" 를 파일시스템 레벨에서 추적 가능하게 해야 대본-영상 동기화 추적 가능.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
---

# feedback: shot_id 라벨 파일명 규칙

## 대표님 v4 지시 원문
> "어떤씬에 쓰일건지 정확하게 적어놓고 파일이름같은곳에다가"

## 규칙

1. Asset Sourcer (Agent 1) 다운로드 결과: `<shot_id>_c<rank>_<source>_<short_title_slug>.{mp4|jpg|png}`
2. Video Producer (Agent 2) 출력: `<shot_id>_final.mp4` (shot 당 1개, unique)
3. Key frame 추출: `<shot_id>_c<rank>.jpg` (Agent 1) / `<shot_id>_final.jpg` (Agent 2) / `<shot_id>_mid.jpg` (Agent 4)
4. Manifest JSON 에 `shot_id` 필드 필수 — 파일-대본 cross-reference

## 예시 (Ryan Waller v4)
```
output/<ep>/sources/real_v4/
├── hook_s01_c1_youtube_kOyB7.mp4
├── hook_s01_c2_wikimedia_Phoenix_night.jpg
├── hook_s01_c3_youtube_uVm2A.mp4
└── _keyframes/
    ├── hook_s01_c1.jpg
    ├── hook_s01_c2.jpg
    └── hook_s01_c3.jpg

output/<ep>/sources/shot_final/
├── hook_s01_final.mp4
├── hook_s02_final.mp4
└── ...

output/<ep>/sources/real_v4/manifest_v4.json
{
  "shots": {
    "hook_s01": {
      "selected": "c1",
      "candidates": [
        {"c": 1, "source": "youtube", "local": "hook_s01_c1_youtube_kOyB7.mp4", "claude_analysis": "...",},
        ...
      ]
    }
  }
}
```

## Cross-reference
- `feedback_shot_level_asset_1to1_mapping.md` (1:1 매핑 원칙)
- `feedback_video_sourcing_specific_keywords.md` (search keyword)
