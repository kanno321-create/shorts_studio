# FAILURES.md — Append-Only Reservoir

> **D-11:** Append-only via `check_failures_append_only` in `.claude/hooks/pre_tool_use.py`.
>          Modification of existing lines is physically blocked (deny). Only Write with
>          existing-content-as-prefix or new-entry append is allowed.
> **D-14:** Separate from `_imported_from_shorts_naberal.md` (Phase 3 sha256-locked).
>          This file never modifies or duplicates that file — only accumulates Phase 6+ entries.
> **D-2 저수지 원칙:** New failures accumulate here. 30-day aggregation (Plan 09) scans both
>                     this file and `_imported_from_shorts_naberal.md` to surface patterns
>                     (recurrence ≥ 3 → `SKILL.md.candidate` dry-run).

## Entry Schema

```
### FAIL-NNN: [one-line summary]
- **Tier**: A/B/C/D
- **발생 세션**: YYYY-MM-DD 세션 N
- **재발 횟수**: 1
- **Trigger**: [what triggers this failure]
- **무엇**: [what went wrong, observable symptom]
- **왜**: [root cause, invariant violated]
- **정답**: [correct behavior, invariant restored]
- **검증**: [how to verify the fix holds — grep/test/metric]
- **상태**: [observed | resolved | recurring]
- **관련**: [links to other FAIL-IDs, FAILURES_INDEX.md category, wiki nodes]
```

## Entries

(none yet — first Phase 6+ entry goes below this header line; do NOT modify the
above schema or any existing entry once added — append-only Hook will deny.)

