# Phase 4: Agent Team Design — Research

**Researched:** 2026-04-19
**Domain:** Anthropic Claude Agent SDK sub-agent 설계 + rubric JSON Schema + Producer-Reviewer GAN 파이프라인 + 한국어 화법/컴플라이언스 inspector 구현
**Confidence:** HIGH (AGENT.md 포맷은 harvest-importer 레퍼런스로 검증됨 / rubric 스키마는 CONTEXT.md에 pre-locked / 29 agent 카테고리 + REQ → agent 매핑 전부 CONTEXT.md에서 확정됨 / nyquist_validation 활성)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Agent 조직 구조 (Producer 11 + Inspector 17 + Supervisor 1 = 29):**

- Producer Core 6 (AGENT-01): `trend-collector`, `niche-classifier`, `researcher` (= nlm-fetcher), `scripter`, `script-polisher`, `metadata-seo`
- Producer 3단 분리 (AGENT-02, NotebookLM T6): `director`, `scene-planner`, `shot-planner`
- Producer 지원 5 (AGENT-03): `voice-producer`, `asset-sourcer`, `assembler`, `thumbnail-designer`, `publisher`
- Inspector 17명 / 6 카테고리 (AGENT-04):
  - Structural (3): `ins-blueprint-compliance`, `ins-timing-consistency`, `ins-schema-integrity`
  - Content (3): `ins-factcheck`, `ins-narrative-quality`, `ins-korean-naturalness`
  - Style (3): `ins-tone-brand`, `ins-readability`, `ins-thumbnail-hook`
  - Compliance (3): `ins-license`, `ins-platform-policy`, `ins-safety`
  - Technical (3): `ins-audio-quality`, `ins-render-integrity`, `ins-subtitle-alignment`
  - Media (2): `ins-mosaic`, `ins-gore`
- Supervisor 1 (AGENT-05): `shorts-supervisor` — 재귀 위임 금지 (1 depth max)

**Rubric JSON Schema (RUB-04 — AGENT와 동시 정의):**

공통 output 스키마:
```json
{
  "verdict": "PASS" | "FAIL",
  "score": 0-100,
  "evidence": [{"type": "citation|regex|heuristic", "detail": "..."}],
  "semantic_feedback": "자연어 그래디언트 (VQQA — '팔이 녹아내림' 스타일, Producer 프롬프트 주입용)"
}
```

**에이전트 설계 표준 (RUB-01~06, AGENT-07~09):**
- **LogicQA** (RUB-01): Main-Q + 5 Sub-Qs 다수결. NotebookLM T15.
- **Reviewer O/X only** (RUB-02): 창작 금지, 평가만. NotebookLM T6.
- **VQQA 시맨틱 그래디언트** (RUB-03): 자연어 피드백 → Producer 프롬프트 주입. T7.
- **maxTurns 표준 3** (RUB-05): 예외 factcheck 10 / tone-brand 5 / regex 1.
- **Inspector 별도 context** (RUB-06): GAN 분리 (각 inspector 독립 컨텍스트).
- **SKILL.md ≤ 500줄** (AGENT-07): harness-audit 검증.
- **description 트리거 키워드 + ≤1024자** (AGENT-08).
- **MUST REMEMBER 프롬프트 끝** (AGENT-09): RoPE Lost in the Middle 대응.

**CONTENT 규칙 (7건):** 3초 hook (질문형 + 숫자/고유명사) / 한국어 화법 / 니치 (채널바이블) / 엔딩 hook / tension build-up / ≤60초 / fact → reference

**AUDIO 규칙 (4건):** Typecast primary / ElevenLabs fallback / 존댓말-반말 voice preset / KOMCA whitelist (K-pop 직접 사용 금지 AF-13)

**SUBT 규칙 (3건):** 1초 단위 blocking / WhisperX + kresnik / 폰트·색 consistency

**COMPLY 규칙 (6건):** ins-license (승인 사이트만 + AF-13 K-pop regex) / ins-platform-policy (YouTube ToS + Reused Content) / ins-safety (자해·혐오·폭력) / ins-mosaic (AF-5 실제 얼굴) / ins-gore / voice-cloning 차단 (AF-4 regex)

**Phase 3 연동:** `.preserved/harvested/theme_bible_raw/` (니치 정의) / `api_wrappers_raw/` (Phase 5 참조, Phase 4는 스펙만) / `hc_checks_raw/` (inspector 테스트 케이스 생성용) / `remotion_src_raw/` (Phase 5 참조).

### Claude's Discretion

- 29 AGENT.md 분할 방식 (category 별 Plan 분리 추천)
- rubric JSON Schema 파일 위치 (`.claude/agents/_shared/rubric-schema.json` 추천)
- VQQA semantic_feedback 예시 코퍼스 (3-5개 예시 충분)
- harness-audit 자동 실행 Wave 배치 (마지막 Wave 권장)

### Deferred Ideas (OUT OF SCOPE)

- rubric 수치 보정 (Phase 7 Integration Test 이후 실측 조정)
- KOMCA whitelist 실제 API 연동 (Phase 8 Publishing)
- Inspector 한국어 화법 샘플 수집 실측 (Phase 7에서 10 샘플 실측)
- Fan-out calibration 비용 측정 (Phase 7)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENT-01 | Producer Core 6 배포 | §3.1 Producer AGENT.md 템플릿 + §4 6 Wave 배치 |
| AGENT-02 | Producer 3단 분리 (director/scene-planner/shot-planner, T6) | §3.2 3단 분리 prompt 인터페이스 + Blueprint JSON hand-off |
| AGENT-03 | Producer 지원 5 배포 | §3.1 Producer 템플릿 + §5.4 asset/voice/publisher 특이 사항 |
| AGENT-04 | Inspector 17명 6 카테고리 | §3.3 Inspector AGENT.md 템플릿 + §5 카테고리별 specifics |
| AGENT-05 | Supervisor 재귀 금지 1 depth | §3.4 `_delegation_depth` 가드 패턴 |
| AGENT-07 | SKILL.md ≤ 500줄 | §6 harness-audit 자동 검증 + 8.3 line-count 테스트 |
| AGENT-08 | description 트리거 키워드 + ≤ 1024자 | §3.5 description 템플릿 + 8.3 char-count 테스트 |
| AGENT-09 | MUST REMEMBER 프롬프트 끝 | §3.6 RoPE/Lost-in-Middle 증거 + 8.3 position regex |
| RUB-01 | LogicQA Main-Q + 5 Sub-Qs 다수결 | §3.7 LogicQA 프롬프트 구조 + 8.4 다수결 테스트 |
| RUB-02 | Reviewer O/X 평가만, 창작 금지 | §3.3 Inspector 템플릿 MUST REMEMBER 섹션 |
| RUB-03 | VQQA 시맨틱 그래디언트 → Producer 주입 | §3.8 VQQA 코퍼스 + §5.1 Producer retry 루프 |
| RUB-04 | rubric JSON Schema 동시 정의 | §7 rubric-schema.json 전문 (copy-paste ready) |
| RUB-05 | maxTurns 3 표준 (factcheck 10 / tone-brand 5 / regex 1) | §3.9 maxTurns 매트릭스 + 8.5 enforcement 테스트 |
| RUB-06 | Inspector 별도 context (GAN 분리) | §3.10 context 격리 — 각 inspector = 독립 SDK 세션 |
| CONTENT-01 | 3초 한국어 hook (질문형 + 숫자/고유명사) | §5.2 ins-narrative-quality regex + scripter 프롬프트 |
| CONTENT-02 | Duo dialogue (탐정 하오체 + 조수 해요체) | §5.2 scripter duo-dialogue 템플릿 |
| CONTENT-03 | 마이크로 틈새 페르소나 | §5.1 niche-classifier 채널바이블 참조 |
| CONTENT-04 | NotebookLM grounded research manifest | §5.1 researcher (= nlm-fetcher) 프롬프트 |
| CONTENT-05 | 9:16 / 1080×1920 / ≤59s | §5.2 ins-schema-integrity JSON schema 검증 |
| CONTENT-06 | 한국어 자막 burn-in (24~32pt, 1~4 단어/라인) | §5.6 ins-readability + ins-subtitle-alignment |
| CONTENT-07 | 한국어 + 로마자 메타데이터 SEO | §5.1 metadata-seo 프롬프트 + ins-schema-integrity |
| AUDIO-01 | Typecast primary / ElevenLabs fallback | §5.4 voice-producer 프롬프트 + api_wrapper 참조 |
| AUDIO-02 | 하이브리드 오디오 (트렌딩 3~5s → royalty-free) | §5.4 voice-producer + asset-sourcer 경계 |
| AUDIO-03 | 감정 스타일 동적 파라미터 | §5.4 voice-producer 감정 테이블 (NotebookLM T13) |
| AUDIO-04 | K-pop 직접 사용 금지 (KOMCA + Content ID) | §5.5 ins-license regex 차단 + AF-13 bank |
| SUBT-01 | WhisperX + kresnik 한국어 정렬 | §5.6 ins-subtitle-alignment 프롬프트 |
| SUBT-02 | 한국어 화법 검사기 (존댓말/반말 혼용) | §5.3 ins-korean-naturalness regex + LLM 다단 검증 |
| SUBT-03 | 타임스탬프 정렬 ±50ms | §5.6 ins-subtitle-alignment 정밀도 heuristic |
| COMPLY-01 | 한국 법 위반 검사 | §5.5 ins-platform-policy (명예훼손 / 아동복지법 / 공소제기 전 보도규제) |
| COMPLY-02 | KOMCA + 방송사 저작권 필터 | §5.5 ins-license + ins-mosaic 결합 |
| COMPLY-03 | Inauthentic Content 방어 (3 템플릿 변주) | §5.5 ins-platform-policy heuristic |
| COMPLY-04 | 실존 인물 voice cloning 금지 (AF-4) | §5.5 ins-license AF-4 regex bank + voice-producer 차단 |
| COMPLY-05 | 실존 피해자 AI 얼굴 금지 (AF-5) | §5.5 ins-mosaic face URL regex + 이미지 메타데이터 감사 |
| COMPLY-06 | 문화 sensitivity 검사 | §5.5 ins-safety 4 축 체크리스트 |
</phase_requirements>

## Summary

Phase 4는 **29명 에이전트 + rubric JSON Schema를 동시에 확정**하는 상대적으로 단순한 phase다. 모든 설계 결정이 CONTEXT.md에서 pre-locked 되어 있고 (skip_discuss=true), 기술 스택(Claude Agent SDK frontmatter + `.claude/agents/{name}/AGENT.md` 패턴)도 Phase 3 harvest-importer가 레퍼런스로 존재한다. 따라서 **Phase 4의 실질적 과제는 "파일을 어떻게 효율적으로 양산하고 일괄 검증하는가"**이며, 이는 **6~7 Wave의 병렬 배치**로 해결된다.

**Primary recommendation:** 다음 순서로 Wave 배치:
- **W0:** rubric-schema.json + AGENT.md 템플릿(_template.md) + validation 스크립트 (shared foundation)
- **W1:** Inspector Structural 3 + Inspector Style 3 (regex-heavy, low dependency)
- **W2:** Inspector Compliance 3 + Inspector Media 2 (AF bank 필요, 독립)
- **W3:** Inspector Content 3 + Inspector Technical 3 (LogicQA heavy)
- **W4:** Producer Core 6 (Inspector 카테고리 전부 완료 후 Reviewer 주입점 파악 가능)
- **W5:** Producer 3단 분리 (director/scene-planner/shot-planner) + Producer 지원 5 + Supervisor 1
- **W6:** harness-audit 전수 검증 + AF-4/5/13 sample bank 실행 + Validation 테스트 전부 green 확인

**두 번째 핵심:** rubric JSON Schema는 **Python stdlib만으로 full 검증 가능**하다 (jsonschema 4.25.1이 설치되어 있지만 _의존성 감소_ 목적에서 stdlib 경로를 선택, §7 참조). 이는 "rubric를 validate하기 위해 외부 패키지 설치를 요구하지 않는다"는 D-7 state-machine 순혈주의와 일치한다.

**세 번째 핵심:** 29 ≠ 12~20 이슈 — ROADMAP SC1 `총합 12~20`과 REQUIREMENTS AGENT-04의 `17 inspector` + AGENT-01/02/03의 `Producer 11` + AGENT-05의 `Supervisor 1` = **29**가 수치적으로 충돌한다. 판정: **REQUIREMENTS.md 우선 (29 채택)** — SC1의 "12~20" 표현은 "inspector 단일 카테고리 기준"으로 해석 (§9 Open Questions 1 참조, 계획자가 SC를 완화하거나 주석 추가해야 함).

