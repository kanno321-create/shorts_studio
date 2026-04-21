---
phase: 13-live-smoke
status: complete_tier1
finalized: 2026-04-22
milestone: v1.0.2
---

# Phase 13 — Traceability Matrix (Tier 1 closure)

**Phase**: 13 Live Smoke 재도전
**Milestone**: v1.0.2 Production Readiness
**Tier 1 completion**: 2026-04-22
**Tier 2 deferred**: 실 과금 5 tests (live_smoke marker) — 대표님 승인 지점
**Grand total REQ mapping**: v1.0.1 96 + Phase 11 6 + Phase 12 6 + v1.0.2 12 = **120 REQ**

---

## 대표님께 드리는 요약 보고

대표님, Phase 13 (Live Smoke 재도전) 의 Tier 1 infrastructure 완결 보고 드립니다.

6 Wave (0~5) 를 통해 Live Smoke 재도전에 필요한 모든 기반을 구축하였습니다. Wave 0 에서 `live_smoke` pytest marker + `BudgetCounter` SSOT + preflight CLI 4-check + 4 golden fixture 를 anchoring 하였고, Wave 1~4 에서 SMOKE-01~06 각각을 Tier 1 (mock/shape) + Tier 2 (실 API placeholder) 로 분리 구현하였습니다. Wave 5 에서는 Phase 14 패턴을 복제한 `phase13_acceptance.py` + `test_phase13_acceptance.py` 를 신설하여 6 SC + 2 audit 자동 판정 gate 를 완성하였습니다.

**Tier 1 39 tests GREEN** + Phase 14 adapter_contract 30 tests 회귀 보존 + harness_audit 점수 90 + drift_scan A급 0 건 모두 확인하였습니다. `phase13_acceptance.py` 가 ALL_PASS (rc=0) 를 반환하고, `test_phase13_acceptance.py` 10개 테스트 전수 green (17.46s) 을 확인하였습니다.

**Tier 2 (실 과금 live run) 는 본 Phase 범위에서 deferred 처리**하였습니다. 5 evidence 파일 (producer_output / supervisor_output / smoke_upload / budget_usage / smoke_e2e) 생성은 대표님께서 별도 승인 지점에서 `pytest --run-live` 또는 `py scripts/smoke/phase13_live_smoke.py --live` 명령을 직접 내려주셔야 진행됩니다. CLAUDE.md 금기사항 #8 (일일 업로드 금지) 및 $5 HARD 예산 cap 준수를 위한 설계적 분리입니다.

Phase 11 deferred SC#1/SC#2 (supervisor rc=1 blocker + video publish 검증) 는 Phase 12 AGENT-STD-03 compression 구조로 **구조적 해소 경로** 를 확립했습니다. 실 API 환경에서의 empirical closure 는 Tier 2 live run 완료 시 달성됩니다.

v1.0.2 밀스톤 12 REQ 중 Phase 14 6건 (ADAPT-01~06) 이 공식 validated, Phase 13 6건 (SMOKE-01~06) 이 Tier 1 validated + Tier 2 deferred 상태입니다. 진척 9/12 (75% Tier 1 기준, Tier 2 완료 시 100%).

---

## REQ × SC × Plan × Evidence Matrix

