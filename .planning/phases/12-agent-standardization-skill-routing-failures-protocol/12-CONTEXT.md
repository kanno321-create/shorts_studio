# Phase 12: Agent Standardization + Skill Routing + FAILURES Protocol - Context

**Gathered:** 2026-04-21
**Status:** Ready for planning
**Source:** /gsd:discuss-phase 12 세션 #29 연장 — 대표님 직접 4 영역 결정 (AGENT.md 표준 template × 30명 Migration 전략 × FAILURES 500줄 rotation × AGENT-STD-03 Supervisor 압축). Area 4 Q1 "compressed 형식 fallback" 은 대표님 "품질 위주, 추천안 수용" 지시로 해석 — decisions[] truncate + 명시적 표시 채택 + severity-based ordering 보강안 추가.

<domain>
## Phase Boundary

**Goal (ROADMAP §316-328)**: Phase 11 라이브 smoke 1차 실패(F-D2-EXCEPTION-01, trend-collector JSON 미준수) + 2차 attempt GATE 2 "프롬프트가 너무 깁니다"(rc=1)로 노출된 **하네스 품질 3대 고질 해소** — (a) 출력 형식 drift, (b) 도구 오용, (c) 재호출 루프. 30명 에이전트(13 producer + 17 inspector) AGENT.md 전수 표준화 + Agent × Skill 매핑 매트릭스 + FAILURES.md 500줄 rotation + `<mandatory_reads>` 블록 + Supervisor prompt 압축. 본 phase 완결 시 Phase 11 deferred SC#1(live smoke 완주)/SC#2(영상 1편 실 발행) 재도전 경로 확보.

**Depends on:** Phase 11 complete_with_deferred (2026-04-21) + 대표님 session #29 'a' 응답(Option D + Phase 12 발의 양쪽 승인).

**Phase 12 scope (이 Plan들이 건드릴 경계)**:
- `.claude/agents/producers/*/AGENT.md` (13 files: 14 producer - harvest-importer Phase 3 deprecated 제외)
- `.claude/agents/inspectors/*/*/AGENT.md` (17 files: structural 3 + content 3 + style 3 + compliance 3 + technical 3 + media 2)
- `.planning/phases/12-.../templates/producer.md.template` + `inspector.md.template` (Plan 01 신규 산출)
- `wiki/agent_skill_matrix.md` (신규 30 × 8 매트릭스)
- `.claude/hooks/pre_tool_use.py` `check_failures_append_only` (500줄 cap 확장)
- `scripts/audit/failures_rotate.py` (신규)
- `scripts/orchestrator/invokers.py` `ClaudeAgentSupervisorInvoker.__call__` + 신규 `_compress_producer_output()` private
- `tests/phase12/` (신규 — Mock replay fixture + schema verification + rotation idempotency)
- `scripts/validate/verify_agent_skill_matrix.py` + `verify_agent_md_schema.py` (신규)

**Phase 12 scope 밖 (deferred 또는 후속 Phase)**:
- `mandatory_reads` 블록의 **hard enforcement** (Hook 검증 + invoker 교육 hint 자동 삽입) — Phase 13 재검토 조건부 발의 (F-D2-EXCEPTION-01 재발 시)
- ClaudeAgentProducerInvoker compression — Phase 11 Option D retry-with-JSON-nudge 이미 반영, 이번 scope 아님
- `_imported_from_shorts_naberal.md` 500줄 cap 적용 (Phase 3 D-14 sha256-lock 보존 — 영구 면제)
- frontmatter 재설계(`schema_version`, `inputs_schema_ref` 등 확장 필드) — YAGNI
- 단일 batch commit 방식 (30명 일괄) — rollback 입도 상실 위험

</domain>

<decisions>
## Implementation Decisions

### AGENT.md 표준 schema 형식 (Area 1)

