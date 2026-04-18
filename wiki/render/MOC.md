---
category: render
status: scaffold
tags: [moc, shorts, render]
updated: 2026-04-19
---

# Render Stack — Map of Content

> Tier 2 도메인-특화 지식 노드 맵. naberal-shorts-studio 전용.
> 실제 노드 내용은 Phase 6 (Wiki + NotebookLM Integration) 에서 채워짐.

## Scope

Remotion v4 + Kling 2.6 Pro primary / Runway Gen-3 Alpha Turbo backup 렌더 스택. Low-Res First 파이프라인 + Shotstack 색보정.

## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [ ] `kling_api_spec.md` — Kling 2.6 Pro API (HMAC 서명, 가격, rate limits)
- [ ] `runway_fallback_policy.md` — Kling 실패 시 Runway Gen-3 Alpha Turbo 전환 조건
- [ ] `remotion_composition_schema.md` — Remotion v4 composition 표준 구조
- [ ] `shotstack_color_grading.md` — 일괄 색보정 API (T14)
- [ ] `low_res_first_pipeline.md` — 720p → AI 업스케일 2단계 (T4)

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
