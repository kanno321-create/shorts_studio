# Phase 12: Agent Standardization + Skill Routing + FAILURES Protocol - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-21
**Phase:** 12-agent-standardization-skill-routing-failures-protocol
**Areas discussed:** AGENT.md 표준 template 세부, 30명 Migration 전략, FAILURES 500줄 rotation 정책, AGENT-STD-03 Supervisor 압축

---

## Initial Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| AGENT.md 표준 template 세부 | trend-collector v1.1 복제 vs role별 differentiated template. 섹션 순서, XML 블록 vs Markdown, frontmatter 확장, 한/영 섹션명 일관성 | ✓ |
| 30명 Migration 전략 | Wave 기반 incremental (Producer 13 → Inspector 17 6카테고리) vs 단일 batch commit | ✓ |
| FAILURES 500줄 rotation 정책 | Rotation trigger (pre-write Hook vs session_end vs daily cron), archive naming, sha256-locked 파일 면제 처리 | ✓ |
| AGENT-STD-03 Supervisor 압축 | summary 4필드 locked. context limit fallback, scope(SupervisorInvoker만 vs 전반), Phase 11 smoke 2차 regression 검증 | ✓ |

**User's choice:** 4개 영역 전체 선택 (multiSelect)
**Notes:** ROADMAP 이 이미 7 plan 을 제안하여 plan scope 는 locked. gray area 는 plan 내부 구현 세부에 집중.

---

## Area 1: AGENT.md 표준 template 세부

### Q1.1: 30명이 공유할 표준 schema 형식은?

| Option | Description | Selected |
|--------|-------------|----------|
| XML 블록 5섹션 엄격 (Recommended) | `<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>` 5개 XML 블록 순서 고정. regex 검증 쉬움, downstream 에이전트 고밀활용 크리티컬. trend-collector v1.1 패턴 연장. | ✓ |
| Markdown 헤딩 유지 + XML 선택적 | 현행 29명처럼 Markdown `## 섹션명(한글)` 에 XML 블록은 `<mandatory_reads>`/`<output_format>` 두 개만 강제. 나머지는 기존 관습 유지. drift 가능성 높음. | |
| XML 5섹션 + role별 differentiated | XML 5섹션 엄격 + role=producer 와 role=inspector 는 서로 다른 필드를 가질 수 있음. 유연성 최고, 검증 복잡도 중간. | |

**User's choice:** XML 블록 5섹션 엄격 (Recommended)
**Notes:** trend-collector v1.1 이 실증 prototype. 30명 일관성과 regex 검증 친화성 선택.

### Q1.2: frontmatter 확장 범위?

| Option | Description | Selected |
|--------|-------------|----------|
| 현재 필드 유지 (Recommended) | name/description/version/role/category/maxTurns 유지. `skills` 매핑은 별도 matrix 파일(agent_skill_matrix.md)에만 기록. 단일 source-of-truth 원칙 준수, drift 위험 최소. | ✓ |
| skills_required 필드 추가 | frontmatter 에 `skills_required: [progressive-disclosure, gate-dispatcher]` 배열 필드 추가. matrix 와 AGENT.md 상호 검증 가능하나 속성 이중 관리 필요. | |
| 전체 재설계 (필드 재구성) | version → schema_version 2개 분리, 새 필드 다수 추가(inputs_schema_ref, outputs_schema_ref 등). 많은 변경 필요, regression risk 큼. | |

**User's choice:** 현재 필드 유지 (Recommended)
**Notes:** matrix 가 SSOT. frontmatter 에 skills_required 추가 금지.

### Q1.3: `<mandatory_reads>` 블록의 "전수 읽기" 강제 수준은?

| Option | Description | Selected |
|--------|-------------|----------|
| 문구만 명시 (soft) (Recommended) | 블록에 '매 호출마다 전수 읽기, 샘플링 금지' 문구 표준화. Claude CLI 가 실제로 전수 읽는지는 prompt engineering 신뢰. 구현 비용 0, F-D2-EXCEPTION-01 재발 시 invoker log 증거가 필요하면 Phase 13 강제 전환. | ✓ |
| Invoker 검증 로직 추가 (hard) | ClaudeAgentProducerInvoker 가 AGENT.md 의 <mandatory_reads> 블록을 파싱해 교육 hint 를 append-system-prompt 에 명시 삽입. 구현 비용 중간, 효과 검증 가능. | |
| Hook 검증 + invoker 삽입 두 단계 | pre-session 또는 pre-invoke hook 이 <mandatory_reads> 블록 존재 확인 + invoker 삽입 + 경고 로깅. FAILURES.md 기록 가능. 구현 복잡도 최고. | |

