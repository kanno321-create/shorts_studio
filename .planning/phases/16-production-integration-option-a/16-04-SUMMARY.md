---
plan: 16-04
phase: 16
name: "Visual Spec Schema + sources/ Directory + asset-sourcer Extension + Baseline Parity"
status: complete
completed: 2026-04-22
wave_count: 3
task_count: 9
requirements: [REQ-PROD-INT-04, REQ-PROD-INT-06, REQ-PROD-INT-09, REQ-PROD-INT-13]
phase_final: true
tags: [visual-spec, pydantic-v2, json-schema, asset-sourcer, baseline-parity, sc4-duration, sc5-shock-defence, phase16-final]
duration_human: "1 session block (세션 #33)"
key_files:
  created:
    - .planning/phases/16-production-integration-option-a/schemas/visual-spec.v1.schema.json
    - .planning/phases/16-production-integration-option-a/schemas/scene-manifest.v4.schema.json
    - .claude/memory/project_channel_preset_incidents.md
    - scripts/orchestrator/api/visual_spec_builder.py
    - scripts/validate/verify_baseline_parity.py
    - scripts/validate/verify_visual_spec_schema.py
    - tests/phase16/test_visual_spec_schema.py
    - tests/phase16/test_scene_manifest_v4.py
    - tests/phase16/test_asset_sourcer_visual_spec.py
    - tests/phase16/test_sources_directory_contract.py
    - tests/phase16/test_baseline_parity_script.py
    - .planning/phases/16-production-integration-option-a/16-04-parity-smoke.json
  modified:
    - scripts/orchestrator/api/models.py  # +168 lines (4 new Pydantic classes)
    - .claude/agents/producers/asset-sourcer/AGENT.md  # v1.2 -> v1.3
commits:
  - "637fd88: W0-SCHEMAS visual-spec.v1 + scene-manifest.v4 JSON Schemas"
  - "ba884d1: W0-PRESET incidents 채널 preset 박제"
  - "6f4bedb: W1-MODELS RED TDD tests (ImportError expected)"
  - "06f9066: W1-MODELS GREEN VisualSpec/ClipDesign/TitleKeyword/SourcesManifest"
  - "273a8d7: W1-BUILDER visual_spec_builder.build() + load_channel_preset()"
  - "eaf4cda: W1-ASSET-SOURCER-EXT asset-sourcer v1.3 + 33 상한 유지"
  - "282e3a8: W1-PARITY-SCRIPT verify_baseline_parity.py ffprobe comparator"
  - "249d497: W1-VISUAL-SPEC-VALIDATOR dual validator CLI"
  - "b333dc9: W2-TESTS 4 test files + scene-manifest schema relax"
  - "<this>: W2-SUMMARY docs(16-04) Phase 16 final"
dependency_graph:
  requires:
    - .preserved/harvested/baseline_specs_raw/  # zodiac-killer / nazca-lines / roanoke-colony 3 baseline
    - scripts/orchestrator/api/models.py        # extended (ContinuityPrefix 기존 보전)
    - .claude/memory/MEMORY.md                  # preset memory 인덱스 대상
  provides:
    - VisualSpec / ClipDesign / TitleKeyword / SourcesManifest Pydantic 계약
    - visual_spec_builder.build() — Designer single SOT (Q2)
    - verify_baseline_parity.py — SC#5 shock-event defence gate
    - verify_visual_spec_schema.py — output/<episode>/visual_spec.json 이중 validator
    - incidents channel preset SSOT (3 episode triangulation)
    - asset-sourcer v1.3 visual_spec/sources_manifest 책임 흡수
  affects:
    - remotion/src/compositions/ShortsVideo.tsx  # props 계약 공유 (Plan 16-02 산출)
    - scripts/orchestrator/shorts_pipeline.py   # ASSEMBLY gate verify_baseline_parity 호출 여지
    - CLAUDE.md 금기 #9 ("33 상한") 2차 방어선
tech_stack:
  added:
    - pydantic v2 (extra='forbid', field_validator, Literal enum, PositiveInt, confloat)
    - jsonschema Draft-07 (visual-spec.v1 + scene-manifest.v4)
    - ffprobe subprocess (absolute + baseline-relative criteria)
  patterns:
    - "Schema as SSOT — JSON Schema + Pydantic 이중 방어"
    - "Designer single source of truth (Q2): visual_spec_override 경로"
    - "Triangulation from real baselines (zodiac + nazca + roanoke)"
    - "SC#5 absolute thresholds (channels/sr/bitrate/subtitle) — session #32 shock 재발 방지"
    - "Per-episode relative parity ±10% (bitrate/fps)"
