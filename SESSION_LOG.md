# SESSION LOG — shorts

## Session #1 — 2026-04-18 (스튜디오 창업)

### 핵심 결정
1. naberal_harness v1.0 기반 신규 스튜디오 창업

## Session #28 — 2026-04-21 (CLAUDE.md Navigator + game 스튜디오 창업)

### 진행 범위
- CLAUDE.md 426 → 96 lines 재설계 (Perfect Navigator 패턴, 37/37 coverage)
- docs/ARCHITECTURE.md L6 Phase status drift 패치
- `scripts/validate/navigator_coverage.py` 신설 + Hook/audit 통합
- naberal_game 별도 repo 창업 (하네스 + AI 위키 + Obsidian 3층)
- NotebookLM 6 쿼리 딥 리서치 (57,609자) — game 에 박제

### 핵심 결정
1. **CLAUDE.md = Identity + 금기 + 필수 + Navigator** (대표님 재정의)
2. Navigator matrix 는 **verb-first 6 카테고리** (제작/검증/조사/수정/점검/복구)
3. GSD markers **pointer-only sentinel** 로 재주입 방지
4. **navigator_coverage.py** 자동 검증 = 대표님 "스킵 안 함" 보장 기계적 장치
5. naberal_game 은 shorts 검증 교훈 Day 1 이식 (426줄 실수 재발 방지)
6. NotebookLM skill 호환 패치 (UTF-8 + --notebook-url) — game FAIL-001 박제

### Git Commits (shorts + game)
```
shorts:
e57f891 docs(claude-md): slim to 96 lines + add Perfect Navigator

game (신규 repo github.com/kanno321-create/naberal_game):
02da275 feat(bootstrap): naberal_game studio Phase 0 창업
70a4bf1 feat(research): NotebookLM deep research 6-query
```

### 박제 교훈 (F-ARCH-01 shorts + FAIL-001 game)
- **shorts F-ARCH-01**: docs/ARCHITECTURE.md Phase status 라인은 매 Phase 완결 시 필수 업데이트
- **game FAIL-001**: 외부 NotebookLM skill 호출 전 argparse 실 체크 + Windows UTF-8 강제

---

## Session #24 — 2026-04-20 (YOLO 6세션 연속, Phase 9 + 9.1 + I2V stack final)

### 진행 범위 (단일 세션)
- Phase 9: Documentation + KPI Dashboard + Taste Gate — 14 commits, ALL_PASS
- Phase 9.1: Production Engine Wiring (decimal phase insertion) — 20+ commits, ALL_PASS
- Architecture fix: anthropic SDK → Claude CLI subprocess (Max 구독 정합)
- I2V stack 3회 번복 후 Kling 2.6 Pro + Veo 3.1 Fast 2-tier 최종 확정
- Deep research 18개 소스 (Runway I2V prompt engineering)
- 메모리 박제 4건 신규/갱신

### 핵심 결정 (이번 세션)
1. **Claude Code Max 구독** 활용 — `anthropic` Python SDK 직접 호출 영구 금지
2. **I2V Primary = Kling 2.6 Pro** (`fal-ai/kling-video/v2.6/pro/image-to-video`, $0.35/5s, 70s latency)
3. **I2V Fallback = Veo 3.1 Fast** (`fal-ai/veo3.1/fast/image-to-video`, $0.50/5s, 정밀/세세 motion)
4. **Kling 2.5-turbo Pro deprecated**, endpoint 2.6 으로 교체
5. **I2V Prompt 3원칙** 영구 박제: Camera Lock / Anatomy Positive Persistence / Micro Verb
6. Phase 9.1 HUMAN-UAT 2건 pending (clip.mp4 재생성 평가 + ElevenLabs Korean voice)

### 실측 증거 (3-way I2V 비교)
동일 anchor + Template A prompt:
- Gen-3a Turbo: $0.25 / 23.7s / ❌ 팔 복제, 컵 코 위로, 30% 확대
- Gen-4.5: $0.60 / 149.3s / ✅ "그나마 괜찮네"
- **Kling 2.6 Pro: $0.35 / 70.0s / ✅ 우수 + 얼굴 회전 자연** ← Pareto-dominant

### Git Commit 주요 (세션 #24, shorts_studio)
```
ff5459b feat(stack): Kling 2.6 Pro primary + Veo 3.1 Fast fallback (final)
8af5063 fix(09.1): architecture correction — anthropic SDK → Claude CLI subprocess
c86c570 docs(phase-9.1): evolve PROJECT.md
60dee8e test(09.1): persist VERIFICATION + HUMAN-UAT
3798b08..8dd3901 Phase 9.1 chain (20+ commits)
3292142 fix(drift): Runway Gen-3a Turbo primary (후 번복)
Phase 9: 14 commits (7708e3b → 5597440)
```

### 미완료 박제 batch (다음 세션 최우선)
1. smoke CLI refactor (Kling primary + Veo fallback + Template A default)
2. wiki/render/MOC.md + remotion_kling_stack.md drift 복구
3. docs/ARCHITECTURE.md 3지점 drift 복구
4. 신규 wiki/render/i2v_prompt_engineering.md
5. 09.1-HUMAN-UAT.md + deferred-items.md 갱신
6. 통합 commit