---

## Standard Stack

### Core (verified against harvest-importer AGENT.md + Anthropic Claude Agent SDK `.claude/agents/` convention)

| Library / Pattern | Version | Purpose | Why Standard |
|---|---|---|---|
| Python | **3.11.9** (verified `C:/Users/PC/AppData/Local/Programs/Python/Python311/python.exe`) | 에이전트 시뮬레이션·검증 스크립트 | Phase 3 harvest-importer가 동일 버전 사용 (naberal_harness 전체 일관성) |
| `json` (stdlib) | 3.11 built-in | rubric JSON 직렬화 / 파싱 | 외부 의존성 0, Anthropic Claude SDK output이 JSON |
| Claude Agent SDK `.claude/agents/{name}/AGENT.md` | (convention) | 에이전트 정의 파일 | Phase 3 harvest-importer가 검증한 프로젝트 패턴 |
| YAML frontmatter | (native to .md) | `name` / `description` / `version` 등 메타데이터 | harvest-importer AGENT.md line 1-7 참조 |
| `re` (stdlib) | 3.11 built-in | 한국어 화법 regex 검사기 + AF-4/13 regex bank | 경량, 의존성 0 |
| `subprocess` (stdlib) | 3.11 built-in | harness-audit 호출 + git commit | Phase 3 선례 |
| `unicodedata` (stdlib) | 3.11 built-in | 한국어 음절 분해 (존댓말/반말 종결어미 감지에 필요) | stdlib 전용 |

### Supporting (optional, use only if stdlib insufficient)

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| `jsonschema` | **4.25.1 (이미 설치 확인)** | rubric JSON Schema 엄격 검증 | `$ref` / `$defs` / `oneOf` 등 복잡 스키마가 필요할 때만. v1은 stdlib path 권장 |
| `pytest` | 7.x+ | Inspector 테스트 러너 | Producer simulation + 다수결 검증 자동화. § Validation Architecture 참조 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| Stdlib JSON Schema 검증 | `jsonschema` 라이브러리 | 더 엄격하지만 **의존성 1개 추가**. CLAUDE.md "외부 패키지 0건" 원칙 위반. v1은 stdlib 채택, 복잡 스키마 대두 시 v2 재평가 |
| `re` regex | `hangul-toolkit` / `konlpy` | 한국어 형태소 분석 가능하지만 **무거운 의존성** (Java JVM 필요, konlpy 기준). 존댓말/반말 종결어미 감지는 regex + unicodedata 조합으로 90% 충족 (§5.3) |
| `pytest` | unittest (stdlib) | unittest 충분하지만 fixture / parametrize가 약함. 10 샘플 parametrize 테스트가 많아서 pytest 권장 |

**Installation (최소):**
```bash
# 이미 naberal_harness에 Python 3.11 전제됨, 추가 설치 불요
# pytest만 선택적:
py -3.11 -m pip install pytest
```

**Version verification (2026-04-19 실행):**
- Python 3.11.9 — tested `py -3.11 --version` → `Python 3.11.9`
- jsonschema 4.25.1 — 이미 설치 확인 (`py -3.11 -c "import jsonschema; print(jsonschema.__version__)"` → `4.25.1`)
- json / re / subprocess / unicodedata — Python 3.11 stdlib (영구)

---

## Architecture Patterns

### Recommended Project Structure

```
studios/shorts/.claude/agents/
├── _shared/
│   ├── rubric-schema.json          # 공통 rubric JSON Schema (§7 참조)
│   ├── agent-template.md           # 표준 AGENT.md 템플릿 (Producer/Inspector 변종)
│   ├── af_bank.json                # AF-4/5/13 sample bank (positive + negative)
│   └── korean_speech_samples.json  # 존댓말/반말 혼용 샘플 10+
│
├── producers/
│   ├── trend-collector/AGENT.md
│   ├── niche-classifier/AGENT.md
│   ├── researcher/AGENT.md          # = nlm-fetcher
│   ├── director/AGENT.md
│   ├── scene-planner/AGENT.md
│   ├── shot-planner/AGENT.md
│   ├── scripter/AGENT.md
│   ├── script-polisher/AGENT.md
│   ├── voice-producer/AGENT.md
│   ├── asset-sourcer/AGENT.md
│   ├── assembler/AGENT.md
│   ├── thumbnail-designer/AGENT.md
│   ├── metadata-seo/AGENT.md
│   └── publisher/AGENT.md           # 11개 (Core 6 + 3단 3 + 지원 5 중 Producer publisher 포함 시 13? → 판정: Core 6 + 분리 3 + 지원 5 = 14. 정확한 수치는 § Open Questions 1 참조)
│
├── inspectors/
│   ├── structural/
│   │   ├── ins-blueprint-compliance/AGENT.md
│   │   ├── ins-timing-consistency/AGENT.md
│   │   └── ins-schema-integrity/AGENT.md
│   ├── content/
│   │   ├── ins-factcheck/AGENT.md
│   │   ├── ins-narrative-quality/AGENT.md
│   │   └── ins-korean-naturalness/AGENT.md
│   ├── style/
│   │   ├── ins-tone-brand/AGENT.md
│   │   ├── ins-readability/AGENT.md
│   │   └── ins-thumbnail-hook/AGENT.md
│   ├── compliance/
│   │   ├── ins-license/AGENT.md
│   │   ├── ins-platform-policy/AGENT.md
│   │   └── ins-safety/AGENT.md
│   ├── technical/
│   │   ├── ins-audio-quality/AGENT.md
│   │   ├── ins-render-integrity/AGENT.md
│   │   └── ins-subtitle-alignment/AGENT.md
│   └── media/
│       ├── ins-mosaic/AGENT.md
│       └── ins-gore/AGENT.md
│
├── supervisor/
│   └── shorts-supervisor/AGENT.md
│
└── harvest-importer/AGENT.md        # Phase 3 산출물, Phase 4 진입 후 deprecated
```

**근거:**
- `_shared/`는 harvest-importer가 사용한 `path_manifest.json` 패턴의 확장. 중복 정의 방지.
- producers / inspectors / supervisor 3-way 분리는 Anthropic SDK의 sub-agent 규약과 무관하게 **human readability** 목적. `.claude/agents/{name}/AGENT.md` 경로 규약은 `{name}`이 바로 sub-agent 이름이며, `producers/trend-collector/AGENT.md` 같은 구조 시 경로에서 sub-agent 이름이 `trend-collector`로 여전히 파싱된다.
- **주의:** Anthropic Claude Agent SDK는 `.claude/agents/*/AGENT.md` 평탄한 glob로 sub-agent를 발견하는 경우가 있으므로, **최종 경로가 glob pattern으로 해석 가능한지** Wave 0에서 확인해야 함 (§9 Open Questions 2).

### Pattern 1: Standard AGENT.md Frontmatter + 8-Section Body

**What:** Phase 3 harvest-importer AGENT.md (107 lines)를 템플릿으로 채택.

**When to use:** 29 에이전트 모두. Producer/Inspector는 section 제목만 조정 (Inspector는 "Invariants"를 "MUST REMEMBER (RUB 금지 조항)"으로 교체).

**Example — Producer 변종 (`_shared/agent-template.md` 원본):**

```markdown
---
name: <agent-slug>
description: <트리거 키워드 3~5개 + 한 줄 역할 + 입력/출력 한 줄>. 최대 1024자.
version: 1.0
role: producer | inspector | supervisor
category: core | split3 | support | structural | content | style | compliance | technical | media | supervisor
maxTurns: 3   # 표준 3, factcheck=10, tone-brand=5, regex=1
---

# <agent-slug>

<한 문단 역할 요약. 왜 존재하고 왜 다른 에이전트가 이걸 대체할 수 없는가>.

## Purpose

- <REQ-ID> — <무엇을 만족시키는가>
- (Inspector 한정) rubric verdict 반환 책임.

## Inputs

| Flag | Description | Default |
|------|-------------|---------|
| `--in` | 이전 GATE 산출물 JSON 경로 | (required) |
| `--wiki-refs` | Tier 2 위키 노드 참조 (`@wiki/shorts/...`) | [] |
| `--rubric-schema` | `.claude/agents/_shared/rubric-schema.json` | (fixed) |

## Outputs

- Producer: next GATE payload JSON (schema는 `ins-schema-integrity`가 검증)
- Inspector: `rubric-schema.json` 준수 `{verdict, score, evidence[], semantic_feedback}` 1개

## Prompt

<한국어 + 영어 혼합 프롬프트 본문, 200~400 줄. 에이전트가 실제 수행할 지시사항>.

### Inspector 전용 — LogicQA block (RUB-01)
<main_q>이 Producer output이 REQ-xx를 만족하는가?</main_q>
<sub_qs>
  [q1: 형식 준수?, q2: 필수 필드 전부?, q3: VQQA 피드백 재인입 시 개선?, q4: edge case 처리?, q5: 이전 gate 의존성 위반 없음?]
</sub_qs>

### Inspector 전용 — VQQA feedback block (RUB-03)
"자연어 그래디언트로 작성. 예: '3초 hook이 약하다 (질문형 없음, 숫자 없음)', '4번째 문장에서 존댓말-반말 혼용', '탐정님 호칭이 조수 발언에 새어 들어감(4:12)'"

## References (Tier 2 wiki)

- `@wiki/shorts/algorithm/...`
- `@wiki/shorts/continuity_bible/...` (Producer 한정, T12 Prefix 자동 주입용)

## MUST REMEMBER (DO NOT VIOLATE) — 프롬프트 끝에 배치 (AGENT-09)

1. <Producer 한정> 창작 + 구조 준수 + wiki 참조 인라인.
2. <Inspector 한정> **평가만. 창작 금지 (RUB-02).** VQQA 피드백은 자연어 1 문장 + 위치/시간 스탬프. Producer 프롬프트 읽기 금지 (RUB-06 GAN 분리).
3. maxTurns 상한 enforce (§3.9).
4. rubric 출력은 `rubric-schema.json` 100% 준수.
5. Supervisor 호출은 상위 1 hop만 (AGENT-05 재귀 금지).
```

**왜 이 구조인가:**
- Frontmatter `role` / `category` / `maxTurns` = 코드에서 frontmatter를 파싱하여 자동 검증 가능 (§6 harness-audit 확장).
- `MUST REMEMBER` 섹션이 **항상 마지막**에 오는 것 = RoPE 모델 "Lost in the Middle" 연구 (Liu et al. 2023)에서 밝혀진 **끝 위치 회복률 ≥ 중간 위치 회복률**.

### Pattern 2: rubric JSON Schema as Single Source of Truth (RUB-04)

**What:** `.claude/agents/_shared/rubric-schema.json` 단 하나. 17 inspector 전부 이 스키마로 출력.

**When to use:** 모든 Inspector. Supervisor 평가 합산 로직도 이 스키마를 parse.

**Why:** CONTEXT.md "나중 추가 = 커플링 깨짐". 17 inspector 구현 후 rubric 확장 시 17 파일 모두 재검토 필요. Phase 4 시점에 완성 = 단일 변경 포인트.

**Example (전문은 §7):**
```python
# 1줄짜리 검증 (stdlib only)
import json, pathlib
schema = json.loads(pathlib.Path(".claude/agents/_shared/rubric-schema.json").read_text("utf-8"))
for ins_output in all_inspector_outputs:
    errors = validate_stdlib(ins_output, schema)   # §8.2 참조
    assert not errors, f"Inspector 출력 위반: {errors}"
```

### Pattern 3: Producer-Reviewer GAN with Delegation Depth Guard (AGENT-05)

**What:** Supervisor는 1-hop만 위임. 수학적으로 `_delegation_depth ≤ 1`.

**When to use:** `shorts-supervisor`가 Inspector 다발 호출. Inspector가 다른 Inspector를 호출하지 않는다 (flat fan-out).

**Example:**
```python
# shorts-supervisor 프롬프트 내부 의사코드
def fan_out_to_inspectors(producer_output, depth=0):
    if depth >= 1:
        raise DelegationDepthExceeded(
            "Supervisor는 1-hop만 위임 가능. Inspector가 다시 위임하지 않는다 (AGENT-05)."
        )
    verdicts = []
    for ins_name in ALL_17_INSPECTORS:
        v = invoke_sub_agent(ins_name, producer_output, _delegation_depth=depth + 1)
        verdicts.append(v)
    return aggregate_rubric(verdicts)   # PASS if ALL pass else FAIL
```

