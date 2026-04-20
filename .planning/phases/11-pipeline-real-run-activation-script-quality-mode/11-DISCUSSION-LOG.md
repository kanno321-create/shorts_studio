# Phase 11: Pipeline Real-Run Activation + Script Quality Mode - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `11-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-04-21
**Phase:** 11-pipeline-real-run-activation-script-quality-mode
**Areas discussed:** Invoker fix approach, Adapter graceful degrade scope, Wrapper UX format, SCRIPT-01 implementation boundary
**Mode:** Executive delegation ("욜로모드로 묻지말고 진행") — 대표님 선 일괄 위임 → 4 parallel code-mapping agents → AI 최고 품질 기준 locked decisions

---

## Gray Area Selection Turn

**User prompt:** "Phase 11에서 어떤 영역을 상세히 논의하시겠습니까? (복수 선택)"

| Option | Description | Selected |
|--------|-------------|----------|
| Invoker 수정 방식 (PIPELINE-01) | stdin piping / argv reorder / Agent SDK | ✓ |
| Adapter degrade 범위 (PIPELINE-03) | 5개 전수 / 선별 / registry | ✓ |
| Wrapper UX 형식 (PIPELINE-04) | .bat / .ps1+.cmd / Python launcher | ✓ |
| SCRIPT-01 옵션 B/C 구현 경계 | Phase 11 완료 / Phase 12 분리 | ✓ |

**User's freeform response:** "난 개발에대해서 잘모르니까,, 전체코드를 완전히 맵핑한 후 제대로 실행되게해라"

**User's follow-up:** "욜로모드로 묻지말고 진행해줘"

**Notes:** 비개발자 대표님이 4 gray area 모두 선택 + 추가 질문 금지 + AI 최고 품질 기준 결정 위임. Phase 10 패턴(executive delegation)과 동일.

---

## Area 1: Invoker 수정 방식 (PIPELINE-01)

**Code map source:** parallel agent (a117de672277669e7) — read `invokers.py` 339 lines + dep manifest check + memory grep

| Option | Description | Selected |
|--------|-------------|----------|
| A — stdin piping | `subprocess.Popen(stdin=PIPE).communicate(input=user_prompt)`. `invokers.py:141-171` 단일 수정. Low risk. | ✓ |
| B — `--prompt` flag reorder | 역사적으로 Claude CLI에 `--prompt` 플래그 미기록. 검증 실패 가능성 높음. | |
| C — Claude Agent SDK migration | `claude_agent_sdk` 패키지. 하지만 `.claude/memory/project_claude_code_max_no_api_key.md` "anthropic/SDK 금지" 결정 있음(Max 구독 중복결제). | |

**User's choice:** Delegated to AI — Option A selected.

**Notes:**
- 대표님 Max 구독 billing 경로 불변성 최우선 → Option C는 memory 규율 위반 위험
- CLI 2.1.112 canonical form = stdin 또는 positional 중 택일. 에러 "Input must be provided through stdin or prompt argument" = 현 positional argv를 CLI가 더 이상 인식 못함
- Windows argv 길이 한계(AGENT.md body ~수KB) 자동 회피 보너스
- Phase 9.1 smoke는 mock invoker 기반 — real-run 첫 실증 지점

---

## Area 2: Adapter graceful degrade 범위 (PIPELINE-03)

**Code map source:** parallel agent (a6423677305cd5c23) — read 5 adapter `__init__` + pipeline site L210-235

| Option | Description | Selected |
|--------|-------------|----------|
| A — pipeline-site 통일 wrap | 4개(Kling/Runway/Typecast/ElevenLabs) `shorts_pipeline.py:210-213`을 Phase 9.1 shotstack/nanobanana/ken_burns(L214-235) 패턴으로 wrap. 1 파일 ~20줄. | ✓ |
| B — 선별 wrap (현 .env 부재 키만) | 조건부 wrap. .env 변경 시 재발. | |
| C — Adapter registry + lazy 전역 refactor | 5+ 파일 touch. 244/244 regression 위험. | |

**User's choice:** Delegated to AI — Option A selected.

**Notes:**
- 발견된 defect (D-07): Shotstack adapter도 adapter 내부(`shotstack.py:81-97`)에서 eager ValueError. 대표님 세션 #28 즉석 패치는 **pipeline site(L214-218)에만** 반영됨 → adapter 내부는 변경 없음
- Phase 9.1이 adapter 내부를 건드리지 않고 pipeline site에서만 처리한 선례 동일 적용
- MagicMock 주입 테스트 seam 보존 핵심 (244/244 phase04 GREEN baseline)
- Option C 전역 refactor는 Phase 12+ deferred로 이동

---

## Area 3: Wrapper UX 형식 (PIPELINE-04)

**Code map source:** parallel agent (afdfc264a959c0a6f) — glob .bat/.ps1/.cmd/.sh + Win11 policy 확인 + argparse 라인 분석

| Option | Description | Selected |
|--------|-------------|----------|
| A — .bat 단독 | 1 파일. `.env` multi-line 값(API key `=` 포함) `for /f` 파싱 취약. | |
| B — .cmd bootstrap + .ps1 engine | 2 파일. `.cmd`가 `-ExecutionPolicy Bypass`로 `.ps1` 시작. PS `Get-Content + regex`로 `.env` 안전 파싱. try/catch + Read-Host pause-on-error. | ✓ |
| C — Python launcher (run.py) | py assoc 불안정. ImportError 시 창 즉시 닫힘(input() 도달 전). | |

