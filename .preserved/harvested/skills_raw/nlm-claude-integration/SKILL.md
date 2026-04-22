---
name: nlm-claude-integration
description: Claude Code와 NotebookLM을 연동하는 하이브리드 워크플로우. MCP 서버를 통한 프로그래밍 연동, 개발 지식 관리, 코드 리뷰 지원, 기술 문서 자동화 시 사용. "NLM 연동", "노트북 연결", "Claude NotebookLM", "MCP 노트북" 키워드에 반응.
user-invocable: false
---

# Claude Code + NotebookLM 하이브리드 워크플로우

## 활용 시점
- Claude Code에서 NotebookLM 노트북을 직접 쿼리할 때
- 코드베이스 지식을 NotebookLM에 체계화할 때
- 기술 문서를 NotebookLM으로 자동 생성/관리할 때
- 코드 리뷰 시 도메인 지식 참조가 필요할 때
- 프로젝트 온보딩 자료를 자동화할 때

## MCP 서버 연결 방법

### PleasePrompto NotebookLM MCP (npm)
```json
// .claude/mcp.json 또는 settings.json에 추가
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp"],
      "env": {
        "GOOGLE_API_KEY": "<your-google-api-key>"
      }
    }
  }
}
```

### jacob-bd NotebookLM CLI (pip)
```bash
# CLI 사용법
nlm list              # 노트북 목록 조회
nlm query "질문"       # 노트북에 질문
nlm create "이름"      # 노트북 생성
nlm add-source <id>   # 소스 추가
```

## 하이브리드 워크플로우

### 1. 코드베이스 → NotebookLM 지식화
```
Step 1: 프로젝트 핵심 문서 추출
  - README.md, CLAUDE.md, API 스키마
  - 아키텍처 문서, ADR(Architecture Decision Records)
  - 핵심 모듈 docstring/주석 모음

Step 2: NotebookLM 노트북 구성
  노트북: "[프로젝트명] 기술 지식"
  소스:
    - 프로젝트 README (마크다운)
    - API 스펙 (OpenAPI JSON → 마크다운 변환)
    - 아키텍처 문서
    - 핵심 비즈니스 로직 설명

Step 3: Claude Code에서 쿼리
  "이 프로젝트에서 인증 흐름은 어떻게 작동해?"
  "FIX-4 파이프라인 Stage 2 실패 시 어떤 조치를 해야 해?"
  → NotebookLM이 소스 기반으로 정확한 답변 + 인용 제공
```

### 2. 코드 리뷰 + 도메인 지식 참조
```
Step 1: 도메인 지식 노트북 준비
  - 견적 규칙 JSON → NotebookLM 업로드
  - 차단기 선택 가이드 → NotebookLM 업로드
  - 외함 크기 공식 → NotebookLM 업로드

Step 2: 코드 리뷰 시 연동
  Claude Code가 코드 리뷰 수행 중:
    1. 견적 로직 변경 감지
    2. NotebookLM에 해당 규칙 쿼리
    3. 규칙 준수 여부 검증
    4. 위반 사항 리뷰 코멘트 생성

Step 3: 활용 프롬프트
  "이 코드가 CHK_BUNDLE_MAGNET 규칙을 올바르게 구현했는지 확인해줘"
  → NLM에서 마그네트 동반자재 규칙 조회
  → 코드 대조 검증
```

### 3. 기술 문서 자동화 파이프라인
```
코드 변경 → Claude Code 분석 → NotebookLM 업데이트 → 문서 생성

구체적 흐름:
  1. git diff로 변경 사항 감지
  2. Claude Code가 변경 요약 생성
  3. 요약을 NotebookLM 소스로 추가
  4. NotebookLM에서 업데이트된 문서 생성
     - API 변경 로그
     - 릴리스 노트 초안
     - 영향 분석 보고서
```

### 4. 디버깅 지식 축적
```
Step 1: 버그 수정 시
  - 근본 원인 분석 결과 기록
  - 수정 내용 및 영향 범위 기록
  - 재발 방지 대책 기록

Step 2: NotebookLM에 축적
  노트북: "트러블슈팅 지식 베이스"
  소스: 각 버그 수정 보고서 (마크다운)

Step 3: 유사 문제 발생 시
  "이전에 비슷한 DB 연결 오류가 있었나? 어떻게 해결했어?"
  → NotebookLM이 과거 수정 이력에서 답변
```

## NABERAL Corp 통합 시나리오

### KIS Estimator 지식 관리
```
NotebookLM 노트북 구성:
  1. [KIS 견적 규칙] ← ai_estimation_core.json 기반
  2. [KIS 차단기 DB] ← breaker_dimensions.json + 단가표
  3. [KIS 외함 규칙] ← enclosure_rules + dimension_rules
  4. [KIS 트러블슈팅] ← 과거 버그 수정 기록 축적

Claude Code 연동:
  견적 코드 수정 시 → NLM에서 규칙 확인 → 검증 통과 후 커밋
```

### ERP 개발 지원
```
NotebookLM 노트북:
  [LEAN ERP 설계] ← 모듈 구조 + DB 스키마 + API 패턴

Claude Code 연동:
  새 모듈 개발 시 → NLM에서 기존 패턴 조회 → 일관성 유지
```

## 설정 가이드

### 환경변수
```bash
# Google API 키 (NotebookLM API 접근용)
GOOGLE_API_KEY=your_api_key_here

# NotebookLM 기본 노트북 ID (선택사항)
NLM_DEFAULT_NOTEBOOK=notebook_id_here
```

### Claude Code 설정 (.claude/settings.json)
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp"],
      "env": {
        "GOOGLE_API_KEY": "${GOOGLE_API_KEY}"
      }
    }
  }
}
```

## 주의사항
- NotebookLM API는 Google AI Studio 키 필요
- 무료 플랜: 노트북당 소스 50개 제한
- Plus 플랜: 노트북당 소스 300개, 우선 처리
- 민감한 코드/데이터는 업로드 전 검토 필요
