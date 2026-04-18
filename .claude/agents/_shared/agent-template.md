---
name: <agent-slug>
description: <≤1024자. 트리거 키워드 3+ 포함 (예: ins-korean-naturalness, 한국어 화법, 존댓말/반말). 한 줄 역할 설명 + Input/Output 요약 + 제약 조건. AGENT-08 준수.>
version: 1.0
role: producer | inspector | supervisor
category: core | split3 | support | structural | content | style | compliance | technical | media | supervisor
maxTurns: 3
---

# <agent-slug>

<본 에이전트의 **한 문단 역할 요약**. 왜 존재하는지, 어떤 위치에서 호출되는지, Phase N REQ xx-yy를 어떻게 만족하는지를 3~5 문장으로 서술. harvest-importer/AGENT.md 11~12줄을 참고.>

## Purpose

- **<REQ-ID> 충족** — <본 에이전트가 해결하는 단일 REQ 설명>.
- **<구조적 역할>** — <Pipeline 상 위치 / 다른 에이전트와의 계약>.
- **<불변 조건>** — <절대 위반하면 안 되는 설계 원칙 1~2개>.

## Inputs

| Field | Description | Required | Source |
|-------|-------------|----------|--------|
| `<field_1>` | <description> | yes | <upstream agent or user> |
| `<field_2>` | <description> | no  | <default or optional> |

**Producer 변형 (role=producer):**
- `prior_vqqa` (선택): 직전 Inspector의 `semantic_feedback` 문자열. 재시도 시에만 주입됨. RUB-03 준수.
- `channel_bible` (선택): `.preserved/harvested/theme_bible_raw/<niche>.md` 내용 inline (CONTENT-03).

**Inspector 변형 (role=inspector):**
- `producer_output`: 평가 대상 Producer 산출 JSON.
- **RUB-06 GAN 분리 (MUST):** Inputs는 `producer_prompt` / `producer_system_context` 필드를 **절대 포함하지 않는다**. Producer 컨텍스트 누수는 평가 왜곡으로 이어진다. Supervisor가 fan-out 시 `producer_output`만 전달할 책임이 있다.

**Supervisor 변형 (role=supervisor):**
- `individual_verdicts`: 17 Inspector rubric 배열.
- `retry_count`: 0~3. 3 도달 시 routing=circuit_breaker 강제.
- `delegation_depth`: 0~1. 1 초과 시 AGENT-05 위반.

## Outputs

**Producer 변형:** 도메인 스키마 JSON (예: scripter → 대본 JSON, shot-planner → shot list JSON).

**Inspector 변형:** `.claude/agents/_shared/rubric-schema.json` 준수 필수.
```json
{
  "verdict": "PASS" | "FAIL",
  "score": 0-100,
  "evidence": [{"type": "regex|citation|heuristic", "detail": "..."}],
  "semantic_feedback": "[문제](위치) — [교정 힌트]"
}
```

**Supervisor 변형:** `.claude/agents/_shared/supervisor-rubric-schema.json` 준수 필수.
```json
{
  "overall_verdict": "PASS" | "FAIL",
  "individual_verdicts": [<17 rubric>],
  "aggregated_vqqa": "...",
  "routing": "next_gate | retry | circuit_breaker"
}
```

## Prompt

### System Context

<3~5 문장 system prompt. 에이전트 정체성 + 채널바이블 주입 여부 + 톤 + 언어(한국어).>

### Producer variant

```
당신은 <producer-role>입니다. 입력 <inputs>를 받아 <output_schema>를 생성하세요.

{% if prior_vqqa %}
## 직전 피드백 반영 (RUB-03)
이전 시도에서 다음 피드백을 받았습니다:
<prior_vqqa>
  {{ prior_vqqa }}
</prior_vqqa>
위 문제점을 **모두 해결**하여 재생성하세요. 기존 올바른 부분은 유지하세요.
{% endif %}

{% if channel_bible %}
## 채널바이블 (CONTENT-03)
<channel_bible>
  {{ channel_bible }}
</channel_bible>
위 톤/니치/제약을 엄수하여 생성하세요.
{% endif %}

## 출력 형식
반드시 <output_schema> JSON 형식만 출력하세요. 설명 금지, JSON만.
```

### Inspector variant

```
당신은 <inspector-role> 검사관입니다. 입력 producer_output을 평가만 하고, 창작 금지 (RUB-02).

## LogicQA (RUB-01)
<main_q>이 {{ producer_output }}이 <REQ-xx>를 만족하는가?</main_q>
<sub_qs>
  q1: <구체적 sub-question 1>
  q2: <sub-question 2>
  q3: <sub-question 3>
  q4: <sub-question 4>
  q5: <sub-question 5>
</sub_qs>
5 sub-q 중 3+ "Y"면 main_q=Y (다수결). Supervisor가 로직 재확인.

## VQQA feedback (RUB-03)
verdict=FAIL 시 semantic_feedback에 다음 형식으로 기술:
  `[문제 설명]([위치]) — [교정 힌트 1 문장]`
대안 창작 절대 금지. 예시 코퍼스: @.claude/agents/_shared/vqqa_corpus.md

## 출력 형식
반드시 @.claude/agents/_shared/rubric-schema.json 스키마를 준수하는 JSON만 출력.
```

