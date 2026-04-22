---
plan: 16-02
phase: 16
name: "Remotion Renderer Infrastructure + ASSEMBLY Gate Branch"
status: complete
completed: 2026-04-22
wave_count: 3
task_count: 7
requirements: [REQ-PROD-INT-02, REQ-PROD-INT-10, REQ-PROD-INT-14]
duration_human: "1 session block"
tags: [remotion, typescript, ffprobe, assembly-gate, null-freeze, sc4-baseline]
key_files:
  created:
    - remotion/package.json
    - remotion/tsconfig.json
    - remotion/remotion.config.ts
    - remotion/.gitignore
    - remotion/README.md
    - remotion/src/index.ts
    - remotion/src/Root.tsx
    - remotion/src/compositions/ShortsVideo.tsx
    - remotion/src/components/BracketCaption.tsx
    - remotion/src/components/crime/ContextGraphicScene.tsx
    - remotion/src/components/crime/ImpactCutScene.tsx
    - remotion/src/components/crime/SpeakerSubtitle.tsx
    - remotion/src/components/crime/IconExplainer.tsx
    - remotion/src/components/crime/TimelineCard.tsx
    - remotion/src/components/crime/index.ts
    - remotion/src/lib/fonts.ts
    - remotion/src/lib/props-schema.ts
    - remotion/src/lib/transitions/presentations/{glitch,rgb-split,zoom-blur,light-leak,clock-wipe,pixelate,checkerboard}.tsx
    - remotion/fixtures/smoke_props.json
    - scripts/orchestrator/api/remotion_renderer.py
    - tests/phase16/test_remotion_renderer_api.py
    - tests/phase16/test_shorts_props_build.py
    - tests/phase16/test_shorts_props_validate.py
    - tests/phase16/test_null_freeze_sentinel.py
    - tests/phase16/test_narration_drives_timing.py
    - tests/phase16/test_post_render_baseline.py
    - tests/phase16/test_assembly_gate_branching.py
    - .planning/phases/16-production-integration-option-a/16-02-SUMMARY.md
    - .planning/phases/16-production-integration-option-a/16-02-tsc.log
    - .planning/phases/16-production-integration-option-a/16-02-remotion-version.log
    - .planning/phases/16-production-integration-option-a/deferred-items.md
  modified:
    - scripts/orchestrator/shorts_pipeline.py
    - .gitignore
commits:
  - "425fafb: W0-PROBE remotion/ bootstrap"
  - "a39bfcc: W0-NPM-INSTALL remotion@4.0.451"
  - "70b5e01: W1-TS-COPY 19 TypeScript files + tsc 0 errors"
  - "48fcf6b: W1-RENDERER-CORE remotion_renderer.py + 40 TDD tests"
  - "ff81ad5: W2-ASSEMBLY + W2-TESTS 3-branch cascade + 9 branching tests"
  - "<this>: W2-SUMMARY docs(16-02) plan summary"
---

# Phase 16 Plan 16-02: Remotion Renderer Infrastructure + ASSEMBLY Gate Branch Summary

**One-liner:** shorts_naberal Remotion 4.x 스택 (`remotion/` TypeScript + Python bridge `remotion_renderer.py`) 을 1:1 이식하여 `shorts_pipeline.py:_run_assembly` 에 `remotion > shotstack > ffmpeg` 3분기 cascade 를 도입. ffprobe 기반 production baseline (1080×1920 · ≥60s · h264/hevc) 을 renderer 내부에서 강제하여 "spec 통과 ≠ production 통과" 재발 방지.

## Deliverables

### `remotion/` TypeScript 프로젝트 (신규, Phase 16-02 Wave 0–1 산출)
- **Bootstrap (W0-PROBE):** `package.json` (remotion@^4.0.0 + @remotion/cli + @remotion/transitions@^4.0.445 + react@^18.3.1 + zod@^4.3.6) + `tsconfig.json` (strict ES2020 + DOM.Iterable, jsx react-jsx, bundler moduleResolution) + `remotion.config.ts` (jpeg image format, overwrite, concurrency=1) + `.gitignore` + `README.md`.
- **npm install (W0-NPM-INSTALL):** 245 packages installed, 0 vulnerabilities, 33s runtime. Remotion version verified `4.0.451` (≥4.x).
- **TypeScript source port (W1-TS-COPY):** 19 files ported 1:1 from `.preserved/harvested/remotion_src_raw/` with `// Ported from ...` header:
  - Shorts-only composition: `src/Root.tsx` (trimmed to single ShortsVideo registration — Rule 2 deviation; long-form card imports removed)
  - Core composition: `src/compositions/ShortsVideo.tsx` (914 lines w/ header, DESIGN_SPEC constants preserved: `TOP_BAR_H=320`, `BOTTOM_BAR_H=333`)
  - Crime components (5): ContextGraphicScene / ImpactCutScene / SpeakerSubtitle / IconExplainer / TimelineCard + index
  - Transitions (7 presentation): glitch / rgb-split / zoom-blur / light-leak / clock-wipe / pixelate / checkerboard
  - Lib: fonts.ts (BlackHanSans + NotoSansKR + DoHyeon + Inter + NotoSansJP + JP custom fonts), props-schema.ts (Zod schemas)
