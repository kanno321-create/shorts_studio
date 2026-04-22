# NEXT SESSION START — 세션 #35 진입 프롬프트

**작성**: 2026-04-23 세션 #34 종료 시점
**작성 근거**: 대표님 지시 "수정 다끝나면 새로운 영상제작은 처음부터할꺼고 다음세션에서할수있도록 핸드오프 3종도 작성부탁해"
**1-page 경계**: 30초 진입 프롬프트. 깊은 맥락은 `WORK_HANDOFF.md` §세션#34, 대화 흐름은 `SESSION_LOG.md` §Session #34.

---

## 🚨 세션 #34 요약 (무슨 일이 있었나)

Ryan Waller 쇼츠 **v2/v3/v3.1/v3.2** 4번 재제작 시도, 전부 대표님 판정 실패. 실패 패턴 분석으로 **영구 INVARIANT 3-Rule** 확립 + **Script-Driven 3-Agent Pipeline v1** 설계. **v4 실 render 는 세션 제약으로 미실행** — 다음 세션 과제.

---

## 🎯 세션 #35 단 하나의 목표

**완전히 새로운 영상 제작을 INVARIANT 3-Rule 준수하며 처음부터** (대표님 명시 지시 "새로운 영상제작은 처음부터할꺼고").

### 사건 선택지 (대표님 결정 대기)
- (A) TOP 5 NLM pool 2~5위 사건으로 pivot (세션 #33 NLM 쿼리 결과 `outputs/nlm_queries/crime_top_pitch_20260422_231341.md` 참조)
- (B) 완전 새 NLM 쿼리로 다른 채널 (예: `incidents_jp` 외 미개척)
- (C) Ryan Waller 재도전 (기존 자산 재활용)

세션 #35 첫 질문 = 대표님께 선택지 확인.

---

## ⚡ 첫 5분 행동 (세션 #35 바로 실행)

```bash
# 1. 컨텍스트 로드 (10초)
cat NEXT_SESSION_START.md                 # 이 파일
head -300 WORK_HANDOFF.md                  # 세션 #34 산출물 + v4 pipeline spec
cat .claude/memory/MEMORY.md               # 🔴 INVARIANT 3-Rule 인덱스

# 2. INVARIANT 3-rule 필수 정독 (5분)
cat .claude/memory/feedback_every_agent_reads_script_first.md       # Rule 1
cat .claude/memory/feedback_script_markers_absolute_compliance.md   # Rule 2
cat .claude/memory/feedback_agents_require_visual_analysis.md       # Rule 3

# 3. Pipeline spec + 보조 원칙 (2분)
cat .claude/memory/project_script_driven_agent_pipeline_v1.md
cat C:/Users/PC/.claude/plans/glistening-snacking-sparkle.md         # v4 plan (execution blueprint)

# 4. 대표님께 사건 선택 확인 요청 (A/B/C)
```

---

## 🔴 INVARIANT 3-Rule (절대 준수 — 모든 영상 작업 영구)

세션 #34 대표님 직접 지시로 확립. **이번 쇼츠 한정 아님**, 향후 모든 영상/모든 채널/모든 에이전트 (Producer 15 + Inspector 17 + 조율자) 영구 적용.

### Rule 1 — 모든 에이전트는 대본을 반드시 보면서 작업한다
- 에이전트 entry-point 첫 행위 = `script.json` (당 에피소드) 로드
- 대본 없이 자기 heuristic 만으로 작업 **금지**
- 구현: AGENT.md `<mandatory_reads>` + stdout 로그 `reads script_v*`

### Rule 2 — 대본 표현 그대로 반영, 벗어남 금지
- **emotion_markers** (감정) → TTS emotion_preset
- **situation_markers** (장소/시간/대상) → 영상 scene / 검색 keyword
- **motion_markers** (움직임 동사) → Kling I2V prompt motion
- 대본에 없는 요소 자체 해석·추가 **금지** (예: 대본에 경찰차 없으면 영상에 사이렌 넣기 금지)

### Rule 3 — Claude Opus 4.7 Subagent 가 key frame 시각 판정
- 크롤링·제작·검사 단계 = Agent tool, `subagent_type="general-purpose"`, `model="opus"` 로 spawn
- Subagent 가 Read 로 key frame 보고 판정 → JSON 리턴
- **메인 세션 직접 Read 금지** (context 보호), 외부 vision API (Gemini/GPT-4o/TwelveLabs) **금지**

---

## 🏗️ Script-Driven 3-Agent Pipeline (v4 블루프린트)

```
scripter/human → script_v1.json
                      ↓
Agent 0 Shot-Breakdown → script_v4.json (shots[] + emotion/situation/motion markers)
    ├──→ Agent 1 Asset Sourcer (멀티소스 search + subagent vision)
    │        → sources/real_v4/ + manifest_v4.json
    ├──→ Agent 3 TTS Generator (Morgan narrator + Guri assistant + PresetPrompt)
    │        → narration_v4.mp3 + timing_v4.json
    │                ↓
    │        Agent Subtitle → subtitles_remotion_v4.{json,ass,srt}
    │
    └──→ Agent 2 Video Producer (shot-level trim/Kling + subagent verify)
              → sources/shot_final/<shot_id>_final.mp4 × N
                      ↓
              Agent Spec → visual_spec_v4.json (outro-last assertion)
                      ↓
              Agent 5 Render → final_v4.mp4
                      ↓
              Agent 4 Inspector (subagent vision) → inspect_report_v4.md
```

**상세 spec**: `C:/Users/PC/.claude/plans/glistening-snacking-sparkle.md` (14 Step 실행 순서 + 재사용 모듈 + 검증 기준)

---

## 🛠️ 재사용 가능 (세션 #34 산출물)

### 영구 스킬 / 모듈
- `scripts/orchestrator/video_sourcing/` (6 파일) — YouTube + Wikimedia + rank + download
- `scripts/experiments/generate_ryan_waller_kling_official.py` — Kling 공식 API JWT 패턴 (`POST https://api.klingai.com/v1/videos/image2video`, `model_name=kling-v2-6`, `mode=pro`, `duration=10`)
- `scripts/experiments/generate_ryan_waller_tts_v3_2.py` — Typecast PresetPrompt 패턴 (Morgan `tc_6256118ea1103af69f0a87ec` ssfm-v30 / Guri `tc_6359e7ea258d1b6dc3abe6e6` ssfm-v21)
- `scripts/experiments/extract_ryan_waller_doc_clips_v2.py` — ffmpeg 9:16 letterbox trim 패턴
- `scripts/validate/verify_baseline_parity.py` — 9 criteria 검증

### API keys (.env)
- `TYPECAST_API_KEY` — TTS
- `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` — Kling 공식 JWT (대표님 "api 크레딧 많다")
- `FAL_KEY` — fal.ai 대체 경로 (duration≤8 제약, 우회용)
- `YOUTUBE_API_KEY` + `GOOGLE_API_KEY` — YouTube Data API v3
- `OPENAI_API_KEY` / `PEXELS_API_KEY` / `PIXABAY_API_KEY` — 필요 시 확장

### Reference 품질 baseline
- `shorts_naberal/output/zodiac-killer/` (81% real content, 184 subtitle cue)
- `shorts_naberal/output/elisa-lam/` (100% real + 15 video clips)
- `shorts_naberal/scripts/video-pipeline/_kling_i2v_batch.py` (Kling duration 10)

### 자산
- `output/ryan-waller/sources/intro_signature.mp4` (v4 탐정 시그니처)
- `output/ryan-waller/sources/outro_signature.mp4` (shorts_naberal/zodiac-killer 에서 복사, 2.08 MB)
- `output/ryan-waller/sources/character_detective.png`, `character_assistant.png` (웰시 코기, top-bar overlay 전용 — scene 등장 금지)

---

## ⚠️ 세션 #35 절대 준수

1. **INVARIANT 3-Rule** — 예외 없음. 위반 시 return 후 재작업.
2. **조수(왓슨) 영상 scene 등장 절대 금지** — 상단 bar overlay 만 허용
3. **shot-level 1:1 매핑** — 한 clip 을 여러 shot 에 재사용 금지, 파일명에 shot_id 라벨
4. **outro_signature 반드시 last clip** — 중간 배치 + 뒤에 추가 shot 금지
5. **여성 YouTuber 호스트 영상 배제** — title/channel 에 "Young Love" 같은 true-crime YouTuber 감지 시 skip
6. **Typecast whisper preset 사용 자제** — tonedown + intensity 0.9 로 대체 + ffmpeg loudnorm
7. **CLAUDE.md 금기 11건 전수 준수** — 특히 #6 shorts_naberal 원본 수정 금지 + #9 33 에이전트 초과 금지 (신규 agent 생성 대신 `general-purpose` subagent 활용)

---

## 🗺️ 세션 #35~#36 예상 경로

### 세션 #35 (새 영상 v1 제작)
1. 대표님 사건 선택 (A/B/C)
2. NLM 쿼리 (필요 시) → TOP 사건 fact sheet
3. scripter → script_v1.json
4. Agent 0 shot-breakdown → script_v4.json (with markers)
5. Agent 1 Sourcer (subagent vision) → manifest
6. Agent 3 TTS 생성
7. Agent 2 Producer (subagent verify per shot)
8. Agent Spec + Agent 5 Render
9. Agent 4 Inspector (subagent vision)
10. 대표님 검수

### 예상 소요
- **시간**: 3-4 시간 (NLM + script 작성 + 22 shot × Kling + render + 검증)
- **비용**: $8-20 (Kling API + Typecast quota 범위)

### 성공 기준
- 대본-영상 1:1 매핑 검증 (Inspector subagent pass)
- freeze 0건 (shot 1:1 매핑 + shot 단위 duration)
- parity ≥8/9
- 대표님 눈/귀 검수 합격

---

## 📂 세션 #34 산출물 전수 경로

### INVARIANT 박제 (영구, 새 메모리 8종)
```
.claude/memory/
├── feedback_every_agent_reads_script_first.md         # Rule 1
├── feedback_script_markers_absolute_compliance.md     # Rule 2
├── feedback_agents_require_visual_analysis.md         # Rule 3
├── feedback_shot_level_asset_1to1_mapping.md          # v4 보조
├── feedback_outro_signature_must_be_last_clip.md      # v4 보조
├── feedback_whisper_volume_normalize.md               # v4 보조
├── feedback_shot_filename_label_explicit.md           # v4 보조
└── project_script_driven_agent_pipeline_v1.md         # Pipeline SSOT
```

### v3.2 산출물 (부분 제출 상태, 참조만)
```
output/ryan-waller/
├── final_v3_2.mp4                      # 81.7 MB — 대표님 7 지적
├── script_v3.json / narration_v3_2.mp3
├── subtitles_remotion_v3_2.{json,ass,srt}
├── visual_spec_v3_2.json
└── sources/
    ├── intro_signature.mp4, outro_signature.mp4
    ├── character_{detective,assistant}.png
    ├── broll_0{1..6}_*_v3.mp4 (Kling 공식 API 생성 6 clips)
    ├── real/raw_documentaries/ZI8G0KOOtqk_*.mp4 (65분 Full Interrogation)
    └── real/raw_doc_clips_v2/*.mp4 (9 extracted clips)
```

### Plan (v4 execution blueprint)
- `C:\Users\PC\.claude\plans\glistening-snacking-sparkle.md` — 14 Step + INVARIANT 3-Rule + 아키텍처 결정

---

*세션 #34 종료 — Ryan Waller v2/v3/v3.1/v3.2 반복 실패에서 INVARIANT 3-Rule + Pipeline v1 확립. 세션 #35 에서 새 영상 처음부터 적용.*
