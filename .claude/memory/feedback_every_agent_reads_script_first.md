---
name: feedback_every_agent_reads_script_first
description: 🔴 영구 INVARIANT Rule 1 — 모든 영상 작업의 모든 에이전트는 script.json 을 반드시 첫 행위로 읽는다. Ryan Waller v4 한정 아님. 향후 모든 영상 / 모든 채널 / 모든 에이전트 (Producer 15 + Inspector 17 + 조율자) 적용.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
scope: permanent_all_video_work
priority: critical
---

# 🔴 INVARIANT Rule 1 — 모든 에이전트는 대본을 반드시 보면서 작업한다

## 대표님 원문 (verbatim)

2026-04-23 세션 #34:
> "모든 에이전트는 대본을 반드시 보면서 작업한다."

2026-04-23 직후 추가 지시:
> "이번 뿐만이 아니라 앞으로 하는 모든 영상작업에 필수다"

## 규칙

**모든 영상 작업의 모든 에이전트는** 작업 entry-point 의 **첫 행위로 해당 에피소드의 `script.json` (또는 script_v*.json) 을 로드한다.** 대본 없이 자기 heuristic 만으로 작업 금지.

### 적용 범위 (범용)

| 에이전트군 | 해당 |
|-----------|------|
| Producer 15 | trend-collector / niche-classifier / researcher / director / scene-planner / shot-planner / scripter / script-polisher / voice-producer / asset-sourcer / subtitle-producer / thumbnail-designer / assembler / metadata-seo / publisher |
| Inspector 17 | ins-schema-integrity / ins-timing-consistency / ins-blueprint-compliance / ins-factcheck / ins-narrative-quality / ins-korean-naturalness / ins-thumbnail-hook / ins-tone-brand / ins-readability / ins-license / ins-platform-policy / ins-safety / ins-audio-quality / ins-render-integrity / ins-subtitle-alignment / ins-mosaic / ins-gore |
| 조율자 | shorts-supervisor |

대본 이전 단계 (trend / niche / research / director) 는 **산출 직후** 의 후속 에이전트 호출 사이클에 편입 — 단계가 script 를 생성한 시점부터 이후 모든 후행 에이전트 강제 적용.

### 구현 강제 수단

1. **AGENT.md 의 `<mandatory_reads>` 블록에 `output/<episode>/script.json` 명시** — 전 에이전트 v1.x → v2.0 승격 시 필수 포함
2. **에이전트 entry 로그에 `reads script_v*` 출력 의무** — `grep "reads script" logs/*.log` 로 전수 확인
3. **ins-schema-integrity 에 검증 규칙 추가** — 에이전트 산출물 JSON 의 `metadata.consulted_script_path` 필드 필수
4. **감사 도구** — `scripts/validate/verify_script_consultation.py` (향후) — 파이프라인 실행 후 모든 에이전트 로그 전수 검증

### 위반 사례 (금지)

- 에이전트가 script.json 없이 "일반적으로 crime-noir 은 이렇다" heuristic 로 판단
- 에이전트가 자기 입력 (예: visual_directing 한 줄) 만 보고 전체 대본 맥락 무시
- shot-level 에이전트가 section 단위만 읽고 shot 내부 text 무시

## Why

세션 #34 Ryan Waller v1~v3.2 반복 실패 root cause = 에이전트가 대본 읽지 않고 자기 입력만 보고 판단 → 대본-영상 불일치 반복. 대표님 "대본이랑 영상이랑 따로놀잖아" (v2 판정), "대본대로 영상이 움직여야된다" (v3.2 판정).

Reference shorts_naberal (elisa-lam 등) 은 section 별 visual_directing 필드로 명시적 대본-영상 동기화. 우리 파이프라인은 이 연결고리 구조적으로 부재 → 이를 INVARIANT 로 격상.

## How to apply (실 체크포인트)

1. **새 영상 시작 시**: script.json 이 생성된 시점 부터 모든 후행 에이전트의 mandatory_reads 에 포함되었는지 확인
2. **에이전트 수정/신규 시**: AGENT.md 에 script.json read 조항 삽입
3. **파이프라인 실행 시**: 각 에이전트 로그 첫 줄 "reads script_v*" 출력 확인
4. **검수 시**: 대본-산출물 매칭 spot-check

## 검증

```bash
# 각 에이전트 실행 로그 전수 검증
grep -l "reads script" logs/*.log | wc -l  # 모든 에이전트 로그 파일 수와 일치해야
```

## Cross-reference

- `feedback_script_markers_absolute_compliance.md` (Rule 2 — 대본 표현 준수)
- `feedback_agents_require_visual_analysis.md` (Rule 3 — subagent vision)
- `project_script_driven_agent_pipeline_v1.md` (전체 pipeline SSOT)
- CLAUDE.md 금기 #9 "33 에이전트 초과 금지" — 신규 에이전트 생성 대신 기존 에이전트의 AGENT.md patch
- v3 `feedback_script_video_sync_via_visual_directing.md` (전단계 박제, 본 Rule 1 이 상위 규칙)
