# Phase 3: Harvest - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — decisions pre-locked in 02-HARVEST_SCOPE.md)

<domain>
## Phase Boundary

shorts_naberal의 작동 검증된 자산(theme-bible, Remotion src, hc_checks, FAILURES, API wrappers)을 `.preserved/harvested/`에 **읽기 전용**으로 이관하고 CONFLICT_MAP 39건을 전수 판정하여, Phase 4 Agent 설계가 "무엇을 승계하고 무엇을 폐기하는가"라는 질문 없이 진행될 수 있는 기반을 구축한다.

**Scope in:**
- 4 raw 디렉토리 복사 (theme_bible_raw / remotion_src_raw / hc_checks_raw / api_wrappers_raw)
- FAILURES 통합본 이관 (`_imported_from_shorts_naberal.md`)
- chmod -w / attrib +R Tier 3 immutable lockdown
- HARVEST_DECISIONS.md 39건 (A급 13 승격 + B/C급 26 5-rule 알고리즘 판정)
- Harvest Blacklist 준수 (11 entries) + grep 감사

**Scope out:**
- shorts_naberal 원본 수정 (읽기만)
- longform/ 전체 (A-11 폐기, shorts 전용 스튜디오)
- Phase 4+ 에이전트 프롬프트 재작성 (Harvest는 복사만, 재작성은 후속)

</domain>

<decisions>
## Implementation Decisions

### A급 13건 사전 판정 (02-HARVEST_SCOPE.md §1 인용)
- **승계 2건**: A-2 (cuts[] 스키마), A-9 (탐정님 호명 금지 regex)
- **폐기 3건**: A-5 (TODO 미연결 4곳), A-6 (skip_gates 블록), A-11 (longform-scripter)
- **통합-재작성 8건**: A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 — 개념만 참조, Phase 4+ 에서 신규 구현

### B/C급 26건 5-rule 판정 알고리즘 (02-HARVEST_SCOPE.md §5)
1. Harvest blacklist takes precedence → 폐기
2. Scope boundary (longform/JP/worktree/duo_japan) → 폐기
3. Session 77+ canonical forms → 승계 신형
4. Cosmetic cleanup (gitignore/worktree_copy/tmp_committed) → cleanup
5. Default → 통합-재작성

Harvest-importer 에이전트(AGENT-06)가 이 알고리즘을 코드로 파싱하여 실행.

### Harvest Blacklist 11 entries (02-HARVEST_SCOPE.md §2)
Python dict 형식으로 제공. A-6 skip_gates 블록 (orchestrate.py:1239-1291), A-5 TODO 4곳, longform/, create-video/, create-shorts/SKILL.md, selenium 패턴, orchestrate.py 전체 — 이관 시 skip.

### 4 raw 디렉토리 매핑 (REQUIREMENTS.md HARVEST-01~05)
| 목적지 | 소스 | 필터 | REQ |
|--------|------|------|-----|
| `.preserved/harvested/theme_bible_raw/` | `shorts_naberal/.claude/theme-bible/` | 무필터 | HARVEST-01 |
| `.preserved/harvested/remotion_src_raw/` | `shorts_naberal/src/` | `node_modules/` 제외 | HARVEST-02 |
| `.preserved/harvested/hc_checks_raw/` | `shorts_naberal/scripts/*hc_checks*` | Blacklist 참조 | HARVEST-03 |
| `.preserved/harvested/api_wrappers_raw/` | `shorts_naberal/scripts/api/` | `orchestrate.py` 자체 제외 | HARVEST-05 |

### FAILURES 이관 (HARVEST-04)
- 소스: `shorts_naberal/.claude/failures/**/FAILURES.md` + 루트 `FAILURES.md`
- 대상: `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
- 규칙: append-only concat + `<!-- source: ... -->` 주석으로 출처 유지

### Tier 3 Immutable Lockdown (HARVEST-06)
Windows: `attrib +R /S /D .preserved\harvested\*` 재귀 적용. Write 시도 시 OS 레벨 거부.

### Claude's Discretion
- 4 raw 디렉토리 병렬 복사 순서는 자유 (의존성 없음)
- chmod 적용 시점은 모든 복사 완료 후 마지막 단계
- HARVEST_DECISIONS.md 포맷은 HARVEST_SCOPE.md A급 테이블과 동일 컬럼 유지 (5-column)
- harvest-importer 에이전트 구현 방식 (Python 스크립트 vs 인라인 bash) 은 planner 재량

</decisions>

<code_context>
## Existing Code Insights

### 소스 코드베이스 (shorts_naberal/, 읽기 전용)
- `.claude/theme-bible/` — 채널 바이블 (전체 승계)
- `src/` — Remotion composition (node_modules 제외)
- `scripts/api/` — Kling / Runway / ElevenLabs / Typecast / Fish Audio / HeyGen / Hedra wrapper
- `scripts/orchestrator/orchestrate.py` — **전체 폐기 대상** (5166줄 drift, Phase 5 재작성)
- `scripts/orchestrator/*hc_checks*` — 실측 작동 모듈 (블랙리스트 외 승계)
- `.claude/failures/` — 에이전트별 FAILURES.md (통합 이관 대상)
- `longform/` — **전체 폐기** (scope 외)

### 목적지 코드베이스 (studios/shorts/, Phase 2 완료 시점)
- `.preserved/harvested/.gitkeep` — Phase 2에서 scaffold만 (실 파일은 이 Phase에서 채움)
- `.claude/failures/orchestrator.md` — 기존 Tier A 실패 기록 (보존, 병합 없음)
- `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` — 본 Phase의 canonical 입력
- `wiki/` — Tier 2 MOC 스켈레톤 (Phase 4~6에서 채움, 본 Phase와 무관)

### 통합 지점
- harvest-importer 에이전트는 Phase 3에서만 존재 (AGENT-06) — Phase 4 Agent Team Design은 본 에이전트를 참조하지 않음
- Phase 3 완료 후 `.preserved/harvested/` 는 Phase 4+ 에이전트가 프롬프트 reference 로만 사용 (copy-paste 금지, 재작성 의무)

</code_context>

<specifics>
## Specific Ideas

- HARVEST_SCOPE.md Python dict 를 harvest-importer 에이전트가 직접 eval 없이 json.loads 또는 ast.literal_eval 로 로드할 것. 보안상 eval 금지.
- diff -r 검증은 Windows에서 `fc /b` 대체 가능 (또는 Python `filecmp.dircmp` 활용).
- attrib +R 적용 전 symbolic link / junction 존재 여부 확인 (shorts_naberal 은 일반 파일 트리이므로 이슈 없음 예상, 단 verify).
- HARVEST_DECISIONS.md 는 HARVEST_SCOPE.md A급 13 블록 + B/C급 26 신규 블록 합쳐 5-column 통일 포맷 유지.
- Phase 10 첫 1~2개월 SKILL patch 금지 규율과 연동: `_imported_from_shorts_naberal.md` 는 읽기 전용 레퍼런스.

</specifics>

<deferred>
## Deferred Ideas

None — Phase 3 는 사전 판정된 HARVEST_SCOPE.md 를 충실히 실행. 새로운 결정은 B/C급 26건 알고리즘 적용 결과뿐이며, 이 또한 Phase 2에서 규칙 lock 완료.

</deferred>
