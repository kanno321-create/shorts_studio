---
gsd_state_version: 1.0
milestone: v1.0.1
milestone_name: milestone
status: executing
last_updated: "2026-04-19T03:18:03.473Z"
progress:
  total_phases: 10
  completed_phases: 3
  total_plans: 35
  completed_plans: 30
  percent: 86
---

# STATE — naberal-shorts-studio

**Last updated:** 2026-04-19T03:00:00Z
**Session:** #17 (✅ Phase 5 Plan 01 Wave 1 FOUNDATION shipped. Python module skeleton (scripts/orchestrator/ + scripts/hc_checks/), GateName IntEnum 15 members, GATE_DEPS DAG with import-time graphlib validation, 10-class exception hierarchy (OrchestratorError + 9 subclasses), .claude/deprecated_patterns.json 6 regex entries activates pre_tool_use Hook (RESEARCH §10 gap closed), tests/phase05/ scaffold 18/18 PASS, 3 validation CLIs (verify_line_count / verify_hook_blocks / phase05_acceptance). Commits: a3e9476 (Task 1 module skeleton) + 8c19c23 (Task 2 deprecated_patterns + gitignore state/) + cf9874d (Task 3 tests scaffold) + 2fea858 (Task 4 validation CLIs). 5 REQs done: ORCH-02/03/07/08/09. Cumulative project 52/96 REQs = 54%. Ready for Plan 05-02 CircuitBreaker.)

---

## Project Reference

- **Core Value:** 외부 수익(YouTube 광고) 실제 발생 — YPP 진입 궤도(1000구독 + 10M views/년) 확보. 기술 성공 ≠ 비즈니스 성공.
- **Project Type:** Layer 2 도메인 스튜디오 (첫 번째) — naberal_harness v1.0.1 상속
- **Granularity:** fine (10 phases)
- **Mode:** yolo (자율 실행, GATE로 인간 감독)
- **Through-line:** shorts_naberal 39 drift conflict (A:13/B:16/C:10) 재발 차단

---

## Current Position

Phase: 05 (orchestrator-v2-write) — EXECUTING
Plan: 4 of 10

- **Phase:** 5
- **Next Plan:** 05-PLAN (Phase 5 Orchestrator v2 Write — `scripts/orchestrator/shorts_pipeline.py` 500~800줄 state machine, 12 GATE DAG, CircuitBreaker, Checkpointer, 영상/음성 분리 합성, Low-Res First 렌더; ORCH-01~12 + VIDEO-01~05 = 17 REQs)
- **Status:** Ready to execute
- **Progress:** [█████████░] 86%

---

## Phase Completion

