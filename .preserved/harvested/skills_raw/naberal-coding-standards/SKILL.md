---
name: naberal-coding-standards
description: NABERAL 프로젝트 코딩 표준, CI 게이트, 개발 워크플로우, DB 패턴, Evidence 시스템, FIX-4 품질 기준값. 코드 작성, 커밋, 브랜치, 배포, 아키텍처 작업 시 반드시 참조. "코딩", "개발", "CI", "커밋", "브랜치", "배포", "아키텍처", "품질", "게이트" 키워드에 반응.
user-invocable: false
---

# NABERAL 코딩 표준 및 개발 워크플로우

## 3대 개발 원칙

| 원칙 | 의미 | 위반 시 |
|------|------|---------|
| **Contract-First** | OpenAPI/스키마를 코드보다 먼저 작성. 계약 불일치 = 빌드 실패 | 즉시 중단 |
| **SSOT** | 상수/단위/정책은 오직 `core/ssot/**`에서만. 하드코딩 금지 | 즉시 중단 |
| **Evidence-Gated** | 모든 변경은 증거(SHA256/타임스탬프) 동반. 무증거 변경 금지 | 즉시 중단 |

## CI Gate 기준 (G1~G6)

| Gate | 이름 | 기준 | 실패 시 |
|------|------|------|---------|
| G1 | Lint/Policy | ruff + black 통과, 금지어(TODO/MOCK/STUB) 미검출 | 머지 차단 |
| G2 | SSOT/Magic | SSOT 위반 0, 매직 리터럴 0 | 머지 차단 |
| G3 | Contract | OpenAPI 스펙 vs 코드 계약 일치 100% | 머지 차단 |
| G3.5 | Probe | 헬스 프로브 응답 정상 | 머지 차단 |
| G4 | Tests+Coverage | 전체 테스트 통과, 커버리지 >= 60% (라쳇 적용 시 상향) | 머지 차단 |
| G5 | Evidence | Evidence 팩 생성 완료 | 머지 차단 |
| G6 | Deploy Pack | 배포 아티팩트 생성 정상 | 머지 차단 |

### 커버리지 라쳇 정책
- 기본: overall >= 60%
- 3회 연속 그린 시 자동 상향: 62 -> 65 -> 70
- 패키지 가드: core >= 75% / infra >= 70% / engine >= 68%

## DB 패턴

### Dual-DSN (필수)
```
앱 (비동기): asyncpg -> DATABASE_URL
Alembic (동기): psycopg2 -> ALEMBIC_DATABASE_URL_SYNC
```
- 두 DSN을 혼용하지 않는다.
- Railway 환경변수에 반드시 둘 다 등록.

### 스키마 및 보안
- PostgreSQL 전용 (다른 DB 금지)
- RLS (Row Level Security) 활성화
- JWT_SECRET 모드 명시
- 모든 TIMESTAMP는 TIMESTAMPTZ (UTC 기본)
- created_at / updated_at 필수

### 마이그레이션
- Alembic 마이그레이션은 반드시 **멱등**
- downgrade 함수 동작 확인 필수
- 실패 시 롤백 문서로 즉시 복구
- 기존 데이터 호환성 확인

## 에러 스키마 표준

```json
{
  "code": "E_VALIDATION",
  "message": "상평형이 4%를 초과합니다",
  "hint": "분기 차단기 배치를 재조정하세요",
  "traceId": "uuid-v4",
  "meta": {
    "dedupKey": "hash-value"
  }
}
```
- SSE 엔드포인트: heartbeat + meta.seq 필수

## Import 규칙

```python
# CORRECT
from kis_estimator_core.services import estimation_service
from kis_estimator_core.engine import breaker_placer

# WRONG - 즉시 수정
from src.kis_estimator_core.services import estimation_service
from ..engine import breaker_placer  # 상대경로 금지
```

## FIX-4 파이프라인 품질 게이트

