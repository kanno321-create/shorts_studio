---
phase: 2
slug: domain-definition
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> **Source:** 02-RESEARCH.md § Validation Architecture (Nyquist 적용) line 823+

Phase 2는 **코드 변경 0줄**의 doc/infra phase. Validation은 **file existence + grep pattern + schema value check + git log**로 구성. Framework 설치 불필요.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Bash/PowerShell 내장 명령 + `python scripts/structure_check.py` (기존) |
| **Config file** | N/A (커맨드 기반) |
| **Quick run command** | `python C:/Users/PC/Desktop/naberal_group/harness/scripts/structure_check.py` |
| **Full suite command** | 아래 Per-Task Verification Map 섹션의 모든 command 순차 실행 |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit** (웨이브 단위): 해당 웨이브의 smoke 테스트만 (예: W1 완료 시 schema_version grep + structure_check.py)
- **After every plan wave**: 누적된 모든 smoke + unit (수초 내 완료, < 10s)
- **Before `/gsd:verify-work`:** 전체 12개 테스트 실행. 모두 PASS 시에만 Phase 3 진입 허용
- **Max feedback latency:** < 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-W1-01 | 01 | 1 | INFRA-02 (schema bump) | unit | `grep -c "schema_version: 1.1.0" C:/Users/PC/Desktop/naberal_group/harness/STRUCTURE.md` (expected: 1) | ✅ | ⬜ pending |
| 2-W1-02 | 01 | 1 | INFRA-02 (backup) | unit | `test -f C:/Users/PC/Desktop/naberal_group/harness/STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak` | ✅ | ⬜ pending |
| 2-W1-03 | 01 | 1 | INFRA-02 (Whitelist) | integration | `cd C:/Users/PC/Desktop/naberal_group/harness && python scripts/structure_check.py; echo $?` (expected: 0) | ✅ | ⬜ pending |
| 2-W1-04 | 01 | 1 | INFRA-02 (harness commit) | smoke | `cd C:/Users/PC/Desktop/naberal_group/harness && git log --oneline -1 STRUCTURE.md | grep "v1.1.0"` (expected: 1 match) | ✅ | ⬜ pending |
| 2-W2a-01 | 02 | 2 | INFRA-02 (Tier 1 exist) | smoke | `test -d C:/Users/PC/Desktop/naberal_group/harness/wiki && test -f C:/Users/PC/Desktop/naberal_group/harness/wiki/README.md` | ✅ | ⬜ pending |
| 2-W2b-01 | 03 | 2 | INFRA-02 (Tier 2 exist) | smoke | `for d in algorithm ypp render kpi continuity_bible; do test -d "studios/shorts/wiki/$d" && test -f "studios/shorts/wiki/$d/MOC.md"; done && test -f studios/shorts/wiki/README.md` | ✅ | ⬜ pending |
| 2-W2c-01 | 03 | 2 | INFRA-02 (Tier 3 exist) | smoke | `test -d studios/shorts/.preserved/harvested` | ✅ | ⬜ pending |
| 2-W3-01 | 04 | 3 | INFRA-02 (CLAUDE.md TODO) | unit | `grep -E "TODO:|TODO\(next-session\)" studios/shorts/CLAUDE.md | grep -vE "^[[:space:]]*<!--"` (expected: 0 matches) | ✅ | ⬜ pending |
| 2-W3-02 | 04 | 3 | INFRA-02 (line 7 typo fix) | unit | `grep -c "vv1.0" studios/shorts/CLAUDE.md` (expected: 0) + `grep -c "v1.0.1" studios/shorts/CLAUDE.md` (expected: ≥1) | ✅ | ⬜ pending |
| 2-W3-03 | 04 | 3 | INFRA-02 (8 absolute rules) | unit | `grep -c "skip_gates=True 금지" studios/shorts/CLAUDE.md` (expected: 1) + 동일 패턴 7개 더 | ✅ | ⬜ pending |
| 2-W3-04 | 05 | 3 | INFRA-02 (HARVEST_SCOPE) | unit | `test -f studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md && for i in 1 2 3 4 5 6 7 8 9 10 11 12 13; do grep -c "A-$i" studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md; done` (each: ≥1) | ✅ | ⬜ pending |
| 2-W4-01 | 06 | 4 | INFRA-02 (studio commit) | smoke | `cd studios/shorts && git log --oneline -5 | grep -Ei "phase 2|INFRA-02|domain definition"` (expected: ≥1 match) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

**None — Phase 2는 인프라 검증이므로 테스트 파일 신규 생성 불필요.**

기존 `C:/Users/PC/Desktop/naberal_group/harness/scripts/structure_check.py` + Bash/PowerShell 내장 명령으로 충분. Phase 2 산출물 자체가 검증 대상 파일들이므로, 별도 test fixture 불필요.

**선택적 (Planner 판단)**: `studios/shorts/scripts/verify_phase2.sh` — 12개 테스트를 한 줄 명령으로 wrap. 필수 아님. Phase 3 이후 회귀 감지에 재사용 가능.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLAUDE.md 5 TODO 치환 내용의 **의미 충실도** | INFRA-02 (SC#3) | grep은 TODO 존재 유무만 확인. D-1~D-10 내용이 적절하게 반영됐는지 의미 평가 필요 | 대표님이 CLAUDE.md Line 3 / 38-42 / 44-45 / 64-66 / 68 실제 내용 읽고 확인 |
| Tier 2 MOC.md 5 카테고리 Scope 문장 | INFRA-02 (SC#1) | 각 MOC의 Scope 1문장이 도메인 정확성 가지는지는 자동 확인 불가 | 대표님이 5개 MOC.md 각 Scope 확인 |
| HARVEST_SCOPE.md A급 13건 판정 합리성 | INFRA-02 (SC#4) | 승계/폐기/통합 판정이 D-1~D-10과 일치하는지는 의미적 검토 | 대표님이 A-1 ~ A-13 각 판정 근거 열람 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (해당 없음 — Wave 0 빈 것으로 OK)
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter (execute-phase 완료 시 업데이트)

**Approval:** pending (Phase 2 execute 후 승인)

---

## References

- **Source research:** `.planning/phases/02-domain-definition/02-RESEARCH.md` § Validation Architecture (line 823-870)
- **Context decisions:** `.planning/phases/02-domain-definition/02-CONTEXT.md` (D2-A~D2-D)
- **Nyquist principle:** Sampling rate sufficient for continuous feedback — per-task smoke + per-wave unit + phase gate integration
- **Doc-phase adaptation:** file existence + grep pattern + schema value check + git log → framework-free validation