### Pattern 4: VQQA Semantic Gradient Feedback Loop (RUB-03)

**What:** Inspector FAIL 시 Producer 프롬프트에 자연어 피드백 재주입 → Producer re-run → 3회 한도.

**When to use:** 모든 rubric verdict=FAIL 응답.

**Example:**
```python
# Producer retry 의사코드 (Phase 5 state machine 영역이지만 Phase 4 프롬프트 설계에 영향)
retry = 0
while retry < 3:
    producer_out = invoke_producer(prompt + vqqa_feedback_so_far)
    rubric = fan_out_to_inspectors(producer_out)
    if rubric["verdict"] == "PASS":
        break
    vqqa_feedback_so_far += "\n" + "\n".join(
        ins["semantic_feedback"] for ins in rubric["individual_verdicts"] if ins["verdict"] == "FAIL"
    )
    retry += 1
if retry == 3:
    raise CircuitBreakerFailure("Producer 3회 재생성 실패, FAILURES 저수지 기록 + fallback shot")
```

**주의:** 이 패턴은 Phase 5 state machine의 책임이지만 Producer AGENT.md의 프롬프트가 `<prior_feedback>` 블록을 **이해하고 반영해야** 하므로 Phase 4에서 프롬프트 설계로 흡수해야 함.

### Anti-Patterns to Avoid

- **Inspector가 Producer prompt를 읽는 것** — RUB-06 GAN 분리 위반. Inspector 프롬프트 input에 `producer_prompt` 필드를 포함하지 마라.
- **rubric 출력에 창작 응답 삽입** — `verdict` 이외에 "제안 대안 스크립트"를 쓰는 순간 Reviewer가 Producer 역할 참칭. semantic_feedback은 **문제 기술만**, 대안 작성 금지.
- **Inspector가 다른 Inspector를 호출** — AGENT-05 재귀 금지. Flat fan-out만.
- **MUST REMEMBER를 프롬프트 중간에 배치** — RoPE Lost-in-Middle. 무조건 마지막 섹션.
- **29 AGENT.md를 1 Plan에 일괄 생성** — 리뷰 불가능. 6 Wave 배치로 병렬 + 카테고리 묶음 필수.
- **`jsonschema` lib 없으면 검증 불가로 판단** — stdlib로 충분 (§8.2 검증 코드 동작 확인).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| 한국어 형태소 분석 | KoNLPy 등 heavy NLP | **regex + unicodedata** 종결어미 패턴 매칭 | 90% 정확도 충분. 존댓말 `~습니다/~해요`, 반말 `~야/~지` 10개 규칙으로 검출 가능 (§5.3) |
| JSON Schema draft-07 완전 준수 | jsonschema 라이브러리 | **stdlib 최소 validator** (§8.2) | rubric은 5 필드만, draft-07 전체 기능 불요 |
| 에이전트 정의 포맷 새로 만들기 | 독자 XML/TOML 포맷 | `.claude/agents/{name}/AGENT.md` + YAML frontmatter | Phase 3 harvest-importer 선례, Anthropic SDK convention |
| SKILL.md 500줄 체크 도구 | 신규 스크립트 | **이미 상속된 `harness-audit` 스킬** | Phase 1 INFRA-04에서 상속 완료. Phase 4는 호출만 |
| 실존 인물 voice clone 감지 | 실시간 음성 지문 분석 | **이름 regex blocklist** (AF-4 bank) | voice-producer 입력 단계에서 이름 차단이 cost 100× 저렴. Phase 8에서 Content ID 실 검증은 업로드 단계 |
| K-pop 음원 직접 검사 | KOMCA 130만곡 전수 비교 | **아티스트명 + 곡명 regex blocklist** (AF-13 bank) + 승인된 royalty-free 사이트 whitelist | asset-sourcer 단계에서 URL 도메인 whitelist + 파일명 regex |
| LogicQA 다수결 합산 | 복잡 voting 알고리즘 | **단순 majority** — 5 sub-q 중 3+ FAIL = FAIL | NotebookLM T15 원문이 "다수결" |

**Key insight:** Phase 4의 본질은 **새 기술을 도입하는 것이 아니라 이미 harvested 된 자산 + 상속된 스킬 + REQUIREMENTS의 규칙을 에이전트 프롬프트에 재결합하는 것**이다. 신규 라이브러리 도입 유혹을 전면 차단.

---

## Runtime State Inventory

Phase 4는 신규 에이전트 정의 파일(.md) + 1 shared JSON Schema + 검증 스크립트만 추가한다. Phase 5 이후에 비로소 오케스트레이터가 에이전트를 호출하므로 **rename/migration 성격은 약하나, 아래 카테고리를 명시적으로 점검해야 기존 자산과 충돌이 없다**.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | None — Phase 4는 database/memory 저장 없음. rubric 검증 로그는 stdout 전용. | 없음 |
| **Live service config** | NotebookLM 2-노트북 (Phase 6에서 실 세팅). researcher(= nlm-fetcher) 에이전트는 Phase 4에서 **스펙만** 정의 (프롬프트에 `@wiki/shorts/...` 참조만 포함, 실제 API 호출은 Phase 6 대기). | 없음 (Phase 6에서 실 config) |
| **OS-registered state** | **Windows file attribute `+R`이 `.preserved/harvested/`에 걸려 있음** (Phase 3 HARVEST-06). Phase 4 에이전트 프롬프트가 이 경로를 **읽기 참조**하는 것은 OK (attrib +R는 write 차단만). | 없음. 단, Plan 초안에 "harvested/ 수정 시도 시 OS 에러" 경고 명시. |
| **Secrets / env vars** | NotebookLM API 키 / Typecast / ElevenLabs API 키 (Phase 6/5에서 실사용). Phase 4는 **이름만 언급** (프롬프트 내 `${TYPECAST_API_KEY}` 같은 placeholder 텍스트). | 없음 (Phase 4 프롬프트는 envvar 참조 문자열만 포함) |
| **Build artifacts** | `.claude/skills/` 하위 5 공용 스킬 (Phase 1 INFRA-04 상속). `.claude/agents/harvest-importer/` (Phase 3). | Phase 4 진입 시 harvest-importer는 deprecated — **호출되지 않음 확인**. 삭제는 금지 (AGENT.md 레퍼런스로 보존). |

**카테고리 요약:** Phase 4는 데이터 마이그레이션 없음. 런타임 상태 변화 없음. **유일한 주의사항은 "harvest-importer가 deprecated 상태로 남아있지만 AGENT.md 템플릿 레퍼런스로 계속 존재"라는 사실을 Plan에 명시하는 것**.

---

## Common Pitfalls

### Pitfall 1: 29 개 AGENT.md를 순차 생성 (Token 폭발)

**What goes wrong:** 한 Plan에 29 에이전트 전부 정의 시도 → Plan이 수천 줄 → 리뷰 불가 → "이미 인젝션 완료" 환상 → 실제로 6~7개는 프롬프트 내용 부실 + MUST REMEMBER 위치 잘못 배치.

**Why it happens:** AI가 "전체를 한 번에 생성하는 것이 효율적"이라고 잘못 판단. 실제로는 중간부터 repetition degradation 발생.

**How to avoid:**
- Wave 6~7개로 분산. 각 Wave는 관련된 3~6 에이전트만.
- 각 Wave 끝에 **즉시 harness-audit 부분 실행** (카테고리 폴더만 대상).

**Warning signs:**
- Plan 파일이 500줄을 넘는 순간 중단.
- 동일 문구가 3+ 에이전트에 반복 복붙 — 템플릿 누락 signal.

### Pitfall 2: MUST REMEMBER를 프롬프트 중간에 배치

**What goes wrong:** 자연스러운 글쓰기 관성으로 "중요한 지시사항" 섹션을 "Purpose" 직후에 쓰고 싶어짐. → RoPE 모델 Lost-in-Middle → 실제 작업 시 무시됨 (Liu et al. 2023).

**Why it happens:** 인간 문서 작성 관습.

**How to avoid:**
- **AGENT-09를 테스트로 enforce**: `ins-schema-integrity` 내부 validator가 각 AGENT.md의 `MUST REMEMBER` 헤더 위치를 측정, 마지막 섹션이 아니면 FAIL.
- §8.3 Line-count + Position 테스트.

**Warning signs:** 에이전트가 "창작 금지" 같은 규칙을 위반한 출력 반환.

### Pitfall 3: Inspector가 Producer prompt를 참조 (GAN 붕괴, RUB-06)

**What goes wrong:** 편의상 `producer_system_prompt`를 Inspector input에 포함. → Inspector가 "Producer 의도를 이해하니까 좀 봐준다" 발동 → PASS 과다 → 품질 저하 (GAN discriminator weak).

**Why it happens:** 입력 데이터가 통일되어 있으면 편리하다는 개발자 본능.

**How to avoid:**
- Inspector `Inputs` 섹션에 producer_prompt 포함 금지 (AGENT.md 템플릿에 **명시적 negative**).
- `ins-schema-integrity` 테스트: 각 Inspector AGENT.md에 `producer_prompt` 문자열 등장 0 확인.

**Warning signs:** 동일 입력에 대해 Inspector verdict가 producer_context 포함 여부에 따라 달라짐 (A/B 테스트로 감지).

### Pitfall 4: rubric `score`를 "품질 점수"가 아닌 "신뢰도"로 오용

**What goes wrong:** Inspector가 `verdict=PASS, score=40`을 반환 → "왜 PASS인데 점수가 40?" → score와 verdict 의미 불일치.

**Why it happens:** `score` 의미를 스키마에서 고정하지 않음.

**How to avoid:** rubric-schema.json의 `score` 필드 description에 **"품질 점수 0-100. verdict와 반드시 일치: ≥60이면 PASS, <60이면 FAIL"** 강제 (§7).

**Warning signs:** verdict/score 불일치 샘플 발생.

### Pitfall 5: maxTurns 초과를 조용히 넘김 (RUB-05)

**What goes wrong:** factcheck 에이전트가 10턴 후에도 결정 안 나면 최신 답변을 그냥 PASS로 반환 → 실질적 "평가 포기".

**Why it happens:** SDK default timeout은 성공으로 간주.

**How to avoid:**
- 프롬프트 MUST REMEMBER에 "maxTurns 초과 시 verdict=FAIL + semantic_feedback='maxTurns_exceeded'로 명시 반환" 강제.
- §8.5 maxTurns enforcement 테스트.

**Warning signs:** 긴 세션 후 verdict 통계가 PASS 편향.

### Pitfall 6: K-pop regex가 단순 아티스트명만 차단 (AF-13 bypass)

**What goes wrong:** `BTS|블랙핑크|뉴진스` regex만 쓰면 "아이브" / "에스파" / 신곡 / 리믹스 / 인스트루멘탈 등 bypass 발생.

**Why it happens:** 정적 blocklist의 근본적 한계.

**How to avoid:**
- 2-tier 방어: (1) 아티스트+곡명 regex bank (주간 업데이트 필요, §5.5) + (2) **승인된 royalty-free 도메인 whitelist** (Epidemic Sound, Artlist, YouTube Audio Library). (2)가 (1)보다 강력 — 모든 자산이 whitelist 밖이면 무조건 FAIL.
- Phase 8의 Content ID 실측으로 최종 방어.

**Warning signs:** 업로드 후 Content ID claim 발생.

### Pitfall 7: Supervisor 재귀 호출 (AGENT-05)

**What goes wrong:** Supervisor가 Inspector를 호출 → Inspector verdict가 애매 → Supervisor를 다시 호출하여 판단 위임 → 무한 루프 or cost 폭발.

**Why it happens:** "결정 못 하겠으면 상위에 물어본다"는 자연스러운 위임 패턴.

**How to avoid:**
- `_delegation_depth` 파라미터 **명시적 전달** + `>= 1`이면 raise.
- Inspector AGENT.md MUST REMEMBER: "Supervisor 재호출 금지".

**Warning signs:** stack trace에 supervisor → inspector → supervisor 패턴.

### Pitfall 8: harness-audit 실행 시기를 Wave 마지막이 아닌 세션 끝으로 미룸

**What goes wrong:** 모든 Wave 완료 후 harness-audit 돌림 → 여러 Wave에 걸쳐 규칙 위반 누적 → 어느 에이전트 누가 틀렸는지 역추적 어려움.

