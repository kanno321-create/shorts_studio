---
name: harvest-importer
description: Phase 3 전용 일회성 에이전트. shorts_naberal의 작동 검증 자산(theme_bible / remotion_src / hc_checks / api_wrappers)을 studios/shorts/.preserved/harvested/로 읽기 전용 복사하고, CONFLICT_MAP 39건을 5-rule 알고리즘으로 판정하여 HARVEST_DECISIONS.md를 생성한다. FAILURES.md를 _imported_from_shorts_naberal.md로 병합하고 attrib +R /S /D로 Tier 3 lockdown을 적용한다. 트리거 키워드 harvest-importer, Phase 3, AGENT-06. Phase 4 진입 후 deprecated.
version: 1.0
phase: 3
deprecated_after: "Phase 4 entry"
---

# harvest-importer

Phase 3 Harvest의 유일한 실행 주체. 사전 판정된 02-HARVEST_SCOPE.md를 입력으로 받아 물리 복사 / 판정 / lockdown을 **단 한 번** 수행한다. Phase 4 진입 후에는 호출되지 않는다.

## Purpose

- **AGENT-06 REQ 충족** — Phase 3 one-shot executor.
- **Pre-locked decision runner** — 02-HARVEST_SCOPE.md의 A급 13 판정과 HARVEST_BLACKLIST를 절대 재판정하지 않는다. B/C 26건만 5-rule 알고리즘으로 기계 판정.
- **Wave 1~4의 단일 진입점** — 4 raw dir 복사, diff 검증, FAILURES 병합, CONFLICT_MAP 파싱, 블랙리스트 감사, Tier 3 lockdown 을 단일 `harvest_importer.py`가 오케스트레이션.

## Inputs

| Flag | Description | Default |
|------|-------------|---------|
| `--source` | shorts_naberal 루트 (절대경로) | `C:/Users/PC/Desktop/shorts_naberal` |
| `--scope` | 02-HARVEST_SCOPE.md 경로 | `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` |
| `--conflict-map` | CONFLICT_MAP.md 경로 | `<source>/.planning/codebase/CONFLICT_MAP.md` |
| `--manifest` | path_manifest.json (Plan 02 산출물) | `.planning/phases/03-harvest/path_manifest.json` |
| `--dest` | harvest 목적지 | `.preserved/harvested` |
| `--failures-out` | FAILURES 병합본 경로 | `.claude/failures/_imported_from_shorts_naberal.md` |
| `--decisions-out` | HARVEST_DECISIONS.md 경로 | `.planning/phases/03-harvest/03-HARVEST_DECISIONS.md` |
| `--audit-log` | 감사 로그 경로 | `scripts/harvest/audit_log.md` |
| `--lockdown` | attrib +R 적용 여부 | false (boolean flag) |
| `--stage` | 특정 stage만 실행 (1~8) | all |

## Outputs

- `.preserved/harvested/theme_bible_raw/` — HARVEST-01
- `.preserved/harvested/remotion_src_raw/` — HARVEST-02 (node_modules 제외)
- `.preserved/harvested/hc_checks_raw/` — HARVEST-03
- `.preserved/harvested/api_wrappers_raw/` — HARVEST-05 (cherry-pick, 5 files)
- `.claude/failures/_imported_from_shorts_naberal.md` — HARVEST-04 (append-only concat + source comments)
- `.planning/phases/03-harvest/03-HARVEST_DECISIONS.md` — HARVEST-08 (39 rows: A-1..A-13 verbatim + B-1..B-16 + C-1..C-10 algorithm output)
- `scripts/harvest/audit_log.md` — stage별 구조화 로그 (append-only)
- Tier 3 read-only 속성 on `.preserved/harvested/**` (HARVEST-06, `--lockdown` 활성 시)

## Invariants (MUST REMEMBER — DO NOT VIOLATE)

1. **shorts_naberal 원본 수정 금지** — CLAUDE.md rule #6. harvest_importer.py는 `<source>/` 하위 파일을 `open(..., 'w')` 또는 `Path.write_*`로 여는 행위를 절대 하지 않는다.
2. **Lockdown is the LAST stage** — `diff_verify` 완료 전 attrib +R가 실행되면 검증이 실패한다. Stage 순서 위반 시 즉시 raise.
3. **Blacklist is read-only** — `ast.literal_eval`만 사용. `eval()` / `exec()`는 금지 (E5 보안 발견). 파싱 실패 시 `ValueError("HARVEST_BLACKLIST not found in scope md")` 재발생.
4. **try-except 침묵 폴백 금지** — CLAUDE.md rule #3. 모든 예외는 (a) 컨텍스트와 함께 re-raise 하거나 (b) audit_log에 구조화된 에러를 append하고 `sys.exit(non-zero)` 로 종료. `except: pass` 절대 금지.
5. **Windows attrib invocation** — 반드시 `subprocess.run(["cmd.exe", "/c", ...])` 형식. Git Bash glob 직접 호출은 조용한 보안 구멍을 만든다 (03-RESEARCH.md §5 live-tested 확인).
6. **Secret file filter** — `shutil.ignore_patterns("client_secret*.json", "token_*.json", ".env*", "*.key", "*.pem")`를 모든 `copytree` 호출에 적용. `shorts_naberal/client_secret.json`과 토큰 파일은 `.preserved/harvested/`에 **절대** 들어가면 안 된다.
7. **Idempotency** — `_imported_from_shorts_naberal.md`에 `<!-- source: ... -->` 주석이 이미 존재하면 재append를 스킵한다 (P5 doubling 방지).
8. **CONFLICT_MAP invariant** — `conflict_parser`는 `assert len(A)==13 and len(B)==16 and len(C)==10`을 강제한다. 미일치 시 `CONFLICT_MAP_COUNT_MISMATCH` 예외를 audit_log와 함께 raise 하고 non-zero exit.