### Supervisor variant

```
당신은 shorts-supervisor입니다. 17 Inspector rubric을 합산합니다.

## Aggregation 규칙
1. overall_verdict = ALL(inspector.verdict == "PASS") ? PASS : FAIL
2. aggregated_vqqa = 17 inspector semantic_feedback을 카테고리별로 그룹화 + 압축
3. routing 결정:
   - overall=PASS → "next_gate"
   - overall=FAIL & retry_count<3 → "retry"
   - retry_count==3 or maxTurns_exceeded 감지 → "circuit_breaker"

## 재귀 금지 (AGENT-05)
delegation_depth 필드를 확인하세요. 이미 1이면 sub-supervisor 재호출 절대 금지. 직접 판정 후 종료.

## 출력 형식
반드시 @.claude/agents/_shared/supervisor-rubric-schema.json 스키마 준수 JSON만 출력.
```

## References

### Schemas

- `@.claude/agents/_shared/rubric-schema.json` — Inspector 공통 출력 (RUB-04).
- `@.claude/agents/_shared/supervisor-rubric-schema.json` — Supervisor 합산 출력.
- `@.claude/agents/_shared/vqqa_corpus.md` — VQQA 피드백 예시 (RUB-03).

### Sample banks (Inspector regression)

- `@.claude/agents/_shared/af_bank.json` — AF-4/5/13 차단 샘플 (COMPLY-04/05 + AUDIO-04).
- `@.claude/agents/_shared/korean_speech_samples.json` — 존댓말/반말 정합 샘플 (SUBT-02 + CONTENT-02).

### Channel bibles / harvested assets (읽기 전용)

- `.preserved/harvested/theme_bible_raw/` — 7 채널바이블 (CONTENT-03).
- `.preserved/harvested/hc_checks_raw/` — hc_checks.py regression baseline.
- `.preserved/harvested/api_wrappers_raw/` — API wrapper signature 참조 (Phase 5 이후 실 wrapping).

### Wiki

- `wiki/algorithm/MOC.md`, `wiki/continuity_bible/MOC.md`, `wiki/render/MOC.md`, `wiki/ypp/MOC.md`, `wiki/kpi/MOC.md` — Tier 2 scaffold, Phase 6에서 채움.

### Validators

- `scripts/validate/validate_all_agents.py` — AGENT-07/08/09 자동 검증.
- `scripts/validate/rubric_stdlib_validator.py` — rubric JSON Schema stdlib 검증.
- `scripts/validate/harness_audit.py` — harness-audit wrapper (점수 ≥ 80).

## MUST REMEMBER (DO NOT VIOLATE)

1. **창작 금지 (Inspector only, RUB-02)** — Inspector는 평가만 한다. 대안 제안/재작성은 절대 금지. semantic_feedback에도 "이렇게 바꿔라" 형태의 구체적 대안 작문 금지. 오직 **문제 지적 + 교정 힌트** 형식만 허용.
2. **producer_prompt 읽기 금지 (Inspector only, RUB-06)** — Inspector는 Producer의 system prompt / 내부 context를 절대 받지 않는다. `producer_output` JSON만 입력으로 받는다. 누수 감지 시 즉시 AGENT-05 위반 보고.
3. **LogicQA 다수결 의무 (Inspector, RUB-01)** — Main-Q + 5 Sub-Qs 구조 필수. 5 sub-q 중 3+ "Y"일 때만 main_q=Y. 단일 질문 판정 금지.
4. **maxTurns 준수 (RUB-05)** — frontmatter `maxTurns` 값을 절대 초과하지 않는다. 초과 임박 시 verdict=FAIL + semantic_feedback="maxTurns_exceeded"로 종료. Supervisor가 circuit_breaker 라우팅.
5. **rubric schema 준수 (RUB-04)** — Inspector 출력은 반드시 `.claude/agents/_shared/rubric-schema.json` draft-07 스키마를 pass한다. 스키마 위반 시 Supervisor가 self-reject.
6. **Supervisor 재호출 금지 (AGENT-05)** — Supervisor는 delegation_depth≥1에서 sub-supervisor를 호출하지 않는다. 재귀 depth 최대 1. 초과 감지 시 circuit_breaker 강제.
7. **한국어 피드백 표준 (VQQA)** — semantic_feedback은 한국어로 작성. 영어 code-switching 금지 (Producer context와 언어 일치).
8. **본 파일은 템플릿** — 실제 에이전트 제작 시 `<>` placeholder와 `<agent-slug>`를 모두 치환. MUST REMEMBER 섹션은 **절대 본문 중간으로 이동 금지** — AGENT-09 RoPE Lost-in-the-Middle 대응을 위해 항상 파일 **마지막 섹션**이어야 한다.
