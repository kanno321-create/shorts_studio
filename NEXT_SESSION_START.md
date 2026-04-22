# NEXT SESSION START — 세션 #36 진입 프롬프트

**작성**: 2026-04-23 세션 #35 종료 시점
**작성 근거**: 대표님 지시 "플랜모드로 플랜짜고 핸드오프 3종 만들어라 다음세션에서 작업해라"
**1-page 경계**: 30초 진입 프롬프트. 깊은 맥락은 `WORK_HANDOFF.md` §세션#35, 대화 흐름은 `SESSION_LOG.md` §Session #35.

---

## 🚨 세션 #35 요약 (무슨 일이 있었나)

Ryan Waller 쇼츠 재도전. v4 3-pass render (73.32→72.97→73.01 MB) + v5 total reset render (74.33 MB) 총 **5차례 실패**. 대표님 누적 지적 12건 전수 재현 또는 악화. 근본 원인 = **Agent pipeline 완전 우회** + `QUERY_OVERRIDES` 하드코딩 (Rule 2 정면 위반) + Inspector 완전 skip (Rule 3 회피). v6 정석 Agent Capsule 아키텍처 재설계 → plan 파일 확정 + 핸드오프 3종 작성 후 세션 종료.

---

## 🎯 세션 #36 단 하나의 목표

**정석 Agent Capsule 아키텍처 구축 + Ryan Waller v6 대본 100% 반영 쇼츠 제작** (대표님 2026-04-23 지시 "정말 정석대로 무조건 최상의 품질을 정석대로 내가 시킨것이 많고 길더라도 반드시 지켜서").

Plan 파일 `C:/Users/PC/.claude/plans/3-serene-sun.md` 의 Phase 0 → 5 순차 진행.

---

## ⚡ 첫 5분 행동 (세션 #36 바로 실행)

```bash
# 1. Plan + 핸드오프 정독 (3분)
cat C:/Users/PC/.claude/plans/3-serene-sun.md         # v6 전체 아키텍처 + 실행 순서
cat NEXT_SESSION_START.md                              # 이 파일
head -200 WORK_HANDOFF.md                              # 세션 #35 상세

# 2. INVARIANT 3-Rule 재정독 (3분) — 세션 #34 박제, 세션 #35 에서 우회당한 것
cat .claude/memory/feedback_every_agent_reads_script_first.md       # Rule 1
cat .claude/memory/feedback_script_markers_absolute_compliance.md   # Rule 2
cat .claude/memory/feedback_agents_require_visual_analysis.md       # Rule 3
cat .claude/memory/project_script_driven_agent_pipeline_v1.md       # Pipeline SSOT

# 3. 대표님께 3 결정 사항 질의
#    (A) Kling T2I balance 충전 완료?
#    (B) 실 자료 4 소스 확보 방법? (WebSearch / URL / 로컬 파일)
#    (C) Phase 1 범위? (33 agent 전부 / 2개 시범)

# 4. 결정 받으면 Phase 0 → 1 → 2 → 3 → 4 → 5 순차
```

---

## 🔴 INVARIANT 3-Rule (영구 준수 — 세션 #35 에서 구조적으로 우회당함, v6 에서 code-enforced)

1. **모든 에이전트는 script.json 을 첫 행위로 read** — v6 AGENT.md `<mandatory_reads>` 에 script.json 추가 + output JSON 의 `reads_script_path` 필드 의무
2. **대본 표현 (emotion/situation/motion markers) 그대로 반영, 벗어남 금지** — v6 AGENT.md `<rule_2_enforcement>` 블록 추가 + 하드코딩 grep 검증 0 hit
3. **크롤링/제작/검사 단계 Claude Opus 4.7 subagent 시각 판정** — v6 AGENT.md `<rule_3_self_vision_gate>` 블록 + Return 전 자체 Opus vision gate 필수

---

## 🏗️ v6 Agent Capsule 구조 (33 agent 표준)

```
.claude/agents/<category>/<agent-name>/
├── AGENT.md                 # 기존 — v6 patch (Rule 1/2/3 블록)
├── FAILURES.md              # 신규 — agent 과거 실패 + 교훈
├── skills/                  # 신규 — 도메인 특화 도구 (여러 개 가능)
│   ├── <skill-1>.md
│   └── <skill-N>.md
└── memory/                  # 신규
    ├── shared.md            # 전역 .claude/memory/ 포인터
    └── agent_specific.md    # agent 전용 learnable state
```

---

## 📊 Ryan Waller v6 Shot Type 매트릭스