| REQ | Description | SC | Plans | Tier 1 Evidence | Tier 2 Evidence (deferred) |
|-----|-------------|:-:|-------|-----------------|---------------------------|
| **SMOKE-01** | Real Claude CLI producer 호출 + producer_output JSON anchor | SC#1, SC#3 | 13-01, 13-02, 13-06 | `3d975ea` evidence_extractor.py · `af81ca4` test_smoke_01_producer.py Tier 1 · `tests/phase13/fixtures/sample_producer_output.json` · 13-06-acceptance.json checks[0,2,3] | `evidence/producer_output_<sid>.json` (실 live run 후 anchor) |
| **SMOKE-02** | Real Claude CLI supervisor 17-inspector fan-out + rc=1 재현 0회 | SC#1, SC#3 | 13-01, 13-02, 13-06 | `57a12b0` test_smoke_02_supervisor.py Tier 1 (_compress_producer_output exists+callable, _COMPRESS_CHAR_BUDGET=2000) · `sample_supervisor_output.json` (rc1_count=0) · 13-06-acceptance.json checks[0,2,3] | `evidence/supervisor_output_<sid>.json` (rc1_count==0 empirical) |
| **SMOKE-03** | YouTube unlisted + cleanup + public ValueError | SC#1, SC#3 | 13-03, 13-06 | `20749be` upload_evidence.py · `87ad7b4` test_smoke_03_upload_contract.py Tier 1 (public/private ValueError + unlisted HARDCODED) · `f6e7864` docstring scrub + validate_metadata_readback · 13-06-acceptance.json checks[0,2] | `evidence/smoke_upload_<sid>.json` (실 videos.insert + videos.delete cleanup) |
| **SMOKE-04** | production_metadata HTML comment videos.get readback 4 필드 | SC#1, SC#3, SC#4 | 13-03, 13-06 | `0926faf` test_smoke_04_readback.py Tier 1 (DOTALL regex + 4 필드 invariant) · `sample_smoke_upload.json` (required_fields_present=true) · 13-06-acceptance.json checks[0,2,3] | `evidence/smoke_upload_<sid>.json::production_metadata` 실 videos.list readback |
| **SMOKE-05** | Budget cap $5 enforcement + budget_usage.json | SC#1, SC#3, SC#6 | 13-01, 13-04, 13-05, 13-06 | `8a7a1c1` BudgetCounter + BudgetExceededError · `2a9eb3d` RED tests · `d29265d` provider_rates.py (8 adapter × unit price SSOT) · `f243642` test_budget_enforcement.py 7 Tier 1 tests · 13-06-acceptance.json checks[0,2,5] | `evidence/budget_usage_<sid>.json` (실 adapter charges + total_usd ≤ $5.00) |
| **SMOKE-06** | Full E2E 13 GATE dispatched + final_video_id + total_cost_usd | SC#1, SC#3, SC#4, SC#6 | 13-01, 13-05, 13-06 | `52f8371` phase13_live_smoke.py runner (250+ lines, dry-run $0) · `7bb7438` test_smoke_e2e_evidence.py 6 Tier 1 shape tests · `sample_smoke_e2e.json` (gate_count=13) · 13-06-acceptance.json checks[0,2,3,5] | `evidence/smoke_e2e_<sid>.json` (실 TREND→COMPLETE 13 gate + cleanup) |

---

## Success Criteria × Plan × Commit (Tier 1 gate)

| SC | Criteria (Phase 13 Wave 5 acceptance) | Plan Owner | Verifying Commit/Artifact |
|:-:|-------|------------|---------------------------|
| SC#1 | Phase 13 Tier 1 전수 pytest green (≥39 passed) | 13-06 | `09a678a` phase13_acceptance.py · `7375840` test wrapper · Tier 1 47 passed in acceptance.py context (39 phase13 + 8 wrapper) |
| SC#2 | Tier 2 live_smoke ≥5 tests collect 가능 (deferred) | 13-02, 13-03, 13-05, 13-06 | 5 Tier 2 tests: test_live_run + test_smoke_01/02/03/04 — `pytest -m live_smoke --collect-only` 5/44 collected |
| SC#3 | scripts/smoke/ 5 모듈 import clean | 13-01, 13-02, 13-03, 13-04, 13-05, 13-06 | budget_counter + evidence_extractor + upload_evidence + provider_rates + phase13_live_smoke 모두 `importlib.import_module` clean |
| SC#4 | 4 golden fixture JSON UTF-8 parseable | 13-01, 13-06 | `3827ae5` sample_producer_output.json + sample_supervisor_output.json + sample_smoke_upload.json + sample_smoke_e2e.json |
| SC#5 | pytest.ini markers + Phase 14 adapter_contract 30 green | 13-01, 13-06 | `56b5da0` live_smoke marker + Phase 14 adapter_contract 30 passed regression |
| SC#6 | phase13_live_smoke.py --help exit 0 + 4 flags | 13-05, 13-06 | `52f8371` runner + 4 flags advertised: `--live`, `--max-attempts`, `--budget-cap-usd`, `--verbose-compression` |
| AUDIT-01/02 | harness_audit 점수 ≥80 (현재 90) | 13-06 | `HARNESS_AUDIT_SCORE: 90 (violations: 1 warnings: 0)` |
| AUDIT-03/04 | drift_scan A급 drift 0 건 | 13-06 | `drift_scan --dry-run --skip-github-issue` rc=0 |

