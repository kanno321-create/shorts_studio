---
category: continuity_bible
status: ready
tags: [continuity, channel-identity, korean-seniors, color-palette, camera-lens, shorts]
updated: 2026-04-19
source_notebook: naberal-shorts-channel-bible
---

# Channel Identity — Continuity Bible (D-10 Canonical)

> 채널 정체성 고정값 (Single Source of Truth). Plan 06 에서 `prefix.json` 으로 pydantic 직렬화되고, Shotstack adapter 의 filter chain 최전단에 자동 주입됨 (D-9, D-19).

## 5 구성요소 (D-10 canonical)

### (a) 색상 팔레트

- **Navy** `#1A2E4A` — 메인 배경톤 (한국 시니어 skew 채도 낮음)
- **Gold** `#C8A660` — 액센트 / 하이라이트 (탐정 페르소나 단서 강조)
- **Light Gray** `#E4E4E4` — 서브텍스트 / 자막 베이스
- **Warmth scalar** `+0.2` — D-16 senior preference (warm skew, 채도 -10%)
- **HexColor type (Pydantic)** — `list[HexColor]` 형식으로 `ContinuityPrefix.color_palette` 에 직렬화.

### (b) 카메라 렌즈

- **초점거리** `35mm` — pydantic field `ContinuityPrefix.focal_length_mm: int` (D-20)
- **Aperture** `f/2.8` — pydantic field `ContinuityPrefix.aperture_f: float` (D-20)
- **렌즈 특성** — 중간 광각, 자연스러운 원근, 얼굴 왜곡 최소화. 탐정/조수 듀오 쇼츠 2-shot 에 적합.
- **Depth of field** — f/2.8 → 배경 완만한 blur, 피사체 분리 자연스러움. 한국 시니어 읽기 가독성 보호.

### (c) 시각적 스타일

- **LOCKED: `cinematic`** — pydantic field `ContinuityPrefix.visual_style: Literal["photorealistic","cinematic","documentary"]` 중 단일 선택 고정 (D-10 + AF-7 duplicate tangent 방지).
- **대안 옵션 (선택 불가)** — `photorealistic` / `documentary` — 채널 정체성 일관성 위해 LOCK.
- **적용** — Shotstack `film_grain` 필터 강도 +5%, 컷 전환 페이드 타이밍 +0.1s.

### (d) 한국 시니어 시청자 특성 (D-16)

- **연령 50~65세 타겟** — 한국 시니어 / 저관여 B2C
- **채도 낮은 톤** — warmth +0.2 + saturation -10% (Shotstack filter chain 에서 자동 적용)
- **빠른 정보 전달** — 60초 내 결론, 컷 전환 0.8~1.5초 간격
- **존댓말 narration 기본** — 반말 금지 (CONTENT-02)
- **캐릭터 대사 예외** — 탐정 하오체 + 조수 해요체 (CONTENT-02 duo persona)
- **자막 사이즈** — 16~20pt, 하단 30% safe zone 밖 배치
- **pydantic field** — `ContinuityPrefix.audience_profile: str` — 자유 문자열 (예: "Korean seniors 50-65, low-involvement B2C, 존댓말 narration")

### (e) BGM 분위기

- **LITERAL 3 presets** — pydantic field `ContinuityPrefix.bgm_mood: Literal["ambient","tension","uplift"]`:
  - **`ambient`** (default) — 평상 구간, 저주파 pad + 최소 리듬
  - **`tension`** — hook 3초 구간, 상승 strings + sub-bass drop
  - **`uplift`** — 결론-CTA 구간, 밝은 arp + 끝 리버브 tail
- **royalty-free only** — K-pop 직접 사용 금지 (AF-13). Epidemic Sound / Artlist whitelist 기반.

## prefix.json 직렬화 규격 (Plan 06 출력)

Plan 06 에서 이 노드를 소스로 `ContinuityPrefix` pydantic v2 모델이 `wiki/continuity_bible/prefix.json` 으로 직렬화됩니다. 7 필드 전체 규격:

| 필드 | 타입 | 예시 값 | 제약 |
|------|------|---------|------|
| `color_palette` | `list[HexColor]` | `["#1A2E4A","#C8A660","#E4E4E4"]` | 3~5 색 |
| `warmth` | `float` | `0.2` | -1.0 ~ +1.0 |
| `focal_length_mm` | `int` | `35` | 24~85 |
| `aperture_f` | `float` | `2.8` | 1.4~11.0 |
| `visual_style` | `Literal[...]` | `"cinematic"` | photorealistic/cinematic/documentary 3택 |
| `audience_profile` | `str` | `"Korean seniors 50-65, 존댓말 narration"` | 자유 (≤200자) |
| `bgm_mood` | `Literal[...]` | `"ambient"` | ambient/tension/uplift 3택 |

## 사용처

- **Shotstack adapter `_load_continuity_preset`** (D-9) — `scripts/orchestrator/api/shotstack.py` 의 `DEFAULT_CONTINUITY_PRESET` 이 이 JSON 을 읽어 filter chain 최전단에 자동 주입. D-19 filter order LOCK.
- **NotebookLM channel-bible notebook upload source** (D-8) — `naberal-shorts-channel-bible` 노트북의 primary source document. RAG 쿼리 답변 grounding.
- **Agent prompt `@wiki/shorts/` ref** (D-3, D-18) — Phase 4 agents (scripter, thumbnail-designer, shot-planner 등) 이 `@wiki/shorts/continuity_bible/channel_identity.md` 로 참조.

## Related

- [[../algorithm/ranking_factors]] — D-16 한국 시니어 skew 가 alg ranking 적응에 연결
- [[../kpi/retention_3second_hook]] — BGM tension preset (e) 이 3초 hook retention 강화 장치
- [[../render/remotion_kling_stack]] — continuity_prefix filter chain 최전단 주입 (D-19 first order)
- [[MOC]]