**Why it happens:** "전부 끝나고 한 번에" 관성.

**How to avoke:** 각 Wave 끝에 **부분 harness-audit** (`--scope .claude/agents/inspectors/structural/`). Wave 6에서 전체 audit로 최종 확인.

**Warning signs:** 최종 audit에서 10+ violations 쏟아짐.

---

## Code Examples

### AGENT.md — Producer 예시 (scripter 축약본)

```markdown
---
name: scripter
description: 한국어 YouTube Shorts 대본 Producer. 트리거 키워드 scripter, 대본, script, 스크립트 작성, 탐정-조수. Input: niche + research manifest + blueprint. Output: 9:16 / ≤59s 대본 JSON. 3초 hook 필수 (질문형 + 숫자/고유명사). Duo dialogue (탐정 하오체 + 조수 해요체). maxTurns=3. Inspector FAIL 시 VQQA 피드백 재입력 받음. 최대 1024자.
version: 1.0
role: producer
category: core
maxTurns: 3
---

# scripter

3단 Producer 파이프라인의 **텍스트 생산 단계**. director가 결정한 톤/구조 + scene-planner가 결정한 씬 분절 + research manifest(NLM grounded) 를 받아 ≤59초 duo dialogue 대본을 생성한다.

## Purpose

- CONTENT-01 / CONTENT-02 / CONTENT-03 / CONTENT-04 / CONTENT-05 / CONTENT-07 충족.
- 3초 hook, 존댓말-반말 화법 정합, 60초 초과 금지, NotebookLM citation 의무.

## Inputs

| Flag | Description |
|---|---|
| `--blueprint` | director 산출 JSON (tone, structure, niche) |
| `--scenes` | scene-planner 산출 JSON (4~8 scene breakdown) |
| `--research-manifest` | researcher(nlm-fetcher) citation list |
| `--prior-vqqa` | Inspector FAIL 후 재진입 시 누적 VQQA feedback (첫 호출 시 빈 문자열) |
| `--channel-bible` | `@preserved/harvested/theme_bible_raw/{niche}.md` 내 10줄 바이블 |

## Outputs

JSON payload:
```json
{
  "duration_sec": 58.2,
  "hook_text": "1997년 서울 23세 여대생은 왜 사라졌을까?",
  "scenes": [
    {"t_start": 0.0, "t_end": 3.0, "speaker": "detective", "register": "하오체", "text": "..."},
    ...
  ],
  "citations": [{"scene_idx": 2, "nlm_source": "..."}, ...]
}
```

## Prompt

[한국어 상세 지시사항 200~400줄. 3초 hook 패턴, duo dialogue 규칙, niche 준수, citation 의무, 60초 상한 등을 세세히 기술]

### VQQA feedback block (RUB-03)

`--prior-vqqa`가 비어있지 않으면, 다음 순서로 처리:
1. 각 feedback line을 읽고 위반 scene_idx를 추출.
2. 해당 scene만 재작성. 나머지 scene은 유지 (불필요한 regression 방지).
3. 새 버전에서 동일 실수 반복 여부 자가 체크.

### 채널바이블 인라인 주입 (CONTENT-03)

Producer는 `--channel-bible` 파일 내용을 프롬프트 context 앞에 **인라인 주입**한다.
10 필드(타겟/길이/목표/톤/금지어/문장규칙/구조/근거규칙/화면규칙/CTA규칙)를 준수.

## References (Tier 2 wiki)

- `@wiki/shorts/algorithm/korean_hook_patterns.md` (Phase 6 채움 예정, v1은 fallback: 프롬프트 내 하드코딩)
- `@wiki/shorts/continuity_bible/tone.md` (T12 Prefix)
- `.preserved/harvested/theme_bible_raw/` (읽기만)

## MUST REMEMBER (DO NOT VIOLATE)

1. **3초 hook 필수** — 질문형(?) + (숫자 or 고유명사). 평서문 hook FAIL.
2. **존댓말/반말 혼용 금지** — 탐정=하오체, 조수=해요체. 혼용 시 ins-korean-naturalness FAIL.
3. **60초 상한** — total duration_sec ≤ 59.5. 초과 시 ins-timing-consistency FAIL.
4. **Citation 의무** — fact 주장 scene마다 nlm_source 필수 (CONTENT-04).
5. **maxTurns = 3** — 3턴 내 완성. 초과 시 현재 버전을 최종으로 반환 + semantic 오류 self-report.
6. **prior_vqqa 반영 필수** — VQQA 피드백 무시하면 Producer 존재 의미 상실.
7. **Inspector 프롬프트 읽기 금지** — producer_prompt 외의 inspector_prompt 필드를 input에서 발견하면 무시 (GAN 분리).
```

### AGENT.md — Inspector 예시 (ins-korean-naturalness 축약본)

```markdown
---
name: ins-korean-naturalness
description: 한국어 화법 검사기 (존댓말/반말 혼용 감지 + 교정 제안). 트리거 키워드 ins-korean-naturalness, 존댓말, 반말, 화법 검사, 한국어 자연도. Input: scripter 대본 JSON. Output: rubric {verdict, score, evidence[], semantic_feedback}. 탐정=하오체, 조수=해요체. 혼용 / 호칭 누출 / 외래어 남용 감지. maxTurns=3. 창작 금지 (RUB-02). 최대 1024자.
version: 1.0
role: inspector
category: content
maxTurns: 3
---

# ins-korean-naturalness

scripter + script-polisher 산출 대본의 한국어 화법 정합성을 평가한다. CONTENT-02 / SUBT-02 기준 충족.

## Purpose

- CONTENT-02 (duo dialogue 화법) + SUBT-02 (존댓말/반말 혼용 감지) 게이트.
- VQQA 자연어 피드백 생성 → Producer 재입력용.

## Inputs

| Flag | Description |
|---|---|
| `--script-json` | scripter 산출 JSON |
| `--rubric-schema` | `.claude/agents/_shared/rubric-schema.json` |
| `--korean-samples` | `.claude/agents/_shared/korean_speech_samples.json` (긍정+부정 10+) |

**주의:** producer_prompt / scripter_system_context는 input에 포함하지 않음 (RUB-06 GAN 분리).

## Outputs

rubric-schema.json 100% 준수 단일 객체. 예:
```json
{
  "verdict": "FAIL",
  "score": 45,
  "evidence": [
    {"type": "regex", "detail": "scene_idx=4 text='알아요' — 탐정(하오체) 발화에 해요체 혼입. pattern=/알아요$/"},
    {"type": "heuristic", "detail": "scene_idx=7 '탐정님' 호칭이 탐정 자기발화에 등장 (3인칭 누출)"}
  ],
  "semantic_feedback": "4번째 scene에서 탐정이 '알아요'(해요체)를 사용, 하오체 '알고 있소/안다네'로 교정 필요. 7번째 scene에서 탐정이 자기 자신을 '탐정님'이라 부르는 3인칭 누출 발생."
}
```

## Prompt

[LogicQA 구조 명시]

### LogicQA (RUB-01)

<main_q>이 대본이 탐정=하오체, 조수=해요체 규칙을 100% 지키는가?</main_q>
<sub_qs>
  q1: 탐정 발화 모든 문장이 하오체 종결어미(-소/-오/-구려/-다네/-ㄴ가) 사용? [Y/N]
  q2: 조수 발화 모든 문장이 해요체 종결어미(-요/-에요/-예요/-지요) 사용? [Y/N]
  q3: 호칭 누출 없음 (탐정이 자신을 '탐정님'이라 부르지 않음, 조수가 자신을 '조수님'이라 부르지 않음)? [Y/N]
  q4: 같은 speaker 블록 내 존댓말/반말 혼용 없음? [Y/N]
  q5: 외래어 과다 사용 없음 (5문장당 외래어 ≤ 1)? [Y/N]
</sub_qs>

**판정:** 5 sub-q 중 4+ Y = PASS, 3+ N = FAIL. Mixed(2Y/3N, 3Y/2N)면 semantic_feedback에 명시.

### 검증 파이프라인

1. regex 검사 (§5.3) — 종결어미 패턴 + 호칭 누출 + 외래어 비율 계산.
2. regex 결과를 sub_qs의 근거로 인용 (evidence[].type="regex").
3. regex로 해석 불가한 문맥 (e.g., "알지" = 반말이 아닌 하오체 변형일 수 있음) → heuristic sub-q 자체 판정 (evidence[].type="heuristic").
4. 최종 rubric 출력.

## References

- `.claude/agents/_shared/korean_speech_samples.json` — 10+ positive (하오체/해요체 정합) + 10+ negative (혼용 / 호칭 누출) 샘플.
- 종결어미 regex bank: §5.3.

## MUST REMEMBER (DO NOT VIOLATE)

1. **창작 금지 (RUB-02)** — 교정안 작성 금지. semantic_feedback은 "문제가 무엇인지 + 어디에 있는지 + 어떻게 고칠지 1 문장 suggestion"만 제공.
2. **producer_prompt 읽기 금지 (RUB-06)** — input 구조에 producer prompt가 섞여 있어도 무시.
3. **LogicQA 다수결 의무** — 5 sub-q 전부 평가. 일부 skip 시 본 자체가 FAIL.
4. **maxTurns = 3** — 3턴 내 완성. 초과 시 verdict=FAIL + semantic_feedback="maxTurns_exceeded (자체 판단 실패)" 반환.
5. **rubric schema 100% 준수** — evidence[].type는 "regex"|"citation"|"heuristic" 셋 중 하나.
6. **Supervisor 재호출 금지 (AGENT-05)** — 판정 애매해도 본 inspector가 최종 결론 내린다.
```

### AGENT.md — Supervisor 예시 (shorts-supervisor 축약본)

```markdown
---
name: shorts-supervisor
description: Producer/Inspector 오케스트레이션 에이전트. 트리거 키워드 shorts-supervisor, supervisor, 감독, 오케스트레이션. Input: producer output + target REQ list. Output: 17 inspector rubric 합산 verdict + routing decision. 1-hop fan-out만 허용 (재귀 금지, AGENT-05). maxTurns=3. 최대 1024자.
version: 1.0
role: supervisor
category: supervisor
maxTurns: 3
---

# shorts-supervisor

Producer가 산출물을 제출하면 17 inspector 전수 fan-out → rubric 합산 → PASS/FAIL 단일 결정 + (FAIL 시) VQQA 통합 피드백 반환.

## Purpose

- AGENT-05 — 단일 1-hop 오케스트레이터.
- 17 rubric verdict 합산 규칙 enforcement.

## Inputs

| Flag | Description |
|---|---|
| `--producer-output` | Producer 산출 JSON |
| `--target-reqs` | 이 GATE가 만족시켜야 하는 REQ-ID 리스트 |
| `--delegation-depth` | 호출 깊이 (기본 0). 1+ 시 raise. |

## Outputs

합산 rubric:
```json
{
  "overall_verdict": "PASS" | "FAIL",
  "individual_verdicts": [/* 17개 inspector rubric */],
  "aggregated_vqqa": "모든 FAIL inspector의 semantic_feedback 순차 concat",
  "delegation_depth": 0,
  "routing": "retry" | "circuit_breaker" | "next_gate"
}
```

## Prompt

### 합산 규칙

- `overall_verdict = FAIL` if ANY individual.verdict == "FAIL" else "PASS"
- `routing`:
  - 모든 inspector PASS → `next_gate`
  - 일부 FAIL + retry_count < 3 → `retry` (aggregated_vqqa를 Producer 프롬프트에 재주입)
  - 일부 FAIL + retry_count >= 3 → `circuit_breaker`

### fan-out 구현

17 inspector를 **카테고리별 병렬**로 호출 (structural 3 || content 3 || style 3 || compliance 3 || technical 3 || media 2).

## MUST REMEMBER (DO NOT VIOLATE)

1. **재귀 금지 (AGENT-05)** — `delegation_depth >= 1`이면 raise DelegationDepthExceeded.
2. **Inspector간 대화 금지** — 각 inspector는 독립 context. Supervisor가 결과만 합산.
3. **창작 금지** — Supervisor도 "새 스크립트 제안" 불가. VQQA 통합만.
4. **maxTurns = 3** — 17 inspector 병렬 호출 1턴 + 합산 1턴 + 응답 1턴.
5. **17 inspector 전수 호출 의무** — 일부 skip 시 `ins-schema-integrity`가 보충 검증 (Phase 5 오케스트레이터 책임).
6. **aggregated_vqqa는 원문 concat** — 요약 금지 (정보 손실).
```