### FAIL-ARCH-01: docs/ARCHITECTURE.md Phase status 라인 stale — 다른 세션 "Phase 8" 오인
- **Tier**: B
- **발생 세션**: 2026-04-21 세션 #28 (발견), 최초 drift 발생 2026-04-20 Phase 9 Plan 01 작성 시점
- **재발 횟수**: 1
- **Trigger**: Phase 완결 시 `docs/ARCHITECTURE.md` L6 `**Phase status:**` 헤더 업데이트 누락
- **무엇**: Phase 9 Plan 01 시점 "Phase 8 완결 / Phase 9 진행 중" 으로 작성된 status 라인이 Phase 9 + 9.1 완결 + Phase 10 Entry Gate PASSED 이후에도 갱신 안 됨. 다른 Claude 세션이 이 파일을 읽고 "Phase 8" 이라고 오인 — 대표님 "다른 나베가 페이즈 8이라는데,,,실제로는 10을 작업하고있거든" 질문 유발
- **왜**: `Last updated:` 라인은 자동 갱신되지만 status 문장은 수동 갱신 필요. Phase gate 진입·완결 checkpoint 에 해당 라인 패치가 포함 안 됨
- **정답**: 각 Phase VERIFICATION 완결 시 `docs/ARCHITECTURE.md` L6 status 라인을 새 상태로 교체 (예: "Phase 9 + 9.1 완결, Phase 10 Entry Gate PASSED"). 세션 #28 에서 수동 패치 완료 (commit `e57f891` 포함)
- **검증**: `grep -n "Phase status" docs/ARCHITECTURE.md` → 현재 Phase 번호 vs `.planning/ROADMAP.md` [x] 마커 일치 여부. 세션 시작 session_start.py Hook 에 "ARCHITECTURE.md Phase status 일치 검사" 추가 후보
- **상태**: resolved (세션 #28 패치) — 재발 방지는 Phase 완결 체크리스트에 라인 업데이트 추가 필요
- **관련**: commit `e57f891` / `WORK_HANDOFF.md` 세션 #28 완료 항목 / `CLAUDE.md` Navigator 재설계와 동반 발견

### F-D2-EXCEPTION-01: trend-collector AGENT.md directive-authorized patch — JSON-only output enforcement
- **Tier**: B
- **발생 세션**: 2026-04-21 세션 #29 (Phase 11 Wave 3 remediation)
- **재발 횟수**: 1
- **Trigger**: Phase 11 라이브 smoke 1차 실행 (session_id `phase11_20260421_031945`) GATE 1 TREND 진입 시 trend-collector 가 JSON 대신 한국어 대화체("대표님, 어떤 결정 정보를 필요합니다...") 반환 → `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` → `RuntimeError: Producer 'trend-collector' JSON 미준수 (대표님)` → 파이프라인 149.74s 만에 중단, gate_file_count=0
- **무엇**: Phase 11 smoke 전체 0/14 GATE 완주. 비용 $0.00 (early abort). reports/phase11_smoke_phase11_20260421_031945.json 에 실패 audit 기록. Root cause: trend-collector AGENT.md 에 출력 형식 엄격 명시 부재 — Claude CLI 가 해석 요청 받은 것으로 오인하여 대화체로 응답
- **왜**: trend-collector AGENT.md v1.0 에 "JSON만 출력" 지시는 있었으나 (a) 금지 패턴 예시 부재, (b) `<mandatory_reads>` 블록으로 과거 실패 전수 인지 강제 없음, (c) invoker 측 retry-with-nudge 부재 — 1차 실패 즉시 GATE 실패로 직행
- **정답**: trend-collector AGENT.md v1.1 로 업그레이드 (`<mandatory_reads>` + `<output_format>` 블록 + 금지 패턴 5종 예시 + Invoker nudge 계약 명시). D-2 저수지 원칙은 SKILL patch 금지 (학습 충돌 방지 목적) 를 의미하지만, 본 patch 는 **"인프라 구조 확립"** — 학습이 아닌 출력 형식 강제 + 실패 사례 인지 주입이므로 directive-authorized exception 으로 처리
- **Scope**: 1 파일 (`.claude/agents/producers/trend-collector/AGENT.md`, v1.0 → v1.1)
- **Authorized by**: 대표님 직접 지시 (세션 #29 "둘다" 응답 = Option D 승인 + Phase 12 발의 양쪽)
- **검증**: (1) trend-collector AGENT.md 의 frontmatter version 이 1.1 이고 `<mandatory_reads>` + `<output_format>` 블록 존재. (2) `grep -n "JSON 전용 출력" .claude/agents/producers/trend-collector/AGENT.md` 가 MUST REMEMBER §8 매칭. (3) Phase 11 smoke 재실행 시 GATE 1 TREND 가 JSON 반환으로 통과 (또는 실패 시 invoker retry-with-nudge 가 흡수).
- **상태**: resolved (patch 적용 완료) — Phase 12 에서 30명 전수 표준화 예정 (AGENT-STD-01/02 REQ)
- **Follow-up**: Phase 12 의 30+ 파일 patch 는 F-D2-EXCEPTION-02 (directive-authorized batch) 단일 entry 로 처리 예정 — FAIL-PROTO-02 REQ
- **관련**: Phase 11 Plan 11-06 / reports/phase11_smoke_phase11_20260421_031945.json / Phase 12 AGENT-STD-01, AGENT-STD-02, FAIL-PROTO-02 REQ-IDs

### F-D2-EXCEPTION-02 — Wave 2 Producer batch (Phase 12 agent standardization directive-authorized batch, 2026-04-21)
- **Tier**: B
- **발생 세션**: 2026-04-21 세션 #29 (Phase 12 Plan 02 Wave 2)
- **재발 횟수**: 1
- **Trigger**: Phase 12 AGENT-STD-01 + AGENT-STD-02 + FAIL-PROTO-02 REQ 이행 — 13 Producer AGENT.md 를 Plan 01 template 기반 5-block schema (v1.2) 로 일괄 승격
- **무엇**: 13 Producer AGENT.md 패치 (niche-classifier, researcher, director, scripter, metadata-seo, scene-planner, shot-planner, script-polisher, voice-producer, asset-sourcer, thumbnail-designer, assembler, publisher). trend-collector 는 Plan 01 Task 4 에서 별도 migration 완료 (Phase 12 합계 14/14 producer v1.2). D-2 Lock (2026-04-20 ~ 2026-06-20) 기간 중 SKILL patch 금지 원칙 대상이 아님 — 본 patch 는 AGENT.md (역할 정의) 이며 SKILL.md (학습/스킬) 와 다른 레이어. 다만 대량 (30+ 파일 경로) 패치 이므로 FAIL-PROTO-02 하에 F-D2-EXCEPTION-02 단일 batch entry 로 일괄 기록 (30+ 개별 F-D2-NN 생성 회피).
- **Scope**: 13 AGENT.md (`.claude/agents/producers/{niche-classifier,researcher,director,scripter,metadata-seo,scene-planner,shot-planner,script-polisher,voice-producer,asset-sourcer,thumbnail-designer,assembler,publisher}/AGENT.md`)
- **Commits**: 7 commits, marker `[plan-02]` 전수 부착 — `93a285b` (niche-classifier), `9ed8f31` (researcher), `2089449` (director+scripter+metadata-seo), `1226750` (scene-planner+shot-planner+script-polisher), `22b13bb` (voice-producer+asset-sourcer+thumbnail-designer), `172f623` (assembler+publisher), `2d1aa23` (finalize: maxTurns Phase 4 regression fix + test populate)
- **Authorized by**: 대표님 세션 #29 (Phase 12 발의 승인, Option D "둘다" 응답 — F-D2-EXCEPTION-01 trend-collector 단일 patch + Phase 12 30+ 파일 batch 양쪽 승인)
- **왜**: Plan 02 는 Phase 11 F-D2-EXCEPTION-01 (trend-collector JSON 미준수) 재발 차단의 구조적 인프라 확립. 13 producer 전수 `<output_format>` JSON 스키마 + 금지 패턴 5종 + `<mandatory_reads>` 전수 읽기 literal (`매 호출마다 전수 읽기, 샘플링 금지`) + RUB-06 mirror 주입 — 개별 skill 학습 patch 가 아닌 역할 정의 표준화
- **정답**: 13 producer 모두 5-block schema (`<role>` → `<mandatory_reads>` → `<output_format>` → `<skills>` → `<constraints>`) + `version: 1.2` frontmatter + body prose (Purpose/Inputs/Outputs/Prompt/References/MUST REMEMBER) 보존. Phase 4 RUB-05 maxTurns matrix 준수 (전 producer maxTurns=3; scripter/asset-sourcer/publisher 는 finalize commit 2d1aa23 에서 Rule 1 자동 수정)
- **검증**: (1) `py -3.11 scripts/validate/verify_agent_md_schema.py --all` → 14/14 producer PASS (17 inspector FAIL 은 Plan 12-03 scope). (2) `py -3.11 -m pytest tests/phase12/test_agent_md_schema.py -v` → 16 passed (2 collective + 14 parametrized). (3) `py -3.11 -m pytest tests/phase04/ -q` → 244 passed (Phase 4 RUB-05 matrix 회귀 0). (4) `py -3.11 -m pytest tests/phase11/ -q` → 36 passed. (5) `git log --grep='\[plan-02\]' --oneline | wc -l` → 7 (commit marker 전수 부착).
- **상태**: resolved (Plan 02 Wave 2 완결, 2026-04-21) — Plan 12-03 에서 17 inspector 동일 패턴으로 migration 예정 시 F-D2-EXCEPTION-03 별도 entry (또는 본 entry supplement) 로 기록
- **관련**: Plan 12-01 (`.claude/agents/producers/trend-collector/AGENT.md` v1.2 prototype, commit `0ebb5e9`) / Plan 12-04 (`wiki/agent_skill_matrix.md` reciprocity SSOT, commit `43000b8`) / F-D2-EXCEPTION-01 (Phase 11 prototype single-file patch) / Phase 12 VALIDATION.md

### F-D2-EXCEPTION-02 — Wave 3 Inspector batch (Phase 12 agent standardization directive-authorized batch supplement, 2026-04-21)
- **Tier**: B
- **발생 세션**: 2026-04-21 세션 #29 (Phase 12 Plan 03 Wave 3)
- **재발 횟수**: 1 (F-D2-EXCEPTION-02 supplement entry — Wave 2 와 동일 batch 카테고리, Wave 별 marker 분리 기록 per Plan 02 SUMMARY follow-up note)
- **Trigger**: Phase 12 AGENT-STD-01 + AGENT-STD-02 + FAIL-PROTO-02 REQ 이행 — 17 Inspector AGENT.md 를 Plan 01 inspector.md.template 기반 5-block schema (v1.1) 로 일괄 승격. 6 sub-wave (Structural 3 → Content 3 → Style 3 → Compliance 3 → Technical 3 → Media 2) 로 atomic 커밋 분할.
- **무엇**: 17 Inspector AGENT.md 패치 (ins-schema-integrity, ins-timing-consistency, ins-blueprint-compliance, ins-factcheck, ins-narrative-quality, ins-korean-naturalness, ins-thumbnail-hook, ins-tone-brand, ins-readability, ins-license, ins-platform-policy, ins-safety, ins-audio-quality, ins-render-integrity, ins-subtitle-alignment, ins-mosaic, ins-gore). Plan 02 Wave 2 14 producer 와 합쳐 Phase 12 합계 31/31 AGENT.md v1.x compliant. D-2 Lock 기간 중 SKILL patch 금지 원칙 대상이 아님 — 본 patch 는 AGENT.md (역할 정의) 이며 SKILL.md (학습/스킬) 와 다른 레이어. F-D2-EXCEPTION-02 supplement entry 형식 — Wave 2 와 동일 batch 카테고리이므로 별도 F-D2-EXCEPTION-03 entry 신설 회피 (Plan 02 SUMMARY follow-up flag 준수).
- **Scope**: 17 AGENT.md (`.claude/agents/inspectors/{structural,content,style,compliance,technical,media}/<inspector>/AGENT.md`)
- **Commits**: 6 commits, marker `[plan-03]` 전수 부착 — `b97cfac` (Wave 3a Structural 3), `80d24b0` (Wave 3b Content 3), `654a7d8` (Wave 3c Style 3), `674dbea` (Wave 3d Compliance 3), `78f6293` (Wave 3e Technical 3), `fd1e0c3` (Wave 3f Media 2 — 17/17 milestone)
- **Authorized by**: 대표님 세션 #29 (Phase 12 발의 승인, Option D "둘다" 응답 — Wave 2 와 동일 권한 범위에서 Wave 3 진행)
- **왜**: Plan 03 은 Plan 02 의 Producer 표준화 보완 — Inspector GAN 분리 mirror 양방향 완성 (Producer: inspector_prompt 읽기 금지 / Inspector: producer_prompt 읽기 금지). 17 inspector 전수 `<output_format>` JSON 스키마 (rubric-schema.json) + 금지 패턴 5종 + `<mandatory_reads>` 전수 읽기 literal (`매 호출마다 전수 읽기, 샘플링 금지`) + RUB-06 역방향 mirror + Plan 04 matrix SSOT reciprocity (Structural 3 의 progressive-disclosure literal 부재 — Issue #1 fix) 주입
- **정답**: 17 inspector 모두 5-block schema (`<role>` → `<mandatory_reads>` → `<output_format>` → `<skills>` → `<constraints>`) + `version: 1.1` frontmatter + body prose (Purpose/Inputs/Outputs/Prompt/References/MUST REMEMBER) 보존. Phase 4 RUB-05 maxTurns matrix 준수 (ins-factcheck=10, ins-tone-brand=5, ins-blueprint-compliance/ins-timing-consistency/ins-schema-integrity=1, 나머지 12=3). Plan 04 matrix reciprocity 정합 (Structural 3 의 `progressive-disclosure` literal 부재 — `verify_agent_skill_matrix.py --fail-on-drift` exit 0)
- **검증**: (1) `py -3.11 scripts/validate/verify_agent_md_schema.py --all` → 31/31 PASS (14 producer + 17 inspector, Plan 12 SC#1 GREEN). (2) `py -3.11 -m pytest tests/phase12/test_agent_md_schema.py -v` → 37 passed (2 collective + 14 producer + 17 inspector + 3 structural-no-progressive-disclosure + 1 total-31). (3) `py -3.11 -m pytest tests/phase04/ -q` → 244 passed (Phase 4 RUB-05 matrix + GAN_CLEAN 17/17 회귀 0). (4) `py -3.11 scripts/validate/verify_agent_skill_matrix.py --fail-on-drift` → exit 0 (155/155 cells reciprocate). (5) `git log --grep='\[plan-03\]' --oneline | wc -l` → 6 (commit marker 전수 부착). (6) `git log --grep='\[plan-03\]' --name-only --pretty=format: | grep -c "AGENT.md"` → 17 (정확히 inspector scope).
- **상태**: resolved (Plan 03 Wave 3 완결, 2026-04-21) — Phase 12 AGENT-STD-01 SC#1 + AGENT-STD-02 + FAIL-PROTO-02 SC 충족. Plan 04 matrix SSOT 와 31/31 reciprocity 완성. RUB-06 양방향 GAN 분리 mirror 구조적 보장.
- **관련**: F-D2-EXCEPTION-02 Wave 2 (Producer 13 batch, commits `93a285b..2d1aa23`) / Plan 12-01 (template + verifier + trend-collector v1.2 prototype) / Plan 12-04 (`wiki/agent_skill_matrix.md` reciprocity SSOT) / Plan 12-06 (mandatory_reads prose validator — `매 호출마다 전수 읽기, 샘플링 금지` literal 검증 대상 17개 inspector 추가) / Phase 4 `tests/phase04/test_maxturns_matrix.py::EXPECTED_NON_DEFAULT` (authoritative source) / Phase 12 VALIDATION.md

### F-LIVE-SMOKE-JSON-NONCOMPLIANCE — Claude CLI 자연어 반환 + nudge retry 빈 응답 (세션 #30, 2026-04-22)
- **Tier**: A (Live smoke 경로 차단, 영상 생성 실패)
- **발생 세션**: 2026-04-22 세션 #30 (Phase 13 live smoke retry 2차 시도, `overseas_crime_sample_20260422_retry`)
- **재발 횟수**: 1 (신규)
- **Trigger**: Phase 15 Wave 1 15-02 encoding fix 적용 후 live smoke 재시도. 대표님 "해외범죄" 샘플 쇼츠 1편 제작 목표.
- **무엇**: TREND gate supervisor 첫 호출 (50초 소요 — CLI 실제 실행) 이 JSON schema 무시하고 자연어 반환 ("TREND gate PASS, 다음 게이트 NICHE 로 진행합니다, 대표님"). `_MAX_NUDGE_ATTEMPTS=3` retry 모두 stdout 비어있음 (`claude CLI stdout 비어있음 — --json-schema 응답 미수신`). attempt 2 의 3 retries 모두 동일 empty stdout → 총 115초 FAIL.
- **Scope**: `scripts/orchestrator/invokers.py` supervisor 경로 + `_SUPERVISOR_JSON_SCHEMA` + Claude Code CLI 2.1.63 `--json-schema` 엄수
- **Commits**: 없음 (실 과금 $0, no production code change this attempt). Evidence: `.planning/phases/13-live-smoke/evidence/smoke_e2e_overseas_crime_sample_20260422_retry.json` (status=FAILED, wall=115.2s, dispatched=0)
- **Authorized by**: 대표님 세션 #30 "실제 업로드용 테스트이므로 해외 범죄 1건 제작해라 쇼츠"
- **왜**: Phase 15 Wave 1 encoding fix 가 argv 전달 문제 해소는 성공했으나 Claude Code CLI (대화형) 의 `--json-schema` 엄수가 brittle — 특히 한국어 system prompt + long supervisor AGENT.md body 조합에서 자연어 응답 반환. Nudge retry 시 CLI 가 empty stdout 을 반환하는 패턴은 session/quota 경계에서 발생 가능.
- **정답 (미실행, 다음 세션 예정)**: Option A "수동 혼합 경로" — 대표님 승인 — `--skip-supervisor` flag 1개 추가 (runner 에 5 lines 패치) + 대표님 수동 대본 주입 (`--revise-script`) + VOICE/ASSETS/UPLOAD 실 API 경로 보존. Supervisor quality gate 는 영상 제작 달성 후 점진 복구.
- **검증 (미실행)**: 다음 세션 live run 시 13 gate dispatched + 최종 video_id + cleanup + budget ≤ $5 확인 후 resolved 로 flip.
- **상태**: open (다음 세션 #31 에서 해소)
- **관련**: Phase 11 SC#1 defer (live smoke 1차 defer 원인 — 초기 encoding bug) / Phase 12 AGENT-STD-03 `_compress_producer_output` (producer output 압축은 scope OK, 그러나 supervisor AGENT.md body / Claude CLI JSON 엄수는 scope 밖) / Phase 15 Wave 1 15-02 (encoding fix, 본 F 이후 유지) / `.claude/memory/feedback_infinite_loop_avoidance.md` (추가 Phase 발의 전 goal 재시도 우선)

### F-META-HOOK-FAILURES-NOT-INJECTED — 원칙 있어도 Hook wiring 없으면 무의미 (세션 #30, 2026-04-22)
- **Tier**: A (meta-infrastructure, 모든 실패 학습 경로의 상위 조건)
- **발생 세션**: 2026-04-22 세션 #30 (대표님 직접 지적)
- **재발 횟수**: 1 (신규)
- **Trigger**: 대표님 세션 #30 종료 직전 지적 — "원칙에 실패하면 실패리스트에 올려서 교훈까지 제공하고 그걸 참조한뒤 작업시작하게하는거 아니가??"
- **무엇**: FAILURES.md append-only 원칙 (D-11 Hook 강제) + entry schema (무엇/왜/정답/검증/상태) 는 모두 존재했으나, **세션 시작 시 자동 주입이 안 됨**. `session_start.py` 는 WORK_HANDOFF + MEMORY + env keys + Navigator coverage 만 주입하고 FAILURES 최근 entry 는 노출 안 함. 결과: F-LIVE-SMOKE-JSON-NONCOMPLIANCE 같은 open 실패가 다음 세션에서 자동으로 안 보여 같은 실수 반복 위험. FAILURES_INDEX.md 의 "Phase 6+ Entries" 섹션도 "(none yet)" 그대로 stale — F-D2-EXCEPTION-01/02 (Wave 2, 3), FAIL-ARCH-01, F-LIVE-SMOKE-JSON-NONCOMPLIANCE 모두 미등재.
- **왜**: (1) 원칙 명문화와 hook wiring 이 분리 작업이라는 인식 부재 — CLAUDE.md "FAILURES.md append-only" 룰만 적고 session_start.py 에 load_recent_failures() 함수 연결 누락. (2) FAILURES_INDEX.md 는 수동 관리 파일인데 새 entry 추가 시 INDEX 동기화 프로토콜이 빠짐 (기존 "Update Protocol" 섹션은 있으나 실행 안 됨). (3) CONFLICT_MAP A-6 (skip_gates=True) 처럼 pre_tool_use.py regex 차단 같은 "코드 강제" 가 FAILURES 참조 경로에는 없음 — 텍스트 지시가 아니라 hook 강제로 전환됐어야 함.
- **정답**: (1) `session_start.py` 에 `load_recent_failures()` 함수 추가 — FAILURES.md 에서 `### F-` 헤더 기준 entry split, open 상태 entry 전수 + 최근 5건 자동 주입 (800자 초과 시 truncate). (2) `FAILURES_INDEX.md` Phase 6+ Entries 섹션에 5 entry (FAIL-ARCH-01, F-D2-EXCEPTION-01, F-D2-EXCEPTION-02 Wave 2/3, F-LIVE-SMOKE-JSON-NONCOMPLIANCE, F-META-HOOK-FAILURES-NOT-INJECTED) 등재. (3) 본 entry 를 append-only 경로로 추가하여 스스로 다음 세션 #31 시작 시 open 상태로 노출되도록 함. (4) CLAUDE.md Session Init 섹션에 "session_start.py 가 FAILURES 자동 주입" 명시. **상위 원칙**: 새 원칙 추가 시 "코드 강제 wiring" 을 동반 작업으로 요구 — 텍스트 지시 단독은 drift 유발.
- **검증**: (1) `python .claude/hooks/session_start.py` 실행 → `context` 필드에 "📛 최근 실패 사례 + 교훈" 섹션 포함 + open 1건 + 최근 5건 entry block 존재. (2) `grep -c "^### F-" .claude/failures/FAILURES.md` 와 `grep -c "See .F-" .claude/failures/FAILURES_INDEX.md` 값 일치 (drift 0). (3) 세션 #31 실제 시작 시 system reminder 에 본 entry 포함 여부 수동 확인 — 없으면 hook wiring 재검토.
- **상태**: resolved (session_start.py + FAILURES_INDEX.md 동시 업데이트, 세션 #30 2026-04-22)
- **Lessons (핵심 교훈)**:
  1. **원칙 ≠ 실행 — wiring 동반 필수**: 새 룰 추가 시 텍스트 지시가 아니라 hook/script 코드 강제로 전환.
  2. **FAILURES 는 자동 주입 = 학습 루프 완결 조건**: 실패 등재만 하고 다음 세션 자동 노출이 없으면 학습 안 됨.
  3. **INDEX drift 금지**: 새 entry append 시 FAILURES_INDEX.md 동시 업데이트 프로토콜 준수.
  4. **Meta-failure 등재 가치**: "인프라 gap 자체" 를 실패로 등재하면 다음 세션이 그 gap 의 재발을 차단.
- **관련**: `session_start.py` v2 (2026-04-22 patch, load_recent_failures 추가) / `FAILURES_INDEX.md` Phase 6+ 섹션 / `.claude/memory/feedback_lenient_retry_over_strict_block.md` (같은 날짜 동반 원칙, nudge retry 철학) / `.claude/memory/feedback_infinite_loop_avoidance.md` (infrastructure 확장 지연 금지, 본 entry 는 확장이 아니라 gap 수리이므로 합치)

### F-SUPERVISOR-VERDICT-TYPE-MISMATCH — state.Verdict (Enum) vs gate_guard.Verdict (dataclass) latent bug (세션 #31, 2026-04-22)
- **Tier**: A (live smoke 차단, 영상 생성 실패)
- **발생 세션**: 2026-04-22 세션 #31 (BTK 해외범죄 쇼츠 live run 1차 시도, `btk_v1_session31`)
- **재발 횟수**: 1 (신규 — F-LIVE-SMOKE-JSON-NONCOMPLIANCE 우회 후 드러난 2차 장애)
- **Trigger**: 세션 #30 합의 `--skip-supervisor` flag 로 F-LIVE-SMOKE JSON 에러 회피 후 TREND gate dispatch 에서 `TypeError: asdict() should be called on dataclass instances`. attempts 1 + 2 양쪽 동일 에러, 총 0.1초 (즉시 실패).
- **무엇**: BTK 해외범죄 샘플 쇼츠 0/13 gate 완주. 비용 $0 (early abort, pre-seed + auto-PASS 만 동작). `_AutoPassSupervisorInvoker` 가 `state.Verdict.PASS` (Enum) 반환 → `GateGuard.dispatch` 내부 `asdict(verdict)` 가 Enum 에 실패. Evidence: `.planning/phases/13-live-smoke/evidence/smoke_e2e_btk_v1_session31.json` + `.planning/phases/15-system-prompt-compression-user-feedback-loop/evidence/live-run-btk-v1.log`.
- **왜**: Phase 5 `gate_guard.Verdict` 는 rubric-schema draft-07 dataclass (result/score/evidence/semantic_feedback/inspector_name), Phase 9.1 `state.Verdict` 는 Enum (PASS/FAIL/RETRY). 두 타입 공존은 의도적 (`state.py` docstring 설계 노트 참조) — Enum 에 `.result` property 가 있어 `verdict.result == "PASS"` 동등성 체크는 통과하나, `asdict()` 는 순수 dataclass 에만 작동. 실 `ClaudeAgentSupervisorInvoker` 도 Enum 반환하므로 same latent bug 지만 F-LIVE-SMOKE JSON 에러가 먼저 터져 dispatch 도달 전 차단되어 드러나지 않았음. `--skip-supervisor` 가 JSON 에러를 우회하자 2차 에러가 surface.
- **Scope**: 1 파일 (`scripts/smoke/phase13_live_smoke.py` — `_AutoPassSupervisorInvoker.__call__` 반환 타입 교정). 실 supervisor 경로의 동일 bug 수정은 scope 밖 (본 세션 영상 제작 goal 이후 별도 후속).
- **Commits**: `[다음 commit marker]`
- **Authorized by**: 대표님 세션 #31 "외국 범죄 대박날만한 것" 연속 지시 (lenient retry 원칙 자동 적용 — hard abort 금지, 즉시 진단 + 최소 수정 재시도)
- **정답**: `_AutoPassSupervisorInvoker.__call__` 이 `gate_guard.Verdict(result="PASS", score=100, evidence=[], semantic_feedback="auto-pass", inspector_name="auto-pass-supervisor-bypass")` dataclass 반환. 테스트 `tests/phase15/test_skip_supervisor.py` 의 4개 dataclass 계약 검증 (isinstance / asdict / 필수 필드) 추가.
- **검증**: (1) `py -3.11 -m pytest tests/phase15/test_skip_supervisor.py -v` → 6 passed. (2) 재실행 live run 이 TREND dispatch 통과 (evidence: smoke_e2e_btk_v1_session31_retry.json dispatched ≥ 1). (3) `grep -n "asdict" scripts/smoke/phase13_live_smoke.py` 가 0 (무관), `scripts/orchestrator/gate_guard.py` 에만 존재.
- **상태**: resolved (세션 #31, 2026-04-22 — 즉시 패치 + 테스트 + 재시도 예정)
- **Lessons (핵심 교훈)**:
  1. **Bypass 는 새 bug 를 노출시킨다**: 하나의 에러(JSON 엄수)를 우회하면 그 뒤에 가려져 있던 latent bug 가 드러난다. bypass 패치는 "연쇄 에러" 가능성을 염두에 둔 테스트 설계 필요.
  2. **타입 중복은 인터페이스 계약으로 묶여야 한다**: `state.Verdict` (Enum) + `gate_guard.Verdict` (dataclass) 공존은 의도적이었으나, `.result` property 외에 `asdict` 호환도 요구되는 곳이 있었다. 인터페이스 양쪽 만족시키는 `__dataclass_fields__` 호환 Enum + 공용 `to_checkpoint_dict()` 메서드 같은 정합화가 후속 과제.
  3. **타입 힌트는 런타임 계약이 아니다**: `supervisor_invoker: Callable[[GateName, dict], Verdict]` 가 dataclass Verdict 를 명시해도 실제 impl 은 Enum 을 반환. mypy/ruff strict 검사가 없으면 drift 가 쌓인다.
  4. **lenient retry 원칙의 실전 적용**: JSON 에러도 type 에러도 hard-abort 없이 즉시 진단 → 최소 패치 → 재시도. 세션 #30 `feedback_lenient_retry_over_strict_block.md` 가 정확히 이 경로 권장.
- **관련**: `F-LIVE-SMOKE-JSON-NONCOMPLIANCE` (선행 차단 원인, 본 bug 를 가려둔 상위 층) / `scripts/orchestrator/state.py` docstring 설계 노트 / `scripts/orchestrator/gate_guard.py` L171 `verdict=asdict(verdict)` / `tests/phase15/test_skip_supervisor.py` 4 dataclass 계약 테스트 / `.claude/memory/feedback_lenient_retry_over_strict_block.md` (대표님 원칙 준수)
