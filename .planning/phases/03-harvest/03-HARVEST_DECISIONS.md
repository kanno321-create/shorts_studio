# HARVEST_DECISIONS — Phase 3 전수 판정 결과

**Source:** `.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md` (A급 13 사전 판정)
**Generator:** `scripts/harvest/decision_builder.py` (5-rule algorithm, B/C 26 판정)
**CONFLICT_MAP:** 39 entries (A:13 verbatim + B:16 + C:10 algorithm)

## 5-rule 알고리즘 (B/C 26 적용)

1. Harvest blacklist match → 폐기
2. Scope boundary (longform/incidents_jp/worktree/duo_japan) → 폐기
3. Session 77+ canonical forms → 승계 신형
4. C-class + cosmetic cleanup (gitignore/worktree_copy/.tmp_/_backup_) → cleanup
5. Default → 통합-재작성

## 39 전수 판정 테이블

| ID | 드리프트 요약 | 판정 | 근거 | 실행 지시 |
|----|---------------|------|------|-----------|
| A-1 | Runway vs Kling primary | **통합-재작성** (Kling primary + Runway backup) | D-3 STACK §Visual, SUMMARY §2 (Kling 2.6 Pro + Runway Gen-3 Alpha Turbo backup) | Phase 4 video-sourcer 에이전트가 Kling primary, Runway fallback 체인 구현. 원본 `config/stock-search-config.json`은 승계 금지 (2개 노트 충돌 상태) |
| A-2 | cuts[] vs segments[] 스키마 | **승계** (cuts[] canonical) | 세션 77 실측 사용 `longform_script.json` + `script-converter/AGENT.md` 캐노니컬화 | Phase 4 scripter 에이전트가 `cuts[]/narration` 스키마만 출력. `segments[]/text` 역정규화 코드는 Phase 5 `longform_tts.py` 재작성 시 제거 |
| A-3 | researcher vs NLM-fetcher 진입점 | **통합-재작성** (NLM-fetcher 승계, researcher 폐기) | D-4 NotebookLM RAG, 세션 77 `CLAUDE.md:105-131` "🔴 최초공정은 NLM 2-노트북" | Phase 4 agent 팀에 `nlm-fetcher` 기본 + `researcher`(fallback only). `.claude/skills/create-shorts/SKILL.md:233,253` 전면 재작성 |
| A-4 | unique 60/80/100% 기준 | **통합-재작성** (ins-license 단일 ≥80% 기준) | SUMMARY §7 Reviewer 카테고리, NotebookLM T15 LogicQA Main-Q+Sub-Qs 다수결 | Phase 4 `ins-license`만 구현 (기존 `ins-matching`의 unique 항목 삭제 + `ins-duplicate` 완전 폐기). 단일 검사관, 단일 기준 |
| A-5 | TODO(next-session) 4곳 미연결 | **전수 폐기** | D-6 pre_tool_use regex 차단, AF-14 `TODO(next-session)` 금지 | Phase 3 harvest-importer는 `orchestrate.py` 자체를 `api_wrappers_raw/`에 복사조차 금지. Phase 5에서 state machine 새로 작성. Hook이 문자열 자체 차단 |
| A-6 | skip_gates=True 디버그 경로 | **전수 폐기** | D-6 3중 방어선, D-7 state machine, AF-14, SUMMARY §8 #3 pitfall | `orchestrate.py:1239-1291` 블록은 harvest blacklist 확정. Phase 5 `shorts_pipeline.py` state machine은 `skip_gates` 파라미터 자체 부재 |
| A-7 | Morgan tempo 0.93 vs 0.97 | **통합-재작성** (0.93 canonical) | `DESIGN_BIBLE.md:179` 7.9자/초 계산 기준점 | Phase 4 voice-producer 에이전트가 0.93 고정. `config/voice-presets.json` 승계 시 `voice_pools.incidents.narrator.audio_tempo=0.97` 필드 제거 |
| A-8 | "놓지 않았습니다" 시그니처 | **통합-재작성** (조건부 허용 = ins-structure 규칙) | 세션 77 최종 확정본 `ins-structure/AGENT.md:143,159` | Phase 4 `ins-structure` 에이전트가 "Part1/마지막편만 허용, 중간편 금지" 규칙 구현. 기존 `scripter/FAILURES.md:124-130` FAIL-SCR-010은 deprecated 마킹 |
| A-9 | "탐정님" 호명 금지 | **승계** (호명 금지 규칙) | 17일 `voice/AGENT.md:64-73`, memory `feedback_assistant_no_detective_honor` | Phase 4 `ins-korean-naturalness` 또는 `ins-duo`가 "탐정님" regex 차단. 듀오 대화 가이드에 명시 승계 |
| A-10 | "조수" vs "마스코트" 명칭 | **통합-재작성** ("조수" 통일, config key `assistant`) | 세션 77 `CLAUDE.md`, `PIPELINE.md:10,98` "마스코트" 제거 방향 확정 | Phase 3 harvest 시 longform/ 경로는 이관 대상 아님 (쇼츠만). shorts 관련 `channels.yaml` 만 참조하여 config key 를 `assistant` 로 재작성, 표시명 "조수" 통일 |
| A-11 | longform-scripter.md 2곳 충돌 | **전수 폐기** (shorts 스코프 외) | 본 스튜디오는 shorts 전용, D-10 주 3~4편 쇼츠 확정 | Phase 3 harvest에서 `shorts_naberal/longform/` 디렉토리 전체 스킵. `longform/longform-scripter.md` + `longform/agents/longform-scripter.md` 양쪽 모두 import 금지 |
| A-12 | create-shorts vs create-video 진입점 | **통합-재작성** (create-shorts 승계, create-video 폐기) | A-3과 연결, shorts 전용, 세션 77 `subtitle_generate.py:515` shorts 런타임 차단 | Phase 4 에이전트 설계 시 `create-shorts` 스킬 재작성, `create-video` 는 harvest blacklist. 오용 시 차단된 `subtitle_generate.py` 호출 → 예외 발생 방지 |
| A-13 | 영상 소스 우선순위 (Veo 5개 vs Runway 6~8) | **통합-재작성** (Kling primary → Runway backup only, Veo 미사용) | SUMMARY §2 STACK 확정, AF-10 sweet spot 연결, Cost $0.07~0.14/sec | Phase 4 video-sourcer 프롬프트가 Kling 단일 primary + Runway fallback 만. Veo 완전 배제 (cost + I2V 일관성). `DESIGN_BIBLE.md` DB-01 + `longform/PIPELINE.md:97` 참조 금지 |
| B-1 | longform 길이 표준 — 13-15분 vs 13-18분 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-2 | 쉼표 pause 시간 — 250ms vs 300-400ms | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-3 | incidents_jp 보이스 — Fish Audio vs VOICEVOX Nemo | **폐기** | rule 2: scope boundary (incidents_jp) | Phase 4+ 에이전트 설계 시 rule 2 적용 |
| B-4 | visual_mode 3종 — photorealistic vs t2i_i2v vs character_art | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-5 | duo 조수 비율 — 15-30% vs 20-35% vs 30% vs 20-40% | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-6 | longform/config/channels.yaml loop_layer_enabled 드리프트 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-7 | inspectors maxTurns 규칙 없음 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-8 | Stage 4 TTS 스크립트 스키마 vs script-converter 출력 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-9 | paperclip 스킬 구형 잔존 (orchestrate.py 호출) | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-10 | Pexels 언급 잔존 (shorts-video-sourcer SKILL) | **폐기** | rule 1: blacklist match (scripts/orchestrator/orchestrate.py) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-11 | docs 파일 3개 동시 기록 — WORK_HANDOFF / SESSION_LOG / NEXT_SESSION_PROMPT | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-12 | CLAUDE.md 파이프라인 요약 — 3박스 혼재 | **폐기** | rule 1: blacklist match (.claude/skills/create-shorts/SKILL.md) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-13 | longform 길이 상한 DESIGN_BIBLE "120s 상한" vs 채널별 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-14 | ins-duplicate vs ins-license 역할 겹침 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| B-15 | `.tmp_nlm/` 디렉토리 커밋됨 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| B-16 | audio-pipeline 하이픈 디렉토리 (sys.path.insert 4곳) | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| C-1 | `NLM_PROMPT_GUIDE.md` 루트 배치 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| C-2 | `_fun_summary_frames/` 루트 디렉토리 | **cleanup** | rule 4: cosmetic cleanup (gitignore) | Phase 4+ 에이전트 설계 시 rule 4 적용 |
| C-3 | 세션 스크립트 패턴 (`scripts/_sessionN_*.py`) 잔존 흔적 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| C-4 | `CLAUDE.md.backup_20260406` | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| C-5 | `.tmp_agents/` `.tmp_benchmark/` 커밋됨 | **cleanup** | rule 4: cosmetic cleanup (gitignore) | Phase 4+ 에이전트 설계 시 rule 4 적용 |
| C-6 | DESIGN_BIBLE worktree 사본 3개 | **폐기** | rule 2: scope boundary (worktree) | Phase 4+ 에이전트 설계 시 rule 2 적용 |
| C-7 | longform/SCRIPT_SKILL.md vs longform/skills/longform-script/SKILL.md | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| C-8 | root skill 라우팅에 longform/child 없음 | **폐기** | rule 1: blacklist match (longform/) | Phase 4+ 에이전트 설계 시 rule 1 적용 |
| C-9 | Fish Audio URL 3곳 하드코딩 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |
| C-10 | HeyGen/Hedra BASE_URL 하드코딩 | **통합-재작성** | rule 5: default — integrate with rewrite | Phase 4+ 에이전트 설계 시 rule 5 적용 |

