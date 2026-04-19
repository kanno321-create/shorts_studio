# Phase 8: Remote + Publishing + Production Metadata — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `08-CONTEXT.md` — this log preserves the alternatives considered during `--auto` selection.

**Date:** 2026-04-19
**Phase:** 08-remote-publishing-production-metadata
**Mode:** `--auto` (YOLO continuation, session #21)
**Areas discussed:** Remote connection, YouTube publishing, Production metadata + funnel, Test strategy, Smoke gate placement
**User input:** Option A (Phase 7 핸드오프 질문 답변) — "욜로모드 continuation + 최초 adapter smoke test 직전 승인 gate 1회 삽입"

---

## Remote Connection

### GitHub Authentication

| Option | Description | Selected |
|--------|-------------|----------|
| Fine-grained PAT | repo별 scope 제한 + 90일 만료 갱신 | ✓ |
| OAuth App | 다사용자 + 관리 콘솔 (과도) | |
| Deploy Key | push 전용 + repo 생성 API 호출 불가 | |

**Selected:** Fine-grained PAT
**Rationale:** 단일 사용자 Private repo에 OAuth App 오버헤드. Deploy Key는 repo 생성 API 호출 불가. Fine-grained PAT가 `contents:write` + `metadata:read` scope로 최소권한 충족.

### Harness Linking Method

| Option | Description | Selected |
|--------|-------------|----------|
| git submodule | 버전 고정 + clone 자동 연결 + .gitmodules 추적 | ✓ |
| git subtree | 원본 수정 리스크 | |
| Symlink | clone 이식성 부재 | |
| Copy | drift 재발 | |

**Selected:** git submodule
**Rationale:** REQUIREMENTS REMOTE-03 "submodule or 참조" 중 submodule이 PROJECT.md "v1.0.1 상속" 선언과 정합. clone 시 항상 같은 레이아웃 보장.

### Push Target Branch

| Option | Description | Selected |
|--------|-------------|----------|
| main | GitHub 2020+ 기본값 | ✓ |
| master | 레거시 | |

**Selected:** main
**Rationale:** 신규 저장소는 main으로 시작. 로컬 master → main rename 후 push.

---

## YouTube Publishing

### OAuth 2.0 Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Installed Application (desktop) | refresh token 1회 획득 후 재사용 | ✓ |
| Service Account | 채널 업로드 미지원 (Google 정책) | |
| Web OAuth | flask 서버 필요 | |

**Selected:** Installed Application (desktop OAuth)
**Rationale:** publisher AGENT.md `auth: oauth2_refresh_token` 명시. Service Account YouTube 정책 미지원. Web OAuth는 단일 사용자에 과도.

### AI Disclosure Enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| hardcoded True flag | 스위치 off 경로 자체 부재 (D-7 물리 차단) | ✓ |
| config 기반 토글 | off 경로 존재 = 우회 리스크 | |

**Selected:** hardcoded True flag
**Rationale:** Typecast/ElevenLabs 합성 음성 항상 사용. `syntheticMedia=True` 하드코딩 + `False` 0 hit anchor test.

### 48h+ Interval Enforcement Storage

| Option | Description | Selected |
|--------|-------------|----------|
| filesystem JSON lock | AGENT.md 기존 스펙 | ✓ |
| SQLite | 단일 lock state에 과도 | |
| Redis | 인프라 의존 | |

**Selected:** `.planning/publish_lock.json` filesystem lock
**Rationale:** publisher AGENT.md 이미 명시. atomic `os.replace` 기 존재 패턴 재사용.

### KST Peak Window

**Selected (publisher AGENT.md 확정):** 평일 20:00-23:00 KST / 주말 12:00-15:00 KST
**Rationale:** 재논의 불필요. `zoneinfo.ZoneInfo("Asia/Seoul")` 기반 검사.

---

## Production Metadata + Funnel

### production_metadata Insertion

| Option | Description | Selected |
|--------|-------------|----------|
| description HTML 주석 | AGENT.md 확정 + E-P2 역추적 | ✓ |
| tags 필드 | 500 char limit | |
| YouTube custom metadata API field | v3 미지원 | |

**Selected:** `<!-- production_metadata ...JSON... -->` description 말미
**Rationale:** 시청자 노출 zero + Reused Content 이의제기 역추적 자료.

### Pinned Comment + End-Screen

| Option | Description | Selected |
|--------|-------------|----------|
| 업로드 직후 API 체인 자동 실행 | 누락 방지 | ✓ |
| 수동 실행 | 누락 리스크 | |

**Selected:** 자동 (`commentThreads.insert` + description subscribe link)
**Rationale:** end-screen은 Data API v3 미지원 → description 내 CTA + pinned comment로 대체.

---

## Test Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Mock + smoke 1회 실 업로드 (privacyStatus=unlisted + cleanup) | Option A 사용자 확정 | ✓ |
| Mock only | smoke test 부재 → credential 오류 감지 불가 | |
| Full real API 스위트 | 실 채널 이력 누적 | |

**Selected:** Phase 7 mock 계승 + smoke test 1회
**Rationale:** 사용자 Option A. 실 API credit 최소 소모 + cleanup 으로 채널 이력 방지.

### Smoke Gate Placement

| Option | Description | Selected |
|--------|-------------|----------|
| 최초 real YouTube adapter 교체 직전 1회 | Option A | ✓ |
| 각 SC 직전 매번 | 속도 저하 | |
| 부재 (Full YOLO) | 사용자 Option B 거부 | |

**Selected:** Wave 5 단일 gate
**Rationale:** GitHub push / submodule은 reversible. YouTube upload는 채널 영구 이력. 유일 경계선에만 gate.

---

## Claude's Discretion (auto-resolved)

- Unit test 파일 네이밍 (Phase 7 관례 계승)
- 예외 클래스 이름 (scripts/orchestrator/ 10-class hierarchy 스타일 계승)
- submodule 내부 경로 충돌 resolution (Wave 1 실행 중 판단)

## Deferred Ideas

- 자동 재업로드 / 실패 복구 (v2)
- multi-channel publishing (v2)
- 핀 댓글 A/B testing (KPI-03 Phase 10)
- YouTube Shorts 썸네일 커스터마이즈 (current thumbnails.set로 처리)

---

*Generated 2026-04-19 by gsd-discuss-phase --auto (session #21 YOLO continuation from Phase 7)*
