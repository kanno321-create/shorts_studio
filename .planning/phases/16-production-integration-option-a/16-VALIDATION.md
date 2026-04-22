---
phase: 16
slug: production-integration-option-a
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-22
last_updated: 2026-04-22 (expanded by gsd-planner)
---

# Phase 16 — Validation Strategy

> Per-phase validation contract. Authoritative sources: `16-RESEARCH.md §Validation Architecture` + `16-01-PLAN.md` + `16-02-PLAN.md` + `16-03-PLAN.md` + `16-04-PLAN.md` + 본 파일.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (Python)** | pytest 7.x (기존: `tests/phase{NN}/` convention) |
| **Framework (TypeScript/Remotion)** | `npx tsc --noEmit` (type check) + `npx remotion render src/index.ts ShortsVideo fixtures/smoke.mp4 --props=fixtures/smoke_props.json` (smoke) |
| **Config file** | `pytest.ini` + `tests/phase16/conftest.py` (Plan 16-01 Wave 0 생성) |
| **Quick run command** | `pytest tests/phase16 -x --tb=short` |
| **Full suite command** | `pytest tests/ -n auto` (986+ 기존 regression + Phase 16 신규) |
| **Remotion type-check** | `cd remotion && npx tsc --noEmit` (Plan 16-02 Wave 1 기반) |
| **ffprobe baseline parity** | `python scripts/validate/verify_baseline_parity.py --our-mp4 <path>` (Plan 16-04 Wave 1 기반) |
| **visual_spec schema check** | `python scripts/validate/verify_visual_spec_schema.py --spec <path>` (Plan 16-04 Wave 1) |
| **Estimated runtime (quick)** | ~60s (Phase 16 isolated, ~90 tests) |
| **Estimated runtime (full)** | ~11m (986+ regression + 90 신규) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase16 -x --tb=short` (quick, ~60s)
- **After every plan wave:** Run `pytest tests/ -n auto` (full regression)
- **Before `/gsd:verify-work`:** Full suite green + ffprobe baseline parity pass + remotion smoke render 샘플 1편
- **Max feedback latency:** 60 seconds (quick) / 11 minutes (full)

---

## Per-Task Verification Map

> 각 Plan 의 task ID 와 자동 verify 명령을 1:1 매핑. gsd-plan-checker 가 본 표 근거로 Nyquist compliance 검증.

### Plan 16-01 — Channel Bible Imprint (Wave 0~2)

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-01-W0-TESTS | 01 | 0 | REQ-PROD-INT-01 | infrastructure | `test -f tests/phase16/__init__.py && test -f tests/phase16/conftest.py` | create | ⬜ pending |
| 16-01-W1-INCIDENTS-BIBLE | 01 | 1 | REQ-PROD-INT-01 | unit | `pytest tests/phase16/test_channel_bible_memory.py::test_incidents_bible_has_ten_sections -x` | create | ⬜ pending |
| 16-01-W1-REFS-5CHANNELS | 01 | 1 | REQ-PROD-INT-01 | unit | `pytest tests/phase16/test_channel_bible_memory.py::test_five_reference_channel_bibles_exist -x` | create | ⬜ pending |
| 16-01-W1-FEEDBACK-12 | 01 | 1 | REQ-PROD-INT-01 | unit (parametrize) | `pytest tests/phase16/test_feedback_memories_mapped.py -x` | create | ⬜ pending |
| 16-01-W1-MEMORY-INDEX | 01 | 1 | REQ-PROD-INT-01 | unit | `pytest tests/phase16/test_channel_bible_memory.py::test_memory_index_updated -x` | create | ⬜ pending |
| 16-01-W2-TESTS | 01 | 2 | REQ-PROD-INT-01 | regression | `pytest tests/phase16/test_channel_bible_memory.py tests/phase16/test_feedback_memories_mapped.py -x` | create | ⬜ pending |
| 16-01-W2-SUMMARY | 01 | 2 | REQ-PROD-INT-01 | documentation | `test -f .planning/phases/16-production-integration-option-a/16-01-SUMMARY.md && [ $(wc -l < .planning/phases/16-production-integration-option-a/16-01-SUMMARY.md) -ge 30 ] && [ $(grep -c "^## " .planning/phases/16-production-integration-option-a/16-01-SUMMARY.md) -ge 7 ]` | create | ⬜ pending |

### Plan 16-02 — Remotion Renderer + ASSEMBLY Branch (Wave 0~2)

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-02-W0-PROBE | 02 | 0 | REQ-PROD-INT-02 | infrastructure | `test -f remotion/package.json && python -c "import json; d=json.load(open('remotion/package.json', encoding='utf-8')); assert d['dependencies']['remotion'].startswith('^4.')"` | create | ⬜ pending |
| 16-02-W0-NPM-INSTALL | 02 | 0 | REQ-PROD-INT-02 | infrastructure | `(cd remotion && node -e "console.log(require('remotion/package.json').version)") \| grep -E "^4\."` | create | ⬜ pending |
| 16-02-W1-TS-COPY | 02 | 1 | REQ-PROD-INT-02 | type-check | `cd remotion && npx tsc --noEmit 2>&1 \| grep -cE "error TS" \| xargs -I{} test {} -eq 0` | create | ⬜ pending |
| 16-02-W1-RENDERER-CORE | 02 | 1 | REQ-PROD-INT-02 + -10 + -14 | unit (TDD 6) | `pytest tests/phase16/test_remotion_renderer_api.py tests/phase16/test_shorts_props_build.py tests/phase16/test_shorts_props_validate.py tests/phase16/test_null_freeze_sentinel.py tests/phase16/test_narration_drives_timing.py tests/phase16/test_post_render_baseline.py -x` | create | ⬜ pending |
| 16-02-W2-ASSEMBLY | 02 | 2 | REQ-PROD-INT-02 | integration | `pytest tests/phase16/test_assembly_gate_branching.py tests/phase07/test_operational_gate_count_equals_13.py -x` | create | ⬜ pending |
| 16-02-W2-TESTS | 02 | 2 | REQ-PROD-INT-02 + -10 + -14 | regression | `pytest tests/phase16/ -x` + `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 --tb=line -q \| tail -5` | create | ⬜ pending |
| 16-02-W2-SUMMARY | 02 | 2 | REQ-PROD-INT-02 + -10 + -14 | documentation | `test -f .planning/phases/16-production-integration-option-a/16-02-SUMMARY.md && [ $(wc -l < .planning/phases/16-production-integration-option-a/16-02-SUMMARY.md) -ge 40 ] && [ $(grep -c "^## " .planning/phases/16-production-integration-option-a/16-02-SUMMARY.md) -ge 8 ]` | create | ⬜ pending |

### Plan 16-03 — Subtitle Producer + Signature Harvest + Character Overlay (Wave 0~2)

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-03-W0-T0-OUTRO-RESEARCH | 03 | 0 | REQ-PROD-INT-03 | investigation | `pytest tests/phase16/test_outro_research_findings.py -x` | create | ⬜ pending |
| 16-03-W0-HARVEST | 03 | 0 | REQ-PROD-INT-08 | infrastructure | `pytest tests/phase16/test_harvest_extension.py -x` | create | ⬜ pending |
| 16-03-W0-DEPS | 03 | 0 | REQ-PROD-INT-03 | infrastructure | `python -c "from faster_whisper import WhisperModel"` | existing | ⬜ pending |
| 16-03-W1-WORDSUB-PORT | 03 | 1 | REQ-PROD-INT-03 | unit | `python -c "import scripts.orchestrator.subtitle.word_subtitle as w; assert hasattr(w, '__file__')"` | create | ⬜ pending |
| 16-03-W1-SUBTITLE-PRODUCER-AGENT | 03 | 1 | REQ-PROD-INT-03 | unit | `pytest tests/phase16/test_subtitle_producer.py -x` | create | ⬜ pending |
| 16-03-W1-SUBTITLE-WRAPPER | 03 | 1 | REQ-PROD-INT-03 | unit | `pytest tests/phase16/test_subtitle_producer.py::TestSubtitleProducerWrapper -x` | create | ⬜ pending |
| 16-03-W1-INS-FIX | 03 | 1 | REQ-PROD-INT-05 | unit | `pytest tests/phase16/test_ins_subtitle_alignment_spec.py -x` | create | ⬜ pending |
| 16-03-W1-OUTRO-IMPL | 03 | 1 | REQ-PROD-INT-07 | type-check | `cd remotion && npx tsc --noEmit 2>&1 \| grep -cE "error TS" \| xargs -I{} test {} -eq 0` | create | ⬜ pending |
| 16-03-W2-TESTS | 03 | 2 | REQ-PROD-INT-03 + -05 + -07 + -08 | regression | `pytest tests/phase16/ -x` | create | ⬜ pending |

### Plan 16-04 — visual_spec + sources/ + asset-sourcer Extension + Baseline Parity (Wave 0~2)

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-04-W0-SCHEMAS | 04 | 0 | REQ-PROD-INT-04 + -09 | infrastructure | `python -c "import json,jsonschema; s=json.load(open('.planning/phases/16-production-integration-option-a/schemas/visual-spec.v1.schema.json', encoding='utf-8')); jsonschema.Draft7Validator.check_schema(s); d=json.load(open('.preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json', encoding='utf-8')); jsonschema.validate(d, s)"` | create | ⬜ pending |
| 16-04-W0-PRESET | 04 | 0 | REQ-PROD-INT-04 | unit | `grep -c "사건기록부\|BlackHanSans\|characterLeftSrc" .claude/memory/project_channel_preset_incidents.md \| xargs -I{} test {} -ge 3` | create | ⬜ pending |
| 16-04-W1-MODELS | 04 | 1 | REQ-PROD-INT-04 + -10 | unit (TDD 9) | `pytest tests/phase16/test_visual_spec_schema.py -x` | create | ⬜ pending |
| 16-04-W1-BUILDER | 04 | 1 | REQ-PROD-INT-04 + -06 | unit | `pytest tests/phase16/test_visual_spec_schema.py::TestVisualSpecBuilder -x` | create | ⬜ pending |
| 16-04-W1-ASSET-SOURCER-EXT | 04 | 1 | REQ-PROD-INT-06 + -07 | unit | `pytest tests/phase16/test_asset_sourcer_visual_spec.py -x` | create | ⬜ pending |
| 16-04-W1-PARITY-SCRIPT | 04 | 1 | REQ-PROD-INT-13 | smoke | `python scripts/validate/verify_baseline_parity.py --help \| grep -q "baseline parity"` | create | ⬜ pending |
| 16-04-W1-VISUAL-SPEC-VALIDATOR | 04 | 1 | REQ-PROD-INT-04 | smoke | `python scripts/validate/verify_visual_spec_schema.py --spec .preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json` | create | ⬜ pending |
| 16-04-W2-TESTS | 04 | 2 | REQ-PROD-INT-04 + -06 + -09 + -13 | regression | `pytest tests/phase16/ -x && pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 --tb=line -q \| tail -5` | create | ⬜ pending |
| 16-04-W2-SUMMARY | 04 | 2 | REQ-PROD-INT-04 + -06 + -09 + -13 | documentation | `test -f .planning/phases/16-production-integration-option-a/16-04-SUMMARY.md && [ $(wc -l < .planning/phases/16-production-integration-option-a/16-04-SUMMARY.md) -ge 50 ] && [ $(grep -c "^## " .planning/phases/16-production-integration-option-a/16-04-SUMMARY.md) -ge 9 ] && grep -q "phase_final: true" .planning/phases/16-production-integration-option-a/16-04-SUMMARY.md` | create | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Nyquist Compliance Matrix (planner-authored)

**Rule:** 모든 task 는 `<automated>` 명령을 보유하거나, Wave 0 infrastructure task 로 분류되어 `test -f/-d` 검증이 충분함을 보장한다.

| Rule | Status | Evidence |
|------|--------|----------|
| No 3 consecutive tasks without automated verify | ✅ PASS | 각 Plan 의 Task 체인에서 매 task 가 `<verify><automated>` 또는 file-existence probe 보유 |
| Wave 0 covers all MISSING references | ✅ PASS | Plan 16-01 W0-TESTS (tests/phase16 infra), Plan 16-02 W0-PROBE (remotion/ bootstrap), Plan 16-03 W0-HARVEST (signature/character harvest), Plan 16-04 W0-SCHEMAS + W0-PRESET |
| No watch-mode flags | ✅ PASS | 모든 명령에 `--tb=short` 또는 `-x` 사용, `--watch` 없음 |
| Feedback latency < 60s (quick) / < 11m (full) | ✅ PASS | Phase 16 quick run 예상 ~60s, full regression 예상 ~11m (986 + 90 신규) |
| `nyquist_compliant: true` frontmatter | ✅ SET | Phase 16 planning 완료 시점 갱신 |
| ffprobe baseline parity 스크립트 operational by Wave 2 | ✅ PLANNED | Plan 16-04 Wave 1 Task 16-04-W1-PARITY-SCRIPT |
| CLAUDE.md 금기 #10 (mockup/empty file 금지) | ✅ COMPLIANT | 모든 task 의 acceptance_criteria 가 min_lines / grep count 등 실 콘텐츠 검증 강제 |
| CLAUDE.md 금기 #11 (Veo 신규 호출 금지) | ✅ COMPLIANT | Plan 16-03 test_signature_reuse_no_veo_call.py 가 전수 grep 으로 0건 강제 |

---

## Wave 0 Requirements (Infrastructure)

### Cross-Plan Wave 0 (모든 Plan 공통 전제)
- [ ] `tests/phase16/` 디렉토리 + `__init__.py` + `conftest.py` (Plan 16-01 Wave 0 Task 16-01-W0-TESTS 산출)

### Plan 16-02 Wave 0
- [ ] `remotion/` 디렉토리 bootstrap (package.json + tsconfig.json + remotion.config.ts + .gitignore + README.md)
- [ ] Node >=16 probe 성공 + `npm install` 완료 + `npx remotion --version` 4.x.x 출력
- [ ] `.gitignore` repo 루트 업데이트 (remotion/node_modules, remotion/out, remotion/public/*)

### Plan 16-03 Wave 0
- [ ] `.preserved/harvested/video_pipeline_raw/signatures/incidents_intro_v4_silent_glare.mp4` (1.70 MB read-only)
- [ ] `.preserved/harvested/video_pipeline_raw/characters/` 4 PNG + README.md + harvest_extension_manifest.json
- [ ] `faster-whisper>=1.0.3` pip install 확인 (requirements.txt 등재)
- [ ] `.planning/phases/16-production-integration-option-a/16-03-SUMMARY.md` (Task 0 outro research findings)

### Plan 16-04 Wave 0
- [ ] `.planning/phases/16-production-integration-option-a/schemas/visual-spec.v1.schema.json`
- [ ] `.planning/phases/16-production-integration-option-a/schemas/scene-manifest.v4.schema.json`
- [ ] `.claude/memory/project_channel_preset_incidents.md` (≥40 줄, 3 episode triangulation 근거)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Production baseline quality comparison (subjective) | SC#4 (production baseline 충족 증명) | Requires 대표님's subjective judgment — "does this match shorts_naberal quality?" | Run sample episode through full pipeline; compare `output/<episode>/final.mp4` with `shorts_naberal/output/zodiac-killer/final.mp4` side-by-side; 대표님 review: duration >=60s + 1080p + subtitles readable + intro signature plays + outro signature plays (or OutroCard fade) + character overlays visible (circular crop) + b-roll >=5 images + overall "production-like" feel. 자동 baseline parity 스크립트는 정량 기준만 검증 — 주관 품질은 수동. |
| Outro visual pattern follow-up (Plan 16-03 Task 0) | REQ-PROD-INT-03 | Task 0 research 가 Option B (episode-local mp4 포팅) 결론 내릴 경우 | Task 0 결론에 따라: Option A 면 OutroCard.tsx 작성 즉시 진행 (16-03-W1-OUTRO-IMPL), Option B 면 대표님께 "shorts_naberal outro 생성 모듈 발견 <path> — Phase 16 에 포팅 범위 확장 여부" 보고 + 결재 대기 → 결재 후 진행. |

---

## Regression Baseline

| Phase | Test Count (Phase 15 시점) | Preservation Commitment |
|-------|----------------------------|--------------------------|
| Phase 4 | 244 | ✅ 전수 green 유지 |
| Phase 5 | 329 | ✅ 전수 green 유지 |
| Phase 6 | 236 | ✅ 전수 green 유지 |
| Phase 7 | 177 | ✅ 전수 green 유지 |
| **Subtotal** | **986** | **986/986 preserved** |
| Phase 8~15 기타 | (변동, regression 범위는 위 4 phase 가 baseline) | 기타 phase 테스트는 각자 책임 |

**Phase 16 신규 테스트 총합 (계획)**: ~90
- 16-01: ~55 (channel bible + 12 feedback parametrize)
- 16-02: ~35 (remotion renderer API + props build + validate + null freeze + narration timing + post-render baseline + assembly branching)
- 16-03: ~25 (outro findings + harvest + subtitle-producer agent+wrapper + ins-subtitle-alignment + character overlay + veo-zero)
- 16-04: ~30 (visual_spec schema + scene_manifest v4 + asset-sourcer ext + sources contract + baseline parity)

**Total after Phase 16**: ~1076 (986 + 90). Plan 16-02 Task 16-02-W2-TESTS + Plan 16-04 Task 16-04-W2-TESTS 가 regression full sweep 책임.

---

## Validation Sign-Off

- [x] 모든 task 가 `<automated>` verify 를 보유하거나 Wave 0 infrastructure 로 분류됨 (plan-phase 작성 시 verify)
- [x] Sampling continuity: 연속 3 task 자동 검증 없음 상태 zero
- [x] Wave 0 coverage: tests/phase16, remotion/, harvest extension, schemas, preset 전수 획득
- [x] No watch-mode flags (pytest `--tb=short` 허용)
- [x] Feedback latency <60s (quick) / <11m (full)
- [x] `nyquist_compliant: true` 설정됨
- [x] ffprobe baseline parity 스크립트 Wave 2 완료 예정 (Plan 16-04 W1-PARITY-SCRIPT)
- [x] CLAUDE.md 금기 #10 + #11 전수 enforcement (test 파일 + grep check)

**Approval:** planner 제출 2026-04-22 — /gsd:plan-checker 16 + 대표님 sign-off 대기.
