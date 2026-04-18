# HARVEST_SCOPE — Phase 3 Harvest 범위 결정서

**Created:** 2026-04-19 (Phase 2 Domain Definition)
**Consumer:** Phase 3 harvest-importer 에이전트 (spawned by `/gsd:execute-phase 3`)
**Source:** `shorts_naberal/.planning/codebase/CONFLICT_MAP.md` (A:13 / B:16 / C:10 = 39)
**Purpose:** Phase 2가 A급 13건만 사전 판정. B/C급 26건은 Phase 3 위임.

---

## § A급 13건 사전 판정 (Phase 2 완결)

본 테이블은 `shorts_naberal/.planning/codebase/CONFLICT_MAP.md` A급 13건을 "승계 / 폐기 / 통합-재작성" 3-way 로 사전 판정한 결과다. Phase 3 harvest-importer 에이전트는 이 5-컬럼 테이블을 그대로 파싱하여 import/skip 결정에 사용한다.

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

### 판정 분포

- **승계 2건**: A-2 (cuts[] 스키마), A-9 (탐정님 호명 금지) — 그대로 받아써서 Phase 4+ 에이전트 룰에 반영
- **폐기 3건**: A-5 (TODO 미연결), A-6 (skip_gates), A-11 (longform-scripter) — Harvest 시 참조 금지, Hook/Blacklist 이중 차단
- **통합-재작성 8건**: A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 — 개념만 참조, Phase 4+ 에서 새로 구현

D2-C 결정(CONTEXT.md) 및 02-RESEARCH.md § A급 13건 Draft Judgments 매트릭스와 완전 일치.

---

## § Harvest Blacklist (절대 import 금지)

Phase 3 harvest-importer 에이전트는 **이 목록을 read-lock**. 복사 시 skip. Python dict 형식으로 제공하여 에이전트가 그대로 로드 가능.

```python
HARVEST_BLACKLIST = [
    # A-6: skip_gates 디버그 경로 (AF-14 직접 연결)
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1239-1291", "reason": "A-6 skip_gates=True block — HC-4 우회 경로 상시 존재, 디버그 상주 금지"},

    # A-5: TODO(next-session) 미연결 4곳 (AF-14 직접 연결)
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "520", "reason": "A-5 TODO(next-session) wire ins-narration GATE 3a check"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "781", "reason": "A-5 TODO(next-session) unwired gate"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1051", "reason": "A-5 TODO(next-session) unwired gate"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1129", "reason": "A-5 TODO(next-session) unwired gate"},

    # A-11 / A-12: 스코프 외 진입점 (shorts 스튜디오는 shorts 전용)
    {"path": "longform/", "reason": "A-11 longform-scripter 2곳 충돌 + 본 스튜디오 shorts 전용 (D-10 주 3~4편 쇼츠)"},
    {"file": ".claude/skills/create-video/", "reason": "A-12 롱폼 진입점, 폐기. subtitle_generate.py shorts 런타임 차단"},

    # A-3: 구 shorts-researcher 경로 (NLM-fetcher primary 전환)
    {"file": ".claude/skills/create-shorts/SKILL.md", "reason": "A-3 구 @shorts-researcher / @shorts-scripter 직접 호출 패턴 — 재작성 대상, 원본 import 금지"},

    # AF-8: Selenium 업로드 (YouTube ToS 위반)
    {"pattern": "selenium", "reason": "AF-8 YouTube Data API v3 공식만 허용, Selenium ban 위험"},

    # D-7: 구 orchestrator 전체 (5166줄 → 500~800줄 재작성)
    {"file": "scripts/orchestrator/orchestrate.py", "reason": "D-7 state machine 500~800줄 재작성 (Phase 5) — 전량 폐기"},
]
```

**해석 규칙:**
- `file` 키: 정확한 파일 경로 (루트 = `shorts_naberal/`)
- `path` 키: 디렉토리 prefix 매칭
- `lines` 키: 해당 범위만 skip (파일 자체는 다른 용도로 참조 가능할 수 있으나, 본 테이블에선 `file` 전체 폐기와 중복 기재하여 명확화)
- `pattern` 키: 파일 내용 regex (import 전 grep 사전 검사)
- `reason` 키: Phase 3 감사 로그에 기록될 사유