**User's choice:** Delegated to AI — Option B selected.

**Notes:**
- Windows 11 `CurrentUser` 기본 PS ExecutionPolicy = `Restricted` → `.ps1` 더블클릭 시 Notepad 열림 → `.cmd`로 부트스트랩 필수
- 기존 `scripts/schedule/windows_tasks.ps1` 컨벤션 계승 (Korean block comments, `-NoProfile`, absolute ScriptRoot)
- 대표님 "관리자 권한 불필요 + 창 안 꺼짐" 명시 요구에 B가 가장 robust
- `.env` 파싱을 PS regex로 이관하여 orchestrator `_load_dotenv_if_present()`와 이중 안전망

---

## Area 4: SCRIPT-01 옵션 B/C 구현 경계

**Code map source:** parallel agent (a97dd35580c5f02e3) — read NLM_2STEP_TEMPLATE.md + query.py + scripter AGENT.md(212줄) + 예상 구현 범위 산정

| Option | Description | Selected |
|--------|-------------|----------|
| X1 — Phase 11 내 B/C 완전 구현 | REQ SCRIPT-01 원문 "선택된 옵션 구현까지 완료" 리터럴 준수. 9-10 plan sprawl 위험. | |
| X2 — skeleton stub + Phase 12 분리 | Drift 위험 (A-5 `TODO(next-session)` 패턴 유사). | |
| X3 — Phase 11 pre-commit to Option A baseline + Phase 12 조건부 spawn | Phase 11 narrow focus 유지. B/C 선택 시 Phase 12 자동 발행. | ✓ |

**User's choice:** Delegated to AI — Option X3 selected.

**Notes:**
- REQ SCRIPT-01 원문 "평가 후 구현까지 완료" 논리 모순 — 평가는 영상 1편 **발행 후** 트리거되므로 동일 phase 내 후속 구현 시간 부재
- X3는 REQ amendment 권고 포함 ("옵션 선정 + Phase 12 조건부 발행"으로 REQUIREMENTS.md 수정) — plan-phase 첫 과제
- `scripts/notebooklm/query.py`는 **이미 multi-notebook 호환**(D-4 per Plan 06-06, `notebook_id` 인자 필수) — 옵션 B 구현 시 query.py 자체 변경 불요
- Phase 11 발행 영상 1편은 **옵션 A 산출물**로 고정 (현 scripter agent Claude Opus prompt-based duo dialogue 유지)

---

## Side-Effect Decisions Emerged from Code Mapping

### PIPELINE-02 `.env` auto-load approach
- **Zero-dep 파서 선택** — `scripts/orchestrator/__init__.py`에 `_load_dotenv_if_present()` 추가
- 근거: repo root에 `requirements.txt` / `pyproject.toml` 부재 — python-dotenv 외부 dep 추가는 harness 의존성 변경 필요. Zero-dep가 실행 단순성 보장
- `.env` 부재 시 silently skip, 중복 호출 멱등

### argparse `--session-id` 완화
- `required=True` → `required=False, default=None` + `session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")`
- 이유: wrapper가 session-id 자동 주입하지 않아도 Python단에서 생성. 더블클릭 UX 보강 + smoke test CLI 호환 유지

### Shotstack adapter defect (D-07)
- 발견: `shotstack.py:81-97`이 실제로는 여전히 eager ValueError. 대표님 세션 #28 "즉석 graceful degrade 패치"는 pipeline site만 반영된 상태
- Phase 11 조치: pipeline site 4개 wrap 통일 시 shotstack도 동일 블록 재정비 (adapter 내부는 Phase 12+ deferred)

---

## Claude's Discretion (AI 재량 영역)

- Plan 실행 Wave 구조 (Phase 9.1/10과 동일 Wave 1~4 discipline 권장)
- 각 Plan의 구체적 테스트 케이스 설계
- `run_pipeline.ps1` 세부 에러 메시지 문구 (대표님 친화 Korean)
- `_load_dotenv_if_present()` 함수 주석/docstring 스타일
- Phase 11 full smoke 실 발행 cost 추적 방식 (cap 없이 실비 기록)
- D-19 REQUIREMENTS.md amendment 문구

---

## Deferred Ideas

### Phase 12 조건부 (SCRIPT-01 옵션 B/C 선택 시)
- Phase 12: NLM 2-Step Scripter Redesign (옵션 B)
- Phase 12 대안: Shorts/Longform 2-mode 분리 (옵션 C)

### Phase 12+ 독립 후속
- Adapter registry + lazy instantiation 전역 refactor (PIPELINE-03 Option C)
- Phase 04/08 retrospective VERIFICATION.md (ROADMAP SC#6 optional)
- Shotstack adapter 내부 lazy 근본 수정

### 로드맵 backlog
- REQ SCRIPT-01 원문 amendment 공식 처리 (D-19)

### Reviewed Todos (not folded — already scoped to `phase-regression-cleanup`)
- D10-01-DEF-01, D10-03-DEF-01, D10-03-DEF-02, D10-06-DEF-01