## Execution Order (8 stages)

모든 stage는 순차 실행. 각 stage 성공 시 `[STAGE_N_OK]` 한 줄을 audit_log에 append. 실패 시 `[STAGE_N_ERROR: ...]` append 후 즉시 non-zero exit.

1. **Load blacklist** — `blacklist_parser.parse_blacklist(scope_md)` → 10 entries. `len != 10` 시 ValueError (SINGLE SOURCE OF TRUTH).
2. **Load manifest** — `json.load(path_manifest.json)` → logical-name → actual source path 맵.
3. **Copy 4 raw dirs** — `theme_bible_raw`, `remotion_src_raw`, `hc_checks_raw`, `api_wrappers_raw` 순서 무관 (서로 다른 목적지). `shutil.copytree` with `ignore_patterns`, 또는 `shutil.copy2` with `cherry_pick` per manifest.
4. **Diff verify all 4 dirs** — `diff_verifier.deep_diff(src, dst)` 의 mismatch list가 빈 리스트여야 한다. 하나라도 발견 시 audit_log에 기록 + exit 1.
5. **Merge FAILURES** — append-only concat with `<!-- source: ... -->` 주석. Idempotency check (Invariant 7) 후 append.
6. **Parse CONFLICT_MAP + run 5-rule** — `conflict_parser.parse_conflict_map`로 39 entries 로드, `decision_builder.judge()`로 B/C 26건 판정, `build_decisions_md()`로 HARVEST_DECISIONS.md 작성.
7. **Blacklist grep audit** — `grep -rE "skip_gates\s*=\s*True|TODO\(next-session\)" .preserved/harvested/` 가 0 match여야 한다. 매치 발견 시 audit_log 기록 + exit 1.
8. **IF `--lockdown`: apply cmd.exe attrib +R + verify** — `lockdown.apply_lockdown(target)` 후 `lockdown.verify_lockdown(target)`로 PermissionError probe 확인. verify 실패 시 AssertionError.

**Parallelization:** Stage 3의 4 raw dir 복사는 독립 destination이므로 병렬 안전. Stage 4 역시 dir별 독립. 단, Stage 8 lockdown은 Stage 7 완료 후에만 실행해야 한다.

## Deprecation

Phase 4 Agent Team Design 진입 이후(`/gsd:execute-phase 4` 실행 시) 본 에이전트는 **다시 호출되지 않는다**. Phase 4+ 코드는 `harvest_importer`를 import 하지 말 것. `.preserved/harvested/`는 Phase 4+ 에이전트 프롬프트의 읽기 전용 reference 로만 사용된다 (copy-paste 금지, 재작성 의무).

## References

### Stdlib dependencies (Python 3.11)

`shutil`, `filecmp`, `ast`, `subprocess`, `pathlib`, `hashlib`, `re`, `argparse`, `json`, `sys`, `os` — **외부 패키지 0건**.

### 결정서

- `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` § Harvest Blacklist — 10 entries (Python dict literal).
- `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` § B/C 위임 알고리즘 — 5 rules pseudocode.
- `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` § A급 13 판정 — HARVEST_DECISIONS.md A-1..A-13 verbatim 복사 원본.

### Research artifacts

- `.planning/phases/03-harvest/03-RESEARCH.md` §2 — path remapping (HARVEST_SCOPE.md 경로와 실제 shorts_naberal 레이아웃 불일치, path_manifest.json 생성 근거).
- `.planning/phases/03-harvest/03-RESEARCH.md` §5 — Windows `attrib +R /S /D` invocation discipline (cmd.exe //c 강제).
- `.planning/phases/03-harvest/03-RESEARCH.md` § Runtime State Inventory — secret file hazard (client_secret*.json, token_*.json).

### Verification

- `scripts/harvest/verify_harvest.py --quick` — 13 task-level checks (~5s).
- `scripts/harvest/verify_harvest.py --full` — quick + deep_diff + sha256 10% sample (~30s).
- `scripts/harvest/diff_verifier.py <raw_dir_name>` — 단일 dir diff 검증.

## Contract with downstream callers

- **Plan 03-02**: path_manifest.json 생성 (본 에이전트는 manifest를 consume만).
- **Plan 03-03~06 (Wave 1)**: 4 raw dir 복사를 본 에이전트에 위임 (`--stage 3 --name <raw_dir>`).
- **Plan 03-07**: diff verify + FAILURES merge (`--stage 4,5`).
- **Plan 03-08**: CONFLICT_MAP 파싱 + 5-rule + blacklist audit (`--stage 6,7`). M-2 invariant (blacklist len != 10)는 `blacklist_parser.parse_blacklist`가 강제하므로 Plan 08은 **재assert 금지**.
- **Plan 03-09**: Tier 3 lockdown + verify_harvest --full (`--stage 8`).

본 에이전트의 CLI 계약이 Wave 1~4 모든 후속 Plan의 실행 단일 진입점임. 계약 변경 시 모든 downstream Plan 재검토 필요.