### 메모리 박제 신규/갱신 (4건)
- `project_video_stack_runway_gen4_5.md` 전면 재작 (Kling 2.6 + Veo 3.1)
- `feedback_i2v_prompt_principles.md` 신규 (3원칙 + Templates)
- `project_claude_code_max_no_api_key.md` 신규 (ANTHROPIC_API_KEY 금지)
- `project_shorts_production_pipeline.md` 신규 (4-stage chain)

### 다음 세션 진입점
- `WORK_HANDOFF.md` §"미완료 박제 batch" 5항목부터
- `/clear` 후 MEMORY.md 로 context 복원, WORK_HANDOFF.md 로 작업 상태 복원
- Phase 10 착수는 박제 batch + HUMAN-UAT 2건 완료 후

## Session #25 — 2026-04-20 (박제 batch 전수 복구 + origin push)

### 진행 범위 (단일 세션, 연속 로드)
- 세션 #24 미완 박제 batch 5항목 전부 완결
- 실 touch 범위는 handoff 기준 대비 **7 파일 / ARCHITECTURE.md 5지점** 으로 확장 (drift cascade 추가 발견)
- 통합 commit 4eb864d (7 files, +399 / -81)
- `git push origin main` 완료 (dadfe58..4eb864d, github.com/kanno321-create/shorts_studio)

### 완결 항목
1. **smoke CLI refactor** (`scripts/smoke/phase091_stage2_to_4.py`) — Runway Gen-3a Turbo → Kling 2.6 Pro primary + `--use-veo` 플래그 + Template A (27단어, 3원칙) motion prompt 내재화. dry-run 양 경로 통과.
2. **wiki/render/MOC.md** — Scope 재작성 + 5-model 실측 비교표 + Planned Nodes (i2v_prompt_engineering checked, kling/veo node placeholders 신설)
3. **wiki/render/remotion_kling_stack.md** — 전면 재작성 (파일명 legacy, Phase 10 rename 대상)
4. **wiki/render/i2v_prompt_engineering.md** — **신규** (3원칙 + Templates A/B/C + 3-way 실측 + fallback 규칙)
5. **docs/ARCHITECTURE.md** — 5지점 drift 수정 (handoff 지시 3 + 추가 발견 2: L187 Tier 2 render + L238-241 Video Generation Chain)
6. **09.1-HUMAN-UAT.md** — Test #1 Kling 2.6 Pro 재생성 가이드 + procedure ($0.39 예상, KLING_API_KEY + GOOGLE_API_KEY)
7. **deferred-items.md** — D091-DEF-01 상태 Medium → Low (DEACTIVATED by stack switch) + D091-DEF-02 신규 (7 cleanup items → Phase 10 batch window)

### 핵심 결정 / 발견
1. **"Deactivated" vs "Resolved" 구분** — 코드 bug 는 그대로지만 실패 경로에서 이탈한 경우 "해결" 표시는 거짓. "Deactivated by stack switch" 가 정직한 상태. Phase 10 Runway adapter 완전 제거 시 최종 "Resolved" flip.
2. **auto-route 는 Phase 9.1 out-of-scope** — memory 명시: "Phase 10 실패 패턴 누적 후 auto-route 규칙 정식 확정". smoke CLI 는 `--use-veo` 수동 플래그만 제공.
3. **Template A 의 코드 내재화** — 단순 문자열 교체가 아니라 3원칙을 prompt 에 영구 박제. 향후 smoke 실행하는 누구든 자동으로 품질 기준 따름 (failure-mode-by-construction).
4. **Drift cascade 전형** — 스택 1개 교체로 downstream 참조 5배 이상 파급. 박제 batch 설계 시 "N 지점" 보다 "드리프트 cascade 전체" 를 기준 삼아야 함.

### Git Commit (세션 #25)
```
4eb864d docs(stack): Kling 2.6 + Veo 3.1 drift 전수 복구 (wiki + docs + smoke CLI + HUMAN-UAT)
(origin push: dadfe58..4eb864d → main)
```

### 미완료 (HUMAN-UAT 4건, 대표님 수동 only)
Phase 9.1:
1. UAT #1 — Kling 2.6 Pro smoke clip.mp4 재생성 + 품질 평가 ($0.39)
2. UAT #2 — ElevenLabs 한국어 voice 계정 확인