---

## Phase 11 Deferred SC 해소 (구조적 경로 확립)

Phase 11 11-VERIFICATION.md §11 Gap Analysis 의 2 deferred SC 가 본 Phase 13 에서 **구조적 해소 경로** 확립:

- **Phase 11 SC#1 (Full 0→13 real-run smoke, supervisor rc=1 blocker)** → Phase 13 SMOKE-02 Tier 1 가 Phase 12 AGENT-STD-03 `_compress_producer_output()` (27% 압축 ratio) 의 존재 + callable + `_COMPRESS_CHAR_BUDGET=2000` invariant 를 test surface 로 검증 (`57a12b0`). **Tier 2 empirical closure** 는 실 Claude CLI 호출 후 `evidence/supervisor_output_<sid>.json::rc1_count == 0` 생성 시 완료 — 대표님 live run 승인 대기.
- **Phase 11 SC#2 (Video published + SCRIPT-01 verdict locked)** → Phase 13 SMOKE-03/04 Tier 1 가 YouTube Data API v3 public/private ValueError contract + production_metadata 4 필드 regex readback 을 test surface 로 검증 (`87ad7b4`, `0926faf`). **Tier 2 empirical closure** 는 실 videos.insert + videos.list + videos.delete 호출 후 `evidence/smoke_upload_<sid>.json` 생성 시 완료. SCRIPT-01 verdict lock 은 Tier 2 live run 의 human_verification 지점에서 대표님 6-axis eval 진행.

---

## Phase Dependencies (Inbound)

- **Phase 8** (Remote + Publishing): PUB-01/02/03/04/05 shipped — `smoke_test.py` + `production_metadata.py` + OAuth 경로 본 phase 에서 consume.
- **Phase 9.1** (Production Engine Wiring): `invokers.py` real Claude CLI 경로 + `_check_cost_cap()` BudgetCounter 패턴 조상.
- **Phase 11** (Pipeline Real-Run Activation): `phase11_full_run.py` 493-line harness → Wave 4 가 clone (`phase13_live_smoke.py`).
- **Phase 12** (Agent Standardization + Supervisor Compression): AGENT-STD-03 `_compress_producer_output()` 가 SMOKE-02 rc=0 의 구조적 전제.
- **Phase 14** (API Adapter Remediation): `phase14_acceptance.py` + `14-TRACEABILITY.md` 패턴 → Plan 06 가 복제 (`09a678a`, `7375840`, 본 문서).

---

## Wave Breakdown