- **D-A1-01**: **XML 블록 5섹션 엄격** 채택. `<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>` 고정 순서. 모든 30명 AGENT.md 의 body(frontmatter 다음) 첫 부분이 이 5 블록 순서로 시작. trend-collector v1.1 패턴 연장.
- **D-A1-02**: **frontmatter 현재 필드 유지** — `name` / `description` / `version` / `role` / `category` / `maxTurns` 만. `skills` 매핑은 `wiki/agent_skill_matrix.md` 가 **단일 source-of-truth (SSOT)**. frontmatter 에 `skills_required` 필드 추가 금지 (이중 관리 drift 방지).
- **D-A1-03**: **`<mandatory_reads>` 전수 읽기 soft 강제** — 블록 내부에 "매 호출마다 전수 읽기, 샘플링 금지" 문구 표준화. Claude CLI prompt engineering 신뢰. Hook/invoker hard enforcement 는 Phase 13 재검토 조건부(F-D2-EXCEPTION-01 패턴 재발 시).
- **D-A1-04**: **영문 XML 태그 + 한국어 내부 설명** — 태그는 `<role>` 등 영문 snake-case. 블록 내부 본문 + 설명 주석은 한국어 baseline(나베랄 정체성 준수). regex 검증 친화성 + 인터내셔널 호환성.

### 30명 Migration 전략 (Area 2)

- **D-A2-01**: **Wave 기반 (Phase 4 패턴)** 채택. 8 Wave 구조:
  - Wave 1: Producer Core 6 (trend-collector / niche-classifier / researcher / director / scripter / metadata-seo) — trend-collector 는 v1.1 → v1.2 (5 블록 완성)
  - Wave 2: Producer Support 7 (scene-planner / shot-planner / script-polisher / voice-producer / asset-sourcer / thumbnail-designer / assembler / publisher 중 13 total에 맞춰 7명 선정)
  - Wave 3: Inspector Structural 3 (ins-schema-integrity / ins-timing-consistency / ins-blueprint-compliance)
  - Wave 4: Inspector Content 3 (ins-factcheck / ins-narrative-quality / ins-korean-naturalness)
  - Wave 5: Inspector Style 3 (ins-thumbnail-hook / ins-tone-brand / ins-readability)
  - Wave 6: Inspector Compliance 3 (ins-license / ins-platform-policy / ins-safety)
  - Wave 7: Inspector Technical 3 (ins-audio-quality / ins-render-integrity / ins-subtitle-alignment)
  - Wave 8: Inspector Media 2 (ins-mosaic / ins-gore)
  - 13 Producer 최종 카운트(= 14 - harvest-importer deprecated)는 Plan 01 단계에서 producer 디렉토리 실측 기반으로 6+7 분할 확정.
- **D-A2-02**: **role별 template 2종 생성** (Plan 01 산출) — `12-.../templates/producer.md.template` + `inspector.md.template`. 각 Wave 는 template 에서 clone → 에이전트별 content(Inputs/Outputs/Examples) 병합. trend-collector v1.1 direct clone 금지(role 차이 수동 적용 drift 회피).
- **D-A2-03**: **각 Wave commit 직후 regression** — `pytest tests/` + `scripts/validate/verify_agent_md_schema.py` + `scripts/validate/harness_audit.py` 3종 sweep. 실패 시 다음 wave 차단 + revert 제안. Phase 4 증명된 pattern.
- **D-A2-04**: **Wave 단위 rollback 경계** — 각 Wave 는 단일 atomic commit(다만 TDD RED→GREEN 시 최대 2 commit 허용). git revert `<wave-commit>` 으로 해당 wave 에이전트 그룹만 전 버전으로. skill_patch_counter 는 Wave commit 들을 **F-D2-EXCEPTION-02** 단일 directive-authorized batch entry 로 일괄 기록 (Phase 11 AUDIT-05 idempotency 활용).

### FAILURES 500줄 rotation 정책 (Area 3)

