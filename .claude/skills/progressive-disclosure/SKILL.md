---
name: progressive-disclosure
description: SKILL.md와 장문 지침서가 500줄을 초과해 Lost-in-the-Middle 현상(LLM이 중간부 지시 30%+ 누락)을 유발하지 않도록 자동 검사하고 references/ 분리를 제안. "SKILL 슬림화", "문서 500줄 넘음", "Lost in the Middle", "Progressive Disclosure", "스킬 너무 길어" 요청 시 반드시 트리거.
---

# Progressive Disclosure — 단계적 정보 공개

LLM(특히 RoPE 기반 모델)은 긴 프롬프트의 **중간부에서 정확도 30%+ 감소** (Lost in the Middle, Liu et al. 2023). 해결책은 3단계 정보 계층화:

```
Metadata (name + description)  ← 항상 로드, ~100 단어
      ↓
SKILL.md 본문                  ← 트리거 시 로드, <500줄
      ↓
references/                    ← 필요할 때만 로드, 무제한
```

## 언제 트리거되나

사용자가 다음 표현 쓸 때 반드시 트리거:
- "SKILL.md 너무 길어"
- "문서 500줄 넘어서 어떡해"
- "Lost in the Middle 해결"
- "Progressive Disclosure 적용"
- "스킬 슬림화해줘"
- "에이전트가 중간 지시를 놓쳐"

## 워크플로우

### Phase 1: 스캔
**도구**: `harness/scripts/context_audit.py` (또는 수동)
```bash
python ../../harness/scripts/context_audit.py --threshold 500
```
**출력**: 500줄 초과 파일 목록 + 각 파일 줄수

### Phase 2: 분류
각 긴 파일을 아래 카테고리로 분류:
| 카테고리 | 처리 |
|---------|-----|
| 진짜 핵심 (본문 유지) | 500줄 이내로 압축 |
| 조건부 참조 (특정 상황에만 필요) | `references/` 분리 |
| 예시·데이터 (항상 로드 불필요) | `references/` 또는 `assets/` |
| 중복 (이미 다른 곳에 있음) | 삭제 + 링크 |

### Phase 3: 분리
references/ 구조:
```
my-skill/
├── SKILL.md (본문, ≤500줄, 언제 references 로드할지 포인터 명시)
└── references/
    ├── aws.md      ← "AWS 사용 시만 읽어"
    ├── gcp.md
    └── detailed_examples.md
```

SKILL.md 본문에 포인터 예시:
```markdown
## AWS 사용 시
상세 절차는 `references/aws.md` 참조.
```

### Phase 4: 재배치 (Lost-in-the-Middle 구조적 대응)
본문 500줄 내에서도 **중요 지시는 끝부분에 재배치**:
- 가장 중요한 규칙·금지사항은 문서 **끝 5~10줄**
- LLM이 끝을 더 잘 기억함 (학술 측정)
- 중복 허용 — 시작과 끝 양쪽에 동일 규칙 배치도 OK

## 입력/출력

**입력**: 분석 대상 디렉토리 (`.claude/skills/`, `docs/`, `wiki/` 등)
**출력**: 분리 제안 리포트 (`.planning/slim_proposal.md` 같은 경로)

## 관련 에이전트

- 모든 에이전트가 이 스킬 공유 (공용)
- 특히 **supervisor 계열**이 주기 실행

## 관련 파일

- `references/metrics.md` — Lost-in-the-Middle 측정치·논문 요약 (있다면)
- `references/templates.md` — 분리 후 구조 예시 (있다면)

## 실패 패턴

- 기계적 500줄 컷 (맥락 끊어버림) → **의미 단위로 분리**
- references/ 만들고 SKILL.md에 포인터 안 남김 → **Claude가 못 찾음**
- 중요 지시를 중간에만 배치 → **끝 재배치 필요**

## 성공 기준

- [ ] 모든 SKILL.md ≤ 500줄
- [ ] 각 references/ 파일 상단에 "언제 로드" 설명
- [ ] 중요 규칙이 문서 끝에도 재배치됨
- [ ] Metadata(description)에 트리거 키워드 명시

## 증거 (Research)

- **Liu et al. 2023** "Lost in the Middle: How Language Models Use Long Contexts"
- **Anthropic** Claude Agent Skills 공식 가이드: 500줄 리밋 권장
- **revfactory/harness** SKILL.md 본문도 평균 300~450줄 유지

---

> 🧩 본 스킬은 naberal_harness Layer 1의 공용 자산. 모든 스튜디오가 상속.
> **핵심 지시 재강조**: SKILL.md 500줄 초과 시 references/ 분리 + 중요 규칙 끝 재배치.
