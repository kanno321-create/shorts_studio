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
