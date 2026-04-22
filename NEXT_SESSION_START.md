# NEXT SESSION START — 세션 #33 진입 프롬프트

**작성**: 2026-04-22 세션 #32 종료 시점
**작성자**: 대표님 지시 "핸드오프 3종만들고, 다음세션에서 지금이랑 자연스럽게 이어서 작업가능하도록 전후사정 대화를 제대로 남기고 작업을 제대로 넘겨라"
**1-page 경계**: 이 문서는 다음 세션의 첫 30초 진입 프롬프트. 깊은 맥락은 WORK_HANDOFF.md, 대화 흐름은 SESSION_LOG.md `Session #32` 참조.

---

## 🚨 세션 #32 충격 사건 요약 (반드시 인지)

대표님이 SESSION #31 산출물 (`outputs/ffmpeg_assembly/assembled_1776844680770.mp4`) 을 보시고 "**큰일났다 이런 퀄리티로 어떻게 하노**" 라 충격받으셨습니다. 분석 결과:

- **우리 영상**: 13초 720p 519kbps · 자막없음 · 자료사진 0개 · 인트로/아웃로 없음 · 캐릭터 오버레이 없음
- **Production baseline (`shorts_naberal/output/zodiac-killer/final.mp4` 등 6편)**: **60~130초 · 1080p · 5~21Mbps · 단어단위 자막 + 인트로/아웃로 시그니처 + 캐릭터 듀오(탐정+왓슨) + 사건 자료 사진 10~15개 + Ken Burns + Remotion 합성**

**본질 차이**: spec 게이트 통과 ≠ production 콘텐츠. 우리는 **architecture 자체가 빠져있는 상태**였습니다. 대표님 표현: "**이대로는 아예 시작도못하고 망하겠다**".

→ 대표님 결정 = **옵션 A 즉시 도입** (Remotion + word_subtitle + intro_signature + 채널바이블 production 자산을 `.preserved/harvested/` 로 가져와 우리 ASSEMBLY 재배선).

---

## 🧠 자동 주입 확인 (첫 5초)

세션 #33 시작 시 `session_start.py` Hook 이 다음을 자동 주입:

