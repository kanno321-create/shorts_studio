---
name: drift-detection
description: 스튜디오 내 구형-신형 충돌(drift)을 전수 스캔해 CONFLICT_MAP.md에 기록·갱신. 에이전트가 모순된 지시 때문에 재호출 루프에 빠지는 현상을 예방. "drift 검사", "충돌 스캔", "CONFLICT MAP 갱신", "구형-신형 충돌", "에이전트가 루프 빠짐" 요청 시 반드시 트리거.
---

# Drift Detection — 구형-신형 충돌 자동 탐지

스튜디오가 성장하면 필연적으로 **규약 모순**이 쌓임:
- 조수 발화 비율 "20-35%" vs "15-30%"
- API 경로 `orchestrate.py` vs `harness.py`
- 문서-코드 불일치

이 스킬은 **패턴 기반 스캔**으로 충돌을 전수조사하여 `.planning/codebase/CONFLICT_MAP.md` 를 갱신.

## 언제 트리거되나

- "drift 검사"
- "충돌 스캔"
- "CONFLICT_MAP 갱신"
- "구형-신형 충돌 찾아줘"
- "에이전트가 모순 지시로 헤매"
- 주기 실행 (주 1회 권장)

## 워크플로우

### Phase 1: 패턴 등록
`.claude/drift_patterns.json`에 스튜디오별 검사 패턴 정의:
```json
{
  "patterns": [
    {
      "name": "assistant_ratio",
      "description": "조수 발화 비율 기준 모순",
      "regex": "(\\d{2})-(\\d{2})%\\s*(조수|assistant)",
      "conflict_condition": "grouped_by_context",
      "grade": "A"
    },
    {
      "name": "skip_gates",
      "description": "skip_gates=True 디버그 경로 상주",
      "regex": "skip_gates\\s*=\\s*True",
      "conflict_condition": "any_occurrence",
      "grade": "A"
    }
  ]
}
```

### Phase 2: 스캔
```bash
python ../../harness/scripts/drift_scan.py \
  --root . \
  --patterns .claude/drift_patterns.json \
  --output .planning/codebase/CONFLICT_MAP.md
```

**스캔 범위 기본값**:
- `.claude/agents/`
- `.claude/skills/`
- `scripts/`
- `config/`
- `docs/`
- `wiki/`

**민감 경로 제외**: `.env`, `**/auth_info.json`, `**/browser_state/`

### Phase 3: CONFLICT_MAP.md 갱신
출력 형식:
```markdown
# CONFLICT MAP — {{YYYY-MM-DD}}

## A급 (Blocking — 에이전트 루프 원인)

### A-1. 조수 발화 비율 모순
| 구분 | 내용 |
|-----|------|
| 패턴 | `\\d{2}-\\d{2}%\\s*조수` |
| 위치 A | `.claude/agents/producers/scripter/AGENT.md:86` "20-35%" |
| 위치 B | `.claude/agents/inspectors/ins-duo/AGENT.md:26` "15-30%" |
| 영향 | Scripter PASS → Inspector FAIL 재호출 루프 |
| 정답 후보 | [A] 20-35 유지 [B] 15-30 유지 [C] 새 기준 |
| 정답 확정 | **대기** |
```

### Phase 4: 대표님 결정 유도
- 각 A/B급 항목은 "정답 확정" 필드 **대기 상태**로 시작
- 대표님이 결정 후 필드 업데이트
- 결정 완료된 것만 Step 2 (Wave 집행) 대상

### Phase 5: 재발 방지 자동화
결정 완료 후:
1. `.claude/deprecated_patterns.json`에 구형 regex 추가
2. pre_tool_use.py가 자동 차단
3. session_start.py가 잔존 자동 경고

## 입력/출력

**입력**: 스튜디오 루트 경로
**출력**:
- `.planning/codebase/CONFLICT_MAP.md` (생성/갱신)
- `.planning/codebase/CONFLICT_HISTORY.jsonl` (append-only 이력)

## 관련 에이전트

- supervisor 계열이 주기 호출
- **도메인 스튜디오의 "자기 진단" 기능**

## 실패 패턴

- 패턴 regex 틀림 → false positive 폭증
- 민감 경로 스캔 → 토큰 유출
- CONFLICT_MAP 덮어쓰기 → 과거 결정 유실 (CONFLICT_HISTORY.jsonl 사용)

## 성공 기준

- [ ] A급 충돌 0 또는 전부 정답 확정
- [ ] CONFLICT_HISTORY.jsonl에 모든 결정 이력
- [ ] deprecated_patterns.json과 동기화

## 증거 (Research)

- shorts_naberal 사례: 16일 조사에서 A급 13건·B급 16건·C급 10건 자동 탐지 → 대표님 호소 "에이전트 스킵" 근본 원인 특정
- Anthropic "Building Effective Agents": "모순된 지시는 에이전트 루프 1순위 원인"

---

> 🧩 Layer 1 공용. 모든 스튜디오 상속.
> **핵심**: 정기 스캔 + 결정 완료 항목만 집행 + CONFLICT_HISTORY로 이력 보존.