| Stage | 지표 | 기준값 | 검증 방법 |
|-------|------|--------|----------|
| 1. Enclosure | fit_score | >= 0.90 | `enclosure.validate()` |
| 2. Breaker | 상평형 | <= 4% | `layout.balance_phases()` |
| 2. Breaker | 간섭 위반 | = 0 | `layout.check_clearance()` |
| 2. Breaker | 열 위반 | = 0 | 열 밀도 검사 |
| 3. Format | 수식 보존 | = 100% | `estimate.verify_formulas()` |
| 4. Cover | 표지 규칙 | = 100% | `doc.cover_validate()` |
| 5. Doc Lint | 린트 오류 | = 0 | `doc.lint()` |
| 회귀 | 골드셋 | 20/20 PASS | `pytest -m regression` |

## 성능 목표

| 작업 | 목표 | 최대 |
|------|------|------|
| API 응답 (P95) | < 200ms | 500ms |
| Health 체크 | < 50ms | 100ms |
| 브레이커 배치 (100개) | < 1s | 30s |
| 외함 계산 | < 500ms | 1s |

## Evidence 시스템

### Evidence 수집 경로
```
/spec_kit/evidence/{timestamp}/
  input.json       # 입력 데이터
  output.json      # 출력 결과
  metrics.json     # 성능 지표
  validation.json  # 검증 결과
  visual.svg       # 시각화
```
- SHA256 해시로 무결성 보장
- 모든 계산은 증거 생성 필수
- 회귀 테스트 20/20 통과 전 머지 금지

## 개발 세션 워크플로우

### 세션 시작
```bash
git status && git branch        # 현재 상태 확인
git checkout -b feature/[작업명]  # 작업 브랜치 생성
```
- WORK_HANDOFF.md 읽고 현재 상황 파악

### 작업 중
```bash
# 1. TodoWrite로 작업 계획
# 2. 단위별 구현 -> 테스트 -> 검증
# 3. 품질 체크 (수시 실행)
mypy src/
pytest
ruff check src/
```

### 커밋 전 필수 확인
```bash
pytest -m regression   # 회귀 테스트 20/20 PASS 필수
pytest --cov=src       # 커버리지 >= 60% 확인
```

### 세션 종료
- WORK_HANDOFF.md 갱신 (완료/미완료/블로커/다음 작업)

## 커밋 메시지 규약

```
feat: 새 기능 추가
fix: 버그 수정
refactor: 코드 구조 변경 (기능 변화 없음)
ci: CI/CD 파이프라인 변경
chore: 빌드/의존성/설정 변경
docs: 문서 변경
test: 테스트 추가/수정
```
- 한 커밋에 한 가지 변경만
- 본문에 "왜" 변경했는지 기록

## 브랜치 전략

```
main (배포용) <- feature/[작업명] (작업용)
```
- main에 직접 커밋 금지
- feature 브랜치에서 작업 후 PR
- PR에 Evidence 팩 동봉 필수

## 장애 대응

1. **롤백 우선**: 마지막 그린 태그로 즉시 롤백
2. **RCA (Root Cause Analysis)**: 근본 원인 분석
3. **재현**: 재현 가능한 테스트 케이스 작성
4. **재발 방지**: 회귀 테스트에 케이스 추가

## 금지 6법 (LAW-01~06)

| 코드 | 금지 사항 |
|------|----------|
| LAW-01 | 아키텍처 일탈 (정의된 레이어 구조 위반) |
| LAW-02 | SSOT 위반 (하드코딩, 매직 리터럴) |
| LAW-03 | 하드코딩 (환경변수/설정으로 분리해야 할 값) |
| LAW-04 | AppError 무시 (에러 삼키기, bare except) |
| LAW-05 | 단일책임 위반 (한 모듈이 여러 역할) |
| LAW-06 | Shared 스키마 중복 (shared 모듈 재정의) |