- **D-A3-01**: **append 시점 pre_tool_use Hook trigger** — `.claude/hooks/pre_tool_use.py` 의 `check_failures_append_only` 에 500줄 cap 추가. 초과 시 Write/Edit deny + 안내 메시지: "FAILURES.md 500줄 cap 초과 — `python scripts/audit/failures_rotate.py` 실행 후 재시도". 실시간 강제 + Hook regex 1줄 추가 수준의 미세 성능 부담. rotation 실행 책임 = 사용자/오케스트레이터(에이전트 아님).
- **D-A3-02**: **Archive naming = `_archive/YYYY-MM.md` (rotation 시점 월)** — `.claude/failures/_archive/2026-04.md` 형식. rotation 실행 당시 월 기준으로 하나의 archive 파일. 동일 월 내 여러 rotation 발생 시 동일 파일에 append. 간단성 + 분석 시 시간축 정렬 용이.
- **D-A3-03**: **`_imported_from_shorts_naberal.md` 영구 면제** — Phase 3 D-14 sha256-locked read-only reservoir 이므로 500줄 cap 적용 X + rotation 스캔 대상에서 명시적 제외. `failures_rotate.py` 는 `FAILURES.md` 만 스캔. D-2 저수지 원칙: 중복 스캔 `aggregate_patterns.py` 는 두 파일 모두 스캔 유지(분석용) — rotation 과 별개 책임.
- **D-A3-04**: **`scripts/audit/failures_rotate.py` + Hook whitelist** — 스크립트 위치 `scripts/audit/` (skill_patch_counter.py 와 동일 디렉토리). append-only Hook 은 `os.environ.get('FAILURES_ROTATE_CTX') == '1'` 일 때만 rotation 경로 whitelist 통과. 스크립트가 env var 세팅 후 (1) 500줄 cap 지점까지 archive 이관 → (2) FAILURES.md head 섹션(schema + 주의문) 보존 + oldest-entries 이동 → (3) git commit (F-D2-EXCEPTION-02 batch entry). idempotent.

### AGENT-STD-03 Supervisor prompt 압축 (Area 4)