**Hook 이중 차단:** 위 블랙리스트는 Phase 1에서 설치된 `pre_tool_use.py` 의 `deprecated_patterns.json` regex 와 중복 방어 (skip_gates=True, TODO(next-session), selenium 등).

---

## § 4개 raw 디렉토리 매핑 (Phase 3 실행 지침)

Phase 3 harvest-importer 는 `shorts_naberal/` 읽기 전용 소스로부터 **4개 raw 디렉토리**에 물리 복사한다. 각 매핑은 REQUIREMENTS.md `HARVEST-01~05` 와 1:1 대응.

| 목적지 (studios/shorts/) | 소스 (shorts_naberal/) | 필터 | 요구사항 ID |
|--------------------------|------------------------|------|-------------|
| `.preserved/harvested/theme_bible_raw/` | `.claude/theme-bible/` (전체) | 무필터 복사 — 채널 바이블은 검증된 자산 | **HARVEST-01** |
| `.preserved/harvested/remotion_src_raw/` | `src/` (Remotion composition) | `node_modules/` 제외 (대용량 패키지) | **HARVEST-02** |
| `.preserved/harvested/hc_checks_raw/` | `scripts/*hc_checks*` 실측 작동 모듈만 | 블랙리스트 참조 (orchestrate.py 제외) | **HARVEST-03** |
| `.preserved/harvested/api_wrappers_raw/` | `scripts/api/` (Runway / Kling / ElevenLabs / Typecast wrapper) | 블랙리스트 참조 — `orchestrate.py` 자체는 제외, API wrapper 만 복사 | **HARVEST-05** |

**Tier 3 Lockdown (HARVEST-06):** Phase 3 Harvest 완료 직후, `.preserved/harvested/` 전체에 `chmod -w` (Linux/macOS) 또는 `attrib +R` (Windows) 적용. 이후 수정 시도는 OS 레벨에서 거부. CONFLICT_MAP 39건 재드리프트 구조적 차단.

---

## § FAILURES 이관 경로

과거 학습 자산(`FAILURES.md`)을 승계하되 출처를 보존하여 Phase 4+ 에이전트가 역사적 실패 사례를 소급 학습 가능하도록 한다.

- **소스:** `shorts_naberal/.claude/failures/**/FAILURES.md` 및 루트 `FAILURES.md` (있을 경우)
- **대상:** `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
- **규칙:** append-only concat (HARVEST-04). 개별 agent FAILURES 는 병합하되 `<!-- source: shorts_naberal/.claude/failures/<agent>/FAILURES.md --><br>` 주석으로 출처 유지. 원본 파일 수정 금지, 통합본만 studios/ 에 기록.

**D-2 저수지 규율 연동:** 이관된 FAILURES 는 Phase 10 첫 1~2개월 SKILL patch 금지 기간 동안 "읽기 전용 레퍼런스"로만 사용. 월 1회 batch 리뷰 시점에 `.candidate.md` 로 승격 후 7일 staged rollout.

---

## § B/C급 26건 Phase 3 위임 지침

D2-C 결정: Phase 2 는 A급 13건만 판정. B급 16건 + C급 10건 = 26건은 Phase 3 harvest-importer 에이전트가 다음 알고리즘으로 자동 판정한다.

### 판정 알고리즘 (pseudocode)

```python
# Phase 3 harvest-importer agent decision algorithm
# Input: conflict_map entries for B(16) + C(10) = 26 items
# Output: verdict in {승계, 폐기, 통합-재작성, cleanup}

for item in conflict_map[B:16] + conflict_map[C:10]:
    # Rule 1: Harvest blacklist takes precedence
    if item.path in HARVEST_BLACKLIST:
        verdict = "폐기"

    # Rule 2: longform / JP / worktree are out of scope (shorts 전용)
    elif item.domain in ("longform", "incidents_jp", "worktree", "duo_japan"):
        verdict = "폐기"  # scope boundary

    # Rule 3: Session 77+ canonical forms are inherited as-is
    elif item.신형_위치 matches "session 77 after" OR "17일 uncommitted":
        verdict = "승계 신형"

    # Rule 4: Pure cosmetic cleanup (gitignore, worktree copies, .tmp)
    elif item.category == "C급" AND item.type in ("gitignore_missing", "worktree_copy", "tmp_committed"):
        verdict = "cleanup"  # 일괄 cleanup 커밋으로 처리

    # Rule 5: Default — integrate with rewrite (Phase 4+ agent prompt 반영)
    else:
        verdict = "통합-재작성"  # Phase 4 에이전트 프롬프트 설계 시 참조