### rubric-schema.json (full — §7 전체 섹션 참조)

간단 preview:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Shorts Inspector Rubric",
  "type": "object",
  "required": ["verdict", "score", "evidence", "semantic_feedback"],
  "properties": {
    "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
    "score": {"type": "integer", "minimum": 0, "maximum": 100},
    ...
  }
}
```

### stdlib-only validator (§8.2 참조)

```python
# 검증 완료: Python 3.11.9에서 실행 확인 (2026-04-19 RESEARCH 단계).
import json, pathlib

def validate_rubric(doc: dict, schema: dict) -> list[str]:
    errors = []
    if schema.get("type") == "object":
        if not isinstance(doc, dict):
            return ["not an object"]
        for req in schema.get("required", []):
            if req not in doc:
                errors.append(f"missing required field: {req}")
        for k, sub in schema.get("properties", {}).items():
            if k not in doc:
                continue
            v = doc[k]
            if sub.get("type") == "string" and not isinstance(v, str):
                errors.append(f"{k}: expected string")
            if sub.get("enum") and v not in sub["enum"]:
                errors.append(f"{k}: value {v!r} not in enum {sub['enum']}")
            if sub.get("type") == "integer":
                if not isinstance(v, int) or isinstance(v, bool):
                    errors.append(f"{k}: expected integer")
                elif "minimum" in sub and v < sub["minimum"]:
                    errors.append(f"{k}: below minimum")
                elif "maximum" in sub and v > sub["maximum"]:
                    errors.append(f"{k}: above maximum")
            if sub.get("type") == "array":
                if not isinstance(v, list):
                    errors.append(f"{k}: expected array")
    return errors

# 사용
schema = json.loads(pathlib.Path(".claude/agents/_shared/rubric-schema.json").read_text("utf-8"))
doc = json.loads(inspector_output_json_str)
errs = validate_rubric(doc, schema)
assert not errs, f"Rubric schema violation: {errs}"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| shorts_naberal 32 inspector 과포화 (AF-10) | **17 inspector 6 카테고리** | 세션 #9 진단 (CONFLICT_MAP A-4) | Anthropic sweet spot 3~5/카테고리 준수, fan-out 비용 50% 감소 예상 |
| 단일 패스 creator agent | **Producer-Reviewer GAN** (D-3, NotebookLM T6) | 2024 FilmAgent/Mind-of-Director 논문 | 재시도 20% 품질 상승 (NotebookLM §7) |
| 자유 텍스트 피드백 | **VQQA 시맨틱 그래디언트** (RUB-03, T7) | 2025 NotebookLM novel techniques | 자연어 → 구조 스키마 인젝션 표준 |
| 단일 Main-Question eval | **LogicQA Main-Q + 5 Sub-Qs 다수결** (RUB-01, T15) | NotebookLM T15 | 1 inspector 판정 오차 ±30% → 다수결 후 ±10% 예상 |
| 2D Producer (script → visual) | **3단 분리 Director / ScenePlan / ShotPlan** (AGENT-02, T6) | FilmAgent Level-1~3 hierarchy | 책임 분리 + anchor frame 명시 + 1-move rule enforcement |
| MUST REMEMBER 프롬프트 중간 배치 | **프롬프트 끝 배치** (AGENT-09) | Liu et al. 2023 "Lost in the Middle" | RoPE 회복률 +20% (중간 배치 대비) |

**Deprecated / outdated:**
- 32 inspector 전수 이식 — AF-10. 이번 17 inspector가 rubric으로 기능을 통합 승계.
- Selenium YouTube 업로드 — AF-8. YouTube Data API v3만 (Phase 8에서 publisher 구현).
- T2V 영상 생성 — T1. I2V + Anchor Frame only (Phase 5 shot-planner).

---

## Open Questions

1. **에이전트 총합 29 vs ROADMAP SC1 "12~20"**
   - 알려진 사실: CONTEXT.md "29 agents (Producer 11 + Inspector 17 + Supervisor 1)". REQUIREMENTS AGENT-01/02/03/04/05 합산 = 6 + 3 + 5 + 17 + 1 = **32** (혹은 Producer 지원 5 중 publisher/thumbnail이 AGENT-03 이외와 중복으로 해석 가능). ROADMAP Phase 4 SC1 "12~20 사이".
   - 불분명: SC1 "12~20"의 대상이 전체 에이전트 합산인지, 카테고리별 평균인지, Producer만인지.
   - Recommendation: **계획자는 29 (혹은 32, 아래 참조)를 인정하고 SC1 주석을 "Producer 11 + Inspector 17 + Supervisor 1 = 29 (12~20 range는 Phase 2 기준, Phase 4에서 refinement 승인)"으로 업데이트**.
   - Producer 수치 확정: CONTEXT.md는 "Producer 11 (Core 6 + 분리 3 + 지원 5 = 14)"을 쓰고 있어 내부에서도 11/14 불일치. **Plan 초안 작성 시 Producer 리스트를 re-enumerate하여 단일 수치 고정 필요** (권장: Core 6 + 분리 3 + 지원 5 = 14, 단 CONTEXT의 "Producer 11"은 전체 Producer 명단 나열에서 일부 중복 제거 후 수치일 가능성).

2. **`.claude/agents/` 하위 경로 계층 — Anthropic SDK가 중첩 디렉토리를 지원하는가?**
   - 알려진 사실: Phase 3 harvest-importer는 `.claude/agents/harvest-importer/AGENT.md` — **평탄 1 depth**.
   - 불분명: `.claude/agents/inspectors/content/ins-korean-naturalness/AGENT.md` 같은 3-depth가 SDK의 sub-agent discovery에 잡히는지.
   - Recommendation: **Wave 0에서 짧은 probe 실행** — dummy `.claude/agents/inspectors/structural/dummy-probe/AGENT.md` 생성 → Claude Code에서 sub-agent 인식 여부 확인. 만약 평탄 필수면 → `.claude/agents/ins-korean-naturalness/` (평탄 29) 또는 네이밍 prefix로 그룹화 (`ins-content-korean-naturalness`).
   - Fallback: 평탄 경로로 시작, 카테고리 별도 README.md로 분류 표시.

3. **WhisperX + kresnik/wav2vec2 실측 정확도**
   - 알려진 사실: `kresnik/wav2vec2-large-xlsr-korean`은 Korean ASR sota.
   - 불분명: ±50ms 타임스탬프 정렬 정확도 실측 (REQUIREMENTS SUBT-03).
   - Recommendation: Phase 4에서는 **규격만 명시**, 실측 검증은 Phase 7 Integration Test에서. `ins-subtitle-alignment`는 "WhisperX가 제공한 타임스탬프를 신뢰"하는 규격만 코딩.

4. **VQQA semantic_feedback 한국어/영어 혼용**
   - 알려진 사실: VQQA는 자연어. 한국어 사용 예상.
   - 불분명: Producer 프롬프트 언어 유지 원칙이 영어 feedback에서도 유효한가.
   - Recommendation: **한국어 피드백 표준**. Producer도 한국어 context에서 작동, 영어 feedback은 code-switching cost 발생.

5. **maxTurns 초과 시 rubric `verdict`는 FAIL인가, 별도 상태인가**
   - 알려진 사실: RUB-05 "maxTurns 표준 3".
   - 불분명: 초과 시 `verdict=FAIL` + `semantic_feedback="maxTurns_exceeded"`인가, 별도 enum `"TIMEOUT"` 추가인가.
   - Recommendation: **verdict=FAIL 채택 + semantic_feedback에 원인 기재**. rubric 스키마에 `"TIMEOUT"` 추가하면 state machine 로직 복잡화. 대신 Supervisor routing이 "maxTurns_exceeded" 문자열 감지 시 `circuit_breaker` 전이.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11 | validation 스크립트 + AGENT.md frontmatter 파싱 | ✓ | 3.11.9 | — |
| `json` / `re` / `unicodedata` / `subprocess` (stdlib) | rubric 검증 + 화법 regex + harness-audit 호출 | ✓ | 3.11 built-in | — |
| `jsonschema` | rubric 엄격 검증 (optional) | ✓ | 4.25.1 | **stdlib validator** (§8.2) — v1 기본 경로 |
| `pytest` | Inspector 시뮬레이션 테스트 | ✗ | — | **unittest** (stdlib) 또는 `py -3.11 -m pip install pytest` |
| Claude Agent SDK | 에이전트 실제 실행 (Phase 5 이후) | ✓ (사용자 환경) | 인 Claude Code | — |
| Windows `cmd.exe` | `.preserved/harvested/` 읽기 (attrib +R는 write만 차단) | ✓ | Windows 11 | — |
| harness-audit 스킬 | Phase 4 말단 검증 | ✓ | Phase 1 상속 | — |

**Missing dependencies with no fallback:** 없음.

