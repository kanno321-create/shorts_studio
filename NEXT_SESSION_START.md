# NEXT SESSION START — 세션 #34 진입 프롬프트

**작성**: 2026-04-23 세션 #33 종료 시점 (컨텍스트 포화)
**작성 근거**: 대표님 지시 "컨텍스트 꽉참, 핸드오프 3종 만들어서 다음 세션에서 바로 수정작업할수있게 잘작성해라"
**1-page 경계**: 30초 진입 프롬프트. 깊은 맥락은 WORK_HANDOFF.md §세션#33, 대화 흐름은 SESSION_LOG.md §Session #33.

---

## 🚨 세션 #33 핵심 사건 요약

1. **Phase 16 Production Integration Option A 완료** — 39 commits, 4 Plan all green, Phase 16 VERIFICATION PASSED (5/5 SC), gsd-tools `phase complete 16` 공식 종료.
2. **첫 production smoke 시도: Ryan Waller 쇼츠** — NLM 리서치 → 대본 → TTS → 자막 → gpt-image-2 × 6 → Remotion render → `output/ryan-waller/final.mp4` **68.8 MB** 생성 성공.
3. **🔴 대표님 판정: 실패** — 5가지 핵심 결함 지적. **원인 전수 진단 완료 + 교정 계획 수립. 교정 작업은 세션 #34 에서 수행**.

---

## 🎯 세션 #34 단 하나의 목표

**Ryan Waller v2 재제작** — 5 실패 전수 교정 + 재렌더 + baseline parity 재검증.

---

## ⚡ 첫 5분 행동 (세션 #34 바로 실행)

```bash
# 1. 컨텍스트 로드 (10초)
cat NEXT_SESSION_START.md               # 이 파일
head -150 WORK_HANDOFF.md                # 세션 #33 전체 산출
grep -A5 "FAIL-" WORK_HANDOFF.md | head -50  # 5 실패 근본 원인

# 2. 현 산출물 목록 확인 (5초)
ls output/ryan-waller/                   # script.json / narration.mp3 / final.mp4 등
ls output/ryan-waller/sources/           # 6 b-roll + signature + character

# 3. 교정 대상 파일 5종 path 확인
echo "FIX-1,2 TTS SSML: scripts/orchestrator/api/typecast.py L189-213"
echo "FIX-3 조수 교체: shorts_naberal/output/zodiac-killer/sources/character_assistant.png"
echo "FIX-4 Kling I2V: scripts/orchestrator/api/kling_i2v.py (Phase 9)"
echo "FIX-5 왓슨 CTA: .claude/memory/feedback_watson_cta_pool.md"
```

---

## 🔴 5 실패 + 근본 원인 + 교정 방법 (기술 요약)

| # | 증상 (대표님 지적) | 근본 원인 | 교정 |
|---|---|---|---|
| FAIL-1 | 대본의 "감정선/슬래시/괄호" 를 그대로 낭독 | `typecast.py:_inject_punctuation_breaks()` 가 SSML `<break time="Xs"/>` tag 삽입 → ssfm-v30 SDK 가 SSML 미지원 → literal 낭독 | 함수 호출 제거 또는 `comma_pause=0 mark_pause=0` 무력화. config 의 `auto_punctuation_pause:true` 가 이미 Typecast native pause 담당. |
| FAIL-2 | 감정 없는 국어책 낭독 | FAIL-1 과 **동일 root cause** — SSML 오염 + 자연 pause 파괴로 emotion 파라미터 효과가 노이즈에 묻힘 | FAIL-1 수정만 하면 자동 해소 (확인 필요). 추가로 Morgan emotion 변화 실측. |
| FAIL-3 | 조수 캐릭터가 일본판 (검은 머리 인간) | `.preserved/harvested/video_pipeline_raw/characters/` 는 `incidents_assistant_jp_a.png` (**`_jp_`** = 일본판). 한국판 웰시 코기는 episode-specific `shorts_naberal/output/zodiac-killer/sources/character_assistant.png` 에만 존재 → **harvest 누락** | `cp shorts_naberal/output/zodiac-killer/sources/character_assistant.png output/ryan-waller/sources/character_assistant.png` 후 재 harvest 계획 수립 |
| FAIL-4 | 모든 영상이 Ken Burns pan/zoom 만 (정적 이미지) | 내가 CLAUDE.md 금기 #11 "Veo 금지" 를 "I2V 전체 금지" 로 **확대해석**. 실제로 **Kling 2.6 Pro I2V 는 허용** (금기 #11 명시). | `scripts/orchestrator/api/kling_i2v.py` 로 6 image 각각을 anchor frame 으로 Kling I2V 호출 → mp4 clips 6개. 예상 비용 $3-5, 시간 20-40분. |
| FAIL-5 | 마지막에 탐정 CTA 만, 왓슨(웰시 코기) CTA 누락 | 대본 Aftermath 에 탐정 Pool #9 만. Bible §10 은 **탐정 CTA + 왓슨 CTA 둘 다** (duo pattern — hook 과 대칭). `feedback_watson_cta_pool.md` 에 pool 10개 이미 박제. | 대본 끝에 왓슨 CTA 1문장 추가 (예: "다음 기록도, 함께 봐요?"). TTS 재생성 시 왓슨 보이스 (Guri or Morgan emotion=urgent) 사용. |

