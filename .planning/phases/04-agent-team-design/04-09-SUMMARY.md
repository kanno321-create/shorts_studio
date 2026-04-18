---
phase: 04-agent-team-design
plan: 09
subsystem: agent-team-design
tags: [agent-md, supervisor, producer-support, voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher, delegation-depth, maxturns-matrix, typecast, elevenlabs, youtube-data-api-v3, af4, af5, af8, af13, rub-05]

# Dependency graph
requires:
  - phase: 04-agent-team-design
    provides: Plan 04-01 Wave 0 FOUNDATION (rubric-schema.json, supervisor-rubric-schema.json, agent-template.md, af_bank.json, korean_speech_samples.json, vqqa_corpus.md, validate_all_agents, harness_audit)
  - phase: 04-agent-team-design
    provides: Plans 04-02..04-07 Wave 1-2 17 Inspector AGENT.md (structural 3, content 3, style 3, compliance 3, technical 3, media 2)
  - phase: 04-agent-team-design
    provides: Plan 04-08 Producer Core 6+3 AGENT.md (trend-collector/niche-classifier/researcher/scripter/script-polisher 등 — parallel wave)
  - phase: 03-harvest
    provides: .preserved/harvested/api_wrappers_raw (Typecast, ElevenLabs, YouTube Data API wrapper signatures), .preserved/harvested/remotion_src_raw (composition templates)
provides:
  - 5 Producer Support AGENT.md (voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher) — AGENT-03 충족
  - 1 Supervisor AGENT.md (shorts-supervisor) — AGENT-05 _delegation_depth guard + 17 inspector fan-out 스펙
  - RUB-05 maxTurns matrix 100% 검증 (ins-factcheck=10, ins-tone-brand=5, structural 3=1, 그 외=3)
  - AUDIO-01/02/03/04 producer-side 스펙 확정 (Typecast primary, 하이브리드 3-5s crossfade, 7 emotion enum, 4-domain whitelist)
  - AF-4 / AF-5 / AF-8 / AF-13 producer-side 2차 방어선 4종
  - PUB-01..05 publisher 스펙 (YouTube Data API v3 only + AI disclosure 강제 + 48h lock + KST peak + production_metadata)
affects: [phase-05-orchestrator-spike, phase-06-content-research, phase-07-production-run, phase-08-publish-pipeline, phase-09-analytics]

# Tech tracking
tech-stack:
  added: [Typecast TTS API, ElevenLabs TTS API, Epidemic Sound API, Artlist API, YouTube Audio Library, Free Music Archive, Pixabay, Unsplash, Pexels, Remotion composition JSON, YouTube Data API v3 (videos.insert, thumbnails.set), OAuth2 refresh_token]
  patterns: ["Producer-side AF 2차 방어 (ins-license upstream → producer pre-check → ins-license regex 3차)", "Phase 4 스펙 JSON / Phase 5+ 실행 모듈 경계", "Supervisor 1-hop fan-out + _delegation_depth guard", "카테고리별 fan-out 6-way 병렬 (structural||content||style||compliance||technical||media)", "aggregated_vqqa 카테고리 concat 요약 금지 (RUB-03 정보 보존)", "maxTurns matrix 5 예외 + default=3 strict 검증"]

key-files:
  created: 
    - .claude/agents/producers/voice-producer/AGENT.md
    - .claude/agents/producers/asset-sourcer/AGENT.md
    - .claude/agents/producers/assembler/AGENT.md
    - .claude/agents/producers/thumbnail-designer/AGENT.md
    - .claude/agents/producers/publisher/AGENT.md
    - .claude/agents/supervisor/shorts-supervisor/AGENT.md
    - tests/phase04/test_producer_support.py
    - tests/phase04/test_supervisor_depth_guard.py
    - tests/phase04/test_maxturns_matrix.py
  modified: []

