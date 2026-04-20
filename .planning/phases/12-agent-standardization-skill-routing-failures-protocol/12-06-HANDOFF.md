---
plan: 12-06
status: not_started
created: 2026-04-21
phase: 12-agent-standardization-skill-routing-failures-protocol
upstream_dependency: Plan 12-02 + Plan 12-03 완료 필수 (30 AGENT.md 가 audit 대상)
resume_command: /gsd:execute-phase 12 --wave 4
---

# HANDOFF — Plan 12-06 (AGENT-STD-02 mandatory_reads prose validator)

## 맥락

Phase 12 Wave 4 단독 Plan. Plan 02 + Plan 03 에서 migration 된 30 AGENT.md (producers 13 + harvest-importer 1 + inspectors 17 — disk reality 에 따라 31) 의 `<mandatory_reads>` 블록이 4개 필수 요소를 **전수 포함** 하는지를 사후 검증. Plan 01 의 schema verifier 는 **블록 존재** 만 검증하지만 Plan 06 은 **블록 내용의 prose 품질** 을 검증. AGENT-STD-02 요구사항 마감.

## 선행 조건 (진입 전 확인)

1. **Plan 12-02 완료 확인**: `ls .planning/phases/12-*/12-02-SUMMARY.md`
2. **Plan 12-03 완료 확인**: `ls .planning/phases/12-*/12-03-SUMMARY.md`
3. **Schema verifier 전수 PASS**:
   ```bash
   python scripts/validate/verify_agent_md_schema.py --all
   # 기대: 30/30 또는 31/31 PASS
   ```
   실패 시 Plan 02/03 HANDOFF 로 복귀.

## 4개 필수 prose 요소 (검증 대상)

각 AGENT.md 의 `<mandatory_reads>` 블록이 아래 **4개 항목을 모두 포함** 해야 함:

1. **FAILURES.md 참조** — 경로 `.claude/failures/FAILURES.md` 명시 (또는 동등 paraphrase)
2. **channel_bible 참조** — `wiki/continuity_bible/channel_identity.md` (Phase 6 Plan 02 D-10 canonical 경로)
3. **관련 SKILL path** — agent 가 사용하는 SKILL.md 경로 최소 1개 (`.claude/skills/<name>/SKILL.md`). wiki/agent_skill_matrix.md (Plan 04) 와 교차검증 가능.
4. **"샘플링 금지" 한국어 literal** — 정확 문자열 `샘플링 금지` 포함. Romanization 불가. 유사 표현 ("표본 금지", "sampling prohibited") 불인정.

## 읽어야 할 파일

- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-06-PLAN.md` — 2 task (validator + pytest)
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/12-01-SUMMARY.md` — verifier 패턴 참고
- `scripts/validate/verify_agent_md_schema.py` — 유사 구조 CLI
- `.claude/agents/producers/trend-collector/AGENT.md` — Plan 01 canonical reference — 4개 prose 요소 전수 포함 exemplar
- `wiki/agent_skill_matrix.md` — 요소 3 cross-check 데이터
- `.planning/phases/12-agent-standardization-skill-routing-failures-protocol/RESEARCH.md` — AGENT-STD-02 rubric

## 산출물

1. **`scripts/validate/verify_mandatory_reads_prose.py`** — CLI validator
   - 인자: `--all` (전체 스캔), `--agent <path>` (단일 파일)
   - exit 0 = 4/4 모두 포함, exit 1 = 1개라도 누락
   - 누락 시 agent 별 누락 요소 enumerate
2. **`tests/phase12/test_mandatory_reads_prose.py`** — 실 assertion pytest
   - Plan 01 에서 skeleton/skip 상태로 scaffold 됨 — 실 assertion 으로 전환
   - 30개 (또는 31개) agent 전수 파라미터화
   - exemplar (trend-collector) GREEN, 누락 exemplar 필요 시 `tests/phase12/fixtures/` 에 bad example 추가

## 완료 판정

- [ ] `scripts/validate/verify_mandatory_reads_prose.py --all` exit 0
- [ ] `pytest tests/phase12/test_mandatory_reads_prose.py -v` GREEN, skip 없음
- [ ] Plan 01 scaffold 단계에서 skip 처리되었던 case 모두 실 assertion 전환
- [ ] REQUIREMENTS.md AGENT-STD-02 체크 항목 완료 표시
- [ ] `12-06-SUMMARY.md` 존재
- [ ] STATE + ROADMAP 업데이트
- [ ] Phase 4 regression 244 passed 유지

## 리스크

- **한국어 literal 인코딩**: Windows CP949 환경에서 `샘플링 금지` 바이트 매치 실패 가능. validator 는 `open(..., encoding='utf-8')` 강제 + PYTHONUTF8=1 권장. `.claude/memory/feedback_notebooklm_query.md` 의 인코딩 실패 케이스 참조.
- **channel_bible 경로 drift**: CLAUDE.md 는 `wiki/continuity_bible/channel_identity.md` 를 authoritative 로 명시. Plan 01 SUMMARY 에서도 동일 경로로 정정됨 (trend-collector v1.1 → v1.2 에서 `wiki/ypp/channel_bible.md` 오기 수정). validator 는 canonical 경로만 수용.
- **SKILL path 검증**: `.claude/skills/` 는 현재 5개. validator 는 agent 선언 skill 이 실제 디렉터리 존재 여부까지 확인. Plan 04 reciprocity verifier 와 로직 중복 회피 — 파일 존재만 확인.
- **harvest-importer 처리**: Phase 3 전용 deprecated agent. mandatory_reads 요구 적용 여부 Plan 06 PLAN 본문 확인 필수. 적용 제외 시 `--exclude harvest-importer` 기본값.