**User's choice:** 문구만 명시 (soft) (Recommended)
**Notes:** Phase 13 재검토 조건부 (F-D2-EXCEPTION-01 패턴 재발 시).

### Q1.4: 섹션명 언어 규칙?

| Option | Description | Selected |
|--------|-------------|----------|
| 영문 XML 태그 + 국문 설명 (Recommended) | `<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>` 영문 태그. 블록 내부 설명은 한국어. regex 검증 쉬움, 인터내셔널 상식 부합. | ✓ |
| 전면 한국어 XML 태그 | `<역할>`, `<필수읽기>`, `<출력형식>`, `<스킬>`, `<제약>` 한국어 태그. CLAUDE.md 나베랄 정체성(한국어 baseline)과 일치. 국제 도구호환성 불편, grep 근시 멀티바이트 이슈. | |
| 영문 태그 적지어 (agent_role/mandatory_reads 등) | snake_case 영문. 직관적이지만 XML 스타일과 거리 있음. | |

**User's choice:** 영문 XML 태그 + 국문 설명 (Recommended)

### Area 1 추가 질문?
**User's choice:** 다음 영역으로 (Recommended)

---

## Area 2: 30명 Migration 전략

### Q2.1: Migration 실행 단위는?

| Option | Description | Selected |
|--------|-------------|----------|
| Wave 기반 (Phase 4 패턴) (Recommended) | Wave 1 Producer Core 6 → Wave 2 Producer Support 7 → Wave 3~8 Inspector 6 카테고리. 각 wave 별 commit + regression. Phase 4 에서 이미 증명된 경로. | ✓ |
| 2 wave (Producer 13 → Inspector 17) | role 별 2개 wave. Plan 02 (Producer batch) + Plan 03 (Inspector batch). commit 단위 크고 rollback 입도 떨어짐. | |
| 단일 batch (30명 일괄) | Plan 02 단일에 30명 전수 patch. F-D2-EXCEPTION-02 batch entry 와 상온성 최상, rollback 경계 1개. 실패 현재화 위험 높음. | |

**User's choice:** Wave 기반 (Phase 4 패턴) (Recommended)

### Q2.2: trend-collector v1.1 template 복제 방식?

| Option | Description | Selected |
|--------|-------------|----------|
| role별 template 2종 생성 (Recommended) | `.planning/phases/12-.../templates/producer.md.template` + `inspector.md.template` 생성 (Plan 01 결과물). 30명 각각 template로부터 role 매칭 clone + 기존 content 병합. 독립적 testability. | ✓ |
| trend-collector 에서 직접 clone | trend-collector AGENT.md 복사 후 에이전트별 치환. Role 차이 수동 적용 필요, drift 리스크. | |
| 기존 각 AGENT.md in-place 패치 | 새 파일 없이 기존 파일에 <mandatory_reads>/<output_format>/<skills>/<constraints> 블록만 삽입. content 보존령 최대이나 regex 정합성 확신 어려움. | |

**User's choice:** role별 template 2종 생성 (Recommended)

### Q2.3: Wave 간 regression test 주기?

| Option | Description | Selected |
|--------|-------------|----------|
| 각 Wave commit 직후 regression (Recommended) | Phase 4 패턴. pytest tests/ + verify_agent_md_schema.py + harness_audit 삽화 없이 즉시. 실패 시 다음 wave 차단 + rollback. TDD 교본. | ✓ |
| 3 wave 묶음 후 일괄 regression | Wave 1-3 완료 후 regression. 시간 절감 기대되나 실패 원인 식별 어려움 급증. | |
| Phase 마지막 1회 regression | 8 wave 전수 완료 후 1회에 regression. 실패 누적 시 blast radius 최대. | |

**User's choice:** 각 Wave commit 직후 regression (Recommended)