## 판정 분포 요약 (Counts Summary)

| Class | 승계 / 승계 신형 | 폐기 | 통합-재작성 | cleanup | Total |
|-------|------------------|------|-------------|---------|-------|
| A (verbatim)      | 2 | 3  | 8  | 0 | 13 |
| B (5-rule)        | 0 | 8  | 8  | 0 | 16 |
| C (5-rule)        | 0 | 4  | 4  | 2 | 10 |
| **Total**         | **2** | **15** | **20** | **2** | **39** |

**A급 검증:** 승계 2 (A-2, A-9) / 폐기 3 (A-5, A-6, A-11) / 통합-재작성 8 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13) — 02-HARVEST_SCOPE.md § 판정 분포와 100% 일치.

**B/C급 rule 분포 (26 entries):**
- rule 1 (blacklist match): 10건 (B-1, B-5, B-6, B-8, B-10, B-12, B-15, C-1, C-7, C-8)
- rule 2 (scope boundary): 2건 (B-3, C-6)
- rule 3 (session 77+ canonical): 0건
- rule 4 (C-class cosmetic cleanup): 2건 (C-2, C-5)
- rule 5 (default rewrite): 12건 (B-2, B-4, B-7, B-9, B-11, B-13, B-14, B-16, C-3, C-4, C-9, C-10)
- Sum: 10+2+0+2+12 = 26 ✓

*Generated by harvest_importer.py. A급 13 rows verbatim from 02-HARVEST_SCOPE.md. B/C 26 rows produced by 5-rule algorithm.*