---

## 📂 세션 #33 산출물 핵심 경로

### Ryan Waller 쇼츠 (세션 #34 교정 대상)
```
output/ryan-waller/
├── final.mp4                 (68.8 MB, 1080×1920, h264, 116s — 실패작)
├── narration.mp3             (Typecast Morgan, 116.04s, SSML 오염)
├── narration_timing.json
├── script.json               (19 sentences — 왓슨 CTA 누락)
├── visual_spec.json
├── sources_manifest.json
├── blueprint.json
├── subtitles_remotion.{ass,json,srt}
└── sources/
    ├── intro_signature.mp4   (v4, OK)
    ├── character_detective.png (harvest — OK, 탐정 확인)
    ├── character_assistant.png (🔴 일본판 — 교체 필요)
    └── broll_01~06 *.png     (gpt-image-2 정적 — Kling I2V 전환 필요)
```

### Phase 16 산출물 (완료, read-only 참조만)
```
.planning/phases/16-production-integration-option-a/
├── 16-CONTEXT.md / 16-RESEARCH.md (1259줄) / 16-VALIDATION.md / 16-VERIFICATION.md (PASSED)
├── 16-0{1,2,3,4}-PLAN.md + 16-0{1,2,3,4}-SUMMARY.md
└── schemas/visual-spec.v1.schema.json + scene-manifest.v4.schema.json
```

### 박제된 메모리 (세션 #33)
- `reference_signature_and_character_assets.md` (🔴 korean welsh corgi 누락 명시 추가 필요 — FAIL-3 사실 반영)
- `feedback_detective_exit_cta.md` (탐정 pool 10 완성)
- `feedback_notebooklm_paste_only.md` (NLM paste 원칙)
- `project_channel_bible_incidents_v1.md` + 5 reference 채널바이블 + 12 feedback (Phase 16-01)
- `project_channel_preset_incidents.md` (Phase 16-04)

---

## ⚠️ 세션 #34 절대 준수

1. **교정 전 실증**: narration.mp3 재생해서 SSML literal 낭독 여부 ear-verify (대표님 feedback 기반 + 직접 ffmpeg 로 3-4초 sample 들어보기).
2. **FIX-4 Kling I2V 호출 전 CLAUDE.md 금기 #4/#11 재독** — I2V only, Anchor Frame, Veo 금지. Kling 2.6 Pro 단독.
3. **FIX-5 왓슨 CTA** 선정 시 `feedback_watson_cta_pool.md` 에서 choice. 식상한 문구 금지 (세션 #33 대표님 피드백 준수).
4. **5 실패 박제 (feedback memories) 선행** — v2 재제작 전 5 실패 원인을 feedback 메모리로 영구 박제 (재발 방지). 세션 #33 에서는 한 것 없음.
5. **v2 baseline parity 재검증** — v1 은 7/9 PASS (bitrate + subtitle_track 이슈). v2 는 9/9 또는 명시적 이유 있는 sub-criterion 만 불합격.

---

## 🗺️ 다음 단계 (세션 #34~35)

### 세션 #34: 교정 + v2 재제작
1. **5 실패 박제** — 5 feedback memories 생성 (재발 방지)
2. **FIX-1+2**: typecast.py SSML 비활성화 + narration 재생성
3. **FIX-3**: 웰시 코기 character_assistant.png 교체
4. **FIX-5**: 대본 왓슨 CTA 추가 + TTS 재생성 + 자막 재생성
5. **FIX-4**: Kling I2V × 6 clips 생성 → sources/ 교체
6. Remotion render v2 + ffprobe + baseline parity
7. 대표님 v2 검수 → 합격 시 upload, 불합격 시 재교정

### 세션 #35+ (v2 합격 후)
- 이 쇼츠 upload (YouTube Data API v3, unlisted smoke)
- 2번째 사건 착수 (NLM pool #3/#5 중 선택)
- Phase 17 계획 (incidents-jp + word_subtitle.py 빈출력 debug + Kling I2V 표준화)

---

*세션 #33 종료 — Ryan Waller v1 실패작 보관 (`output/ryan-waller/final.mp4` 교훈 자료로 유지). 세션 #34 = v2 재제작 집중.*