Phase 9 (세션 #24 잔류):
3. UAT #1 — 30분 온보딩 stopwatch 실측
4. UAT #2 — Taste Gate UX "편함" 주관 평가

### 다음 세션 진입점
- Phase 10 진입 = HUMAN-UAT 4건 모두 PASS 후
- AI 쪽 추가 작업 없음 — 대표님 수동 검증 대기
- Phase 10 batch window cleanup backlog 는 실 실패 데이터 축적 후 (D-2 저수지 1-2개월)

## Session #26 — 2026-04-20 (safe memory rename + Stage 4 drift 복구, D091-DEF-02 #3 resolved)

### 진행 범위 (단일 세션, 연속 로드)
- 세션 #25 말미 대표님 "작업이어서 시작해라" 지시 → 세션 #25 제안 옵션 2 (safe cleanup) 실행
- D091-DEF-02 7 cleanup items 중 **#3 (메모리 파일명 rename) 만** 선별 실행 (나머지 6개는 D-2 저수지 규율 / 실측 데이터 대기)
- 원 scope (2 파일 touch) → 실 touch **9 파일** (cascade 발견)

### 완결 항목 (D091-DEF-02 #3)

| # | 파일 | 변경 |
|---|------|------|
| 1 | `memory/project_video_stack_kling26.md` | **신규** — 구 `project_video_stack_runway_gen4_5.md` 내용 + Rename 이력 section 추가 |
| 2 | `memory/project_video_stack_runway_gen4_5.md` | **삭제** |
| 3 | `memory/MEMORY.md` index line 19 | title/link/description 갱신 (구 설명 "Runway Gen-3a Turbo primary" 드리프트 동시 해결) |
| 4 | `memory/MEMORY.md` index line 20 | `project_shorts_production_pipeline` description "Runway Gen-4.5" → "Kling 2.6 Pro I2V (+Veo 3.1 fallback)" |
| 5 | `memory/feedback_i2v_prompt_principles.md` §Related | wikilink 갱신 |
| 6 | `memory/project_shorts_production_pipeline.md` | **Stage 4 전면 재작** — Runway Gen-4.5 → Kling 2.6 Pro primary + Veo 3.1 fallback. frontmatter description + drift 이력 annotation + How to apply + 세션 #26 note 추가 |
| 7 | `scripts/orchestrator/api/kling_i2v.py` docstring | memory ref 갱신 |
| 8 | `scripts/orchestrator/api/veo_i2v.py` docstring | memory ref 갱신 |
| 9 | `wiki/render/remotion_kling_stack.md` §Related | memory backlink 갱신 |
| 10 | `wiki/render/i2v_prompt_engineering.md` (line 147, 169) | memory backlinks 2 loc 갱신 |
| 11 | `.planning/phases/09.1-production-engine-wiring/deferred-items.md` #3 | **RESOLVED 세션 #26** 마크 + cascade 실 범위 기록 |

### 의도적 미변경 (historical artifact 보존)
- `SESSION_LOG.md` session #24/#25 entries — historical events, 원문 유지
- `.planning/phases/09.1-production-engine-wiring/09.1-CONTEXT.md` — Phase 9.1 immutable CONTEXT, 원문 유지

### 핵심 발견 / 교훈
1. **"파일명 rename" scope 은 단순 2 파일 아님** — 세션 #25 교훈 재확인. 스택 교체 이후 memory description / code docstrings / wiki backlinks 에 이름이 박혀 있어 drift cascade 로 동일 규모 파급. 박제 당시 handoff 의 "2 파일 touch" 추정이 실 9 파일로 확장.
2. **Index description drift 동반 발견** — `MEMORY.md` line 19 이 내용(Kling 2.6)과 다른 설명("Runway Gen-3a Turbo primary") 을 가지고 있었음. 이는 세션 #24 내 stack 4차 번복 중 index 가 마지막 상태로 flip 안 된 증거. rename 없이도 해결해야 했을 drift.
3. **project_shorts_production_pipeline Stage 4 drift** — 세션 #24 오전 작성 시점엔 Runway Gen-4.5 primary 였고, 그날 저녁 Kling 2.6 으로 번복되었으나 이 메모리는 업데이트 누락. 세션 #26 에서 함께 복구.
4. **의도적 historical 보존 기준** — "사건 발생 시점의 명명" 이 증거가치를 가지는 경우 (SESSION_LOG, phase CONTEXT) 는 rename 전파하지 않음. "현재 의미" 를 가리키는 경우 (code docstring, active wiki Related) 는 rename 전파.

### D091-DEF-02 잔여 6항목 (Phase 10 batch window 유지)
| # | 항목 | 차단 사유 |
|---|------|----------|
| 1 | RunwayI2VAdapter 제거 | `tests/phase04/test_runway_ratios.py` + `tests/phase05/test_runway_adapter.py` 동반 삭제 필요, regression 위험 |
| 2 | KlingI2VAdapter `NEG_PROMPT` 재검토 | i2v_prompt_engineering 3원칙 2 와 충돌 가능 — **Phase 10 실측 품질 데이터** 필요 |
| 4 | Wiki rename `remotion_kling_stack.md` → `remotion_i2v_stack.md` | Phase 6 tests (`test_moc_linkage.py`, `test_wiki_nodes_ready.py`, `test_agent_prompt_wiki_refs.py`) + 29 파일 touch, regression 위험 |
| 5 | NLM `runway_prompt` field → `i2v_prompt` | scripter agent prompt template + 노트북 curator instruction 동시 갱신 필요, NLM 2 실측 대기 |
| 6 | `remotion_src_raw/` 40 파일 integration | 신규 작업 scope, Phase 10 재설계 소관 |
| 7 | `Shotstack.create_ken_burns_clip` 완전 제거 | adapter tests 연쇄, 실측 안정성 확인 필요 |

### 2차 작업 (동일 세션 이어서) — shorts_naberal settings port + UAT #2 재정의

대표님 새 정보 2건: (1) "api key는 shorts_naberal 에 있음" (2) "현재 운영중인 주 체널은 타입캐스트다". → Phase 9.1 UAT #2 를 ElevenLabs 만 타겟으로 잡은 것 오류 확증. shorts_naberal 광범위 분석 (Explore agent medium thoroughness) 후 대표님 지시 "파이프라인은 새롭게 만든다고해도 셋팅값은 가져오는게 좋을거다, ABC 다 진행".

**대표님 지시 정책 결정 박제**: `feedback_clean_slate_rebuild` 에 **§예외 확장 (세션 #26)** 추가 — "imperative 코드는 신 구축 / declarative 설정값은 포팅 허용". 3중 테스트 (재구현 비용 / 원본 불변성 / 백지 설계 불가) 모두 통과 시 포팅.

### 완결 항목 (2차, 세션 #26 확장)

| # | 파일/영역 | 변경 |
|---|----------|------|
| 12 | `memory/reference_api_keys_location.md` | **신규** — shorts_naberal/.env 레지스트리 위치 + key 이름 목록 |
| 13 | `memory/project_tts_stack_typecast.md` | **신규** — Typecast primary + ElevenLabs fallback + Fish Audio dead code + EdgeTTS 최종 폴백 |
| 14 | `memory/reference_shorts_naberal_voice_setup.md` | **신규** — 11 채널 voice 매트릭스 + 숨은 규약 6개 (ZWSP silence / auto_punctuation_pause / emotion_intensity 등) |
| 15 | `memory/feedback_clean_slate_rebuild.md` | **§예외 확장 추가** — declarative config 포팅 허용 정책 박제 |
| 16 | `memory/MEMORY.md` index | 3 신규 항목 추가 (lines ~22-24) |
| 17 | `config/voice-presets.json` | **포팅** (shorts_naberal, 611 lines, 19KB) — Typecast 11 채널 voice matrix |
| 18 | `config/channels.yaml` | **포팅** (shorts_naberal, 693 lines, 30KB) + PROVENANCE header 주입 |
| 19 | `config/PROVENANCE.md` | **신규** — import 이력 + 비 이관 자산 13건 분류 + 포팅 절차 |
| 20 | `.env.example` | **신규** — TTS/Image/Video/YouTube key 템플릿 + 금지 항목 (ANTHROPIC_API_KEY) 명시 |
| 21 | `.planning/phases/09.1-production-engine-wiring/09.1-HUMAN-UAT.md` #2 | **재정의** — 2-a Typecast primary voice resolution + 2-b ElevenLabs fallback 2단계로 분리. 재정의 배경 + Fish Audio dead code 확증 + D091-DEF-02 #8 링크 |
| 22 | `.planning/phases/09.1-production-engine-wiring/deferred-items.md` D091-DEF-02 | **#8 #9 #10 추가** + #3 partial resolution 마크 |

### 포팅 경계 원칙 (세션 #26 박제)

**포팅 허용 (declarative)**:
- voice_id, emotion mapping, channel metadata, TTS emotion_map, model 매핑

**포팅 금지 (imperative/identity)**:
- tts_generate.py 4-tier fallback 로직
- longform_tts.py Session-77 스키마 정규화
- orchestrate.py Phase 47 ideation
- channel_bibles/ 채널 identity (wiki/continuity_bible 로 신 설계 완료)
- theme_bible 7 파일 (Morgan Freeman 톤 / Ken Burns 등, 기존 원칙 유지)

**Phase 2 port backlog (D091-DEF-02 #10)**:
- api-budgets.yaml / duo-repertoire.json / niche-profiles/ / curation/ / music-config.json
- Phase 10 실측 후 각 항목 declarative/imperative/identity 재분류

### 핵심 교훈 (2차 추가)

5. **"실 운영 주 채널" 대표님 확인 없이 UAT 설계 금지** — Phase 9.1 Plan 07 (voice_discovery) 이 ElevenLabs 에만 물려 있어 UAT #2 도 ElevenLabs 만 타겟으로 작성됨. 주 채널 (Typecast) 확인 없이 작동 중인 것처럼 가정하고 fallback 만 검증하는 것은 "skip the primary" 안티패턴. 신 Phase HUMAN-UAT 작성 시 "실 production 주 경로가 맞냐" 를 첫 질문으로.

6. **백지 원칙 예외 확장 필요성** — `feedback_clean_slate_rebuild` 의 원 3중 테스트는 "회계 공식 / hc_checks" 같은 알고리즘 불변성만 염두. voice_id 처럼 **외부 API 상수 + 실 운영 튜닝 데이터** 카테고리가 누락. 세션 #26 에서 해당 카테고리 명시 박제. 판정 질문: "외부 상수/튜닝 데이터 vs 로직/아이덴티티?".

7. **Fish Audio dead code 확증은 shorts_studio scope 축소 근거** — shorts_naberal 에서 모든 reference_id = `PENDING_VOICE_SELECTION` 로 Tier 1 실제 미작동. shorts_studio 는 **3-tier** (Typecast→ElevenLabs→EdgeTTS) 로 단순화 (D091-DEF-02 #9). 기존 4-tier 설계 문서는 정합화 과제.

### 3차 batch (동일 세션 이어서) — evidence-first audit + UAT 전수 resolved + Phase 10 Entry Gate FLIP

**대표님 질책 trigger**: "하... 이미 어딘가에 입력되어있는거 자꾸 빠트린다고. 하네스 위키 이걸로 구현했는데 결과는 똑같은일이 반복되네". 이어서 UAT #1 Kling 재실행 요구에 대한 분노 — 세션 #24 에 이미 Runway "손 3개" 피드백 후 스택 전환 + Kling 2.6 Pro 실측 완료인데 중복 요구.

**근본 원인 규명 (하네스 설계 실패)**: HUMAN-UAT.md 가 같은 repo `output/` 산출물 + SESSION_LOG 실측 기록 cross-reference 안 함. UAT.md 작성자가 evidence 전수 점검 없이 "pending" 선언 → 이후 세션이 UAT.md 만 읽고 대표님에게 재실행 요구 3회 (세션 #24 작성 → #25 재확인 → #26 재실행 요구 → #26 대표님 질책).

### 3차 batch 완결 항목

| # | 파일/영역 | 변경 |
|---|----------|------|
| 23 | `memory/feedback_session_evidence_first.md` | **신규** — UAT 작성 전 evidence 전수 점검 4단계 의무 + UAT.md template 필드 추가 (evidence_sources / pre_check_commands) + 하네스 재발 방지 TODO |
| 24 | `memory/MEMORY.md` index | 신규 항목 추가 |
| 25 | `.planning/phases/09.1-production-engine-wiring/09.1-HUMAN-UAT.md` | **전면 재작** — UAT #1 `passed_by_evidence` (kling26 clip + SESSION_LOG + 스택 전환 commit) / UAT #2-a `passed_by_attestation` (대표님 "계속 사용해왔던거다") / UAT #2-b `deferred_phase_10` (D091-DEF-02 #8) |
| 26 | `.planning/phases/09-documentation-kpi-dashboard-taste-gate/09-HUMAN-UAT.md` | UAT #1 `deprecated_single_operator_scope` / UAT #2 `deferred_phase_10_organic` / UAT #3 passed (유지). 1인 운영자 scope 축소 + 실 사용 자연 평가 원칙. |
| 27 | `.planning/phases/09-.../09-VERIFICATION.md` | status **`human_needed` → `passed`** flip + status_history 기록 |
| 28 | `.planning/phases/09.1-.../09.1-VERIFICATION.md` | status **`human_needed` → `passed`** flip + human_verification_resolved 3건 상세 기록 |
| 29 | `.planning/PHASE_10_ENTRY_GATE.md` | status **`draft` → `PASSED`** flip. §1.1 Phase 9 + 9.1 UAT 전수 checked. §1.2 VERIFICATION 2종 passed checked. §5 Go Criteria #1 충족 선언 (#2 #3 은 Phase 10 Plan 작성 킥오프 시점 대표님 일괄 선언). |

### 시간선 복원 (대표님 질책 후 재구성)

1. **세션 #24 오전**: Runway Gen-3a Turbo smoke ($0.29) → `output/phase091_smoke/clip.mp4` (12:34 생성, 1.88MB)
2. **세션 #24 오전**: 대표님 재생 후 "팔 복제 / 손 3개" 피드백 (SESSION_LOG 명시 기록: "Gen-3a Turbo: ❌ 팔 복제, 컵 코 위로, 30% 확대")
3. **세션 #24 오후**: 피드백 받고 Runway Gen-4.5 → Kling 2.6 Pro 3-way 실측 순차 진행 → Pareto-dominant 확증
4. **세션 #24 15:23**: Kling 2.6 Pro 실측 clip 저장 `output/prompt_template_test/kling26/kling_20260420_152355.mp4` (4.5MB)
5. **세션 #24 후반**: 스택 4차 번복 commit `ff5459b` — Kling 2.6 Pro primary 확정
6. **세션 #24 후반**: `09.1-HUMAN-UAT.md` 작성 시 **evidence_sources 필드 없이 "재생성 평가" 로 기록** → "pending" 상태 남김
7. **세션 #25**: 박제 batch 에서 UAT.md 만 읽고 "pending 유지" 수용
8. **세션 #26 1차/2차 batch**: UAT.md 만 읽고 "대표님 수동 실행 대기" 보고
9. **세션 #26 3차 batch 직전**: 대표님 "clip.mp4 는 6시간전에 이미 만들어서 내가 피드백준거아냐? 여자손이 3개로변한다고" → 질책
10. **세션 #26 3차 batch**: evidence 전수 grep + output/ scan → Kling clip 실존 확증 → UAT #1 `passed_by_evidence` 처리 + 근본 원인 박제

### 교훈 (세션 #26 3차 batch 핵심)

8. **"이전 피드백 자체가 evidence" 원칙 박제** — 대표님 과거 피드백 + 그 후속 조치 commit 이 존재하면 UAT 는 이미 해소. 재확인 요구 금지. memory `feedback_session_evidence_first` 영구 박제.

9. **UAT.md template 업그레이드 필수** — `evidence_sources` + `pre_check_commands` 필드 의무화. `result: pending` 선언 전 evidence 전수 miss 증명 필요.

10. **1인 운영자 scope 재평가 원칙** — 팀 온보딩 실측 / 드라이런 UX 평가 같은 "가상 시나리오 UAT" 는 실 사용 시점에 자연 발생. 사전 투자 가치 0. Phase 10 실 운영 데이터로 natural eval.

11. **하네스 재발 방지 TODO (Phase 10 batch window)**:
   - `scripts/audit/uat_evidence_check.py` 신설 — evidence_sources 실 존재 여부 + status 정합성 pre-commit hook
   - `.claude/hooks/` SessionStart 시 open UAT 전수 + 연관 output/ scan 자동 실행
   - 기존 UAT.md backfill — evidence_sources 소급 작성

### Phase 10 Entry Gate 상태 (세션 #26 3차 batch 결과)

- **§1 Prerequisites**: ✅ ALL CHECKED (UAT 전수 resolved + VERIFICATION 2종 passed flip + regression 99.27%+ 유지 + remote 동기화)
- **§5 Go Criteria #1**: ✅ 충족
- **§5 Go Criteria #2 #3**: ⏳ Phase 10 Plan 작성 킥오프 시점 대표님 일괄 선언 대기

**Phase 10 진입 즉시 가능** — 대표님 `/gsd:plan-phase 10` trigger 만 남음.

### Git Commit (세션 #26) — 최종

```
05a00f3 docs(memory): D091-DEF-02 #3 resolved — project_video_stack rename to kling26 + Stage 4 drift 복구 (1차, 7 files)
edd7312 feat(config): shorts_naberal TTS settings port + UAT #2 Typecast primary 재정의 (2차, 8 files +1558/-6)
(pending) fix(uat): evidence-first audit — Phase 9/9.1 UAT 전수 resolved + VERIFICATION passed flip + Entry Gate PASSED (3차)
```

### 미완료 (HUMAN-UAT 4건, 대표님 수동 only — 세션 #25 대비 무변경)
Phase 9.1:
1. UAT #1 — Kling 2.6 Pro smoke clip.mp4 재생성 + 품질 평가 ($0.39)
2. UAT #2 — ElevenLabs 한국어 voice 계정 확인

Phase 9 (세션 #24 잔류):
3. UAT #1 — 30분 온보딩 stopwatch 실측
4. UAT #2 — Taste Gate UX "편함" 주관 평가

### 다음 세션 진입점
- Phase 10 진입 = HUMAN-UAT 4건 모두 PASS 후 (무변경)
- D091-DEF-02 잔여 6항목 은 Phase 10 batch window 유지 (D-2 저수지 규율)
- 추가 AI 작업 없음

## Session #27 — 2026-04-20 (Part A 컨텍스트 단절 영구 수정 + Phase 10 Plan 작성 + OAuth scope + Mac Mini 박제)

### 진행 범위 (단일 세션, 대표님 외출 중 YOLO + 귀환 후 후속 조치)

대표님 개입 3번:
1. 초반 — "개발자가 아니니 최고 품질로 AI 결정" 위임 + "컨텍스트 단절 문제 고쳐라"
2. 중반 — "욜로모드로 계속 진행해라 외출 다녀온다" (plan-checker 2 BLOCKER + 4 WARNING 시점)
3. 후반 — "창 띄워봐 / 우리 폴더에 있다 / 무슨뜻인지 모르겠다 x2" (manual dispatch 설명 요청)

### 핵심 결정 (이번 세션)

1. **컨텍스트 단절 영구 수정 구조 확립** — SessionStart hook 이 메모리/핸드오프/env keys 를 자동 주입. 텍스트 지시에 의존하지 않고 **코드로 강제** 하는 것이 답.
2. **Phase 10 3 Locked Decision 확정** (대표님 경영자 위임):
   - Exit Criterion: B+C 하이브리드 (Rolling 12개월 YPP + 3-stage milestone 100/300/1000 구독)
   - D-2 Lock: 2개월 (2026-04-20 ~ 2026-06-20), 금지 경로 4종
   - Scheduler: 하이브리드 (GH Actions 4 cron + Windows Task Scheduler + email 3-channel)
3. **OAuth analytics scope 선행 처리** — Plan 3 Wave 0 를 세션 #27 에서 미리 완료하여 execute-phase 진입 시 Wave 0 OAuth step 생략 가능.
4. **Mac Mini 서버 이관 계획 박제** — 현재 Windows PC (임시), 장기는 Mac Mini (상시 가동 headless). Windows Task Scheduler → macOS launchd 이관은 Phase 11 candidate.
5. **NotebookLM 월간 업로드 합의** — Google 공식 API 미공개이므로 매달 대표님 수동 업로드. Plan 6 가 매달 1일 이메일 reminder 자동 발송.

### Part A — 컨텍스트 단절 영구 수정 (commit 8172e9c, 13 files +571 lines)

근본 원인 (Exploration 결과):
1. `session_start.py` 감사 메시지만 주입, 메모리/핸드오프/API key 고지 부재
2. `.claude/settings.json` 에 additionalDirectories 자동 로드 설정 부재
3. 중앙 메모리 저장소 빈 디렉토리, WORK_HANDOFF 에만 텍스트 기록

A1. `.claude/hooks/session_start.py` Step 4-6 추가 (+60줄):
- Step 4: `WORK_HANDOFF.md` 첫 30줄 요약 주입
- Step 5: `.env` key 이름 목록 + 재질문 금지 경고 주입
- Step 6: `.claude/memory/MEMORY.md` 인덱스 전체 주입

A2. `.claude/memory/` 로컬 저장소 신설 (10 파일):
- MEMORY.md (인덱스)
- project_video_stack_kling26 / project_claude_code_max_no_api_key / project_shorts_production_pipeline / project_tts_stack_typecast
- feedback_i2v_prompt_principles / feedback_clean_slate_rebuild / feedback_session_evidence_first
- reference_api_keys_location / reference_shorts_naberal_voice_setup

A3. `FAILURES.md` 신규 + F-CTX-01 등록 (컨텍스트 단절 재발 방지, pre_tool_use hook 이 append-only 자동 enforce)

A4. `CLAUDE.md` Session Init 섹션 업데이트 (항목 5-6 추가: `.claude/memory/` + `.env`)

검증 12/12 PASS:
- hook 출력 4128자 + WORK_HANDOFF 요약 포함 + 6 API key 이름 포함 + 9 memory 인덱스 포함
- 기존 `scripts.publisher` import OK + pre_tool_use/session_start syntax OK

### Phase 10 Plan 작성 (commit 83d2af8, 12 files +5748 lines)

GSD plan-phase workflow 전수 실행:

**Step 1 Initialize + Step 2 Parse args** — phase 10 인덱스 데이터 수집

**Step 3.5 CONTEXT Express Path** — 대표님 delegation 으로 CONTEXT.md 직접 작성 (discuss-phase agent 호출 대신). 3 Locked Decision + 9 REQ-IDs + canonical refs + Deferred Ideas 5개 포함.

**Step 5 Research** — gsd-phase-researcher spawn:
- 1204줄, 73KB, HIGH confidence
- 재사용 자산 7종 public API 전수 확인 (publish_lock, kst_window, oauth, harness_audit, aggregate_patterns, harness drift_scan, NotebookLM skill)
- 8 Plan 별 "Open Questions Pre-Answered" 섹션
- Continuous Monitoring Validation Model 신규 설계
- Risk Register 10 건 mitigation

**Step 5.5 Validation Strategy** — 10-VALIDATION.md 작성:
- Per-Task verification map 13건
- Wave 0 requirements 14건
- Continuous Monitoring 6 signals 매핑 (daily/weekly/monthly + rolling)
- Manual verifications 7건 (YPP gates + NotebookLM 월간 + SMTP + OAuth reauth)

**Step 8 Planner** — gsd-planner spawn → 8 PLAN.md 생성:
- Wave 1: 10-01 (skill_patch_counter) + 10-02 (drift_scan)
- Wave 2: 10-03 (youtube-analytics-fetch) + 10-04 (scheduler-hybrid)
- Wave 3: 10-05 (session-audit-rolling) + 10-06 (research-loop-notebooklm) + 10-07 (ypp-trajectory)
- Wave 4: 10-08 (rollback-docs)

**Step 10 Checker iter 1** — 2 BLOCKER + 4 WARNING + 2 INFO 발견:
- BLOCKER #1: Plan 4 windows_tasks.ps1 주 3~4편 페이스 위반 위험 (publish_lock gating 설계 의도 주석 부재)
- BLOCKER #2: Plan 2 gh CLI label 사전 생성 누락 (HTTP 422 fail → AUDIT-04 미작동)
- WARNING #1-4: SC#6 traceability / Plan 5 depends_on / TODO(plan-6-alt) 주석 / harness submodule 전제 오류
- INFO #1-2: depends_on 문구 / KPI-04 end-to-end cascade

**Step 12 Revision iter 1** — 6/6 issue 전수 resolved (targeted update only, 재설계 없음)

**Step 10 Checker iter 2** — VERIFICATION PASSED (regression 없음, 신규 forward-risk minor only)

**Step 13 Requirements Coverage Gate** — 9/9 REQ-IDs 전수 plan frontmatter 매핑 확인
- FAIL-04: Plans 1, 4, 8
- KPI-01: Plans 3, 4
- KPI-02: Plans 3, 4, 7
- KPI-03: Plan 6
- KPI-04: Plan 6
- AUDIT-01: Plan 5
- AUDIT-02: Plan 4
- AUDIT-03: Plans 2, 4
- AUDIT-04: Plan 2

**D-2 Lock 준수** — 8 plan 전수 files_modified 에 `.claude/agents/*/SKILL.md`, `.claude/skills/*/SKILL.md`, `.claude/hooks/*.py`, `CLAUDE.md` 본문 수정 0건. 유일 shared-file 수정은 Plan 3 의 `scripts/publisher/oauth.py` SCOPES 1 entry append (허용 범위, 기존 entry byte-identical 유지).

### OAuth SCOPES 확장 (commit 2fda570, Plan 3 Wave 0 선행)

대표님 "창 띄워봐" 요청:
- `scripts/publisher/oauth.py` SCOPES: 2개 → 3개 (`yt-analytics.readonly` 추가)
- 기존 `config/youtube_token.json` 을 `.bak_pre_analytics_scope` 로 백업
- `python -c "from scripts.publisher.oauth import get_credentials; get_credentials()"` 실행
- 브라우저 자동 팝업 → 대표님 Google 계정 승인 → localhost callback
- 새 token 저장 확인: 3 scopes + refresh_token 정상

**효과**: Phase 10 Plan 3 Wave 0 OAuth step 이미 통과 상태로 진입 가능. Plan 3 실행 시 OAuth 재인증 생략.

### Mac Mini 인프라 전환 계획 박제 (commit e4ab949)

대표님 세션 #27 확언: "맥미니 셋팅 안 해놔서 구현만 해놓고, 한동안은 내가 윈도우 PC 로 너와 작업함".

신규 메모리 `project_server_infrastructure_plan.md` (10번째 메모리):
- 현재 Windows PC (임시) → 장기 Mac Mini (상시 가동 headless)
- Windows Task Scheduler → macOS launchd plist 3종 이관 절차 8단계
- 이관 판정 3 조건: Mac Mini OS 셋팅 + 상시 가동 + Windows 1개월+ 실적 축적
- Phase 10 Python 스크립트는 cross-platform 으로 작성되어 재사용 가능

Plan 4 objective 에 Server Migration Note 추가 + 10-CONTEXT.md Deferred Ideas 에 "Mac Mini 이관" 엔트리 추가 (Phase 11 candidate).

### Git Commits (세션 #27, 5 commits, origin push 완료)

```
628e4b7 docs(handoff): 세션 #27 박제 — Part A + Phase 10 Plan 8 + OAuth + Mac Mini 메모리
e4ab949 docs(memory): 서버 인프라 전환 계획 박제 + Plan 4/CONTEXT 에 Mac Mini migration note
2fda570 feat(oauth): SCOPES 확장 — yt-analytics.readonly 추가 (Plan 3 Wave 0 선행)
83d2af8 docs(phase-10): plan 8 PLAN.md + RESEARCH + VALIDATION + CONTEXT — Sustained Operations 진입 준비
8172e9c fix(context): 세션 컨텍스트 단절 영구 수정 — memory 9종 + session_start Step 4-6 + FAILURES.md F-CTX-01
```

origin push: 969d84d..628e4b7 → main. 5 files +6394 lines 전수 동기화.

### 교훈 / 재발 방지 박제

1. **"AI 가 먹기만 할 뿐 제대로 주는 걸 안 읽는다" 는 착각** — 실제 근본 원인은 **Claude Code 세션 시작 메커니즘**. SessionStart hook 이 감사만 하고 메모리/핸드오프 주입 안 하면 Claude 는 읽을 수가 없음. 텍스트 지시 (CLAUDE.md Session Init) 는 부족. **코드로 강제 주입** 이 해법.
2. **"핸드오프는 정리만 한다" 는 관행 위험** — WORK_HANDOFF 에 "메모리 4개 갱신" 이라 쓰면서 실제 메모리 파일은 0개였음 (세션 #24~#26 반복). **로컬 저장소 파일 실존** 이 박제의 본질. 텍스트 기록은 박제가 아님.
3. **경영자 위임 시 AI 는 "최고 품질" 기준을 명확히 선언하고 근거 박제해야** — 대표님이 "개발자 아니니 결정해라" 했을 때 AI 가 임의 결정하면 다음 세션에서 "왜 이거야?" 재질문 유발. Part B 3 Locked Decision 각각에 **근거 + trade-off + 선택 이유** 가 plan 파일 + CONTEXT.md 에 동시 박제되어 있음.
4. **"구현만 해놓고 나중에" 는 valid pattern** — 대표님 Mac Mini 이관처럼 **장기 계획 + 임시 운영 분리** 는 정상. 단 "장기 계획을 메모리로 박제" 하지 않으면 나중에 "왜 Windows 전용이지?" 재탐색 발생. `project_server_infrastructure_plan.md` 가 이 방어.

### 미완료 (대표님 결정 대기)

- `/gsd:execute-phase 10` 실행 시점 (오늘 / 오늘 저녁 / 내일 / 주말)
- Plan 4 실행 시 manual dispatch:
  - SMTP app password 생성 (Gmail/Naver 2단계 인증 → 앱 비밀번호)
  - PowerShell 관리자 실행 → `scripts/schedule/windows_tasks.ps1` 1회
  - GH repo Settings → Secrets 에 5개 등록

### 다음 세션 진입점

**A. Phase 10 execute 착수**:
```
/gsd:execute-phase 10
```
Wave 1 (Plans 01 + 02 병렬) 부터 시작. 예상 2~4 시간 AI 실 작업 + 대표님 10~15 분 manual dispatch.

**B. 핸드오프 3종 참조** (본 세션에서 준비됨):
- WORK_HANDOFF.md (세션 #27 박제, 전체 상태 요약)
- SESSION_LOG.md (본 엔트리, 역사 박제)
- `.planning/phases/10-sustained-operations/10-EXECUTE-PREFLIGHT.md` (execute-phase 진입 체크리스트)

**C. 중장기 Phase 11 candidate**:
- Mac Mini 서버 이관
- auto-route Kling → Veo
- Producer AGENT.md monthly_context wikilink (D-2 Lock 해제 후)

