---
tags: [readme, wiki-home, tier-2, shorts]
---

# 📚 naberal-shorts-studio — Tier 2 Wiki

도메인-특화 지식 노드. naberal-shorts-studio 전용 RAG 소스.

## Tier 분류

- **Tier 1** (`../../../harness/wiki/`): 도메인-독립 공용 노드 (한국어 존댓말 baseline, YouTube API 한도 등)
- **Tier 2** (이 폴더): 쇼츠 도메인 전용 (알고리즘, YPP 기준, 렌더 스택, KPI, Continuity Bible)
- **Tier 3** (`../.preserved/harvested/`): 과거 shorts_naberal 자산 이관 — 읽기 전용 불변 (Phase 3 chmod -w)

## 카테고리 (5)

| 카테고리 | Scope | MOC |
|----------|-------|-----|
| `algorithm/` | YouTube Shorts 추천 알고리즘 + ranking 요소 | [[algorithm/MOC]] |
| `ypp/` | YouTube Partner Program 진입 조건 | [[ypp/MOC]] |
| `render/` | Remotion v4 + Kling 2.6 Pro / Runway Gen-3 Alpha Turbo 렌더 스택 | [[render/MOC]] |
| `kpi/` | 3초 hook retention / 완주율 / 평균 시청 지표 | [[kpi/MOC]] |
| `continuity_bible/` | 색상 팔레트 + 카메라 렌즈 + 시각 스타일 prefix (D-1) | [[continuity_bible/MOC]] |

## NotebookLM 연동 (Phase 6)

- **노트북 A: 일반** — shorts 도메인 일반 지식 (알고리즘, YPP, 렌더)
- **노트북 B: 채널바이블** — 채널 정체성 (Continuity Bible, 탐정/조수 페르소나, 색상 팔레트)
- Fallback Chain: NotebookLM RAG → grep wiki/ → hardcoded defaults (WIKI-04)

## 현재 상태

**Phase 2 (2026-04-19):** Scaffold — 5 카테고리 폴더 + MOC 스켈레톤만 존재. 실 노드는 Phase 6.

**추가 절차:**
1. Phase 6 실행 시 각 MOC.md의 `Planned Nodes` checkbox를 채우며 노드 파일 생성
2. 노드 생성 시 frontmatter `status: stub → ready` 승격
3. Tier 1 이관 대상 노드 발견 시 Phase 6 검토 후 batch 이관

---

*Scaffolded: 2026-04-19 (Phase 2 Domain Definition)*