```

### B급 16건 사전 검토 결과 (Planner 참고 — 비구속적 힌트)

Phase 3 harvest-importer 는 아래 분류를 **힌트로만** 사용. 실제 판정은 Phase 3 실측 후 최종 확정.

- **스코프 외 (longform / duo / Japan / dev)** → 폐기: B-1 (13-15분 vs 13-18분, longform), B-3 (incidents_jp 보이스), B-5 부분 (롱폼 듀오 비율), B-6 (longform/config/channels.yaml), B-8 (longform_tts.py 스키마), B-16 (audio-pipeline sys.path)
- **이미 해결 / 하위 동기화만 필요** → 승계: B-10 (Pexels 완전 금지 완료, 코멘트 정리만), B-12 (CLAUDE.md 파이프라인 요약 신형 유지, 하위 스킬만 동기화)
- **규칙 문서화 필요** → Phase 4 RUB-05 적용: B-7 (maxTurns 무분류 → Phase 4 표준 3 / 예외 10·5·1 규칙 적용)
- **config 실측 후 판정** → Phase 3 판정: B-2 (pause_comma 250ms vs 300-400ms), B-4 (visual_mode t2i_i2v), B-9 (paperclip orchestrate.py 호출 잔존), B-13 (길이 상한 120s vs 140s), B-14 (ins-duplicate/license 역할 겹침 — A-4 로 이미 해결), B-15 (`.tmp_nlm/` `.gitignore`)
- **합계**: 폐기 6 / 승계 2 / Phase 3 판정 8

### C급 10건 사전 검토 결과 (Planner 참고 — 비구속적 힌트)

- **일괄 cleanup 커밋** → cleanup: C-1 (`NLM_PROMPT_GUIDE.md` 위치), C-2 (`_fun_summary_frames/`), C-4 (`CLAUDE.md.backup_20260406`), C-5 (`.tmp_agents/` `.tmp_benchmark/`)
- **스코프 외 (longform / worktree / JP)** → 폐기: C-6 (DESIGN_BIBLE worktree 사본), C-7 (longform/SCRIPT_SKILL.md 중복), C-8 (longform/child skill 라우팅)
- **config 리팩토링 저우선순위** → Phase 3 판정: C-9 (Fish Audio URL 하드코딩), C-10 (HeyGen/Hedra BASE_URL 하드코딩)
- **해결 완료 (재확인만)** → 이관 불필요: C-3 (세션 스크립트 삭제 완료)
- **합계**: cleanup 4 / 폐기 3 / Phase 3 판정 2 / 해결 1

---

## § Harvest 성공 기준 (Phase 3 Success Criteria 연동)

Phase 3 `/gsd:verify-work 3` 는 아래 체크리스트로 본 문서와 매핑된 결과물을 검증한다.

- [ ] `.preserved/harvested/` 하위 4 raw 디렉토리 (theme_bible_raw, remotion_src_raw, hc_checks_raw, api_wrappers_raw) 존재 + `diff -r` 0 검증 (소스 vs 복사본 동일성)
- [ ] `chmod -w` (또는 `attrib +R`) 실제 발동 (수정 시도 시 거부 확인 — Write tool permission denied)
- [ ] `HARVEST_DECISIONS.md` 생성 — 본 파일의 A급 13 판정 + B/C급 26 Phase 3 판정 결과 병합본 (39건 전수)
- [ ] `.claude/failures/_imported_from_shorts_naberal.md` 존재 + append-only concat 검증
- [ ] Harvest Blacklist 준수 — `grep -r "skip_gates=True" .preserved/harvested/` 결과 0건, `grep -r "TODO(next-session)" .preserved/harvested/` 결과 0건

Phase 3 harvest-importer 는 본 파일 § Harvest Blacklist 섹션을 **Python dict 로 파싱**하여 import 차단 목록으로 사용. 위 5개 체크는 모두 통과해야 Phase 4 Agent Team Design 진입 허용.

---

*Phase 2 산출물 (2026-04-19). Phase 3 에서 `HARVEST_DECISIONS.md` 로 승격 (A급 13 + B/C급 26 = 39건 전수 판정).*