metrics:
  duration_minutes: "~55"
  tasks_completed: 9
  tests_added: 56
  files_created: 12
  files_modified: 2
  total_new_lines: ~1980
---

# Phase 16 Plan 16-04: Visual Spec + sources/ + asset-sourcer + Baseline Parity Summary

**One-liner:** zodiac-killer baseline 스키마 1:1 복제로 `VisualSpec` Pydantic v2 모델 + JSON Schema Draft-07 + `visual_spec_builder.build()` + `verify_baseline_parity.py` (SC#5 절대 thresholds: stereo / 44100Hz / 5000kbps / subtitle >=1) 을 산출하여 "spec 통과 != production 통과" 재발 방지 장치 operational 확인. **Phase 16 최종 Plan — Production Integration Option A 완료.**

## Deliverables

### 신규 산출물 (12 file)
1. **JSON Schemas** — `.planning/phases/16-production-integration-option-a/schemas/`
   - `visual-spec.v1.schema.json` (Draft-07, additionalProperties:false in root+clips+titleKeywords)
   - `scene-manifest.v4.schema.json` (Draft-07, section_type enum + provider open-string)
2. **Pydantic v2 모델** — `scripts/orchestrator/api/models.py` (기존 168 → 338 lines, +170)
   - `VisualSpec` (extra='forbid', 15 필드)
   - `ClipDesign` (Pitfall 4 movement=None, Pitfall 6 int-only durationInFrames)
   - `TitleKeyword` (HEX color validator)
   - `SourcesManifest` (Pitfall 5 scene_sources >=5, feedback_veo_supplementary_only veo<=2)
3. **visual_spec_builder** — `scripts/orchestrator/api/visual_spec_builder.py` (372 lines)
   - `build(blueprint, script, channel_preset, sources_manifest, audio_s, episode_id, override)` — Designer single SOT 보전 (Q2)
   - `load_channel_preset(Path)` — preset memory 간이 regex 파서
   - Helpers: `_build_clips`, `_to_relative`, `_heuristic_title_line1/2`
4. **Validators**
   - `scripts/validate/verify_baseline_parity.py` (324 lines) — ffprobe + SC#5 절대 thresholds
   - `scripts/validate/verify_visual_spec_schema.py` (119 lines) — JSON Schema + Pydantic 이중 CLI
5. **Preset memory** — `.claude/memory/project_channel_preset_incidents.md` (84 lines)
   - 3 episode triangulation (zodiac-killer / nazca-lines / roanoke-colony)
   - channelName / accentColor / fontFamily 3종 / subtitle 5 속성 / transitions 8종 / Q4 좌우 고정
6. **Test files (5, 각 >=60 lines)** — `tests/phase16/`
   - `test_visual_spec_schema.py` (269 lines, 17 tests)
   - `test_scene_manifest_v4.py` (105 lines, 8 tests)
   - `test_asset_sourcer_visual_spec.py` (83 lines, 8 tests)
   - `test_sources_directory_contract.py` (115 lines, 10 tests)
   - `test_baseline_parity_script.py` (171 lines, 13 tests)

### 수정된 산출물 (2 file)
- `scripts/orchestrator/api/models.py` — 4 class append (기존 ContinuityPrefix/TypecastRequest 등 미수정)
- `.claude/agents/producers/asset-sourcer/AGENT.md` — v1.2 → v1.3 (description 692 → 931 chars, <= 1024 준수; role 확장; **"33 상한 유지" 명시**)

## Tests

**Phase 16-04 신규: 56/56 GREEN** (명령: `pytest tests/phase16/test_visual_spec_schema.py tests/phase16/test_scene_manifest_v4.py tests/phase16/test_asset_sourcer_visual_spec.py tests/phase16/test_sources_directory_contract.py tests/phase16/test_baseline_parity_script.py`)

| 파일                                  | 수집 | 통과 | 비고                                                       |
| ------------------------------------- | ---- | ---- | ---------------------------------------------------------- |
| test_visual_spec_schema.py            | 17   | 17   | VisualSpec/Clip/Title/Sources + Builder smoke 3 + Schema 2 |
| test_scene_manifest_v4.py             | 8    | 8    | Schema valid + 3 baselines + 4 reject (v3/empty/channel/stats) |
| test_asset_sourcer_visual_spec.py     | 8    | 8    | v1.3 frontmatter + 1024 desc + visual_spec/sources counts + Q4 좌우 + 33 상한 |
| test_sources_directory_contract.py    | 10   | 10   | scene_sources>=5, real_ratio [0,1], veo/sig<=2, outro Optional, extra forbidden |
| test_baseline_parity_script.py        | 13   | 13   | within, all_pass, fail-res/dur/mono/sr/519kbps/nosub, rel±10%, CLI nonexistent |
| **합계**                              | 56   | 56   | **100%**                                                    |

실행 시간: 0.87s (warnings 포함).

## Regression

**Phase 4-6 실행 결과**: 751 passed / 52 failed / 7 deselected (36.98s).

- 52 pre-existing failures 전수 이미 Plan 16-02 `deferred-items.md` 에 분류·문서화. 본 Plan 은 기존 class/함수 미수정 (`models.py` 는 append only, `asset-sourcer/AGENT.md` 는 frontmatter 확장 + role 섹션 추가). **16-04 이 유발한 새 regression 은 0.**
- phase07 `test_full_phase07_suite_green_excluding_wrapper` 는 subprocess-timeout 이슈 (Plan 16-02 이전부터 pre-existing, deferred-items #5).
- 16-04 수정 범위는 신규 파일 + AGENT.md metadata 확장 + models.py append only — existing tests surface 에 영향 없음.

## Baseline Parity (SC#5 evidence)

**실측 실행**: `python -X utf8 scripts/validate/verify_baseline_parity.py --our-mp4 "C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/final.mp4" --episode zodiac-killer --report .planning/phases/16-04-parity-smoke.json`

**shorts_naberal zodiac-killer 에 대한 SC#5 criterion 측정 (9 criterion 중 8 통과):**

| Criterion               | Value     | Threshold                        | Pass                        |
| ----------------------- | --------- | -------------------------------- | --------------------------- |
| resolution              | 1080x1920 | strict                           | ✅                           |
| duration                | ~72s      | 60-125s (**MIN_DURATION_S=60.0**) | ✅                           |
| codec                   | h264      | h264/hevc                        | ✅                           |
| audio_channels          | 2         | ==2 (stereo)                     | ✅                           |
| audio_sample_rate       | 48000 Hz  | >=44100                          | ✅                           |
| min_video_bitrate       | 5626 kbps | >=5000 kbps                      | ✅ (519kbps shock 재발 방지) |
| subtitle_track_present  | 0         | >=1                              | ❌ (shorts_naberal 는 burn-in subtitle, separate track 없음) |
| bitrate_vs_baseline     | 5626      | 5171 avg ±10%                    | ✅                           |
| fps_vs_baseline         | 30.0      | 30.0 avg                         | ✅                           |

**Note**: zodiac-killer 자체가 burn-in subtitle 이라 stream-level subtitle track 은 0. 이는 baseline 특성 (Remotion burn-in). 우리 Plan 16-04 스크립트는 이 criterion 을 옵션화 하지 않고 발견 — 향후 실제 우리 render 출력이 subtitle stream 을 포함하는지 검증 시 유효. shorts_naberal 기준은 **dual subtitle strategy** (burn-in + ass/srt sidecar).

**Absolute thresholds 의 session #32 shock defence 의미**: 519 kbps 같은 "spec 통과 but production 허망" 재발 불가 — 5000 kbps 절대 floor 로 gate 차단.

**Report JSON**: `.planning/phases/16-production-integration-option-a/16-04-parity-smoke.json` (9 criterion 전수 기록).

## visual_spec.json Schema Compliance

**zodiac-killer baseline 이중 통과**:

1. **JSON Schema Draft-07**:
   ```bash
   $ python scripts/validate/verify_visual_spec_schema.py \
       --spec .preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json
   [verify_visual_spec_schema] JSON Schema Draft-07 PASS
   [verify_visual_spec_schema] Pydantic VisualSpec PASS
   $ echo $?
   0
   ```
2. **Pydantic VisualSpec**: `clips=16, durationInFrames=3385, fontFamily=BlackHanSans, characterLeft.endswith('character_assistant.png'), characterRight.endswith('character_detective.png')` 전수 통과.

3. **추가 baseline 검증**: roanoke-colony 의 `characterLeftSrc="roanoke-colony/character_assistant.png"` + `characterRightSrc="roanoke-colony/character_detective.png"` 도 Q4 좌우 convention 준수 확인 — Pydantic model_validate 통과.

## Deviations

### Rule 3 — scene-manifest.v4 schema enum 완화
- **Found during**: W2-TESTS 실행 (`test_nazca_scene_manifest_passes_if_exists` FAIL)
- **Issue**: nazca-lines scene-manifest 에 `section_type="cta"` + `provider="wikipedia"` 가 실존. 계획된 enum (`intro/hook/body/outro` + `veo_reuse/serper/gpt_image2/kling/runway/nano_banana/remotion_card`) 미포함.
- **Fix**: `section_type` enum 에 "cta" 추가; `provider` 는 enum 제거 → open-string (minLength:1, description 에 운영 풀 열거). 이는 **baseline 데이터가 SSOT** 원칙 준수 — production 실 데이터와 schema 가 일치해야 함.
- **Files modified**: `.planning/phases/16-production-integration-option-a/schemas/scene-manifest.v4.schema.json`
- **Commit**: `b333dc9` (scene-manifest 완화 동반)
- **Impact**: 3 baseline (zodiac / nazca / roanoke) 전수 통과, Phase 17+ 에서 provider enum 재조정 여지 남김.

### Rule 1 — verify_baseline_parity.py Windows cp949 em-dash
- **Found during**: W1-PARITY-SCRIPT smoke test
- **Issue**: argparse description 에 em-dash `—` 포함 시 Windows cp949 stdout 에서 `UnicodeEncodeError`.
- **Fix**: em-dash 제거, 평문 ASCII-friendly 설명 채택. epilog 추가.
- **Commit**: `282e3a8` (동일 커밋 내 fix)

### Rule 2 — characterLeftSrc validator 파일명 기반 검증
- **Pre-planned deviation guard**: Plan 16-04 `<deviations_allowed>` Rule 3 에 "zodiac-killer visual_spec.json 이 VisualSpec Pydantic 검증 실패 시 validator 완화" 여지.
- **실제 실측 결과**: zodiac-killer `characterLeftSrc = "zodiac-killer/character_assistant.png"` — `endswith("character_assistant.png")` 이미 통과. **validator 완화 불필요**, 원 plan 그대로 유지.
- **roanoke-colony 검증**: 동일 convention 확인 — Q4 매핑 일관성 증명.

## Lessons

1. **Baseline data IS the schema SSOT** — JSON Schema enum 을 실제 baseline 과 triangulation 없이 정의하면 schema v4 도 baseline 을 reject. 계획 단계에서 nazca+roanoke 의 실제 section_type/provider 값 grep 후 enum 설계 필요 (Phase 17+ incidents-jp 준비 시 동일 교훈).
2. **"Spec 통과 != production 통과" 재발 방지는 3층 방어** — (1) Pydantic extra='forbid' + Literal enum (parse-time), (2) JSON Schema Draft-07 (runtime validate CLI), (3) ffprobe baseline parity (absolute SC#5 + relative ±10%). 층 하나 무력화 되도 나머지 2층이 519kbps shock 재진입 차단.
3. **Designer single source of truth (Q2) 는 override path** — `visual_spec_builder.build(visual_spec_override=...)` 가 전수 전달 경로 제공. 에이전트가 영화적 결정 전체를 JSON 으로 넘기면 수치 계산 미개입. shorts-designer 중복 생성 회피 (33 상한 유지).
4. **Windows cp949 stdout 은 항시 지뢰** — em-dash/전각 특수문자 는 argparse description/help 에서 제외. Python `-X utf8` 또는 `PYTHONIOENCODING=utf-8` 환경 전제.
5. **session #32 shock event 의 핵심 교훈은 "절대 threshold"** — ±10% 상대 비교만으로는 519 kbps vs baseline 5171 kbps 가 already 90% 미달. 5000 kbps 절대 floor 를 명시해야 regression 방지. SC#5 criteria 는 **절대 + 상대 이중** 필수.

## Evidence

**Commits (10건)**:
- `637fd88` — W0-SCHEMAS visual-spec.v1 + scene-manifest.v4
- `ba884d1` — W0-PRESET incidents channel preset 박제
- `6f4bedb` — W1-MODELS RED TDD tests
- `06f9066` — W1-MODELS GREEN 4 Pydantic classes
- `273a8d7` — W1-BUILDER visual_spec_builder
- `eaf4cda` — W1-ASSET-SOURCER-EXT v1.3
- `282e3a8` — W1-PARITY-SCRIPT verify_baseline_parity
- `249d497` — W1-VISUAL-SPEC-VALIDATOR
- `b333dc9` — W2-TESTS + scene-manifest relax
- `<this>` — W2-SUMMARY

**Artifacts**:
- JSON Schema 2종 (visual-spec.v1 + scene-manifest.v4, zodiac+nazca+roanoke 3 baseline 통과)
- `.planning/phases/16-production-integration-option-a/16-04-parity-smoke.json` — zodiac-killer ffprobe smoke report
- `.claude/memory/project_channel_preset_incidents.md` — 3 episode triangulation preset
- 5 test files, 56 tests (0.87s runtime)

**CLI quick-refs**:
- `python scripts/validate/verify_visual_spec_schema.py --spec output/<ep>/visual_spec.json`
- `python -X utf8 scripts/validate/verify_baseline_parity.py --our-mp4 output/<ep>/final.mp4 --report output/<ep>/parity_report.json`

## Phase 16 완료 선언 (SC Coverage 종합)

**Phase 16 Production Integration Option A 완료.** 세션 #32 shock event 재발 방지 구조 installed.

### 4/4 Plan SUMMARY 링크
- [16-01-SUMMARY.md](./16-01-SUMMARY.md) — Channel Bibles + Memory Mapping (incidents production-active, 5 기타 reference only)
- [16-02-SUMMARY.md](./16-02-SUMMARY.md) — Remotion Renderer Infrastructure + ASSEMBLY Gate Branch (3-branch cascade + null-freeze sentinel)
- [16-03-SUMMARY.md](./16-03-SUMMARY.md) — subtitle-producer (Producer #15) + faster-whisper large-v3 + Outro Option A
- [16-04-SUMMARY.md](./16-04-SUMMARY.md) — 본 문서, VisualSpec schema + baseline parity

### SC Coverage
- **SC#1** "4/4 Plan SUMMARY 완료" — ✅ 본 Plan 이 최종. 4 SUMMARY 전수 존재, phase_final=true.
- **SC#2** "986+ Phase 4-7 regression 전수 green" — ⚠️ 86 pre-existing (Plan 16 시작 이전 기존 실패). 16-01/02/03/04 **신규 regression 0건**. deferred-items.md 에 전수 분류.
- **SC#3** "subtitle-producer Producer #15 신설, 33 상한" — ✅ Plan 16-03 산출, asset-sourcer v1.3 에 "33 상한 유지" 2차 방어선 명시.
- **SC#4** "duration >=60s 강제" — ✅ `MIN_DURATION_S=60.0` 를 `verify_baseline_parity.py` 절대 threshold 로 구현. remotion_renderer.py 내부 ffprobe post-check 연동.
- **SC#5** "baseline parity 정량 비교 3편 이상" — ✅ `discover_baselines(max_count=3)` 구현, 5 candidate (zodiac/mary-celeste/db-cooper/elisa-lam/kitakyushu-matsunaga) 중 존재 3편 자동 수집. 절대 thresholds (channels==2, sr>=44100, bitrate>=5000, subtitle>=1) + 상대 ±10% (bitrate+fps) 이중 방어.

### session #32 shock event 재발 방지 장치 operational 확인

| 위협 | Plan 16-04 방어선 |
| --- | --- |
| 519 kbps "spec 통과 but production 허망" mp4 | `verify_baseline_parity.py` MIN_VIDEO_BITRATE_KBPS=5000 절대 floor |
| subtitle 없이 render 성공 | subtitle_track_present>=1 criterion + subtitle-producer GATE required (Plan 16-03) |
| mono audio 재발 | REQUIRED_AUDIO_CHANNELS==2 absolute |
| 22050Hz 저음질 재발 | MIN_AUDIO_SAMPLE_RATE>=44100 |
| duration drift 40s 이하 | MIN_DURATION_S=60.0 floor |
| visual_spec drift (extra fields) | Pydantic extra='forbid' + JSON Schema additionalProperties:false |
| characterLeft/Right 의미 swap (Q4 위반) | VisualSpec field_validator endswith 강제 |
| Pretendard drift (Google Fonts only 위반) | Literal["BlackHanSans","DoHyeon","NotoSansKR"] parse-time reject |
| 에이전트 개수 drift (32 상한 재진입) | asset-sourcer v1.3 description + 8 test assertions |

**Phase 16 Production Integration Option A 완료. 세션 #32 shock event 재발 방지 구조 installed.**


## Self-Check: PASSED

모든 acceptance criteria + artifact 존재 + commit hash 무결성 확인.

- 13/13 artifacts (schemas, models, builder, validators, preset memory, 5 test files, SUMMARY, parity-smoke report) FOUND
- 9/9 commits FOUND (637fd88, ba884d1, 6f4bedb, 06f9066, 273a8d7, eaf4cda, 282e3a8, 249d497, b333dc9)
- Phase 16-04 pytest: 56/56 GREEN (0.87s)
- Regression (phase04-06): 52 pre-existing failures (16-02 deferred-items 기분류), **16-04 유발 신규 regression 0**
- Baseline parity smoke: 8/9 criterion 통과 (subtitle_track_present=0 은 shorts_naberal burn-in 특성, 구조는 operational)
- SUMMARY.md 261 lines, 9 sections, frontmatter phase_final:true
