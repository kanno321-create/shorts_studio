# Phase 16: Production Integration Option A — Research

**Researched:** 2026-04-22 (Session #33 pre-planning)
**Domain:** Remotion-based 쇼츠 production 합성 + word-level 자막 + 캐릭터 오버레이 + visual_spec 계약
**Confidence:** HIGH (내부 코드 고고학 증거 기반, 외부 웹리서치 5건 cross-check)
**Researcher:** 나베랄 감마
**Consumer:** `/gsd:plan-phase 16` (Plan 16-01 ~ 16-04 작성)

---

## Summary

Phase 16 의 본질은 **신규 설계가 아니라 이식 (transplant)** 입니다. shorts_naberal 은 6-Stage 파이프라인 (RESEARCH → BLUEPRINT → SCRIPT → ASSETS(parallel 3-way) → RENDER(Remotion) → QA) 을 이미 완성된 상태로 `.preserved/harvested/` 에 읽기 전용으로 포팅되어 있고, 우리의 13 GATE 파이프라인 (`shorts_pipeline.py`) 은 **ASSEMBLY gate 한 지점만 분기** 하면 이 합성 체계를 그대로 받아들일 수 있도록 이미 Shotstack↔ffmpeg 분기 패턴이 구축되어 있습니다 (`_run_assembly` line 515~).

핵심 통찰 3가지:

1. **Remotion 은 한 개의 메인 합성 `ShortsVideo.tsx` 로 전체 쇼츠를 렌더합니다.** 11 개의 카드 컴포지션 (IntroCard, OutroCard, TitleCard 등) 은 그래픽 오버레이 "조각" 이고, 쇼츠 본편의 일차 타임라인은 `ShortsVideo.tsx` 내부의 `<TransitionSeries>` 가 `clips[]` props 를 받아 자체적으로 처리합니다. 즉 우리가 옮겨야 할 "합성 단위" 는 **1 개 composition + 7 개 transition preset + 3 개 crime-specific scene variant (ContextGraphic, ImpactCut, SpeakerSubtitle) + 1 개 BracketCaption** 이고, 나머지 카드들은 long-form 용이므로 Phase 16 범위 밖입니다.

2. **shorts_naberal 은 이미 Python bridge 스크립트 (`remotion_render.py`) 로 Remotion CLI 를 호출하도록 추상화되어 있습니다.** 이 bridge 가 (a) `prepare_remotion_assets` (파일을 `remotion/public/<job_id>/` 에 복사) (b) `build_shorts_props` (script.json + blueprint + visual_spec 을 병합하여 ShortsVideoProps 생성) (c) `validate_shorts_props` (Zod 호환 사전검증) (d) 렌더 후 cleanup — 4 단계를 수행합니다. 우리는 이 bridge 를 **`scripts/orchestrator/api/remotion_renderer.py`** 로 미러하여 `ffmpeg_assembler` 와 동일한 `.render(timeline, resolution, aspect_ratio) -> dict` signature 로 포장하면 됩니다.

3. **word-level 자막은 faster-whisper large-v3 + Korean timestamp repair pattern 으로 해결됩니다.** shorts_naberal 이 정확히 이 조합을 production 에서 검증했고 (`audio_pipeline_raw/word_subtitle.py`, 1697 줄, SRT+ASS+JSON 3종 한 번에 생성). 우리 inspector `ins-subtitle-alignment` 의 AGENT.md 가 "상류 = subtitle-producer" 를 명시하지만 실제로 `subtitle-producer/` 디렉토리는 없는 상태 — 설계상 이미 빈 자리가 비어 있습니다.

**Primary recommendation:** Plan 16-02 (Remotion renderer wiring) 가 가장 큰 리스크. Plan 16-03 (자막) 은 신규 producer (`subtitle-producer`) 를 추가하여 Producer 14 → 15 로 1명 증가 (32 에이전트 상한 Producer 14+Inspector 17+Supervisor 1=32 → 15+17+1=33 의 룰 완화 필요). Plan 16-04 (visual_spec) 은 `asset-sourcer` 의 출력 스키마 확장만으로 해결 가능 — 신규 에이전트 추가 불필요. Plan 16-01 (채널바이블 박제) 은 코드 수정 0, 텍스트 박제만.

---

## User Constraints (from CLAUDE.md + ROADMAP.md Phase 16 block)

### Locked Decisions (리서치 대상 아님)

- **A 즉시도입** — shorts_naberal production architecture 채택 (대표님 2026-04-22).
- **Veo 방침**: (a) 기존 Veo 자산 (`.preserved/harvested/video_pipeline_raw/` + `output/_shared/signatures/incidents_intro_v4_silent_glare.mp4`) 참조·복사만. Veo API 신규 호출 금지. Kling 재생성도 이번 Phase 에서 하지 않음.
- **Kling 2.6 Pro 단독** (I2V only) — Veo 변종 금지.
- **I2V 보조용만, 실제 이미지 최우선** (incidents.md §9 + `feedback_veo_supplementary_only`). 우리 현재의 "I2V primary" 정책을 **역전** 필요.
- **gpt-image-2 primary, Nano Banana fallback** (정지 이미지, `project_image_stack_gpt_image2` 박제 확정).
- **Remotion composition 채택** (대표님 "A 즉시도입이다"). ffmpeg_assembler 는 fallback 으로 유지.

### Claude's Discretion (나베랄 판단 영역)

- **Python bridge 이름**: `remotion_renderer.py` vs `shorts_video_composer.py` 등 — 본 리서치는 `remotion_renderer.py` 권장.
- **subtitle producer 명명**: `subtitle-producer` vs `word-subtitle-producer` — `ins-subtitle-alignment` 가 이미 "subtitle-producer" 를 언급하므로 이 이름 권장.
- **asset-sourcer 확장 vs 신규 producer**: visual_spec 생성 주체. 본 리서치는 asset-sourcer **확장** 을 prescriptive 로 권장 (아래 Q2 참조).
- **캐릭터 파일 조달 채널**: `output_dir/sources/` 디렉토리 구조 (shorts_naberal baseline 패턴 유지).

### Deferred Ideas (OUT OF SCOPE — Phase 16 에서는 처리 안 함)

- **일본 채널 변환 (incidents-jp)** — Phase 16 에서는 한국 채널(incidents)만. 일본 채널은 별도 Phase 로 분리 (`channel-incidents-jp` SKILL 존재하지만 이식 나중).
- **Long-form 16:9 파이프라인** — `LongformVideo.tsx` + `longform_subtitle.py` 는 Phase 16 범위 밖.
- **Kling 재생성** — 기존 자산 없는 편 새로 만드는 것 금지 (대표님 locked).
- **42 항목 QA 체크리스트 전체 이식** — 현재 17 inspector + 이번 Phase 에서 subtitle-producer 추가 후 나머지 25 inspector 는 별도 Phase.
- **Human-in-the-Loop 3 승인 게이트** — 프로세스 설계 이슈, 별도 Phase.
- **채널바이블 7 전부** — Phase 16-01 에서는 incidents.md 하나만 박제하고 나머지 6 (wildlife/humor/politics/trend/documentary + README) 는 구조만 복사 후 Phase 17+ 로 연기 가능. (Plan 16-01 에서 최종 결정)

---

## Phase Requirements

Phase 16 은 신규 REQ 가 plan-phase 에서 추가될 예정이므로 본 리서치는 **가능한 REQ ID 영역을 예약** 합니다. plan-phase 가 아래 제안을 참조하여 REQ 번호를 발급:

| 예약 ID | Description | Research Support |
|---------|-------------|------------------|
| REQ-PROD-INT-01 | ASSEMBLY gate 에 Remotion renderer 경로 신설 (ffmpeg_assembler fallback 유지) | §Architecture Patterns §Q1 |
| REQ-PROD-INT-02 | `remotion_renderer.py` bridge 작성 — `remotion_render.py:render_shorts_video` 패턴 미러 | §Code Examples #1 |
| REQ-PROD-INT-03 | ShortsVideoProps Zod schema 호환 검증 (`build_shorts_props` + `validate_shorts_props` 패턴) | §Q1 + §Code Examples #2 |
| REQ-PROD-INT-04 | word-level 자막 생성 producer 신규 (`subtitle-producer`) — faster-whisper large-v3 + SRT/ASS/JSON 3종 출력 | §Q3 |
| REQ-PROD-INT-05 | `ins-subtitle-alignment` description 정정 (WhisperX → faster-whisper + 실제 시스템 정합) | §Q3 |
| REQ-PROD-INT-06 | `visual_spec.json` 산출 책임 → asset-sourcer 확장 (schema `clipDesign[]` + `characterLeftSrc`/`characterRightSrc` + `titleKeywords` + `subtitlePosition`) | §Q2 |
| REQ-PROD-INT-07 | 캐릭터 오버레이 파일 조달 → asset-sourcer, 합성 injection → remotion_renderer.py | §Q4 |
| REQ-PROD-INT-08 | 인트로/아웃로 시그니처 재사용 (`output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` 참조·복사) — Veo 신규 호출 금지 | §Don't Hand-Roll |
| REQ-PROD-INT-09 | `output_dir/sources/` 디렉토리 구조 강제 — scene-manifest.json v4 계약 | §Code Examples #3 |
| REQ-PROD-INT-10 | `visual_spec.clipDesign[]` movement=null ⇒ 의도적 freeze (sentinel `_NULL_FREEZE` 패턴) | §Common Pitfalls #4 |
| REQ-PROD-INT-11 | 채널바이블 `incidents.md` v1.0 박제 → `.claude/memory/project_channel_bible_incidents_v1.md` | §User Constraints |
| REQ-PROD-INT-12 | production feedback 12+ 항목 매핑 (`feedback_*` 메모리로 박제 또는 참조) | §User Constraints |
| REQ-PROD-INT-13 | baseline 정량 비교 검증 — ffprobe 1080×1920 + ≥60s + 자막 트랙 + 자료사진 ≥5 | §Common Pitfalls #1 |
| REQ-PROD-INT-14 | Narration Drives Timing 불변 — TTS ffprobe 실측 → durationInFrames 자동보정 (shotts-pipeline SKILL.md Core Principle) | §Architecture Patterns Pattern 4 |

---

## Standard Stack

### Core (HIGH confidence — internal package.json + harvested code)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `remotion` | ^4.0.0 (최신 4.0.448) | 쇼츠 본 합성 엔진 (React-based video) | shorts_naberal production 확정 스택 |
| `@remotion/cli` | ^4.0.0 | CLI renderer (`npx remotion render`) | Python bridge 에서 subprocess 호출 대상 |
| `@remotion/transitions` | ^4.0.445 | TransitionSeries + 7 presentation | `ShortsVideo.tsx:549` line 에서 직접 사용 |
| `@remotion/captions` | ^4.0.441 | SRT/caption 파서 (선택, 참고용) | shorts_naberal 의존성에 존재 |
| `@remotion/fonts` | ^4.0.0 | 폰트 관리 | `lib/fonts.ts` 에서 BlackHanSans/DoHyeon/NotoSansKR 로드 |
| `@remotion/google-fonts` | ^4.0.441 | Google Fonts 자동 로드 | Pretendard **금지**, Google Fonts 만 |
| `react` + `react-dom` | ^18.3.1 | Remotion 런타임 | — |
| `zod` | ^4.3.6 | Props schema validation (`shortsVideoSchema`) | ShortsVideo.tsx line 98~ Zod 사용 |
| `typescript` | ^5.4.0 | Remotion 코드 baseline | — |
| Node.js | ≥ 16.0.0 (권장 20.x) | Remotion 4.x 최소 | remotion.dev 공식 |
| Chrome Headless Shell | 자동 설치 | 렌더러 엔진 (Windows x64 지원) | remotion.dev 공식 |
| `faster-whisper` | ≥ 1.0.0 (latest) | 자막 word-level 전사 | `word_subtitle.py:1338` `WhisperModel` CUDA→CPU 폴백 |
| `faster-whisper` model | `large-v3` | 한국어 CER 최적 | `word_subtitle.py:1642` 기본값 |
| `ffmpeg` (PATH) | 시스템 설치 | audio duration 측정 + fallback 조립 | `remotion_render.py:304` ffprobe 호출 |

### Supporting (MEDIUM confidence — harvested code indirect)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Kling 2.6 Pro (I2V) | API (client already wired) | I2V **보조용만** | 실제 자료 이미지/영상 없을 때만 4순위 |
| gpt-image-2 | API (Phase 15) | Anchor/sources 이미지 생성 | 1순위 대체 (`project_image_stack_gpt_image2`) |
| Nano Banana | API (Phase 15 fallback) | Anchor fallback | gpt-image-2 rate limit 시 |
| Typecast Morgan | API (Phase 15) | 탐정 보이스 (`ssfm-v30`, tempo 0.93, tonedown) | `blueprint.json:voice_hint.main` |
| Typecast Guri | API (Phase 15) | 왓슨 보이스 (`ssfm-v21`, normal) | `blueprint.json:voice_hint.assistant` |
| ElevenLabs | API (Phase 15 fallback) | Typecast 장애 시 TTS fallback | D-10 |

### Alternatives Considered & Rejected

| Instead of | Rejected Alternative | Rejection Reason |
|------------|---------------------|------------------|
| faster-whisper large-v3 | WhisperX (ins-subtitle-alignment 현재 description) | shorts_naberal production 에서 faster-whisper 채택 확정. WhisperX 는 화자 분리(diarization) 에 강점이나 우리는 듀오 내레이션 역할을 script.speaker 필드로 이미 고정하므로 불필요. Inspector description 정정 필요 (REQ-PROD-INT-05). |
| faster-whisper large-v3 | Whisper Large V3 Turbo (6x 빠름) | 한국어 정확도 1~2% 하락 위험. 쇼츠는 60~120s 이므로 속도보다 정확도 우선. |
| Whisper word_timestamps=True | Whisper segment-level only | Korean word timestamps 는 unreliable 이나 `word_subtitle.py:1326~1523` 이 clamp/merge/fallback 수리 파이프라인을 이미 완비. 구간만으로는 "단어단위 하이라이트" 불가능. |
| Remotion CLI 호출 | Remotion Lambda (AWS) | 대표님 locked: 로컬 Windows 실행. Lambda 도입 시 AWS 비용 + IAM 복잡도. Phase 17+ 고려. |
| libass + ffmpeg subtitles 필터 | Native ASS 렌더 | Remotion 은 ASS 파일을 직접 읽지 않음 — `subtitles_remotion.json` 의 cue 배열을 props 로 받아 React 컴포넌트가 직접 렌더. ASS 는 외부 편집자/검증용. |
| Pretendard 폰트 | Pretendard Bold 700 | `shorts-designer/SKILL.md:133` "Pretendard 사용 금지 — Google Fonts (BlackHanSans/DoHyeon/NotoSansKR)". shorts_naberal `lib/fonts.ts` 확정. |

### Installation

**Node-side (new — remotion workspace):**

```bash
# Phase 16-02 Task 1 — remotion/ 디렉토리 신규 스캐폴드
cd C:/Users/PC/Desktop/naberal_group/studios/shorts
mkdir remotion
cd remotion
cat > package.json << 'EOF'
{
  "name": "shorts-remotion",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "studio": "remotion studio src/index.ts",
    "render": "remotion render src/index.ts"
  },
  "dependencies": {
    "@remotion/captions": "^4.0.441",
    "@remotion/cli": "^4.0.0",
    "@remotion/fonts": "^4.0.0",
    "@remotion/google-fonts": "^4.0.441",
    "@remotion/transitions": "^4.0.445",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "remotion": "^4.0.0",
    "zod": "^4.3.6"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.4.0"
  }
}
EOF
npm install
```

**Python-side (new — faster-whisper):**

```bash
# Phase 16-03 Task 1 — subtitle-producer 환경
pip install faster-whisper  # CTranslate2 기반, 최신 (≥1.0)
# CUDA: pip install nvidia-cudnn-cu12 nvidia-cublas-cu12  (선택)
```

**Version verification protocol:**

```bash
npm view remotion version                           # 4.0.448 expected (2025-04 기준)
npm view @remotion/transitions version              # 4.0.445+
pip index versions faster-whisper                   # 1.x.x
```

모든 Task action 에 version pinning 문자열 기록 필수.

---

## Architecture Patterns

### Recommended Project Structure (Post Phase 16)

```
shorts/
├── remotion/                                   ★ Phase 16-02 신규
│   ├── package.json                            (위 baseline)
│   ├── tsconfig.json
│   ├── src/
│   │   ├── index.ts                            (registerRoot)
│   │   ├── Root.tsx                            (Composition registry)
│   │   ├── compositions/
│   │   │   └── ShortsVideo.tsx                 (메인 쇼츠 합성 - harvested 1:1 복사)
│   │   ├── components/
│   │   │   ├── BracketCaption.tsx
│   │   │   └── crime/
│   │   │       ├── ContextGraphicScene.tsx
│   │   │       ├── ImpactCutScene.tsx
│   │   │       ├── SpeakerSubtitle.tsx
│   │   │       └── index.ts
│   │   └── lib/
│   │       ├── fonts.ts                        (BlackHanSans + Japanese 조건 로드)
│   │       ├── props-schema.ts
│   │       └── transitions/presentations/      (glitch, rgbSplit, zoomBlur, lightLeak, clockWipe, pixelate, checkerboard + @remotion/transitions fade)
│   └── public/                                 (per-job assets 임시, render 후 cleanup)
├── scripts/
│   ├── orchestrator/
│   │   ├── shorts_pipeline.py                  (ASSEMBLY gate 분기 수정 — §Pattern 1)
│   │   ├── api/
│   │   │   ├── ffmpeg_assembler.py             (유지 - fallback)
│   │   │   └── remotion_renderer.py            ★ 신규 (Phase 16-02) — remotion_render.py 미러
│   │   ├── subtitle/
│   │   │   └── word_subtitle.py                ★ 신규 (Phase 16-03) — harvested 미러 + 우리 에이전트 frontmatter
│   │   └── intro_outro_signature.py            ★ 신규 (Phase 16-03) — 기존 자산 재사용, 생성 금지
├── output/
│   ├── _shared/signatures/
│   │   └── incidents_intro_v4_silent_glare.mp4 ★ Phase 16-03 시점에 `.preserved/harvested/` 에서 복사
│   └── <episode>/                              ★ per-run artifact dir
│       ├── sources/                            (Phase 16-04 계약)
│       │   ├── character_detective.png         (asset-sourcer 조달)
│       │   ├── character_assistant.png         (asset-sourcer 조달)
│       │   ├── intro_signature.mp4             (asset-sourcer 복사)
│       │   ├── outro_signature.mp4             (asset-sourcer 복사)
│       │   ├── z340_cipher_original.jpg        (asset-sourcer 조달 — gpt-image-2 or Serper)
│       │   └── ... (≥5 sources 강제)
│       ├── visual_spec.json                    ★ asset-sourcer 산출 (Phase 16-04)
│       ├── scene-manifest.json                 (v4 schema, Phase 16-04 정립)
│       ├── script.json
│       ├── blueprint.json
│       ├── narration.mp3
│       ├── subtitles_remotion.json             ★ subtitle-producer 산출 (Phase 16-03)
│       ├── subtitles_remotion.ass              ★ subtitle-producer 산출
│       ├── subtitles_remotion.srt              ★ subtitle-producer 산출
│       ├── section_timing.json                 (Narration Drives Timing)
│       └── final.mp4                           ★ remotion_renderer.py 산출 (replaces ffmpeg outputs/ffmpeg_assembly/)
├── .claude/
│   ├── agents/
│   │   └── producers/
│   │       └── subtitle-producer/              ★ 신규 (Phase 16-03)
│   │           └── AGENT.md
│   └── memory/
│       └── project_channel_bible_incidents_v1.md ★ 신규 (Phase 16-01)
└── .preserved/harvested/                       (유지 — read-only)
```

### Pattern 1: ASSEMBLY Gate Branching (Shotstack → Remotion → ffmpeg fallback)

**What:** `_run_assembly` (`shorts_pipeline.py:515`) 가 현재 Shotstack/ffmpeg 2분기. Remotion 을 **1 순위** 로 추가하여 3분기.

**When to use:** 모든 ASSEMBLY 호출 (GATE 9). Remotion 가 사용 가능하면 Remotion, 아니면 ffmpeg (Shotstack 은 미인증 상태 유지).

**Evidence:** `shorts_pipeline.py:524~545` 현재 구조
```python
renderer = self.shotstack if self.shotstack is not None else self.ffmpeg_assembler
if renderer is None:
    raise RuntimeError("ASSEMBLY renderer 미구성 ...")
```

**New pattern (Phase 16-02 Task 3):**
```python
# ASSEMBLY gate renderer priority: Remotion > Shotstack > FFmpeg
renderer = (
    self.remotion_renderer
    or self.shotstack
    or self.ffmpeg_assembler
)
if renderer is None:
    raise RuntimeError("ASSEMBLY renderer 미구성 ...")

render_result = renderer.render(
    timeline,
    resolution="fhd",  # 1080x1920 (9:16)
    aspect_ratio="9:16",
)
```

`remotion_renderer` 는 생성자에서 `node --version` + `npx remotion --help` probe 로 사용 가능성 판단. 실패 시 `None` 할당 → ffmpeg fallback 자동.

### Pattern 2: Python Bridge `RemotionRenderer` (ffmpeg_assembler 와 동일 API)

**What:** harvested `remotion_render.py:render_shorts_video` (line 776~1043, 268 줄) 을 미러하여 `scripts/orchestrator/api/remotion_renderer.py` 작성. 단 signature 는 Shotstack/ffmpeg 과 동일한 `.render(timeline, resolution, aspect_ratio) -> dict` 포맷.

**Flow:**
1. `prepare_remotion_assets(output_dir, project_root, scene_clips, audio_path, bgm_path, channel, ...)` — 자산을 `remotion/public/<job_id>/` 에 복사
2. `get_audio_duration_ffprobe(audio_path)` — ffprobe 실측 (±1s 초과 시 ffprobe 값 우선)
3. **Quality gates** (pre-render):
   - scene clips 개수 ≥ 1
   - 자막 coverage ≥ 95% (last_end_ms / audio_ms ≥ 0.95)
4. `build_shorts_props(script, channel, assets, subtitle_json_path, audio_duration, blueprint, visual_spec_provided)` — Zod-호환 props dict 생성
5. `validate_shorts_props(props)` — pre-Zod sanity check
6. `subprocess.run(["npx", "remotion", "render", entry, "ShortsVideo", output, f"--props={...}", "--codec=h264", "--fps=30", "--width=1080", "--height=1920"], cwd=remotion_dir, shell=True on Windows, timeout=600)`
7. `cleanup_remotion_assets(project_root, job_id)` — `remotion/public/<job_id>/` 삭제

**Return shape:**
```python
{"url": final_path_str, "status": "assembled", "renderer": "remotion", "duration_frames": N, "size_mb": X.X}
```

### Pattern 3: `visual_spec.json` 계약 (Designer 대체 = asset-sourcer 확장)

**What:** shorts_naberal 은 `shorts-designer` 에이전트가 visual_spec 생성. 우리는 **asset-sourcer 출력 스키마를 확장** 하여 동일 역할 수행 (32 에이전트 상한 + 책임 분할 최소 침해).

**When to use:** ASSETS gate (GATE 8) 에서 asset-sourcer 가 visuals[] 를 산출할 때, visual_spec.json 으로 동시 출력.

**Extended asset-sourcer output schema (Phase 16-04):**
```json
{
  "gate": "ASSETS",
  "niche_tag": "incidents",
  "render_mode": "I2V_only_supplementary",
  "visual_spec": {
    "titleLine1": "50년 미제",
    "titleLine2": "암호 살인마",
    "titleKeywords": [{"text": "미제", "color": "#FF2200"}, {"text": "살인마", "color": "#FF2200"}],
    "accentColor": "#FF2200",
    "channelName": "사건기록부",
    "hashtags": "#쇼츠 #범죄 #조디악킬러 #미해결사건",
    "fontFamily": "BlackHanSans",
    "characterLeftSrc": "zodiac-killer/character_assistant.png",
    "characterRightSrc": "zodiac-killer/character_detective.png",
    "subtitlePosition": 0.8,
    "subtitleHighlightColor": "#FFFFFF",
    "subtitleFontSize": 68,
    "audioSrc": "zodiac-killer/narration.mp3",
    "transitionType": "fade",
    "clipDesign": [
      {"index": 0, "type": "video", "src": "zodiac-killer/intro_signature.mp4", "movement": null, "transition": "fade"},
      {"index": 1, "type": "image", "src": "zodiac-killer/z340_cipher_original.jpg", "movement": "pan_right", "transition": "fade"},
      ...
    ]
  },
  "i2v_clips": [...],  // 기존 필드 유지
  "audio": {...},      // 기존 필드 유지 (bg_music + hook_sample)
  "visuals": [...],    // 기존 필드 유지 (but 이제 visual_spec.clipDesign[] 의 소스로도 사용)
  "source_strategy": {
    "real_image_target": 6,
    "veo_supplement": 2,
    "signature_reuse": 2,
    "real_ratio": 0.81   // baseline: zodiac-killer 가 0.81 — ≥0.75 강제
  }
}
```

**근거:**
- `visual_spec.json` 의 모든 필드는 shorts_naberal `baseline_specs_raw/zodiac-killer/visual_spec.json` 과 동일 스키마.
- `clipDesign[]` 은 Remotion 의 "Single source of truth" (`remotion_render.py:833~869`): `visual_spec_path` 가 주어지고 clipDesign 이 비어있지 않으면 모든 movement 를 Designer 결정으로 고정. 자동 round-robin 배정 중단.
- asset-sourcer 는 이미 `visuals[]` 와 `audio.bg_music_track` 을 산출 — 디자인 메타(`titleKeywords` / `accentColor` / `characterLeftSrc` / ... ) 만 추가하면 Designer 역할 흡수.

### Pattern 4: Narration Drives Timing (불변 원칙)

**What:** TTS 실제 출력 duration 이 전체 영상 길이를 결정. 영상·이미지 클립은 이에 맞춰 스케일/조각.

**Flow (shorts-pipeline/SKILL.md 고정):**
```
Script 텍스트 → TTS 생성 → ffprobe 실측 → durationInFrames = sec × 30fps
→ section_timing.json (per-section duration_ms)
→ visual_spec.clipDesign[i].durationInFrames = section_timing[i].duration_ms × 30 / 1000
→ Remotion 렌더
```

**Evidence:** `remotion_render.py:894~906`
```python
# 1b. Verify audio duration via ffprobe
ffprobe_duration = get_audio_duration_ffprobe(audio_path)
if ffprobe_duration > 0.0:
    diff = abs(ffprobe_duration - audio_duration)
    if diff > 1.0:
        logger.warning("Audio duration mismatch: caller=%.3fs, ffprobe=%.3fs ...")
        audio_duration = ffprobe_duration  # ffprobe 값 우선
```

**우리 구현 지점:** `VoiceFirstTimeline.align()` 이 이미 "오디오 길이 기준 정렬" 을 수행 (ORCH-10). Phase 16 에서는 Remotion renderer 호출 시 **VoiceFirstTimeline 산출을 visual_spec.clipDesign[].durationInFrames 로 환산**하는 어댑터 함수만 추가.

### Pattern 5: `scene-manifest.json` v4 계약 (Phase 16-04)

**What:** shorts_naberal 이 per-episode 단일 JSON 으로 모든 scene 메타를 담는 v4 스키마. 우리는 GATE 별 artifacts 로 흩어져 있는 정보를 이 스키마로 통합.

**Example:** `.preserved/harvested/baseline_specs_raw/zodiac-killer/scene-manifest.json` (zodiac-killer 197 줄, 15 clips, source_stats 포함)

**Schema (top-level):**
```json
{
  "version": "v4",
  "channel": "incidents",
  "category": "crime",
  "topic": "조디악 킬러",
  "total_clips": 15,
  "clips": [
    {
      "index": 0,
      "section_type": "intro|hook|body|outro",
      "narration_sentence": "...",
      "duration_s": N,
      "source": {
        "type": "image|video|signature|remotion",
        "local_path": "sources/...",
        "provider": "serper|gpt_image2|veo_reuse|kling|...",
        "description": "..."
      }
    }
  ],
  "source_stats": {
    "total": 16,
    "real_image": 13,
    "signature": 2,
    "real_ratio": 0.81
  }
}
```

**책임 분할 (우리 측):**
- Scenes 채움 = scripter (narration_sentence, section_type, duration_s)
- Sources 채움 = asset-sourcer (local_path, provider, description)
- Manifest 병합 및 v4 계약 출력 = `asset-sourcer` 확장분 (§Q2 근거)

### Anti-Patterns to Avoid

- **ShortsVideo.tsx 의 레이아웃 상수 (`TOP_BAR_H=320`, `BOTTOM_BAR_H=333`) 를 우리 측에서 재조정** — DESIGN_SPEC.md 의 픽셀 분석 기반. 수정 시 자막 위치·캐릭터 크기 모두 어긋남.
- **Pretendard 폰트 사용** — `shorts-designer/SKILL.md:133` 명시 금지. Google Fonts (BlackHanSans/DoHyeon/NotoSansKR) 전용.
- **ASS 파일을 Remotion 에 직접 먹이기** — Remotion 은 ASS 네이티브 로더가 없음. `subtitles_remotion.json` 을 props 로 전달해야 함. ASS 는 외부 편집자 / 검증 용도만.
- **자막 cue 배열을 script 텍스트에서 추정 생성** — `_build_render_props_v2.py:115~132` 의 "chunk of 5 words per equal split" 은 fallback 만. 실제 word-level 정렬은 faster-whisper 필수.
- **Round-robin movement 배정** — `remotion_render.py:843~852` 가 visual_spec 제공 시 비활성화. 우리도 동일 규칙: visual_spec 이 있으면 Designer 가 결정한 movement/transition 을 유일 진실로 사용.
- **Veo 신규 호출** — 대표님 금지. `generate_intro_signature.py:67~80` 의 VeoClient 호출 경로는 **참조 금지**. 기존 자산 재사용만.
- **Selenium 업로드** — 관련 없음이지만 금기 #5 mirror.
- **32 에이전트 상한 깨는 것 없이 subtitle-producer 추가 거부하여 ins-subtitle-alignment 에 생성 로직 주입** — GAN 분리 원칙 위반 (RUB-02). Inspector 는 검증만, Producer 는 생성만.

---

## Don't Hand-Roll

이 도메인에서 재구현 금지. 반드시 existing 패턴을 인용 또는 복사해야 할 항목:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **Remotion ShortsVideo 합성 로직** | React/TSX 1000+ 줄 재작성 | `.preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx` 를 `remotion/src/compositions/` 로 1:1 복사 | 합성 로직 744 줄. TopBar (320px, 캐릭터 좌우), 센터 VIDEO_H (1267px, TransitionSeries), 자막 word-highlight (instant switch), 하단 BottomBar (333px, 구독/좋아요/seriesPart) — 모두 DESIGN_SPEC.md 픽셀 분석 기반. 1 픽셀도 재계산 말 것. |
| **7 transition presentations** | glitch/rgbSplit/zoomBlur/lightLeak/clockWipe/pixelate/checkerboard 커스텀 구현 | `.preserved/harvested/remotion_src_raw/lib/transitions/presentations/*.tsx` 복사 | 각 presentation 은 `@remotion/transitions` 의 `PresentationComponent` 인터페이스 구현. `getTransitionConfig` 의 frame 단위 (glitch=20f, lightLeak=35f, cut=1f) 도 shorts_naberal 검증값. |
| **word-level 자막 생성** | faster-whisper + Korean timestamp repair 로직 재구현 | `.preserved/harvested/audio_pipeline_raw/word_subtitle.py` 1697 줄 포팅 (우리 `scripts/orchestrator/subtitle/word_subtitle.py` 로) | Korean word timestamps unreliable → clamp to segment + merge <100ms + fallback even-distribution 수리 파이프라인 (`_extract_words_from_segments` + 그 뒤 ~1000 줄). SRT + ASS + JSON 3종 한 번에 생성. CUDA→CPU 폴백 포함. |
| **ASS karaoke 효과 렌더** | libass 바인딩 + ffmpeg 필터 체인 | Remotion 내장 word-highlight (ShortsVideo.tsx:655~) | Remotion 이 props 로 받은 cue 배열을 React 상태로 관리하여 현재 frame 에 맞는 highlightIndex 의 단어만 색상/굵기 변경. libass 불필요. ASS 파일은 외부 편집자/검증 용. |
| **Ken Burns (pan/zoom) 이미지 애니메이션** | ffmpeg zoompan 필터 | Remotion `KenBurnsImage` 컴포넌트 (ShortsVideo.tsx 내부 function) | Remotion 이 interpolate() 로 프레임 단위 scale/translate 계산. ffmpeg zoompan 은 품질 / 프레임 정밀도 열등. |
| **인트로/아웃로 시그니처 생성** | Veo API 신규 호출 | `output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` 기존 자산 복사 | 대표님 locked — Veo 신규 호출 금지. `generate_intro_signature.py` 는 참조 금지 코드. |
| **scene-manifest v4 스키마** | 자체 스키마 정의 | `.preserved/harvested/baseline_specs_raw/zodiac-killer/scene-manifest.json` 스키마 1:1 미러 | 197 줄 샘플이 이미 production 검증. version/channel/category/topic/total_clips/clips[]/source_stats 필드 모두 Remotion + QA 체크리스트가 소비. |
| **visual_spec.json 스키마** | 자체 designer spec 정의 | `.preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json` (138 줄) 1:1 스키마 + clipDesign[] 추가 | `remotion_render.py:833~869` 가 이 스키마 하드코딩. 필드 한 개만 달라도 Zod validation 실패. |
| **build_shorts_props 병합 로직** | script+blueprint+assets→props 수동 변환 | `.preserved/harvested/video_pipeline_raw/remotion_render.py:501~773` (`build_shorts_props` + `validate_shorts_props`) | 270 줄. title 분할 (blueprint > script.title dict > heuristic), accent 결정, transitionType 자동 round-robin, 캐릭터 인젝션, series 배지, BGM, subtitle cue 로드, Quality Gates (clip 수 ≥ 1 + subtitle coverage ≥ 95%) 를 모두 수행. 재구현 리스크 극대. |
| **한국어 폰트 로딩** | @font-face 직접 | `.preserved/harvested/remotion_src_raw/lib/fonts.ts` 그대로 복사 | BlackHanSans / DoHyeon / NotoSansKR + 일본어 폰트 조건 로드 (`ensureJpTitleFont`). 누락 시 fallback 처리 포함. |
| **TTS audio duration 측정** | librosa / pydub 로 duration 계산 | `ffprobe -show_entries format=duration` subprocess (`remotion_render.py:293~320`) | librosa 는 PCM 디코딩 비용 큼. ffprobe 는 metadata 만 읽음. 이미 ffmpeg 이 Path 에 있으므로 추가 의존성 없음. |

**Key insight:** Phase 16 의 본질적 위험은 **"우리가 더 잘 짤 수 있다"** 는 유혹입니다. shorts_naberal 은 Session 37~75 (약 38 세션 분량) 동안 여러 실패를 거쳐 현 구조에 도달했습니다. 예컨대 `word_subtitle.py` 의 Korean timestamp repair 는 FAIL-SCR-016, FAIL-EDT-008 등 다수의 실패를 흡수한 결과이며, `clipDesign[] single source of truth` 패턴은 FAIL-DES-008 근본 방지 후의 결론입니다. **코드 복사 + 우리 에이전트 frontmatter 랩핑** 전략을 권장.

---

## Runtime State Inventory

> 이 Phase 는 **코드/구성 변경 + 신규 파일 생성** 이지만 rename 이나 migration 은 아닙니다. 그러나 "파일 경로 계약" 이 시스템 전반에 흩어지므로 관련 runtime state 를 점검합니다.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — ChromaDB / Mem0 등 외부 datastore 없음. `.claude/memory/` 는 git 버전관리. | 없음 |
| Live service config | `output/_shared/signatures/` 디렉토리 — 시그니처 재사용 저장소. 세션 간 영속. | Phase 16-03 에서 `.preserved/harvested/video_pipeline_raw/` 의 기존 시그니처를 `output/_shared/signatures/` 로 복사하는 일회성 task 필요. |
| OS-registered state | None — Windows Task Scheduler 등 등록 상태 없음 | 없음 |
| Secrets/env vars | `GOOGLE_API_KEY` (Veo 신규 호출 금지이므로 **사용 금지** 표시 필요), `KLING_API_KEY`, `OPENAI_API_KEY` (gpt-image-2), `TYPECAST_API_KEY`, `SERPER_API_KEY` (자료사진 조달), Typecast `MORGAN_VOICE_ID` / `GURI_VOICE_ID` | GOOGLE_API_KEY 는 코드 주석에 "Veo 금지 — 금기 #11" 명시. 기존 `.env` 구조 변경 없음. |
| Build artifacts | `remotion/public/<job_id>/` 는 render 후 자동 cleanup (`cleanup_remotion_assets`). `remotion/node_modules/` 는 `.gitignore` 필요. `remotion/dist/` 없음 (bundler 없이 CLI 호출). | `.gitignore` 업데이트: `remotion/node_modules/`, `remotion/public/*/` (단 `remotion/public/bgm/` 은 git 포함), `output/*/remotion_props.json` (임시). |

**Nothing found in category `Stored data` or `OS-registered state`**: verified by grepping `.claude/memory/`, `docs/ARCHITECTURE.md`, `scripts/orchestrator/` for ChromaDB/SQLite/Task Scheduler/pm2/launchd — 해당 시스템 미사용.

---

## Common Pitfalls

### Pitfall 1: "Spec 통과 = Production 완료" 재발

**What goes wrong:** 모든 13 GATE supervisor verdict 가 PASS 인데 최종 mp4 는 13s + 자막없음 + 캐릭터없음 (세션 #31 실제 사례).

**Why it happens:** Supervisor verdict 는 **artifact 존재** 를 검증 — 품질은 보지 않음. ffmpeg_assembler 가 `timeline` 을 받아 mp4 를 만들면 `url` 필드가 채워지고 ASSEMBLY PASS.

**How to avoid:** Phase 16-02 Task N 에 **Post-render ffprobe 검증** 을 renderer 내부에 강제 주입.
```python
def _verify_production_baseline(final_path: Path) -> None:
    meta = subprocess.run(["ffprobe", "-v", "error", "-show_format",
                           "-show_streams", "-of", "json", str(final_path)],
                          capture_output=True, text=True, timeout=30)
    info = json.loads(meta.stdout)
    width = int(info["streams"][0]["width"])
    height = int(info["streams"][0]["height"])
    duration = float(info["format"]["duration"])
    assert width == 1080 and height == 1920, f"해상도 불량: {width}x{height}"
    assert duration >= 50.0, f"영상 길이 불량: {duration}s < 50s baseline"
    # subtitle track 은 hardcoded burn-in 이므로 mp4 에 별도 track 없음 — 대신
    # subtitles_remotion.json 의 cue 수 ≥ 15 검증 (60s 에 단어당 0.25s)
```

**Warning signs:** verifier 로그에서 "ffprobe: width=720, height=1280" 또는 "duration < 30s" 발견.

### Pitfall 2: Korean word timestamp drift > 150ms

**What goes wrong:** 자막이 말보다 먼저 나오거나 뒤처져 시청자가 자막과 음성 불일치를 즉각 인지 → 완주율 급락.

**Why it happens:** faster-whisper 의 word_timestamps 는 Korean 에서 부정확. 한국어의 의미단위가 영어 word boundary 와 다름.

**How to avoid:** `word_subtitle.py` 의 3단계 repair 적용 (포팅 시 절대 생략 금지):
1. **Segment boundary clamp**: word.start < segment.start 이면 segment.start 로 클램프
2. **<100ms merge**: duration < 100ms 단어는 인접 단어와 병합
3. **Fallback even distribution**: word_timestamps 가 아예 없으면 segment 텍스트를 균등 분배

**Warning signs:** `ins-subtitle-alignment` 의 drift > 150ms FAIL rate 증가.

### Pitfall 3: Remotion render chrome headless download 타임아웃

**What goes wrong:** 최초 `npx remotion render` 호출 시 Chrome Headless Shell 을 다운로드 (~200MB). 이게 60s default timeout 내에 안 끝나서 render 실패.

**Why it happens:** CI / cold start 환경에서 Chrome 이 아직 `node_modules/.cache/` 에 없음.

**How to avoid:** `remotion_render.py:176~177` 의 first-render 로직 미러:
```python
# First render gets longer timeout (Chrome headless download)
timeout = 120000 if is_first_render else 60000
```

Phase 16-02 Task 에서 `remotion_renderer.__init__` 에 **warm-up probe** 추가 제안:
```python
subprocess.run(["npx", "remotion", "--version"], timeout=180, ...)
```

**Warning signs:** render stderr 에 "Downloading Chrome Headless Shell" 반복 출력.

### Pitfall 4: visual_spec.clipDesign[i].movement = null 을 자동 freeze 로 인식 못 함

**What goes wrong:** Designer 가 "이 clip 은 freeze (움직임 없음) 으로 의도" 를 null 로 표현했는데, renderer 가 이를 "누락" 으로 해석하여 round-robin 자동 movement 배정 → 원치 않는 pan/zoom 발생.

**Why it happens:** JSON null 과 missing key 구분 모호.

**How to avoid:** `remotion_render.py:843~869` sentinel `_NULL_FREEZE` 패턴 1:1 적용:
```python
design_movement = cd.get("movement")
_VALID_MOVEMENTS = {"zoom_in", "zoom_out", "pan_left", "pan_right"}
if design_movement in _VALID_MOVEMENTS:
    sc["movement"] = design_movement
else:
    # null 또는 invalid → 의도적 freeze
    sc["movement"] = "_NULL_FREEZE"  # sentinel
# build_shorts_props 끝에서 sentinel 제거 (Remotion Zod 가 거부하므로)
for rc in remotion_clips:
    if rc.get("movement") == "_NULL_FREEZE":
        rc.pop("movement", None)
```

**Warning signs:** 시청자가 정적 장면 (예: 증거 사진 고정 샷) 에서 원치 않는 pan 을 본다.

### Pitfall 5: `output_dir/sources/` 디렉토리 누락 → 캐릭터 오버레이 조용히 사라짐

**What goes wrong:** `output_dir/sources/character_detective.png` 와 `character_assistant.png` 가 없으면 `remotion_render.py:949~958` 이 조용히 skip. 결과 mp4 에 캐릭터 오버레이 없음. GATE 는 PASS (파일 존재 검사만).

**Why it happens:** shorts_naberal 은 per-episode sources/ 디렉토리를 `video-sourcer` 가 채우는 설계. 우리는 asset-sourcer 에게 이 책임을 이관해야 함.

**How to avoid:** Phase 16-04 Task 에 **asset-sourcer 출력에 sources/ directory manifest 필수** 추가:
```json
{
  "sources_manifest": {
    "character_detective": "output/<episode>/sources/character_detective.png",
    "character_assistant": "output/<episode>/sources/character_assistant.png",
    "intro_signature": "output/<episode>/sources/intro_signature.mp4",
    "outro_signature": "output/<episode>/sources/outro_signature.mp4",
    "scene_sources_count": 13  // ≥5 강제
  }
}
```

Quality gate 로 `len(sources_manifest) >= 9` (캐릭터 2 + 인트로 1 + 아웃로 1 + 장면 ≥ 5) 강제.

**Warning signs:** 최종 mp4 검증에서 TopBar 는 존재하나 좌/우 원형 캐릭터 이미지 없음. Remotion public/<job_id>/ 에 character_*.png 파일 없음.

### Pitfall 6: Zod schema 검증 실패 (shortsVideoSchema)

**What goes wrong:** `npx remotion render` 가 Zod 에러로 즉시 실패. 에러 메시지는 TypeScript 스택 트레이스로 Python 측에서 해석 어려움.

**Why it happens:** props 필드 타입 불일치 (예: `durationInFrames` 가 float, `subtitles[].highlightIndex` 가 string).

**How to avoid:** `build_shorts_props` 끝의 `validate_shorts_props` 사전 체크 **복사 필수** (`remotion_render.py:255~290`):
- audioSrc: non-empty str
- titleLine1: non-empty str
- channelName: non-empty str
- durationInFrames: positive int (float 금지)
- subtitles: list (empty 허용)

**Warning signs:** render stderr 에 "ZodError" + "Expected number, received string at 'durationInFrames'".

### Pitfall 7: 영상 길이 < 60s (session #31 재발)

**What goes wrong:** Script 가 짧게 생성 (예: 9 문장) → TTS 12s 출력 → 영상 13s → production baseline (≥60s) 미달.

**Why it happens:** scripter 의 `length_target` 이 240자 정도로 나올 수 있음 (hook + body 1-2 + outro). blueprint 의 `scripter_contract.length_target: 620` + `duration_target_sec: "90-130"` 을 강제하지 않았음.

**How to avoid:** scripter output validation 에 `duration_sec ≥ 50` + `section count ≥ 4` 가드. 또한 incidents.md §2 "단편 50~60초 / 시리즈편 90~120초 / 상한 120초" 를 scripter 의 `<mandatory_reads>` 에 포함 (Phase 16-01 에서 채널바이블 박제 시 자동 충족).

**Warning signs:** script.json 의 duration_sec < 50 — 기존 GATE 에서 통과되는 상태.

---

## Code Examples

검증된 패턴, 모든 인용은 `.preserved/harvested/` 또는 shorts_naberal 읽기 전용 경로.

### Example 1: Remotion CLI 호출 (Python subprocess)

```python
# Source: .preserved/harvested/video_pipeline_raw/remotion_render.py:984~1023
entry_point = os.path.join(project_root, "remotion", "src", "index.ts").replace("\\", "/")
output_path = os.path.abspath(os.path.join(output_dir, "final.mp4")).replace("\\", "/")
props_path_safe = os.path.abspath(props_path).replace("\\", "/")

cmd = [
    "npx", "remotion", "render",
    entry_point,
    "ShortsVideo",
    output_path,
    f"--props={props_path_safe}",
    "--codec=h264",
    f"--fps=30",
    "--width=1080",
    "--height=1920",
]

# Windows에서 npx는 npx.cmd이므로 shell=True 필요
use_shell = sys.platform == "win32"

result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    timeout=600,  # 10분 (커스텀 전환 효과 렌더 시 추가 시간 필요)
    cwd=os.path.join(project_root, "remotion"),
    shell=use_shell,
)

if result.returncode != 0:
    stderr = result.stderr[-1000:] if result.stderr else "no stderr"
    raise RuntimeError(f"Remotion render failed (exit {result.returncode}): {stderr}")
```

**Task action reference:** Phase 16-02 Task "remotion_renderer.py 작성" — 이 블록을 `RemotionRenderer.render()` 내부에 1:1 복사.

### Example 2: ShortsVideoProps 빌드 (visual_spec + script + assets 병합)

```python
# Source: .preserved/harvested/video_pipeline_raw/remotion_render.py:501~773 (build_shorts_props)
# 핵심 필드 추출 (실제 코드는 270 줄, 아래는 계약 요약)
props = {
    "audioSrc": assets.get("audioSrc", ""),
    "titleLine1": title_line1,              # blueprint.title_display.line1 우선
    "titleLine2": title_line2,              # 없으면 heuristic split
    "titleKeywords": [                      # blueprint.title_display.accent_words 매칭
        {"text": word, "color": accent_color}
        for word in accent_words if word in full_title
    ],
    "accentColor": accent_color,            # preset.defaultAccent fallback
    "channelName": preset["channelName"],   # config/channels.yaml
    "hashtags": preset["hashtags"],
    "subtitles": subtitles_cues,            # subtitles_remotion.json 로드
    "durationInFrames": int(audio_duration * fps),  # ffprobe 기반
    "clips": remotion_clips,                # visual_spec.clipDesign[] 또는 section_timing 기반
    "fontFamily": preset.get("fontFamily"), # "BlackHanSans" (incidents)
    "subtitlePosition": preset.get("subtitlePosition"),  # 0.8 (incidents 하단)
    "subtitleHighlightColor": preset.get("subtitleHighlightColor"),  # "#FFFFFF"
    "subtitleFontSize": preset.get("subtitleFontSize"),  # 68
    "transitionType": transitions[title_hash % len(transitions)],  # round-robin
    # BGM (optional, ducking handled in ShortsVideo.tsx)
    "bgmSrc": assets.get("bgmSrc"),
    "bgmVolume": assets.get("bgmVolume", 0.2),
    # Series badge
    "seriesPart": script.get("series", {}).get("part"),
    "seriesTotal": script.get("series", {}).get("total"),
    # Character avatars (main flow injects these after build)
    # "characterLeftSrc": f"{job_id}/character_left.png",
    # "characterRightSrc": f"{job_id}/character_right.png",
}

# Pre-validate (Zod 호환) — validate_shorts_props() 사전 검사
assert isinstance(props["audioSrc"], str) and props["audioSrc"]
assert isinstance(props["titleLine1"], str) and props["titleLine1"]
assert isinstance(props["durationInFrames"], int) and props["durationInFrames"] > 0
assert isinstance(props["subtitles"], list)
```

**Task action reference:** Phase 16-02 Task "build_shorts_props 포팅" — 원본 270 줄 그대로 복사, 우리 `visual_spec_path` 인자 주입 로직 (`remotion_render.py:833~869`) 도 함께 포함.

### Example 3: scene-manifest.json v4 샘플

```json
// Source: .preserved/harvested/baseline_specs_raw/zodiac-killer/scene-manifest.json (full file, 197 lines)
{
  "version": "v4",
  "channel": "incidents",
  "category": "crime",
  "topic": "조디악 킬러",
  "total_clips": 15,
  "clips": [
    {
      "index": 0,
      "section_type": "intro",
      "narration_sentence": "[인트로 시그니처]",
      "duration_s": 3,
      "source": {
        "type": "signature",
        "local_path": "sources/intro_signature.mp4",
        "provider": "veo_reuse"
      }
    },
    {
      "index": 1,
      "section_type": "hook",
      "narration_sentence": "이 편지에는 63개의 기호로 된 암호가 있었습니다.",
      "duration_s": 4,
      "source": {
        "type": "image",
        "local_path": "sources/z340_cipher_original.jpg",
        "provider": "serper",
        "description": "Z340 암호문 원본 — 63개 기호로 된 실제 암호문"
      }
    }
    // ... 13 more clips ...
  ],
  "source_stats": {
    "total": 16,
    "real_image": 13,
    "signature": 2,
    "unique_sources": 14,
    "real_ratio": 0.81
  }
}
```

**Key fields:**
- `source.provider ∈ {veo_reuse, serper, gpt_image2, kling, nano_banana}` — `veo_reuse` 는 기존 자산 재사용 명시적 표기.
- `source.type ∈ {video, image, signature, remotion}` — Remotion 은 `ShortsVideo` 메인 합성에서는 사용 안 함 (그래픽 카드 composition 용, 16:9 long-form 전용 성격).
- `source_stats.real_ratio ≥ 0.75` — Phase 16-04 검증 기준.

**Task action reference:** Phase 16-04 Task "scene-manifest v4 스키마 강제" — 이 샘플을 `.planning/phases/16-.../schemas/scene-manifest.v4.schema.json` 으로 추출하여 Pydantic 또는 jsonschema 로 검증.

### Example 4: word_subtitle.py CLI 호출 (subtitle-producer 내부)

```python
# Source: .preserved/harvested/audio_pipeline_raw/word_subtitle.py:1624~1697
# subtitle-producer 가 wrapping 할 내부 호출
cmd = [
    "python", "scripts/orchestrator/subtitle/word_subtitle.py",
    "--audio", str(narration_mp3_path),
    "--output", str(subtitles_srt_path),  # 부수적으로 .ass + .json 동일 디렉토리 생성
    "--max-chars", "8",
    "--model", "large-v3",                 # 한국어 CER 최적
    "--script", str(script_json_path),     # Whisper 교정용 (공백/숫자 수정)
    "--language", "ko",                    # 일본: "ja" (후일 incidents-jp Phase)
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
# Output: subtitles.srt + subtitles.ass + subtitles_remotion.json (3종)
```

**Task action reference:** Phase 16-03 Task "subtitle-producer AGENT.md 작성" — `<outputs>` 섹션에 3종 산출 명시, `<command>` 에 위 subprocess 호출 기재.

### Example 5: 캐릭터 오버레이 파일 조달 + 주입 분리 책임

```python
# Source: .preserved/harvested/video_pipeline_raw/remotion_render.py:942~976
# 책임 분할: asset-sourcer 가 파일 배치, remotion_renderer 가 props 주입

# [asset-sourcer 영역] — Phase 16-04 출력
# output/<episode>/sources/character_detective.png
# output/<episode>/sources/character_assistant.png
# (gpt-image-2 high tier 생성 또는 이전 에피소드 재사용)

# [remotion_renderer 영역] — Phase 16-02 구현
job_id = os.path.basename(os.path.normpath(output_dir))
public_char_dir = os.path.join(project_root, "remotion", "public", job_id)
char_left_path = os.path.join(output_dir, "sources", "character_assistant.png")
char_right_path = os.path.join(output_dir, "sources", "character_detective.png")
_char_left_prop = None
_char_right_prop = None
if os.path.exists(char_left_path):
    os.makedirs(public_char_dir, exist_ok=True)
    shutil.copy2(char_left_path, os.path.join(public_char_dir, "character_left.png"))
    _char_left_prop = f"{job_id}/character_left.png"
if os.path.exists(char_right_path):
    os.makedirs(public_char_dir, exist_ok=True)
    shutil.copy2(char_right_path, os.path.join(public_char_dir, "character_right.png"))
    _char_right_prop = f"{job_id}/character_right.png"

# Inject into props (after build_shorts_props)
if _char_left_prop:
    props["characterLeftSrc"] = _char_left_prop
if _char_right_prop:
    props["characterRightSrc"] = _char_right_prop
```

**Key insight:** 왼쪽 = 조수 (Watson/Guri, `character_assistant.png`), 오른쪽 = 탐정 (Morgan, `character_detective.png`). 단순 문자열 치환 아닌 **의미 고정 매핑**. `visual_spec.characterLeftSrc` / `characterRightSrc` 도 동일 의미 — asset-sourcer 는 이 파일명을 한국 채널에서 절대 변경하지 말아야 함.

---

## State of the Art

| Old Approach (우리 세션 #31 상태) | Current Approach (shorts_naberal 채택) | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ffmpeg concat + audio overlay | Remotion ShortsVideo composition (React) | 세션 #31→#32 (2026-04-21→22) | 합성 품질 근본적 개선 (레이어 1개 → 5개: TopBar + 본편 + 자막 + BottomBar + character overlay). 모든 baseline 6편이 Remotion. |
| I2V primary (Kling 으로 모든 씬) | Real image first, I2V supplementary (≤2 scenes) | incidents.md §9 + `feedback_veo_supplementary_only` | 비용 감소 ~80% + 실화 신뢰도 향상. Kling 씬은 "재현 영상 (cinematic recreation)" 라벨 명시. |
| T2V (shorts_naberal 초기 실험) | **I2V only, Anchor Frame 강제** | NotebookLM T1 + 우리 금기 #4 | I2V 품질 상한이 anchor 이미지 품질에 종속 → gpt-image-2 high tier. |
| segment-level 자막 (1~2초 단위) | **Word-level 자막 + highlight** (150~400ms per word, 현 단어 색상 전환) | 세션 37 기타큐슈 Part 1 이후 `subtitle_generate.py` → `word_subtitle.py` 전환 | 시청유지율 핵심 요인 (short attention span). |
| 자막 burn-in via ffmpeg drawtext | Remotion 내 React 렌더 (프레임 단위 state) | Remotion 4.x 도입 후 | 애니메이션/highlight 정밀 제어. libass 미사용. |
| 자동 round-robin movement 배정 | `visual_spec.clipDesign[]` single source of truth | FAIL-DES-008 근본 방지 (`remotion_render.py:833~869` 주석) | Designer 의도 보전. freeze 라는 의도도 `_NULL_FREEZE` sentinel 로 표현 가능. |
| ASS 파일을 Remotion 이 읽음 (잘못된 가정) | `subtitles_remotion.json` cue 배열을 props 로 전달. ASS 는 외부 용 | `shorts-designer/SKILL.md:131` "ASS `{\c&H}` 색상 태그 아님" 명시 | Remotion 이 single source. ASS 는 보존/편집자 참고용. |
| Pretendard 폰트 | Google Fonts (BlackHanSans/DoHyeon/NotoSansKR) | `shorts-designer/SKILL.md:133` "Pretendard 사용 금지" | 라이선스 + 한글 글리프 완성도. |

**Deprecated / outdated (우리 측에서 버려야 할 가정):**
- **우리 REQUIREMENTS.md 이전 버전이 ffmpeg assembler 를 primary 로 전제** — Phase 16 에서 Remotion primary 로 reorder 필요. ffmpeg 은 fallback 유지.
- **`ins-subtitle-alignment` AGENT.md description 의 "WhisperX + kresnik/wav2vec2-large-xlsr-korean"** — production 실제 구현은 faster-whisper large-v3. Phase 16-03 에서 inspector description 정정 필요 (word-level 정렬 검사 기능 자체는 유지).
- **visual_spec 생성 주체가 결정 안 된 상태** — shorts-designer 역할이 asset-sourcer 에 흡수됨으로 공식 결정 (Phase 16-04).

---

## Open Questions (Plan-Phase 결정 사항)

1. **32 에이전트 상한 vs Producer 14 → 15 증가**
   - What we know: `ins-subtitle-alignment` 가 "상류 = subtitle-producer" 를 명시하지만 실제 producer 없음. 신규 producer 추가 시 Producer 14 → 15, 총 32 → 33.
   - What's unclear: CLAUDE.md 금기 #9 "32 에이전트 초과" 는 "Anthropic sweet spot × 6배" 근거. 33 이 정확한 위반인지, sweet spot 논리상 허용되는지.
   - Recommendation: Phase 16-03 Plan 에서 대표님 결단 요청. **대안 1 (권장)**: 33 허용 + 근거 "이미 inspector 가 전제한 빈 슬롯 채움". **대안 2**: 기존 producer (예: `asset-sourcer`) 에 자막 생성 책임 추가 — 그러나 이는 "음향+비주얼+자막" 책임 과중 (Single Responsibility 위반).

2. **channel-incidents-jp 스킬 포팅 범위**
   - What we know: `.preserved/harvested/skills_raw/channel-incidents-jp/SKILL.md` 존재. Phase 16 fixed decision 은 한국 채널만.
   - What's unclear: 일본어 fontFamily (`Noto Sans JP`), 일본 TTS, ja_subtitle.py 파이프의 도입 시점.
   - Recommendation: Phase 16 OUT OF SCOPE. Phase 17 또는 별도 Phase 에서 multilingual 통합.

3. **`shorts-designer` 전체 포팅 vs asset-sourcer 확장**
   - What we know: shorts_naberal 의 designer 는 별도 에이전트. 우리는 32 상한 + asset-sourcer 가 visuals 산출 중이므로 확장으로 해결 가능.
   - What's unclear: visual_spec 에 들어가는 일부 디자인 메타 (예: `titleTagline: "범죄수첩"`, category label) 가 blueprint 에서 오는지 channel preset 에서 오는지.
   - Recommendation: Phase 16-04 Plan Task "channel preset (config/channels.yaml) 신설" 에서 정립. shorts_naberal 의 `config/channels.yaml + channel_registry.py` 구조를 1:1 포팅.

4. **remotion/ 디렉토리의 git 관리**
   - What we know: `remotion/node_modules/` 는 gitignore 필수. `remotion/public/bgm/` (음악 파일) 는 git 포함 (기존 패턴).
   - What's unclear: `remotion/src/` 를 git 커밋 vs LFS. TSX 텍스트만이라 일반 commit 으로 충분할 것.
   - Recommendation: 일반 git commit. LFS 미적용.

5. **테스트 전략 (regression 986 PASS 유지)**
   - What we know: `tests/phase16/` 필요. Remotion 렌더러는 unit test 하기 어려움 (node subprocess + Chrome).
   - What's unclear: CI 환경에서 실제 npx remotion render 실행 vs mock.
   - Recommendation: Phase 16-02 Plan Task 에서 3단계:
     - unit: `build_shorts_props` 순수 함수 (50 케이스)
     - integration mock: subprocess 모킹 (render 호출 여부, cmd args 검증)
     - smoke (매뉴얼 또는 조건부 CI): real render on 10초 샘플 프로젝트

---

## Environment Availability

> 이 Phase 는 외부 tool 의존성 증가가 큽니다. 아래 전수 probe 결과:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Remotion 4.x | ✓ (시스템 기본) | ≥16.0.0 필요 — 현재 상태 probe 필요 | ffmpeg_assembler |
| npm | Remotion deps | ✓ | 수반됨 | — |
| npx | remotion CLI | ✓ | 수반됨 | — |
| Chrome Headless Shell | Remotion render | 자동 (`npx remotion render` 호출 시 수동 다운 ~200MB) | Remotion 관리 | — |
| ffmpeg | audio duration probe + fallback 합성 | ✓ (기존 ffmpeg_assembler 전제) | 시스템 PATH | — |
| ffprobe | duration 측정 | ✓ (ffmpeg 번들) | — | — |
| Python 3.11+ | faster-whisper | ✓ (기존) | 3.11+ | — |
| CUDA 12.x + cuDNN | faster-whisper GPU | 선택 | — | CPU fallback (`word_subtitle.py:1341~1348` 자동 전환) |
| faster-whisper | 자막 word-level | ✗ (신규 설치) | — | 없음 (blocking) |
| Kling 2.6 Pro API | I2V 보조용 | ✓ (Phase 15 wired) | — | Runway Gen-3 |
| gpt-image-2 API | sources 이미지 생성 | ✓ (Phase 15 wired) | — | Nano Banana |
| Serper API | 실제 자료 검색 | ✗ (잘 모름 — 확인 필요) | — | gpt-image-2 illustration |
| Typecast API | Morgan + Guri 보이스 | ✓ (Phase 15 wired) | — | ElevenLabs |

**Missing dependencies with no fallback:**
- `faster-whisper` (+ large-v3 모델 파일 ~3GB 최초 다운) — Phase 16-03 Plan Task 에 설치 + 모델 프리다운 step 필수.

**Missing dependencies with fallback:**
- CUDA: cuDNN 미설치 시 CPU 로 자동 fallback. 60s 오디오 기준 CPU transcribe 는 ~3~5 분 (GPU 는 ~20s). 기능상 동작하지만 렌더 시간 지연.
- Serper API: 자료사진 부재 시 gpt-image-2 illustration 으로 대체 (단 real_ratio 하락).

**Probe commands** (Phase 16-02 Task 0 에 포함):
```bash
node --version            # ≥ 16
npx remotion --version 2>&1 || echo "remotion not installed yet"
ffmpeg -version | head -1
ffprobe -version | head -1
python -c "from faster_whisper import WhisperModel; print('OK')" 2>&1 || echo "faster-whisper not installed"
```

---

## Validation Architecture

> `.planning/config.json` 확인 불가 — nyquist_validation 기본값(enabled) 으로 진행.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (기존) + vitest (Remotion React, 신규) |
| Config file | `pyproject.toml` (python) + `remotion/vitest.config.ts` (신규 Phase 16-02) |
| Quick run command | `pytest tests/phase16/ -x` |
| Full suite command | `pytest tests/ && (cd remotion && npm test)` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-PROD-INT-01 | ASSEMBLY renderer priority order (remotion > shotstack > ffmpeg) | unit | `pytest tests/phase16/test_assembly_gate_branching.py -x` | Wave 0 |
| REQ-PROD-INT-02 | remotion_renderer.render() API parity with ffmpeg_assembler | unit | `pytest tests/phase16/test_remotion_renderer_api.py -x` | Wave 0 |
| REQ-PROD-INT-03 | build_shorts_props 출력 Zod 통과 | unit | `pytest tests/phase16/test_shorts_props_build.py -x` | Wave 0 |
| REQ-PROD-INT-03 | validate_shorts_props 의 필드 검증 (audioSrc non-empty, durationInFrames int) | unit | `pytest tests/phase16/test_shorts_props_validate.py -x` | Wave 0 |
| REQ-PROD-INT-04 | subtitle-producer AGENT.md frontmatter 유효 + 산출 3종 (srt/ass/json) | unit + smoke | `pytest tests/phase16/test_subtitle_producer.py -x` + `python scripts/orchestrator/subtitle/word_subtitle.py --audio sample.mp3 --output /tmp/out.srt --script sample.json` | Wave 0 |
| REQ-PROD-INT-05 | ins-subtitle-alignment description drift regression | unit | `pytest tests/phase16/test_ins_subtitle_alignment_spec.py -x` | Wave 0 |
| REQ-PROD-INT-06 | asset-sourcer 확장 출력에 visual_spec 필드 포함 | unit | `pytest tests/phase16/test_asset_sourcer_visual_spec.py -x` | Wave 0 |
| REQ-PROD-INT-07 | 캐릭터 파일 경로 계약 (sources/character_detective.png + assistant.png) | integration | `pytest tests/phase16/test_character_overlay_injection.py -x` | Wave 0 |
| REQ-PROD-INT-08 | 인트로/아웃로 시그니처 기존 자산 참조 (Veo 신규 호출 0회) | integration + policy | `pytest tests/phase16/test_signature_reuse_no_veo_call.py -x` | Wave 0 |
| REQ-PROD-INT-09 | scene-manifest v4 스키마 준수 | unit | `pytest tests/phase16/test_scene_manifest_v4.py -x` | Wave 0 |
| REQ-PROD-INT-10 | movement=null → `_NULL_FREEZE` sentinel → pop 전 Zod 통과 | unit | `pytest tests/phase16/test_null_freeze_sentinel.py -x` | Wave 0 |
| REQ-PROD-INT-11 | project_channel_bible_incidents_v1 메모리 존재 + 필수 섹션 | unit (doc check) | `pytest tests/phase16/test_channel_bible_memory.py -x` | Wave 0 |
| REQ-PROD-INT-12 | feedback_* 메모리 12+ 박제 또는 참조 존재 | unit (doc check) | `pytest tests/phase16/test_feedback_memories_mapped.py -x` | Wave 0 |
| REQ-PROD-INT-13 | ffprobe 기반 post-render baseline 검증 | smoke | `pytest tests/phase16/test_post_render_baseline.py -x` (샘플 mp4 필요) | Wave 0 |
| REQ-PROD-INT-14 | Narration Drives Timing — ffprobe duration == durationInFrames/30 (±1s) | integration | `pytest tests/phase16/test_narration_drives_timing.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/phase16/ -x` (신규 테스트만)
- **Per wave merge:** `pytest tests/ -x && (cd remotion && npm test)` (986 기존 + 신규 20 + remotion unit)
- **Phase gate (`/gsd:verify-work`):** full suite green + 샘플 영상 1편 production baseline 통과 증명 (`outputs/phase16_smoke_run.mp4` ffprobe)

### Wave 0 Gaps

- [ ] `tests/phase16/` 디렉토리 — 신규 (현재 없음)
- [ ] `tests/phase16/conftest.py` — 공유 fixtures (sample audio, sample script.json, mock subprocess.run)
- [ ] `tests/phase16/fixtures/` — zodiac-killer baseline 을 tests data 로 일부 복사 (read-only 원칙 유지 위해 `shutil.copy2` 로 fixture 임시 디렉토리로만)
- [ ] `remotion/vitest.config.ts` + `remotion/src/__tests__/` — Phase 16-02 에서 신규
- [ ] Framework install: `pip install faster-whisper` + `cd remotion && npm install`

---

## Sources

### Primary (HIGH confidence — 직접 읽은 파일)

**shorts_naberal production code (`.preserved/harvested/`, read-only)**
- `video_pipeline_raw/remotion_render.py` (1162 줄) — Python ↔ Remotion bridge. §Pattern 2, §Example 1-2-5, §Pitfall 3-4-5-6.
- `video_pipeline_raw/_build_render_props_v2.py` (150+ 줄) — section_timing 기반 clip duration 계산.
- `video_pipeline_raw/generate_intro_signature.py` (80+ 줄) — Veo 호출 경로 (**참조 금지, 우회 필수**).
- `audio_pipeline_raw/word_subtitle.py` (1697 줄) — faster-whisper word-level 자막 + 3종 산출. §Don't Hand-Roll.
- `audio_pipeline_raw/subtitle_generate.py:1~18` — `word_subtitle.py` deprecation 고지.
- `remotion_src_raw/Root.tsx` (313 줄) — Composition registry.
- `remotion_src_raw/compositions/ShortsVideo.tsx` (744+ 줄) — 메인 합성 로직. §Pattern 1, §Example 5.
- `theme_bible_raw/incidents.md` (70+ 줄) — 사건기록부 v1.0 SSOT. §User Constraints.
- `skills_raw/shorts-pipeline/SKILL.md` — 6-Stage 파이프라인 + Narration Drives Timing. §Pattern 4.
- `skills_raw/shorts-designer/SKILL.md` — visual_spec 책임 주체 + Pretendard 금지. §Q2, §Anti-Patterns.
- `baseline_specs_raw/zodiac-killer/visual_spec.json` (138 줄) — props 샘플. §Q2.
- `baseline_specs_raw/zodiac-killer/subtitles_remotion.json` (full) — cue 배열 샘플. §Q3.
- `baseline_specs_raw/zodiac-killer/subtitles_remotion.ass` (first 80 줄) — ASS karaoke 포맷. §Q3.
- `baseline_specs_raw/zodiac-killer/scene-manifest.json` (197 줄) — v4 스키마. §Example 3.
- `baseline_specs_raw/zodiac-killer/blueprint.json` (145 줄) — scripter_contract + voice_hint + source_strategy. §Q2.

**shorts_naberal remotion workspace (direct read)**
- `C:/Users/PC/Desktop/shorts_naberal/remotion/package.json` — Remotion 4.x 의존성 버전 확정. §Standard Stack.

**우리 측 현 코드 (shorts 프로젝트)**
- `scripts/orchestrator/shorts_pipeline.py` (841 줄) — `_run_assembly` 분기 포인트. §Pattern 1.
- `scripts/orchestrator/api/ffmpeg_assembler.py` (313 줄) — API signature 참고. §Pattern 2.
- `scripts/orchestrator/gate_guard.py` (216 줄).
- `.claude/agents/producers/asset-sourcer/AGENT.md` — 확장 대상. §Q2.
- `.claude/agents/producers/scripter/AGENT.md` — hand-off 파트너.
- `.claude/agents/producers/assembler/AGENT.md` — 스펙 역할 유지 (렌더 실행은 renderer).
- `.claude/agents/producers/thumbnail-designer/AGENT.md` — 캐릭터 오버레이와 **무관** 확인. §Q4.
- `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md` — description 정정 대상. §Q3.
- `.claude/memory/reference_production_gap_map.md` — 11 누락 컴포넌트.
- `.claude/memory/reference_harvested_full_index.md` — 9 폴더 160 파일 인덱스.
- `.planning/ROADMAP.md:462~508` — Phase 16 정의.

### Secondary (MEDIUM confidence — 외부 공식 문서)

- [Remotion CLI render docs](https://www.remotion.dev/docs/cli/render) — `--width`, `--height`, `--fps`, `--props` 플래그 검증.
- [Remotion Chrome Headless Shell](https://www.remotion.dev/docs/miscellaneous/chrome-headless-shell) — Windows x64 자동 다운 확정.
- [Remotion Upgrading](https://www.remotion.dev/docs/upgrading) — Node ≥16.0.0 강제.
- [Remotion Captions](https://www.remotion.dev/docs/captions/) — Whisper 추천, parse-srt 예시. ASS 네이티브 지원 없음 확정.
- [faster-whisper PyPI](https://pypi.org/project/faster-whisper/) + [SYSTRAN/faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper) — word_timestamps=True API 확인.
- [OpenAI whisper-large-v3 Discussion #1762](https://github.com/openai/whisper/discussions/1762) — Korean CER 개선, large-v2 대비 10-20% error reduction.
- [libass Wiki ASS Format Guide](https://github.com/libass/libass/wiki/ASS-File-Format-Guide) — \k karaoke 태그 구조 확인. Remotion 네이티브 파싱 부재 확정.

### Tertiary (LOW confidence — 확인 필요)

- shorts_naberal 세션 번호 (37, 75 등) 인용은 내부 주석 기반. 정확한 타임라인 / 당시 결정 맥락은 우리가 직접 접근 불가.
- 실제 Serper API 키 가용성 (`.env` 확인 미수행) — Phase 16-04 Plan 작성 전 대표님 확인 필요.
- `output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` 파일 실존 여부 — `.preserved/harvested/video_pipeline_raw/` 에 스크립트는 있으나 실제 mp4 파일은 harvest 에 포함되지 않았을 수 있음. Phase 16-03 Task 0 에 "shorts_naberal output/_shared/signatures/ 디렉토리 실존 체크 + 자산 복사" 명시적 포함 필요.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — shorts_naberal `remotion/package.json` 원본 읽기 + Remotion 공식 docs 확인.
- Architecture patterns: **HIGH** — harvested `remotion_render.py` 1162 줄 직접 분석 + 우리 `shorts_pipeline.py` 분기점 확인.
- Pitfalls: **HIGH** — 6/7 항목이 harvested 주석 (FAIL-DES-008, 세션 37, FAIL-SCR-016 등) 내 명시.
- Q1~Q4: **HIGH** — 4 답 모두 file:line 증거 첨부.
- Standard stack **versions**: MEDIUM — 최신 버전 확인은 `npm view remotion version` 실행 전제 (Phase 16-02 Task 0 에서 확정).
- Environment availability **probe 결과**: LOW — 실제 시스템 probe 미실행 (리서처는 파일만 읽음). Phase 16-02 Task 0 에서 실제 실행 필수.

**Research date:** 2026-04-22
**Valid until:**
- 2026-05-22 (Remotion 4.x 안정적 — major 버전 변경 없을 것)
- 즉시 만료 if: 대표님이 "일본 채널도 이번 Phase 포함" 지시 / 신규 에이전트 금지 결단 / Veo 재개 허가 (후자 2개는 현재 locked)

---

# 4 Research Questions — 답변

## Q1. Remotion 합성 구조 (11 Cards + 7 transitions) → 우리 GATE 매핑

### 답변 요약

**우리 ASSEMBLY gate (GATE 9) 한 지점만 수정합니다.** shorts_naberal 의 "11 Cards" 는 오해 — 실제로는 **1 메인 composition (`ShortsVideo.tsx`) + 10 long-form/graphic card sub-compositions** 구성입니다. 쇼츠 본편은 `ShortsVideo.tsx` 1개만 사용하며, 이 composition 내부의 `<TransitionSeries>` 가 `clips[]` 를 받아 7 transition presentation 중 선택합니다. 따라서 우리가 이식해야 할 composition 은 `ShortsVideo.tsx` **1 개 + 그 의존성 5 개 (BracketCaption, crime 서브컴포넌트 3 개, 7 transition presentation)** 뿐입니다.

### 매핑 테이블

| shorts_naberal Composition/Component | Our GATE / 모듈 | Role in Phase 16 |
|--------------------------------------|-----------------|-------------------|
| `compositions/ShortsVideo.tsx` (메인) | GATE 9 ASSEMBLY — `remotion_renderer.py` 가 호출 | **필수 이식** (1:1 복사) |
| `compositions/IntroCard.tsx` | **사용 안 함** (intro 는 인트로 시그니처 mp4 클립으로 해결) | 이식 불필요 |
| `compositions/OutroCard.tsx` | **사용 안 함** (outro 는 아웃로 시그니처 mp4) | 이식 불필요 |
| `compositions/TitleCard.tsx` 외 7 개 | **long-form 용** (LongformVideo composition 에서 사용) | Phase 16 OUT OF SCOPE |
| `components/BracketCaption.tsx` | ShortsVideo 가 직접 import — 이식 필수 | 이식 필수 |
| `components/crime/{ContextGraphicScene, ImpactCutScene, SpeakerSubtitle}.tsx` | ShortsVideo `clip.sceneType` 분기에서 사용 — 이식 필수 | 이식 필수 |
| `components/crime/{IconExplainer, TimelineCard}.tsx` | ShortsVideo 미사용 (incidents 채널 특화 미확인) | 이식 필수 (index.ts 에서 export 되므로) |
| `lib/transitions/presentations/{glitch, rgbSplit, zoomBlur, lightLeak, clockWipe, pixelate, checkerboard}.tsx` | ShortsVideo 직접 import — 이식 필수 | 이식 필수 |
| `lib/fonts.ts` | ShortsVideo 가 titleFont/subtitleFont/bodyFont + jp 변형 사용 | 이식 필수 |
| `lib/props-schema.ts` | Root.tsx 에서 카드 컴포지션 스키마 참조 (long-form 용) | Phase 16 에서는 사용 미미 — 우리 Root.tsx 는 단축 버전으로 작성 |

### 파일 경로 매핑

| shorts_naberal | 우리 프로젝트 (Phase 16 후) |
|---|---|
| `remotion/src/index.ts` | `remotion/src/index.ts` (신규) |
| `remotion/src/Root.tsx` | `remotion/src/Root.tsx` (신규, ShortsVideo Composition 하나만 등록) |
| `remotion/src/compositions/ShortsVideo.tsx` | `remotion/src/compositions/ShortsVideo.tsx` (1:1 복사) |
| `remotion/src/components/BracketCaption.tsx` | 동일 경로 복사 |
| `remotion/src/components/crime/*.tsx` | 동일 경로 복사 |
| `remotion/src/lib/fonts.ts` | 동일 경로 복사 |
| `remotion/src/lib/transitions/presentations/*.tsx` | 동일 경로 복사 |
| `scripts/video-pipeline/remotion_render.py` | `scripts/orchestrator/api/remotion_renderer.py` (미러) |

### 우리 13 GATE 영향도

| GATE | Phase 16 변경 | 변경 내용 |
|------|---------------|-----------|
| TREND / NICHE | 없음 | — |
| RESEARCH_NLM | 없음 (일본 NLM 2-노트북 제안은 Phase 17+) | — |
| BLUEPRINT | 미미 | blueprint.json 에 `title_display.{line1,line2,accent_words,accent_color}` + `scripter_contract` + `voice_hint` + `source_strategy` + `visual_highlights` 스키마 확장 (Phase 16-04) |
| SCRIPT / POLISH | 미미 | 채널바이블 `<mandatory_reads>` 에 incidents.md 추가 (Phase 16-01) |
| VOICE | 없음 | — |
| **ASSETS** | **중대** | asset-sourcer 확장: visual_spec.json + sources/ manifest + scene-manifest v4 (Phase 16-04) |
| **ASSEMBLY** | **중대** | remotion_renderer 1 순위 분기 + word_subtitle 호출 (Phase 16-02) |
| THUMBNAIL | 미미 | 캐릭터 오버레이는 ASSEMBLY 에서 처리 — thumbnail-designer 는 기존 role 유지 |
| METADATA / UPLOAD / MONITOR / COMPLETE | 없음 | — |

**Evidence:**
- `.preserved/harvested/remotion_src_raw/Root.tsx:17` — `import { ShortsVideo, shortsVideoSchema } from "./compositions/ShortsVideo";` (쇼츠는 1 composition 확정)
- `.preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx:13` — `import { TransitionSeries, linearTiming } from "@remotion/transitions";`
- `.preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx:549~651` — `<TransitionSeries>` 내부 7-way switch (`getTransitionConfig`).
- `.preserved/harvested/video_pipeline_raw/remotion_render.py:984~998` — subprocess 호출 시 composition ID = `"ShortsVideo"` 고정.
- `scripts/orchestrator/shorts_pipeline.py:515~562` — `_run_assembly` 분기 포인트.

---

## Q2. `visual_spec.json` 생성 주체 = scripter vs asset-sourcer vs assembler

### 답변 요약

**`asset-sourcer` 의 출력 스키마를 확장** 합니다. 신규 에이전트를 만들지 않습니다.

### 근거

1. **shorts_naberal 의 실제 구현**: `shorts-designer` 라는 **별도 에이전트** 가 visual_spec 을 생성 (`.preserved/harvested/skills_raw/shorts-designer/SKILL.md:2~11`).
2. **우리 쪽 책임 분할**: 우리에겐 `shorts-designer` 가 없음. 32 에이전트 상한 + 책임 최소 침해 관점에서 **asset-sourcer** 가 가장 자연스러운 흡수 대상:
   - `asset-sourcer` 는 이미 `visuals[]` (URL 기반 자료 사진) 과 `audio.bg_music_track` 을 산출. visual_spec 은 이 자산에 **디자인 메타 (색상/폰트/위치/transition)** 를 추가할 뿐.
   - shorts-designer 의 역할 (ShortsVideo props 스키마 매핑) 은 **자산 + 디자인 결정의 중간 layer** — asset-sourcer 가 자산을 만든 직후 이를 디자인 결정과 함께 묶어 출력하는 것이 자연스러움.
3. **`scripter` 제외 근거**: scripter 는 narrative/tone/duration 을 결정. visual 디자인 (색상/폰트/캐릭터 위치) 과는 직교. blueprint.json 의 `title_display.accent_words` 처럼 scripter 가 **준비는 하지만** visual_spec 필드 자체는 asset-sourcer 가 병합.
4. **`assembler` 제외 근거**: assembler 의 스펙 역할 (Phase 4) 은 **composition 명세 작성** — 실 렌더는 Phase 16-02 의 `remotion_renderer.py` 가 수행. assembler 가 visual_spec 까지 만들면 "디자인+조립 결정+합성 호출" 3가지 책임. Single Responsibility 위반.
5. **shorts_naberal 패턴 모방**: harvested `remotion_render.py:829~869` 가 `visual_spec.clipDesign[]` 을 **단일 진실** 로 사용 — "Designer 결정 보전" 원칙. 우리도 asset-sourcer 가 clipDesign 을 내면 renderer 가 자동 보전.

### asset-sourcer 확장 스키마 (output 에 visual_spec 필드 추가)

(§Architecture Patterns Pattern 3 참조 — 완전한 JSON 예시)

### Phase 16-04 Task 구조

1. asset-sourcer `AGENT.md` 업데이트 — `<outputs>` 에 `visual_spec` 섹션 추가, `<skills>` 에 `shorts-designer` 패턴 참조 명시.
2. `.claude/memory/project_channel_preset_incidents.md` 신규 — channel preset (`channelName`, `hashtags`, `fontFamily`, `subtitleFontSize`, `subtitleHighlightColor`, `transitions[]`) 박제.
3. `scripts/orchestrator/api/visual_spec_builder.py` 신규 — blueprint + script + channel preset + sources manifest → visual_spec.json 변환 함수. (이는 asset-sourcer 가 호출하는 헬퍼 — 에이전트 자체는 영화적 결정만, 계산은 함수에 위임.)
4. `tests/phase16/test_visual_spec_schema.py` — zodiac-killer baseline 과 구조 동등성 검증.

**Evidence:**
- `.preserved/harvested/skills_raw/shorts-designer/SKILL.md:110~125` — visual_spec.json 스키마 정의 (designer 담당).
- `.preserved/harvested/skills_raw/shorts-designer/SKILL.md:125` — "audioSrc, videoSrc, imageSrc, subtitles, durationInFrames 는 editor 가 설정" (다른 주체의 입력 필드).
- `.preserved/harvested/video_pipeline_raw/remotion_render.py:833~869` — `visual_spec_path` 로드 시 clipDesign 이 단일 진실.
- `.claude/agents/producers/asset-sourcer/AGENT.md:120~158` — 기존 `visuals[]` 출력. visual_spec 흡수의 자연 수용체.

---

## Q3. 단어단위 자막 → `ins-subtitle-alignment` 확장 vs 신규 producer

### 답변 요약

**신규 Producer `subtitle-producer` 를 추가** 합니다. `ins-subtitle-alignment` 는 검증 역할만 유지하되 description 을 "WhisperX → faster-whisper" 로 정정합니다.

### 근거

1. **GAN 분리 원칙 (RUB-02 + RUB-06)**: Inspector 는 검증만, Producer 는 생성만. Inspector 에 생성 로직 주입 시 "검증자가 자신을 검증" → collapse.
2. **이미 설계상 빈 슬롯**: `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md:12` 가 "상류 = **subtitle-producer**" 명시 — 현재 producer 없음. 즉 Phase 15 시점에 subtitle-producer 빈 슬롯이 이미 예약되어 있음.
3. **32 에이전트 상한**: 현재 Producer 14 + Inspector 17 + Supervisor 1 = 32. subtitle-producer 추가 시 Producer 15, 총 **33**. CLAUDE.md 금기 #9 는 "Anthropic sweet spot × 6배" 논리에서 나온 수치 (sweet spot ≈ 5, 6배 = 30, 여유 있게 32 상한). 33 은 이 상한에서 +1. **대표님 결단 필요** (Open Questions #1) 하지만 이미 inspector 가 전제한 빈 슬롯을 채우는 것이므로 "신규 에이전트 추가" 보다 "예약 채움" 에 가까움.
4. **shorts_naberal 의 subtitle 책임 분할**: `shorts-pipeline/SKILL.md:64` — "Stage 4 ASSETS (parallel): ... producers/subtitle → subtitles (faster-whisper)". 즉 shorts_naberal 은 **producers/subtitle** 을 별도 에이전트로 가짐. 우리 패턴 모방 시 자연스러움.
5. **asset-sourcer 흡수는 부적절**: asset-sourcer 는 이미 "audio BGM + visuals + visual_spec" 3 책임. + subtitle = 4 책임 — Single Responsibility 과중.
6. **scripter 흡수는 부적절**: scripter 는 **narration 텍스트** 를 생성. **narration audio** 와 **word-level alignment** 는 TTS 후에야 가능. GATE 순서상 scripter 는 VOICE 보다 앞에 위치, 자막은 VOICE 뒤 (audio 기반).

### subtitle-producer AGENT.md 스펙 요약

```yaml
---
name: subtitle-producer
description: faster-whisper large-v3 기반 word-level 자막 생성. narration.mp3 + script.json 받아 subtitles.srt + subtitles_remotion.ass + subtitles_remotion.json 3종 동시 생성. Korean word timestamp repair 포함 (clamp/merge/fallback). maxTurns=3. 트리거 키워드 subtitle-producer, word_subtitle, faster-whisper, 자막, 단어단위, WhisperModel, large-v3, SRT, ASS, subtitles_remotion. 일본어 (ja_subtitle.py) 는 Phase 17+.
version: 1.0
role: producer
category: support
maxTurns: 3
---
```

- **Input**: `producer_output` (VOICE gate narration.mp3 + script.json), `language` (ko|ja|en, 기본 ko), `max_chars_per_line` (기본 8).
- **Output**: `{"gate": "ASSETS", "subtitles_srt": "...", "subtitles_ass": "...", "subtitles_json": "...", "phrase_count": N, "coverage_percent": 96.3, "faster_whisper_model": "large-v3", "device": "cuda|cpu"}`
- **Script**: `scripts/orchestrator/subtitle/word_subtitle.py` (harvested 에서 포팅, 1697 줄, 수정 없이 복사 + `__main__` 진입).
- **Downstream**: `ins-subtitle-alignment` 가 subtitles_remotion.json cue 배열의 drift 검증 (≤150ms).
- **GATE 위치**: Stage 4 ASSETS 의 병렬 3-way 중 하나 (voice + visuals + subtitle — 우리 pipeline 은 VOICE / ASSETS 가 순차이지만 ASSETS 내부에서 asset-sourcer, subtitle-producer, thumbnail-designer 병렬 실행 가능).

### ins-subtitle-alignment 정정 (REQ-PROD-INT-05)

- **description 변경 (`version: 1.1` → `1.2`)**: "WhisperX + kresnik/wav2vec2-large-xlsr-korean" → "faster-whisper large-v3 기반 subtitle-producer 출력 검증"
- **MUST REMEMBER 섹션에 "상류 = subtitle-producer (Phase 16-03 추가)" 명시 유지.**
- **검증 로직 불변**: drift ±150ms, 자막 ≤25 chars/line, 1~4 words/line (CONTENT-06).
- **신규 검증 항목 (권장)**: `coverage_percent ≥ 95%` (subtitles 마지막 endMs / audio 총 길이 ≥ 0.95).

**Evidence:**
- `.preserved/harvested/skills_raw/shorts-pipeline/SKILL.md:64` — "producers/subtitle → subtitles (faster-whisper)" 병렬 3-way.
- `.claude/agents/inspectors/technical/ins-subtitle-alignment/AGENT.md:12` — "상류 = subtitle-producer".
- `.preserved/harvested/audio_pipeline_raw/word_subtitle.py:1478~1535` — CUDA → CPU fallback + word timestamp repair.
- `.preserved/harvested/audio_pipeline_raw/subtitle_generate.py:1~18` — word_subtitle 가 SRT+ASS+JSON 3종 통합 생성.

---

## Q4. 캐릭터 오버레이 (탐정 Morgan + 왓슨) → thumbnail-designer vs assembler vs 신규

### 답변 요약

**이 중 어느 것도 아님**. 캐릭터 오버레이는 **asset-sourcer (파일 조달) + remotion_renderer.py (props 주입) + ShortsVideo.tsx (실제 렌더)** 3 계층 분산 처리. 책임 분할상 신규 에이전트도 thumbnail-designer/assembler 확장도 불필요.

### 증거

**shorts_naberal 코드 (harvested):**

```python
# .preserved/harvested/video_pipeline_raw/remotion_render.py:942~976
# 1b. Copy character avatars to remotion/public/ if they exist
job_id = os.path.basename(os.path.normpath(output_dir))
public_char_dir = os.path.join(project_root, "remotion", "public", job_id)
char_left_path = os.path.join(output_dir, "sources", "character_assistant.png")
char_right_path = os.path.join(output_dir, "sources", "character_detective.png")
_char_left_prop = None
_char_right_prop = None
if os.path.exists(char_left_path):
    os.makedirs(public_char_dir, exist_ok=True)
    shutil.copy2(char_left_path, os.path.join(public_char_dir, "character_left.png"))
    _char_left_prop = f"{job_id}/character_left.png"
if os.path.exists(char_right_path):
    # ... 동일 ...
    _char_right_prop = f"{job_id}/character_right.png"

# 2b. Inject character avatar props (after build_shorts_props)
if _char_left_prop:
    props["characterLeftSrc"] = _char_left_prop
if _char_right_prop:
    props["characterRightSrc"] = _char_right_prop
```

즉 **character 파일이 `output_dir/sources/` 에 "있으면 사용, 없으면 skip"**. 렌더러는 파일 존재 체크만. **누가** 이 파일을 만드는지는 이 스크립트에 드러나 있지 않음 — 다른 모듈 (asset-sourcer 또는 video-sourcer) 의 책임.

**visual_spec.json (zodiac-killer)**:
```json
// .preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json:18~19
"characterLeftSrc": "zodiac-killer/character_assistant.png",
"characterRightSrc": "zodiac-killer/character_detective.png",
```

경로가 `<job_id>/character_*.png` — `remotion/public/<job_id>/` staticFile() 경로 컨벤션. visual_spec 에 기록된다는 것은 **Designer 결정 범위** 임을 시사.

**Remotion ShortsVideo.tsx:**
```tsx
// .preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx:406~430
{characterLeftSrc && (
  <div style={{
    width: 200, height: 200, borderRadius: "50%",
    border: `3px solid ${accentColor}`,
    // ... face crop transform
  }}>
    <Img src={staticFile(characterLeftSrc)} ... />
  </div>
)}

// ShortsVideo.tsx:488~502
{characterRightSrc && (
  <Img
    src={staticFile(characterRightSrc)}
    style={{ width: 200, height: 200, borderRadius: "50%", ... }}
  />
)}
```

즉 **렌더 자체는 React 컴포넌트가 처리**. characterLeftSrc 가 optional prop 이므로 없으면 조용히 skip.

### 책임 분할 (우리 측 결정)

| 단계 | 책임 주체 | 출력 |
|------|-----------|------|
| **캐릭터 파일 생성/조달** | **asset-sourcer** (확장, Phase 16-04) | `output/<episode>/sources/character_detective.png` + `character_assistant.png` |
| **파일 경로를 visual_spec 에 기록** | **asset-sourcer** (visual_spec 생성 시) | `visual_spec.characterLeftSrc = "<episode>/character_assistant.png"` |
| **파일을 remotion/public/ 에 복사 + props 주입** | **remotion_renderer.py** (Phase 16-02) | `props.characterLeftSrc` + `props.characterRightSrc` |
| **실제 렌더 (원형 크롭 + border + drop-shadow)** | **Remotion `ShortsVideo.tsx`** (Phase 16-02 이식) | final.mp4 의 TopBar 오버레이 |

### 왜 thumbnail-designer / assembler / 신규 에이전트가 아닌가

- **thumbnail-designer**: 썸네일은 **표지 이미지** — 영상 본편의 캐릭터 오버레이와 별개. 썸네일에는 보통 사건 현장 사진 + 자극적 텍스트 오버레이가 들어감. 탐정 캐릭터는 본편 TopBar 에만 등장. `.claude/agents/producers/thumbnail-designer/AGENT.md` 의 책임은 "text_overlay ≤14자 + hook_strength ≥60 + AF-5 방어" — 캐릭터와 무관.
- **assembler**: assembler 는 "composition 스펙" — 어떤 asset 을 어떤 순서로 쌓을지. **캐릭터 asset 존재** 를 전제할 뿐, 조달은 다른 에이전트. 우리 assembler AGENT.md (version 1.2) 는 이미 "voice-producer 오디오 + asset-sourcer I2V clip + thumbnail-designer 썸네일 스펙" 을 받는 구조. asset 내에 캐릭터 포함이 자연.
- **신규 `character-designer` 에이전트**: 32 상한 + 단일 책임 위반. 캐릭터 PNG 는 이미 gpt-image-2 (세션 간 재사용 가능) — 조달 과정이 asset-sourcer 의 다른 visual 조달과 동일 플로우.

### Phase 9.1 CharRegistry 와의 호환

- Phase 9.1 이 구축한 `CharRegistry` 는 "캐릭터 ID ↔ anchor 이미지 ↔ prompt 시드" 매핑. 이번에 필요한 `character_detective.png` + `character_assistant.png` 는 CharRegistry 의 "incidents 채널 primary duo" 엔트리로 등록 가능.
- 재사용: 에피소드마다 같은 캐릭터 이미지를 반복 조달하지 않고 `CharRegistry.get("incidents_detective_v1")` 로 캐시된 PNG 복사.
- Phase 16-04 Task 에 "CharRegistry 에 incidents 듀오 엔트리 추가" 포함.

### 좌/우 의미 고정 (절대 바꾸면 안 됨)

- `characterLeftSrc = assistant` (왓슨/Guri, 조수) — 파일명 고정 `character_assistant.png`.
- `characterRightSrc = detective` (Morgan, 탐정) — 파일명 고정 `character_detective.png`.
- shorts_naberal baseline 6편 모두 일관. incidents 채널 브랜드 consistency.
- 일본 채널 (Phase 17+) 도 동일 좌/우 규칙 유지, 파일 내용만 일본 캐릭터로 교체 (`character-incidents-jp` SKILL 확인 완료).

**Evidence:**
- `.preserved/harvested/video_pipeline_raw/remotion_render.py:942~976` — remotion_renderer 의 복사+주입 로직.
- `.preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json:18~19` — visual_spec 필드.
- `.preserved/harvested/remotion_src_raw/compositions/ShortsVideo.tsx:406~502` — 좌/우 렌더 분기 (왼쪽 = 조수 face zoom, 오른쪽 = 탐정 크기만 확대).
- `.preserved/harvested/baseline_specs_raw/zodiac-killer/scene-manifest.json:242~247` (roanoke-colony) — `sources/character_detective.png` + `sources/character_assistant.png` scene-manifest 에 명시.
- `.preserved/harvested/hc_checks_raw/hc_checks.py:498~500` — 세션 75 실패: "dyatlov-pass/sources/ 에 character_detective.png + character_assistant.png 가 이전 에피소드와 md5 완전 동일" — 즉 검사관이 **재사용 여부** 를 검증 (에피소드 간 다양성 체크). 우리도 유사 검사 필요하면 Phase 16-04 에 추가.

---

*End of RESEARCH.md — 나베랄 감마, 2026-04-22, 대표님께 제출.*
