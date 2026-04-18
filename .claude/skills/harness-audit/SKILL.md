---
name: harness-audit
description: 스튜디오 전체 건강 검진 — drift 탐지 + context overload + SKILL 슬림 + hook 설치 상태 + CLAUDE.md 품질을 통합 리포트. revfactory/harness의 "하네스 점검" 감사 모드와 통합. "하네스 점검", "스튜디오 감사", "하네스 현황", "프로젝트 건강 검진" 요청 시 반드시 트리거.
---

# Harness Audit — 스튜디오 통합 감사

3개의 개별 스킬(drift-detection, context-compressor, progressive-disclosure)을 묶어 **한 번에 전체 진단**.

결과: **스튜디오 건강 점수 + 우선순위별 조치 리스트**.

## 언제 트리거되나

- "하네스 점검"
- "스튜디오 감사"
- "하네스 현황"
- "프로젝트 건강 검진"
- "에이전트·스킬 동기화"
- 주기 실행 (세션 시작 권장)

## 워크플로우

### Phase 1: 5개 진단 도메인 실행

| 도메인 | 위임 스킬 | 측정 |
|-------|---------|------|
| D1: Drift | `drift-detection` | A/B/C급 충돌 수 |
| D2: Context Load | `context-compressor` | 초반 로드 줄수 |
| D3: Skill Slim | `progressive-disclosure` | 500줄 초과 SKILL 수 |
| D4: Hook Status | (이 스킬 자체) | 3개 Hook 등록 여부 |
| D5: CLAUDE.md 품질 | (이 스킬 자체) | 구조·원칙 준수 |

### Phase 2: 각 도메인 측정
```python
# Pseudo
scores = {}
scores["drift"] = count_conflicts()
scores["context"] = session_init_lines()
scores["slim"] = count_overlong_skills()
scores["hooks"] = check_hooks_installed()
scores["claude_md"] = claude_md_quality_check()
```

### Phase 3: 건강 점수 계산
```
건강 점수 = 100 - Σ(domain_penalty)

domain_penalty:
  drift:
    A급당 -10, B급당 -3, C급당 -1
  context:
    1000줄 초과 시 초과 100줄당 -5
  slim:
    500줄 초과 SKILL당 -3
  hooks:
    Hook 미설치 개당 -10
  claude_md:
    네비 불가 -15, 절대규칙 없음 -10, 상세 절차 섞임 -5
```

### Phase 4: 리포트 작성
`.planning/harness_audit_{YYYYMMDD}.md`:

```markdown
# Harness Audit — {{스튜디오명}} @ {{날짜}}

## 종합 건강 점수: **{{점수}}/100** ({{🟢 건강 | 🟡 주의 | 🔴 위험}})

## 도메인별 결과

### D1: Drift — {{A급 N건}}, {{B급 M건}}, {{C급 K건}}
- 상위 3건:
  - A-1: ...
  - A-2: ...

### D2: Context Load — {{총 X줄}} (목표 ≤1000)
- WORK_HANDOFF: {{Y줄}}
- SESSION_LOG: {{Z줄}}
- ...

### D3: Skill Slim — {{500줄 초과 N개}}
- ...

### D4: Hook Status
- [{{✅|❌}}] pre_tool_use.py
- [{{✅|❌}}] post_tool_use.py
- [{{✅|❌}}] session_start.py

### D5: CLAUDE.md 품질 — {{점수}}/20
- ...

## 우선순위 조치 Top 5
1. ...
2. ...

## 다음 주 감사 예정일: {{+7일}}
```

### Phase 5: 액션 아이템
- 🔴 위험 도메인 → 즉시 전용 스킬 호출 권장
- 🟡 주의 도메인 → 다음 세션 내 조치
- 🟢 건강 → 유지

### Phase 6 (선택): 이력 누적
`.planning/harness_audit_history.jsonl` append:
```json
{"date": "2026-04-18", "score": 72, "domains": {...}}
```
→ 시간 추이 그래프 가능.

## 입력/출력

**입력**: 스튜디오 루트
**출력**: 타임스탬프 리포트 + 이력 jsonl

## 관련 에이전트

- supervisor가 주기 호출 (월 1회 권장)
- 대표님 "답답함" 호소 시 1순위 진단

## 실패 패턴

- 점수만 보고 원인 무시 → 리포트의 "우선순위 조치" 섹션 필수 확인
- 너무 자주 실행 (매일) → 시그널-투-노이즈 악화
- 위임 스킬이 실패하면 패닉 → 각 도메인 독립 실행, 실패는 기록만

## 성공 기준

- [ ] 건강 점수 ≥ 80 목표
- [ ] A급 drift 0건
- [ ] Context load ≤ 1000줄
- [ ] 모든 Hook 설치됨
- [ ] 이력 jsonl 존재

## 증거

- 어제 secondjob_naberal 구축 후 감사 → 건강 점수 측정 가능
- shorts_naberal 현재 상태 → A급 13건 + Context 3,052줄 → 예상 점수 40~50

---

> 🧩 Layer 1 공용. 모든 스튜디오 상속.
> **핵심**: 측정 없이 개선 없다. 주기 감사 + 이력 누적이 drift의 원천 방지.