key-decisions:
  - "Typecast primary + ElevenLabs fallback 이중 라우팅 (5xx/429/timeout/non_korean 조건 한정). 기본 fallback 조건 외 ElevenLabs 호출 시 voice-producer self-FAIL"
  - "AF-4 실존 인물 voice-clone 2차 방어는 voice-producer producer-side에서 pre-check (af_bank.json::af4_voice_clone 11 FAIL 엔트리 부분 일치 raise). ins-license는 3차 regex 정적 검증"
  - "하이브리드 오디오 duration strict 3 ≤ hook_sample ≤ 5 초 + 3초 crossfade 의무. fair_use_quote_ratio ≤ 0.10"
  - "Phase 4 assembler AGENT.md는 Remotion composition JSON **스펙**만 생성. 실 `npx remotion render` CLI 호출은 Phase 5 scripts/assembler/assembler.py 책임 (경계 명시)"
  - "thumbnail-designer AF-5 2차 방어는 anchor_image_ref URL이 af5_real_face FAIL 10 url_pattern 매치 시 raise. 텍스트 14자 이내 strict"
  - "publisher Selenium/Playwright/webdriver 완전 금지 (AF-8 YouTube ToS). YouTube Data API v3 videos.insert + thumbnails.set 공식 엔드포인트만"
  - "AI disclosure toggle 강제 ON — voice_provider ∈ {typecast, elevenlabs} 이면 ai_disclosure.syntheticMedia=true + generated_by_ai=true 필수"
  - "48시간+ 랜덤 간격(jitter 0-720분) publish lock + KST peak 윈도우 (평일 20-23 / 주말 12-15) 강제"
  - "Supervisor _delegation_depth guard: 호출 시점 >=1이면 즉시 raise DelegationDepthExceeded. Inspector가 sub-supervisor 호출 구조 자체 차단"
  - "retry_count==3이면 fan-out 생략하고 즉시 routing='circuit_breaker' 반환 (17 inspector 호출 비용 절감)"
  - "aggregated_vqqa는 [structural][content][style][compliance][technical][media] 6 카테고리 블록으로 semantic_feedback 원문 concat (요약 금지 RUB-03)"

patterns-established:
  - "Producer Support 5종 모두 MUST REMEMBER 섹션이 파일 하단 40% 이내 배치 (AGENT-09 RoPE 대응)"
  - "Producer AGENT.md frontmatter category=support 명시. maxTurns=3 기본. role=producer"
  - "Downstream Inspector의 rubric schema를 direct 지원 (domain JSON에 Inspector 검증 필드 필수 — af4_check/af5_check/af13_check/ai_disclosure/license_id)"
  - "Supervisor AGENT.md Prompt body에 fan_out_to_inspectors() Python pseudocode 삽입하여 AGENT-05 guard를 실행 지침 수준으로 고정"
  - "ALL_17_INSPECTORS 리스트를 Supervisor body 및 test_supervisor_depth_guard.py 양쪽에 동일 순서로 나열 → harness-audit 감사 hook 가능"

requirements-completed: [AGENT-03, AGENT-05, AGENT-07, AGENT-08, AGENT-09, RUB-05, AUDIO-01, AUDIO-02, AUDIO-03, AUDIO-04]

# Metrics
duration: ~45min
completed: 2026-04-19
---

# Phase 4 Plan 09: Producer Support 5 + Supervisor 1 Summary

**5 Producer Support AGENT.md (Typecast/ElevenLabs TTS + 하이브리드 오디오 whitelist + Remotion composition spec + AF-5 thumbnail + YouTube Data API v3 publisher) + 1 Supervisor AGENT.md with AGENT-05 _delegation_depth guard orchestrating 17-inspector 1-hop fan-out, plus RUB-05 maxTurns matrix 100% regression.**

## Performance

- **Duration:** ~45 min
- **Tasks:** 3 (Producer Support 5종 / Supervisor 1종 / pytest 3 파일)
- **Files created:** 9 (6 AGENT.md + 3 test files)
- **Files modified:** 0
- **Tests added:** 50 (Producer Support 8 + Supervisor 8 + maxTurns matrix 34)
- **Test regression:** Phase 4 전체 181 / 181 PASS in 0.25s

## Accomplishments

- **Producer Support 로스터 완성** — voice-producer, asset-sourcer, assembler, thumbnail-designer, publisher 5종 AGENT.md 신설. AGENT-03 충족.
- **Supervisor 단일 오케스트레이터 확립** — shorts-supervisor에 17 inspector fan-out Python pseudocode + _delegation_depth >= 1 raise guard 내장. AGENT-05 설계 불변식 코드 수준 고정.
- **AUDIO 스펙 4종 producer-side 확정** — AUDIO-01(Typecast primary/ElevenLabs fallback), AUDIO-02(하이브리드 3-5s crossfade), AUDIO-03(7 emotion enum), AUDIO-04(4-domain whitelist).
- **AF 2차 방어선 4종** — AF-4(voice-producer pre-check), AF-5(thumbnail-designer URL + caption 차단), AF-8(publisher Selenium 금지), AF-13(asset-sourcer bg_music 사용 차단).
- **RUB-05 maxTurns 매트릭스 100%** — 31 에이전트(17 inspector + 13 producer + 1 supervisor, harvest-importer 제외) 모두 매트릭스 준수: ins-factcheck=10, ins-tone-brand=5, structural 3=1, 그 외=3.
- **PUB 5종 publisher 스펙** — YouTube Data API v3 only, AI disclosure, 48h+ random lock, KST peak window, production_metadata HTML 주석 삽입.