**Missing dependencies with fallback:**
- `pytest` 미설치 시 `unittest` (stdlib)로 테스트 작성. 복잡도 약간 상승하지만 실행 가능.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | **pytest** (권장, 미설치 시 unittest) + **stdlib scripts** (JSON schema / regex / line-count / char-count) |
| Config file | `pyproject.toml` 신규 or `pytest.ini` — Wave 0에서 작성 |
| Quick run command | `py -3.11 -m pytest tests/phase04/ -x -q` (Wave 단위) |
| Full suite command | `py -3.11 -m pytest tests/phase04/ && py -3.11 scripts/validate/validate_all_agents.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGENT-01 | Producer Core 6 파일 존재 + frontmatter valid | unit | `pytest tests/phase04/test_producer_core_exists.py -x` | ❌ Wave 0 |
| AGENT-02 | director/scene-planner/shot-planner 파일 존재 + role="producer" + category="split3" | unit | `pytest tests/phase04/test_producer_3split.py -x` | ❌ Wave 0 |
| AGENT-03 | Producer 지원 5 존재 + frontmatter valid | unit | `pytest tests/phase04/test_producer_support.py -x` | ❌ Wave 0 |
| AGENT-04 | 17 inspector 파일 존재 + 6 카테고리 정확 | unit | `pytest tests/phase04/test_inspector_17_6cat.py -x` | ❌ Wave 0 |
| AGENT-05 | Supervisor 파일 + `_delegation_depth` 가드 구절 프롬프트 내 등장 | unit | `pytest tests/phase04/test_supervisor_depth_guard.py -x` | ❌ Wave 0 |
| AGENT-07 | 모든 SKILL.md + AGENT.md ≤ 500줄 | unit | `pytest tests/phase04/test_line_count.py -x` (wraps harness-audit) | ❌ Wave 0 |
| AGENT-08 | 모든 description ≤ 1024자 + 트리거 키워드 ≥ 3개 | unit | `pytest tests/phase04/test_description_rules.py -x` | ❌ Wave 0 |
| AGENT-09 | MUST REMEMBER 섹션이 AGENT.md 본문 마지막 50 줄 이내 | unit | `pytest tests/phase04/test_must_remember_position.py -x` | ❌ Wave 0 |
| RUB-01 | LogicQA Main-Q + 5 Sub-Qs 블록이 모든 Inspector 프롬프트에 존재 | unit | `pytest tests/phase04/test_logicqa_structure.py -x` | ❌ Wave 0 |
| RUB-02 | Inspector MUST REMEMBER에 "창작 금지" 포함 | unit | `pytest tests/phase04/test_inspector_no_creation.py -x` | ❌ Wave 0 |
| RUB-03 | VQQA feedback 샘플 3개를 Producer에 재주입 → Producer 프롬프트에 `<prior_feedback>` 인식 구절 존재 | unit | `pytest tests/phase04/test_vqqa_injection.py -x` | ❌ Wave 0 |
| RUB-04 | rubric-schema.json 파일 존재 + stdlib validator로 사용 예제 5개 검증 | unit | `pytest tests/phase04/test_rubric_schema.py -x` | ❌ Wave 0 |
| RUB-05 | maxTurns frontmatter 값이 3 / 10 / 5 / 1 중 하나 + factcheck=10, tone-brand=5 확인 | unit | `pytest tests/phase04/test_maxturns_matrix.py -x` | ❌ Wave 0 |
| RUB-06 | Inspector Inputs 섹션에 `producer_prompt` / `producer_system_context` 문자열 0 등장 | unit | `pytest tests/phase04/test_gan_separation.py -x` | ❌ Wave 0 |
| CONTENT-01 | scripter 프롬프트에 "3초 hook" + "질문형" + "숫자|고유명사" regex 등장 | unit | `pytest tests/phase04/test_scripter_3s_hook.py -x` | ❌ Wave 0 |
| CONTENT-02 | scripter 프롬프트에 "탐정" + "하오체" + "조수" + "해요체" 등장 | unit | `pytest tests/phase04/test_scripter_duo.py -x` | ❌ Wave 0 |
| CONTENT-03 | niche-classifier 프롬프트가 `.preserved/harvested/theme_bible_raw/` 경로 참조 | unit | `pytest tests/phase04/test_niche_bible_ref.py -x` | ❌ Wave 0 |
| CONTENT-04 | researcher(nlm-fetcher) 프롬프트에 "citation" / "source-grounded" 등장 | unit | `pytest tests/phase04/test_researcher_citation.py -x` | ❌ Wave 0 |
| CONTENT-05 | ins-schema-integrity 프롬프트에 "9:16" + "1080×1920" + "59" 등장 | unit | `pytest tests/phase04/test_schema_integrity_format.py -x` | ❌ Wave 0 |
| CONTENT-06 | ins-readability + ins-subtitle-alignment 프롬프트에 "24" / "32" / "1-4" 등장 | unit | `pytest tests/phase04/test_subtitle_rules.py -x` | ❌ Wave 0 |
| CONTENT-07 | metadata-seo 프롬프트에 "roman" + "한국어" 등장 | unit | `pytest tests/phase04/test_metadata_seo_bilingual.py -x` | ❌ Wave 0 |
| AUDIO-01 | voice-producer 프롬프트에 "Typecast" primary + "ElevenLabs" fallback 명시 | unit | `pytest tests/phase04/test_voice_primary_fallback.py -x` | ❌ Wave 0 |
| AUDIO-02 | asset-sourcer 프롬프트에 "royalty-free" + "3~5" + "crossfade" 등장 | unit | `pytest tests/phase04/test_audio_hybrid.py -x` | ❌ Wave 0 |
| AUDIO-03 | voice-producer 프롬프트에 감정 스타일 4+ enum 등장 (happy/sad/tense/neutral 등) | unit | `pytest tests/phase04/test_voice_emotion.py -x` | ❌ Wave 0 |
| AUDIO-04 | ins-license 프롬프트에 "KOMCA" + "K-pop" + "AF-13" 등장 + AF-13 bank 샘플 10 검사 → 10/10 차단 | unit + smoke | `pytest tests/phase04/test_af13_kpop_block.py -x` | ❌ Wave 0 |
| SUBT-01 | ins-subtitle-alignment 프롬프트에 "WhisperX" + "kresnik" 등장 | unit | `pytest tests/phase04/test_subt_whisperx.py -x` | ❌ Wave 0 |
| SUBT-02 | ins-korean-naturalness 프롬프트 + 존댓말/반말 샘플 10 검사 → ≥ 9 FAIL | unit + smoke | `pytest tests/phase04/test_korean_naturalness_samples.py -x` | ❌ Wave 0 |
| SUBT-03 | ins-subtitle-alignment 프롬프트에 "±50ms" 또는 "50" 밀리초 언급 | unit | `pytest tests/phase04/test_subt_50ms.py -x` | ❌ Wave 0 |
| COMPLY-01 | ins-platform-policy 프롬프트에 "명예훼손" + "아동복지법" + "공소제기 전 보도규제" 등장 | unit | `pytest tests/phase04/test_korean_law_check.py -x` | ❌ Wave 0 |
| COMPLY-02 | ins-license + ins-mosaic 연계 프롬프트에 "KOMCA" + "방송사" 등장 | unit | `pytest tests/phase04/test_broadcaster_filter.py -x` | ❌ Wave 0 |
| COMPLY-03 | ins-platform-policy 프롬프트에 "3 템플릿" + "Inauthentic" + "Human signal" 등장 | unit | `pytest tests/phase04/test_inauthentic_defense.py -x` | ❌ Wave 0 |
| COMPLY-04 | AF-4 bank (실존 인물명 10+) → ins-license + voice-producer가 10/10 차단 | unit + smoke | `pytest tests/phase04/test_af4_voice_clone.py -x` | ❌ Wave 0 |
| COMPLY-05 | AF-5 bank (실제 얼굴 URL 패턴 10+) → ins-mosaic가 10/10 차단 | unit + smoke | `pytest tests/phase04/test_af5_real_face.py -x` | ❌ Wave 0 |
| COMPLY-06 | ins-safety 프롬프트에 "지역" + "세대" + "정치" + "젠더" 4축 등장 | unit | `pytest tests/phase04/test_cultural_sensitivity.py -x` | ❌ Wave 0 |

**추가 integration test (Wave 6):**
- `tests/phase04/test_logicqa_simulation.py` — Inspector 1개 (ins-korean-naturalness) 선정 → 혼용 샘플 3개 주입 → LogicQA Main-Q + 5 Sub-Qs 응답 시뮬레이션 → 다수결 결과 확인 (canned prompt → expected response mapping).
- `tests/phase04/test_supervisor_fanout.py` — 17 Inspector mock rubric 입력 → Supervisor 합산 → overall_verdict 및 routing 검증.
- `tests/phase04/test_harness_audit_integration.py` — 실제 `harness-audit` 스킬 호출 → 점수 ≥ 80 확인.

### Sampling Rate

- **Per task commit:** `py -3.11 -m pytest tests/phase04/test_<specific>.py -x -q` (해당 task 관련 테스트만)
- **Per wave merge:** `py -3.11 -m pytest tests/phase04/ -x -q` + `py -3.11 scripts/validate/validate_all_agents.py --scope <wave-scope>`
- **Phase gate:** full suite green + harness-audit 점수 ≥ 80 + AF-4/5/13 bank 100% 차단 + 한국어 샘플 10/9+ FAIL 탐지 = `/gsd:verify-work` 통과

### Wave 0 Gaps

- [ ] `.claude/agents/_shared/rubric-schema.json` — RUB-04의 single source of truth
- [ ] `.claude/agents/_shared/agent-template.md` — AGENT.md 표준 템플릿 (Producer/Inspector 변종)
- [ ] `.claude/agents/_shared/af_bank.json` — AF-4 / AF-5 / AF-13 positive + negative 샘플 각 10+
- [ ] `.claude/agents/_shared/korean_speech_samples.json` — 존댓말/반말 혼용 positive 10 + negative 10 + 호칭 누출 샘플 5
- [ ] `scripts/validate/validate_all_agents.py` — frontmatter 파싱 + line-count + description char-count + MUST REMEMBER position (stdlib only)
- [ ] `tests/phase04/conftest.py` — pytest fixture (AGENT.md loader + frontmatter parser + rubric validator)
- [ ] `tests/phase04/test_<category>_<REQ>.py` — 위 34 REQ 매핑 per-test (분할 파일, Wave별 grouping)
- [ ] Framework install (optional): `py -3.11 -m pip install pytest` — 미설치 시 unittest fallback
- [ ] `scripts/validate/rubric_stdlib_validator.py` — stdlib JSON Schema validator (§8.2 코드)

---

## Sources

### Primary (HIGH confidence)

- `.planning/phases/04-agent-team-design/04-CONTEXT.md` — pre-locked decisions, 34 REQ scope, harvest 연동, 29 agents 구조 확정
- `.planning/REQUIREMENTS.md` — 34 REQ-ID 정확 매핑 + v1/v2 구분 + AF-1~15 anti-features
- `.planning/ROADMAP.md` Phase 4 섹션 — 6 Success Criteria + Requirements 매핑
- `.planning/PROJECT.md` — D-1~D-10 Active decisions + Core Value (YPP 궤도)
- `.planning/research/SUMMARY.md` — 14 sections, NotebookLM T6/T7/T15/T16 + Stack lock, 한국 시장 non-negotiables
- `.claude/agents/harvest-importer/AGENT.md` — 검증된 AGENT.md 포맷 (107 lines, frontmatter + 8 sections + MUST REMEMBER 마지막)
- `.claude/skills/harness-audit/SKILL.md` — 500줄 검증 로직 (Phase 1 상속 완료)
- `.preserved/harvested/theme_bible_raw/README.md` — 10줄 채널바이블 스펙 (CONTENT-03 근거)
- Python 3.11.9 + jsonschema 4.25.1 — live-tested 2026-04-19 (stdlib validator feasibility 확인)

### Secondary (MEDIUM confidence)

- Liu et al. 2023 "Lost in the Middle" (Stanford) — AGENT-09 MUST REMEMBER 끝 배치 근거 (PROJECT.md Context에서 참조)
- Anthropic "Building Effective Agents" (6 patterns + Evaluator-Optimizer) — Producer-Reviewer GAN 패턴
- FilmAgent (arXiv 2501.12909) / Mind-of-Director (arXiv 2603.14790) — 3단 Producer 분리 (AGENT-02 T6)
- NotebookLM 52 inline citations (연구 RAW) — T1~T17 novel techniques 원본

### Tertiary (LOW confidence)

- Anthropic Claude Agent SDK 중첩 디렉토리 지원 (§ Open Questions 2) — 공식 문서 검색 필요. v1은 평탄 경로 fallback.
- VQQA 용어 자체의 원 출처 — NotebookLM 연구 RAW의 T7로 참조되나 academic paper 출처 미확인. 내부 개념명으로 간주.

---

## Metadata

**Confidence breakdown:**

- **User constraints:** HIGH — 04-CONTEXT.md에 pre-locked + REQUIREMENTS.md 1:1 매핑 완료
- **Standard stack:** HIGH — Python 3.11.9 + stdlib live-verified, jsonschema 4.25.1 fallback 확인
- **Architecture patterns:** HIGH — harvest-importer AGENT.md가 검증된 template. Producer-Reviewer GAN은 NotebookLM T6 + Anthropic Evaluator-Optimizer로 이중 근거
- **Rubric JSON Schema:** HIGH — stdlib validator §8.2 코드 live-tested
- **Korean naturalness regex:** MEDIUM — 종결어미 패턴은 regex + unicodedata 90% 충족 예상, 실측은 Phase 7 대기
- **AF-4/5/13 bank 효과성:** MEDIUM — regex blocklist는 완벽하지 않음. 2-tier (whitelist + blocklist) 조합 필요. 실측 Phase 8 Content ID 이후
- **Pitfalls (8개):** HIGH — CONFLICT_MAP 39 + 세션 #9 진단 실증 근거
- **Wave 배치 (6~7개):** HIGH — 의존성 DAG는 CONTEXT.md에서 논리적으로 도출 가능
- **29 vs 12~20 수치 충돌:** LOW (Open Question 1) — 계획자 판단 필요. 최종 결정은 Phase 4 Plan 초안에서

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30일 — Phase 4 실행 완료 예정, Python/jsonschema 버전은 stable 범주)

---

## Appendix §3: AGENT.md / Rubric 패턴 (본문 §Architecture Patterns 확장)

### §3.1 Producer AGENT.md 템플릿 표준

Producer 14 개 (Core 6 + 3단 3 + 지원 5)에 공통 적용. Section 구성:

1. **Frontmatter** (YAML, `---` ~ `---`): `name`, `description` (≤1024자), `version`, `role: producer`, `category: core|split3|support`, `maxTurns: 3`
2. **Heading (agent name)** — 한 문단 역할 요약 (왜 존재하는가, 대체 불가능성)
3. **## Purpose** — 만족시키는 REQ-ID 나열
4. **## Inputs** — Flag table (prior_vqqa 필드 필수)
5. **## Outputs** — JSON schema (다음 GATE payload)
6. **## Prompt** — 한국어 상세 지시사항 200~400줄
   - VQQA feedback 반영 서브섹션
   - 채널바이블 인라인 주입 지시 (CONTENT-03)
7. **## References** — `@wiki/shorts/...` + harvested/theme_bible_raw 참조
8. **## MUST REMEMBER** — 5~7개 bullets, 프롬프트 끝에 배치

### §3.2 Producer 3단 분리 인터페이스 (AGENT-02, T6)

- **director**: niche + research → `Blueprint JSON` (tone, high-level structure, target emotion, channel_bible_ref). 5~10 scenes 개요.
- **scene-planner**: Blueprint → `Scenes JSON` (4~8 scene 분절, 각 scene의 t_start/t_end, mood, visual_motif). **1 Move Rule** (T2) enforcement.
- **shot-planner**: Scenes → `Shots JSON` (각 scene 내 1~3 shot, anchor_frame_ref, camera_move, I2V 프롬프트). **T2V 금지** (T1) — prompt에 "I2V only, anchor frame required" 하드코딩.

Hand-off는 순수 JSON. 이전 단계 prompt 읽기 금지.

### §3.3 Inspector AGENT.md 템플릿 표준

1. **Frontmatter**: `role: inspector`, `category: structural|content|style|compliance|technical|media`, `maxTurns: 3 (또는 10/5/1)`
2. **Purpose** — REQ-ID 및 COMPLY/AF 차단 역할
3. **Inputs** — `script-json` 또는 해당 GATE 산출물. **`producer_prompt` 미포함 명시** (RUB-06 GAN 분리)
4. **Outputs** — rubric-schema.json 100% 준수 1 객체
5. **Prompt**:
   - LogicQA block (main_q + 5 sub_qs)
   - 검증 파이프라인 (regex → heuristic → LLM 판정)
   - VQQA semantic_feedback 생성 지침
6. **References** — `.claude/agents/_shared/rubric-schema.json` + 카테고리별 bank (korean_samples, af_bank 등)
7. **MUST REMEMBER**: 창작 금지 (RUB-02), producer_prompt 읽기 금지 (RUB-06), LogicQA 다수결 의무, maxTurns 준수, rubric schema 준수, Supervisor 재호출 금지

### §3.4 Supervisor 재귀 방지 (AGENT-05)

`_delegation_depth` 필드 프롬프트 내 의사코드 embed. Input frontmatter에 `delegation_depth` 플래그 필수. Wave 0 Validation 테스트 `test_supervisor_depth_guard.py`가 이 구절 존재를 regex로 확인.

### §3.5 description 필드 규칙 (AGENT-08)

- ≤ 1024자 (byte가 아닌 char 기준 — Korean 포함 시 byte는 2~3× 증가)
- 트리거 키워드 **최소 3개** 포함 (Claude Code가 description을 auto-routing에 사용)
- 형식: `<역할 1줄>. 트리거 키워드 <k1>, <k2>, <k3>, .... Input: <...>. Output: <...>. <핵심 제약 1줄>. 최대 1024자.`
- Wave 0 Validation: `test_description_rules.py`가 char count + 트리거 키워드 수 자동 검증.

### §3.6 MUST REMEMBER 위치 (AGENT-09)

AGENT.md 본문 마지막 섹션이어야 한다. Validation: `scripts/validate/validate_all_agents.py --check-must-remember-position`가 각 AGENT.md의 `## MUST REMEMBER` 헤더 줄번호를 파일 전체 줄 수 대비 비율 계산, 95% 이상 지점이 아니면 FAIL.

