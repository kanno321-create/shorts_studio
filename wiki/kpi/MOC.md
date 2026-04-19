---
category: kpi
status: scaffold
tags: [moc, shorts, kpi]
updated: 2026-04-19
---

# KPI — Map of Content

> Tier 2 도메인-특화 지식 노드 맵. naberal-shorts-studio 전용.
> 실제 노드 내용은 Phase 6 (Wiki + NotebookLM Integration) 에서 채워짐.

## Scope

Shorts 성과 지표 목표값 + 측정 방식. 3초 hook retention / 완주율 / 평균 시청 3종. 월 1회 kpi_log.md 자동 집계.

## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [ ] `three_second_hook_target.md` — retention > 60% (SUMMARY §9 Korean specifics)
- [ ] `completion_rate_target.md` — 완주율 > 40%
- [ ] `avg_watch_duration_target.md` — > 25초
- [ ] `kpi_log_template.md` — 월 1회 `kpi_log.md` 자동 생성 포맷 (KPI-02)
- [x] `retention_3second_hook.md` — 3초 retention >60% 목표 + YouTube Analytics 측정 (Phase 6 ready)

## Related

- **Tier 1** (도메인-독립, `../../../../harness/wiki/`): (Phase 6에서 링크)
- **Other Tier 2 categories**: (Phase 6에서 링크)
- **Root CLAUDE.md**: [[../../CLAUDE.md]] — domain scope 참조

## Source References

- **Research basis**: `.planning/research/SUMMARY.md` §14 (17 Novel Techniques)
- **Requirements**: `.planning/REQUIREMENTS.md` §WIKI
- **Agent consumer**: Phase 4 에이전트 prompts가 `@wiki/shorts/kpi/MOC.md` 형식으로 참조

---

*Scaffolded: 2026-04-19 (Phase 2 Domain Definition)*
*Next update: Phase 6 (NotebookLM integration + FAILURES Reservoir)*
