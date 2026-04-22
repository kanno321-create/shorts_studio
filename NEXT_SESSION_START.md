# NEXT SESSION START — 세션 #31 진입 프롬프트

**작성**: 2026-04-22 세션 #30 종료 시점 (세션 후반 대표님 원칙 2종 + FAILURES auto-injection wiring 반영 갱신)
**작성자**: 대표님 지시 "핸드오프 3종 작성해줘"
**1-page 경계**: 이 문서는 다음 세션의 첫 30초 진입 프롬프트 역할. 긴 맥락은 WORK_HANDOFF.md 참조.

---

## 🧠 자동 주입 확인 (첫 5초)

세션 #31 시작 시 `session_start.py` Hook 이 다음을 system reminder 로 자동 주입합니다. **따로 읽을 필요 없음 — 이미 context 에 있음**:

1. 🔑 `.env` API keys 목록 (재질문 금지)
2. 📋 WORK_HANDOFF.md 첫 30줄
3. 🧠 MEMORY.md index + 2 feedback memory
   - `feedback_infinite_loop_avoidance.md` — Phase 확장으로 원래 goal 지연 금지
   - `feedback_lenient_retry_over_strict_block.md` — JSON/포맷 비준수 → hard-fail 금지, nudge retry 유도
4. 📛 **최근 실패 사례 + 교훈** (open 1 + 최근 5 entry):
   - `F-LIVE-SMOKE-JSON-NONCOMPLIANCE` (Tier A, **open**) — Claude CLI 자연어 반환 + empty stdout
   - `F-META-HOOK-FAILURES-NOT-INJECTED` (Tier A, resolved) — 원칙 ≠ 실행, wiring 필수
   - 그 외 F-D2-EXCEPTION-01/02 Wave 2/3 + FAIL-ARCH-01
5. 🗺️ Navigator coverage + CONFLICT_MAP 상태

---

## 🎯 대표님 합의된 단 하나의 목표

**해외범죄 샘플 쇼츠 1편 실제 제작 + YouTube unlisted 업로드 + 자동 cleanup**

Phase 추가 금지 (memory: `feedback_infinite_loop_avoidance.md` 자동 적용). 영상 1편 달성 이후 다음 단계 결정.

---

## 📦 현재 상태 (세션 #30 종료)

### 이미 shipped (사용 가능)
- ✅ **Phase 13 Live Smoke 재도전** — complete_with_deferred (Tier 1 60 tests green)
- ✅ **Phase 14 API Adapter Remediation** — complete_with_deferred (ADAPT-01~06 validated, 15→0 failures)
- ✅ **Phase 15 Wave 0~4 (2/3)** — 27 commits:
  - **encoding fix** (`_invoke_claude_cli_once` tempfile + `--append-system-prompt-file`)
  - shorts-supervisor AGENT.md 10591→5712 chars (Progressive Disclosure)
  - **5 UFL flags**: `--evidence-dir`, `--revision-from GATE`, `--feedback TEXT`, `--revise-script PATH`, `--pause-after GATE`
  - `rate_video.py` CLI + `verify_feedback_format.py` (UFL-04 2/3)

### 대기 (다음 세션 작업 후보)
- 🚧 **Live smoke 실 영상 제작 시도** — 2차 시도 실패 (Claude CLI JSON 미준수). 해결책 합의됨 (아래 참조).
- 🚧 Phase 15 Wave 4 Task 3 (researcher AGENT.md `<mandatory_reads>` 확장) — optional, 영상 제작에 not blocking
- 🚧 Phase 15 Wave 5/6 (live retry + phase gate) — **Wave 5 는 아래 경로로 대체**

---

## 🛠 대표님 승인된 경로 (세션 #31 에서 실행)

### Step 1 (5분): `--skip-supervisor` flag 추가
`scripts/smoke/phase13_live_smoke.py` 에 argparse flag 1개 + `_AutoPassSupervisorInvoker` wrapper 1개 (~20 lines):

```python
class _AutoPassSupervisorInvoker:
    """모든 gate 자동 PASS 반환 — supervisor Claude CLI 호출 SKIP.

    대표님 세션 #30 합의 경로: Claude CLI JSON schema 엄수 brittle 문제
    우회. Quality gate 는 영상 제작 달성 후 점진 복구.
    """
    def __call__(self, gate, output):
        from scripts.orchestrator.state import Verdict
        return Verdict.PASS

# phase13_live_smoke.py main:
if args.skip_supervisor:
    supervisor = _AutoPassSupervisorInvoker()
else:
    supervisor = make_default_supervisor_invoker(...)
```

테스트: `pytest tests/phase15/test_skip_supervisor.py` (새 파일, ~3 tests green)

### Step 2 (5분): 해외범죄 대본 1편 작성
`scripts/smoke/sample_scripts/overseas_crime_interpol_v1.md` — 60초 분량:
- incidents 채널바이블 준수 (탐정 하오체 + 조수 해요체)
- Hook 3초 질문형 + 숫자/고유명사
- Structure: Hook → 갈등/오해 (5-30초) → 핵심 3포인트 (30-90초) → 반전/정리 (마지막 2-5초)
- 예시 소재: 인터폴 국제 적색수배 + FBI 해외 도피범 사건 (공개 정보만 사용, 실명 없음)

