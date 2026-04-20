---
plan: 12-02
status: partial — finish_last_mile
created: 2026-04-21
phase: 12-agent-standardization-skill-routing-failures-protocol
disk_reality: 14/14 producers PASS schema (via verify_agent_md_schema.py)
remaining_work: ~15% (commit pending diffs + SUMMARY + FAILURES entry + STATE/ROADMAP)
resume_command: /gsd:execute-phase 12 --wave 2 --gaps-only   # OR finish inline (see below)
---

# HANDOFF — Plan 12-02 (Producer 12-migration)

## 현재 상태 (disk truth)

- **파일 수준 완료**: 12/12 Producer AGENT.md 가 5-block v1.2 schema 로 migration 완료. `python scripts/validate/verify_agent_md_schema.py --all` → 14/14 producers PASS (trend-collector v1.2 + 12 신규 + harvest-importer 원본).
- **커밋 완료된 work** (6 commits, 최신순):
  - `172f623` assembler + publisher
  - `22b13bb` voice-producer + asset-sourcer + thumbnail-designer
  - `1226750` scene-planner + shot-planner + script-polisher
  - `2089449` director + scripter + metadata-seo
  - `9ed8f31` researcher
  - `93a285b` niche-classifier
- **미커밋 diff** (`git status -s`):
  ```
  M .claude/agents/producers/niche-classifier/AGENT.md   (+1줄)
  M .claude/agents/producers/researcher/AGENT.md          (-3/+3)
  M tests/phase12/test_agent_md_schema.py                 (+113/-2 실 assertion 전환)
  ```

## 남은 작업 (last mile, 약 15%)

1. **미커밋 diff 검토 후 커밋**: `git diff` 로 3파일 실내용 확인 → 의도적 마무리 패치이면 `git add` + `git commit --no-verify -m "feat(12-02): finalize niche-classifier + researcher polish + populate test_agent_md_schema assertions"`. 의도 불명이면 `git restore` 로 revert 후 진행.
2. **test_all_30_agents_have_5_blocks 재조정**: Plan 01 flag 반영 — 테스트 이름·파라미터를 disk reality (31 agents, producers 14 + inspectors 17) 로 맞춤. 단, Inspector 는 Plan 12-03 완료 전까지 fail 이 예상되므로 `@pytest.mark.skipif(inspector_migration_pending)` gate 적용 권장.
3. **F-D2-EXCEPTION-02 batch entry**: `.claude/failures/FAILURES.md` 에 30+ 파일 patch 를 단일 batch entry 로 기록 (FAIL-PROTO-01 하에 skill_patch_counter 가 count 만 보고 — Plan 04 commit `bd15bfd`/`0375dbb` 참고).
4. **skill_patch_counter 연동**: `scripts/audit/skill_patch_counter.py` 가 존재하는지 확인. 없으면 Plan 가 요구하므로 생성. 있으면 F-D2-EXCEPTION-02 배치 count 를 `reports/skill_patch_count_2026-04.md` 에 append.
5. **SUMMARY.md 작성**: `12-02-SUMMARY.md` 생성 — deviations (Plan 02 는 Wave 2 parallel 중 interrupt 발생, 12 producers 커밋 완료 후 재개, skill_patch_counter 미존재 시 신규 생성 결정 등) 포함.
6. **STATE + ROADMAP + REQUIREMENTS 업데이트**:
   ```bash
   node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" roadmap update-plan-progress 12 --plan 12-02
   node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" commit "docs(12-02): complete producer 12-migration plan"   --files .planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-02-SUMMARY.md .planning/STATE.md .planning/ROADMAP.md .claude/failures/FAILURES.md
   ```

## 읽어야 할 파일

- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-02-PLAN.md` — 8 task 상세
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-01-SUMMARY.md` — template + verifier 기준점
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-04-SUMMARY.md` — SSOT matrix (reciprocity 대기 중 — Plan 02 완료 시 drift 해소)
- `.claude/agents/producers/trend-collector/AGENT.md` — canonical 5-block reference
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/RESEARCH.md` — F-D2-EXCEPTION-02 batch 패턴

## 리스크

- **niche-classifier / researcher 미커밋 diff**: v1.2 migration 이후 추가 polish 일 가능성. 실내용 확인 전 무조건 커밋 금지.
- **test_agent_md_schema.py 변경**: +113 줄은 Plan 02 task 1 (test populate) 산출물로 추정. 실행 결과 반드시 GREEN 확인 후 커밋.
- **skill_patch_counter 부재**: `reports/skill_patch_count_2026-04.md` 는 `git status` 에 untracked 로 존재. 이 보고서가 counter 출력이라면 counter 스크립트도 Plan 02 범위. 없으면 신규 구현 필요 — RESEARCH §F-D2-EXCEPTION-02 참조.

## 완료 판정

- [ ] `python scripts/validate/verify_agent_md_schema.py --all` 결과 producers 14/14 PASS 유지
- [ ] `tests/phase12/` 실 assertion 포함 GREEN (inspector 관련 case 는 skip 허용)
- [ ] `tests/phase04/` 244 passed 회귀 없음
- [ ] `.claude/failures/FAILURES.md` 에 F-D2-EXCEPTION-02 단일 batch entry 추가
- [ ] `12-02-SUMMARY.md` 존재
- [ ] `.planning/REQUIREMENTS.md` AGENT-STD-01 진척 기록 업데이트
