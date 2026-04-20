# Phase 9.1 — Deferred Items

Items discovered during execution that are OUT OF SCOPE for the current plan
and logged here per execute-plan.md deviation rules (SCOPE BOUNDARY).

---

## 1. Runway VALID_RATIOS_BY_MODEL drift vs live API

**Discovered:** 2026-04-20 Plan 09.1-06 live smoke run (세션 #24 YOLO)
**File:** `scripts/orchestrator/api/runway_i2v.py` §50-53
**Severity:** Low (**DEACTIVATED** by stack switch) — wrong values advertised, but Runway adapter no longer on production path after 2026-04-20 세션 #24 후반부 Kling 2.6 Pro primary 확정. Production smoke (`scripts/smoke/phase091_stage2_to_4.py`) 는 `--use-veo` 제외 시 Kling, 제외 아니면 Veo 로 routing — Runway 호출 경로 없음.
**Current state (Plan 04 landed):**

```python
VALID_RATIOS_BY_MODEL: dict[str, list[str]] = {
    "gen3a_turbo": ["16:9", "9:16", "768:1280", "1280:768"],
    "gen4.5": ["720:1280"],
}
```

**Observed live (HTTP 400 from `api.dev.runwayml.com/v1/image_to_video`):**

```
{'error': '`ratio` must be one of: 768:1280, 1280:768.', 'docUrl': '...'}
```

I.e. the `gen3a_turbo` I2V endpoint rejects `"16:9"` and `"9:16"` despite
them being advertised by the adapter's constant. Only pixel-dimension
ratios (`768:1280`, `1280:768`) are accepted.

**Impact on Plan 09.1-06:** mitigated in-place (Rule 1 auto-fix — smoke
CLI hardcodes `ratio="768:1280"` with an inline comment referencing this
deferred item). Live smoke run succeeded after the fix.

**Resolution target:** Plan 09.1-07 (Phase Gate aggregator) OR a Phase 10
Runway adapter patch. Fix = remove the two string-ratio entries from the
`gen3a_turbo` list, leaving only `["768:1280", "1280:768"]`; update
`DEFAULT_RATIO` accordingly (probably `"768:1280"` for the 9:16 vertical
Shorts default). Update `tests/phase091/test_runway_ratios.py` matchers.

**NOT fixed in Plan 09.1-06** because:
1. The adapter constant touches multiple tests (`test_runway_ratios.py`)
   that pin the current list — changing it is a Wave 1 regression surface.
2. Plan 09.1-06 scope is "smoke test harness + hook hygiene", not
   adapter remediation.
3. The inline Rule-1 fix in the smoke CLI unblocks the deliverable
   ("Live run: exit 0") without propagating the drift to production
   callers.

**Status update (2026-04-20 세션 #24 후반, 박제 batch):** Kling 2.6 Pro primary 전환으로 Runway adapter 는 production path 에서 이탈 (hold 상태). smoke CLI 의 inline Rule-1 fix 도 제거됨 (Kling adapter 사용). VALID_RATIOS 정확성 이슈는 **Phase 10 Runway adapter 완전 제거 / 문서화 검토** 과제로 승계.

---

## 2. 스택 전환 이후 cleanup backlog (Kling 2.6 primary 전환)

**Discovered:** 2026-04-20 세션 #24 후반부 (stack 4차 번복 후 박제 batch 수행 중)
**Severity:** Low — production path 정상, 정리성 drift.

스택 Kling 2.6 Pro primary + Veo 3.1 Fast fallback 최종 확정 (2026-04-20 세션 #24). 박제 batch 에서 production 경로는 복구되었으나 다음 cleanup 항목은 **Phase 10 batch window** 로 이관:

1. **RunwayI2VAdapter 완전 제거 / hold 명시 주석** — `scripts/orchestrator/api/runway_i2v.py`. 현재 코드만 유지, production 호출 없음. 제거 시 `tests/phase04/test_runway_ratios.py` + `tests/phase05/test_runway_adapter.py` 동반 삭제 필요.
2. **KlingI2VAdapter `NEG_PROMPT` 하드코드 재검토** — `scripts/orchestrator/api/kling_i2v.py` §52-57. i2v_prompt_engineering 3원칙 "negative prompt 역효과" 와 상충 가능. Phase 10 실측에서 품질 저하 확인 시 제거.
3. **메모리 파일명 rename** — `project_video_stack_runway_gen4_5.md` → `project_video_stack_kling26.md`. MEMORY.md index 동시 업데이트 필요 (2 파일 touch).
4. **Wiki 파일명 rename** — `wiki/render/remotion_kling_stack.md` → `remotion_i2v_stack.md`. backlinks scan 필요.
5. **NLM Step 2 `runway_prompt` field → `i2v_prompt`** — `.claude/agents/producers/scripter/` prompt template 업데이트 + 노트북 curator instruction 갱신.
6. **`remotion_src_raw/` 40 파일 고아 자산 integration** — Phase 9.1 scope 외, shorts_naberal 승계 자산 Tier 3 등록 검토.
7. **`Shotstack.create_ken_burns_clip` 완전 제거** — Phase 9.1 Plan 03 에서 KenBurnsLocal 로 교체 완료. Shotstack 클라우드 의존 제거 마무리.

**Resolution target:** Phase 10 첫 batch patch window (D-2 저수지 규율에 따라 첫 1-2개월 실 실패 데이터 축적 후 일괄 처리).

---