### Type 1 — 실 자료 (4 소스 → 10 shots)
| 소스 | 해당 shots | 확보 |
|---|---|---|
| Ryan 눈탱이방탱이 사진 | hook_s03, body_scene_s03, body_dalton_s02 | WebSearch or 대표님 제공 |
| Carver 부자 mugshot | reveal_s01 | Arizona DOC public record |
| Heather Quan 사진 | body_scene_s01 | 가족/뉴스 memorial |
| Full Interrogation 영상 | hook_s05, watson_q1_s01, body_dalton_s01, body_6hours_s02, reveal_s03 | `output/.v4_backup_ryan-waller/` 에서 복원 (65분 raw 이미 보유) |

### Type 2 — AI 생성 (12 shots, Kling T2I+I2V primary, Runway fallback)
hook_s01 · hook_s02 · hook_s04 · hook_s06 (overlay) · body_scene_s02 · body_6hours_s01 · body_6hours_s03 · watson_q2_s01 · reveal_s02 · aftermath_det_s01 · aftermath_det_s02 · aftermath_watson_s01

---

## ⚠️ 세션 #36 절대 준수

1. **INVARIANT 3-Rule code-enforced** — agent prompt 에 Rule 1/2/3 블록 삽입, output JSON validation
2. **experiment Python scripts 폐기** — `produce_ryan_waller_v*.py` 만들지 마. 전부 `Agent(subagent_type="asset-sourcer")` 같은 spawn 방식
3. **QUERY_OVERRIDES 하드코딩 절대 금지** — Pexels query / Kling prompt / Runway prompt 전부 shot.text + shot.markers[*].maps_to 에서 runtime 추출
4. **Inspector 17 전부 spawn** — shorts-supervisor 가 fan-out, skip 금지. 신규 Inspector 대신 supervisor 내장 vision gate (33 상한 유지)
5. **CLAUDE.md 금기 11 전수 준수** — 33 agent 상한, T2V/Veo 금지, Selenium 금지, mockup 금지 등
6. **대본에 크리스마스 언급 = hook_s01 + reveal_s02 만** — 다른 shot 에 크리스마스 anchor 사용 금지

---

## 🗺️ 예상 경로 세션 #36 → #37

### 세션 #36 (7h 예상)
1. 대표님 3 결정 사항 확인
2. Phase 0 (30분) — Capsule template 확장
3. Phase 1 (3h) — 33 agent capsule 일괄 구조화 (FAILURES / skills / memory / AGENT.md patch)
4. Phase 2 (30분) — script_v6.json 재설계
5. Phase 3 (1h) — Type 1 실 자료 4 소스 확보
6. Phase 4 (2h) — Agent orchestration 실 제작 (voice-producer → asset-sourcer → subtitle-producer → assembler → 17 Inspector fan-out → render)
7. Phase 5 (30분) — 대표님 검수 + commit

### 성공 기준
- Opus Inspector 22/22 on-script (v5 는 8/22)
- v4 7 지적 + v5 추가 지적 전수 해결
- 대표님 눈/귀 검수 합격

### 예상 비용
- Kling T2I+I2V 12 shots × $0.73 = **$8.76** (balance 충전 전제)
- 또는 Runway Gen-3 Alpha Turbo fallback ~$10

---

## 📂 세션 #35 산출물 전수 경로

### Plan 파일 (세션 #36 entry point)
- `C:/Users/PC/.claude/plans/3-serene-sun.md` — v6 전체 아키텍처 + Phase 0~5 실행 순서 + Verification + 대표님 결정 사항 3개

### 실패 산출물 (재활용 가능)
```
output/.v4_backup_ryan-waller/
├── script_v5.json                # 22 shots + markers (재활용 base)
├── sources/real/raw_documentaries/ZI8G0KOOtqk_*.mp4   # Full Interrogation 65분 (Type 1 소스)
├── sources/intro_signature.mp4 + outro_signature.mp4  # 브랜드 시그니처
└── narration_v4.mp3              # TTS 참고용 (v6 재생성 가능)

output/ryan-waller/                # v5 실패 자산 (세션 #36 Phase 3 에서 삭제 or archive)
├── script_v5.json, narration_v5.mp3, final_v5.mp4 (74 MB, 실패)
├── inspect_v5/mid_frames/*.jpg (22 frame, Inspector 재진단 가능)
└── inspect_report_v5_diagnostic.md  # Opus 진단 8/22 on-script
```

### 스크립트 (폐기 예정)
- `scripts/experiments/produce_ryan_waller_v5*.py` (4 파일) — v6 에서 agent spawn 으로 대체
- `scripts/experiments/generate_ryan_waller_*_v4/v5.py` (여러 파일) — 로직은 skills/ 로 이관

---

*세션 #35 종료 — v4/v5 5회 render 실패 + Agent Capsule 미완 진단 + v6 정석 아키텍처 plan 확정. 세션 #36 에서 Phase 0~5 순차 진행, 정석대로 최상 품질.*