| Wave | Plan | Role | 주요 산출물 | 주요 Commits |
|------|------|------|-----------|--------------|
| 0 | 13-01 | Preflight Infra | pytest.ini `live_smoke` marker + budget_counter.py + phase13_preflight.py + tests/phase13/ scaffold + 4 golden fixtures | `56b5da0`, `2a9eb3d`, `8a7a1c1`, `3827ae5`, `4349deb` |
| 1 | 13-02 | Real Claude CLI Smoke (SMOKE-01/02) | evidence_extractor.py + test_smoke_01_producer.py + test_smoke_02_supervisor.py + test_evidence_shapes.py | `3d975ea`, `af81ca4`, `57a12b0`, `2a38377` |
| 2 | 13-03 | YouTube Upload Smoke (SMOKE-03/04) | upload_evidence.py + test_smoke_03_upload_contract.py + test_smoke_04_readback.py + docstring scrub | `20749be`, `87ad7b4`, `0926faf`, `f6e7864` |
| 3 | 13-04 | Budget Cap Enforcement (SMOKE-05) | provider_rates.py + test_budget_enforcement.py (7 Tier 1 tests) | `d29265d`, `f243642` |
| 4 | 13-05 | Full E2E Smoke (SMOKE-06) | phase13_live_smoke.py runner + test_smoke_e2e_evidence.py + test_live_run.py (Tier 1 dry-run + Tier 2 placeholder) | `52f8371`, `7bb7438`, `227c415` |
| 5 | 13-06 | Phase Gate (본 Plan) | phase13_acceptance.py + test_phase13_acceptance.py + 13-TRACEABILITY.md (본 문서) + 13-VALIDATION.md flip | `09a678a`, `7375840`, (TRACEABILITY commit), (VALIDATION flip commit) |

---

## Tier 1 / Tier 2 분리 명세 (금기 #1, #8 준수)

**본 Phase 13 의 완료 판정은 Tier 1 범위 한정**이며, Tier 2 는 대표님 승인 후 별도 실행됩니다. 이는 CLAUDE.md 금기사항 준수를 위한 구조적 분리입니다:

- **금기 #1 skip_gates 금지**: phase13_acceptance.py 의 HARD-GATE (`grep -q 'ALL_PASS' ... || exit 1`) 는 Tier 1 8 check 전수를 통과해야 VALIDATION flip 가능. Tier 2 를 skip 하는 것이 아니라, Tier 2 는 본 gate 의 **범위 외** (별도 approval 게이트).
- **금기 #8 일일 업로드 금지**: Tier 2 live run 은 실 YouTube 업로드 (즉시 cleanup=True 포함) + 실 Kling/Typecast/Nano Banana 호출 ($1.50~$3.00 소비) 을 수반. 본 gate 가 Tier 2 를 자동 실행하면 매 CI/commit 마다 실 과금 trigger → 봇 패턴 + 채널 reputation 오염. 따라서 Tier 2 는 수동 opt-in (`--run-live` 또는 `--live`) 으로만 활성.

**Tier 2 실행 경로** (대표님 승인 후):

```bash
# Option A: pytest 경유 (5 tests Tier 2)
py -3.11 -m pytest tests/phase13/ -m live_smoke --run-live -v --no-cov

# Option B: CLI 직접 실행 (phase13_live_smoke.py)
py -3.11 scripts/smoke/phase13_live_smoke.py --live --budget-cap-usd 5.00 --max-attempts 2
```

**Tier 2 완료 후 생성될 evidence** (5 파일):
- `evidence/producer_output_<sid>.json`
- `evidence/supervisor_output_<sid>.json`
- `evidence/smoke_upload_<sid>.json`
- `evidence/budget_usage_<sid>.json`
- `evidence/smoke_e2e_<sid>.json`

---

## Budget & Evidence Audit

- **Tier 1 비용**: $0.00 (mock/fixture/dry-run 전용)
- **Tier 2 예상 비용**: $1.50~$3.00 (8 Kling cuts × $0.35 dominant + Typecast $0.12 + Nano Banana $0.04)
- **Hard cap**: $5.00 (BudgetCounter + BudgetExceededError)
- **YouTube quota**: smoke=1651/10000 units (videos.insert 1600 + list 1 + delete 50) — daily free
- **Tier 1 Evidence Chain**: 4 golden fixture JSON + `13-06-acceptance.json` + `13-06-phase-gate.log`
- **Cleanup invariant**: unlisted HARDCODED (D-11) + `cleanup=True` (Phase 8 ship) + `SHORTS_PUBLISH_LOCK_PATH` temp override (Phase 8 D-06)