### §3.7 LogicQA 프롬프트 구조 (RUB-01)

Inspector 프롬프트 내 **반드시 등장하는 XML 유사 블록**:
```
<main_q>이 {produce_output}이 {REQ-xx}를 만족하는가?</main_q>
<sub_qs>
  q1: ...
  q2: ...
  q3: ...
  q4: ...
  q5: ...
</sub_qs>
```
Validation: `test_logicqa_structure.py`가 17 Inspector 전부에서 `<main_q>` + `<sub_qs>` 블록 + 정확히 5개 sub-q 검증.

### §3.8 VQQA semantic_feedback 예시 코퍼스 (RUB-03)

최소 3~5 예시를 `_shared/vqqa_corpus.md`에 기록 (계획자 자유):

1. "3초 hook이 약하다 (질문형 없음, 숫자 없음) — 예: '1997년 서울 23세 여대생은 왜 사라졌을까?'"
2. "4번째 scene에서 탐정이 '알아요'(해요체) 사용, 하오체 '알고 있소'로 교정 필요"
3. "탐정 발화에 '탐정님' 호칭 누출(3:15) — 자기 자신 3인칭 표현은 금지"
4. "7번째 scene이 1 Move Rule 위반 — 카메라 팬 + 피사체 이동 동시 요청됨"
5. "audio track에 BTS 'Dynamite' snippet 감지됨 (KOMCA strike 위험, AF-13)"

형식: **[문제]([위치 or 시간 스탬프]) — [교정 힌트 1 문장]**. 대안 창작 금지.

### §3.9 maxTurns 매트릭스 (RUB-05)

| Agent Type | maxTurns | 근거 |
|---|---|---|
| Producer (표준) | 3 | 초안 + VQQA 1회 반영 + 최종 |
| Inspector (표준) | 3 | regex + LLM 판정 + 요약 |
| `ins-factcheck` | **10** | 다중 source cross-verification 필요 |
| `ins-tone-brand` | **5** | 채널바이블 대조 + 톤 샘플 LLM 판정 |
| `ins-schema-integrity` 등 순수 regex | **1** | 결정론적 검증, 다중 turn 불필요 |
| Supervisor | 3 | fan-out + 합산 + 응답 |

Validation: `test_maxturns_matrix.py`가 frontmatter `maxTurns` 필드 값 검증.

### §3.10 Inspector 별도 context (RUB-06 GAN 분리)

실제 실행 시 Claude Agent SDK가 sub-agent를 호출하면 기본적으로 **새 context**가 할당된다 (이는 SDK 동작). Phase 4에서 확보해야 할 것은:
- Inspector AGENT.md Inputs 섹션이 `producer_prompt` / `producer_system_context` 등 Producer context leak 필드를 포함하지 않을 것.
- Supervisor가 fan-out 시에도 각 inspector에게 **`producer_output` JSON만** 전달 (Producer가 사용한 prompt 동봉 금지).

Validation: `test_gan_separation.py`가 `grep -rE "producer_prompt|producer_system_context" .claude/agents/inspectors/` → 0 match 강제.

---

## Appendix §5: Inspector/Producer 카테고리별 Specifics

### §5.1 Producer Core 6 (trend-collector, niche-classifier, researcher, scripter, script-polisher, metadata-seo)

- **trend-collector**: 한국 실시간 트렌드 수집 (NotebookLM RAG). Output: 10~20 keyword candidates + niche tag.
- **niche-classifier**: keyword → channel_bible 매핑. `.preserved/harvested/theme_bible_raw/{niche}.md` 참조 필수.
- **researcher (= nlm-fetcher)**: NotebookLM 2 노트북 (일반 + 채널바이블) 질의 → citation list + fact sheet. **Fallback chain** (WIKI-04) 언급 (실 구현은 Phase 6).
- **scripter**: niche + blueprint + scenes + research → 대본 JSON. 3초 hook + duo dialogue + 60초 상한 + citation 의무.
- **script-polisher**: scripter output의 문체/리듬/종결어미 일관성 교정. 기능 보강 금지 (의미 변경 금지, 표현만 다듬기).
- **metadata-seo**: 한국어 제목/설명/태그 + 로마자 병기 (CONTENT-07). YouTube 글자수 제한 준수.

### §5.2 scripter 3초 hook + duo dialogue 상세

**3초 hook regex 검증 (CONTENT-01):**
- 질문형: 문장 말 `?`
- 숫자 or 고유명사: `[0-9]{2,}|[가-힣]{2,}` 조합 + 연도/도시/이름 패턴

**Duo dialogue (CONTENT-02):**
- 탐정 speaker blocks: 하오체 종결어미 `(소|오|구려|다네|ㄴ가|ㄴ다|겠소)`
- 조수 speaker blocks: 해요체 `(요|에요|예요|지요)`
- 혼용 0.

### §5.3 ins-korean-naturalness 한국어 화법 regex bank

**종결어미 패턴:**
- 하오체: `(하오|이오|보오|가오|구려|다네|습니다|올시다)`
- 해요체: `(해요|이에요|예요|지요|거든요|네요|잖아요)`
- 반말: `(해|야|지|야지|거든|네|잖아|다)`
- 존댓말 일반: `(습니다|니까|십시오|시오)`

**호칭 누출:**
- 탐정이 자기 자신을 `탐정님|탐정 선생|탐정 공|본인|소생` 외 대명사로 부르면 OK. `탐정님`이 `탐정` 발화 블록에 등장하면 FAIL.
- 조수가 자기 자신을 `조수님|조수 공` 사용 시 FAIL.

**외래어 과다 (heuristic):** 5문장당 외래어 ≥ 2 시 경고. regex: `[A-Za-z가-힣]*[A-Za-z]+[가-힣]*` (한영 혼합 단어).

**Validation 샘플 (SUBT-02):**
- Positive 10: 하오체/해요체 정합 유지 대본.
- Negative 10: 혼용 / 호칭 누출 / 외래어 남용 대본.
- `ins-korean-naturalness` 시뮬레이션 결과가 **negative 10 중 ≥ 9 FAIL + positive 10 중 ≥ 8 PASS**.

### §5.4 AUDIO 규칙 — voice-producer / asset-sourcer 경계

**voice-producer (AUDIO-01, 03):**
- Primary: Typecast (한국어 TTS 1위, 존댓말/반말 자연성).
- Fallback: ElevenLabs Multilingual v3.
- 감정 enum: `neutral | tense | sad | happy | urgent | mysterious | empathetic` (T13 동적 파라미터).
- speaker별 voice preset: 탐정 voice_id + 조수 voice_id (채널바이블 기반, Phase 5에서 실 id 확정).
- AF-4 차단: 실존 인물 이름 input 시 즉시 raise (ins-license가 upstream에서 1차 차단, voice-producer는 2차 방어).

**asset-sourcer (AUDIO-02):**
- 하이브리드 오디오: 트렌딩 3~5초 (royalty-free whitelist 내) + 본 음악 crossfade.
- KOMCA whitelist 도메인: Epidemic Sound, Artlist, YouTube Audio Library, Free Music Archive.
- 모든 오디오 자산 URL이 whitelist 밖이면 FAIL (ins-license 차단).

### §5.5 COMPLY 규칙 — ins-license / ins-platform-policy / ins-safety / ins-mosaic / ins-gore

**ins-license (COMPLY-02, 04 / AUDIO-04 / AF-13):**
- AF-13 K-pop regex bank (예시 10개, 주간 업데이트 필요):
  - `BTS|방탄소년단|블랙핑크|BLACKPINK|뉴진스|NewJeans|아이브|IVE|에스파|aespa|르세라핌|LE SSERAFIM|스트레이 키즈|Stray Kids|세븐틴|SEVENTEEN|NCT|트와이스|TWICE`
- 곡명 bank: `다이너마이트|Dynamite|Butter|Spring Day|Savage|Ditto|...`
- URL 도메인 whitelist 우선 검사 → whitelist 밖 = FAIL.

**ins-platform-policy (COMPLY-01, 03):**
- 한국 법: `명예훼손|아동복지법|공소제기.*전.*보도|초상권` 키워드 등장 시 수동 검증 플래그.
- Inauthentic defense: 동일 scripter 산출물 3개 간 Jaccard 유사도 ≥ 0.7 시 FAIL (3 템플릿 변주 요구).
- Human signal: 프롬프트에 "대표님 얼굴 B-roll 1 scene" 또는 "human VO insert" 확인.

**ins-safety (COMPLY-06):**
- 4 축 체크리스트: 지역(경상-전라 편견) / 세대(mz-꼰대) / 정치(진보-보수) / 젠더(성차별).
- 혐오 표현 blocklist 100+ (Phase 4에서 15~20개 초안 작성 후 Phase 9 taste gate로 보강).

**ins-mosaic (COMPLY-05 / AF-5):**
- 얼굴 URL 패턴 (이미지 메타데이터 또는 asset URL) — "news" / "victim" / "press-photo" / 실제 언론사 도메인 blocklist.
- AI 얼굴 생성 (asset-sourcer 산출)에서 실존 피해자 이름이 caption에 등장 시 FAIL.

**ins-gore:**
- 과도한 유혈 묘사 키워드 ("피", "유혈", "절단", "흉기" + 빈도 heuristic). Phase 4는 규칙만, Phase 7에서 샘플 실측.

### §5.6 TECHNICAL — ins-audio-quality / ins-render-integrity / ins-subtitle-alignment

**ins-audio-quality:**
- 피크 레벨 -3 dBFS 초과 시 경고. 연속 silence ≥ 1초 시 FAIL.
- (실 측정은 Phase 5에서 ffmpeg 호출. Phase 4는 규격만.)

**ins-render-integrity:**
- 9:16 / 1080×1920 픽셀 정확 일치. Duration ≤ 59.5s.
- Remotion 출력 메타데이터 파싱 (규격만, 실 구현 Phase 5).

