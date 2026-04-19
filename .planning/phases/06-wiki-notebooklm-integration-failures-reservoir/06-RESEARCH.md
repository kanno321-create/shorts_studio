# Phase 6: Wiki + NotebookLM Integration + FAILURES Reservoir — Research

**Researched:** 2026-04-19
**Domain:** Knowledge infrastructure + RAG wiring + learning reservoir (Obsidian-flavoured Tier 2 wiki nodes + NotebookLM 2-notebook RAG + FAILURES.md append-only + SKILL_HISTORY backup + 30-day aggregation CLI)
**Confidence:** HIGH (20 locked decisions D-1~D-20 in CONTEXT.md + infrastructure already in place from Phase 5 + external skill contract already readable + dependencies already installed + 15 agents with Phase 6 placeholders already surface-mapped)

## Summary

Phase 6 is the plumbing phase that fills the knowledge holes Phase 5 explicitly punted on (D-17 placeholder "Phase 6 확정") while installing the FAILURES-as-learning-reservoir discipline that Phase 10 needs as a pre-condition. Five Tier 2 wiki categories exist as MOC scaffolds from Phase 2; Phase 6 converts the `Planned Nodes` checkboxes into `status: ready` nodes with frontmatter + Obsidian graph links. A `ContinuityPrefix` pydantic v2 model lands in `scripts/orchestrator/api/models.py` alongside the existing `I2VRequest` / `ShotstackRenderRequest`, and `ShotstackAdapter` auto-injects the prefix at the first position of its filter chain while preserving the D-17 `color_grade → saturation → film_grain` invariant. Two `.claude/deprecated_patterns.json` regexes are added (FAILURES.md line-delete + SKILL.md direct edit without backup). `SKILL_HISTORY/<skill>/v{timestamp}.md.bak` backup logic is implemented in `pre_tool_use.py`. A `scripts/failures/aggregate_patterns.py` CLI runs dry-run pattern counting across the (immutable 500-line imported file + the new append-only FAILURES.md) to flag ≥3-occurrence patterns. Finally, 15 of the 32 Phase 4 agent prompts (those that currently embed `Phase 6` placeholders) get real `@wiki/shorts/<category>/<node>.md` references substituted in.

The research establishes that every dependency is available at target versions (pydantic 2.12.5, httpx 0.28.1, pytest 8.4.2, Python 3.11.9), the external `shorts_naberal/.claude/skills/notebooklm` wrapper contract is stable and callable via environment variable, and the Phase 5 `shotstack.py` adapter has a well-defined injection seam at `_build_timeline_payload`'s `filters_order` parameter. Two risks dominate: (a) NotebookLM authentication state stored in `~/.claude/skills/notebooklm/data/browser_state/` may be stale and require interactive re-auth (Playwright + Google manual login), and (b) the Hook regex for FAILURES.md append-only enforcement MUST distinguish "delete existing line" from "edit newly-added line before commit" — the simplest safe heuristic is "block any Edit whose `old_string` matches a regex of the imported FAILURES file's line structure OR matches a committed line in FAILURES.md" — which requires git blame or a staged-diff check.

**Primary recommendation:** Split Phase 6 into **9 plans across 5 waves**. Wave 0 scaffolds frontmatter schema validator + wiki linter. Wave 1 authors 5 wiki nodes (1 per category, parallel). Wave 2 writes NotebookLM wrapper + library.json extension + Fallback Chain (sequential — wrapper is prerequisite for Fallback). Wave 3 ships `ContinuityPrefix` pydantic model + Shotstack injection + pytest on filter-order invariant. Wave 4 extends the Hook (2 new regexes + SKILL_HISTORY backup) + ships `aggregate_patterns.py` CLI + agent prompt mass update (parallel where independent). Wave 5 is the Phase 6 gate: VALIDATION.md flip + 9/9 REQ traceability + sha256 immutability verification on `_imported_from_shorts_naberal.md`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tier 규율 (D-1~D-3)**
- **D-1: Tier 2 단독 범위** — `naberal_harness/wiki/` (Tier 1) 는 Phase 2 결정 D2-A대로 빈 폴더 유지. 공유 가능성 판단 Phase 10까지 deferred. Phase 6에서 생성되는 모든 노드는 `studios/shorts/wiki/` 아래에만 배치. 성급한 일반화는 shorts 편향을 공용 제약으로 변질시킴.
- **D-2: 5 카테고리 구조 고정** — `algorithm/`, `ypp/`, `render/`, `kpi/`, `continuity_bible/` 5개만. 신규 카테고리 추가 금지 (Phase 6 범위). 카테고리별 MOC.md 기존 `Planned Nodes` checkbox가 실노드 파일로 변환되는 것을 최소 단위로 함.
- **D-3: 노드 참조 포맷 `@wiki/shorts/xxx.md` 고정** — 에이전트 프롬프트에서 절대 경로/상대 경로 혼용 금지. `@wiki/shorts/algorithm/ranking_factors.md` 형식만 허용. Phase 4 32 agents 전수 grep + 교체.

**NotebookLM 2-노트북 분리 (D-4~D-8)**
- **D-4: 2-노트북 분리 원칙** — 일반 노트북(리서치/알고리즘/YPP 소스) ≠ 채널바이블 노트북(Continuity prefix 전용). 교차 오염 시 hallucination 재발. 쿼리 대상 노트북 결정은 호출부에서 명시적 노트북 ID 지정.
- **D-5: NotebookLM Fallback Chain 3-tier 필수** — `RAG query → grep wiki/ → hardcoded defaults` 순서로 자동 전환. RAG 단독 의존 시 Google outage = 파이프라인 전체 중단. 의도적 API fail 시뮬레이션으로 fallback 실측 검증 (`test_notebooklm_fallback.py`).
- **D-6: NotebookLM 쿼리 규율 — 완성된 단일 문자열** — `feedback_notebooklm_query.md` 메모리 규칙 준수. 실시간 타이핑·다중 질문 금지. 쿼리는 호출 전 완성된 1개 문자열로 작성 후 browser input에 paste. 한국어 쿼리 허용.
- **D-7: `shorts_naberal/.claude/skills/notebooklm/` 인프라 참조(복사 아님)** — Playwright + browser_state 중복 인증 세션 금지. studios/shorts는 wrapper 스크립트만 작성 + 환경변수로 skill 경로 참조 (`NOTEBOOKLM_SKILL_PATH`). skill 자체 코드는 복제 금지.
- **D-8: library.json 채널바이블 노트북 추가** — 기존 `shorts-production-pipeline-bible` 보존. 신규 `naberal-shorts-channel-bible` 항목 append. 등록 후 최소 1회 query 검증으로 authentication + RAG 동작 증명.

**Continuity Bible Prefix 자동 주입 (D-9~D-10)**
- **D-9: ShotstackAdapter color preset 직접 주입** — 수동 복붙 금지. Phase 5 `scripts/orchestrator/api/shotstack.py`의 `DEFAULT_RESOLUTION="hd"` 바로 옆에 `DEFAULT_CONTINUITY_PRESET` dict 추가. 렌더 요청 빌드 시 filter chain 최전단에 자동 삽입. D-17 filter order 준수.
- **D-10: Continuity Bible 5 구성요소** — (a) 색상 팔레트(HEX 3-5색 + warmth), (b) 카메라 렌즈(초점거리 + aperture), (c) 시각적 스타일(photorealistic/cinematic/documentary 중 1개 lock), (d) 한국 시니어 시청자 특성(채도 낮은 톤·깔끔한 구도), (e) BGM 분위기(ambient/tension/uplift 3 preset). wiki 노드 `continuity_bible/channel_identity.md`에 정식 기록 + JSON 직렬화 `continuity_bible/prefix.json` 별도 제공(API adapter가 읽음).

**FAILURES 저수지 규율 (D-11~D-13)**
- **D-11: `FAILURES.md` append-only via Hook 차단** — `.claude/deprecated_patterns.json`에 신규 regex 추가: 기존 `FAILURES.md` 라인 수정/삭제 시 write 차단. 새 entry는 파일 끝 append만 허용. Hook subprocess test로 실증.
- **D-12: `SKILL_HISTORY/{skill_name}/v{n}.md.bak` 백업** — SKILL 파일 수정 감지 훅이 수정 직전 기존 버전을 `SKILL_HISTORY/<skill>/v<timestamp>.md.bak`로 복사. 복구 가능성 보장. Phase 10 첫 1~2개월 SKILL patch 금지 기간 규율(FAIL-04)과 연동.
- **D-13: 30-day 집계 dry-run** — `scripts/failures/aggregate_patterns.py` CLI 작성. input=`FAILURES.md` + `_imported_from_shorts_naberal.md`. 패턴 키 해시 기반 카운트 → ≥3 발견 시 `SKILL.md.candidate` + 7-day staged rollout state 기록. Phase 6에서는 **dry-run 출력만** 검증. 실 승격은 Phase 10.

**기존 자산 보존 (D-14)**
- **D-14: `_imported_from_shorts_naberal.md` 500줄 완전 불변** — Phase 3 sha256=978bb938... 고정. Phase 6에서 FAILURES 구조화 시에도 이 파일의 **원본 라인 수정 금지**. 구조화(카테고리 태깅/index) 필요 시 별도 `FAILURES_INDEX.md` 파일로 제공.

**SKILL 슬림화 (D-15)**
- **D-15: SKILL.md ≤500줄 본문 + 나머지는 wiki 참조** — Lost in the Middle 완화 (RULER 벤치마크 기반). SKILL 500줄 초과 시 harness-audit(Phase 7)에서 A급 drift 경고. Phase 6에서는 기존 SKILL 파일 실측만 수행(위반 시 Phase 9 개선 대상으로 deferred-items.md 기록).

**한국 시장 특화 (D-16)**
- **D-16: 한국 시니어/저관여 B2C 시청자 반영** — 3초 hook, 질문형 제목 패턴, 존댓말/반말 스위칭(스크립터), KOMCA 저작권 준수, Typecast TTS 1위 고정. 채널바이블 노트북에 이 컨텍스트 명시 포함. NotebookLM 쿼리 기본 언어 = 한국어.

**노드 메타데이터 (D-17)**
- **D-17: Wiki 노드 frontmatter 스키마** — `category: <algorithm|ypp|render|kpi|continuity_bible>`, `status: <stub|ready>`, `tags: [...]`, `updated: YYYY-MM-DD`, `source_notebook: <notebook_id>` 필드 필수. 기존 MOC.md 스키마 연속성 유지. `status=ready`만 에이전트 참조 가능(`status=stub`은 WIP).

**Phase 4 Agent Prompt 주입 (D-18)**
- **D-18: Phase 6에서 32 agents prompt 전수 수정** — Phase 7 이관 금지. wiki 노드와 agent prompt는 pair로 완성되어야 downstream verification이 의미를 가짐. 수정 대상: `.claude/agents/**/*.md` 에서 기존 placeholder(TBD/Phase 6) → 실 `@wiki/shorts/xxx.md` 참조 교체. 교체 전후 prompt 길이 delta 기록.

**Shotstack 주입 지점 (D-19~D-20)**
- **D-19: Shotstack filter order 고정 (D-17 Phase 5 준수)** — ContinuityPrefix filter = first in chain. 기존 Phase 5 filter order 계약 유지: `continuity_prefix → color_correction → stabilize → ken_burns(fallback시)`. 순서 위반 시 pytest 실패.
- **D-20: Continuity prefix JSON 스키마 pydantic v2 고정** — `scripts/orchestrator/api/models.py`에 `ContinuityPrefix` 클래스 추가 (color_palette: list[HexColor], focal_length_mm: int, aperture_f: float, visual_style: Literal["photorealistic","cinematic","documentary"], audience_profile: str, bgm_mood: Literal["ambient","tension","uplift"]). Shotstack adapter가 이 객체를 소비.

### Claude's Discretion (구현 세부)

- 각 카테고리 내 실노드 파일명·개수(최소 1개 ready). 단 `continuity_bible/channel_identity.md`는 D-10 구성요소 5개 포함 필수.
- NotebookLM query wrapper 위치: `scripts/notebooklm/query.py` vs `scripts/wiki/notebooklm_query.py` — planner 판단.
- FAILURES 30-day aggregation CLI 파일 경로: planner 판단(단 `scripts/failures/` 아래).
- Hook subprocess test 파일 위치: `tests/phase06/` (Phase 5 패턴 승계).

### Deferred Ideas (OUT OF SCOPE)