---

## v1.0.2 Milestone Coverage Check

- **v1.0.1 96 REQ**: all validated (Phase 1~10/10.1/11/12 complete)
- **Phase 11 6 REQ** (PIPELINE-01~04 + SCRIPT-01 + AUDIT-05): validated in Phase 11
- **Phase 12 6 REQ** (AGENT-STD-01/02/03 + SKILL-ROUTE-01 + FAIL-PROTO-01/02): validated in Phase 12
- **v1.0.2 12 REQ**:
  - **Phase 14 6 REQ** (ADAPT-01~06): validated 2026-04-21 (Phase 14 TRACEABILITY)
  - **Phase 13 6 REQ** (SMOKE-01~06): **Tier 1 validated 2026-04-22** (본 문서) + Tier 2 deferred (대표님 승인 지점)

**v1.0.2 진척**:
- Tier 1 기준: 12/12 (100% infra + surface tests green)
- Tier 2 기준 (실 live run evidence 포함): 6/12 (50%) — Phase 14 완결 + Phase 13 Tier 2 대기

---

## Deviations & Notes

- **Plan 06 Task 13-06-01 Rule 1 deviation**: SC#1 pytest invocation 이 `tests/phase13/` 전체를 collect 하면 `test_phase13_acceptance.py` 자체가 포함되어 무한 재귀 (acceptance.py → pytest → acceptance.py → timeout 300s). `--ignore=tests/phase13/test_phase13_acceptance.py` 로 surgical 차단. Commit `7375840` 에서 fix + wrapper 테스트 동반 추가.
- **Plan 06 Task 13-06-01 Tier 범위 조정**: 원 Plan 은 5 evidence 파일 glob 기반 SC#1~6 검증 (live run 완료 후 시나리오). 실제 Wave 4 가 Tier 2 live run 을 deferred 처리했으므로 Task 13-06-01 의 SC#1~6 정의를 Tier 1 infrastructure 관점 (pytest + import + fixtures + runner CLI) 으로 재정의. 이는 계획 품질 이슈가 아니라 Tier 1/2 분리 설계의 자연스러운 귀결 — 대표님 objective 에서 명시적으로 지시.
- **Plan 04 Task 13-04-02 TDD 단일 commit**: 본 test 가 소비하는 `BudgetCounter` 는 Plan 01 `8a7a1c1` 에서 이미 shipped. RED 단계가 자연발생 불가 → 단일 GREEN commit 으로 응축 (Summary 13-04 참조).
- **Plan 03 Task 13-03 Rule 2 expansion**: upload_evidence.py 가 `validate_metadata_readback` 헬퍼 추가 + 금지 단어 (selenium/webdriver) docstring scrub. Commit `f6e7864`.

---

## 갱신 기록

- **2026-04-22** Phase 13 Plan 06 Task 13-06-03 신설. 6 SMOKE REQ × 8 gate check (6 SC + 2 audit) × 6 Plans × Tier 1 evidence + Tier 2 deferred paths 4-way 매트릭스 완전성 + Phase 11 deferred 구조적 해소 + 대표님 존댓말 보고 블록 포함. Tier 2 live run 은 본 문서 기준 deferred.
- **Next**: Phase 13 Plan 06 Task 13-06-04 HARD-GATE (`grep -q 'ALL_PASS' 13-06-phase-gate.log || exit 1`) + 13-VALIDATION.md `approved_with_deferred` flip.
- **Future (대표님 승인 후)**: Tier 2 live run → 5 evidence 파일 anchor → 본 문서 update (Tier 2 column 이 실 commit hash + evidence file path 로 채워짐) → `status: complete` (from `complete_tier1`) 재flip.
