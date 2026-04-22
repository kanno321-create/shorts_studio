---
memory_id: project_channel_bible_incidents_v1
source: .preserved/harvested/theme_bible_raw/incidents.md
version: v1.0
status: production_active
imprinted_session: 33
imprinted_date: 2026-04-22
phase: 16-01
channel: incidents
drafted_by: 나베랄
approved_by: 대표님
approved_date: 2026-04-17
---

# incidents (사건기록부) 채널바이블 v1.0 — 박제본

> shorts_naberal `.preserved/harvested/theme_bible_raw/incidents.md` (v1.0, 대표님 2026-04-17 승인) 의 박제 사본.
> 원본은 `.preserved/harvested/` read-only lock (CLAUDE.md 금기 #6). Producer / Inspector 에이전트는 본 메모리만 참조한다.
> Phase 16-01 은 박제 only — 에이전트 AGENT.md `<mandatory_reads>` 업데이트는 Phase 17+ 순차 진행.

## 1. 타겟
30~50대 남성 중심. 범죄·미스터리·실화 관심.
영화 《살인의 추억》《세븐》 톤, 팟캐스트 《그것이 알고싶다》 청취층.

## 2. 영상 길이
- 단편 50~60초
- 시리즈편 (Part N) 90~120초
- 상한 120초 (DESIGN_BIBLE 기준)

## 3. 목표
감정 1개 (불쾌한 긴장감 or 인간에 대한 공허함) + 정보 1개 (시청자가 영상 종료 후 기억하는 디테일 1개) — **둘 다 1개만**.

## 4. 톤
탐정 1인칭 독백 + 왓슨(조수) 시청자 대리 질문. 딱딱하지만 몰입감 있게. 감정 과잉 금지 (울먹임·감탄사 X). 냉정한 사실 제시 + 문장 말미 짧은 인간적 반응 허용. 종결어미 "습니다/입니다/였죠" 만 (FAIL-SCR-011 / FAIL-SCR-016 방지 → `feedback_script_tone_seupnida`).

## 5. 금지어 (블랙리스트)
- "여러분", "놀랍게도", "결론부터 말하면", "~해보세요"
- "충격적인", "소름 끼치는", "엄청난", "역대급", "믿을 수 없는" (감탄 수식어 남발)
- "다음과 같다", "그것은 바로" (국어책 체언종결)
- "되었다", "되어 있었다" (수동태 3연속 금지 — Q2 번역체 패턴)
- 체언종결 2연속 금지 ("공포였다. 침묵이었다." — 금지)
- 3글자 이상 핵심 구절 반복 금지 (FAIL-SCR-006)
- "다시" / "또" 과거 참조 앞 첫 설정 없이 금지
- AI 클리셰 금지: "믿으시겠습니까", "놀라운 사실이 하나 더 있습니다", "상상할 수 없는"

## 6. 문장규칙
평균 길이 12~22자. 20자+ 문장에 쉼표 ≥2개 (호흡 마크). Hook ≤ 50자. 한 컷 = 한 호흡. 한 문장에 메시지 1개. 리듬: Q2 BBC 기준 std ≥ 30자 (짧은-긴-중 교차). 20자 이하 드라마 라인 ≥ 1회/영상. 서사체 필수 — 개조식·체언 종결 단문 2연속 금지 (FAIL-SCR-001 방지). 관형절 + 연결 형태소 (-고 / -며 / -어서 / -는데 / -자마자 / -ㄴ 채) 활용.

## 7. 구조 (4단계 고정)
- **Hook (0-5초)**: 탐정 현장 도착. 질문/반전/금지된 진실/오해 깨기 중 1개로 첫 문장. Hook section 의 narration 에 **"오늘의 기록."** 의무 포함 (FAIL-SCR-002 방어).
- **갈등·오해 (5-30초)**: 시청자 선입견과 다른 실체. 왓슨 첫 질문 → 탐정 답변 (키워드 >= 60% 대응 — `feedback_duo_natural_dialogue`).
- **핵심 3포인트 (30-90초)**: 증거 / 프로파일링 / 현장 관찰. 각 포인트 숫자·비교·사례 >= 1 개.
- **반전·정리 (마지막 2-5초)**: 인간적 공허 + 다음 편 예고형 CTA.

## 8. 근거규칙
숫자·비교·사례 >= 1 (한 편). 실화 기반 — 핵심 사실 엄격, 장면 디테일·호흡은 각색 허용 (`feedback_dramatization_allowed`). "~라고 합니다" 전달형 vs "탐정이 직접 본 것" 직관형 구분 (`feedback_info_source_distinction`). 예: "세 시간 뒤", "이웃 주민 12명", "2003년 7월 14일".

## 9. 화면규칙
매 컷 보여줄 것 1개 명시 (자막/그래픽/현장 이미지/I2V 재현). **Veo/I2V 보조용만**, 실제 이미지 크롤링 최우선 (`feedback_veo_supplementary_only`, CLAUDE.md 금기 #11 보강). 자막 6~12자, 동사 종결, 의미 단위 그룹핑 (`feedback_subtitle_semantic_grouping`). 숫자 쪼개짐 금지 ("1,701통" 한 단어 유지 → `feedback_number_split_subtitle`). 영상:이미지 비율 >= 30% (`feedback_video_clip_priority`). 텍스트 스크린샷 자동 제거.

## 10. CTA규칙
구독 강요 금지. 시리즈 끝맺음 3단계 (`feedback_series_ending_tiers`):
- Part 1: 시그니처 끝 문구 ("저는 이 사건을 아직 놓지 않았습니다" 등)
- Part 2: 독백형 여운
- Part 3: 경각심 + 다음 에피소드 예고

탐정 퇴장 문구 풀 10개 랜덤 선택, 과공손 "뵙겠습니다" 금지 (`feedback_detective_exit_cta`). 왓슨 CTA 풀 10개 (`feedback_watson_cta_pool`). 엔딩 시그니처: 탐정 정면 -> 뒤돌아 걸어감 패턴 (`feedback_outro_signature`).

---

## FAIL-SCR 매핑 (원본 incidents.md §FAIL-SCR 매핑 전수 이관)

| 실패 ID       | 원인                          | 바이블 방지                               |
| ------------- | ----------------------------- | ----------------------------------------- |
| FAIL-SCR-011  | 국어책 낭독체, Hook 과속      | §4 종결어미 + §6 문장규칙                 |
| FAIL-SCR-006  | 핵심 구절 반복                | §5 금지어 (3글자+ 반복 금지)              |
| FAIL-SCR-004  | 듀오 흐름 끊김, CTA 누락      | §7 구조 (왓슨 질문/탐정 답변) + §10 CTA   |
| FAIL-SCR-016  | "어요/해요" 체 혼입           | §4 종결어미 "습니다/입니다/였죠" 만       |
| FAIL-SCR-001  | 체언종결 단문 2연속 (개조식)  | §6 문장규칙 (서사체 필수)                 |
| FAIL-SCR-002  | "오늘의 기록" 인삿말 누락     | §7 Hook section 강제 포함                 |

## 관련 feedback 메모리 (12건)

- feedback_script_tone_seupnida (§4 — 종결어미)
- feedback_duo_natural_dialogue (§7 — 왓슨 질문/탐정 답변 리듬)
- feedback_subtitle_semantic_grouping (§9 — 자막 6~12자 동사 종결)
- feedback_video_clip_priority (§9 — 영상:이미지 >= 30%)
- feedback_outro_signature (§10 — 엔딩 시그니처)
- feedback_series_ending_tiers (§10 — Part 1/2/3 CTA 차등)
- feedback_detective_exit_cta (§10 — 탐정 퇴장 문구 10 pool)
- feedback_watson_cta_pool (§10 — 왓슨 CTA 10 pool)
- feedback_dramatization_allowed (§8 — 장면 디테일 각색 허용)
- feedback_info_source_distinction (§8 — "~라고 합니다" vs 직관)
- feedback_veo_supplementary_only (§9 — I2V 보조용, 실제 이미지 최우선)
- feedback_number_split_subtitle (§9 — "1,701통" 한 단어 유지)

## Hook signature (channel-incidents SKILL §Hook 시그니처 Veo 재사용 패턴)

- **Hook clip duration 하드 고정**: **9.0 초** (세션 43 대표님 지시 "한 남자의 기록을 펼쳤습니다 까지 시그니처 영상 보여라, 너무 빨리 없어짐")
- **인트로 시그니처 파일**: `.preserved/harvested/video_pipeline_raw/signatures/incidents_intro_v4_silent_glare.mp4` (Plan 16-03 Task 1 harvest 확장 후 배치 예정)
- **실소스 위치** (Plan 16-03 Task 1 복사 대상): `C:/Users/PC/Desktop/shorts_naberal/output/_shared/signatures/incidents_intro_v4_silent_glare.mp4` (1.70 MB, Veo 3.1 Lite 생성물, v4 채택본)
- **MAPPING (0, 0) 고정**: Hook section 전체를 signature Veo 1 clip 으로 배치. sentence split 금지 (channel-incidents SKILL 재사용 절차 §2).
- **Veo 신규 호출 금지** (CLAUDE.md 금기 #11): 기존 v4 파일 복사/재사용만. 시그니처 v5 이상 재생성은 Phase 17+ 대표님 명시 지시 필요.

## Duo 대화 자연화 규칙 (대표님 2026-04-18 지시, channel-incidents SKILL §)

1. **조수 "탐정님" 호명 절대 금지** — 호명이 교과서 말투 + AI티. 자연 대화는 질문으로 바로 진입.
2. **탐정 -> 조수 호명도 금지** — "즌다" 호명 금지. 시청자 몰입 방해.
3. **조수 질문 -> 탐정 직답** — 첫 문장에서 키워드 >= 60% 대응. 화제 전환 명령 없음.
4. **조수 영상 과다 등장 금지** — assistant 화자 섹션도 시각은 쉽먼/현장/증거물 교체 가능. TTS 만 즌다 보이스.

## 나레이션 호흡 규칙 (대표님 2026-04-18 지시)

- 쉼표(`,`) 구간에서 반드시 짧게 끊어읽기 (300~400ms pause, Morgan 보이스 tempo=0.93 기준).
- scripter / script-polisher 는 2~4 어절마다 쉼표 검토.
- TTS 파라미터: Typecast `pause_at_comma=true` 또는 SSML `<break time="300ms"/>`.

## Voice Preset (channel-incidents SKILL §)

| 항목           | 값                                             |
| -------------- | ---------------------------------------------- |
| 메인 보이스    | Risan Ji                                       |
| 대체 보이스    | Sullock Hong, Jungmin, Morgan                  |
| accent         | #E53E3E                                        |
| audio_tempo    | 0.9 (범죄 다큐 무게감)                         |
| emotion 기본   | tonedown                                       |

섹션별 감정: Hook=normal / Body=tonedown / 클라이맥스=whisper / CTA=sad·tonedown.

## 재사용 안내

모든 Producer (scripter / script-polisher / director / scene-planner / voice-producer / asset-sourcer / assembler) / Inspector (ins-korean-naturalness / ins-factcheck / ins-narrative-quality / ins-tone-brand / ins-readability) AGENT.md 는 본 메모리를 `<mandatory_reads>` 에 추가해야 합니다 (Phase 16-01 에서는 박제만 수행, 에이전트 mandatory_reads 업데이트는 Phase 17+ 개별 진행).

## 원본 참조

- SSOT 원본: `.preserved/harvested/theme_bible_raw/incidents.md` (v1.0, read-only)
- SKILL 파생: `.preserved/harvested/skills_raw/channel-incidents/SKILL.md` (duo 규칙 + Hook 시그니처 Veo 재사용 + 탐정 POV 3요소)
- 파생 테마 바이블 (Phase 16 reference_only): wildlife / humor / politics / trend / documentary
