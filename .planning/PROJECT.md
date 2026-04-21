# naberal-shorts-studio

## What This Is

AI 에이전트 팀이 자율적으로 YouTube Shorts 영상을 주 3~4편 제작·발행하여, 대표님의 기존 YouTube 채널을 **YPP(1000구독 + 10M views/연) 진입 궤도**에 올리는 자동 영상제작 스튜디오. `naberal_harness v1.0.1` Layer 1 인프라를 상속하고, 기존 `shorts_naberal`의 작동 검증된 영상 제작 로직·바이블·유틸을 **선별 Harvest**하여 구축한다.

나베랄 그룹 2-Layer 아키텍처의 **첫 번째 Layer 2 스튜디오**이자, 이후 만들어질 모든 도메인 스튜디오(blog, rocket 등)의 참조 구현이 된다.

## Core Value

**외부 수익(YouTube 광고)이 실제 발생하는 자동화 파이프라인**.

내부 기술 성공(영상 1편 생성)이 아니라 **YPP 진입 궤도 확보**가 최종 기준이다. 기술이 잘 돌아도 수익이 없으면 실패로 간주.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- [x] **REQ-01**: `naberal_harness v1.0.1` Layer 1 상속 + **3-Tier 위키 구조** 구축 완료 — Validated in Phase 1 (Scaffold) + Phase 2 (Domain Definition). harness/wiki/(Tier 1 minimal, D2-A) + studios/shorts/wiki/(Tier 2, 5 카테고리+MOC, D2-B) + .preserved/harvested/(Tier 3) 물리 생성 + STRUCTURE.md v1.0.0→v1.1.0 schema bump (commit harness@8a8c32b + studio@f360e17).

### Active

<!-- Current scope. Building toward these. -->