- **Tier 1 공유 노드 승격**: Phase 10 데이터 수집 후 재평가. Phase 6 범위 외 (D-1).
- **실제 30-day 집계 실행**: Phase 10에서 실데이터로. Phase 6는 dry-run 검증까지 (D-13).
- **SKILL 500줄 초과 실제 분할**: Phase 9 deferred-items.md에 기록하고 Phase 9 개선 작업 (D-15).
- **NotebookLM 신규 노트북 URL 확보**: 대표님이 Google NotebookLM 콘솔에서 신규 "채널바이블" 노트북 생성 후 URL 제공 필요. Phase 6 execute 중 blocking 발생 시 placeholder URL로 진행 + deferred-items.md에 실 URL 교체 TODO 기록.
- **NotebookLM authentication refresh**: 기존 `browser_state` 만료 시 재인증 필요 — Phase 6에서 감지 시 대표님에 1회 재인증 요청 후 진행.
- **Continuity prefix를 Kling/Runway adapter에도 주입**: Phase 6은 Shotstack만. Kling/Runway adapter 확장은 Phase 7 통합 테스트에서 필요성 판단.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIKI-01 | Tier 2 `studios/shorts/wiki/` 도메인 특화 노드 (알고리즘/YPP/렌더/KPI) Obsidian 그래프 | §Area 1 (Frontmatter schema + Obsidian link syntax + 5 ready nodes enumeration) |
| WIKI-02 | Continuity Bible (색상 팔레트/카메라 렌즈/시각적 스타일) — 모든 API 호출 시 Prefix 자동 주입 | §Area 5 (ContinuityPrefix pydantic v2 + Shotstack `filters_order` injection) |
| WIKI-03 | NotebookLM 2-노트북 세팅 (일반 + 채널바이블) | §Area 2 (library.json extension schema + channel-bible creation flow) |
| WIKI-04 | NotebookLM Fallback Chain (RAG 실패 시 grep wiki → hardcoded defaults) | §Area 4 (3-tier interface contract + deterministic fault injection test) |
| WIKI-05 | 에이전트 프롬프트에서 wiki 노드 참조는 `@wiki/shorts/xxx.md` 형식 고정 | §Area 9 (15/32 agents already contain `Phase 6` placeholders — mass update surface) |
| WIKI-06 | SKILL.md는 ≤500줄 본문 + 나머지는 wiki 참조 (Lost in the Middle 완화) | §Area 1 + §Area 11 (measurement only per D-15; violations deferred to Phase 9) |
| FAIL-01 | `FAILURES.md` append-only (즉시 SKILL 수정 금지) — D-2 저수지 원칙 | §Area 6 (Hook regex design + `old_string` committed-line detection + false-positive mitigation) |
| FAIL-02 | 30일 집계 → 패턴 ≥ 3회 → `SKILL.md.candidate` → 7일 staged rollout → 승격 | §Area 8 (pattern key normalization + 2-schema unification + dry-run JSON output) |
| FAIL-03 | `SKILL_HISTORY/` 디렉토리 — SKILL 수정 시 기존 버전 `v{n}.md.bak` 백업 | §Area 7 (pre-tool hook trigger + timestamp filename + restoration UX) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **도메인 절대 규칙 8개** 불변 (skip_gates / TODO(next-session) / try-except 침묵 / T2V / Selenium / shorts_naberal 수정 / K-pop 직접 사용 / 주 3~4편). Phase 6 작업은 이 8개 중 어느 것도 접촉하지 않아야 함.
- **SKILL.md ≤ 500줄** — D-15 동일 원칙. Phase 6은 새 SKILL 파일 생성 안 함, 기존 감사만.
- **에이전트 총합 32명** (Producer 14 + Inspector 17 + Supervisor 1) — D-18이 이 32명 모두 순회하는 scope.
- **Hooks 3종 활성** — pre_tool_use.py 가 이 phase 에서 확장 대상 (D-11 + D-12).
- **GSD Workflow Enforcement** — 작업은 `/gsd:execute-phase` 통해.
- **shorts_naberal 원본 수정 금지** — D-7 NotebookLM skill 참조 방식 준수.

## Standard Stack

### Core (all verified installed on target machine — Phase 5 carry-over)

| Library | Version (verified 2026-04-19) | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11.9 | runtime | Phase 5 D-19 요건 승계 (match_case, walrus, typing.Self) |
| `pydantic` | 2.12.5 | ContinuityPrefix schema (D-20), validation at parse time | Phase 5 `I2VRequest`/`ShotstackRenderRequest` 패턴 동일 — `arbitrary_types_allowed=True` + `Field(...)` 제약 |
| `httpx` | 0.28.1 | Shotstack API call (carry-over) | 변경 없음 — `_post_render` 기존 pattern 유지 |
| `pytest` | 8.4.2 | test runner (Phase 5 precedent tests/phase05/) | Phase 6은 `tests/phase06/` 신규 디렉토리, conftest는 phase05 패턴 복제 |
| stdlib `pathlib` | built-in | wiki node file ops + SKILL_HISTORY backup | Phase 1 Hook이 이미 pathlib.Path 사용 |
| stdlib `hashlib` | built-in | sha256 of `_imported_from_shorts_naberal.md` immutability check | Phase 3 Checkpoint pattern 승계 |
| stdlib `json` | built-in | library.json append + prefix.json serialization | Phase 5 Checkpointer pattern |
| stdlib `re` | built-in | Hook regex + FAILURES append-detection | pre_tool_use.py 이미 `re.search` 사용 |
| stdlib `subprocess` | built-in | NotebookLM run.py wrapper invocation | shorts_naberal skill은 `run.py` subprocess가 유일한 공식 API |
| stdlib `shutil` | built-in | SKILL_HISTORY backup (copy2) | timestamp 보존 복사 |
| stdlib `datetime` | built-in | backup filename timestamp (v20260419_143000.md.bak) | 기존 `shorts_naberal/SKILL_HISTORY/` 실존 패턴 참조 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pyyaml` | 6.x (해당 시 stdlib `yaml` 부재 → 요구되면 pip install) | frontmatter parsing for wiki nodes | wiki-linter가 YAML frontmatter 해석 필요 — **ALT: stdlib `json` + 자체 frontmatter parser 20줄** (추천, 의존성 최소화) |
| shorts_naberal `notebooklm` skill | (external, read-only) | Playwright + patchright browser automation | D-7 per decision; invoked only via `subprocess.run([sys.executable, SKILL_PATH/"scripts/run.py", "ask_question.py", ...])` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom YAML parser (20-line regex) | `pyyaml` dependency | pyyaml adds external dep and supply-chain risk for a 20-line need. Phase 5 avoided yaml entirely. **DECISION: custom regex frontmatter parser.** |
| `subprocess.run(run.py, ...)` | direct Playwright import | D-7 explicitly forbids skill code duplication. Running the wrapper via subprocess keeps the venv and browser_state isolated to the external skill directory. **DECISION: subprocess only.** |
| Git-based FAILURES append-only enforcement | Hook regex | Git hooks fire at commit time (too late — already written). pre_tool_use Hook fires at Edit/Write invocation (catches before file touched). **DECISION: pre_tool_use extension.** |
| Pre-tool Hook backup for SKILL | Post-tool backup | Pre-tool captures the OLD version before write; Post-tool only captures AFTER (useless for rollback). **DECISION: pre_tool_use backup in `.claude/hooks/pre_tool_use.py` before Write/Edit dispatch.** |
| `graphlib.TopologicalSorter` for wiki link DAG | Manual BFS | Phase 5 already uses graphlib for GATE DAG; Phase 6 wiki links are a flat graph (not DAG) — `networkx` overkill, manual adjacency dict sufficient. **DECISION: manual adjacency + link-validator pass.** |

**Installation** (no new package installs needed — everything is stdlib or already present):
```bash
# Verification only — no installs
python -c "import pydantic, httpx, pytest; print(pydantic.VERSION, httpx.__version__, pytest.__version__)"
# Expected: 2.12.5 0.28.1 8.4.2
```

**Version verification:** All 3 critical libs verified via direct `python -c "import X"` on 2026-04-19. No drift from Phase 5 baseline. No Phase 6-specific installs required.

## Architecture Patterns

### Recommended File Structure (additions to existing tree)

```
studios/shorts/
├── wiki/
│   ├── algorithm/
│   │   ├── MOC.md                     # exists (scaffold)
│   │   └── ranking_factors.md         # NEW Phase 6 (status=ready)
│   ├── ypp/
│   │   ├── MOC.md
│   │   └── entry_conditions.md        # NEW
│   ├── render/
│   │   ├── MOC.md
│   │   └── remotion_kling_stack.md    # NEW
│   ├── kpi/
│   │   ├── MOC.md
│   │   └── retention_3second_hook.md  # NEW
│   └── continuity_bible/
│       ├── MOC.md
│       ├── channel_identity.md        # NEW (5 components per D-10)
│       └── prefix.json                # NEW (JSON serialization of ContinuityPrefix)
├── scripts/
│   ├── notebooklm/
│   │   ├── __init__.py
│   │   ├── query.py                   # NEW — subprocess wrapper to run.py
│   │   └── fallback.py                # NEW — 3-tier Fallback Chain (D-5)
│   ├── failures/
│   │   ├── __init__.py
│   │   └── aggregate_patterns.py      # NEW — 30-day dry-run CLI (D-13)
│   ├── wiki/
│   │   ├── __init__.py
│   │   ├── frontmatter.py             # NEW — 20-line YAML-lite parser
│   │   └── link_validator.py          # NEW — @wiki/shorts/xxx.md reference checker
│   ├── orchestrator/
│   │   └── api/
│   │       ├── models.py              # EXTEND — add ContinuityPrefix (D-20)
│   │       └── shotstack.py           # EXTEND — DEFAULT_CONTINUITY_PRESET + filter injection (D-9)
│   └── hook/                          # no such path; hooks live in .claude/hooks/
├── .claude/
│   ├── hooks/
│   │   └── pre_tool_use.py            # EXTEND — 2 new checks (FAILURES append-only + SKILL_HISTORY backup)
│   ├── deprecated_patterns.json       # EXTEND — 2 new regex entries (D-11)
│   ├── failures/
│   │   ├── _imported_from_shorts_naberal.md  # IMMUTABLE (D-14, sha256 verify)
│   │   ├── FAILURES.md                # NEW — append-only new-entry file
│   │   └── FAILURES_INDEX.md          # NEW — category tagging index (leaves _imported untouched)
│   └── agents/**/AGENT.md             # EDIT — 15 files with `Phase 6` placeholders → real @wiki refs
├── SKILL_HISTORY/                     # NEW DIR
│   └── <skill_name>/
│       └── v<YYYYMMDD_HHMMSS>.md.bak  # created by Hook before SKILL write
└── tests/phase06/
    ├── conftest.py
    ├── test_wiki_frontmatter.py
    ├── test_notebooklm_fallback_chain.py
    ├── test_continuity_prefix_schema.py
    ├── test_shotstack_filter_order.py
    ├── test_failures_append_only_hook.py
    ├── test_skill_history_backup.py
    ├── test_aggregate_patterns_dry_run.py
    ├── test_agent_prompt_references.py
    └── test_immutable_imported_failures.py
```

### Pattern 1: Frontmatter Schema Validator (Wiki Node Authoring)
**What:** 20-line stdlib-only YAML-lite parser that accepts the 5-field schema from D-17.
**When to use:** Every wiki node Write, in the `test_wiki_frontmatter.py` regression pass.

```python
# scripts/wiki/frontmatter.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Literal