### Q2.4: Migration rollback 경계는?

| Option | Description | Selected |
|--------|-------------|----------|
| Wave 단위 (Recommended) | git revert 하면 해당 wave 의 에이전트 그룹만 전 버전으로. 다른 Wave 변경 보존. Phase 4 증명된 패턴. 8 Wave 로 나누면 revert 입도 적절. | ✓ |
| 에이전트 단위 | 각 에이전트별 atomic commit 대량 생성 (30 commit). rollback 입도 최소, git log 오염 심각. skill_patch_counter 기록 수가 큰폭 증가. | |
| Phase 단위 (전체 revert 또는 보존) | 단일 batch commit 지향. rollback 시 Phase 전체 되돌림. F-D2-EXCEPTION-02 batch entry 와 정합하나 부분 실패 시 대책 부재. | |

**User's choice:** Wave 단위 (Recommended)

### Area 2 추가 질문?
**User's choice:** 다음 영역으로 (Recommended)

---

## Area 3: FAILURES 500줄 rotation 정책

### Q3.1: Rotation 실행 trigger 타이밍?

| Option | Description | Selected |
|--------|-------------|----------|
| append 시점 pre_tool_use Hook (Recommended) | check_failures_append_only 에 500줄 cap 추가. 초과 시 즉시 deny + rotation 안내 메시지. 실시간 강제, 성능 부담 미세(Hook regex 1줄 추가). rotation 실행 책임 = 사용자/오케스트레이터. | ✓ |
| session_end Hook auto-rotate | 세션 종료 시 500줄 초과하면 자동 rotation. UX 매끄러움, 대표님 수동 실행 불필요. 세션 중 500줄 임시 초과 허용 → 해당 세션 내 나중 에이전트들은 여전히 초과된 파일 읽음(전수읽기 위반 가능성). | |
| Daily cron 스케줄링 | scripts/schedule/windows_tasks.ps1 에 daily rotation job 추가. 인간 개입 없음, 단 24시간 사이의 전수읽기 위반 가능성 여전히 존재. | |
| pre-write Hook + Manual CLI 병행 | Hook 은 강제 차단만 + scripts/audit/failures_rotate.py 는 CLI 로만 제공. 에이전트가 Hook 에 막히면 사용자가 CLI 실행. 에이전트 side-effect 제로. | |

**User's choice:** append 시점 pre_tool_use Hook (Recommended)

### Q3.2: Archive 파일 naming 규칙?

| Option | Description | Selected |
|--------|-------------|----------|
| YYYY-MM.md (rotation 시점 월) (Recommended) | `_archive/2026-04.md` 형식. rotation 실행한 달 기준. 단순함. entry 가 여러 달에 걸쳐 있어도 하나의 archive 파일로 이동. rotation 자체 entry는 최근 것들만 남김. | ✓ |
| YYYY-MM.md (entry 발생 월 별로 분할) | entry 의 `발생 세션` 필드 파싱해 월별로 분리. 2026-02.md/2026-03.md/2026-04.md 동시에 생성 가능. 분석 손쉬움 큰 대신 구현 복잡. | |
| FAILURES-archive-{seq}.md (순번) | `_archive/FAILURES-archive-001.md`, `-002.md`. 중립적 시관 순서. 검색 시 월별 그룹화 불편. | |

**User's choice:** YYYY-MM.md (rotation 시점 월) (Recommended)

### Q3.3: `_imported_from_shorts_naberal.md` (sha256-locked) 처리?

| Option | Description | Selected |
|--------|-------------|----------|
| 면제 (500줄 cap 적용 X) + rotation 스캔 제외 (Recommended) | 해당 파일은 Phase 3 D-14 sha256-locked read-only reservoir. rotation 스크립트는 `FAILURES.md` 만 스캔. D-2 정책(중복 스캔 `aggregate_patterns.py` 는 두 파일 모두 스캔 → rotation 과 별개 책임). | ✓ |
| _imported도 500줄 cap 적용 | sha256-lock unlock 후 rotation. Phase 3 invariant 위반, D-14 재검토 필요. NOT recommended. | |
| 면제 하되 크기 한계 경고 로깅 | 현재 500줄 고정이므로 경고 불필요하나, 미래 _imported가 업데이트될 경우 인지. read-only이므로 실익 미지수. | |