- [ ] **REQ-02**: `shorts_naberal`에서 작동 검증된 자산 Harvest (theme-bible, 렌더 `src/`, hc_checks 유틸, FAILURES.md) — 읽기만, 원본 수정 금지
- [ ] **REQ-03**: 도메인 에이전트 **12~20명 통합 설계** (기존 32명 inspector 과포화 회피, Anthropic sweet spot 준수)
- [ ] **REQ-04**: 오케스트레이터 v2 재작성 (**500~800줄 state machine 기반**, `skip_gates=True` / `TODO(next-session)` 물리 차단)
- [ ] **REQ-05**: **Producer-Reviewer 이중 생성** 파이프라인 + rubric 기반 자동 품질 게이트 (인간 감독 → 에이전트 감독 이관)
- [ ] **REQ-06**: **FAILURES.md 저수지** + SKILL.md 버저닝 + `SKILL_HISTORY/` 백업으로 학습 충돌 방지 (피드백 즉시 SKILL 수정 금지, 월 1회 batch)
- [ ] **REQ-07**: **NotebookLM 스킬 통합** (Tier 2 위키의 동적 RAG 쿼리 인터페이스, source-grounded 답변으로 환각 방지)
- [ ] **REQ-08**: 기존 YouTube 채널에 **주 3~4편 자동 발행** end-to-end 파이프라인 (콘텐츠 니치: shorts_naberal 승계, Phase 3에서 확정)
- [ ] **REQ-09**: **KPI-driven feedback loop** (YouTube Analytics → `wiki/kpi/kpi_log.md` → 다음 달 Producer 입력으로 반영되는 학습 회로) — **Infrastructure installed in Phase 9 + Phase 10** (Taste Gate protocol + kpi_log.md Hybrid Part A/B + `scripts/taste_gate/record_feedback.py` Hook-compat appender + Phase 10 KPI-01~04 자동 회로 — `fetch_kpi.py` + `monthly_aggregate.py` + `monthly_update.py` 3-tier fallback + `trajectory_append.py` YPP 궤도 그래프). Full cycle validation pending Phase 10 Month 1 real data (operational start after 대표님 OAuth 재인증 + GH Secrets + Windows Task 등록).
- [ ] **REQ-04 refined**: **Orchestrator v2 Production Engine Wiring** (500~800 state machine, producer/supervisor Claude Agent SDK 실 wiring) — **Engine wiring completed in Phase 9.1 (2026-04-20 세션 #24)**. `shorts_pipeline.py` 792 lines (≤800 유지) + `invokers.py` 306 + `api/nanobanana.py` 200 + `api/ken_burns.py` 192 + `character_registry.py` 99 + `voice_discovery.py` 91. Claude Agent SDK (`anthropic==0.75.0`) + google-genai + FFmpeg 로컬 Ken-Burns + Runway Gen-3a Turbo primary + VALID_RATIOS_BY_MODEL. Stage 2→4 실 smoke $0.29 MP4 생성. Phase 10 진입 전 3 manual items pending (ANTHROPIC_API_KEY 실 호출 / 대표님 clip.mp4 품질 평가 / ElevenLabs 한국어 voice 확인).
- [ ] **REQ-10**: 건강 감사 점수 **≥ 80** + A급 drift **0건** + SKILL 500줄 초과 **0건** 달성 (harness-audit 스킬로 검증) — **Infrastructure completed in Phase 10**: `skill_patch_counter.py` (D-2 Lock 감시 CLI, FAIL-04) + `drift_scan.py` (A급 drift wrapper + phase_lock, AUDIT-03/04) + `session_audit_rollup.py` (30일 rolling ≥ 80, AUDIT-01) 가동. Validation pending 첫 30일 rolling 실측 및 drift 주 1회 cron 실행.
- [ ] **REQ-11**: 하네스 품질 3대 gap (에이전트 재호출 루프 / 출력 형식 drift / 도구 오용) 구조적 해소 — **Validated in Phase 12 (Agent Standardization + Skill Routing + FAILURES Protocol)**: 30 AGENT.md (14 producer + 17 inspector, harvest-importer/shorts-supervisor 제외) 5-block v1.x schema 전수 migration + `verify_agent_md_schema.py` 31/31 PASS + `verify_agent_skill_matrix.py` 155/155 cells reciprocate + `verify_mandatory_reads_prose.py` 31/31 PASS + FAILURES.md 500줄 rotation protocol (pre_tool_use.py cap + `failures_rotate.py` CLI + `FAILURES_ROTATE_CTX` env bypass + `_imported_from_shorts_naberal.md` HARD-EXCLUDE) + Supervisor prompt compression (`_compress_producer_output()` 27% ratio) → Phase 11 Gate 2 rc=1 "프롬프트가 너무 깁니다" 구조적 closure. Hard enforcement(Hook 차단)는 Phase 13 conditional per D-A1-03.

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- **일 5편+ 양산 모델** — 주 3~4편 품질우선 채택. 인프라 과투자 회피. 수익 검증 후 v2에서 재결정.
- **신규 YouTube 채널 구축 (0구독 시작)** — 기존 채널 활용 결정. 0구독 초기 성장 전략은 별도 프로젝트.
- **대안 수익원(쿠팡파트너스 / 블로그 유입 / 브랜드 딜)** — YPP 광고 수익을 일차 검증. 다른 수익 모델은 v2 이후.
- **`shorts_naberal` 직접 수정** — 대표님의 uncommitted 20+ 작업 보존. Harvest는 읽기만 허용.
- **콘텐츠 니치 신규 탐색 / pivot** — 기존 `shorts_naberal` 니치 승계 확정. pivot은 v2.
- **Live 스트리밍 / Long-form 영상** — Shorts 전용. 장편·라이브는 별도 스튜디오.
- **32 inspector 전수 보존** — 과포화 해소가 목표. 기능은 rubric 통합으로 승계.

## Context

- **상위 아키텍처**: 나베랄 그룹 2-Layer 구조 — Layer 1 (`naberal_harness`, 공용 인프라), Layer 2 (이 스튜디오, 도메인 전용).
- **학계 근거**: FilmAgent / Mind-of-Director / Omniagent 모범사례와 `shorts_naberal`의 89% 일치 (RESEARCH_REPORT 2026-04-18). 방향성은 맞았으나 구현이 drift.
- **구형 drift 진단 (세션 #9)**: A급 13, B급 16, C급 10 충돌. 오케스트레이터 5166줄, 32 inspector 과포화, TODO(next-session) 4건 미연결, Runway vs Kling primary 전환 미완결 — **"스킵" 근본 원인**.
- **선행 자산**:
  - `naberal_harness v1.0.1` (Private GitHub, 29 파일, 공용 스킬 5개 + Hook 3개 + CLI 4개)
  - `shorts_naberal/.planning/` (읽기 전용 진단 자료: RESEARCH_REPORT, CONFLICT_MAP, DECISIONS_TEMPLATE)
  - `secondjob_naberal/wiki/` (블로그 도메인 위키, 참조 가능)
  - `.claude/skills/notebooklm/` (NotebookLM 스킬, Tier 2 위키 RAG 엔진으로 활용)
- **Claude/LLM 제약**:
  - **Lost in the Middle** — 긴 프롬프트 중간 지시 누락 (Stanford 2023)
  - **description 트리거 키워드**가 에이전트 호출 결정
  - **RoPE 모델 끝 지시 더 잘 기억** → 중요 지시는 문서 끝 재배치
- **대표님 성향**: 품질 최우선, 구조적 통제 중시, 답답함 원인 = 반복적 drift → 이번 구조적 해결로 대응.

## Constraints

- **Tech**: `naberal_harness v1.0.1` 준수 — `STRUCTURE.md` Whitelist 외 폴더 생성 금지, SKILL.md ≤ 500줄, Hook 3종 필수 설치
- **Architecture**: 에이전트 **12~20명** (32명 과포화 금지), 오케스트레이터 **500~800줄** (5166줄 수준 금지)
- **Code Quality**: `skip_gates=True` 금지, `TODO(next-session)` 금지, try-except 조용한 폴백 금지 (pre_tool_use 차단)
- **Git**: 독립 git 저장소, `shorts_naberal` 수정 금지, 원격 = `github.com/kanno321-create/shorts_studio` (Phase 8)
- **Workflow**: GSD 정식 — phase별 commit, 커밋 없으면 다음 phase 진입 불가
- **Publication**: 주 3~4편 (품질우선), 기존 YouTube 채널 활용, shorts_naberal 니치 승계
- **Dependency**: Runway / Kling / ElevenLabs / NotebookLM 등 외부 AI API (shorts_naberal 기존 wrapper 승계)
- **Compliance**: YouTube Shorts 정책 + YPP 요건 준수, 저작권/초상권 안전
- **Budget**: 외부 API 비용 — 월 예산은 수익 검증 전 보수적 운영 (구체 수치는 Phase 5에서 확정)

## Key Decisions

<!-- 세션 #10 Deep Questioning에서 7개 구조적 해결책 승인 → 10개 결정으로 확장 -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| **D-1**: 3-Tier 위키 채택 (harness / studio / preserved) | 프로젝트별 위키 고립 해결, 지식 재발견 반복 방지 | ✅ Validated Phase 2 (commit f360e17) |
| **D-2**: FAILURES.md 저수지 패턴 (피드백 즉시 SKILL 수정 금지, 월 1회 batch 리뷰) | 학습 충돌 방지, 대표님 기억 의존 제거 | ✅ Validated Phase 10 (D-2 Lock 감시 + drift scan + FAILURES append-only 인프라 완결) |
| **D-3**: Producer-Reviewer 이중 생성 표준 패턴 (rubric 기반 품질 게이트) | 단일 패스 품질 부족 극복, 외주 조합 한계 돌파 | — Pending |
| **D-4**: NotebookLM = Tier 2 위키의 RAG 쿼리 인터페이스 | 방대한 지식 동적 쿼리 + source-grounded 답변으로 환각 방지 | — Pending |
| **D-5**: SKILL.md 버저닝 + `SKILL_HISTORY/` 백업 + Staged Rollout (`.candidate`) | 스킬 업데이트 충돌 방지, rollback 보장 | — Pending |
| **D-6**: 하네스 3중 방어선 (Hook 차단 / Dispatcher 강제 / Audit 감사) | 지식 누적 시 에이전트 스킵 구조적 대응 | ✅ Validated Phase 10 (`pre_tool_use.py` + `gate_dispatcher` + `harness_audit.py` + Phase 10 `drift_scan.py`/`session_audit_rollup.py` 전부 가동) |
| **D-7**: state machine 오케스트레이터 (텍스트 체크리스트 완전 폐기) | 에이전트 자의적 순서 조정 물리 차단 | — Pending |
| **D-8**: Harvest 전략 — "Harvest, not Fork" (작동 자산 승계 + drift 덩어리 폐기) | 3~6개월 재발견 회피, shorts_naberal 자산 존중 | 🟡 Scoped Phase 2 (HARVEST_SCOPE.md A급 13 판정 완료) → 실행 Phase 3 |
| **D-9**: Core Value = 외부 수익(YouTube 광고) 발생, YPP 진입 궤도 | 기술 성공 ≠ 비즈니스 성공, 명확히 분리 | — Pending |
| **D-10**: 주 3~4편 품질우선 (일 10편 양산모델 아님) | 건강한 파이프라인, 인프라 과투자 회피 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state (채널 구독자, 조회수, 월 수익 등)

---
*Last updated: 2026-04-21 after Phase 12 Agent Standardization + Skill Routing + FAILURES Protocol completion (session #29 — 7/7 plans shipped, AGENT-STD-01/02/03 + SKILL-ROUTE-01 + FAIL-PROTO-01/02 all complete, 31/31 AGENT.md schema compliant, Phase 11 Gate 2 rc=1 gap structurally closed, REQ-11 validated). Pre-existing phase05/06/07 API adapter drift (15 failures in veo_i2v/elevenlabs/shotstack — Phase 09.1 era) documented as out-of-scope for Phase 12; candidate for dedicated remediation phase. Live smoke 재도전 (Phase 11 SC#1/SC#2 실 Claude CLI + YouTube 과금 환경) 은 Phase 13 로 handoff.*