- **D-A4-01**: **decisions[] truncate + 명시적 표시 (fallback)** — compressed summary(`{gate, verdict, decisions[], error_codes[]}`) 도 context limit 초과 시 decisions[] 앞에서부터 재는 char 예산(기본 2000 chars, research 단계 재검토) 정지 + `"_truncated": "N more decisions truncated"` 메타 필드 표시. `error_codes[]` 는 전수 보존(Inspector retry 가이드 필수). **품질 강화안 (대표님 지시)**: decisions[] 항목에 severity/score 필드 존재 시 severity_desc → score_asc 순 정렬 후 truncate (정보 유실 최소화). severity 필드 부재 시 순차 truncate fallback.
- **D-A4-02**: **ClaudeAgentSupervisorInvoker.__call__ scope 한정** — Phase 11 Option D 가 Producer invoker retry-with-JSON-nudge 기능 반영 완료 상태 → supervisor 경로만 공백. 1 파일 수정 blast radius 최소, Phase 11 regression 280/280 보존 심각. `ClaudeAgentProducerInvoker`, 기타 Invoker 는 본 phase scope 아님 (Phase 13+ 조건부).
- **D-A4-03**: **Mock replay + unit test 1차 regression** — `tests/phase12/test_supervisor_compress.py` 에 (1) Phase 11 smoke 2차 attempt producer_output JSON fixture (실측 크기 — 녹화 필수) + (2) `MockClaudeCLI` 경유 SupervisorInvoker 호출, (3) compress 전후 byte size 측정 assertion(압축률 > 40% + Claude CLI context limit 기준 대비 safe margin). 실 smoke 추가 실행은 Phase 13 deferred(Phase 11 SC#1 재도전 별도 플랜).
- **D-A4-04**: **`invokers.py` 내 `_compress_producer_output()` private 함수** — `scripts/orchestrator/invokers.py` 내 새 private 함수. `ClaudeAgentSupervisorInvoker.__call__` 의 `body = json.dumps(producer_output)` 직전 `compressed = _compress_producer_output(producer_output); body = json.dumps(compressed)` 삽입. 1 파일 수정, 테스트 seam = 직접 import. Phase 11 D-01~D-04 (stdin piping) 패턴 복사.

### Claude's Discretion (research/planner 재량)

- template 내 `<role>` / `<output_format>` 블록의 prose 세부 문구 (30명 각각 customized 하되 schema 준수)
- Wave 2 Producer Support 7 의 정확한 분할 (Plan 01 단계에서 producer 디렉토리 실측 기반)
- 7 plan 중 PLAN 01(template + schema) 외 Plan 04(skill-matrix) / Plan 05(FAILURES rotation) / Plan 07(supervisor-compress) 의 실행 순서(wave pattern 과 병행 가능성)
- severity-based ordering 구현 시 rubric-schema.json 확장 여부 (research 결과 따라)
- compression char budget 기본값(2000) vs Claude CLI context limit 실측 기반 동적 계산

### Folded Todos

Phase 12 관련 pending todo 없음 (`gsd-tools todo match-phase 12` 결과 `todo_count: 0`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 12 REQ 정의 & Goal
- `.planning/ROADMAP.md` §316-337 — Phase 12 entry + 7 plan proposal + 6 Success Criteria + Progress Table row
- `.planning/REQUIREMENTS.md` §377-401 — AGENT-STD-01, AGENT-STD-02, AGENT-STD-03, SKILL-ROUTE-01, FAIL-PROTO-01, FAIL-PROTO-02 REQ 정의

### Phase 11 연결 노드 (AGENT-STD-03 + F-D2-EXCEPTION-01 출처)
- `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-CONTEXT.md` §D-17~D-21 — Phase 12 deferred SCRIPT-01 옵션 B/C 조건부 spawn 맥락
- `.planning/phases/11-pipeline-real-run-activation-script-quality-mode/11-VERIFICATION.md` — Gap #1 (AGENT-STD-03 source of truth — context limit "프롬프트가 너무 깁니다" rc=1 증거)
- `.claude/failures/FAILURES.md` §F-D2-EXCEPTION-01 — trend-collector JSON 미준수 patch + directive-authorized 선례 (FAIL-PROTO-02 prototype)

### Phase 4 에이전트 구조 + 32 에이전트 lock
- `.planning/phases/04-agent-team-design/04-CONTEXT.md` — 32 에이전트 구조 + 17 Inspector 6 카테고리 + Wave 1a~5 migration 패턴
- `.planning/phases/04-agent-team-design/04-VALIDATION.md` — 244/244 pytest PASS + GAN_CLEAN 17/17 baseline(Phase 12 regression 기준)

### Phase 6 FAILURES append-only + D-2 저수지
- `.planning/phases/06-wiki-notebooklm-integration-failures-reservoir/06-CONTEXT.md` §D-11 / §D-14 — append-only Hook + sha256-lock invariant
- `scripts/failures/aggregate_patterns.py` — 두 failures 파일 스캔 분석 CLI (rotation 과 별개 책임)

### Phase 10 D-2 저수지 + skill_patch_counter
- `.planning/phases/10-sustained-operations/10-CONTEXT.md` — D-2 저수지 규율 baseline (SKILL patch 금지, directive-authorized exception 경계)
- `scripts/audit/skill_patch_counter.py` — Phase 11 AUDIT-05 idempotency (F-D2-EXCEPTION-02 batch entry 멱등 기록 활용)

### Template prototype & 에이전트 파일들
- `.claude/agents/producers/trend-collector/AGENT.md` (v1.1) — `<mandatory_reads>` + `<output_format>` 블록 prototype (Wave 1 에서 v1.2 로 완성 — 5 블록 전수)
- `.claude/agents/producers/` + `.claude/agents/inspectors/` — 30명 AGENT.md migration target (13 producer + 17 inspector)

### Hook & 인프라
- `.claude/hooks/pre_tool_use.py` — `check_failures_append_only` 수정 대상 (500줄 cap 확장)
- `scripts/orchestrator/invokers.py` — `ClaudeAgentSupervisorInvoker.__call__` 수정 대상 (AGENT-STD-03)

### Channel bible & wiki
- `wiki/continuity_bible/channel_identity.md` — 7 niche 통합 channel bible (REQUIREMENTS AGENT-STD-02 문구 "wiki/ypp/channel_bible.md" 는 **경로 drift** — research 단계에서 실제 경로로 정정 권고)
- `.preserved/harvested/theme_bible_raw/{documentary,humor,incidents,politics,trend,wildlife}.md` — niche-specific bible (Phase 3 sha256-locked). Producer AGENT.md `<mandatory_reads>` 에서 해당 niche 매핑 경로 참조.
- `wiki/ypp/MOC.md` + `wiki/algorithm/MOC.md` + `wiki/render/MOC.md` — 기존 30 AGENT.md 의 `@wiki/shorts/...` 참조 대상 (Phase 6 Plan 10 에서 52 refs 배포 완료)

### Project & Global
- `CLAUDE.md` §금기사항 + §필수사항 — Hook 3종 + 32 에이전트 + SKILL 500줄 불변
- `naberal_harness/STRUCTURE.md` — Whitelist 헌법 (Phase 12 신규 디렉토리 `_archive/` 등록 필요 여부 research 단계 검증)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **trend-collector v1.1 AGENT.md**: `<mandatory_reads>` + `<output_format>` 블록 prototype. Wave 1 에서 5 블록 완성 + 12 producer 복제 기준선. frontmatter `version: 1.1` → Wave 완료 시 `1.2` bump.
- **Phase 4 Wave 1a~5 migration 패턴**: 244/244 pytest PASS + 32 agent 생성 증명된 경로. Wave 내 parallel execution 가능, Wave 간 sequential + regression gate.
- **`scripts/audit/skill_patch_counter.py`**: Phase 11 AUDIT-05 commit-hash-set idempotency. F-D2-EXCEPTION-02 batch entry 멱등 기록에 재활용.
- **Phase 11 11-01 `_invoke_claude_cli` stdin piping**: D-01~D-04 pattern. AGENT-STD-03 supervisor compression 도 동일 "1 파일 수정 + 테스트 seam 보존" 경계 유지.
- **`.claude/hooks/pre_tool_use.py` check_failures_append_only** 기존 regex — 500줄 cap 추가는 1줄 변경 수준.
- **`scripts/failures/aggregate_patterns.py`**: 두 failures 파일 스캔 로직 재사용 — rotation 대상 파일 구분은 새 코드 필요 없이 스캔 대상 인수로 제어.

### Established Patterns
- **XML 블록 + 한국어 설명**: trend-collector v1.1 + rubric-schema.json 의 evidence 배열 주석 패턴. 신규 template 이 따를 기준.
- **Wave 패턴 + atomic commit**: Phase 4 / Phase 7 / Phase 8 일관 적용. TDD RED→GREEN 허용, wave 당 1-2 commit.
- **F-D2-EXCEPTION-NN directive-authorized batch**: Phase 11 F-D2-EXCEPTION-01 prototype. 30+ 파일 patch 를 단일 FAILURES entry 로 기록 (authorized_by + scope + verification 3 필드 필수).
- **`os.environ.get('CONTEXT_VAR') == '1'` Hook whitelist**: 기존 pre_tool_use 가 쓰는 `CLAUDE_AGENT_BYPASS` 등의 패턴 연장. 신규 `FAILURES_ROTATE_CTX` 추가.
- **Mock CLI + unit test fixture**: Phase 7 `tests/phase07/mocks/` 패턴 재사용. `tests/phase12/mocks/MockClaudeCLI` 신규 또는 기존 재import.

### Integration Points
- **ROADMAP.md Progress Table**: Phase 12 row `0/7 📋 Planned` → Wave 진행에 따라 갱신
- **REQUIREMENTS.md [x] 플립**: 7 REQ (AGENT-STD-01/02/03, SKILL-ROUTE-01, FAIL-PROTO-01/02 + 덤) — 각 Wave commit 에 동봉
- **`.planning/STATE.md` session record**: 매 Wave 완료 시 `gsd-tools state record-session` 기록
- **`wiki/agent_skill_matrix.md` 신규 작성**: Wave 3 정도에서 — template 확정 + Producer 전수 완료 후 매트릭스 Row 안정화, 이후 Inspector Wave 가 추가
- **`.claude/failures/FAILURES.md` F-D2-EXCEPTION-02 entry**: Phase 12 첫 Wave commit 시점 또는 Phase 완료 시점 중 하나에 단일 기록 — plan-phase 에서 timing 확정

</code_context>

<specifics>
## Specific Ideas

- **trend-collector v1.1 이 기준선**: Wave 1 에서 v1.1 → v1.2 승격(5 블록 완성) 후 나머지 12 producer 는 v1.2 직접 시작. Inspector 17 은 Wave 3~8 에서 v1.0 → v1.1 (inspector template 기반).
- **"샘플링 금지, 전수 읽기" 강력 문구**: 대표님 session #29 지시. soft enforcement 이지만 prose 자체는 명시적이고 반복 — 30명 모든 `<mandatory_reads>` 블록에 동일 문구.
- **"품질 위주, 제대로 돌아가는 프로그램"** (대표님 Area 4 Q1 답변): AGENT-STD-03 fallback 구현 시 단순 truncate 보다 severity-based ordering 우선 검토. 정보 유실 최소화 원칙.
- **Phase 11 smoke 2차 attempt 증거 보존**: fixture 로 재사용할 producer_output JSON 은 Phase 11 reports/ 디렉토리에서 실측 추출 — Plan 07 단계에서 구체 경로 확정.
- **REQUIREMENTS 경로 drift "wiki/ypp/channel_bible.md"**: research 단계에서 정정 PR 권고 — 실제 파일은 `wiki/continuity_bible/channel_identity.md` + `.preserved/harvested/theme_bible_raw/<niche>.md`.

</specifics>

<deferred>
## Deferred Ideas

### 본 Phase scope 초과, 다른 Phase 로 이관
- **mandatory_reads hard enforcement** (Hook 검증 + invoker 교육 hint 자동 삽입) — Phase 13 조건부 (F-D2-EXCEPTION-01 재발 관측 시)
- **ClaudeAgentProducerInvoker compression** — Phase 11 retry-nudge 와 중복, AGENT-STD-03 scope 밖. Phase 13+ 조건부.
- **frontmatter schema_version 확장** (inputs_schema_ref / outputs_schema_ref / skills_required) — YAGNI, 현 구조로 충분
- **`_imported_from_shorts_naberal.md` 500줄 cap 적용** — Phase 3 D-14 sha256-lock 영구 면제
- **단일 batch commit 방식** (30명 일괄) — rollback 입도 상실 위험, Wave 기반 탈락
- **Phase 11 SC#1 live smoke 재도전** — Phase 12 완결 후 별도 mini-phase(또는 Phase 12 VERIFICATION 내 optional step)
- **skill-matrix 의 forbidden 4단계 cell 값** (required/optional/forbidden/n-a) — ROADMAP 이 3단 (required/optional/n-a) 으로 lock, forbidden 사례(inspector_prompt 읽기 금지)는 AGENT.md `<constraints>` 블록 개별 명시로 대체

### Reviewed Todos (not folded)
해당 없음 — Phase 12 매칭 pending todo 0건.

</deferred>

---

*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Context gathered: 2026-04-21*