1. 🔑 `.env` API keys (재질문 금지) — `OPENAI_API_KEY` 신규 추가됨 (gpt-image-2 안정 보관)
2. 📋 WORK_HANDOFF.md 첫 30줄 (세션 #32 항목)
3. 🧠 MEMORY.md index — **신규 4 메모리 자동 노출**:
   - `feedback_no_mockup_no_empty_files` — **🔴 절대 금지**: 목업/스텁/빈 파일/placeholder 생성 (대표님 절대 규칙)
   - `reference_production_gap_map` — production vs 우리 11 누락 컴포넌트
   - `reference_harvested_full_index` — **🔴 옵션 A 진입 자료**: 9폴더 160파일 + 5-Step 진입 + Phase A1~A4 로드맵
   - `project_image_stack_gpt_image2` — 정지 이미지 = gpt-image-2 primary
4. 📛 최근 실패 (open + 최근 5)
5. 🗺️ Navigator + CONFLICT_MAP

---

## 🎯 단 하나의 목표 (세션 #33)

**Phase A1 진행** — `.preserved/harvested/theme_bible_raw/incidents.md` (사건기록부 v1.0 SSOT) + `skills_raw/channel-incidents/SKILL.md` + `baseline_specs_raw/zodiac-killer/visual_spec.json` 를 흡수해 **`.claude/memory/project_channel_bibles_v1.md`** 신규 박제 + production feedback 메모리 12+ 매핑.

**금지** (옵션 A 모든 단계 공통):
- ❌ 코드 수정 (Phase A2~A4 에서, A1 은 박제만)
- ❌ 13초 영상을 production 으로 인정
- ❌ 자막·인트로·아웃로 누락된 영상을 production 으로 인정
- ❌ "spec 통과 = 완료" 보고 (충격 사건 재발 방지)
- ❌ 빈 출력 / placeholder / 목업 (CLAUDE.md 금기 #10)
- ❌ Veo 호출 (CLAUDE.md 금기 #11) — 가이드만 Kling 응용용
- ❌ shorts_naberal 원본 수정 (CLAUDE.md 금기 #6) — `.preserved/harvested/` read-only 잠금 완료

---

## 🚀 첫 5분 행동 (Step 1 SSOT 흡수)

```
1. cat .preserved/harvested/theme_bible_raw/incidents.md            # 사건기록부 v1.0 SSOT
2. cat .preserved/harvested/skills_raw/channel-incidents/SKILL.md
3. cat .preserved/harvested/baseline_specs_raw/zodiac-killer/visual_spec.json   # Remotion props 실제 예
4. head -100 .preserved/harvested/baseline_specs_raw/zodiac-killer/subtitles_remotion.ass   # 자막 형식
5. cat .preserved/harvested/skills_raw/channel-incidents-jp/SKILL.md   # 일본 채널
```

## 🚀 첫 1시간 행동 (Phase A1)

1. 신규 메모리 작성 — `.claude/memory/project_channel_bibles_v1.md` (7 채널 v1.0 핵심 추출 + cross-ref)
2. production feedback 12+ 메모리 식별 — `incidents.md` 에 cross-reference 된 메모리 이름 (`feedback_script_tone_seupnida`, `feedback_duo_natural_dialogue`, `feedback_subtitle_semantic_grouping`, `feedback_video_clip_priority`, `feedback_outro_signature`, `feedback_series_ending_tiers`, `feedback_detective_exit_cta`, `feedback_watson_cta_pool`, `feedback_dramatization_allowed`, `feedback_info_source_distinction`, `feedback_veo_supplementary_only`, `feedback_number_split_subtitle`) 의 production 원본 위치 확인 + 우리 `.claude/memory/` 로 매핑
3. MEMORY.md 인덱스 갱신
4. 보고 → 대표님 Phase A2 진행 여부 결정

## 🚀 향후 (Phase A2~A4, 다음 세션 이후)

- Phase A2 (2~3 세션): ASSEMBLY 재배선 — `scripts/orchestrator/api/remotion_renderer.py` 신규 + shorts_pipeline ASSEMBLY 분기
- Phase A3 (1~2 세션): word_subtitle + intro/outro signature 통합
- Phase A4 (1~2 세션): visual_spec.json 생성 로직 + sources/ 디렉토리 구조

---

## ⚠️ 절대 준수 (이 세션에서 박제)

1. **목업·빈 파일·placeholder 금지** (CLAUDE.md 금기 #10) — 모든 산출물 production-ready 실 콘텐츠
2. **Veo 호출 금지** (CLAUDE.md 금기 #11) — Kling 단독, VEO_PROMPT_GUIDE 는 Kling 응용 참조만
3. **shorts_naberal 원본 수정 금지** (금기 #6) — `.preserved/harvested/` 9 폴더 160 파일 read-only 잠금됨
4. **production baseline 충족 검증 필수** — 60~120초 + 1080p + 자막 + 인트로/아웃로 + 캐릭터 + 자료사진 ≥ 5장
5. **대표님께 "완료" 보고 전 baseline 6편과 정량/정성 비교** — 충격 사건 재발 방지

---

## 📚 깊은 맥락 (필요 시)

- **세션 #32 전체 흐름**: `SESSION_LOG.md` Session #32 entry — 대화 인용 포함
- **세션 #32 박제 산출물**: `WORK_HANDOFF.md` 세션 #32 섹션
- **production 격차 11 컴포넌트**: `.claude/memory/reference_production_gap_map.md`
- **harvest 160 파일 인덱스**: `.claude/memory/reference_harvested_full_index.md`
- **gpt-image-2 결정**: `.claude/memory/project_image_stack_gpt_image2.md`

---

*세션 #32 종료 — 옵션 A Phase A1 진입 대기. 다음 세션 첫 행동: 위 "첫 5분 행동" 5개 명령부터.*
