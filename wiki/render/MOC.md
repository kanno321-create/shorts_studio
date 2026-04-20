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

Remotion v4 + **Runway Gen-3a Turbo primary** / Kling 2.5-turbo Pro backup 렌더 스택. Low-Res First 파이프라인 + Shotstack 색보정. **2026-04-20 세션 #24 실측 재결정** (이전 Kling primary 에서 교체; 3-way 비교 결과 Gen-3a Turbo = $0.25/5s, 21s latency, 품질 충분; Gen-4.5 = 품질 우위이나 비용 2.4배 + 지연 6배로 기각; Kling 2.5-turbo = backup).

## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [ ] `runway_gen3a_turbo_api_spec.md` — Runway Gen-3a Turbo API (유효 모델/ratios, 가격 5 credits/s, rate limits)
- [ ] `kling_backup_policy.md` — Runway 실패 시 Kling 2.5-turbo Pro (fal.ai) 전환 조건
- [ ] `remotion_composition_schema.md` — Remotion v4 composition 표준 구조
- [ ] `shotstack_color_grading.md` — 일괄 색보정 API (T14)
- [ ] `low_res_first_pipeline.md` — 768:1280 → AI 업스케일 2단계 (T4)
- [x] `remotion_kling_stack.md` — Remotion v4 + Runway Gen-3a Turbo primary + Kling 2.5-turbo backup + Shotstack composite (2026-04-20 세션 #24 재결정 후 업데이트 예정)

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