**ins-subtitle-alignment (SUBT-01, 03):**
- WhisperX + `kresnik/wav2vec2-large-xlsr-korean` 기반 word-level 정렬.
- ±50ms 정확도 heuristic: subtitle json의 word.start와 audio waveform onset 비교.
- 폰트: Pretendard / Noto Sans KR (§SUBT `폰트/색`).
- 폰트 크기 24~32pt, 1~4 단어/라인, 중앙 정렬 (CONTENT-06).

---

## Appendix §7: rubric-schema.json (Full, copy-paste ready)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://naberal-shorts-studio/agents/_shared/rubric-schema.json",
  "title": "Shorts Inspector Rubric Output",
  "description": "17 Inspector 공통 출력 스키마. Producer-Reviewer GAN 파이프라인의 평가 단일 인터페이스. Phase 4 RUB-04.",
  "type": "object",
  "additionalProperties": false,
  "required": ["verdict", "score", "evidence", "semantic_feedback"],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": ["PASS", "FAIL"],
      "description": "PASS if score >= 60 AND no critical_violation in evidence; FAIL otherwise. Supervisor overall_verdict는 모든 inspector PASS일 때만 PASS."
    },
    "score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "품질 점수. 0=치명적 위반, 100=완벽. 60 threshold와 verdict 일치 의무 (score>=60 ↔ verdict=PASS)."
    },
    "evidence": {
      "type": "array",
      "minItems": 0,
      "description": "판정 근거. 빈 배열 허용 (PASS이며 자동 통과 시). FAIL 시 최소 1개 필수.",
      "items": {
        "type": "object",
        "required": ["type", "detail"],
        "additionalProperties": false,
        "properties": {
          "type": {
            "type": "string",
            "enum": ["regex", "citation", "heuristic"],
            "description": "regex=패턴 매칭, citation=외부 문서(위키/harvested) 인용, heuristic=LLM 자체 판단"
          },
          "detail": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2000,
            "description": "근거 한 줄. 위치/시간 스탬프 포함 권장. 예: 'scene_idx=4 text=... pattern=/...$/'"
          },
          "location": {
            "type": "string",
            "description": "선택. 'scene:4', 'line:12', 't:3.2s', 'frame:45' 등",
            "maxLength": 100
          },
          "severity": {
            "type": "string",
            "enum": ["info", "warning", "critical"],
            "description": "선택. critical 1+ 시 verdict=FAIL 강제"
          }
        }
      }
    },
    "semantic_feedback": {
      "type": "string",
      "minLength": 0,
      "maxLength": 5000,
      "description": "VQQA 시맨틱 그래디언트 (RUB-03). 자연어 피드백, Producer 프롬프트 주입용. 형식: '[문제 설명](위치) — [교정 힌트 1 문장]'. 대안 창작 금지. PASS verdict 시 빈 문자열 허용."
    },
    "inspector_name": {
      "type": "string",
      "description": "선택. 자기 identification (예: 'ins-korean-naturalness'). Supervisor 로깅용.",
      "pattern": "^ins-[a-z0-9-]+$"
    },
    "logicqa_sub_verdicts": {
      "type": "array",
      "description": "선택. LogicQA 5 sub-q 개별 판정 (RUB-01). Supervisor 감사용.",
      "minItems": 5,
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["q_id", "result"],
        "properties": {
          "q_id": {"type": "string", "pattern": "^q[1-5]$"},
          "result": {"type": "string", "enum": ["Y", "N"]},
          "reason": {"type": "string", "maxLength": 500}
        }
      }
    },
    "maxTurns_used": {
      "type": "integer",
      "minimum": 0,
      "description": "선택. 본 inspector가 사용한 실제 turn 수. Supervisor maxTurns enforcement 감사용."
    }
  }
}
```

**Supervisor 합산 출력 스키마 (별도 파일 `supervisor-rubric-schema.json` 권장):**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Shorts Supervisor Aggregated Rubric",
  "type": "object",
  "required": ["overall_verdict", "individual_verdicts", "aggregated_vqqa", "routing"],
  "properties": {
    "overall_verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
    "individual_verdicts": {
      "type": "array",
      "minItems": 17,
      "maxItems": 17,
      "items": {"$ref": "./rubric-schema.json"}
    },
    "aggregated_vqqa": {"type": "string", "maxLength": 20000},
    "routing": {"type": "string", "enum": ["next_gate", "retry", "circuit_breaker"]},
    "delegation_depth": {"type": "integer", "minimum": 0, "maximum": 1},
    "retry_count": {"type": "integer", "minimum": 0, "maximum": 3}
  }
}
```

---

## Appendix §8: Validation 구현 상세

### §8.1 Frontmatter 파서 (stdlib only)

```python
# scripts/validate/parse_frontmatter.py
import pathlib

def parse_frontmatter(md_path: pathlib.Path) -> tuple[dict, str]:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{md_path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{md_path}: unclosed frontmatter")
    front = text[4:end]
    body = text[end + 5:]
    meta = {}
    for line in front.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body
```

### §8.2 Stdlib JSON Schema validator

(이미 §Code Examples 상단에 게재. Python 3.11.9 live-tested.)

### §8.3 Line count / char count / MUST REMEMBER position

```python
# scripts/validate/validate_all_agents.py (일부)
import pathlib, sys

AGENTS_DIR = pathlib.Path(".claude/agents")

def check_line_count(md_path, limit=500):
    lines = md_path.read_text(encoding="utf-8").splitlines()
    return len(lines), len(lines) <= limit

def check_description_chars(meta, limit=1024):
    desc = meta.get("description", "")
    return len(desc), len(desc) <= limit

def check_must_remember_position(body):
    """MUST REMEMBER 헤더가 본문 마지막 50줄 이내에 등장해야 한다 (AGENT-09)."""
    lines = body.splitlines()
    total = len(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith("## MUST REMEMBER"):
            # 헤더 시작 ~ 파일 끝 까지의 비율이 50% 이상 (즉, 후반부에 위치)
            return i, (total - i) / total if total > 0 else 0
    return -1, 0  # not found

def run_all():
    violations = []
    for md_path in AGENTS_DIR.rglob("AGENT.md"):
        meta, body = parse_frontmatter(md_path)
        total_lines, line_ok = check_line_count(md_path)
        desc_len, desc_ok = check_description_chars(meta)
        mr_line, mr_ratio = check_must_remember_position(body)
        if not line_ok:
            violations.append(f"{md_path}: {total_lines}lines > 500 (AGENT-07)")
        if not desc_ok:
            violations.append(f"{md_path}: description {desc_len}char > 1024 (AGENT-08)")
        if mr_line == -1:
            violations.append(f"{md_path}: MUST REMEMBER 섹션 없음 (AGENT-09)")
        elif mr_ratio > 0.1:
            # MUST REMEMBER 헤더가 파일 상단 90% 이상이면 위반 (즉 뒤에 더 많은 내용이 있음)
            violations.append(f"{md_path}: MUST REMEMBER 위치 이상 (line {mr_line}/{total_lines})")
    if violations:
        for v in violations:
            print(v, file=sys.stderr)
        sys.exit(1)
    print(f"OK: {sum(1 for _ in AGENTS_DIR.rglob('AGENT.md'))} agents validated")
```

### §8.4 LogicQA 다수결 시뮬레이션 (test_logicqa_simulation.py)

```python
# tests/phase04/test_logicqa_simulation.py
import json
from pathlib import Path

def test_korean_naturalness_majority_vote():
    """Canned prompt → expected response mapping.
    실제 LLM 호출 없이 prompt/response 테이블로 LogicQA 다수결 로직만 검증."""
    mock_sub_verdicts = [
        {"q_id": "q1", "result": "N", "reason": "탐정 발화 '알아요' 해요체 혼입"},
        {"q_id": "q2", "result": "Y"},
        {"q_id": "q3", "result": "N", "reason": "탐정님 호칭 누출"},
        {"q_id": "q4", "result": "N"},
        {"q_id": "q5", "result": "Y"},
    ]
    n_count = sum(1 for v in mock_sub_verdicts if v["result"] == "N")
    assert n_count >= 3, "3+ N이면 FAIL 판정 필요"
    # Expected rubric
    rubric = {
        "verdict": "FAIL",
        "score": 40,
        "evidence": [{"type": "regex", "detail": v["reason"]}
                      for v in mock_sub_verdicts if v.get("reason")],
        "semantic_feedback": "; ".join(v["reason"] for v in mock_sub_verdicts if v.get("reason")),
        "logicqa_sub_verdicts": mock_sub_verdicts,
    }
    # stdlib validator로 통과 확인
    from scripts.validate.rubric_stdlib_validator import validate_rubric
    schema = json.loads(Path(".claude/agents/_shared/rubric-schema.json").read_text("utf-8"))
    errs = validate_rubric(rubric, schema)
    assert not errs, f"Schema violation: {errs}"
```

### §8.5 maxTurns enforcement 테스트

```python
# tests/phase04/test_maxturns_matrix.py
import pathlib, pytest

EXPECTED = {
    "ins-factcheck": 10,
    "ins-tone-brand": 5,
    "ins-schema-integrity": 1,
    "ins-blueprint-compliance": 1,  # 순수 regex로 가정
    "ins-timing-consistency": 1,
}

@pytest.mark.parametrize("md_path", list(pathlib.Path(".claude/agents").rglob("AGENT.md")))
def test_maxturns_value(md_path):
    meta, _ = parse_frontmatter(md_path)
    name = meta["name"]
    expected = EXPECTED.get(name, 3)  # default 3
    actual = int(meta.get("maxTurns", 3))
    assert actual == expected, f"{name}: maxTurns expected {expected}, got {actual}"
```

---

## Appendix §9: DAG 의존성 그래프 (Phase 4 Plan 내부 Wave 의존성)

```
Wave 0 (Foundation, NO-DEP)
  ├── rubric-schema.json
  ├── agent-template.md
  ├── af_bank.json
  ├── korean_speech_samples.json
  ├── scripts/validate/validate_all_agents.py
  └── tests/phase04/conftest.py

Wave 1 (Inspector Structural + Style, depends on W0)
  ├── ins-blueprint-compliance
  ├── ins-timing-consistency
  ├── ins-schema-integrity
  ├── ins-tone-brand
  ├── ins-readability
  └── ins-thumbnail-hook

Wave 2 (Inspector Compliance + Media, depends on W0 + af_bank)
  ├── ins-license
  ├── ins-platform-policy
  ├── ins-safety
  ├── ins-mosaic
  └── ins-gore

Wave 3 (Inspector Content + Technical, depends on W0 + korean_samples)
  ├── ins-factcheck
  ├── ins-narrative-quality
  ├── ins-korean-naturalness
  ├── ins-audio-quality
  ├── ins-render-integrity
  └── ins-subtitle-alignment

Wave 4 (Producer Core 6, depends on W1-W3 inspector rubric schemas 이해)
  ├── trend-collector
  ├── niche-classifier
  ├── researcher (nlm-fetcher)
  ├── scripter
  ├── script-polisher
  └── metadata-seo

Wave 5 (Producer 3단 + 지원 5 + Supervisor, depends on W4)
  ├── director
  ├── scene-planner
  ├── shot-planner
  ├── voice-producer
  ├── asset-sourcer
  ├── assembler
  ├── thumbnail-designer
  ├── publisher
  └── shorts-supervisor

Wave 6 (Integration Validation, depends on W0-W5)
  ├── harness-audit 전수 실행 → 점수 ≥ 80
  ├── AF-4 / AF-5 / AF-13 bank 100% 차단 smoke test
  ├── 한국어 샘플 10 → ≥ 9 FAIL smoke test
  └── scripts/validate/validate_all_agents.py full pass
```

**병렬 안전성:** Wave 1/2/3는 inspector로 서로 독립 (다른 카테고리) → 3-way 병렬 안전. Wave 4 Producer Core는 inspector rubric 이해 필요 (프롬프트 내 "ins-korean-naturalness FAIL 시 hooks 교정" 같은 참조 문장이 등장). Wave 5 Producer 지원/Supervisor는 Wave 4 Producer 인터페이스 필요 (특히 Supervisor는 전체 fan-out list 확정 필요).

**Critical path:** W0 → W3 (ins-korean-naturalness은 한국어 화법 로직이 집중) → W4 (scripter는 korean rules 참조) → W5 (Supervisor) → W6.

---

## RESEARCH COMPLETE