**User's choice:** 면제 (500줄 cap 적용 X) + rotation 스캐 제외 (Recommended)
**Notes:** "스캐" 오타는 원문 "스캔"의 의도.

### Q3.4: rotation 스크립트 위치 + append-only Hook 프로토콜?

| Option | Description | Selected |
|--------|-------------|----------|
| scripts/audit/failures_rotate.py + Hook whitelist (Recommended) | 스크립트 위치 scripts/audit/ (skill_patch_counter.py 와 동일). append-only Hook 은 이 스크립트 경로만 whitelist(os.environ['FAILURES_ROTATE_CTX']=='1' 검사). 스크립트가 (1) 500줄 초과 지점까지 archive → (2) FAILURES.md 앞 부분 정리 → (3) commit. idempotent. | ✓ |
| scripts/failures/rotate.py + Hook bypass env var | scripts/failures/ (aggregate_patterns.py 와 동일 패키지). scope 관리 일관성. Hook bypass 동일 패턴. | |
| Hook 코드 내 직접 rotation 지원 | append-only Hook 이 직접 rotation 수행. regex 검증 후 500줄 초과면 현재 append 는 받고 후속 rotation 예약. Hook 복잡도 증가, 단일 책임 원칙 위반. | |

**User's choice:** scripts/audit/failures_rotate.py + Hook whitelist (Recommended)

### Area 3 추가 질문?
**User's choice:** (생략 — 곧바로 Area 4로 진행)

---

## Area 4: AGENT-STD-03 Supervisor 압축

### Q4.1: compressed 형식도 context limit 초과 시 fallback?

| Option | Description | Selected |
|--------|-------------|----------|
| decisions[] truncate + 명시적 표시 (Recommended) | decisions[] 를 앞에서부터 재는 char 예산(예: 2000 chars) 정지 + '...N more decisions truncated' 표시. error_codes[] 는 전수 보존(Inspector retry 가이드 필수 정보). 정보 손실 명시적, downstream 에이전트가 판단 가능. | ✓ (품질 강화안 추가) |
| decisions[] drop + file reference | context limit 음 시 decisions[] 모두 제거 후 외부 파일 경로('@reports/.../producer_output.json') 로 접근 유도. 에이전트가 파일 읽을 수 있지만 retry nudge 에 연쇄 흐름 추가 호출. | |
| Chunked summary (중요도 넌엑 선별) | decisions[] 에 severity/score 등 중요도 필드 평가 후 top-N 만 남김. 정보 유지력 최상, 구현 복잡도 큼. rubric-schema.json 확장 필요. | |

**User's choice:** "모든선택은 품질위주로 제대로 돌아가는 프로그램이 되도록, 너가 추천하는선택지를 모두선택해라" (free text)
**Claude interpretation:** 대표님 지시 = 품질 위주 + recommended 옵션 수용 → Q1 Recommended(decisions[] truncate + 명시적 표시) 채택. 품질 강화 차원으로 **severity-based ordering 보강안 추가**: decisions[] 항목에 severity/score 필드 존재 시 severity_desc → score_asc 순 정렬 후 truncate (정보 유실 최소화). severity 필드 부재 시 순차 truncate fallback.

### Q4.2: Compression scope 범위?

| Option | Description | Selected |
|--------|-------------|----------|
| ClaudeAgentSupervisorInvoker.__call__ 만 (Recommended) | AGENT-STD-03 ROADMAP 명시 스코프와 정합. Phase 11 Option D 가 Producer invoker retry-nudge 적용 완료 → supervisor 만 남은 공백. 미단위 blast radius, Phase 11 regression 329/329 보존 심각. 1 파일 수정. | ✓ |
| ClaudeAgentSupervisorInvoker + ClaudeAgentProducerInvoker 둘 다 | Producer invoker 도 prior_vqqa 이 누적되면 bloat 가능성. 두 곳 동일 compression 모듈 사용. DRY 원칙 준수. scope 널으나 Phase 11 retry-nudge 과 상호작용 검증 필요(combine 시 정보 중복 vs 손실). | |
| 전체 Invoker 계층 + 공용 compression 모듈 | scripts/orchestrator/invoker_common.py 신규 생성. 모든 invoker 경로에 적용. 대규모 재구조, Phase 11 regression 영향 심각. | |