_ALLOWED_CATEGORIES = {"algorithm", "ypp", "render", "kpi", "continuity_bible"}
_ALLOWED_STATUS = {"stub", "ready"}
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def parse_frontmatter(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{md_path}: no frontmatter block")
    body = m.group(1)
    out: dict = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out

def validate_node(md_path: Path) -> None:
    fm = parse_frontmatter(md_path)
    missing = {"category", "status", "tags", "updated", "source_notebook"} - fm.keys()
    if missing:
        raise ValueError(f"{md_path}: missing frontmatter {missing}")
    if fm["category"] not in _ALLOWED_CATEGORIES:
        raise ValueError(f"{md_path}: category '{fm['category']}' not in {_ALLOWED_CATEGORIES}")
    if fm["status"] not in _ALLOWED_STATUS:
        raise ValueError(f"{md_path}: status '{fm['status']}' not in {_ALLOWED_STATUS}")
```

### Pattern 2: Fallback Chain Protocol (NotebookLM 3-Tier)
**What:** Interface contract `query(question: str, notebook_id: str) -> str` implemented by three ordered fallback layers.
**When to use:** Every NotebookLM query from an agent or orchestrator.

```python
# scripts/notebooklm/fallback.py
from __future__ import annotations
import subprocess
import os
import re
from pathlib import Path
from typing import Protocol

class QueryBackend(Protocol):
    def query(self, question: str, notebook_id: str) -> str: ...

class RAGBackend:
    """Tier 1: real NotebookLM via external skill."""
    SKILL_PATH = Path(os.environ.get("NOTEBOOKLM_SKILL_PATH",
        r"C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm"))
    def query(self, question: str, notebook_id: str) -> str:
        cmd = [sys.executable, str(self.SKILL_PATH / "scripts/run.py"),
               "ask_question.py", "--question", question, "--notebook-id", notebook_id]
        result = subprocess.run(cmd, timeout=600, capture_output=True, text=True,
                               encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"NotebookLM fail: {result.stderr}")
        return result.stdout

class GrepWikiBackend:
    """Tier 2: grep studios/shorts/wiki/ for keyword matches."""
    WIKI_ROOT = Path("studios/shorts/wiki")
    def query(self, question: str, notebook_id: str) -> str:
        keywords = re.findall(r"\w{3,}", question)[:5]
        hits: list[str] = []
        for md in self.WIKI_ROOT.rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            if all(k.lower() in text.lower() for k in keywords):
                hits.append(f"## {md}\n{text[:500]}")
        if not hits:
            raise RuntimeError("grep wiki: no hits")
        return "\n\n".join(hits)

class HardcodedDefaultsBackend:
    """Tier 3: hardcoded baseline per D-5 (never raises)."""
    DEFAULTS = {
        "naberal-shorts-channel-bible": "색상=navy+gold, lens=35mm, style=cinematic, audience=한국 시니어, bgm=ambient",
        "shorts-production-pipeline-bible": "YPP=1000구독+10M views/yr, RPM=$0.20, T2V 금지 I2V only",
    }
    def query(self, question: str, notebook_id: str) -> str:
        return self.DEFAULTS.get(notebook_id, "fallback defaults unavailable for notebook_id=" + notebook_id)

class NotebookLMFallbackChain:
    def __init__(self, backends: list[QueryBackend] | None = None) -> None:
        self.backends = backends or [RAGBackend(), GrepWikiBackend(), HardcodedDefaultsBackend()]
    def query(self, question: str, notebook_id: str) -> tuple[str, int]:
        """Returns (answer, tier_used) — tier 0=RAG, 1=grep, 2=defaults."""
        for tier, be in enumerate(self.backends):
            try:
                return be.query(question, notebook_id), tier
            except Exception:
                continue
        raise RuntimeError("all NotebookLM fallback tiers exhausted")
```

### Pattern 3: Shotstack Continuity Prefix Injection (D-9 + D-19)
**What:** Prepend ContinuityPrefix-derived filter entries to `ShotstackRenderRequest.filters_order` while preserving D-17 invariant.

```python
# scripts/orchestrator/api/shotstack.py (EXTEND)
DEFAULT_CONTINUITY_PRESET: dict | None = None  # loaded from continuity_bible/prefix.json at import

def _inject_continuity(self, filters_order: list[str]) -> list[str]:
    """D-9/D-19: prefix injection at position 0, preserving D-17 tail."""
    if not DEFAULT_CONTINUITY_PRESET:
        return filters_order
    # The prefix itself is represented as a single filter name; the underlying
    # JSON preset is picked up downstream by Shotstack via adapter params.
    return ["continuity_prefix"] + filters_order  # D-17 tail intact
```

Test invariant:
```python
def test_filter_order_preserved():
    ad = ShotstackAdapter(api_key="x")
    result = ad._inject_continuity(["color_grade", "saturation", "film_grain"])
    assert result == ["continuity_prefix", "color_grade", "saturation", "film_grain"]
```

### Pattern 4: Append-Only Hook Discrimination (D-11)
**What:** Hook examines Edit tool payload; if `file_path` matches `FAILURES.md` AND `old_string` is non-empty (= modifying existing content rather than appending), deny.

```python
# .claude/hooks/pre_tool_use.py (EXTEND around line 170)
def check_failures_append_only(tool_name: str, tool_input: dict) -> str | None:
    fp = tool_input.get("file_path", "")
    if not fp.endswith("FAILURES.md"):
        return None
    if tool_name == "Edit":
        old = tool_input.get("old_string", "")
        if old.strip():
            return "FAILURES.md is append-only (D-11). Use Write with full new content appended, or add a new entry at EOF."
    if tool_name == "Write":
        # Require that the new content CONTAINS the existing file content as prefix
        existing = Path(fp).read_text(encoding="utf-8") if Path(fp).exists() else ""
        new = tool_input.get("content", "")
        if existing and not new.startswith(existing):
            return "FAILURES.md Write must preserve entire existing content as prefix (append-only)."
    return None
```

### Pattern 5: SKILL_HISTORY Backup via Hook (D-12)
**What:** Before any Write/Edit to `SKILL.md`, copy current file to `SKILL_HISTORY/<skill_name>/v<timestamp>.md.bak`.

```python
def backup_skill_before_write(tool_input: dict) -> None:
    fp = Path(tool_input.get("file_path", ""))
    if fp.name != "SKILL.md":
        return
    if not fp.exists():
        return  # first-time creation, nothing to back up
    skill_name = fp.parent.name
    history_dir = Path("SKILL_HISTORY") / skill_name
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(fp, history_dir / f"v{stamp}.md.bak")
```

### Anti-Patterns to Avoid

- **Duplicating the notebooklm skill into studios/shorts/** — forbidden by D-7. Creates two auth sessions that fight for the same Google cookies; both break.
- **Using `pyyaml` for 5 frontmatter fields** — 40MB dep tree for a job a 20-line regex does. Phase 5 avoided yaml.
- **Running aggregate_patterns.py against real data in Phase 6** — D-13 explicitly says dry-run only. Running the full promotion to SKILL.md.candidate would corrupt the Phase 10 regime.
- **Editing `_imported_from_shorts_naberal.md`** — D-14 sha256 lock. Even a whitespace fix breaks the Phase 3 immutability invariant and violates HARVEST-04.
- **Adding `continuity_prefix` as a 4th entry in filters_order instead of position 0** — D-19 requires `first in chain`. Saturation before prefix changes the entire color grade pipeline.
- **Running NotebookLM queries via typed-character simulation** — D-6 + `feedback_notebooklm_query.md` memory rule. Must be clipboard paste of a pre-composed single string.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| NotebookLM browser automation | a second Playwright setup in studios/shorts | external `shorts_naberal/.claude/skills/notebooklm` via `subprocess.run(run.py)` | D-7 explicit. Two Playwright instances = two browser profiles = dual auth sessions → cookie race → both fail. The existing skill has battle-tested auth handling for Google manual login. |
| YAML frontmatter parsing | pyyaml import | 20-line stdlib regex (see Pattern 1) | 40MB dep for 5 fields is gratuitous. Phase 5 precedent: no yaml in stack. |
| Obsidian graph computation | `networkx` | stdlib dict adjacency + manual BFS | Wiki has 5 categories × 1-2 nodes each (≤10 nodes); networkx overkill. |
| Pydantic HexColor type | Custom HexColor regex | `pydantic.constr(pattern=r"^#[0-9A-Fa-f]{6}$")` | Pydantic v2 already supports constrained strings via `Annotated[str, Field(pattern=...)]`. Save the wheel. |
| 30-day pattern aggregation | pandas | stdlib `collections.Counter` + hashlib + argparse | Input is ≤1MB markdown (500 imported + append-only growing); pandas overkill. |
| Diff detection for FAILURES | full git integration | Hook stat() old-file + string-prefix check | Git-based = runs at commit (too late). Pre-tool hook fires before write. |

**Key insight:** Phase 6 is an **integration phase, not a build-from-scratch phase.** The heavy lifting (Playwright browser automation, pydantic schemas, shotstack adapter) is already in place from Phase 5 and the external skill. Phase 6's job is wiring, not invention. Every attempt to "improve" existing infrastructure by rewriting it violates the harvest discipline from Phase 3.

## Runtime State Inventory

> Phase 6 is a **content-authoring + configuration phase** with limited runtime state impact. The items below are rename/refactor-adjacent only in that the `@wiki/shorts/` reference format is being introduced into 15 agent prompts. No pre-existing runtime state embeds the old placeholder strings because the placeholders were stubs awaiting Phase 6 (the placeholders themselves never flowed into a running system).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None** — No database, ChromaDB, Redis, or SQLite in this project. Verified by `ls studios/shorts/` (no data/, no db files). NotebookLM's own library.json is a file, not a live DB. | No data migration needed. library.json gets an append (D-8). |
| Live service config | **NotebookLM notebook registry** — live state stored in external skill's `data/library.json`. Phase 6 MUST append `naberal-shorts-channel-bible` entry; this requires 대표님 to first create the notebook at notebooklm.google.com and provide the UUID URL. Planner must include an item: "blocking on 대표님-provided URL; fallback to placeholder `TBD-url-await-user`." | JSON file append (D-8). Dry-run test validates schema round-trip. |
| OS-registered state | **None** — No Windows Task Scheduler tasks, no pm2, no systemd units for this project. Phase 5 confirmed. | No re-registration. |
| Secrets/env vars | **`NOTEBOOKLM_SKILL_PATH`** (NEW, D-7) — optional env var pointing at `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm`. Default hardcoded in fallback.py. No real secret; just a path. Also `SHOTSTACK_API_KEY` (already live from Phase 5, unchanged). | Document in a new `.env.example` entry or README note. No SOPS involved. |
| Build artifacts / installed packages | **`shorts_naberal/.claude/skills/notebooklm/.venv/`** — existing Playwright venv; Phase 6 MUST NOT touch this (D-7). `studios/shorts/` itself needs no new installs (already verified). | None. Verify via Phase 3 Tier-3 lockdown that attrib +R still applies. |

**Nothing found in category (explicit):** Stored data, OS-registered state — verified by filesystem scan. Build artifacts for studios/shorts/ — no new binaries produced.

**The canonical question answered:** After every wiki file is written and every agent prompt is updated with real references, the only live runtime state that changes is (a) NotebookLM library.json gains 1 entry, (b) `.claude/deprecated_patterns.json` gains 2 regex entries, (c) `.claude/hooks/pre_tool_use.py` gains ~50 lines. All three are file-based and under version control. No out-of-repo state carries the Phase 6 changes.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.11+ | All scripts | ✓ | 3.11.9 | — |
| pydantic v2 | ContinuityPrefix model | ✓ | 2.12.5 | — |
| httpx | Shotstack HTTP (existing) | ✓ | 0.28.1 | — |
| pytest | test suite | ✓ | 8.4.2 | — |
| shorts_naberal notebooklm skill | NotebookLM RAG Tier 1 | ✓ (path `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/`) | SKILL.md present, run.py present, library.json present | — (core dep for Tier 1) |
| NotebookLM browser_state | Playwright auth persistence | ⚠️ UNKNOWN — may be expired | last seen 2026-04-07 per library.json | User re-auth via `run.py auth_manager.py setup` (interactive, 1-time) |
| NotebookLM channel-bible notebook URL | D-8 library.json entry | ✗ — not yet created in Google NotebookLM console | — | Placeholder URL `TBD-url-await-user`, logged as blocking deferred-item |
| Google Chrome / Chromium | Playwright headless mode | ✓ (patchright auto-installs) | managed by run.py venv | — |
| git | Commit workflow + FAILURES append-only fallback check | ✓ | present | — |

**Missing dependencies with no fallback:** None — every hard dependency is present. The only blocking item is **user action** (create channel-bible notebook in Google console + provide URL + potentially re-auth).

**Missing dependencies with fallback:** 
- Channel-bible notebook URL → use placeholder, log to deferred-items.md, proceed with wiki + prefix work.
- Expired browser_state → planner includes a Wave 0 step: `python run.py auth_manager.py status` → if not authenticated, request 대표님 to run `auth_manager.py setup` once; then retry.

## Area 1: Wiki Node Authoring Methodology

### Frontmatter Schema (D-17 — canonical)

```yaml
---
category: algorithm           # required; enum of 5 per D-2
status: ready                 # required; enum {stub, ready}; only ready is agent-visible
tags: [moc, shorts, ...]     # required; list
updated: 2026-04-19           # required; ISO date
source_notebook: shorts-production-pipeline-bible   # required; notebook id or "hardcoded" if no NotebookLM source
---
```

### Linkage Conventions

- **Inside Obsidian syntax (for human graph navigation):** `[[algorithm/ranking_factors]]` or `[[ranking_factors]]` (Obsidian resolves by basename). Already used in existing MOC.md scaffolds.
- **Inside Claude agent prompts (for AI context references):** `@wiki/shorts/algorithm/ranking_factors.md` (D-3 fixed format). The `@` prefix triggers Claude's file-read affordance.
- **Cross-references between wiki nodes:** Use Obsidian `[[...]]`. Prefer basename-unique filenames within a category to avoid collisions.
- **MOC back-links:** Every leaf node SHOULD link back to its category MOC via a `## Related` section, matching the pattern in existing scaffolds.

### 5 Required `status: ready` Nodes (Minimum Viable — one per category)

| Category | Node filename | Content focus | Source |
|----------|---------------|---------------|--------|
| `algorithm/` | `ranking_factors.md` | 3초 hook + completion rate + CTR + rewatch ratio (Korean seniors skew) | MOC Planned Node #1 + research/SUMMARY.md §9 |
| `ypp/` | `entry_conditions.md` | 1000 subs + 10M views/year (Shorts pathway) vs 1000 subs + 4K watch hours (long-form pathway); Korean RPM ~$0.20 | MOC Planned Node #3 + research/SUMMARY.md §11 |
| `render/` | `remotion_kling_stack.md` | Remotion v4 + Kling 2.6 Pro primary + Runway Gen-3 Alpha Turbo backup; 720p-first + Shotstack composite | MOC Planned Node + Phase 5 RESEARCH §STACK |
| `kpi/` | `retention_3second_hook.md` | Target >60% retention at t=3s; measurement via YouTube Analytics `audienceRetention` field | MOC Planned Node #1 + REQUIREMENTS KPI-06 |
| `continuity_bible/` | `channel_identity.md` + `prefix.json` | 5 components per D-10 (palette/lens/style/audience/bgm); JSON machine-readable for adapter | D-10 mandatory |

### Validation Pass

- **Lint:** `scripts/wiki/frontmatter.py::validate_node()` for each `*.md` under `wiki/`. Fails on missing/invalid enum fields.
- **Reference integrity:** `scripts/wiki/link_validator.py` walks `@wiki/shorts/...` mentions in `.claude/agents/**/AGENT.md` and asserts file exists + `status: ready`.

### Code Example — Minimal Ready Node

```markdown
---
category: algorithm
status: ready
tags: [algorithm, ranking, shorts]
updated: 2026-04-19
source_notebook: shorts-production-pipeline-bible
---

# Ranking Factors — YouTube Shorts 알고리즘

## 핵심 신호 (우선순위)
1. 완주율 (completion rate)
2. 3초 retention
3. 재시청율 (loop)
...

## Related
- [[../continuity_bible/channel_identity]] — hook 언어 톤
- [[MOC]] — 카테고리 전체
```

## Area 2: NotebookLM Library Extension

### library.json Schema (current — carry-over)

Two notebooks already registered. Schema fields:

```json
{
  "notebooks": {
    "<id>": {
      "id": "<id>",
      "url": "https://notebooklm.google.com/notebook/<uuid>",
      "name": "Human name",
      "description": "...",
      "topics": ["..."],
      "content_types": [],
      "use_cases": [],
      "tags": [],
      "created_at": "ISO",
      "updated_at": "ISO",
      "use_count": 0,
      "last_used": null
    }
  },
  "active_notebook_id": "<id>",
  "updated_at": "ISO"
}
```

### New Entry (D-8)

```json
"naberal-shorts-channel-bible": {
  "id": "naberal-shorts-channel-bible",
  "url": "TBD-url-await-user",
  "name": "Naberal Shorts Channel Bible",
  "description": "Continuity Bible prefix 전용. 색상 팔레트 + 카메라 렌즈 + 시각 스타일 + 한국 시니어 타겟팅.",
  "topics": ["continuity","channel-identity","korean-seniors","color-palette","camera-lens"],
  "content_types": [],
  "use_cases": [],
  "tags": [],
  "created_at": "2026-04-19T...",
  "updated_at": "2026-04-19T...",
  "use_count": 0,
  "last_used": null
}
```

### Creation Flow

1. **User (대표님) action required:** Open https://notebooklm.google.com → Create new notebook → upload `studios/shorts/wiki/continuity_bible/channel_identity.md` + `prefix.json` + `studios/shorts/CLAUDE.md` as sources → copy URL → report to Claude.
2. **Claude action (planner Wave 2):** Use `subprocess.run([sys.executable, SKILL_PATH/"scripts/run.py", "notebook_manager.py", "add", "--url", URL, "--name", ..., "--description", ..., "--topics", ...])`.
3. **Verification:** Run 1 sanity query via `ask_question.py --notebook-id naberal-shorts-channel-bible --question "한 줄로 이 노트북의 주제를 말해줘"`. Expected: source-grounded answer referencing channel_identity.md.

### Authentication Reuse (D-7)

- The existing `shorts_naberal/.claude/skills/notebooklm/data/browser_state/` holds Google login cookies for this Playwright profile.
- **No credentials are copied into studios/shorts.** All browser automation runs inside the external skill's venv.
- **Expiry check command** (to be run in Wave 0): `python run.py auth_manager.py status` → if returns "not authenticated", user must run `python run.py auth_manager.py setup` (browser pops open, user signs into Google manually, state persists).

## Area 3: NotebookLM Query Wrapper (scripts/notebooklm/query.py)

### Contract

```python
# scripts/notebooklm/query.py
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_SKILL_PATH = Path(r"C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm")

def query_notebook(
    question: str,                  # single pre-composed Korean string per D-6
    notebook_id: str,               # D-4: explicit notebook id, no fallback to active
    timeout_s: int = 600,
    skill_path: Path | None = None,
) -> str:
    """Return raw NotebookLM answer text (stripped of FOLLOW_UP_REMINDER)."""
    sp = skill_path or Path(os.environ.get("NOTEBOOKLM_SKILL_PATH", DEFAULT_SKILL_PATH))
    if not sp.exists():
        raise FileNotFoundError(f"NotebookLM skill not found at {sp}")
    cmd = [
        sys.executable, str(sp / "scripts" / "run.py"),
        "ask_question.py",
        "--question", question,         # CRITICAL: single argv item, no newlines
        "--notebook-id", notebook_id,
        "--timeout", str(timeout_s),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", timeout=timeout_s + 30)
    if result.returncode != 0:
        raise RuntimeError(f"NotebookLM query failed (rc={result.returncode}): {result.stderr}")
    # Strip the boilerplate FOLLOW_UP_REMINDER
    answer = result.stdout
    marker = "EXTREMELY IMPORTANT: Is that ALL you need"
    if marker in answer:
        answer = answer.split(marker)[0].rstrip()
    return answer
```

### Subprocess Call Pattern

- **Single argv item for --question:** D-6 compliance. Never `echo` the question into stdin; use command-line args.
- **UTF-8 encoding explicit:** Windows cp949 will break on Korean. Follow Phase 5 STATE Decision #28 precedent.
- **Timeout buffer:** subprocess timeout = answer_timeout + 30 seconds to allow browser teardown.
- **Stderr captured:** Shown to caller on failure for diagnostic. Never swallowed.

### Test Seams (Deterministic)

- `monkeypatch.setenv("NOTEBOOKLM_SKILL_PATH", str(fake_skill_dir))` + fake skill with a `run.py` that echoes a canned answer → validates wrapper without real browser.
- `monkeypatch.setattr(query, "subprocess", FakeSubprocess)` to inject failure modes (rc=1, timeout, unicode decode error).

### Korean Query Discipline (D-6 + memory `feedback_notebooklm_query.md`)

- **Pre-compose the entire question as one string before calling.** No interactive building.
- **Use paste-via-clipboard (already done inside ask_question.py line 111 `pyperclip.copy(question)`).** Do not modify this.
- **One question per call.** Never bundle 2+ questions with `and` or newline separators. Follow-ups = separate subprocess calls.

## Area 4: Fallback Chain 3-Tier Implementation

### Interface Contract

```python
class QueryBackend(Protocol):
    def query(self, question: str, notebook_id: str) -> str: ...
    # Must raise on failure (no silent empty returns — hooks into CLAUDE.md Rule 3)

class NotebookLMFallbackChain:
    def __init__(self, backends: list[QueryBackend] | None = None): ...
    def query(self, question: str, notebook_id: str) -> tuple[str, int]:
        """Returns (answer, tier_used). Raises only if all tiers fail."""
```

### Failure Mode Matrix

| Tier | Backend | Fails When | Next Tier Behavior |
|------|---------|-----------|---------------------|
| 0 | RAGBackend (NotebookLM) | subprocess rc≠0, timeout, auth expired, notebook not found | Catch exception, log tier=0 failure to stderr, try GrepWikiBackend |
| 1 | GrepWikiBackend | No markdown files under wiki/ match all keywords | Raise "grep wiki: no hits", try HardcodedDefaultsBackend |
| 2 | HardcodedDefaultsBackend | Never raises (always returns something, even `"fallback defaults unavailable for ..."` string) | If returns the sentinel string, caller decides whether to proceed with degraded input |
| — | All 3 fail | Only if backends list is empty or all raise | `NotebookLMFallbackChain.query` raises `RuntimeError("all NotebookLM fallback tiers exhausted")` |

### Deterministic Test Strategy

```python
# tests/phase06/test_notebooklm_fallback_chain.py
class FakeFailingRAG:
    def query(self, q, nid): raise RuntimeError("simulated Google outage")

class FakeFailingGrep:
    def query(self, q, nid): raise RuntimeError("no wiki hits")

def test_falls_through_to_defaults():
    chain = NotebookLMFallbackChain(backends=[
        FakeFailingRAG(), FakeFailingGrep(), HardcodedDefaultsBackend()
    ])
    answer, tier = chain.query("아무 질문", "naberal-shorts-channel-bible")
    assert tier == 2
    assert "색상" in answer or "lens" in answer

def test_rag_success_short_circuits():
    class FakeRAG:
        def query(self, q, nid): return "real NLM answer"
    chain = NotebookLMFallbackChain(backends=[FakeRAG(), GrepWikiBackend(), HardcodedDefaultsBackend()])
    answer, tier = chain.query("Q", "N")
    assert tier == 0
    assert answer == "real NLM answer"

def test_all_fail_raises():
    class FakeFail:
        def query(self, q, nid): raise RuntimeError("nope")
    chain = NotebookLMFallbackChain(backends=[FakeFail(), FakeFail(), FakeFail()])
    with pytest.raises(RuntimeError, match="exhausted"):
        chain.query("Q", "N")
```

### Fault Injection for Phase 6 Acceptance (D-5)

The acceptance test for D-5 is **"intentional API fail simulation."** Implementation:

```python
def test_real_rag_backend_falls_through_on_auth_failure(monkeypatch):
    """Force subprocess rc=1 and assert tier=1 activates."""
    def fake_run(*a, **kw):
        return subprocess.CompletedProcess(a, returncode=1, stdout="", stderr="not authenticated")
    monkeypatch.setattr(subprocess, "run", fake_run)
    chain = NotebookLMFallbackChain()  # default real chain
    answer, tier = chain.query("한국 시니어 톤", "naberal-shorts-channel-bible")
    assert tier in (1, 2)  # grep might find hits in channel_identity.md, or defaults
```

## Area 5: Continuity Prefix Pydantic Schema + Shotstack Injection

### ContinuityPrefix Model (D-20 — in scripts/orchestrator/api/models.py)

```python
# APPEND to scripts/orchestrator/api/models.py
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]

class ContinuityPrefix(BaseModel):
    """D-20: Continuity Bible prefix schema — consumed by ShotstackAdapter.

    All fields enforce D-10 5-component coverage at parse time so a missing
    component fails before any render attempt.
    """
    model_config = ConfigDict(extra="forbid")

    color_palette: list[HexColor] = Field(min_length=3, max_length=5,
        description="D-10(a): 3-5 HEX color anchors.")
    warmth: Annotated[float, Field(ge=-1.0, le=1.0)] = Field(
        description="D-10(a): -1=cool, +1=warm; Korean senior skew = slightly warm (~+0.2).")
    focal_length_mm: Annotated[int, Field(ge=18, le=85)] = Field(
        description="D-10(b): typically 35 or 50.")
    aperture_f: Annotated[float, Field(ge=1.4, le=16.0)] = Field(
        description="D-10(b): f-stop.")
    visual_style: Literal["photorealistic", "cinematic", "documentary"] = Field(
        description="D-10(c): channel locks exactly one.")
    audience_profile: str = Field(min_length=10,
        description="D-10(d) + D-16: Korean-senior audience descriptor string.")
    bgm_mood: Literal["ambient", "tension", "uplift"] = Field(
        description="D-10(e): 3 presets.")

__all__ += ["ContinuityPrefix", "HexColor"]  # extend existing __all__
```

### JSON Serialization (continuity_bible/prefix.json)

```json
{
  "color_palette": ["#1A2E4A", "#C8A660", "#E4E4E4"],
  "warmth": 0.2,
  "focal_length_mm": 35,
  "aperture_f": 2.8,
  "visual_style": "cinematic",
  "audience_profile": "한국 시니어 50-65세, 채도 낮은 톤 선호, 빠른 정보 전달 기대",
  "bgm_mood": "ambient"
}
```

### Shotstack Injection Contract (D-9)

```python
# scripts/orchestrator/api/shotstack.py (EXTEND)

# Class-level load of continuity preset (lazy from prefix.json)
import json
from pathlib import Path
from .models import ContinuityPrefix

DEFAULT_CONTINUITY_PRESET_PATH = Path("studios/shorts/wiki/continuity_bible/prefix.json")

def _load_continuity_preset() -> ContinuityPrefix | None:
    if not DEFAULT_CONTINUITY_PRESET_PATH.exists():
        return None
    return ContinuityPrefix.model_validate_json(
        DEFAULT_CONTINUITY_PRESET_PATH.read_text(encoding="utf-8")
    )

# In ShotstackAdapter:
def _build_timeline_payload(self, *, serialised_entries, resolution, aspect_ratio, filters_order):
    # D-19: inject continuity_prefix at position 0 if preset loaded
    preset = _load_continuity_preset()
    if preset is not None:
        filters_order = ["continuity_prefix"] + list(filters_order)
    # ... existing code unchanged, but filters_order now starts with prefix
    return {
        "timeline": {
            "background": "#000000",
            "tracks": [{"clips": clips}, {"clips": audio_tracks}],
            "filters": list(filters_order),  # first entry is continuity_prefix
            # D-20 preset params for Shotstack to interpret — new field
            "continuity_preset": preset.model_dump() if preset else None,
        },
        ...
    }
```

### Filter Chain Invariant Preservation (D-17 + D-19)

The critical invariant: **D-17 order `color_grade → saturation → film_grain` must remain contiguous and in that order.** D-9 prepends `continuity_prefix` without disturbing the tail.

Test:
```python
def test_prefix_injection_preserves_d17():
    adapter = ShotstackAdapter(api_key="x")
    monkeypatch.setattr(shotstack, "_load_continuity_preset", lambda: FAKE_PRESET)
    payload = adapter._build_timeline_payload(
        serialised_entries=[{"kind": "clip", "start": 0, "end": 1, "clip_path": "/x", "speed": 1.0, "audio_path": "/a"}],
        resolution="hd", aspect_ratio="9:16",
        filters_order=["color_grade", "saturation", "film_grain"],
    )
    assert payload["timeline"]["filters"] == ["continuity_prefix", "color_grade", "saturation", "film_grain"]
    assert payload["timeline"]["continuity_preset"]["visual_style"] == "cinematic"
```

## Area 6: FAILURES.md Append-Only Hook Enforcement

### Regex Design (for `.claude/deprecated_patterns.json`)

**The CONTEXT sample regex `(?i)^\\s*(#|-|[*])\\s*\\[REMOVED\\]` only catches explicit `[REMOVED]` markers — NOT sufficient.** Real append-only enforcement requires logic beyond a single regex because a regex over `new_string` alone cannot distinguish append from modify. The actual enforcement lives in a Python check hooked into `pre_tool_use.py` (see §Pattern 4 above), and the regex in deprecated_patterns.json is a **supplementary marker**:

```json
{
  "regex": "(?i)\\[REMOVED\\]|\\[DELETED\\]|delete this entry",
  "reason": "FAIL-01/D-11: FAILURES.md 삭제 마커 — append-only 위반"
},
{
  "regex": "SKILL\\.md",
  "reason": "FAIL-03/D-12: SKILL.md 직접 수정 차단 — SKILL_HISTORY 백업 확인 필요 (pre_tool_use.py 로직 참조)"
}
```

(Note: the second regex fires on any SKILL.md touch; the accompanying Python check decides whether to block based on whether `SKILL_HISTORY/<skill>/v*.md.bak` exists for today.)

### Edit Diff Detection Strategy

The Hook receives `tool_input` with:
- `Write` → `content` (whole new file)
- `Edit` → `old_string`, `new_string`
- `MultiEdit` → `edits: [{old_string, new_string}, ...]`

For **Edit/MultiEdit on FAILURES.md**: If `old_string` is non-empty and the file already exists, this is a modification (not an append) → DENY unless the old_string is literally the last line (which would be an "edit the just-added line" case).

For **Write on FAILURES.md**: Read existing file, check `new_content.startswith(existing_content)`. If true → append. If false → DENY.

### False-Positive Mitigation

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Typo fix on entry committed 5 minutes ago | Legitimate but `old_string` matches committed line → blocked | Add escape: if file is unstaged (checked via `git diff --cached --name-only` exclusion), allow one-shot Edit. Or: user manually moves the new entry to a `_drafts/` dir first, finalizes, then appends. |
| Markdown formatter reflows lines | `old_string` fails to match because of whitespace drift | Hook should normalize whitespace before comparison (collapse runs of spaces), not just strict `startswith`. |
| New session starts and Claude writes the full file to "reset" | `new_content` doesn't contain old_content as prefix → blocked (CORRECT) | No mitigation; this is the feature. |
| Entry numbering collision (two sessions add FAIL-X simultaneously) | Git merge conflict, not Hook domain | Standard git workflow handles this; Hook stays in its lane. |
| `_imported_from_shorts_naberal.md` edit attempt | Forbidden by D-14 but appears to Hook like FAILURES.md edit | File name different → Hook path check uses exact filename. Plus: sha256 immutability test asserts hash unchanged after each commit. |

### Tests Required

```python
def test_edit_existing_failures_line_blocked():
    # Simulate Edit with old_string = an existing FAILURES.md line
    payload = {"tool_name": "Edit", "input": {
        "file_path": ".../FAILURES.md",
        "old_string": "### FAIL-001: Evaluator PASS 를 대표님 만족으로 착각",
        "new_string": "### FAIL-001: totally different content"
    }}
    result = run_hook(payload)  # subprocess call to pre_tool_use.py
    assert result["decision"] == "deny"
    assert "append-only" in result["reason"]

def test_append_new_entry_allowed():
    existing = Path(".../FAILURES.md").read_text(encoding="utf-8")
    payload = {"tool_name": "Write", "input": {
        "file_path": ".../FAILURES.md",
        "content": existing + "\n\n### FAIL-NEW: brand new entry\n..."
    }}
    result = run_hook(payload)
    assert result["decision"] == "allow"
```

## Area 7: SKILL_HISTORY Backup Pattern

### Trigger Point — Pre-Tool vs Post-Tool

**Chosen: pre-tool.** Rationale:

| Aspect | Pre-Tool | Post-Tool |
|--------|----------|-----------|
| Captures old version | YES — file still intact when hook fires | NO — file already overwritten |
| Atomicity | Safe — if backup fails, Write is denied | Unsafe — file already changed before failure observed |
| Rollback useful? | YES — you can restore from v{timestamp}.md.bak | NO — backup is of new version, defeats purpose |
| Recovery UX | `cp SKILL_HISTORY/<skill>/v<stamp>.md.bak <skill>/SKILL.md` | N/A |

Decision: **pre-tool hook creates backup, then allows Write.** If backup fails (disk full, permission denied), Hook returns `deny` with reason so user can investigate.

### File Naming Scheme

```
SKILL_HISTORY/<skill_name>/v<YYYYMMDD_HHMMSS>.md.bak
```

Example: `SKILL_HISTORY/harness-audit/v20260419_143000.md.bak`

- Granularity: seconds — ensures no collision within a single session.
- `.bak` extension — distinguishes from live `.md`, excluded by wiki-linter glob, not loaded by Claude as context.

### Restoration UX

```bash
# List backups for a skill
ls SKILL_HISTORY/harness-audit/
# → v20260418_120000.md.bak  v20260419_143000.md.bak  v20260419_150000.md.bak

# Restore specific version
cp SKILL_HISTORY/harness-audit/v20260418_120000.md.bak .claude/skills/harness-audit/SKILL.md

# Or programmatic helper
python scripts/skill_history/restore.py --skill harness-audit --timestamp 20260418_120000
```

The `restore.py` helper is **Phase 9 / deferred** (Phase 6 only ships the backup creation + basic `ls`).

### Tests

```python
def test_backup_created_before_skill_write(tmp_path, monkeypatch):
    skill = tmp_path / ".claude/skills/foo/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("old content")
    # ... invoke hook with Write payload targeting skill ...
    history = tmp_path / "SKILL_HISTORY" / "foo"
    backups = list(history.glob("v*.md.bak"))
    assert len(backups) == 1
    assert backups[0].read_text() == "old content"

def test_no_backup_for_initial_create():
    # First-time SKILL.md creation has no old version; backup should skip, not fail
    ...
```

## Area 8: 30-Day Aggregation Dry-Run CLI

### Input Schema Unification (D-13 — 2-file heterogeneity)

**File 1: `_imported_from_shorts_naberal.md`** (500 lines, Phase 3 schema):
```
### FAIL-NNN: [summary]
- **Tier**: A/B/C/D
- **발생 세션**: YYYY-MM-DD 세션 N
- **재발 횟수**: 1
- **Trigger**: ...
...
```

**File 2: `FAILURES.md`** (NEW, Phase 6+ entries, TBD schema — same schema for consistency).

### Pattern Key Normalization

```python
# scripts/failures/aggregate_patterns.py
import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

ENTRY_RE = re.compile(r"^### (FAIL-[\w]+):\s*(.+?)$", re.MULTILINE)
TRIGGER_RE = re.compile(r"^-\s*\*\*Trigger\*\*:\s*(.+?)$", re.MULTILINE)

def iter_entries(md_path: Path) -> Iterator[dict]:
    text = md_path.read_text(encoding="utf-8")
    # Split on "### FAIL-" sections
    sections = re.split(r"(?=^### FAIL-)", text, flags=re.MULTILINE)
    for sec in sections:
        m = ENTRY_RE.search(sec)
        if not m:
            continue
        fail_id, summary = m.group(1), m.group(2).strip()
        trig_match = TRIGGER_RE.search(sec)
        trigger = trig_match.group(1).strip() if trig_match else ""
        yield {"id": fail_id, "summary": summary, "trigger": trigger, "source": md_path.name}

def normalize_pattern_key(entry: dict) -> str:
    """Compute a stable hash key from (summary + first 80 chars of trigger)."""
    base = f"{entry['summary'].lower().strip()}||{entry['trigger'][:80].lower().strip()}"
    # Strip punctuation, collapse whitespace
    base = re.sub(r"[^\w\s가-힣]", "", base)
    base = re.sub(r"\s+", " ", base).strip()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", action="append", type=Path, required=True,
                   help="Paths to FAILURES files (repeatable).")
    p.add_argument("--threshold", type=int, default=3, help="≥N occurrences triggers candidate.")
    p.add_argument("--dry-run", action="store_true", default=True, help="Phase 6 default: dry-run only.")
    p.add_argument("--output", type=Path, help="JSON output path (stdout if omitted).")
    args = p.parse_args()

    counter: Counter[str] = Counter()
    key_examples: dict[str, list[dict]] = {}
    for f in args.input:
        for entry in iter_entries(f):
            key = normalize_pattern_key(entry)
            counter[key] += 1
            key_examples.setdefault(key, []).append(entry)

    candidates = [
        {"key": k, "count": c, "examples": key_examples[k][:3]}
        for k, c in counter.most_common() if c >= args.threshold
    ]
    report = {"candidates": candidates, "total_entries": sum(counter.values())}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Dry-Run Output Schema

```json
{
  "candidates": [
    {
      "key": "a3f8c12d9e04",
      "count": 3,
      "examples": [
        {"id": "FAIL-011", "summary": "기존 프로젝트 구조 확인 없이 새 폴더/파일 구조 제안", "trigger": "신규 설계 요청 시", "source": "_imported_from_shorts_naberal.md"},
        ...
      ]
    }
  ],
  "total_entries": 15
}
```

### Dry-Run Constraint (D-13)

- **NO `SKILL.md.candidate` FILE IS WRITTEN IN PHASE 6.** The CLI has `--dry-run` as default and emits JSON to stdout.
- The *real* promotion (candidate file creation + 7-day staged rollout state) is Phase 10 per ROADMAP.
- Phase 6 acceptance test: call the CLI with both input files, assert valid JSON, assert at least one candidate exists (the imported 500-line file has recurring `feedback_no_background_publish`, `feedback_quality_first`, etc. — but `_imported_from_shorts_naberal.md` has unique FAIL-IDs per entry so recurrence is 1 unless the summary normalizes to the same key across entries → assert the CLI runs without error and outputs valid JSON regardless of candidates count).

### Hash Collision Risk

- 12-hex-char prefix of sha256 = 48 bits. Birthday collision at √(2^48) ≈ 16M entries. Far beyond Phase 10 volume. SAFE.
- If volume grows: extend to 16 chars (64 bits, 4B entries).

## Area 9: 32 Phase 4 Agent Prompt Mass Update

### Current Surface (grep-audited 2026-04-19)

**15 of 32 agent files contain `Phase 6` placeholders:**
```
.claude/agents/inspectors/content/ins-factcheck/AGENT.md
.claude/agents/inspectors/content/ins-korean-naturalness/AGENT.md
.claude/agents/inspectors/content/ins-narrative-quality/AGENT.md
.claude/agents/inspectors/style/ins-thumbnail-hook/AGENT.md
.claude/agents/inspectors/technical/ins-audio-quality/AGENT.md
.claude/agents/inspectors/technical/ins-render-integrity/AGENT.md
.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md
.claude/agents/producers/director/AGENT.md
.claude/agents/producers/metadata-seo/AGENT.md
.claude/agents/producers/niche-classifier/AGENT.md
.claude/agents/producers/researcher/AGENT.md
.claude/agents/producers/scene-planner/AGENT.md
.claude/agents/producers/scripter/AGENT.md
.claude/agents/producers/shot-planner/AGENT.md
.claude/agents/producers/trend-collector/AGENT.md
```

**Typical placeholder patterns observed:**
- `` `wiki/continuity_bible/MOC.md` — Continuity Bible (Phase 6 채움). ``
- `` **채널 일관성** — Phase 6 Continuity Bible에서 정의될 색상 팔레트와 thumbnail 팔레트가 일치하는지 확인. ``
- `` Phase 6 Continuity Bible 임시 proxy ``
- `` (Phase 6 wiring) ``
- `` --asset-catalog | ... | no (Phase 6) | Phase 6 wiring ``

### Update Pattern (D-3 + D-18)

Replace references like:
```
- `wiki/continuity_bible/MOC.md` — Continuity Bible (Phase 6 채움).
```
With:
```
- `@wiki/shorts/continuity_bible/channel_identity.md` — Continuity Bible 5 구성요소 (D-10).
```

For narrative phrases like `(Phase 6 채움)`:
- Remove the parenthetical or replace with `(ready, D-17 frontmatter)`.

### Byte-Level Diff Verification Strategy

1. **Before update:** `sha256sum .claude/agents/**/AGENT.md` → save to `phase06_agents_before.txt`.
2. **Apply updates:** One plan per category (inspector-content, inspector-style, inspector-technical, producer-split3, producer-support, etc.) with explicit Edit operations.
3. **After update:** `sha256sum` again → `phase06_agents_after.txt`.
4. **Verification:** Only the 15 files should have non-zero diff. The other 17 of 32 must be byte-identical.
5. **Prompt length delta recorded** per D-18 final paragraph: `wc -c` before/after each edited file, tabulated in `phase06_agent_prompt_delta.md`.

### Safety Strategy (grep+sed equivalent in MultiEdit form)

- **NO `sed -i`** on Windows — cp949 byte-corruption risk. Use Claude's MultiEdit tool per file.
- One MultiEdit per file is the unit of work. Each edit has `old_string` = exact existing line, `new_string` = replacement. Claude's MultiEdit enforces uniqueness of old_string within file.
- **Never use global-replace across all 15 files in one command.** One file at a time, with explicit before/after line.
- Post-update, run `scripts/wiki/link_validator.py` to ensure every `@wiki/shorts/xxx.md` reference resolves to a real file with `status: ready`.

### Tests

```python
def test_agent_prompts_reference_real_wiki_nodes():
    """Every @wiki/shorts/xxx.md reference resolves to a ready node."""
    REF_RE = re.compile(r"@wiki/shorts/([\w_/]+\.md)")
    wiki_root = Path("studios/shorts/wiki")
    missing: list[tuple[Path, str]] = []
    for agent in Path(".claude/agents").rglob("AGENT.md"):
        for m in REF_RE.finditer(agent.read_text(encoding="utf-8")):
            ref = wiki_root / m.group(1)
            if not ref.exists():
                missing.append((agent, m.group(0)))
                continue
            fm = parse_frontmatter(ref)
            if fm.get("status") != "ready":
                missing.append((agent, m.group(0) + " (status!=ready)"))
    assert not missing, f"Broken refs: {missing}"

def test_no_phase6_placeholders_remain():
    leftover = []
    for agent in Path(".claude/agents").rglob("AGENT.md"):
        text = agent.read_text(encoding="utf-8")
        if "Phase 6 채움" in text or "Phase 6 wiring" in text or "Phase 6에서 정의" in text:
            leftover.append(agent)
    assert not leftover, f"Still has Phase 6 placeholders: {leftover}"
```

## Area 10: Phase 3 Immutability Preservation

### Target File — `_imported_from_shorts_naberal.md`

- Phase 3 path: `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
- Phase 3-recorded sha256 (embedded in file header line 9): `978bb9381fee4e879c99915277a45778091b06f997b6c7355a155a5169ae1559` — this hash is of the **original content block only** (the upstream orchestrator.md).
- Full-file sha256 (including the Phase 3-added header preamble): `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa` (verified 2026-04-19 via `python -c "import hashlib; print(hashlib.sha256(open(...,'rb').read()).hexdigest())"`).
- Line count: 500 (verified).

### D-14 Invariant

No Phase 6 plan may touch this file. All FAILURES-related writes go to the new `FAILURES.md` sibling. If structural tagging is needed (e.g., category index), use a separate `FAILURES_INDEX.md` that *references* entries in `_imported_from_shorts_naberal.md` by fail-ID but never modifies it.

### Verification Approach

Add to `tests/phase06/test_immutable_imported_failures.py`:

```python
def test_imported_failures_sha256_unchanged():
    """D-14: _imported_from_shorts_naberal.md MUST remain byte-for-byte identical."""
    import hashlib
    p = Path("studios/shorts/.claude/failures/_imported_from_shorts_naberal.md")
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    expected = "a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa"
    assert actual == expected, (
        f"D-14 VIOLATION: _imported_from_shorts_naberal.md modified.\n"
        f"  Expected sha256: {expected}\n"
        f"  Actual sha256:   {actual}\n"
        f"  This file is Phase 3 immutable. Restore from git: "
        f"git checkout HEAD -- {p}"
    )

def test_imported_failures_line_count_500():
    p = Path("studios/shorts/.claude/failures/_imported_from_shorts_naberal.md")
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 500, f"D-14: line count changed from 500 to {len(lines)}"
```

### Lifecycle

- **Wave 0 pre-flight:** Run this test. If fails, STOP Phase 6 — something has modified the file since Phase 3.
- **Wave 5 post-flight:** Run this test again as the last gate before VALIDATION.md flip. Identical hash confirms immutability preserved across entire Phase 6 lifecycle.
- **Commit trail:** `git log --follow studios/shorts/.claude/failures/_imported_from_shorts_naberal.md` should show exactly ONE commit (Phase 3 ad98b32 + 1ff5768). Any additional commit = D-14 violation.

## Area 11: Korean Market Context Propagation

### Where Korean Senior / KOMCA / Typecast Context Lives (D-16)

Three landing sites, each with a different consumer:

| Site | Medium | Consumer | Content |
|------|--------|----------|---------|
| 1. wiki node `continuity_bible/channel_identity.md` | prose + JSON | humans + NotebookLM upload | Descriptive paragraph: "한국 시니어 50-65세, 채도 낮은 톤 선호..." |
| 2. `continuity_bible/prefix.json` `audience_profile` field | JSON string | Shotstack adapter + pydantic validation | Same descriptor, machine-consumable |
| 3. NotebookLM channel-bible notebook | uploaded source | RAG query answer grounding | The wiki/continuity_bible/ files, uploaded at notebook creation |
| 4. Agent prompts (via `@wiki/shorts/...` refs) | text | Claude subagents | Implicit — agents read the wiki ref on-demand |

### Propagation Rule

- **Single source of truth:** The wiki node. Every other site MUST derive from it (either by file read, JSON parse, or NotebookLM upload-at-creation).
- **Never hardcode Korean-senior details into agent prompts directly.** Reference the wiki node. If the channel pivots to a different audience, one wiki edit updates everywhere.
- **KOMCA/Typecast details stay in their existing homes** — `ins-license/AGENT.md` has the K-pop blocklist (AF-13 — Phase 4 Plan 05), `voice-producer/AGENT.md` has Typecast as primary (AUDIO-01 — Phase 4 Plan 09). Phase 6 does not duplicate them into continuity_bible.

### 3초 Hook / 질문형 제목 / 존댓말-반말 Switching

These live in:
- `kpi/retention_3second_hook.md` (NEW Phase 6) — measurement + target values
- `ins-narrative-quality/AGENT.md` (Phase 4) — already encodes the 3초 hook LogicQA + question-form regex (CONTENT-01)
- `ins-korean-naturalness/AGENT.md` (Phase 4) — already encodes 존댓말/반말 detection regex (SUBT-02)

Phase 6 does NOT re-implement these. It only adds the wiki node that agents can reference for deeper context when their rubric triggers.

## Area 12: Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (Phase 5 precedent) |
| Config file | `pytest.ini` (reuse Phase 5) — if absent, create at `tests/phase06/conftest.py` sys.path hook |
| Quick run command | `pytest tests/phase06/ -q -x` |
| Full suite command | `pytest tests/phase05/ tests/phase06/ -q` (regression + Phase 6) |
| Phase-gate command | `pytest tests/ -q` (all phases) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIKI-01 | 5 wiki categories have ≥1 `status: ready` node each | unit | `pytest tests/phase06/test_wiki_frontmatter.py::test_all_categories_have_ready_node -x` | ❌ Wave 0 |
| WIKI-01 | Every wiki node has valid D-17 frontmatter | unit | `pytest tests/phase06/test_wiki_frontmatter.py::test_frontmatter_schema_all_nodes -x` | ❌ Wave 0 |
| WIKI-02 | ContinuityPrefix model validates channel_identity values | unit | `pytest tests/phase06/test_continuity_prefix_schema.py -x` | ❌ Wave 0 |
| WIKI-02 | Shotstack adapter injects continuity_prefix at filters_order[0] | unit | `pytest tests/phase06/test_shotstack_filter_order.py::test_prefix_injection_preserves_d17 -x` | ❌ Wave 0 |
| WIKI-03 | library.json contains both notebook ids | unit | `pytest tests/phase06/test_notebooklm_library.py::test_both_notebooks_registered -x` | ❌ Wave 0 |
| WIKI-03 | NotebookLM wrapper subprocess call shape matches run.py contract | unit | `pytest tests/phase06/test_notebooklm_query_wrapper.py -x` | ❌ Wave 0 |
| WIKI-04 | Fallback Chain tier 0 fail → tier 1 → tier 2 in order | unit | `pytest tests/phase06/test_notebooklm_fallback_chain.py -x` | ❌ Wave 0 |
| WIKI-05 | Every `@wiki/shorts/...` ref in agent prompts resolves to `status: ready` node | unit | `pytest tests/phase06/test_agent_prompt_references.py::test_all_refs_resolve -x` | ❌ Wave 0 |
| WIKI-05 | No agent prompt contains "Phase 6 채움" placeholder after update | unit | `pytest tests/phase06/test_agent_prompt_references.py::test_no_phase6_placeholders_remain -x` | ❌ Wave 0 |
| WIKI-06 | Every SKILL.md has ≤500 lines (measurement only, violations → deferred-items.md) | unit | `pytest tests/phase06/test_skill_line_count.py -x` | ❌ Wave 0 |
| FAIL-01 | Hook blocks Edit on FAILURES.md with non-empty old_string | integration (subprocess) | `pytest tests/phase06/test_failures_append_only_hook.py::test_edit_existing_line_blocked -x` | ❌ Wave 0 |
| FAIL-01 | Hook allows Write on FAILURES.md when new content is strict append | integration (subprocess) | `pytest tests/phase06/test_failures_append_only_hook.py::test_append_allowed -x` | ❌ Wave 0 |
| FAIL-01 | `_imported_from_shorts_naberal.md` sha256 unchanged across Phase 6 | unit | `pytest tests/phase06/test_immutable_imported_failures.py -x` | ❌ Wave 0 |
| FAIL-02 | aggregate_patterns.py --dry-run emits valid JSON with candidates list | unit | `pytest tests/phase06/test_aggregate_patterns_dry_run.py -x` | ❌ Wave 0 |
| FAIL-02 | aggregate_patterns.py threshold flag filters <3 occurrence entries | unit | `pytest tests/phase06/test_aggregate_patterns_dry_run.py::test_threshold_3 -x` | ❌ Wave 0 |
| FAIL-03 | Hook creates SKILL_HISTORY backup before SKILL.md Write | integration | `pytest tests/phase06/test_skill_history_backup.py -x` | ❌ Wave 0 |
| FAIL-03 | SKILL_HISTORY backup file name matches `v<YYYYMMDD_HHMMSS>.md.bak` | unit | `pytest tests/phase06/test_skill_history_backup.py::test_filename_format -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/phase06/ -q -x` (≤30 seconds expected)
- **Per wave merge:** `pytest tests/phase05/ tests/phase06/ -q` (full regression sweep)
- **Phase gate:** `pytest tests/ -q` — full repo suite green before `/gsd:verify-work 06`

### Wave 0 Gaps

- [ ] `tests/phase06/conftest.py` — shared fixtures (tmp_path_factory for wiki sandbox, monkeypatch NOTEBOOKLM_SKILL_PATH, fake subprocess runner)
- [ ] `tests/phase06/test_wiki_frontmatter.py` — WIKI-01
- [ ] `tests/phase06/test_continuity_prefix_schema.py` — WIKI-02 data model
- [ ] `tests/phase06/test_shotstack_filter_order.py` — WIKI-02 injection
- [ ] `tests/phase06/test_notebooklm_library.py` — WIKI-03 registry
- [ ] `tests/phase06/test_notebooklm_query_wrapper.py` — WIKI-03 wrapper
- [ ] `tests/phase06/test_notebooklm_fallback_chain.py` — WIKI-04
- [ ] `tests/phase06/test_agent_prompt_references.py` — WIKI-05 + D-18 byte-diff
- [ ] `tests/phase06/test_skill_line_count.py` — WIKI-06 audit
- [ ] `tests/phase06/test_failures_append_only_hook.py` — FAIL-01 (subprocess mode)
- [ ] `tests/phase06/test_immutable_imported_failures.py` — D-14 immutability
- [ ] `tests/phase06/test_aggregate_patterns_dry_run.py` — FAIL-02
- [ ] `tests/phase06/test_skill_history_backup.py` — FAIL-03

Framework install: **none** — pytest 8.4.2 already present.

## Common Pitfalls

### Pitfall 1: Duplicating the notebooklm skill
**What goes wrong:** Developer copies `shorts_naberal/.claude/skills/notebooklm/` into `studios/shorts/.claude/skills/` to "get local control."
**Why it happens:** Subprocess invocation feels fragile ("what if the path breaks?"), so duplication feels safer.
**How to avoid:** D-7 is explicit. Env var `NOTEBOOKLM_SKILL_PATH` covers portability. Test the wrapper, not the skill internals.
**Warning signs:** A new `.venv/` appears under studios/shorts. `playwright install` is run a second time. Two `browser_state/` directories exist.

### Pitfall 2: NotebookLM auth expiry silent fallback
**What goes wrong:** Tier 1 RAG fails silently (auth expired), Tier 2 grep returns partial match, agent proceeds with degraded input without knowing why.
**Why it happens:** Fallback chains eat exceptions. The caller has no way to know which tier answered.
**How to avoid:** `NotebookLMFallbackChain.query` returns `(answer, tier_used)`. Agents log tier. Alert when tier != 0 for production queries. Log to FAILURES.md if auth expires (ironic append to the thing we just built).
**Warning signs:** `tier_used` never equals 0 in production logs. All answers look suspiciously short or generic.

### Pitfall 3: Hook false-positive on legitimate typo fix in FAILURES.md
**What goes wrong:** User adds FAIL-099 entry, notices typo 30 seconds later, tries Edit → blocked by Hook → frustration → disables Hook → future deletion gets through.
**Why it happens:** Append-only regime is strict; typo-fix is indistinguishable from malicious deletion without context.
**How to avoid:** Provide an explicit escape: a `_drafts/` dir for entries-in-progress. User writes the draft, reviews, then moves to FAILURES.md (append). Alternatively: allow Edit if `git status` shows FAILURES.md is unstaged AND `old_string` matches the last N lines (recent addition).
**Warning signs:** User complaints about "the hook blocks legitimate edits." Hook bypass commits in git log.

### Pitfall 4: Filter order violation in Shotstack
**What goes wrong:** Someone re-arranges filters_order to `["color_grade", "continuity_prefix", ...]` thinking "color grade first is logical."
**Why it happens:** Without D-19 as a tested invariant, the ordering is aesthetic.
**How to avoid:** `test_prefix_injection_preserves_d17` asserts exact list equality `["continuity_prefix", "color_grade", "saturation", "film_grain"]`. Fail-fast on reordering.
**Warning signs:** Test file changed in same PR as shotstack.py — review harder.

### Pitfall 5: prefix.json out of sync with ContinuityPrefix schema
**What goes wrong:** Developer updates `prefix.json` adding a new field; pydantic validation (with `extra="forbid"`) rejects it at load time; every render fails.
**Why it happens:** JSON and Python schema drift independently.
**How to avoid:** `test_continuity_prefix_schema::test_prefix_json_validates` loads the actual `prefix.json` through the model on every CI run. Any schema drift surfaces immediately.
**Warning signs:** `ValidationError: Extra inputs are not permitted` in render logs.

### Pitfall 6: 30-day aggregation promotes a candidate accidentally
**What goes wrong:** Developer removes `--dry-run` flag, CLI writes `SKILL.md.candidate`, triggering a 7-day rollout that Phase 6 was not supposed to activate.
**Why it happens:** CLI defaults can be overridden; `--dry-run=False` is a flag.
**How to avoid:** Make dry-run the ONLY mode in Phase 6; move the real promotion logic into a separate script `aggregate_patterns_promote.py` that doesn't exist until Phase 10.
**Warning signs:** A `SKILL.md.candidate` file appears in git status during Phase 6.

### Pitfall 7: Agent prompt references to `status: stub` wiki nodes
**What goes wrong:** Developer adds a wiki node with `status: stub` (WIP) and references it in an agent prompt before promoting to `status: ready`.
**Why it happens:** D-17 enforcement is only at agent-reference time, not at node-write time.
**How to avoid:** `test_all_refs_resolve` checks both existence AND `status: ready`. FAIL unless both.
**Warning signs:** Agent gives confused answers because WIP content differs from expected.

### Pitfall 8: Channel-bible notebook created but not queried
**What goes wrong:** library.json entry is added, but no validation query is run. Auth may be broken, URL may be wrong — not discovered until Phase 7.
**Why it happens:** "Registration success" ≠ "query success".
**How to avoid:** D-8 acceptance requires "최소 1회 query 검증". Plan includes a Wave 2 step that runs a canary query and asserts the answer mentions "continuity" or "color palette."
**Warning signs:** library.json has `use_count: 0` after Phase 6 VALIDATION.

### Pitfall 9: 15-file agent edit explosion
**What goes wrong:** Mass-update of 15 files in one commit creates a 300+ line diff that obscures which change broke downstream tests.
**Why it happens:** Efficiency pressure to "do it all at once."
**How to avoid:** Split agent updates into multiple plans by category (e.g., 3 inspector plans + 2 producer plans), one commit per plan. Each plan has its own test gate.
**Warning signs:** A single commit touches 15 AGENT.md files. Git blame becomes unusable.

### Pitfall 10: continuity_prefix JSON path hardcoded to Windows-style slashes
**What goes wrong:** `DEFAULT_CONTINUITY_PRESET_PATH = Path("studios\\shorts\\...")` breaks on Unix CI.
**Why it happens:** Windows-first development.
**How to avoid:** Always use forward slashes in `Path("...")` — pathlib normalizes per-OS. Or use relative Path with `__file__` anchoring.
**Warning signs:** CI green on Windows, red on Linux.

## Code Examples

### Example 1: Wiki Node — continuity_bible/channel_identity.md
```markdown
---
category: continuity_bible
status: ready
tags: [continuity, channel-identity, korean-seniors]
updated: 2026-04-19
source_notebook: naberal-shorts-channel-bible
---

# Channel Identity — Continuity Bible

## 5 구성요소 (D-10)

### (a) 색상 팔레트
- Navy: `#1A2E4A`
- Gold: `#C8A660`
- Light: `#E4E4E4`
- Warmth: +0.2 (slightly warm, Korean senior preference)

### (b) 카메라 렌즈
- 초점거리: 35mm
- Aperture: f/2.8

### (c) 시각적 스타일
- `cinematic` (locked — no switching per video)

### (d) 한국 시니어 시청자 특성
- 50-65세 주시청층
- 채도 낮은 톤 선호
- 빠른 정보 전달 기대 (3초 내 hook)
- 존댓말 narration 원칙, 캐릭터 대사 예외

### (e) BGM 분위기
- Default: `ambient`
- Tension: used only for hook 3초 구간
- Uplift: used only for 결론/CTA 구간

## Related
- [[../algorithm/ranking_factors]] — hook 효과 측정
- [[../kpi/retention_3second_hook]] — retention 목표
- [[MOC]]
```

### Example 2: Agent Prompt Update Diff (ins-thumbnail-hook)
```diff
 ## 평가 축
 - **3초 hook** — 썸네일 자체가 3초 영상 hook 기능 수행 (질문형/숫자/고유명사).
-- **채널 일관성** — Phase 6 Continuity Bible에서 정의될 색상 팔레트와 thumbnail 팔레트가 일치하는지 확인.
+- **채널 일관성** — `@wiki/shorts/continuity_bible/channel_identity.md` 색상 팔레트와 thumbnail 팔레트 일치 검증 (D-10).
```

### Example 3: 30-Day Aggregation Dry-Run Output
```bash
$ python scripts/failures/aggregate_patterns.py \
    --input .claude/failures/_imported_from_shorts_naberal.md \
    --input .claude/failures/FAILURES.md \
    --threshold 3 --dry-run

{
  "candidates": [],
  "total_entries": 15
}
```
(Initially 0 candidates — makes sense; the 500-line imported file has distinct FAIL-IDs, and FAILURES.md is empty at Phase 6 launch. The test merely asserts the CLI runs, emits valid JSON, and respects threshold.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded BEGIN/END comment markers in a single FAILURES.md | Separate `_imported_from_shorts_naberal.md` (immutable) + `FAILURES.md` (append-only) + `FAILURES_INDEX.md` (derivative) | D-14 + D-11 | Clear ownership boundaries; impossible to accidentally rewrite Phase 3 archive |
| NotebookLM skill as sole RAG source | 3-tier Fallback Chain (RAG → grep → hardcoded) | D-5 + 2025 Google outage context | Pipeline survives Google outage; 3-tier fallback is FAANG-pattern SRE |
| Global `continuity_prefix` in agent prompts | Model-validated JSON in `prefix.json` + pydantic v2 schema | D-20 | Single source of truth; schema drift fails at parse time not render time |
| `sed`-based mass agent prompt rewrite | Per-file MultiEdit with byte-diff verification | D-18 + Windows cp949 experience | No silent encoding corruption; auditable diffs |

**Deprecated/outdated:**
- ~~RAG-only query~~: Phase 6 mandates fallback chain (WIKI-04).
- ~~Monolithic FAILURES.md with inline editing~~: Phase 6 forbids modification of imported content (D-14).
- ~~SKILL.md direct edit without backup~~: Phase 6 Hook creates SKILL_HISTORY entry before write (D-12).

## Open Questions

1. **NotebookLM channel-bible notebook URL**
   - What we know: Creation requires 대표님 manual action in Google console.
   - What's unclear: Timing — does the user create it before Wave 2 or during?
   - Recommendation: Planner includes an explicit "blocking task — request URL from 대표님" as Wave 2 first step. If not received in 24h, proceed with placeholder `TBD-url-await-user` and append to deferred-items.md.

2. **FAILURES.md entry schema finalization**
   - What we know: The imported 500-line file uses a specific schema (FAIL-NNN / Tier / 발생 세션 / 재발 횟수 / Trigger / 무엇 / 왜 / 정답 / 검증 / 상태 / 관련).
   - What's unclear: Should FAILURES.md use exactly the same schema or add Phase-6-specific fields (e.g., session_id, gate_name)?
   - Recommendation: Use the SAME schema. Consistency beats Phase-specific enrichment. Phase 10's aggregation CLI handles either schema via the `trigger` field normalization.

3. **Hook false-positive escape hatch**
   - What we know: Strict append-only will frustrate users on typo-fix scenarios.
   - What's unclear: How to permit "edit the just-added line" without opening the door to arbitrary edits.
   - Recommendation: Phase 6 ships strict enforcement. Phase 9 (docs + taste gate) adds the `_drafts/FAILURES_draft.md` convention based on user feedback. Log any Hook-blocked legitimate edit as a Phase 9 input.

4. **NotebookLM query cost budget**
   - What we know: Google free tier = 50 queries/day/account.
   - What's unclear: How many queries will production pipeline issue per week? Phase 6 pipeline runs dry (no production queries), but Phase 7+ E2E will hit this limit.
   - Recommendation: Phase 6 logs every NotebookLM call with timestamp; Phase 9 KPI dashboard adds a "queries/day" metric. If production projections exceed 40/day, switch the channel-bible notebook to a different Google account.

5. **Does wiki content get uploaded to NotebookLM or only referenced?**
   - What we know: The channel-bible notebook needs source material.
   - What's unclear: Does NotebookLM auto-ingest from the agent's file reads, or does the user upload explicitly?
   - Recommendation: Explicit upload of 5 `status: ready` wiki nodes at notebook creation time. NotebookLM does not crawl filesystems. User drags the 5 files into the Google NotebookLM UI OR we use the notebooklm skill's upload wrapper (check if `notebook_manager.py add` accepts `--sources` — per SKILL.md it does not; sources are uploaded manually in Google UI).

6. **ContinuityPrefix field — should `audience_profile` be structured or free-text?**
   - What we know: D-20 declares `audience_profile: str`. D-10 says "한국 시니어 시청자 특성 (채도 낮은 톤·깔끔한 구도)".
   - What's unclear: Does Shotstack or any adapter actually parse this string or just pass it through?
   - Recommendation: Keep as free-text string for Phase 6. Shotstack doesn't interpret it; its purpose is to surface in NotebookLM RAG answers. Phase 9+ can split into structured sub-fields if agents need parsing.

## Suggested Plan Decomposition (9 plans across 5 waves)

### Wave 0 — Foundation (parallel where possible)
- **06-01-PLAN: Frontmatter parser + wiki lint framework** — `scripts/wiki/frontmatter.py` + `scripts/wiki/link_validator.py` + `tests/phase06/conftest.py` + `test_wiki_frontmatter.py`. Seeds Wave 1 wiki authoring. [WIKI-01, WIKI-06]

### Wave 1 — Wiki Content (fully parallel — 5 plans can run simultaneously)
- **06-02-PLAN: 5 Ready Nodes (single plan, 5 files)** — Author `algorithm/ranking_factors.md`, `ypp/entry_conditions.md`, `render/remotion_kling_stack.md`, `kpi/retention_3second_hook.md`, `continuity_bible/channel_identity.md` + `prefix.json`. All pass frontmatter lint. [WIKI-01, WIKI-02 content]

### Wave 2 — NotebookLM Integration (sequential — each step depends on previous)
- **06-03-PLAN: NotebookLM wrapper** — `scripts/notebooklm/query.py` + `test_notebooklm_query_wrapper.py`. Subprocess call to external skill's `run.py`. Env var portability. [WIKI-03]
- **06-04-PLAN: library.json channel-bible extension + 1 canary query** — Append new entry; run 1 sanity query and assert source-grounded answer. Creates deferred-item if URL blocked. [WIKI-03, D-8]
- **06-05-PLAN: 3-tier Fallback Chain** — `scripts/notebooklm/fallback.py` + fault-injection tests (`test_notebooklm_fallback_chain.py`). [WIKI-04]

### Wave 3 — Continuity Prefix Injection (sequential within wave — model first, then adapter)
- **06-06-PLAN: ContinuityPrefix model + prefix.json** — Extend `scripts/orchestrator/api/models.py` with `ContinuityPrefix` + `HexColor` alias. Write `continuity_bible/prefix.json`. Test `test_continuity_prefix_schema.py`. [WIKI-02, D-20]
- **06-07-PLAN: Shotstack adapter injection** — Extend `scripts/orchestrator/api/shotstack.py` with `_load_continuity_preset()` + `_build_timeline_payload` prefix insertion. Test `test_shotstack_filter_order.py` — D-17/D-19 invariant. [WIKI-02, D-9, D-19]

### Wave 4 — Hook Extension + FAILURES CLI + Agent Prompt Updates (parallel — 3 plans)
- **06-08-PLAN: Hook extension + SKILL_HISTORY backup + 2 regex entries** — Extend `.claude/hooks/pre_tool_use.py` with `check_failures_append_only` + `backup_skill_before_write`. Append 2 entries to `.claude/deprecated_patterns.json`. Tests via subprocess pattern (`test_failures_append_only_hook.py` + `test_skill_history_backup.py` + `test_immutable_imported_failures.py`). [FAIL-01, FAIL-03, D-11, D-12, D-14]
- **06-09-PLAN: 30-day aggregate_patterns dry-run CLI** — `scripts/failures/aggregate_patterns.py` + test `test_aggregate_patterns_dry_run.py`. Pattern hash normalization + threshold gate. Dry-run only (no candidate files). [FAIL-02, D-13]
- **06-10-PLAN: 15-agent prompt mass update** — MultiEdit per file, one commit per ≤5 files. sha256 before/after manifest. Test `test_agent_prompt_references.py` (resolve + no-placeholder). Length delta documented. [WIKI-05, D-3, D-18]

### Wave 5 — Phase Gate
- **06-11-PLAN: FINAL VERIFICATION + VALIDATION.md flip** — Full regression pytest run (phase05 + phase06). 9/9 REQ traceability matrix → `06-TRACEABILITY.md`. `06-VALIDATION.md` frontmatter flip (status=complete, nyquist_compliant=true, wave_0_complete=true). sha256 immutability post-check. Update `WIKI-06` audit result file. [Phase gate — all 9 REQs]

### Dependency Graph
```
06-01 ──┬─> 06-02 ─────┬────────────────────┐
        │              │                    │
        └─> 06-06 ─> 06-07 (needs prefix.json from 06-02)
        │                                   │
        ├─> 06-03 ─> 06-04 ─> 06-05         │
        │                                   │
        ├─> 06-08 (independent)             │
        │                                   │
        ├─> 06-09 (independent)             │
        │                                   │
        └─> 06-10 (needs 06-02 ready nodes) │
                                            │
                                    06-11 <─┘ (needs all)
```

## Requirement Coverage Matrix

| REQ | Plan(s) | Wave | Artifact(s) |
|-----|---------|------|-------------|
| WIKI-01 | 06-01, 06-02 | 0, 1 | `scripts/wiki/frontmatter.py`, 5 wiki nodes with `status: ready` |
| WIKI-02 | 06-06, 06-07 | 3 | `ContinuityPrefix` model, `prefix.json`, `shotstack.py` injection |
| WIKI-03 | 06-03, 06-04 | 2 | `scripts/notebooklm/query.py`, library.json append, 1 canary query |
| WIKI-04 | 06-05 | 2 | `scripts/notebooklm/fallback.py` 3-tier, fault-injection tests |
| WIKI-05 | 06-10 | 4 | 15 AGENT.md files updated, `@wiki/shorts/...` refs resolved + tested |
| WIKI-06 | 06-01, 06-11 | 0, 5 | SKILL ≤500 line audit + deferred-items.md entries for violations |
| FAIL-01 | 06-08 | 4 | Hook `check_failures_append_only`, 2 deprecated_patterns entries, subprocess test |
| FAIL-02 | 06-09 | 4 | `scripts/failures/aggregate_patterns.py` CLI, dry-run JSON schema test |
| FAIL-03 | 06-08 | 4 | Hook `backup_skill_before_write`, `SKILL_HISTORY/` directory, backup test |
| D-14 immutability | 06-08, 06-11 | 4, 5 | `test_immutable_imported_failures.py` sha256 verify (Wave 0 + Wave 5) |
| D-18 agent prompts | 06-10 | 4 | 15 files edited, sha256 manifest before/after, length delta table |

## Sources

### Primary (HIGH confidence)
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-CONTEXT.md` — 20 locked decisions D-1~D-20 verbatim.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/REQUIREMENTS.md` §WIKI + §FAIL — 9 REQ contracts.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.planning/ROADMAP.md` §Phase 6 — 6 Success Criteria.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/shotstack.py` — existing adapter, filter_order seam at line 61 + `_build_timeline_payload` at line 248.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/scripts/orchestrator/api/models.py` — existing pydantic v2 patterns, `__all__` extensibility.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/deprecated_patterns.json` — 6 existing regexes, extension point.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/hooks/pre_tool_use.py` — 222 lines, entry point `main()` line 153, extension via `check_content` and new helpers.
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/SKILL.md` — skill interface contract, `run.py` wrapper mandate.
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/scripts/run.py` — 102 lines, venv auto-setup, subprocess invocation pattern.
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/scripts/ask_question.py` — 272 lines, argparse CLI, pyperclip paste pattern, FOLLOW_UP_REMINDER handling.
- `C:/Users/PC/Desktop/shorts_naberal/.claude/skills/notebooklm/data/library.json` — 2-notebook current state, append schema.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/wiki/*/MOC.md` (5 files) — frontmatter precedent, Planned Nodes checkboxes.

### Secondary (MEDIUM confidence — verified against primary)
- Phase 5 RESEARCH.md — Validation Architecture pattern precedent.
- Phase 5 CONTEXT.md — D-17 filter order locked in Phase 5.
- `C:/Users/PC/Desktop/naberal_group/studios/shorts/.claude/agents/**/AGENT.md` — 15 files grep'd for Phase 6 placeholders (2026-04-19).
- Memory `feedback_notebooklm_query.md` — single-string discipline.
- Memory `feedback_yolo_no_questions.md` — YOLO mode orchestrator-direct authoring precedent.
- Phase 5 STATE decisions #28, #45, #48, #53 — Windows UTF-8 encoding precedent, graphlib patterns, byte-identical-preserve precedent.

### Tertiary (verified via file-content comparison — HIGH)
- sha256 of `_imported_from_shorts_naberal.md` (full file): `a1d92cc1c367f238547c2a743f81fa26adabe466bffdd6b2e285c28c6e2ab0aa` (verified locally 2026-04-19).
- Phase 5 329/329 pytest PASS baseline (per STATE.md line 18).

## Metadata

**Confidence breakdown:**
- Wiki node authoring: **HIGH** — schema pre-declared in D-17, MOC scaffolds in place, validator is 20 lines of stdlib.
- NotebookLM integration: **MEDIUM-HIGH** — wrapper contract from external skill is well-defined; auth expiry and channel-bible URL acquisition are the only real unknowns.
- Fallback chain: **HIGH** — Protocol interface + 3 concrete backends + fault injection is standard SRE pattern.
- ContinuityPrefix + Shotstack injection: **HIGH** — pydantic v2 already in stack, shotstack adapter seam is clean, D-19 test assertion is trivial.
- FAILURES append-only Hook: **MEDIUM** — regex-only approach is insufficient (documented); Python-based check in Hook adds ~50 lines that need subprocess testing.
- SKILL_HISTORY backup: **HIGH** — pre-tool trigger + shutil.copy2 is straightforward; only edge case is first-time create (handled).
- 30-day aggregation dry-run: **HIGH** — stdlib Counter + hashlib + argparse; dry-run constraint is a Python flag default.
- 32 agent prompt mass update: **MEDIUM-HIGH** — 15 files surface-audited; per-file MultiEdit keeps diffs auditable. Risk: placeholder patterns vary more than expected (mitigated by per-file strategy).
- Phase 3 immutability preservation: **HIGH** — sha256 test, 500-line count test, both deterministic.
- Korean market propagation: **HIGH** — single wiki source + propagation rule documented.
- Validation architecture: **HIGH** — 17 tests mapped 1:1 to 9 REQs; framework already installed.

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days — NotebookLM skill versioning and pydantic v2 are stable; Phase 6 plans must complete within this window or re-verify external skill compatibility)

## RESEARCH COMPLETE