### Step 3 (20-30분): Live run
```bash
python scripts/smoke/phase13_live_smoke.py --live \
    --topic "해외범죄,인터폴,FBI 수사" --niche incidents \
    --revise-script scripts/smoke/sample_scripts/overseas_crime_interpol_v1.md \
    --skip-supervisor \
    --budget-cap-usd 5.00 \
    --session-id "overseas_crime_sample_v1"
```

예상 실행 흐름 (13 gates):
- TREND/NICHE: pre-seeded skip ($0)
- RESEARCH_NLM: 실 NotebookLM query ($0, Max sub)
- BLUEPRINT: 실 Claude (director) — supervisor skip
- SCRIPT: 대표님 대본 주입 (scripter skip)
- POLISH: 실 Claude (script-polisher) — supervisor skip
- VOICE: Typecast 실 API (~$0.12)
- ASSETS: Kling I2V 실 API (~$2.80 — 8 cuts)
- ASSEMBLY: ken_burns 로컬 FFmpeg ($0)
- THUMBNAIL: Nano Banana (~$0.04)
- METADATA: 실 Claude (metadata-seo) — supervisor skip
- UPLOAD: YouTube API v3 unlisted (~$0 quota)
- MONITOR: 상태 확인 + cleanup (videos.delete)
- COMPLETE: evidence 5 files anchored

**예상 총 비용**: ~$3.00, ~20-30분 wall time

### Step 4 (대표님 검토): 영상 재생 + rating
YouTube unlisted URL → 재생 → `rate_video.py --video-id <id> --rating N --feedback "..."` → `.claude/memory/feedback_video_quality.md` append

---

## ⚠ 금지 사항 (세션 #31 에서 피할 것)

1. **"Phase 16 발의" 금지** — memory `feedback_infinite_loop_avoidance.md` 자동 적용. 인프라 추가 전에 Step 1~4 로 영상 1편부터.
2. **"또 다른 defer" 금지** — Live run 이 실패해도 phase 추가 없이 즉시 진단 + 최소 수정으로 재시도.
3. **Supervisor AGENT.md 추가 압축 금지** — 10591→5712 이면 충분. 더 줄여도 JSON 엄수 해결 안 됨 (Claude CLI 대화형 session 자체 한계).
4. **대본 에이전트에게 맡기지 말고 대표님 직접 작성** — UFL-02 의 `--revise-script` 는 정확히 이 use case.
5. **$5 cap 엄수** — budget_counter.py 가 자동 enforce. 초과 시 즉시 abort.
6. **Hard-fail 차단 금지 (lenient retry 원칙)** — memory `feedback_lenient_retry_over_strict_block.md` 자동 적용. JSON/포맷/품질 비준수 시 즉시 FAIL 말고 nudge retry (예시 첨부) 로 되돌려보내 재시도 (최소 2~3회). 단 AF-4/5/8/13 + skip_gates=True 등 법적·플랫폼 strike 위험 영역은 hard-block 유지.

---

## 📋 세션 #31 진입 체크리스트

- [ ] **system reminder 에 📛 최근 실패 사례 섹션 포함 여부 확인** — 없으면 `session_start.py` Hook 동작 실패이므로 재검토 (F-META-HOOK-FAILURES-NOT-INJECTED 재발)
- [ ] `git status` — 세션 #30 unstaged 4종 확인 (session_start.py + FAILURES.md + FAILURES_INDEX.md + CLAUDE.md) → **첫 commit** `chore(handoff): session #30 tail wiring — FAILURES auto-injection + lenient retry principle`
- [ ] `git log --oneline -10` — Phase 15 commits + 핸드오프 `08fbce3` 확인
- [ ] Preflight: `python scripts/smoke/phase13_preflight.py` → ALL_PASS 확인
- [ ] Step 1 `--skip-supervisor` flag 구현 → Step 2 해외범죄 대본 → Step 3 live run → Step 4 rating
- [ ] 결과 보고: 영상 URL + 비용 + wall time + cleanup 확인
- [ ] Live run 중 JSON/포맷 실패 시 — **nudge retry 먼저** (lenient retry memory 준수), 즉시 abort 금지

---

## 🔗 Reference Files (빠른 이동)

- 핵심 runner: `scripts/smoke/phase13_live_smoke.py`
- invokers (encoding fix): `scripts/orchestrator/invokers.py` L121-187
- pipeline state machine: `scripts/orchestrator/shorts_pipeline.py` L171-319
- 채널바이블 (incidents): `.preserved/harvested/theme_bible_raw/incidents.md`
- Phase 15 plans: `.planning/phases/15-system-prompt-compression-user-feedback-loop/`
- **Memory (2종, 자동 주입)**:
  - `.claude/memory/feedback_infinite_loop_avoidance.md` — Phase 확장 금지
  - `.claude/memory/feedback_lenient_retry_over_strict_block.md` — hard-fail 금지, nudge retry 선호
- **FAILURES (자동 주입)**:
  - `.claude/failures/FAILURES.md` — open entry + 최근 5건 자동 노출
  - `.claude/failures/FAILURES_INDEX.md` — Phase 6+ 카테고리 색인
- **Hook (세션 #30 후반 patch)**:
  - `.claude/hooks/session_start.py` — `load_recent_failures()` (Step 6a)

---

*이 문서는 세션 #31 진입 시 첫 30초 동안 읽힘. 나머지 상세는 WORK_HANDOFF.md + ARCHITECTURE.md 에 위임.*