**User's choice:** ClaudeAgentSupervisorInvoker.__call__ 만 (Recommended)

### Q4.3: Phase 11 smoke 2차 재실행 regression 검증?

| Option | Description | Selected |
|--------|-------------|----------|
| Mock replay + unit test 1차 (Recommended) | tests/phase12/ 에 fixture 로 Phase 11 smoke 2차 attempt 의 producer_output JSON (사이즈 ~X KB) 배치 + SupervisorInvoker 를 MockClaudeCLI 로 변종. compress 전후 byte size 측정. 실 스모크 비용 없이 증거. 시스템 경계 validation 이미 선략 단위 테스트로. | ✓ |
| Phase 11 재실스모크 + 래이브 관증 | Phase 12 마지막 plan 에서 실제 live smoke 진행. 실증적 확시. 비용 수반(단, $0.50 이내로 예상). AGENT-STD-03 의 Phase 11 SC#1/#2 이관 해소 뜨적이 직접적. | |
| Mock + live smoke 병행 | Mock (Plan 07) + live smoke (Phase gate) 두 단계. 증거 최강하나 노력 이중. Phase 7 패턴 복사. | |

**User's choice:** Mock replay + unit test 1차 (Recommended)

### Q4.4: compression 함수 위치 + interface?

| Option | Description | Selected |
|--------|-------------|----------|
| invokers.py 내 _compress_producer_output() private (Recommended) | scripts/orchestrator/invokers.py 에 새 private 함수 추가. ClaudeAgentSupervisorInvoker.__call__ 의 `body = json.dumps(producer_output)` 직전에 `compressed = _compress_producer_output(producer_output); body = json.dumps(compressed)` 삽입. 1 파일 수정, blast radius 최소. 테스트 seam = 직접 import. Phase 11 D-01~D-04 패턴 복사. | ✓ |
| 신규 모듈 scripts/orchestrator/supervisor_compress.py | 분리 모듈로 독립. 단위 테스트 용이. invokers.py import 추가 + 호출 삽입. 구조 조금 무거워짐. | |
| rubric-schema.json 기반 JSON schema validator + transformer | compression 을 schema transformation 으로 모델링. jsonschema dep 추가 필요 가능(미설치). 오버엔지니어링. | |

**User's choice:** invokers.py 내 _compress_producer_output() private (Recommended)

### Area 4 추가 질문?
**User's choice:** CONTEXT.md 작성 (Recommended)

---

## Claude's Discretion

- template 내 `<role>` / `<output_format>` 블록의 prose 세부 문구 (30명 각각 customized 하되 schema 준수)
- Wave 2 Producer Support 7 의 정확한 분할 (Plan 01 단계에서 producer 디렉토리 실측 기반)
- 7 plan 중 PLAN 01(template + schema) 외 Plan 04(skill-matrix) / Plan 05(FAILURES rotation) / Plan 07(supervisor-compress) 의 실행 순서 (wave pattern 과 병행 가능성)
- severity-based ordering 구현 시 rubric-schema.json 확장 여부 (research 결과 따라)
- compression char budget 기본값(2000) vs Claude CLI context limit 실측 기반 동적 계산

## Deferred Ideas

- **mandatory_reads hard enforcement** (Phase 13 조건부)
- **ClaudeAgentProducerInvoker compression** (Phase 11 retry-nudge 와 중복, Phase 13+ 조건부)
- **frontmatter schema_version 확장** (YAGNI)
- **_imported_from_shorts_naberal.md 500줄 cap 적용** (Phase 3 D-14 sha256-lock 영구 면제)
- **단일 batch commit 방식** (Wave 기반 탈락)
- **Phase 11 SC#1 live smoke 재도전** (Phase 12 완결 후 별도 mini-phase)
- **skill-matrix forbidden 4단계 cell 값** (ROADMAP 3단 lock, AGENT.md <constraints> 블록 개별 명시로 대체)

---

*Phase: 12-agent-standardization-skill-routing-failures-protocol*
*Discussion log written: 2026-04-21*
