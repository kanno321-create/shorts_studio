---
name: feedback_session_evidence_first
description: UAT 작성 전 output/ 산출물 + SESSION_LOG + commit 전수 점검 4단계 의무, "이전 피드백 자체가 evidence" 원칙
type: feedback
---

# Session Evidence-First 원칙

**박제 trigger**: 세션 #26 3차 batch — 대표님 지적 "이미 어딘가에 입력되어있는거 자꾸 빠트린다고. 하네스 위키 이걸로 구현했는데 결과는 똑같은일이 반복되네".

**근본 원인**: HUMAN-UAT.md 작성자가 output/ 산출물 + SESSION_LOG 실측 기록 cross-reference 안 함. UAT.md 만 보고 "pending" 수용이 여러 세션 반복.

## 4단계 evidence 전수 점검 의무

UAT 또는 재질문 전 **반드시 순서대로 확인**:

1. **output/ 산출물 존재 확인** — `ls output/<phase>/` + 파일 크기/날짜
2. **SESSION_LOG 실측 기록** — 해당 세션에 측정/검증 entry 있는지 grep
3. **git commit 증거** — `git log --oneline --grep=<keyword>` 로 후속 조치 commit 존재 여부
4. **메모리 박제** — 관련 project/feedback 메모리 먼저 읽기

**4단계 중 하나라도 hit 하면 UAT 는 이미 resolved**. "pending" 상태를 유지하면 대표님 같은 질문 반복.

## "이전 피드백 자체가 evidence" 원칙

대표님 과거 피드백 + 그 후속 조치 commit 이 존재하면:
- **UAT 는 passed_by_attestation / passed_by_evidence 로 즉시 flip**
- 재확인 요구 금지
- 증거 = commit SHA + 인용 구절

### 적용 사례 (세션 #26 3차)

- **UAT #2-a (Typecast primary)**: 대표님 "계속 사용해왔던거다" → `passed_by_attestation`
- **UAT #1 (Kling 2.6 품질)**: output clip 4.5MB + 대표님 "팔 복제" 피드백 + 후속 commit `ff5459b` (스택 전환) → `passed_by_evidence`

## UAT.md Template 필드 의무 추가

각 UAT 엔트리에 다음 필드 강제:
- `evidence_sources`: 관련 output 파일 / SESSION_LOG 라인 / commit SHA 열거
- `pre_check_commands`: UAT 작성 전 실행해야 하는 검증 명령어

## 하네스 재발 방지 TODO

- [ ] `gsd-uat-template` skill 확장 — UAT 작성 시 evidence_sources 필수 필드 강제
- [ ] SessionStart hook 확장 — 최근 output/ 산출물 + git log summary 주입 (Part A A1 에서 구현)

## Related

- `F-CTX-01` (FAILURES.md) — 동일 근본 원인 (박제된 것을 먼저 읽어라)
- [feedback_clean_slate_rebuild](feedback_clean_slate_rebuild.md) — 포팅 판정도 evidence-first 동일 패턴