- **Fixture:** `remotion/fixtures/smoke_props.json` — zodiac-killer baseline visual_spec copy.
- **Type check:** `cd remotion && npx tsc --noEmit` exit 0 (0 TS errors).

### `scripts/orchestrator/api/remotion_renderer.py` (신규, Wave 1 산출)
- **Line count:** 911 lines (acceptance ≥ 400).
- **Public API:**
  - `RemotionRenderer(project_root, remotion_dir_name='remotion', output_dir, timeout_s=600, first_render_timeout_s=180)` — probes `node` / `ffprobe` / `remotion/package.json`; raises `RemotionUnavailable` on any miss.
  - `render(timeline, resolution='fhd', aspect_ratio='9:16') -> dict` — signature mirror of `FFmpegAssembler.render`.
  - `upscale(url) -> dict` — Phase 8 NOOP (Remotion native 1080p).
- **8 private helpers** (harvested `remotion_render.py` 1:1 port):
  1. `_get_audio_duration_ffprobe` — ffprobe SSOT timing (lines 293–320 mirror)
  2. `_prepare_remotion_assets` — copy to `remotion/public/<job_id>/` (lines 354–500 mirror)
  3. `_build_shorts_props` — Zod-compat props + `_NULL_FREEZE` lifecycle (lines 501–773 mirror + Option B visual_spec precedence)
  4. `_validate_shorts_props` — fail-fast pre-subprocess (lines 255–290 mirror)
  5. `_pre_render_quality_gates` — subtitle coverage ≥ 95%
  6. `_inject_character_props` — Detective / Assistant PNG overlay (lines 942–976 mirror)
  7. `_invoke_remotion_cli` — `npx remotion render src/index.ts ShortsVideo out.mp4 --props=...`
  8. `_cleanup_remotion_assets` — safety-checked per-job workspace teardown (lines 323–353 mirror)
  - + `_verify_production_baseline` (NEW, not in harvested) — ffprobe post-check enforcing ROADMAP SC#4.