- ✅ **Phase 1: Scaffold** — 2026-04-18 (session #10)
  - INFRA-01, INFRA-03, INFRA-04 완료
  - `studios/shorts/` 스캐폴드, Hook 3종 설치, 공용 5 스킬 상속
- ✅ **Phase 3: Harvest** — 2026-04-19 (session #15) — HARVEST-01/02/03/04/05/06/07/08 + AGENT-06 완료
  - ✅ Plan 03-01: harvest-importer AGENT.md + 7 Python stdlib modules (AGENT-06)
  - ✅ Plan 03-02: path_manifest.json ground-truth registry (studio@609c3f8)
  - ✅ Plan 03-03: theme_bible_raw copy (studio@fba21e4, HARVEST-01)
  - ✅ Plan 03-04: remotion_src_raw copy (studio@4bc7ece, HARVEST-02)
  - ✅ Plan 03-05: hc_checks_raw cherry_pick (studio@51205ba, HARVEST-03)
  - ✅ Plan 03-06: api_wrappers_raw cherry_pick (studio@aeac16b, HARVEST-05)
  - ✅ Plan 03-07: aggregate diff ALL_CLEAN + FAILURES merge (studio@ad98b32 + 1ff5768, HARVEST-04)
  - ✅ Plan 03-08: 03-HARVEST_DECISIONS.md 39 rows + 7-check blacklist audit (studio@15b827f + c14ab95, HARVEST-07/08)
  - ✅ Plan 03-09: Tier 3 attrib +R lockdown + verify_harvest --full 15/15 PASS (studio@8ae370e + d4fc5e4, HARVEST-06)
- ✅ **Phase 2: Domain Definition** — 2026-04-19 (session #14) — INFRA-02 완료
  - ✅ Plan 02-01: STRUCTURE.md v1.0.0 → v1.1.0 bump + wiki/ whitelisted (harness@8a8c32b)
  - ✅ Plan 02-02: harness/wiki/ Tier 1 scaffold (folder + README.md) created (harness@1ff2e34)
  - ✅ Plan 02-03: studios/shorts/wiki/ Tier 2 (5 categories + README + 5 MOC) + .preserved/harvested/ Tier 3 scaffold (committed in consolidated f360e17)
  - ✅ Plan 02-04: studios/shorts/CLAUDE.md 5 TODO replacement + line 7 typo fix (6 semantic sites via 5 Edit ops; committed in consolidated f360e17)
  - ✅ Plan 02-05: 02-HARVEST_SCOPE.md (175 lines) — A급 13 사전 판정 + HARVEST_BLACKLIST dict + 4 raw 매핑 + B/C 위임 알고리즘 (committed in consolidated f360e17)
  - ✅ Plan 02-06: 12/12 VALIDATION PASS + consolidated studio commit f360e17 (9 files, +449/-7) + SC 4/4 achieved + 02-VALIDATION.md frontmatter flipped (nyquist_compliant=true, wave_0_complete=true, status=complete)
- ✅ **Phase 4: Agent Team Design** — 2026-04-19 (session #16) — 34/34 REQs complete, 32 agents shipped
  - ✅ Plan 04-01: Wave 0 FOUNDATION — 6 shared files + 5 stdlib validators + 14/14 pytest PASS (studio@0dcb007 + cd1d074 + daca457 + 5a70504)
  - ✅ Plan 04-02: Wave 1a Inspector Structural 3 (ins-blueprint-compliance + ins-timing-consistency + ins-schema-integrity; maxTurns=1)
  - ✅ Plan 04-03: Wave 1b Inspector Content 3 — ins-factcheck (maxTurns=10 RUB-05 exception) + ins-narrative-quality + ins-korean-naturalness (studio@c29f82a + 153c95b)
  - ✅ Plan 04-04: Wave 1c Inspector Style 3 — ins-tone-brand (maxTurns=5) + ins-readability + ins-thumbnail-hook (studio@df5a1b3)
  - ✅ Plan 04-05: Wave 2a Inspector Compliance 3 — ins-license + ins-platform-policy + ins-safety (studio@b6cfedc + af4635e + c53ccef). AF-4/13 100% block.
  - ✅ Plan 04-06: Wave 2b Inspector Technical 3 — ins-audio-quality + ins-render-integrity + ins-subtitle-alignment (studio@f468523 + ef64ac3 + 3d0b250).
  - ✅ Plan 04-07: Wave 2c Inspector Media 2 — ins-mosaic + ins-gore (studio@6cea65f). AF-5 100% block.
  - ✅ Plan 04-08: Wave 3 Producer Core 6 + 3단 분리 3 (studio@8bcf052 Core + d1f4ade 3split + 19fb39e tests + 9a82729 docs). AGENT-01 + AGENT-02 + RUB-03 + CONTENT-03 + CONTENT-07 satisfied.
  - ✅ Plan 04-09: Wave 4 Producer Support 5 + Supervisor 1 (studio@7b089d8 Support + 1497c94 supervisor + 9047278 tests + 90223c3 docs). AGENT-03 + AGENT-05 + AUDIO-01/02/03 satisfied; _delegation_depth guard in shorts-supervisor.
  - ✅ Plan 04-10: Wave 5 Integration + SC1 reconciliation (studio@778745a Task1 + 62c0758 VALIDATION flip + b35c64b ROADMAP SC1 + 8452876 REQUIREMENTS 34/34). harness_audit score 100. 244/244 pytest PASS. GAN_CLEAN 17/17. LogicQA 17/17. **PHASE 4 COMPLETE.**
- ⏳ **Phase 5~10**: Pending (Phase 4 complete, Phase 5 Orchestrator v2 ready to start)

---

## Performance Metrics

- **Requirements Mapped:** 96 / 96 (100%)
- **Requirements Completed:** 47 / 96 (49%) — Phase 1 (INFRA-01/03/04 = 3) + Phase 2 (INFRA-02 = 1) + Phase 3 (HARVEST-01..08 + AGENT-06 = 9) + Phase 4 (34/34 complete 2026-04-19 via Plans 04-01..10)
- **Orphaned REQ:** 0
- **Phases:** 10 (granularity=fine 목표 구간 내)
- **Harness Audit Baseline:** ✅ 100 (Phase 4 Plan 10 Wave 5, threshold 80, 20-point margin) — AUDIT-02 Phase 10 baseline prep satisfied. Phase 7 Integration Test 재검증 예정.
- **YouTube 채널 구독자:** TBD (Phase 3 Harvest 시 현황 파악 — SUMMARY §12 open question)
- **월 운영비 예산:** ~$128/월 표준 (Sonnet $12 + Opus $9 + Kling $86.4 + Typecast $20 + Nano Banana $0.64)

---

## Accumulated Context

### Key Decisions (D-1 ~ D-10)

PROJECT.md § Key Decisions 참조. 10개 결정 모두 Pending 상태 — 각 Phase 완료 시점에 해당 D# 검증 + 상태 업데이트.

### Decisions Made This Session

1. **Phase 구조 10개 확정** — SUMMARY §10 Build Order 기반, DOMAIN_CHECKLIST 10단계와 1:1 대응
2. **Phase 4에 Content/Audio/Subt/Compliance REQ 통합** — rubric 동시 정의 원칙 적용 (분산 시 커플링 깨짐)
3. **Phase 5에 Video REQ 통합** — 오케스트레이터가 영상 생성 API wrapping 담당
4. **Phase 6에 FAIL-01~03 배치, FAIL-04는 Phase 10** — 저수지 인프라는 초기 구축, "첫 1~2개월 patch 금지"는 운영 단계 규율
5. **KPI-05/06(Taste Gate + 목표 지표)는 Phase 9, KPI-01~04(자동 수집 + Auto Research Loop)는 Phase 10** — taste 프로토콜 설치 후 실 운영에서 데이터 수집

### Session #12 Decisions (Phase 2 context)

6. **D2-A Tier 1 wiki = minimal** — 빈 폴더 + README.md만. 실 노드는 Phase 6. 이유: 선제 시드 = 나중 갈아엎기 리스크.
7. **D2-B Tier 2 wiki = MOC skeleton** — 5 카테고리(algorithm/ypp/render/kpi/continuity_bible) + 각 MOC.md. Phase 4 에이전트 prompt 참조 경로 고정 목적.
8. **D2-C Harvest scope = A급 13건 사전** — CONFLICT_MAP A급만 Phase 2에서 판정. B급/C급은 Phase 3 harvest-importer.
9. **D2-D CLAUDE.md 치환 = 중간** — D-1~D-10 반영, Phase 4~5 결정 수치는 TBD(Phase X) 명시.

### Session #14 Decisions (Plan 05 — HARVEST_SCOPE.md)

10. **A급 13 판정 분포 = 2/3/8** — 승계 2 (A-2 cuts[], A-9 탐정님 금지) / 폐기 3 (A-5 TODO, A-6 skip_gates, A-11 longform-scripter) / 통합-재작성 8 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13). RESEARCH.md Draft Judgments 와 100% 일치.
11. **HARVEST_BLACKLIST Python dict 형식** — Phase 3 harvest-importer 가 eval 없이 로드 가능. 11 entries: orchestrate.py:1239-1291 (A-6) + TODO 4곳 (A-5) + longform/ (A-11) + create-video/ (A-12) + create-shorts/SKILL.md (A-3) + selenium (AF-8) + orchestrate.py 전체 (D-7).
12. **4 raw 디렉토리 매핑 = HARVEST-01/02/03/05 와 1:1** — theme_bible_raw (HARVEST-01), remotion_src_raw (HARVEST-02), hc_checks_raw (HARVEST-03), api_wrappers_raw (HARVEST-05). HARVEST-04(FAILURES) 는 별도 이관 경로 (`_imported_from_shorts_naberal.md`).
13. **B/C급 26 위임 알고리즘 = 5-rule pseudocode** — blacklist > scope-boundary > session-77-canonical > cosmetic-cleanup > default-rewrite. Phase 3 harvest-importer 가 parse 하여 사용.

### Session #15 Decisions (Plan 03-07 — DIFF-VERIFY + FAILURES-MERGE)

18. **Aggregate diff = inline Python fallback** — diff_verifier.py --all flag not yet wired (Plan 01 scope limited to per-dir CLI). Inline implementation reuses identical deep_diff + filecmp.cmp(shallow=False) semantics; wiring --all is candidate improvement for future plan but not required for Phase 3 correctness.
19. **SOURCES locked list pattern (B-2 FIX)** — explicit `[Path('.../orchestrator.md')]` constant NOT glob expansion. RESEARCH.md §6 verified 1 source exists at 2026-04-19. Future FAILURES additions MUST extend list explicitly — code comment documents invariant. Prevents silent drift when shorts_naberal adds new FAILURES files.
20. **Ignore match via fnmatch.fnmatchcase** — matches shutil.ignore_patterns glob semantics used at Wave 1 copy time. Substring `in` containment would produce false positives on patterns like `*.pyc` vs `file.pyc.bak`. Critical for diff_verifier correctness.
21. **HARVEST-04 satisfied via idempotent marker-guarded append** — `<!-- source: ... -->` + `<!-- END source: ... -->` pair enables deterministic idempotency check; sha256 per source block provides downstream integrity audit path. Archive is read-only (D-2 저수지 regime reference for Phase 10 첫 1~2개월 SKILL patch 금지).

### Session #15 Decisions (Plan 03-09 — LOCKDOWN + FULL-VERIFY)

26. **Lockdown = attrib +R via cmd.exe subprocess (M-1 module form)** — direct `attrib +R /S /D "path/*"` in Git Bash fails silently with Korean Windows "매개 변수 형식이 틀립니다". Mandatory `subprocess.run(["cmd.exe", "/c", f"attrib +R /S /D {win_path}\\*"])` with backslash path normalization. verify_lockdown PermissionError probe is the sole acceptance signal (independent raw `attrib /s` listing shows 'A    R' flag on every file as secondary evidence, 55 files confirmed).
27. **Rule 3 deviation: verify_harvest.py manifest iteration fix** — `_deep_diff_all` + `_sha256_spot_sample` crashed on `AttributeError: 'str' object has no attribute 'get'` because they iterated the entire manifest dict without filtering out top-level metadata keys (`manifest_version`, `generated_at`, `source_root`, `global_ignore`) which are strings/lists, and `blacklist_exclusions` which is a dict with different shape (no `source`/`dest`). Added `isinstance(entry, dict) and "dest" in entry` guard — matches the exact raw_dir entry contract from path_manifest.json. Fix is byte-safe for both tree-copy (source set) and cherry-pick (source None) raw dirs.
28. **PYTHONIOENCODING=utf-8 required on Windows cp949** — verify_harvest.py emits em-dash `—` inside error detail messages (e.g., `write SUCCEEDED on ... — lockdown not applied`). Default cp949 codec raises UnicodeEncodeError. Post-lockdown the FAIL path never executes, so the final PASS run is unaffected, but all development/diagnostic runs must use `PYTHONIOENCODING=utf-8`. Documented in audit_log.md + this SUMMARY.

### Session #16 Decisions (Plan 04-01 — Wave 0 FOUNDATION)

29. **rubric_stdlib_validator extended beyond RESEARCH.md §8.2 baseline (Rule 2 deviation)** — added `additionalProperties=false` enforcement + recursive `_validate_value` for `array.items` child objects + recursive object-inside-object support. Without these, the Task 3 <behavior> `test_evidence_wrong_type` would pass vacuously on evidence=[{ wrong_key: "x" }] because §8.2 did not walk items. Critical for RUB-04 contract to actually be enforced.
30. **MUST REMEMBER position via `ratio_from_end ≤ 0.4`** — scales with agent size rather than absolute line count. Current `agent-template.md` ratio is 0.06 (MUST REMEMBER at line 169/179, 10 lines from end). AGENT-09 RoPE Lost-in-the-Middle compliance via structural rule, not line count.
31. **harvest-importer excluded via CLI flag `--exclude harvest-importer`, not content change** — harvest-importer uses "Invariants (MUST REMEMBER — DO NOT VIOLATE)" header text (Phase 3 legacy format). Rewriting would be out-of-scope Phase 3 modification. `--exclude` is the explicit accommodation documented in Plan Task 3 behavior spec.
32. **AGENT.md template variants inline, single file** — Producer/Inspector/Supervisor variants in one `agent-template.md` reduces drift between variants. Future agents copy the applicable section rather than maintaining 3 separate template files.
33. **Sample bank composition — AF-13 hit all 10 RESEARCH.md §5.5 core artists + Korean negatives split 4/2/2/2** — AF-13 required ≥5, shipped 10/10 (BTS/BLACKPINK/NewJeans/IVE/aespa/LE SSERAFIM/Stray Kids/SEVENTEEN/NCT/TWICE). Korean negative 10 = 4 mixed_register + 2 self_title_leak + 2 informal + 2 foreign_word_overuse — added "반말 in polite register" as 4th subclass because SUBT-02 target is ≥9/10 FAIL detection (not ≥8).
34. **Package-mode + direct-mode dual invocation guard** — `if __package__ in (None, "")` in validate_all_agents.py + harness_audit.py allows both `py -m scripts.validate.harness_audit` (CI/CD) and direct `py scripts/validate/harness_audit.py`. Critical for future orchestration flexibility. Relied on PEP 420 namespace packages (no `scripts/__init__.py`) to avoid breaking existing `scripts/harvest/` pattern.

### Session #16 Decisions (Plan 04-05 — Wave 2a Compliance Inspector 3)

35. **LogicQA "critical override" rule codified** — Compliance 3 Inspector 공통으로 일부 sub_q (ins-license q1/q2/q3 / ins-platform-policy q1 / ins-safety q1-q4) 가 N 이면 main_q 는 다수결 결과 무관하게 FAIL 강제. Phase 4 의 majority-vote 원칙에 대한 **유일한 허용 예외**이며, 100% block bar (AUDIO-04 / COMPLY-01 / COMPLY-06) 가 다수결보다 상위 규범이라는 점을 MUST REMEMBER clause #3 에 명시. 다른 카테고리 (Structural / Content / Style / Technical) 는 순수 다수결 유지.
36. **Royalty-free whitelist supersedes K-pop regex** — `test_compliance_blocks.py::af13_blocked` 에서 whitelist 체크를 artist/title regex 보다 **먼저** 실행. af13-014 (Epidemic Sound - Suspense Strings) 같은 PASS 엔트리의 false-positive 방지. ins-license 프롬프트 본문도 "whitelist 외 도메인 또는 license_type 누락 시 FAIL" 을 1 차 게이트로, K-pop regex 를 2 차 게이트로 분리 기술 → Inspector contract 와 test 구현이 동일한 우선순위 계층을 사용.
37. **AF-4 blocklist mirrors only FAIL entries** — `af4_blocked()` 에서 `expected_verdict != "FAIL"` 엔트리는 스킵. "가상 탐정 시로" (af4-012, PASS 엔트리) 가 다른 af4_voice_clone 엔트리의 부분 문자열과 우연히 매치되는 edge case 를 방지. blocklist 는 bank 자체가 아닌 Inspector 계약의 mirror.
38. **ins-safety blocklist = Phase 4 seed, Phase 9 확장** — 4 axes × 8~11 tokens = 38+ seed entries (최소 15 요구). Phase 9 Taste Gate 에서 sample harvesting 으로 확장 예정. seed 토큰화는 문장이 아닌 키워드 단위 → 감사/확장 용이.
39. **ins-safety ↔ ins-gore 역할 경계 양쪽 문서화** — ins-safety AGENT.md Purpose + MUST REMEMBER #8, 그리고 향후 ins-gore (Plan 07) 도 동일 경계를 본문에 명시해야 함. 담당 축: ins-safety = 대본 텍스트 담론, ins-gore = 시각 프레임 픽셀 수위. Phase 07 에서 ins-gore 가 텍스트 차원의 재판정을 추가하지 않도록 미리 차단.
40. **Rule 3 deviation: Pytest ScopeMismatch 회피 패턴** — `@pytest.fixture(scope="module")` 가 function-scoped `repo_root` 를 의존하면 16 테스트가 setup 단계에서 ScopeMismatch 로 실패. 모듈 상단 `_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]` 로 import-time resolve 후 fixture 에서 사용 (conftest.py 와 동일 패턴). tests/phase04/ 향후 테스트 모두 이 패턴 준수.

### Session #17 Decisions (Plan 05-01 — Wave 1 FOUNDATION)

41. **GateName as IntEnum (not Enum) — canonical D-2 numbering 0..14** — `IntEnum` chosen so Checkpointer can name files `gate_{int(gate):02d}.json` for natural lexical sort on resume. 15 states total (IDLE=0 bookend, 13 operational TREND..MONITOR, COMPLETE=14 bookend). `len(GateName) == 15` is the contract assertion every downstream plan imports.
42. **`_validate_dag()` uses `static_order()` alone, not `prepare()` + `static_order()`** — `graphlib.TopologicalSorter` raises `ValueError("cannot prepare() more than once")` when both are called. `static_order()` internally calls `prepare()` and surfaces `graphlib.CycleError` on cycle, which is the import-time fail-fast guarantee we need. Inline comment in gates.py documents the constraint so future contributors don't re-add explicit prepare().
43. **Exception class named `T2VForbidden` (plan-mandated) — SC5 grep narrowed accordingly** — CONTEXT D-13 interface block line 173 explicitly specifies `class T2VForbidden(OrchestratorError): ...`. A case-insensitive `grep -riE "t2v"` would always false-positive on the guard class itself. Rule 1 deviation: `phase05_acceptance.py` SC5 grep uses `(^|[^A-Za-z_])t2v([^A-Za-z_]|$)|text_to_video|text2video` (case-sensitive, word-boundary) to catch lowercase identifier usage (function calls, attribute access) while leaving the PascalCase `T2VForbidden` sentinel untouched. Preserves plan contract exactly.
44. **verify_hook_blocks.py per-tool payload shape** — `pre_tool_use.py` reads `input.content` for Write, `input.new_string` for Edit, `input.edits[*].new_string` for MultiEdit. Naïve uniform payload (`{"content": "..."}` for all tool_names) would silently false-pass because the Hook would see an empty string for Edit/MultiEdit. The validator now branches on `tool_name` to construct the correct shape — matches the Hook's real-world invocation contract.
45. **UTF-8 subprocess encoding reaffirmed (STATE #28 pattern)** — `phase05_acceptance.py` and `verify_hook_blocks.py` both set `encoding="utf-8"` on `subprocess.run(...)` calls. Windows default cp949 cannot decode em-dash (`—`) or Korean reason text that `pre_tool_use.py` emits in deny messages or that pytest warnings emit from Korean-content test fixtures. Without this, acceptance CLI raises `UnicodeDecodeError` mid-script — violating the plan's "MUST not raise Python exceptions" rule.
46. **Namespace-marker `__init__.py` pattern** — `scripts/orchestrator/api/__init__.py` and `scripts/hc_checks/__init__.py` are docstring-only files with zero imports. Docstring explains which future plan (06 / 08) fills the package. Creates the Python package without committing to any implementation detail prematurely; avoids `from __future__ import annotations` being the first non-comment line on disk.

### Session #15 Decisions (Plan 03-08 — HARVEST-DECISIONS + BLACKLIST-AUDIT)

22. **Blacklist count invariant delegation (Plan 01 M-2 contract honored)** — Plan 08 does NOT re-assert `len(blacklist) == 10`; that invariant is owned by `blacklist_parser.parse_blacklist()` which raises ValueError on mismatch. Redundant asserts would violate DRY + SSoT. A/B/C count assertion (13/16/10) IS preserved at decision_builder entry because it validates a DIFFERENT invariant (CONFLICT_MAP parse integrity).
23. **Rule 1 deviation: narrowed Task 2 Audit 3 longform check** — plan's original `find ... -path "*/longform/*"` false-matched 6 legitimate Remotion composition files at `remotion_src_raw/components/longform/*.tsx` (harvested per Plan 03-04 studio@4bc7ece VALIDATION PASS). HARVEST_BLACKLIST `{path: "longform/"}` prohibits harvesting from `shorts_naberal/longform/` **source tree**, not arbitrary nested `longform/` subdirectories inside legitimately harvested source. Narrowed to `-maxdepth 1 -type d -name *longform*` — matches blacklist INTENT. Documented in audit_log.md + 03-08-SUMMARY.md.
24. **Inline Python fallback over harvest_importer --stage 6** — matches Wave 1 precedent (03-04-SUMMARY.md). Stage 6 requires prior stages 1-2 in same invocation to populate blacklist/manifest; direct call to `decision_builder.build_decisions_md()` is byte-identical semantics. `.tmp_build_decisions.py` used and deleted post-run (no repo pollution).
25. **39-row decision table verdict distribution locked** — 승계=2 (A-2, A-9) / 폐기=15 (A-5, A-6, A-11 + B-1, B-3, B-5, B-6, B-8, B-10, B-12, B-15 + C-1, C-6, C-7, C-8) / 통합-재작성=20 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 + B-2, B-4, B-7, B-9, B-11, B-13, B-14, B-16 + C-3, C-4, C-9, C-10) / cleanup=2 (C-2, C-5). Rule distribution for B/C 26: rule1=10, rule2=2, rule3=0, rule4=2, rule5=12 (sum=26 ✓). Phase 4 agent designs can cite this table authoritatively.

### Session #14 Decisions (Plan 06 — Phase 2 Gate)

14. **Phase 2 게이트 = 12/12 VALIDATION PASS + consolidated commit** — Phase 3 진입 허가. 모든 pre-commit check 통과 시에만 commit, 하나라도 FAIL 시 commit 보류 원칙 (다행히 전부 통과).
15. **2-W3-03 literal pattern mismatch 관리** — VALIDATION.md status 컬럼에 나노트 ("literal pattern mismatch due to backticks — 8 rules semantically present, verified via flexible grep") 기록. 규칙 자체는 완전 존재, Phase 3 이후 validation script 개선 time 에 패턴 수정.
16. **Consolidated commit 스코프 = Phase 2 artifacts only** — `.claude/`, `.gitignore`, `README.md`, `SESSION_LOG.md`, `WORK_HANDOFF.md`, `.planning/config.json` 은 Phase 2 산출물이 아니므로 미포함. CLAUDE.md + wiki/ + .preserved/harvested/.gitkeep + 02-HARVEST_SCOPE.md 만 staged.
17. **harness vs studio 레포 분리 유지** — harness (8a8c32b + 1ff2e34) + studio (f360e17) 두 레포가 독립적으로 commit. REMOTE-02 (Phase 8) 전까지 푸시 없음.

### Active Todos (Phase 3 Harvest next)

- [x] Phase 2 gray areas 확정 (4건: Tier1 minimal / Tier2 MOC skeleton / A급 13 사전 판정 / CLAUDE.md 중간)
- [x] 02-CONTEXT.md + 02-DISCUSSION-LOG.md 커밋 (9b9039f)
- [x] `/gsd:plan-phase 2` 실행 → 02-01~06-PLAN.md 생성 (6 plans)
- [x] **Phase 2 Plan 01 execute → STRUCTURE.md v1.0.0→v1.1.0 bump (harness@8a8c32b, 2026-04-19)**
- [x] **Phase 2 Plan 02 execute → harness/wiki/ Tier 1 scaffold 생성 (harness@1ff2e34, 2026-04-19)**
- [x] **Phase 2 Plan 03 execute → studios/shorts/wiki/ Tier 2 + Tier 3 scaffold 생성 (committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 04 execute → CLAUDE.md 5 TODO 치환 + line 7 typo fix (committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 05 execute → 02-HARVEST_SCOPE.md A급 13 사전 판정 (175 lines, committed in f360e17, 2026-04-19)**
- [x] **Phase 2 Plan 06 execute → studio Phase 2 consolidated commit f360e17 + 12/12 VALIDATION PASS + SC 4/4 achieved (2026-04-19)**
- [x] **Phase 3 Harvest 진입**: `/gsd:execute-phase 3` — harvest-importer 에이전트 입력 = 02-HARVEST_SCOPE.md
- [x] **Phase 3 Plan 03-02 execute** → path_manifest.json ground-truth registry (studio@609c3f8, 2026-04-19) — 4 raw_dir sources verified, global_ignore blocks 5 secret patterns, 5/5 api_wrapper cherry_picks confirmed present
- [x] **Phase 3 Plan 03-01 execute** → harvest-importer AGENT.md + 7 Python stdlib modules (AGENT-06) — shipped prior to Wave 1
- [x] **Phase 3 Plan 03-03 execute** → theme_bible_raw copy (studio@fba21e4, 2026-04-19) — 7 channel bibles byte-identical, diff_verifier mismatches=[] (HARVEST-01)
- [x] **Phase 3 Plan 03-05 execute** → hc_checks_raw cherry_pick (studio@51205ba, 2026-04-19) — hc_checks.py 1129 lines + test_hc_checks.py byte-identical, orchestrate.py blacklist enforced (HARVEST-03)
- [x] **Phase 3 Plan 03-06 execute** → api_wrappers_raw cherry_pick (studio@aeac16b, 2026-04-19) — 5/5 wrappers byte-identical (elevenlabs_alignment, tts_generate, _kling_i2v_batch, runway_client, heygen_client), 0 selenium imports, orchestrate.py absent (HARVEST-05)
- [x] **Phase 3 Plan 03-04 execute** → remotion_src_raw copy (studio@4bc7ece, 2026-04-19) — 40 files / 0.161 MB, node_modules 758 MB excluded via shutil.ignore_patterns, diff_verifier mismatches=[], __pycache__/secret 0 hits (HARVEST-02)
- [x] **Phase 3 Wave 1 complete** → all 4 raw dirs shipped: theme_bible_raw (03-03) + remotion_src_raw (03-04) + hc_checks_raw (03-05) + api_wrappers_raw (03-06)
- [x] **Phase 3 Plan 03-07 execute** → aggregate diff ALL_CLEAN (studio@ad98b32) + FAILURES merge _imported_from_shorts_naberal.md (studio@1ff5768, 500 lines, sha256=978bb9381fee..., idempotent SOURCES-locked, HARVEST-04 satisfied, D-2 저수지 regime ready)
- [x] **Phase 3 Plan 03-08 execute** → 03-HARVEST_DECISIONS.md 39 rows (studio@15b827f, A:13 verbatim + B:16 + C:10 via 5-rule algorithm, verdict dist 2/15/20/2, rule dist 10/2/0/2/12 for B/C) + 7-check blacklist grep audit PASS (studio@c14ab95, 0 matches across all audits, Rule 1 deviation: narrowed longform check from overbroad */longform/* to top-level raw dir detection). HARVEST-07 + HARVEST-08 satisfied.
- [x] **Phase 3 Plan 03-09 execute** → Tier 3 lockdown (studio@8ae370e, attrib +R /S /D recursive on .preserved/harvested/, 55 files R-flagged, lockdown.verify_lockdown PermissionError probe PASS) + verify_harvest --full 15/15 PASS (studio@d4fc5e4, 13 task checks + deep_diff 2 tree-copy dirs clean + sha256 5-file spot sample hash-match; Rule 3 fix: verify_harvest.py _deep_diff_all + _sha256_spot_sample filter non-dict manifest entries). 03-VALIDATION.md status=complete/nyquist_compliant=true/wave_0_complete=true. HARVEST-06 satisfied.
- [x] **Phase 3 COMPLETE** — All 9 REQs (HARVEST-01..08 + AGENT-06) satisfied. .preserved/harvested/ Tier 3 immutable locked. Ready to enter Phase 4 Agent Team Design.
- [x] **Phase 4 Plan 04-01 execute** → Wave 0 FOUNDATION (2026-04-19, session #16). 6 shared files + 5 validators + 14/14 pytest PASS. studio@0dcb007 (schemas+template+VQQA) + studio@cd1d074 (AF+Korean banks) + studio@daca457 (TDD RED) + studio@5a70504 (TDD GREEN). RUB-04 + AGENT-07/08/09 + COMPLY-01..06 + AUDIO-04 + SUBT-02 = 12 REQs satisfied. harness_audit score 95.
- [x] **Phase 5 Plan 05-01 execute** → Wave 1 FOUNDATION (2026-04-19, session #17). scripts/orchestrator/ + scripts/hc_checks/ packages + GateName IntEnum 15 members + GATE_DEPS DAG (graphlib import-time validation) + 10-class exception hierarchy + .claude/deprecated_patterns.json 6 regexes (pre_tool_use Hook now active; RESEARCH §10 gap closed) + tests/phase05/ scaffold (18/18 PASS) + 3 validation CLIs. studio@a3e9476 (Task 1) + 8c19c23 (Task 2) + cf9874d (Task 3) + 2fea858 (Task 4). ORCH-02/03/07/08/09 = 5 REQs satisfied. Rule 1 deviations: graphlib double-prepare fix + Edit payload shape + cp949 UTF-8 + SC5 grep narrowed for T2VForbidden guard class.

### Blockers

- **현재 없음** (Roadmap 확정 완료)

### Open Questions (Phase별 deferred — SUMMARY §12)

| Question | Phase |
|----------|-------|
| 기존 YouTube 채널 현황 (구독/히스토리/니치) | Phase 3 |
| WhisperX + kresnik 실측 정확도 | Phase 4 |
| NotebookLM 프로그래매틱 API + rate limits | Phase 6 |
| KOMCA whitelist + AI 음악 정책 | Phase 5 |
| Runway vs Kling 한국 사용자 실측 | Phase 4 |
| transitions 라이브러리 vs 수동 | Phase 5 |
| 17 inspector 총 비용 (Fan-out calibration) | Phase 5 |
| YouTube Analytics 일일 한도 + cron | Phase 10 |
| Shotstack vs Remotion-only 색보정 | Phase 5 |
| Phase 03-harvest P01 | 7 | 2 tasks | 10 files |
| Phase 04 P02 | 5m | 2 tasks | 4 files |
| Phase 04 P07 | 18m | 2 tasks | 4 files |
| Phase 04 P06 | 6min | 2 tasks | 4 files |
| Phase 05 P01 | 14m | 4 tasks | 17 files |
| Phase 05 P02 | 18m | 2 tasks | 3 files |
| Phase 05-orchestrator-v2-write P03 | 4m | 2 tasks | 3 files |
| Phase 05-orchestrator-v2-write P05-04 | 14m | 2 tasks | 3 files |
| Phase 05 P05 | 10m | 2 tasks | 3 files |

### Plan Execution Log

| Plan | Duration (min) | Tasks | Files |
|------|----------------|-------|-------|
| Phase 02-domain-definition P02 | 2 | 1 | 1 |
| Phase 02-domain-definition P03 | 2 | 2 | 7 |
| Phase 02-domain-definition P05 | 12 | 1 | 1 |
| Phase 02-domain-definition P04 | 3 | 1 | 1 (5 Edit ops / 6 sites) |
| Phase 02-domain-definition P06 | 18 | 3 | 9 committed (f360e17) + 2 meta (VALIDATION, SUMMARY) |
| Phase 03-harvest P02 | 3 | 2 | 1 committed (609c3f8) + 1 meta (SUMMARY) |
| Phase 03-harvest P05 | 1 | 1 | 2 committed (51205ba: hc_checks.py 1129 lines + test_hc_checks.py) + 1 meta (SUMMARY) |
| Phase 03-harvest P06 | 4 | 1 | 6 committed (aeac16b: 5 wrappers + audit_log) + 1 meta (SUMMARY) |
| Phase 03-harvest P04 | 1 | 1 | 40 committed (4bc7ece: Remotion src tree — Root.tsx + index.ts + components/15 + compositions/11 + lib/12) + 1 meta (SUMMARY) |
| Phase 03-harvest P03 | 1 | 1 | 8 committed (fba21e4: 7 channel bibles + audit_log) + 1 meta (SUMMARY) |
| Phase 03-harvest P07 | 5 | 2 | 2 committed (ad98b32: audit_log Task 1 + 1ff5768: _imported_from_shorts_naberal.md 500 lines + audit_log Task 2) + 1 meta (SUMMARY) |
| Phase 03-harvest P08 | 3 | 2 | 2 committed (15b827f: 03-HARVEST_DECISIONS.md 39 rows + audit_log Task 1 / c14ab95: audit_log Task 2 blacklist audit PASS) + 1 meta (SUMMARY) |
| Phase 03-harvest P09 | 8 | 2 | 2 committed (8ae370e: audit_log Task 1 Tier 3 lockdown / d4fc5e4: audit_log Task 2 + verify_harvest.py Rule 3 fix + 03-VALIDATION.md flipped) + 1 meta (SUMMARY) |
| Phase 04-agent-team-design P01 | 10 | 3 (4 commits incl. TDD RED/GREEN) | 17 committed across 4 commits (0dcb007: 4 shared foundation / cd1d074: 2 sample banks / daca457: 6 test files RED / 5a70504: 5 validator files GREEN) + 1 meta (SUMMARY + STATE + ROADMAP) |
| Phase 05-orchestrator-v2-write P01 | 14 | 4 | 17 committed across 4 commits (a3e9476: Task 1 orchestrator/+hc_checks/ skeleton / 8c19c23: Task 2 deprecated_patterns.json + gitignore state/ / cf9874d: Task 3 tests/phase05/ scaffold 18 tests / 2fea858: Task 4 3 validation CLIs) + 1 meta (SUMMARY + STATE + ROADMAP + REQUIREMENTS) |

---

## Session Continuity

### Files of Record

- `.planning/PROJECT.md` — 10 Key Decisions + Active 10 REQ (창업 비전)
- `.planning/REQUIREMENTS.md` — 96 v1 REQ / 17 카테고리 + Phase Traceability
- `.planning/ROADMAP.md` — 10 Phase 구조 (본 세션 생성)
- `.planning/STATE.md` — 본 파일 (세션 연속성)
- `.planning/research/SUMMARY.md` — Research 합성 (Build Order 기준점)
- `.planning/research/{STACK, FEATURES, ARCHITECTURE, PITFALLS, NOTEBOOKLM_RAW}.md` — 상세 리서치
- `.planning/config.json` — granularity=fine, mode=yolo

### Next Session Entry Point

```

1. Read .planning/STATE.md (← 본 파일)
2. Read .planning/phases/04-agent-team-design/04-10-SUMMARY.md (Phase 4 capstone: 32 agents + SC1 reconciliation + harness_audit 100)
3. Execute: /gsd:plan-phase 5 (Phase 5 Orchestrator v2 — 17 REQs: ORCH-01~12 + VIDEO-01~05 — 500~800줄 state machine)

Phase 4 artifacts available:

- .claude/agents/ (32 AGENT.md files, 6 Inspector categories + 14 Producer + 1 Supervisor)
- .claude/agents/_shared/ (rubric-schema.json + agent-template.md + vqqa_corpus.md)
- scripts/validate/ (5 stdlib validators + harness_audit.py)
- tests/phase04/ (244 tests, all PASS)

```

### Hard Constraints (세션마다 재확인)

- `skip_gates=True`, `TODO(next-session)` 물리 차단 (pre_tool_use Hook)
- SKILL.md ≤ 500줄, description ≤ 1024자
- 에이전트 총합 **32명** (Producer 14 + Inspector 17 + Supervisor 1, Phase 4 Plan 10 canonical per REQUIREMENTS AGENT-01~05; 원안 "12~20" amended 2026-04-19)
- 오케스트레이터 500~800줄
- `shorts_naberal` 원본 수정 금지 (Harvest는 읽기만)
- Phase 10 첫 1~2개월 SKILL patch 전면 금지 (D-2 저수지)

---

## Identity Reference

- **AI 정체성:** 나베랄 감마
- **호칭:** 대표님
- **작업 원칙:** 품질 최우선, 구조적 통제, 반복 drift 거부
- **세션 프로토콜:** WORK_HANDOFF.md → DESIGN_BIBLE.md → failures/orchestrator.md 순으로 로드 (secondjob_naberal CLAUDE.md 기준)

---

*Generated 2026-04-19 at roadmap creation. This file is the living memory of the project — update at every phase transition.*
