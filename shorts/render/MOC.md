---
category: render
status: partial
tags: [moc, shorts, render]
updated: 2026-04-20
---

# Render Stack — Map of Content

> Tier 2 도메인-특화 지식 노드 맵. naberal-shorts-studio 전용.
> 실제 노드 내용은 Phase 6 (Wiki + NotebookLM Integration) 에서 채워짐.

## Scope

Remotion v4 + **Kling 2.6 Pro primary** / **Veo 3.1 Fast fallback** 렌더 스택. Low-Res First 파이프라인 + Shotstack 색보정. **2026-04-20 세션 #24 최종 확정** (오전 Runway Gen-4.5 → 오후 Gen-3a Turbo → 저녁 Kling 2.6 Pro 로 3회 번복 후 Pareto-dominant 확인; Kling 2.5-turbo Pro deprecated; Runway adapter 는 hold 상태로 미호출). 정밀/세세한 motion (얼굴 micro / 손가락 / 머리카락 / 미세 light) 에서 Kling 실패 시 Veo 3.1 Fast 로 수동 전환. auto-route 은 Phase 10 실패 패턴 축적 후 정식화.

실측 증거 (동일 anchor + Template A, 5s clip):

| 모델 | 비용/5s | 지연 | 판정 |
|------|---------|------|------|
| **Kling 2.6 Pro** | **$0.35** | **~70s** | **primary (Pareto-dominant)** |
| Veo 3.1 Fast | $0.50 | ~60-120s (추정) | fallback (정밀 motion 전용) |
| Runway Gen-4.5 | $0.60 | 149s | hold (품질 OK 이나 비용·지연 불리) |
| Runway Gen-3a Turbo | $0.25 | 22s | hold (복합 limb motion 실패) |
| ~~Kling 2.5-turbo Pro~~ | — | — | deprecated (2.6 동가격 업그레이드) |

## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [x] `i2v_prompt_engineering.md` — I2V prompt 3원칙 (camera lock / positive anatomy persistence / micro verb) + Templates A/B/C + 3-way 실측 레퍼런스 (2026-04-20 세션 #24 신설)
- [x] [adapter_contracts.md](./adapter_contracts.md) — 7 adapter (kling / runway / veo_i2v / typecast / elevenlabs / shotstack / whisperx) 입력/출력 schema + retry/fallback + fault injection + mock↔real delta 단일 계약 문서 (Phase 14 ADAPT-05, 2026-04-21 Plan 04 Task 14-04-01 신설)
- [ ] `kling_26_pro_api_spec.md` — Kling 2.6 Pro (fal.ai `kling-video/v2.6/pro/image-to-video`) 파라미터, 가격, rate limits
- [ ] `veo_31_fast_fallback_policy.md` — Kling 실패 → Veo 3.1 Fast 전환 조건 (정밀 motion 트리거, 비용 43% 상승)
- [ ] `remotion_composition_schema.md` — Remotion v4 composition 표준 구조
- [ ] `shotstack_color_grading.md` — 일괄 색보정 API (T14)
- [ ] `low_res_first_pipeline.md` — 768:1280 → AI 업스케일 2단계 (T4)
- [x] `remotion_kling_stack.md` — Remotion v4 + Kling 2.6 Pro primary + Veo 3.1 Fast fallback + Shotstack composite (2026-04-20 세션 #24 박제 batch 에서 전면 재작성, 파일명은 legacy)

## Related

- **Tier 1** (도메인-독립, `../../../../harness/wiki/`): (Phase 6에서 링크)
- **Other Tier 2 categories**: (Phase 6에서 링크)
- **Root CLAUDE.md**: [[../../CLAUDE.md]] — domain scope 참조

## Source References

- **Research basis**: `.planning/research/SUMMARY.md` §14 (17 Novel Techniques)
- **Requirements**: `.planning/REQUIREMENTS.md` §WIKI
- **Agent consumer**: Phase 4 에이전트 prompts가 `@wiki/shorts/render/MOC.md` 형식으로 참조

---

*Scaffolded: 2026-04-19 (Phase 2 Domain Definition)*
*Next update: Phase 6 (NotebookLM integration + FAILURES Reservoir)*