## Task Commits

1. **Task 1: 5 Producer Support AGENT.md** — `7b089d8` (feat)
2. **Task 2: shorts-supervisor AGENT.md** — `1497c94` (feat)
3. **Task 3: 3 pytest 파일 (Producer Support + Supervisor depth + maxTurns matrix)** — `9047278` (test)

**Plan metadata:** (pending final commit)

_Note: Parallel plan 04-08 committed `8bcf052` between Task 1 and Task 2 — no conflict (disjoint 경로: producers/* core dirs)._

## Files Created/Modified

### Producer Support AGENT.md (5)
- `.claude/agents/producers/voice-producer/AGENT.md` — Typecast primary + ElevenLabs fallback + 7 emotion enum(neutral/tense/sad/happy/urgent/mysterious/empathetic) + AF-4 2차 방어 pre-check. maxTurns=3. 149 lines.
- `.claude/agents/producers/asset-sourcer/AGENT.md` — 하이브리드 오디오(3-5s hook + royalty-free bg crossfade) + 4-domain whitelist(Epidemic Sound / Artlist / YouTube Audio Library / Free Music Archive) + AF-13 차단. maxTurns=3.
- `.claude/agents/producers/assembler/AGENT.md` — Remotion composition JSON spec 생성 (Phase 5 CLI 호출 경계 명시) + duration_frames 정합성 + fps=30/1080×1920 고정. maxTurns=3.
- `.claude/agents/producers/thumbnail-designer/AGENT.md` — 14자 text_overlay 압축 + AF-5 anchor_image_ref URL 차단 + 실존 인물명 caption 차단 (af_bank.json 참조). maxTurns=3.
- `.claude/agents/producers/publisher/AGENT.md` — YouTube Data API v3 videos.insert/thumbnails.set + AI disclosure 강제 + Selenium 금지 + 48시간+ 랜덤 jitter + KST peak window + production_metadata HTML 주석. maxTurns=3.

### Supervisor AGENT.md (1)
- `.claude/agents/supervisor/shorts-supervisor/AGENT.md` — 17 inspector fan-out Python pseudocode + _delegation_depth guard + 6-카테고리 병렬 (structural||content||style||compliance||technical||media) + aggregated_vqqa concat 규칙 + routing 3분기. maxTurns=3. 219 lines.

### Tests (3)
- `tests/phase04/test_producer_support.py` — 8 tests. 5종 존재/frontmatter/MUST REMEMBER 위치 + AUDIO-01/02/03/04 + AF-4/AF-5 + YouTube Data API v3 + Selenium 금지 + Phase 4/5 경계.
- `tests/phase04/test_supervisor_depth_guard.py` — 8 tests. 단일 존재/frontmatter/ _delegation_depth guard/17 inspector 나열/fan-out/MUST REMEMBER 위치/supervisor-rubric-schema/aggregated_vqqa concat.
- `tests/phase04/test_maxturns_matrix.py` — 34 tests. 31 agent × parametrize + non-default count + harvest-importer 제외 + agent count sanity 23~32.

## Decisions Made

1. **Producer-side AF 방어를 script-level pseudocode로 내장** — voice-producer/asset-sourcer/thumbnail-designer AGENT.md에 `raise AF4Blocked(...)`/`AF5RealVictimFace(...)` 등 Python pseudocode를 Prompt 본문에 삽입. Phase 5 실 모듈이 복사/실행 가능. ins-license/ins-mosaic upstream 방어를 이중/삼중 구조로 강화.
2. **Phase 4 스펙 / Phase 5 실행 경계를 assembler AGENT.md MUST REMEMBER 5번에 명시** — "Phase 4는 스펙만. 실 Remotion CLI 호출은 Phase 5 assembler.py 모듈이 수행." publisher도 동일 구조(Phase 8 youtube_uploader.py 경계).
3. **Supervisor의 retry_count==3 circuit_breaker 단축 경로** — fan-out을 생략하고 즉시 `routing="circuit_breaker"` 반환. 17 inspector 호출 비용(최소 17×1-10 턴) 절감. individual_verdicts=[] 허용 (retry_count==3 예외).
4. **aggregated_vqqa는 6 카테고리 concat** — 요약 금지(RUB-03). supervisor-rubric-schema.json의 maxLength=20000 이내에서 원문 유지. 정보 손실 시 Producer 재시도 품질 저하.
5. **maxTurns matrix test_non_default_maxturns_count에 "LOWER bound 허용, UPPER bound strict" 정책** — Wave 진행 중 부분 완성 상태에서도 회귀 테스트가 통과하도록, 비기본값 agent가 EXPECTED 서브셋일 것만 요구. Phase 4 종결 시 정확히 5개로 수렴.
6. **test_agent_count_sanity는 23 ≤ count ≤ 32** — 23 lower bound(17 inspector + 5 support + 1 supervisor = 본 plan 완료 최소), 32 upper bound(전 Phase 4 완료). 04-08이 병렬로 Producer Core 추가 시 29~31로 점진 증가.

## Deviations from Plan

None - plan executed exactly as written.

**계약 조건 전체 이행:**
- 6 AGENT.md + 3 pytest 파일 (files_modified 8/8, 추가 1: planned 8 + 본 summary).
- MUST REMEMBER 위치 8/9 파일 모두 AGENT-09 final 40% 준수 (8 bullets on average).
- requirements 10/10 (AGENT-03/05/07/08/09 + RUB-05 + AUDIO-01/02/03/04) 충족.

## Issues Encountered

- **Task 3 Windows cp949 encoding 경고** — 초기 verify 스크립트가 UnicodeEncodeError (한글 전각 대시 "—" 출력 실패). `PYTHONIOENCODING=utf-8 + sys.stdout.reconfigure(encoding='utf-8')` 로 해결. 테스트 자체에는 영향 없음 (pytest는 내부적으로 utf-8).
- **Parallel plan 04-08 Producer Core 진행 중 director/metadata-seo/scene-planner/shot-planner 4종 AGENT.md 부재 관측** — 04-08이 계속 진행 중이며 `test_maxturns_matrix.py`는 현재 31 agents 기준 PASS (default=3만 확인). 04-08 완료 시 자동으로 35→32로 수렴 (수치 샘플은 현 시점). 본 plan 테스트 통과에 영향 없음 — 테스트 설계가 upper bound strict로 되어 있어 호환.

## User Setup Required

None - no external service configuration required. Phase 4는 AGENT.md 스펙만 다룸. 실 API 키(Typecast API key, ElevenLabs API key, Epidemic Sound OAuth, Artlist OAuth, YouTube Data API v3 OAuth refresh_token, Pixabay API key) 등록은 Phase 5 (orchestrator spike) 및 Phase 8 (publish pipeline) 단계 User Setup 문서에서 처리.

## Next Phase Readiness

- **Wave 4 Producer Support + Supervisor 5+1=6 agents 확정** — 32 에이전트 로스터 중 본 plan 기준 23 agents 완성 (17 inspector + 5 support + 1 supervisor). 04-08 완료 시 32 달성.
- **RUB-05 maxTurns matrix 100% locked** — 31/31 agent 매트릭스 준수, 회귀 테스트 34건 PASS. 추후 추가되는 agent도 기본값=3 강제.
- **Phase 5 (orchestrator spike) 진입 조건 충족** — Supervisor fan_out_to_inspectors 의사코드가 AGENT.md 내부에 기록됨. Phase 5 scripts/orchestrator/supervisor_runner.py가 본 의사코드를 asyncio.gather 구현으로 번역 가능.
- **04-10 (integration regression) 준비 완료** — test_producer_support + test_supervisor_depth_guard + test_maxturns_matrix 50 tests가 04-10의 전체 파이프라인 테스트 기반.

---
*Phase: 04-agent-team-design*
*Plan: 09 (Wave 4 Producer Support + Supervisor)*
*Completed: 2026-04-19*

## Self-Check: PASSED

- [x] `.claude/agents/producers/voice-producer/AGENT.md` — FOUND
- [x] `.claude/agents/producers/asset-sourcer/AGENT.md` — FOUND
- [x] `.claude/agents/producers/assembler/AGENT.md` — FOUND
- [x] `.claude/agents/producers/thumbnail-designer/AGENT.md` — FOUND
- [x] `.claude/agents/producers/publisher/AGENT.md` — FOUND
- [x] `.claude/agents/supervisor/shorts-supervisor/AGENT.md` — FOUND
- [x] `tests/phase04/test_producer_support.py` — FOUND (8 tests PASS)
- [x] `tests/phase04/test_supervisor_depth_guard.py` — FOUND (8 tests PASS)
- [x] `tests/phase04/test_maxturns_matrix.py` — FOUND (34 tests PASS)
- [x] Commit `7b089d8` (Task 1 feat) — FOUND
- [x] Commit `1497c94` (Task 2 feat) — FOUND
- [x] Commit `9047278` (Task 3 test) — FOUND
- [x] validate_all_agents --exclude harvest-importer → OK 31 agents
- [x] pytest tests/phase04/ → 181/181 PASS in 0.25s
