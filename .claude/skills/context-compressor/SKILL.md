---
name: context-compressor
description: 긴 CLAUDE.md·WORK_HANDOFF·SKILL.md가 세션 초반 컨텍스트를 30%+ 소비할 때 Lost-in-the-Middle을 방지하기 위한 압축 기법 적용. 과거 세션 아카이브 + 최근 3세션만 유지 + 중복 제거. "컨텍스트 다이어트", "WORK_HANDOFF 슬림", "CLAUDE.md 정리", "세션 로드 줄이기", "문서 너무 많음" 요청 시 반드시 트리거.
---

# Context Compressor — 컨텍스트 압축

Claude 세션이 시작될 때 CLAUDE.md + WORK_HANDOFF.md + SESSION_LOG.md + FAILURES.md 등을 자동 로드. 이것들이 **2,000줄 넘으면 초반 컨텍스트 30%+ 소비** + Lost-in-the-Middle 위험.

이 스킬은 **과거 아카이브 + 최근 유지 + 중복 제거**로 1,000줄 이내 목표.

## 언제 트리거되나

- "WORK_HANDOFF 1500줄 넘었어"
- "컨텍스트 다이어트"
- "CLAUDE.md 정리"
- "세션 로드 너무 무거워"
- "SESSION_LOG 잘라내자"
- "문서 슬림화"

## 워크플로우

### Phase 1: 측정
```bash
python ../../harness/scripts/context_audit.py --mode session-load
```
**출력**:
```
Session init load estimate:
  CLAUDE.md            : 245줄
  WORK_HANDOFF.md      : 1,527줄  ← 비대
  SESSION_LOG.md       : 412줄
  DESIGN_BIBLE.md      : 380줄
  failures/orchestrator.md: 488줄
  Total              : 3,052줄 (약 30% 컨텍스트 소비)
Target: ≤ 1,000줄
```

### Phase 2: WORK_HANDOFF 다이어트
규칙:
- **최근 3개 세션만 유지** (현재 진행 중 + 직전 2개)
- 4개 이상 된 세션 → `docs/archive/handoffs/session_XX.md`로 이동
- 원본 WORK_HANDOFF.md는 300줄 이내

이동 스크립트 예시:
```bash
# 세션 #7 이전 섹션을 archive로
awk '/^## 세션 #7/,0' WORK_HANDOFF.md > docs/archive/handoffs/pre_session_8.md
awk '!/^## 세션 #[1-7]/' WORK_HANDOFF.md > WORK_HANDOFF.md.new
mv WORK_HANDOFF.md.new WORK_HANDOFF.md
```

### Phase 3: SESSION_LOG 압축
- **최근 10개 세션만 유지**
- 이전은 `docs/archive/session_log_2026q1.md`로 묶음
- 핵심 결정만 1줄씩 요약 테이블로 현행 유지

### Phase 4: CLAUDE.md 점검
- 200~250줄 목표
- 초과 시:
  - 상세 절차는 스킬 SKILL.md로 이동
  - 아키텍처 설명은 `docs/ARCHITECTURE.md`로
  - CLAUDE.md는 **네비게이션 + 절대 규칙** 만

### Phase 5: FAILURES 정리
- Append-only 원칙 유지 (삭제 금지)
- 다만 **재발 카운트 1회 + 6개월 경과**한 항목은 `failures/archive.md`로
- 활성 failures/orchestrator.md는 200줄 이내

### Phase 6: 중복 제거
동일 규칙이 여러 곳에 있으면:
- "single source of truth" 정함 (보통 AUTHORITY.md 또는 DESIGN_BIBLE.md)
- 다른 곳은 **포인터만** ("이 규칙은 `docs/DESIGN_BIBLE.md` 참조")

## 입력/출력

**입력**: 스튜디오 루트
**출력**:
- 각 원본 문서 슬림화된 버전
- `docs/archive/` 하위 과거 세션 보관
- `docs/context_audit_report.md` (측정 결과)

## 관련 에이전트

- supervisor 주기 실행 (세션 시작 시 자동)
- 대표님 "답답하다" 호소 시 1순위 진단

## 실패 패턴

- Archive 안 하고 삭제 → **과거 기록 유실**
- WORK_HANDOFF 이름 바꿈 → **Claude가 못 찾음**
- 단순 줄수 컷 → **맥락 파괴**, 의미 단위로 분리

## 성공 기준

- [ ] 세션 초반 로드 ≤ 1,000줄
- [ ] WORK_HANDOFF ≤ 300줄 (최근 3세션)
- [ ] SESSION_LOG ≤ 10개 세션
- [ ] CLAUDE.md ≤ 250줄
- [ ] archive/ 에 모든 과거 기록 보존

## 증거

- shorts_naberal WORK_HANDOFF.md: 1,527줄 상태에서 대표님 "답답하다" 호소 지속
- Anthropic prompt caching 5분 TTL — 긴 프롬프트일수록 캐시 미스 비용↑
- Lost in the Middle 학술 측정: 컨텍스트 중간 30%+ 정확도 감소

---

> 🧩 Layer 1 공용. 모든 스튜디오 상속.
> **핵심**: 삭제 아니라 아카이브. 최신 N개 유지 + 단일 진실 원천 유지.