- **3 exception classes:** `RemotionUnavailable`, `RemotionValidationError`, `RemotionBaselineError`.
- **Module constants exposed:** `TARGET_RESOLUTION=(1080,1920)`, `TARGET_FPS=30`, `MIN_PRODUCTION_DURATION_S=60.0`, `SUBTITLE_COVERAGE_MIN=0.95`, `NULL_FREEZE_SENTINEL="_NULL_FREEZE"`.
- **Security:** 모든 `subprocess.run` 에 `timeout=` 명시 + `shell=(sys.platform=='win32')` 조건화 + explicit `raise` on non-zero rc (CLAUDE.md 금기 #3 준수).
- **Veo count:** 0 (CLAUDE.md 금기 #11 준수, verified `grep -cE 'VeoClient|veo_i2v|import.*veo'` → 0).
- **skip_gates / TODO(next-session) count:** 0 (CLAUDE.md 금기 #1/2 준수).

### `scripts/orchestrator/shorts_pipeline.py` 수정 (Wave 2, 기존 → 신규)
- **Line count:** 841 → 884 (+43). Plan 16-02 acceptance criterion `wc ≤ 900` 만족. CLAUDE.md 필수 #3 (500–800) 은 pre-existing 초과 상태 (Plan 16-02 이전부터) — deferred-items.md 문서화.
- **`__init__` 추가 블록 (line ~265-285):** `self.remotion_renderer = None` + try `RemotionRenderer()` with `RemotionUnavailable` / broad `Exception` catch + logger INFO/WARNING. Shotstack+ffmpeg 초기화 이후에 실행되어 Remotion 실패 시 fallback cascade 무손상.
- **`_run_assembly` 3-branch cascade:**
  ```python
  renderer = self.remotion_renderer or self.shotstack or self.ffmpeg_assembler
  if renderer is None:
      raise RuntimeError("ASSEMBLY renderer 미구성 (대표님) — Remotion/Shotstack/ffmpeg_assembler 모두 없음")
  if renderer is self.remotion_renderer:
      # Remotion: fhd, no circuit breaker
  elif renderer is self.shotstack:
      # Shotstack: hd, circuit breaker
  else:
      # ffmpeg: fhd, no circuit breaker
  ```
- **Metadata tracking:** `render_result.setdefault('renderer', <class>.__name__.lower())` — `assembly_metadata.json` 소비측이 어느 renderer 사용됐는지 알 수 있음.

## Tests

### Phase 16 Plan 16-02 테스트 (49 green)
```
tests/phase16/test_remotion_renderer_api.py ........ 8 passed
tests/phase16/test_shorts_props_build.py ...... 6 passed
tests/phase16/test_shorts_props_validate.py ........ 8 passed
tests/phase16/test_null_freeze_sentinel.py .... 4 passed
tests/phase16/test_narration_drives_timing.py .... 4 passed
tests/phase16/test_post_render_baseline.py .......... 10 passed
tests/phase16/test_assembly_gate_branching.py ......... 9 passed
─────────────────────────────────────────────────────────
                                            49 passed in 0.89s
```
- **TDD 순서 준수:** Wave 1 에서 RED (test 먼저) → GREEN (구현 추가) 반복.
- **Wave 1 산출 6 테스트 (40개 케이스):** API contract + props build + props validate + null-freeze sentinel + narration drives timing + post-render baseline.
- **Wave 2 산출 1 테스트 (9 케이스):** ASSEMBLY 3-branch cascade selection + resolution parameter per renderer + breaker routing + upscale-after-render preserved + metadata stamping.

## Regression

### Phase 7 GATE count 불변 (regression green)
```
pytest tests/phase07/test_operational_gate_count_equals_13.py → 7/7 passed (0.76s)
```
13 operational GATE 변경 없음. 새 GATE 추가 없이 ASSEMBLY 내부 분기만 변경.

### Phase 4-7 전수 실행 결과
- 953 tests 실행 (phase04 244 + phase05 329 + phase06 236 + phase07 144 excl. skips)
- **867 passed, 86 failed, 1 skipped** — 실패 86건 전수가 Plan 16-02 도입 이전부터 pre-existing (verified via `git stash` rollback).
- 예: `test_supervisor_depth_guard::test_17_inspector_names_present` (Phase 9.1 supervisor agent 부족), `test_line_count_is_within_budget` (841 line pre-existing violation), `test_wiki_nodes_ready` (wiki 작성 시점부터 미완).
- **Plan 16-02 changes introduce 0 new regressions.** Scope boundary rule 준수 — out-of-scope 수정 안 함, deferred-items.md 에 전수 문서화.

## Production Baseline (SC#4 evidence)

**ROADMAP Phase 16 SC#4 — "production baseline 충족 증명":**
- `remotion_renderer.py:68` → **`MIN_PRODUCTION_DURATION_S = 60.0`** (not 50.0 legacy — ROADMAP SC#4 기준).
- `remotion_renderer.py:65` → `TARGET_RESOLUTION = (1080, 1920)` (9:16 vertical).
- `remotion_renderer.py:66` → `TARGET_FPS = 30`.

**`_verify_production_baseline()` 강제 규칙** (lines 692–744):
1. `final.mp4` 존재 확인 → 없으면 `RemotionBaselineError("final.mp4 미생성: <path>")`.
2. `ffprobe -show_format -show_streams -of json` 실행 (timeout=30s).
3. video stream 존재 확인 → 없으면 `RemotionBaselineError("video stream 없음")`.
4. `(width, height) == (1080, 1920)` 강제 → 불일치 시 `RemotionBaselineError("해상도 불량: ...")`.
5. `duration ≥ MIN_PRODUCTION_DURATION_S` (60.0s) 강제 → 불일치 시 `RemotionBaselineError("영상 길이 불량: ... < 60.0s baseline (ROADMAP Phase 16 SC#4)")`.
6. `codec in {h264, hevc}` 강제 → 불일치 시 `RemotionBaselineError("codec 불량: <codec>")`.

**증거:** `tests/phase16/test_post_render_baseline.py` 10 케이스 전수 green — 1080×1920 h264 60.5s pass / 720×1280 reject / 50.0s reject / 59.99s reject / vp9 reject / missing file reject / audio-only reject / hevc pass / width-only check / missing stream check. 모든 baseline violation 이 `RemotionBaselineError` 로 감지됨.

## Deviations

### Rule 2 (minor variant) — Root.tsx Shorts-only scope
- **발견:** Harvested `Root.tsx` 는 long-form composition (TitleCard, QuoteCard, StatsCard, ListCard, HighlightCard, BarChartCard, ComparisonCard, IntroCard, OutroCard, LongformVideo) 10+ 파일을 import. 그러나 이들은 Phase 16 scope 밖 (long-form 은 Phase 18+).
- **처리:** Root.tsx 를 Shorts-only 로 trim — ShortsVideo composition 만 registerRoot 에 등록. **import 제거만, 로직 수정 0** (Plan 허용 deviation).
- **근거:** `<deviations_allowed>` Rule 2 명시 — "없는 컴포넌트 (예: Root.tsx 가 long-form composition 참조) 는 import 만 제거 가능 (로직 수정 절대 금지)".

### Rule 2 — tsconfig.json DOM.Iterable lib 추가
- **발견:** `lib/fonts.ts` 의 `document.fonts.add(font)` 호출이 DOM.Iterable lib 미포함 시 `TS2339: Property 'add' does not exist on type 'FontFaceSet'` 오류 발생.
- **처리:** `tsconfig.json` `lib: ["ES2020", "DOM"]` → `["ES2020", "DOM", "DOM.Iterable"]` 추가.
- **근거:** Remotion 4.x 표준 tsconfig 설정. Harvested 원본과 완전 동일.

### 실패 케이스 (None)
- RemotionUnavailable / RemotionValidationError / RemotionBaselineError 전수 정상 동작 (테스트로 검증).
- Authentication gate 없음 (local subprocess 만 사용).
- Rule 1 (bug fix) / Rule 3 (blocker fix) 해당 없음.

## Lessons

### Phase 16-03 (subtitle + signature) 전달 사항
- **`_build_shorts_props` 의 `subtitles` 로드 경로는 `subtitle_json_path` 만 받음.** Plan 16-03 의 subtitle-producer 가 `subtitles_remotion.json` 을 생성하면 `timeline entry.subtitle_json_path` 로 전달해야 `RemotionRenderer._extract_from_timeline` 이 감지.
- **`_inject_character_props` 는 `episode_dir/sources/character_{assistant,detective}.png` 를 찾음.** Plan 16-04 asset-sourcer 확장이 이 파일들을 미리 복사해놓아야 한다.
- **Signature 통합:** `intro_signature.mp4` 는 `remotion_renderer.py` 가 render time 에 copy. Plan 16-03 은 signature 를 `output/_shared/signatures/` 에 보존만, asset-sourcer 는 episode 로 참조만.

### Phase 16-04 (visual_spec + asset-sourcer) 전달 사항
- **visual_spec.clipDesign[] 이 있으면 round-robin movement 비활성화** (Pitfall 4 방어). 16-04 asset-sourcer 가 `visual_spec.json` 을 episode_dir 에 저장하고 timeline entry.visual_spec_path 로 경로 전달.
- **`_NULL_FREEZE` 센티넬 생명주기:** 16-04 asset-sourcer 가 visual_spec 생성 시 "의도적 freeze clip" 은 `movement: null` (JSON null) 으로 명시해야 `RemotionRenderer` 가 정확히 freeze 처리.
- **Pydantic v2 VisualSpec 모델은 16-04 Wave 0 에서 생성됨.** 16-02 는 독립 실행 — 16-04 완료 전까지 `visual_spec_path` 는 optional.

### Pipeline 라인 부채 (shorts_pipeline.py)
- 884 lines (pre-existing 841 + Plan 16-02 43). CLAUDE.md 필수 #3 ORCH-01 (500-800) 이미 위반 상태.
- 전수 refactor 권장 — `_run_assembly` / `_run_thumbnail` / `_run_metadata` / `_run_upload` 등 개별 GATE handler 를 `scripts/orchestrator/handlers/` 로 분리하여 500 line 미만 maintain.
- 본 Plan scope 밖 — future orchestration refactor phase 담당.

## Evidence

### Commits (this plan)
| SHA | Message | Files | Lines +/- |
|-----|---------|-------|-----------|
| 425fafb | W0-PROBE remotion/ bootstrap | 6 | +92 |
| a39bfcc | W0-NPM-INSTALL remotion@4.0.451 | 1 | +4 |
| 70b5e01 | W1-TS-COPY 19 TypeScript files + tsc 0 errors | 22 | +2846 / -1 |
| 48fcf6b | W1-RENDERER-CORE remotion_renderer.py + 40 TDD tests | 7 | +1742 |
| ff81ad5 | W2-ASSEMBLY + W2-TESTS 3-branch cascade + 9 branching tests | 4 | +3262 / -14 |

### Evidence logs
- `.planning/phases/16-production-integration-option-a/16-02-remotion-version.log` — Remotion 4.0.451 + install metadata
- `.planning/phases/16-production-integration-option-a/16-02-tsc.log` — tsc --noEmit exit 0, 0 errors
- `.planning/phases/16-production-integration-option-a/deferred-items.md` — pre-existing Phase 4-7 regression 전수 분류

### Tests summary
- `pytest tests/phase16/ -q` → **49 passed in 0.89s**
- `pytest tests/phase07/test_operational_gate_count_equals_13.py` → **7 passed** (GATE count 13 불변)
- Phase 16-02 테스트 신규 49개 (목표 ≥35 초과) + Plan 16-01 병행 테스트 누적은 16-04 SUMMARY 에서 합산.

### shorts_pipeline.py 변경 증거
- `self.remotion_renderer` 참조 횟수: 4 (acceptance ≥ 3)
- `from .api.remotion_renderer import RemotionRenderer` count: 1
- `renderer is self.remotion_renderer` count: 1
- `"Remotion/Shotstack/ffmpeg_assembler 모두 없음"` count: 1
- ShortsPipeline import 성공 (no runtime ImportError)

## SC Coverage

| SC | Goal | Plan 16-02 Contribution | Status |
|----|------|-------------------------|--------|
| SC#1 | 4/4 Plan SUMMARY 완료 | Plan 16-02 complete (누계 2/4 포함 16-01 completion in parallel) | ⬜ 2/4 (pending 16-03, 16-04) |
| SC#2 | 986+ Phase 4-7 regression 전수 green | Phase 16-02 무수한 새 regression 없음 — 86 pre-existing 실패는 deferred-items 에 문서화, 진행 차단 안 함 | ⚠️ pre-existing (not caused by 16-02) |
| SC#3 | Phase 16 신규 테스트 ≥20 | Phase 16-02 기여 49 (목표 ≥35 초과) | ✅ |
| SC#4 | Production baseline 충족 증명 | `_verify_production_baseline` 이 `MIN_PRODUCTION_DURATION_S=60.0` + 1080×1920 + h264/hevc 강제 — 10 테스트 케이스로 검증 | ✅ |
| SC#5 | 재발 방지 guard 구축 | `_NULL_FREEZE` 센티넬 lifecycle (Pitfall 4) + ffprobe baseline (Pitfall 1) + Veo 0건 (금기 #11) + skip_gates 0건 (금기 #1) | ✅ |

## Self-Check: PASSED

### File existence verification
- ✅ remotion/package.json
- ✅ remotion/tsconfig.json
- ✅ remotion/remotion.config.ts
- ✅ remotion/README.md
- ✅ remotion/src/Root.tsx
- ✅ remotion/src/compositions/ShortsVideo.tsx (914 lines)
- ✅ scripts/orchestrator/api/remotion_renderer.py (911 lines)
- ✅ tests/phase16/test_remotion_renderer_api.py + 6 other test files
- ✅ .planning/phases/16-production-integration-option-a/deferred-items.md

### Commit verification
- ✅ 425fafb W0-PROBE (git log confirmed)
- ✅ a39bfcc W0-NPM-INSTALL (git log confirmed)
- ✅ 70b5e01 W1-TS-COPY (git log confirmed)
- ✅ 48fcf6b W1-RENDERER-CORE (git log confirmed)
- ✅ ff81ad5 W2-ASSEMBLY+W2-TESTS (git log confirmed)

### Plan acceptance criteria
- ✅ `remotion/` TypeScript 프로젝트 boot 성공 (`npm install` + `npx remotion --version` 가능)
- ✅ `remotion_renderer.py` 911 lines (≥400), 8 helper + 2 public, 6 test file green
- ✅ `_run_assembly` remotion > shotstack > ffmpeg cascade
- ✅ pytest tests/phase16/ exit 0 (49 ≥35)
- ⚠️ pytest tests/phase04-07 pre-existing 실패 — deferred-items 문서화, 16-02 scope 밖
- ✅ grep skip_gates/TODO(next-session) = 0 in remotion_renderer.py + remotion/src/
- ✅ grep Veo = 0 in remotion_renderer.py + remotion/src/
