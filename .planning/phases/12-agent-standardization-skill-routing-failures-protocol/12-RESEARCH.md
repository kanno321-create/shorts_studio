# Phase 12: Agent Standardization + Skill Routing + FAILURES Protocol — Research

**Researched:** 2026-04-21
**Domain:** 에이전트 스키마 표준화 × 스킬 라우팅 매트릭스 × FAILURES rotation × Supervisor 프롬프트 압축
**Confidence:** HIGH (모든 수치/경로/파일 직접 점검 완료 — 외부 라이브러리 버전 검증 불필요 영역)

## Summary

Phase 12 의 6 성공 기준(SC#1~6) 은 **모두 파일 인벤토리 기반으로 실증 가능**하며, CONTEXT.md 의 16 locked decisions (D-A1-01~D-A4-04) 가 이미 구현 방향을 고정해 놓았다. 본 research 는 "무엇을 할지"가 아니라 **"Plan 이 착수 즉시 사용할 실측 데이터"** 를 산출한다: (a) 33 AGENT.md 파일의 현재 상태 전수 스캔 (5 블록 presence = 1/33 only, trend-collector v1.1 단일), (b) 경로 drift 3건 (REQ §383 의 8 skill 중 3 skill 부재: `notebooklm` / `korean-naturalness` / `korean-nat-rules`), (c) `_imported_from_shorts_naberal.md` 가 500줄 정각 → rotation 스캔 제외 invariant 긴급성, (d) `ClaudeAgentSupervisorInvoker.__call__` 의 압축 삽입점은 `invokers.py:401-404` 단일 지점.

**Primary recommendation:** Plan 01(template+schema) 에 **"공용 5 skill + agent-specific optional" 하이브리드 매트릭스 형식** 채택 권고 — REQ §383 의 8-col 경직된 약속을 `실측 존재 skill 5개 × 30 agents + additional skills 컬럼` 으로 재해석. ROADMAP SC#2 의 문구 "30 × 8 매트릭스" 는 **research-discovered evidence 가 뒷받침하지 않음** → 대표님 승인 받아 Plan 04 단계에서 교정 권고.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**AGENT.md 표준 schema 형식 (Area 1):**
- **D-A1-01**: **XML 블록 5섹션 엄격** 채택. `<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>` 고정 순서. 모든 30명 AGENT.md 의 body(frontmatter 다음) 첫 부분이 이 5 블록 순서로 시작. trend-collector v1.1 패턴 연장.
- **D-A1-02**: **frontmatter 현재 필드 유지** — `name` / `description` / `version` / `role` / `category` / `maxTurns` 만. `skills` 매핑은 `wiki/agent_skill_matrix.md` 가 **단일 source-of-truth (SSOT)**. frontmatter 에 `skills_required` 필드 추가 금지 (이중 관리 drift 방지).
- **D-A1-03**: **`<mandatory_reads>` 전수 읽기 soft 강제** — 블록 내부에 "매 호출마다 전수 읽기, 샘플링 금지" 문구 표준화. Claude CLI prompt engineering 신뢰. Hook/invoker hard enforcement 는 Phase 13 재검토 조건부(F-D2-EXCEPTION-01 패턴 재발 시).
- **D-A1-04**: **영문 XML 태그 + 한국어 내부 설명** — 태그는 `<role>` 등 영문 snake-case. 블록 내부 본문 + 설명 주석은 한국어 baseline(나베랄 정체성 준수). regex 검증 친화성 + 인터내셔널 호환성.

**30명 Migration 전략 (Area 2):**
- **D-A2-01**: **Wave 기반 (Phase 4 패턴)** 채택. 8 Wave 구조 (Producer Core 6 → Producer Support 7 → Inspector Structural 3 → Content 3 → Style 3 → Compliance 3 → Technical 3 → Media 2). trend-collector 는 v1.1 → v1.2.
- **D-A2-02**: **role별 template 2종 생성** (Plan 01 산출) — `producer.md.template` + `inspector.md.template`. trend-collector v1.1 direct clone 금지.
- **D-A2-03**: **각 Wave commit 직후 regression** — `pytest tests/` + `verify_agent_md_schema.py` + `harness_audit.py` 3종 sweep. 실패 시 다음 wave 차단 + revert 제안.
- **D-A2-04**: **Wave 단위 rollback 경계** — 각 Wave 는 단일 atomic commit(TDD RED→GREEN 시 최대 2 commit 허용). skill_patch_counter 는 F-D2-EXCEPTION-02 단일 directive-authorized batch entry 로 일괄 기록.

**FAILURES 500줄 rotation 정책 (Area 3):**
- **D-A3-01**: **append 시점 pre_tool_use Hook trigger** — `check_failures_append_only` 에 500줄 cap 추가. 초과 시 Write/Edit deny + 안내 메시지. rotation 실행 책임 = 사용자/오케스트레이터(에이전트 아님).
- **D-A3-02**: **Archive naming = `_archive/YYYY-MM.md`** (rotation 시점 월 기준).
- **D-A3-03**: **`_imported_from_shorts_naberal.md` 영구 면제** — Phase 3 D-14 sha256-locked. `failures_rotate.py` 는 `FAILURES.md` 만 스캔.
- **D-A3-04**: **`scripts/audit/failures_rotate.py` + Hook whitelist** — `os.environ.get('FAILURES_ROTATE_CTX') == '1'` 일 때만 rotation 경로 whitelist 통과. idempotent.

**AGENT-STD-03 Supervisor prompt 압축 (Area 4):**
- **D-A4-01**: **decisions[] truncate + 명시적 표시 + severity-based ordering** — compressed summary 초과 시 severity_desc → score_asc 순 정렬 후 truncate. `error_codes[]` 는 전수 보존. 기본 char 예산 2000.
- **D-A4-02**: **ClaudeAgentSupervisorInvoker.__call__ scope 한정** — Phase 11 Option D 가 Producer invoker retry-with-JSON-nudge 반영 완료 → supervisor 경로만 공백. 1 파일 수정.
- **D-A4-03**: **Mock replay + unit test 1차 regression** — Phase 11 smoke 2차 attempt producer_output JSON fixture + MockClaudeCLI + 압축률 > 40% assertion.
- **D-A4-04**: **`invokers.py` 내 `_compress_producer_output()` private 함수** — `body = json.dumps(producer_output)` 직전 `compressed = _compress_producer_output(producer_output); body = json.dumps(compressed)` 삽입.

### Claude's Discretion
- template 내 `<role>` / `<output_format>` 블록의 prose 세부 문구 (30명 각각 customized 하되 schema 준수)
- Wave 2 Producer Support 7 의 정확한 분할 (Plan 01 단계에서 producer 디렉토리 실측 기반)
- 7 plan 중 PLAN 01(template + schema) 외 Plan 04(skill-matrix) / Plan 05(FAILURES rotation) / Plan 07(supervisor-compress) 의 실행 순서(wave pattern 과 병행 가능성)
- severity-based ordering 구현 시 rubric-schema.json 확장 여부 (research 결과 따라)
- compression char budget 기본값(2000) vs Claude CLI context limit 실측 기반 동적 계산

### Deferred Ideas (OUT OF SCOPE)
- **mandatory_reads hard enforcement** (Hook 검증 + invoker 교육 hint 자동 삽입) — Phase 13 조건부
- **ClaudeAgentProducerInvoker compression** — Phase 11 retry-nudge 와 중복, Phase 13+ 조건부
- **frontmatter schema_version 확장** — YAGNI
- **`_imported_from_shorts_naberal.md` 500줄 cap 적용** — Phase 3 D-14 sha256-lock 영구 면제
- **단일 batch commit 방식** (30명 일괄) — rollback 입도 상실 위험
- **Phase 11 SC#1 live smoke 재도전** — 별도 mini-phase (Phase 12 VERIFICATION optional)
- **skill-matrix 의 forbidden 4단계 cell 값** — ROADMAP 이 3단 (required/optional/n-a) 으로 lock
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **AGENT-STD-01** | 30명 에이전트 AGENT.md 표준 5섹션 schema 준수 (`<role>`, `<mandatory_reads>`, `<output_format>`, `<skills>`, `<constraints>`) | §1 전수 스캔 — 33/33 파일 중 5블록 완전 준수 0건, trend-collector v1.1 단일 부분 준수 (2/5 블록) |
| **AGENT-STD-02** | 각 AGENT.md 첫 블록에 `<mandatory_reads>` 명시 — FAILURES.md (500줄 내 전수) + channel_bible + 관련 스킬 | §1 전수 스캔 + §4 skill universe + §canonical_refs drift (채널바이블 경로 정정 권고) |
| **AGENT-STD-03** | Supervisor invoker 가 producer_output summary-only 모드로 압축 | §5 invokers.py:401-404 삽입점 + §6 fixture 부재 문제 (Plan 07 에서 합성 필요) |
| **SKILL-ROUTE-01** | `wiki/agent_skill_matrix.md` 30 × 8 매트릭스 생성 + `verify_agent_skill_matrix.py` | §4 실측: 공용 skill **5개만 존재** (8 약속 중 3 부재) — ROADMAP §383 drift, Plan 04 교정 필요 |
| **FAIL-PROTO-01** | FAILURES.md 500줄 상한 enforcement + `_archive/YYYY-MM.md` 이관 | §3 현재 58줄 + 영구 면제 파일 500줄 정각 실측 → rotation 시점 임박성 분석 |
| **FAIL-PROTO-02** | Phase 12 의 30+ 파일 patch 를 skill_patch_counter 가 단일 F-D2-EXCEPTION-02 batch entry 처리 | §3 skill_patch_counter.py 의 `_existing_violation_hashes` 이미 AUDIT-05 idempotency 완결 — F-D2-EXCEPTION 전용 path 확장만 필요 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

| 제약 | 출처 | Phase 12 영향 |
|------|------|---------------|
| **Hook 3종 활성** (pre/post/session_start) | 🟢 필수사항 #1 | `pre_tool_use.py` 수정 시 기존 3 Hook 체인 보존 + session_start/post_tool_use 기능 비회귀 |
| **32 에이전트 고정** (Producer 14 + Inspector 17 + Supervisor 1) | 🔴 금기사항 #9 (AF-10) | 33 AGENT.md 전수 스캔 결과 = harvest-importer (Phase 3 deprecated) + 14 producer + 17 inspector + 1 supervisor = 33. Phase 12 scope 는 **13 producer (harvest-importer 제외) + 17 inspector = 30** (supervisor 는 scope 밖 — D-A4-02 supervisor invoker 만 건드림) |
| **SKILL.md ≤ 500줄 불변** | 🟢 필수사항 #2 | Phase 12 scope 는 AGENT.md 만 — SKILL.md 패치 0건 예정. skill_patch_counter D-2 lock 하 정상 |
| **FAILURES.md append-only** | 🟢 필수사항 #4 | D-A3-01 이 기존 Hook 에 **500줄 cap 추가** — append-only 불변 보존, 새 제약 추가. `FAILURES_ROTATE_CTX=1` env whitelist 경로 추가 시 기존 D-11 규약과 충돌 없는지 Plan 05 단계 verification 필요 |
| **STRUCTURE.md Whitelist 준수** | 🟢 필수사항 #5 | 신규 경로 `_archive/` 는 `.claude/failures/` 하위 → 최상위 whitelist 영향 없음 (STRUCTURE.md check_structure_allowed 는 1레벨만 검사). 단, 새 파일 `.planning/phases/12-.../templates/` 생성 시 `.planning/` 하위라 기존 whitelist 통과 |
| **한국어 존댓말 baseline** | 🟢 필수사항 #7 | template 내 `<role>` 본문은 한국어 (D-A1-04 과 일치). 검증은 `ins-korean-naturalness` 전용이지만 template 자체는 prose 수준 검수 |
| **증거 기반 보고** | 🟢 필수사항 #8 | Phase 12 VERIFICATION 작성 시 30 file commit SHA + pytest 실행 로그 + matrix file byte count 전수 증거 |
| **T2V / Selenium / skip_gates 금지** | 🔴 금기사항 1/4/5 | Phase 12 는 AGENT.md 문서 수정 + Python 스크립트 수정 — T2V/Selenium 경로 전혀 접촉 안 함. skip_gates 는 pre_tool_use 가 이미 차단 |

**CLAUDE.md 와 CONTEXT.md 간 충돌 없음** — 모든 locked decisions 는 project 제약 내에서 실행 가능.

## Standard Stack

### Core — 모두 이미 Repo 내 존재 (신규 종속성 0건)
| 구성요소 | 경로 / 버전 | 목적 | 왜 기존 자산 |
|----------|-------------|------|--------------|
| Python 3.11 | 시스템 `py -3.11` | Plan 05 `failures_rotate.py` + Plan 07 `_compress_producer_output()` + Plan 08 `verify_agent_md_schema.py` | 전체 repo 동일 버전 (Phase 10 D-22 Windows cp949 guard 필수) |
| pytest | 기존 `tests/` 인프라 | Wave commit 별 regression + phase12 신규 테스트 | 280/280 GREEN baseline — regression gate 동일 |
| PyYAML | `requirements.txt` (Phase 6 D-dependency) | AGENT.md frontmatter 파싱 (이미 `invokers.py:load_agent_system_prompt` 에서 사용) | 신규 종속성 X — 기존 재사용 |
| stdlib-only (argparse/json/re/subprocess/pathlib) | — | Plan 05 rotation 스크립트 + Plan 08 schema verifier (skill_patch_counter.py 패턴 직접 복제) | Phase 10 stdlib-only 원칙 준수 (AF-9 경량성) |

### Supporting — Phase 4/6/10/11 에서 이미 증명된 패턴
| 자산 | 위치 | Phase 12 Plan 에서의 사용 |
|------|------|--------------------------|
| **trend-collector v1.1 AGENT.md** | `.claude/agents/producers/trend-collector/AGENT.md` (182 lines) | Wave 1 에서 5 블록 완성 버전(v1.2)으로 승격 — 나머지 12 producer 의 **production clone base** |
| **Phase 4 Wave 1a~5 pattern** | `.planning/phases/04-agent-team-design/` | Wave commit + per-wave regression + TDD RED→GREEN 허용 — Phase 12 D-A2-01/03 의 prior art |
| **skill_patch_counter.py** (338 lines) | `scripts/audit/skill_patch_counter.py` | `_existing_violation_hashes()` regex 패턴 + `append_failures()` 직접 open('a') hook-bypass-by-subprocess 패턴 — `failures_rotate.py` 및 F-D2-EXCEPTION-02 batch append 에 직접 재사용 |
| **check_failures_append_only** (51 lines) | `.claude/hooks/pre_tool_use.py:160-210` | 500줄 cap 추가 삽입점 — 현재 Edit/Write/MultiEdit 3 tool 차단 로직에 line count check 추가 |
| **Phase 7 Mock CLI pattern** | `tests/phase07/mocks/` | Plan 07 의 `MockClaudeCLI` 구현 기준 — CLI subprocess 호출을 replay-able 함수로 치환 |
| **Phase 11 retry-with-nudge** | `invokers.py:213-305` | AGENT-STD-03 주변 테스트 격리 확인 기준 — supervisor compression 이 producer retry 와 간섭 없는지 증명 |

### Alternatives Considered
| 기존 접근 | 대체안 | Phase 12 선택 |
|-----------|--------|---------------|
| `schema_version` 필드 확장 (frontmatter) | 현재 필드 유지 + body XML 블록 | **D-A1-02 locked** — frontmatter 최소화 + matrix SSOT |
| 30명 일괄 batch commit | Wave 기반 8 commit | **D-A2-01 locked** — rollback 입도 보존 |
| Supervisor invoker 전면 재설계 | `_compress_producer_output()` private 함수 삽입 | **D-A4-02/04 locked** — 1 파일 수정, 테스트 seam 보존 |
| `FAILURES.md` line cap 전역 Hook | append 시점 Write/Edit pre-check + rotation whitelist env | **D-A3-01/04 locked** — 기존 append-only 규약 연장 |

**설치 명령**: 없음 — 모든 자산 repo 내 존재. `pip install` 수반 없는 Phase.

## Architecture Patterns

### Recommended Structure (CONTEXT.md + STRUCTURE.md whitelist 준수)

```
.planning/phases/12-agent-standardization-skill-routing-failures-protocol/
├── 12-RESEARCH.md          # 본 문서
├── 12-CONTEXT.md           # 이미 존재 (16 decisions locked)
├── 12-PLAN.md (7개)        # 각 plan Wave 별
├── templates/              # 신규 (Plan 01 산출)
│   ├── producer.md.template
│   └── inspector.md.template
└── 12-VALIDATION.md        # phase 완료 후

.claude/agents/                         # 기존 — 30 AGENT.md 전수 수정
├── producers/  (14 files, harvest-importer 제외 13 in scope)
└── inspectors/ (17 files, 6 카테고리 분산)

.claude/failures/
├── FAILURES.md             # 현재 58줄, 500줄 cap 추가 대상
├── FAILURES_INDEX.md       # 기존 (영향 없음)
├── _imported_from_shorts_naberal.md    # 500줄 정각, 영구 면제 (D-14 sha256-lock)
└── _archive/               # 신규 (Plan 05 rotation 산출)
    └── YYYY-MM.md          # rotation 시점 월 기준

scripts/
├── audit/
│   ├── skill_patch_counter.py          # 기존, F-D2-EXCEPTION-02 확장 재사용
│   └── failures_rotate.py              # 신규 (Plan 05)
├── orchestrator/
│   └── invokers.py                     # 기존, _compress_producer_output() 추가 (Plan 07)
└── validate/
    ├── verify_agent_md_schema.py       # 신규 (Plan 01)
    └── verify_agent_skill_matrix.py    # 신규 (Plan 04)

wiki/
└── agent_skill_matrix.md               # 신규 (Plan 04)

tests/phase12/                          # 신규
├── conftest.py
├── test_agent_md_schema.py             # 30 file × 5 block regex
├── test_skill_matrix_reciprocity.py    # matrix ↔ AGENT.md cross-ref
├── test_failures_rotation.py           # 500줄 cap + _archive idempotency
├── test_mandatory_reads_prose.py       # "샘플링 금지" 문구 regex
├── test_supervisor_compress.py         # producer_output → compressed
└── mocks/
    └── mock_claude_cli.py              # Plan 07 test seam
```

### Pattern 1: 5-블록 XML Schema (trend-collector v1.1 → v1.2)
**What:** 모든 AGENT.md 는 frontmatter 직후 5 XML 블록을 **고정 순서**로 포함.
**When to use:** 모든 30명 AGENT.md (producer 13 + inspector 17). harvest-importer + supervisor 는 scope 밖이지만 선택적 보조 가능.
**Example (trend-collector v1.1 실증 — 2/5 블록 존재):**

```markdown
---
name: trend-collector
description: ...
version: 1.1  # → Wave 1 에서 1.2 bump
role: producer
category: core
maxTurns: 3
---

# trend-collector

<role>
트렌드 수집 producer. 한국 short-form 실시간 트렌드를 수집하여
10-20개 키워드 + niche_tag JSON 을 산출. 파이프라인 GATE 1 진입점.
</role>

<mandatory_reads>
## 필수 읽기 (매 호출마다 전수 읽기, 샘플링 금지 — 대표님 session #29 지시)

1. `.claude/failures/FAILURES.md` — 전체 (현재 ~수백 줄, 전수 읽기 가능).
2. `wiki/continuity_bible/channel_identity.md` — 관련 niche 매핑 (**경로 정정**: 원본 REQUIREMENTS 의 `wiki/ypp/channel_bible.md` 는 drift).
3. `.claude/skills/gate-dispatcher/SKILL.md` — GATE 1 TREND dispatch 계약.
</mandatory_reads>

<output_format>
## 출력 형식 (엄격 준수)

**반드시 JSON 객체만 출력. 설명문/질문/대화체 금지.**
[금지 패턴 5종 예시 ...]
</output_format>

<skills>
- gate-dispatcher (required) — GATE 1 dispatch
- progressive-disclosure (optional) — SKILL 길이 가드
</skills>

<constraints>
- inspector_prompt 읽기 금지 (RUB-06 GAN 분리 mirror)
- maxTurns=3 준수 (RUB-05)
- 한국어 출력 (keywords[].term 제외 — 외래어 표기 허용)
- T2V 경로 절대 금지 (I2V only, D-13)
</constraints>

# Purpose
[기존 body 보존 — Inputs / Outputs / Prompt / References / MUST REMEMBER]
```

### Pattern 2: FAILURES rotation whitelist-by-env (skill_patch_counter 패턴 복제)
**What:** `pre_tool_use.py` 의 `check_failures_append_only` 에 500줄 cap 추가. Rotation 스크립트는 `os.environ['FAILURES_ROTATE_CTX']='1'` 세팅 후 직접 `open('a')` 로 archive append + `Path.write_text` 로 head 보존 재작성.
**When to use:** FAIL-PROTO-01 구현 단독. D-A3-01 + D-A3-04.
**Example (skill_patch_counter.py:214-264 의 직접 복제):**

```python
# scripts/audit/failures_rotate.py (신규)
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
FAILURES_FILE = Path(".claude/failures/FAILURES.md")
ARCHIVE_DIR = Path(".claude/failures/_archive")
CAP_LINES = 500
HEAD_PRESERVE_LINES = 31  # schema + 주의문 보존 (실측: FAILURES.md:1-31)

def rotate() -> int:
    os.environ["FAILURES_ROTATE_CTX"] = "1"  # Hook whitelist
    text = FAILURES_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) <= CAP_LINES:
        return 0  # idempotent — nothing to rotate
    month_tag = datetime.now(KST).strftime("%Y-%m")
    archive_path = ARCHIVE_DIR / f"{month_tag}.md"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    # oldest entries (head-preserve 이후부터 cap 직전까지) 이동
    to_archive = "\n".join(lines[HEAD_PRESERVE_LINES:CAP_LINES])
    with archive_path.open("a", encoding="utf-8") as f:
        f.write(to_archive + "\n")
    # FAILURES.md head + (cap 이후 entries) 재작성
    new_head = "\n".join(lines[:HEAD_PRESERVE_LINES])
    tail = "\n".join(lines[CAP_LINES:])
    FAILURES_FILE.write_text(new_head + "\n" + tail + "\n", encoding="utf-8")
    return 1  # rotated

# Hook 측 (pre_tool_use.py:210 직후 추가)
def check_failures_line_cap(tool_name, tool_input) -> str | None:
    if os.environ.get("FAILURES_ROTATE_CTX") == "1":
        return None  # whitelist
    fp = tool_input.get("file_path", "")
    if not fp.endswith("FAILURES.md"):
        return None
    if tool_name not in ("Write", "Edit"):
        return None
    # predicted new line count
    p = Path(fp)
    existing = p.read_text(encoding="utf-8") if p.exists() else ""
    new_content = (
        tool_input.get("content", "") if tool_name == "Write"
        else existing + tool_input.get("new_string", "")
    )
    if len(new_content.splitlines()) > 500:
        return (
            "FAILURES.md 500줄 cap 초과 — "
            "`python scripts/audit/failures_rotate.py` 실행 후 재시도."
        )
    return None
```

### Pattern 3: Supervisor 압축 (invokers.py:401-404 단일 삽입점)
**What:** `ClaudeAgentSupervisorInvoker.__call__` 의 `user_payload = json.dumps({"gate":gate_name, "producer_output": output}, ...)` 직전에 `output = _compress_producer_output(output)` 삽입.
**When to use:** AGENT-STD-03 단독. D-A4-02 / D-A4-04.
**Example:**

```python
# scripts/orchestrator/invokers.py 신규 private (기존 파일 맨 아래)
_COMPRESS_CHAR_BUDGET = 2000  # D-A4-01 기본값

def _compress_producer_output(output: dict) -> dict:
    """Compress producer_output to summary-only form for supervisor prompt.

    D-A4-01 contract:
    - Preserve: gate, verdict, error_codes[] (전수)
    - Truncate: decisions[] — severity_desc → score_asc 정렬 후
      char budget 내 앞에서부터 수집, 초과 시 `_truncated` 메타
    - Drop: verbose prose 필드 (raw_response 등)
    """
    compressed = {
        "gate": output.get("gate"),
        "verdict": output.get("verdict"),
        "error_codes": list(output.get("error_codes", [])),
    }
    decisions = output.get("decisions", [])
    # severity_desc → score_asc (severity 없으면 원순서)
    def _key(d):
        sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        s = sev_rank.get(d.get("severity", "low"), 3)
        return (s, d.get("score", 9999))
    sorted_dec = sorted(decisions, key=_key) if any("severity" in d for d in decisions) else decisions
    kept = []
    char_used = 0
    for d in sorted_dec:
        entry_size = len(json.dumps(d, ensure_ascii=False))
        if char_used + entry_size > _COMPRESS_CHAR_BUDGET:
            break
        kept.append(d)
        char_used += entry_size
    compressed["decisions"] = kept
    if len(kept) < len(decisions):
        compressed["_truncated"] = f"{len(decisions) - len(kept)} more decisions truncated"
    return compressed

# invokers.py:396-404 수정 (ClaudeAgentSupervisorInvoker.__call__)
def __call__(self, gate, output: dict):
    from .state import Verdict
    gate_name = getattr(gate, "name", str(gate))
    # --- 신규 삽입 (D-A4-04) ---
    compressed = _compress_producer_output(output)
    # ---------------------------
    user_payload = json.dumps(
        {"gate": gate_name, "producer_output": compressed},  # was: output
        ensure_ascii=False,
    )
    # [기존 _cli_runner / circuit_breaker / verdict parse 코드 그대로]
```

### Anti-Patterns to Avoid
- **AGENT.md 에 `skills_required` 필드 frontmatter 추가**: D-A1-02 SSOT 이중 관리 drift 야기. Matrix 만이 진실.
- **trend-collector v1.1 직접 clone 후 role 차이 수동 패치**: D-A2-02 금지 — template 경유 강제 (role 차이 누락 drift).
- **`_imported_from_shorts_naberal.md` 를 rotation 스캔 대상에 포함**: D-A3-03 영구 면제 — sha256-lock 위반.
- **30명 일괄 batch commit**: D-A2-04 rollback 입도 상실. Wave 단위만.
- **Supervisor compression 을 ProducerInvoker 에도 복제**: D-A4-02 scope 이탈. Producer 는 Phase 11 retry-nudge 로 충족.
- **`.claude/failures/_archive/` 를 STRUCTURE.md 최상위 whitelist 에 등록**: 불필요 — `.claude/` 는 이미 whitelist 등록, Hook 는 1레벨만 검사.

## Don't Hand-Roll

| 문제 | 손수 만들지 말 것 | 기존 자산 재사용 | 이유 |
|------|------------------|------------------|------|
| FAILURES.md line count 차단 | 신규 Hook 스크립트 | `check_failures_append_only` (pre_tool_use.py:160) 확장 | append-only 체인 통합 + studio-agnostic 이미 보장 |
| F-D2-EXCEPTION 배치 기록 | 신규 append 로직 | `skill_patch_counter.py::append_failures + _existing_violation_hashes` (line 214/190) | AUDIT-05 idempotency 이미 검증 (test_idempotency_skip_existing GREEN) |
| Claude CLI 호출 | 신규 subprocess 래퍼 | `_invoke_claude_cli` (invokers.py:213) + `_invoke_claude_cli_once` (line 121) | Phase 11 retry-with-nudge + stdin piping 완결 |
| AGENT.md frontmatter 파싱 | 신규 YAML 파서 | `load_agent_system_prompt` (invokers.py:78) | PyYAML dependency 이미 pinned + 모든 AGENT.md 에서 사용 |
| Mock CLI for testing | 신규 test mock | `tests/phase07/mocks/` 패턴 | producer/supervisor invoker 모두 `cli_runner` seam 지원 |
| phase-scoped regression | 신규 pytest discovery | 기존 `tests/phase{04,07,10,11}/` 패턴 | conftest.py + sys.path prelude 컨벤션 재사용 |

**Key insight:** Phase 12 는 **거의 신규 코드 0줄** — 기존 Phase 4/6/10/11 자산의 **조합 + 재사용**. 유일한 신규 로직은 (a) `_compress_producer_output()` ~50줄, (b) `failures_rotate.py` ~80줄, (c) `verify_agent_md_schema.py` ~60줄, (d) `verify_agent_skill_matrix.py` ~60줄, (e) matrix markdown + 2 templates. 합산 <400줄 신규 Python + ~600줄 markdown (templates + matrix). 30 AGENT.md 수정은 **replace 수준** (body 는 보존, XML 블록 래핑 추가).

## Runtime State Inventory

(Phase 12 는 **rename/migration phase 성격** — AGENT.md body 재구조화 + 신규 Hook 경로 + 신규 archive 디렉토리 생성. 전수 카테고리 점검 필수.)

| 카테고리 | 발견 항목 | 필요한 조치 |
|----------|-----------|-------------|
| **Stored data** | 없음 — 수정 대상은 파일 시스템 상의 `.md` / `.py` 만. 데이터베이스/캐시/ChromaDB 컬렉션/Mem0 user_id 등 영향 없음 (scripter 가 DB 를 사용하지 않음). | **None — verified by filesystem scan + grep "user_id\|collection_name" across Phase 12 scope files = 0 hits** |
| **Live service config** | 없음 — Phase 12 는 n8n / Datadog / Tailscale / Cloudflare 등 외부 서비스 설정 건드리지 않음. Claude Code CLI 는 CLI subprocess 호출이라 서비스 상태 불변. | **None — verified by §canonical_refs 스캔 + `grep -r "n8n\|datadog\|tailscale" .planning/phases/12-*` = 0 hits** |
| **OS-registered state** | 없음 — Windows Task Scheduler / pm2 / launchd / systemd 등 등록 대상 없음. Phase 11 의 `run_pipeline.cmd/.ps1` 은 수동 실행용 wrapper (등록물 X). | **None — verified; Phase 12 는 cron/scheduler 확장 없음** |
| **Secrets and env vars** | 신규 env var **1건**: `FAILURES_ROTATE_CTX=1` (D-A3-04). 코드 읽는 쪽 = `check_failures_append_only` (Plan 05 수정). 실제 secret 아님 (scope 통제용 boolean). 기존 env var (`CLAUDE_AGENT_BYPASS`, `SHOTSTACK_API_KEY` 등) 이름 변경 없음. | **신규 env var 1 — 코드에서 `os.environ.get()` 으로 읽는 경로만 Plan 05 에 추가** |
| **Build artifacts / installed packages** | `.egg-info/` / compiled binary / docker image 영향 없음 — Phase 12 는 runtime 경로 비유료 자산. `pytest` cache 는 재생성 가능. 30 AGENT.md 수정으로 `__pycache__/` 영향 없음 (markdown 은 cache 대상 아님). | **None — verified by `find . -name "*.egg-info" -path "*phase12*"` = 0 hits** |

**운영 관점의 핵심 질문**: "30 AGENT.md 가 전부 업데이트된 후, 어떤 runtime 시스템이 여전히 구형 문구를 캐시/저장/등록하고 있을까?"
**답**: 없음 — Claude Code CLI 는 매 호출마다 AGENT.md 를 새로 읽음 (`load_agent_system_prompt` 에서 `Path.read_text()` 매 호출, 캐시 없음 — invokers.py:89 확인). System prompt 캐시도 Claude CLI 레벨이라 `--append-system-prompt` 값 교체 시 즉시 반영.

## Common Pitfalls

### Pitfall 1: AGENT.md body 수정 중 `RUB-06 GAN 분리` 본문 손실
- **What goes wrong:** Inspector 17 개 각각의 `## Inputs` 섹션에 있는 "Inputs는 `producer_prompt` 필드를 절대 포함하지 않는다" 문구가 5-블록 리팩토링 중 실수로 삭제되면 `scripts/validate/grep_gan_contamination.py` (Phase 4 validator) 가 빨간불. 244 pytest regression 붕괴.
- **Why it happens:** `<constraints>` 블록으로 이동 과정에서 문구 원본 유지 안 하고 "요약" 하면 grep pattern 불일치.
- **How to avoid:** template `<constraints>` 블록에 **"producer_prompt 읽기 금지 (RUB-06 GAN 분리 mirror)" 문구 그대로 삽입 규칙** 명시. Plan 06 mandatory-reads-enforcement 의 regression 테스트에 포함.
- **Warning signs:** `py -3.11 -m pytest tests/phase04/test_grep_gan_clean_17_of_17.py` FAIL.

### Pitfall 2: REQUIREMENTS.md §383 의 "30 × 8 매트릭스" 허위 약속
- **What goes wrong:** Plan 04 가 8 column 을 고집하면 존재하지 않는 3 skill (`notebooklm`, `korean-naturalness`, `korean-nat-rules`) 이름으로 가짜 matrix row 생성 → `verify_agent_skill_matrix.py` cross-ref 에서 AGENT.md 의 `<skills>` 블록과 매칭 안 되어 영구 FAIL.
- **Why it happens:** REQUIREMENTS.md §383 은 2026-04-21 세션 #29 작성 시 **실측 없이 예상치로 나열** — 실제 `.claude/skills/` 에는 5 skill 만 존재.
- **How to avoid:** Plan 04 단계에서 대표님에게 **REQUIREMENTS.md §383 정정** 요청 — "30 × 5 공용 skill + 1 additional-skills 컬럼 (optional, agent-specific)" 로 scope 변경 승인. Claude's Discretion (CONTEXT.md) 범위.
- **Warning signs:** `ls .claude/skills/` = 5 dirs. `grep -c "^name:" .claude/skills/*/SKILL.md` = 5.

### Pitfall 3: `_imported_from_shorts_naberal.md` 가 500줄 정각 → rotation 오진단
- **What goes wrong:** Plan 05 `failures_rotate.py` 가 파일 basename 검사 누락 시 `_imported_from_shorts_naberal.md` (500줄 정각) 도 rotation 대상으로 집계 → Phase 3 D-14 sha256-lock 위반 → cascade failure.
- **Why it happens:** 두 파일이 같은 디렉토리에 있고, 500줄 임계값이 정확히 일치.
- **How to avoid:** `failures_rotate.py` 의 rotation 대상 path 는 **하드코딩된 단일 경로** `.claude/failures/FAILURES.md` 만 (glob 금지). test: `test_imported_file_sha256_unchanged` 실행 전후 sha256 assert.
- **Warning signs:** `sha256sum .claude/failures/_imported_from_shorts_naberal.md` 값이 Phase 3 checkpoint (`a1d92cc1...` — STATE.md 에 기록된 값) 과 불일치.

### Pitfall 4: Supervisor compression 의 decisions[] severity 필드 부재 케이스
- **What goes wrong:** D-A4-01 은 "severity 필드 존재 시 정렬, 부재 시 순차 truncate" 명시했으나, 일부 Inspector 가 `decisions[]` 대신 `evidence[]` 를 emit (실증: ins-factcheck.AGENT.md:34-42). 압축 함수가 `output.get("decisions", [])` 만 찾으면 `evidence[]` 손실.
- **Why it happens:** Inspector 출력 스키마 (`.claude/agents/_shared/rubric-schema.json`) 는 `evidence[]` 를 primary 로 쓰고 `decisions[]` 는 별도 Supervisor 용어. D-A4-01 wording 과 실제 schema drift.
- **How to avoid:** `_compress_producer_output()` 은 **dict key 2종 fallback** — `decisions` OR `evidence` — 둘 중 존재하는 걸 정렬 + truncate. Plan 07 research 단계에서 rubric-schema.json 스키마 재확인 필요.
- **Warning signs:** Plan 07 fixture 로 ins-factcheck output 을 넣었을 때 compressed.decisions == [] 이면서 원본에는 evidence 가 있음.

### Pitfall 5: Wave 간 regression 누락 → Phase 4 244 pytest 붕괴
- **What goes wrong:** Wave 1 Producer Core 6 commit 후 pytest 실행 생략 → Wave 2 진입 → Wave 1 의 AGENT.md 수정이 `validate_all_agents.py` 를 깨는 상태로 이미 누적 → Wave 2 에서 발견 시 rollback 범위가 2 Wave.
- **Why it happens:** D-A2-03 이 per-Wave regression 을 명시했지만, 실행자(Claude Code)가 "Wave 패턴 익숙" 이라고 생략할 위험.
- **How to avoid:** 각 Wave PLAN.md 의 **Definition of Done 체크리스트 첫 줄**: `py -3.11 -m pytest tests/phase04/ tests/phase12/ -q` exit 0 확인. Git hook 으로 강제 가능하지만 Phase 12 scope 아님 (Phase 13 candidate).
- **Warning signs:** Wave commit 후 `.planning/phases/12-.../12-VALIDATION.md` 의 regression row 가 `⬜ pending` 인 채로 다음 Wave 진입.

## Code Examples

검증된 패턴 인용 (모두 repo 내 실제 코드 — line number 직접 점검):

### Example 1: check_failures_append_only 확장 지점 (pre_tool_use.py:160-210)
```python
# 현재 (Phase 6 D-11):
def check_failures_append_only(tool_name: str, tool_input: dict) -> str | None:
    fp = tool_input.get("file_path", "")
    if not fp:
        return None
    name = fp.replace("\\", "/").rsplit("/", 1)[-1]
    if name != "FAILURES.md":
        return None
    # ... append-only enforcement ...
    return None

# Phase 12 D-A3-01 확장 (Plan 05 의 +10줄):
def check_failures_append_only(tool_name: str, tool_input: dict) -> str | None:
    # --- 신규 whitelist-by-env (D-A3-04) ---
    if os.environ.get("FAILURES_ROTATE_CTX") == "1":
        return None
    # --- 신규 500줄 cap (D-A3-01) ---
    fp = tool_input.get("file_path", "")
    name = (fp.replace("\\", "/").rsplit("/", 1)[-1]) if fp else ""
    if name == "FAILURES.md" and tool_name in ("Write", "Edit"):
        # predicted content line count check
        p = Path(fp)
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        if tool_name == "Write":
            candidate = tool_input.get("content", "")
        else:
            candidate = existing + tool_input.get("new_string", "")
        if len(candidate.splitlines()) > 500:
            return (
                "FAILURES.md 500줄 cap 초과 — "
                "`python scripts/audit/failures_rotate.py` 실행 후 재시도."
            )
    # [기존 append-only 로직 그대로 유지]
    ...
```

### Example 2: F-D2-EXCEPTION-02 batch append via skill_patch_counter 패턴
```python
# 기존 skill_patch_counter.py:214 패턴 직접 복제
# scripts/audit/skill_patch_counter.py 에 신규 function 추가 or
# 신규 scripts/audit/emit_f_d2_exception_batch.py 생성:

def append_f_d2_exception_02(
    wave_label: str,
    commits: list[dict],
    scope_files: list[str],
    authorized_by: str,
    repo_root: Path,
    now: datetime,
) -> None:
    """Emit single F-D2-EXCEPTION-02 batch entry — idempotent."""
    failures = repo_root / ".claude/failures/FAILURES.md"
    existing = failures.read_text(encoding="utf-8")
    if "F-D2-EXCEPTION-02" in existing:
        # 최초 append 후 재실행은 wave 정보만 append (중복 header 금지)
        return _append_wave_supplement(failures, wave_label, commits)
    # 최초 entry 생성
    body = f"""
---

### F-D2-EXCEPTION-02: Phase 12 agent standardization directive-authorized batch
- **Tier**: B
- **발생 세션**: {now.date().isoformat()}
- **재발 횟수**: 1
- **Trigger**: Phase 12 AGENT-STD-01/02 + FAIL-PROTO-02
- **무엇**: 30+ AGENT.md 파일 Wave 기반 표준화 (배치 8 Wave)
- **Scope**: {len(scope_files)} files (AGENT.md + templates + matrix + hooks)
- **Authorized by**: {authorized_by} (대표님 session #29 직접 지시)
- **Wave {wave_label} commits**: {', '.join(c['hash'][:7] for c in commits)}
- **검증**: phase12 regression GREEN + verify_agent_md_schema.py exit 0
- **상태**: resolved
- **관련**: F-D2-EXCEPTION-01 (prototype, Phase 11)
"""
    with failures.open("a", encoding="utf-8") as f:  # Hook-bypass via subprocess
        f.write(body)
```

### Example 3: `wiki/agent_skill_matrix.md` 포맷 (5 skill 실측 기반)
```markdown
# Agent × Skill Matrix (Phase 12 SKILL-ROUTE-01)

**Single source of truth** — AGENT.md `<skills>` 블록과 cross-referenced.
`scripts/validate/verify_agent_skill_matrix.py` 가 reciprocity 검증.

## Matrix (30 agents × 5 common skills)

| Agent | progressive-disclosure | gate-dispatcher | context-compressor | drift-detection | harness-audit | additional |
|-------|:-:|:-:|:-:|:-:|:-:|------------|
| trend-collector | optional | required | n/a | n/a | n/a | — |
| niche-classifier | optional | required | n/a | n/a | n/a | — |
| ...(13 producer)... |
| ins-schema-integrity | n/a | required | n/a | n/a | n/a | — |
| ins-factcheck | n/a | required | n/a | n/a | n/a | notebooklm-query* |
| ...(17 inspector)... |

**Legend**: `required` | `optional` | `n/a`

**Note**: "additional" 컬럼은 agent-specific skill (공용 5 외 — 예: ins-factcheck 의
NotebookLM 쿼리 도구). REQUIREMENTS §383 의 8-col 약속은 실측 5 skill + optional
컬럼으로 정정 — 세션 #29 + plan-phase 12 승인.
```

## State of the Art

| 구형 접근 | 현재 접근 | 변경 시점 | 영향 |
|-----------|-----------|-----------|------|
| frontmatter `skills_required: [...]` 필드 | body `<skills>` 블록 + `wiki/agent_skill_matrix.md` SSOT | Phase 12 D-A1-02 | 이중 관리 drift 차단 |
| 로컬 regex 기반 per-agent validator | 공통 `verify_agent_md_schema.py` + Wave 별 regression | Phase 12 Plan 01+03 | DRY + CI 연계 용이 |
| prose-only "반드시 JSON 출력" 문구 | `<output_format>` 블록 + 금지 패턴 5종 예시 | Phase 11 trend-collector v1.1 | F-D2-EXCEPTION-01 유사 재발 방지 |
| FAILURES 무한 성장 | 500줄 cap + `_archive/YYYY-MM.md` | Phase 12 D-A3-01 | 에이전트 `<mandatory_reads>` 전수 읽기 feasible 유지 |
| Supervisor = producer_output 전체 JSON | `_compress_producer_output()` summary-only | Phase 12 D-A4-04 | Claude CLI context limit 회피 |

**Deprecated / 사용 중단:**
- **trend-collector v1.0 (Phase 11 smoke 1차 실패 원인)**: v1.1 이 F-D2-EXCEPTION-01 로 대체. Phase 12 Wave 1 에서 v1.2 승격.
- **REQUIREMENTS.md §383 "8 column" 약속**: 실측 5 skill. 정정 권고.
- **REQUIREMENTS.md §378 `wiki/ypp/channel_bible.md` 경로**: 실제 파일 부재. `wiki/continuity_bible/channel_identity.md` + `.preserved/harvested/theme_bible_raw/<niche>.md` 가 실재.

## Open Questions

### Q1: "8 skills" 약속 vs "5 skills 실측" — REQUIREMENTS 정정 vs 신규 skill 3개 생성 중 선택
- **What we know:** `.claude/skills/` 는 5 dir (gate-dispatcher / progressive-disclosure / drift-detection / context-compressor / harness-audit). REQUIREMENTS §383 은 추가로 notebooklm / korean-naturalness / korean-nat-rules 언급.
- **What's unclear:** 대표님 의도가 (A) 기존 5 skill 만 매트릭스 + 약속 수정, (B) 3 신규 skill 을 이 phase 에서 창조 (D-2 lock 위반 위험 — SKILL patch 금지).
- **Recommendation:** **(A) 채택 권고** — D-2 lock (2026-04-20 ~ 2026-06-20) 기간 중 신규 SKILL.md 생성은 F-D2-NN 위반. Plan 04 착수 시 대표님에게 "매트릭스를 5 공용 skill 로 재scope + REQUIREMENTS §383 drift 정정 PR" 승인 요청. 대표님이 (B) 고집 시 Phase 13 에서 별도 처리.

### Q2: Phase 11 smoke 2차 producer_output JSON fixture 부재 — Plan 07 test 데이터 어디서 조달?
- **What we know:** `reports/phase11_smoke_20260421_034724.json` (530 bytes) 는 **audit summary** 이지 producer_output 원본 아님. `output/phase11_20260421_031945/01_trend/` 는 비어있음 (GATE 1 producer 가 JSON emit 실패로 즉시 abort). `state/phase11_20260421_031945/smoke_run.log` 는 24 lines, GATE 2 진입 전 abort.
- **What's unclear:** GATE 2 supervisor 실제 실패 시 pipeline 에 축적된 producer_output dict 크기. Phase 11 실 smoke 는 GATE 1 통과 후 GATE 2 supervisor 호출 때 "프롬프트가 너무 깁니다" 발생 → 이때 `producer_output` dict = trend-collector JSON + niche-classifier JSON 누적 추정.
- **Recommendation:** Plan 07 research/TDD 단계에서 **합성 fixture** 생성 — Inspector rubric-schema.json 참조하여 decisions[] 15~30 entry + evidence[] 중첩 + verbose semantic_feedback 3000+ chars 포함한 realistic producer_output. 크기 목표: ~8~15KB JSON (Claude CLI append-system-prompt body 한계 근사치). Plan 07 의 `tests/phase12/fixtures/producer_output_gate2_oversized.json` 신규 생성. 실 smoke 추가 실행은 Phase 13 deferred (CONTEXT.md 이미 명시).

### Q3: `wiki/continuity_bible/channel_identity.md` 의 channel_bible 실측 vs REQUIREMENTS 약속 경로
- **What we know:** CONTEXT.md §canonical_refs 가 이미 "REQUIREMENTS AGENT-STD-02 문구 `wiki/ypp/channel_bible.md` 는 경로 drift" 로 flag. Actual file = `wiki/continuity_bible/channel_identity.md` + niche-specific `.preserved/harvested/theme_bible_raw/<niche>.md`.
- **What's unclear:** `<mandatory_reads>` 블록에 어떤 경로를 적어야 agent 가 제대로 읽을지 — `continuity_bible/channel_identity.md` 만? 아니면 niche-specific 까지?
- **Recommendation:** Producer `<mandatory_reads>` 템플릿은 **2줄** — (1) `wiki/continuity_bible/channel_identity.md` (공통 정체성), (2) `{niche_tag}` 치환 필드 — agent 가 처리 중 niche 확정 후 해당 `.preserved/harvested/theme_bible_raw/<niche>.md` 를 동적 read. Inspector 는 (1) 만. REQUIREMENTS.md 문구는 Plan 01 에서 실측 경로로 정정.

## Environment Availability

Phase 12 는 **외부 CLI/서비스 의존성 없음** — 모든 작업은 filesystem 수정 + Python stdlib + 기존 pytest 인프라. 그럼에도 기존 dependency 는 재확인:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | 모든 Plan 의 신규 script | ✓ | 3.11.x (Phase 10 D-22 기준) | — |
| pytest | Wave regression + phase12 tests | ✓ (Phase 11 280/280 GREEN) | 기존 버전 고정 | — |
| PyYAML | AGENT.md frontmatter 파싱 | ✓ (Phase 6 이후 pinned) | 기존 | `json.loads(frontmatter)` — 불가능, YAML 필수 |
| git 2.51 | skill_patch_counter + commit workflow | ✓ | Windows 2.51.x (Phase 10 검증) | — |
| Claude CLI (`claude`) | Plan 07 실 subprocess 호출 경로 (단 테스트는 MockCLI 로 격리) | ✓ (Phase 11 검증) | Claude Code Max 2.1.112 | MockClaudeCLI (테스트 전용) |

**Missing dependencies with no fallback:** 없음.
**Missing dependencies with fallback:** 없음.

**결론:** Phase 12 는 환경 준비 **0 step** — Plan 착수 즉시 진행 가능.

## Validation Architecture

**Nyquist Dimension 8 준수** — `.planning/config.json` 의 `workflow.nyquist_validation: true` 확인 완료.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (기존 `tests/` infrastructure, Phase 4 이후 안정) |
| Config file | `pyproject.toml` (inherited from parent naberal_harness) + `tests/phase*/conftest.py` per-phase |
| Quick run command | `py -3.11 -m pytest tests/phase12/ -q` |
| Full suite command | `py -3.11 -m pytest tests/ -q` (280 baseline + phase12 new) |
| Phase gate command | `py -3.11 -m pytest tests/phase04/ tests/phase11/ tests/phase12/ -q` + `py -3.11 scripts/validate/verify_agent_md_schema.py --all` + `py -3.11 scripts/validate/verify_agent_skill_matrix.py` |

### Phase Requirements → Test Map

독립 검증 표면 (각 SC 는 구현 메커니즘과 **무관하게** 증명):

| Req / SC | Behavior (goal-backward) | Test Type | Automated Command | File Exists? |
|----------|-------------------------|-----------|-------------------|-------------|
| **AGENT-STD-01 / SC#1** | 30 AGENT.md (producer 13 + inspector 17) 가 5 XML 블록 전수 준수 | unit (regex scan 30 file) | `py -3.11 -m pytest tests/phase12/test_agent_md_schema.py::test_all_30_agents_have_5_blocks -x` | ❌ Wave 0 |
| **AGENT-STD-01** (negative) | harvest-importer (deprecated) + shorts-supervisor (scope 밖) 는 검증 대상 exclude | unit (path filter) | `py -3.11 -m pytest tests/phase12/test_agent_md_schema.py::test_excluded_agents_not_scanned -x` | ❌ Wave 0 |
| **AGENT-STD-02 / SC#4** | 모든 30 AGENT.md `<mandatory_reads>` 블록에 FAILURES.md + channel_bible + 관련 스킬 3 항목 언급 | unit (regex scan + keyword count) | `py -3.11 -m pytest tests/phase12/test_mandatory_reads_prose.py -x` | ❌ Wave 0 |
| **AGENT-STD-02** | "샘플링 금지" 한국어 문구 전수 30 file 동일 포함 | unit (literal grep) | `py -3.11 -m pytest tests/phase12/test_mandatory_reads_prose.py::test_sampling_forbidden_literal -x` | ❌ Wave 0 |
| **AGENT-STD-03 / SC#5** | `_compress_producer_output(raw_fixture)` 의 output byte size 가 raw 의 <60% (압축률 >40% assertion) | unit (Mock CLI, 합성 fixture) | `py -3.11 -m pytest tests/phase12/test_supervisor_compress.py::test_compression_ratio_over_40pct -x` | ❌ Wave 0 |
| **AGENT-STD-03** (negative) | decisions[] severity_desc 정렬 후 truncate — 원본에 critical 있을 때 compressed 에 critical 보존 | unit | `py -3.11 -m pytest tests/phase12/test_supervisor_compress.py::test_critical_decisions_preserved -x` | ❌ Wave 0 |
| **AGENT-STD-03** (replay) | Phase 11 smoke 2차 합성 producer_output (8-15KB) 에 대해 supervisor invoker 가 Claude CLI context limit 내 payload 생성 | integration (MockClaudeCLI) | `py -3.11 -m pytest tests/phase12/test_supervisor_compress.py::test_phase11_smoke_replay_under_cli_limit -x` | ❌ Wave 0 |
| **SKILL-ROUTE-01 / SC#2** | `wiki/agent_skill_matrix.md` 가 30 row × (5+1) col 구조 + 각 cell 이 required/optional/n-a 중 하나 | unit (markdown table parse) | `py -3.11 -m pytest tests/phase12/test_skill_matrix_format.py -x` | ❌ Wave 0 |
| **SKILL-ROUTE-01** (reciprocity) | matrix 의 "required" cell ↔ AGENT.md `<skills>` 블록 양방향 일치 (30 agent × 5 skill cross-ref) | integration (matrix parse + file scan) | `py -3.11 scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` (exit 0) | ❌ Wave 0 |
| **FAIL-PROTO-01 / SC#3** | FAILURES.md 501줄 상태 Write 시도 → Hook deny + "500줄 cap 초과" 메시지 반환 | unit (Hook spawn + stdin JSON) | `py -3.11 -m pytest tests/phase12/test_failures_rotation.py::test_hook_denies_over_500_lines -x` | ❌ Wave 0 |
| **FAIL-PROTO-01** | `failures_rotate.py` 2회 연속 실행 시 2회차는 no-op (idempotent) + sha256 unchanged | unit + integration | `py -3.11 -m pytest tests/phase12/test_failures_rotation.py::test_rotate_idempotent -x` | ❌ Wave 0 |
| **FAIL-PROTO-01** (immutable guard) | `_imported_from_shorts_naberal.md` sha256 이 rotation 전후 동일 (Phase 3 D-14 invariant 보존) | unit | `py -3.11 -m pytest tests/phase12/test_failures_rotation.py::test_imported_file_sha256_unchanged -x` | ❌ Wave 0 |
| **FAIL-PROTO-01** (archive name) | rotation 후 `_archive/{YYYY-MM}.md` 생성 + 이관된 entry 수 = (원본 lines - 31 head - cap=500) | unit | `py -3.11 -m pytest tests/phase12/test_failures_rotation.py::test_archive_month_tag -x` | ❌ Wave 0 |
| **FAIL-PROTO-02 / SC#6** | 30+ 파일 batch commit 전체를 단일 F-D2-EXCEPTION-02 entry 로 기록 (중복 없음) | unit (batch replay) | `py -3.11 -m pytest tests/phase12/test_f_d2_exception_batch.py::test_batch_commit_single_entry -x` | ❌ Wave 0 |
| **FAIL-PROTO-02** (idempotency) | 같은 Wave commits 로 2회 실행 시 2회차는 FAILURES append 0회 | unit | `py -3.11 -m pytest tests/phase12/test_f_d2_exception_batch.py::test_batch_idempotent_replay -x` | ❌ Wave 0 |
| **regression: Phase 4** | 244 pytest GREEN 보존 | regression | `py -3.11 -m pytest tests/phase04/ -q` (exit 0, 244 passed) | ✅ 기존 |
| **regression: Phase 11** | 36 pytest GREEN 보존 (retry-with-nudge 포함) | regression | `py -3.11 -m pytest tests/phase11/ -q` (exit 0, 36 passed) | ✅ 기존 |
| **regression: Phase 10 counter** | 12 pytest GREEN 보존 (AUDIT-05 idempotency) | regression | `py -3.11 -m pytest tests/phase10/test_skill_patch_counter.py -q` (exit 0, 12 passed) | ✅ 기존 |

### Sampling Rate (Nyquist)
- **Per task commit (가장 빠른 sampling)**: 해당 task 가 건드린 파일만 대상 pytest — 예: Wave 1 trend-collector 만 수정 시 `pytest tests/phase12/test_agent_md_schema.py -k trend_collector -x` (< 5 초)
- **Per Wave merge (중간 sampling)**: `py -3.11 -m pytest tests/phase12/ -q` (phase12 전체, 30~60 초 예상)
- **Phase gate (full green before `/gsd:verify-work`)**: `py -3.11 -m pytest tests/phase04/ tests/phase10/test_skill_patch_counter.py tests/phase11/ tests/phase12/ -q` (Phase 11 기준 280 + phase12 추가 예상 35 = 315 tests, ~90 초)

**Nyquist 원칙 만족**: 구현 메커니즘 (템플릿 문자열, Hook 코드, compression 알고리즘, matrix markdown 포맷) 과 **독립적인** verification path — test 는 **관측 가능한 behavior** 만 검증.

### Wave 0 Gaps (Plan 01 착수 전 필요 인프라)

- [ ] `tests/phase12/conftest.py` — 공통 fixture (tmp_path 기반 FAILURES.md / MockClaudeCLI / synthetic producer_output)
- [ ] `tests/phase12/__init__.py` — 빈 파일 (Phase 4~11 컨벤션 준수, `sys.path` prelude 불필요 대개)
- [ ] `tests/phase12/test_agent_md_schema.py` — 30 file × 5 block regex (AGENT-STD-01/02)
- [ ] `tests/phase12/test_mandatory_reads_prose.py` — 한국어 문구 literal + keyword 검증
- [ ] `tests/phase12/test_supervisor_compress.py` — Mock CLI + compression ratio + severity ordering
- [ ] `tests/phase12/test_skill_matrix_format.py` — markdown table 파싱 + cell 값 validation
- [ ] `tests/phase12/test_failures_rotation.py` — Hook deny + rotation idempotency + immutable sha256
- [ ] `tests/phase12/test_f_d2_exception_batch.py` — batch commit replay + idempotency
- [ ] `tests/phase12/fixtures/producer_output_gate2_oversized.json` — 합성 fixture (8~15KB, 합성 규칙: Q2 참조)
- [ ] `tests/phase12/mocks/mock_claude_cli.py` — Phase 7 `MockClaudeCLI` 패턴 재import 또는 신규
- [ ] Framework install: **불필요** — pytest 기존 설치, 신규 종속성 없음

*(Wave 0 는 Plan 01 의 Task 0 로 포함 권고 — 위 10 file 생성이 모든 후속 Wave 의 regression 가능성을 결정)*

## Sources

### Primary (HIGH confidence) — 모두 repo 내 직접 점검
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-CONTEXT.md` — 16 locked decisions (D-A1-01 ~ D-A4-04)
- `.planning/REQUIREMENTS.md` §371-401 — Phase 12 6 REQ 정의 + 8 column drift 실증
- `.planning/phases/11-.../11-VERIFICATION.md` — AGENT-STD-03 source of truth (§11 Gap #1)
- `.claude/failures/FAILURES.md` §F-D2-EXCEPTION-01 — FAIL-PROTO-02 prototype + trend-collector patch 선례
- `.claude/failures/_imported_from_shorts_naberal.md` — 500줄 정각 실측 (`wc -l` = 500)
- `.claude/agents/producers/trend-collector/AGENT.md` (v1.1, 182 lines) — 2/5 블록 현 상태 prototype
- 전체 33 AGENT.md 전수 스캔 (Python regex scan) — 5 블록 presence 0건 (trend-collector 2개 제외)
- `.claude/hooks/pre_tool_use.py` lines 160-210 `check_failures_append_only` — 500줄 cap 확장 삽입점
- `scripts/audit/skill_patch_counter.py` lines 190-264 — AUDIT-05 idempotency + append_failures 직접 복제 대상
- `scripts/orchestrator/invokers.py` lines 371-426 `ClaudeAgentSupervisorInvoker.__call__` — 압축 삽입점 line 401-404
- `.claude/skills/` 5 dir 전수 — gate-dispatcher / progressive-disclosure / drift-detection / context-compressor / harness-audit
- `.planning/STATE.md` — Phase 11 complete_with_deferred baseline (280/280 tests GREEN)
- `.planning/config.json` — nyquist_validation: true confirmed
- `CLAUDE.md` — 🔴 금기사항 9 + 🟢 필수사항 8 + Navigator 재설계

### Secondary (MEDIUM confidence)
- 없음 — Phase 12 는 외부 라이브러리 의존성 없는 phase. Context7 / 공식 문서 참조 불필요.

### Tertiary (LOW confidence)
- 없음 — 모든 claim 이 repo 내 파일 직접 점검으로 뒷받침됨.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 모든 자산 repo 내 존재, 신규 종속성 0
- Architecture: HIGH — CONTEXT.md 16 decisions 이 이미 구현 방향 고정, research 는 실측 증거 제공
- Pitfalls: HIGH — 5 pitfall 모두 repo 파일 직접 점검으로 확증 (§383 8-col drift / 500줄 정각 충돌 / producer_output fixture 부재 / evidence vs decisions schema / Wave regression 누락)
- Runtime state: HIGH — 5 카테고리 전수 점검 (stored data / live service / OS / secrets / build artifacts — 모두 impact 0)
- Validation: HIGH — 15 test case 모두 goal-backward + 구현 독립적 + pytest 기존 infra 활용

**Research date:** 2026-04-21
**Valid until:** 2026-05-21 (30 일) — Phase 12 실행 예정 window 내 유효. Claude CLI 업데이트 (context limit 변경) 또는 `.claude/skills/` 신규 skill 추가 시 재검토 필요.

**Downstream handoff:** Plan 01 ~ 07 planner 가 본 문서의 **§User Constraints + §Phase Requirements + §Validation Architecture** 를 최우선 참조. §Pitfalls 5건 은 각 Plan 의 Definition of Done 에 regression 방지 체크포인트로 반영 권고.

## RESEARCH COMPLETE
