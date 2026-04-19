# Phase 8: Remote + Publishing + Production Metadata — Research

**Researched:** 2026-04-19
**Domain:** YouTube Data API v3 실 업로드 + GitHub Private 저장소 생성/push + `production_metadata` 역추적 증명
**Confidence:** HIGH (Google/GitHub 공식 docs + 보존된 Phase 7 mock 패턴 직접 검증)

## Summary

Phase 8은 **실제 외부 상태 변이**를 최초로 일으키는 phase다. Phase 4 `publisher` 에이전트가 만든 upload plan JSON을 `scripts/publisher/youtube_uploader.py`가 받아 YouTube Data API v3 `videos.insert` (resumable, 1600 quota/업로드) + `thumbnails.set` (50 quota) + `commentThreads.insert` (50 quota) 체인으로 집행하고, 동일 Phase에서 `github.com/kanno321-create/shorts_studio` Private 저장소를 REST `POST /user/repos`로 생성하여 `main` 브랜치로 push + `naberal_harness v1.0.1`을 commit-pinned submodule로 연결한다.

핵심 locking은 (1) **48h+ publish_lock.json** filesystem atomic, (2) **KST window** `zoneinfo.ZoneInfo("Asia/Seoul")` 평일 20-23/주말 12-15, (3) **AI disclosure hardcoded** `status.containsSyntheticMedia=True` (2024-10-30 YouTube 신규 필드 — Phase 4 AGENT.md의 `syntheticMedia` 커스텀 키와 공식 필드 이름 불일치, 본 Research가 정정), (4) **end-screen은 Data API v3 미지원** — Phase 4 AGENT.md `captions.insert` 언급은 잘못이며 핀 댓글 + description CTA로 대체 (CONTEXT D-09 이미 결정). Smoke test는 `privacyStatus=unlisted` 업로드 후 `videos.delete` 즉시 cleanup (Option A Wave 5 gate에서 1회만 수행).

**Primary recommendation:** 8-Wave 분할 (Wave 0 FOUNDATION → Wave 1 REMOTE → Wave 2 OAUTH → Wave 3 LOCK+WINDOW+DISCLOSURE → Wave 4 METADATA+FUNNEL → **Wave 5 SMOKE-GATE (사용자 승인 정지)** → Wave 6 E2E+REGRESSION → Wave 7 PHASE GATE). Wave 0에서 `MockYouTube` + `MockGitHub`를 `tests/phase07/mocks/shotstack_mock.py` D-3 `allow_fault_injection=False` 패턴으로 복제하여 Phase 7 986/986 회귀를 깨지 않고 확장한다.

## Project Constraints (from CLAUDE.md + ROADMAP Hard Constraints)

Downstream planner가 어떤 계획도 위반하지 않도록 규정된 제약의 전체 목록. 이 중 **하나라도** 포함된 코드 경로는 pre_tool_use Hook에서 물리 차단된다.

- **CLAUDE-01:** 모든 SKILL.md ≤ 500줄 (double-entry check)
- **CLAUDE-02:** 에이전트 frontmatter `description` ≤ 1024자 (ASCII + 한글 동일)
- **CLAUDE-03:** 에이전트 총합 **32명** (Producer 14 + Inspector 17 + Supervisor 1) — filesystem invariant
- **CLAUDE-04:** `skip_gates=True` 문자열 소스에 0회 — pre_tool_use.py 차단
- **CLAUDE-05:** `TODO(next-session)` / `TODO\(next-session\)` 0 hits — pre_tool_use.py 차단
- **CLAUDE-06:** `selenium` / `playwright` / `webdriver` import 0 hits — AF-8 Selenium 영구 금지
- **CLAUDE-07:** `.preserved/harvested/` 파일 수정 금지 — chmod -w 로 OS 레벨 거부
- **CLAUDE-08:** `FAILURES.md` append-only — Hook check_failures_append_only 차단 (basename-exact + `_imported` 예외)
- **CLAUDE-09:** SKILL.md 수정 전 자동 백업 — Hook backup_skill_before_write `SKILL_HISTORY/<name>/v<ts>.md.bak`
- **CLAUDE-10:** 오케스트레이터 500~800줄 (5166줄 drift 재발 금지) — shorts_pipeline.py 787줄 보존
- **CLAUDE-11:** T2V 호출 경로 0 hits — I2V + Anchor Frame only (NotebookLM T1)
- **ROADMAP-H1:** **Selenium 업로드 영구 금지 (AF-8)** — YouTube Data API v3 공식만 (Phase 8 직격 제약)
- **ROADMAP-H2:** K-pop 트렌드 음원 직접 사용 금지 (AF-13) — COMPLY-02 상속
- **ROADMAP-H3:** `shorts_naberal` 원본 수정 금지 — Harvest 읽기만

## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 GitHub 인증 = Fine-grained PAT** — repo별 scope 제한, 90일 갱신. `GITHUB_TOKEN` env var 주입, 하드코딩/commit 금지. OAuth App / Deploy Key 탐색 금지.

**D-02 하네스 연결 = git submodule** — 로컬 경로 `harness/`, remote URL `github.com/kanno321-create/naberal_harness`. Subtree / symlink 탐색 금지.

**D-03 Push branch = `main`** — Wave 1 atomic commit 내 `git branch -m master main` 후 push. master로 push 금지.

**D-04 YouTube OAuth = Installed Application (desktop)** + refresh token `config/youtube_token.json`. Service Account / Web flow / flask 서버 탐색 금지.

**D-05 AI disclosure = hardcoded True flag** — `.containsSyntheticMedia=True` 하드코딩, off 경로 코드 자체에 불존재. `containsSyntheticMedia.*False` / `syntheticMedia.*False` grep 0 hits anchor test.

**D-06 48h+ 랜덤 간격 = filesystem JSON lock** — `.planning/publish_lock.json`, atomic `os.replace`. SQLite / Redis 탐색 금지.

**D-07 KST 윈도우 = 평일 20-23 / 주말 12-15 KST** — `zoneinfo.ZoneInfo("Asia/Seoul")` + `datetime.now(kst).weekday()/hour`. pytz / naive datetime 탐색 금지.

**D-08 production_metadata = description HTML 주석** — `<!-- production_metadata {JSON} -->`. 태그 필드 / 별도 파일 탐색 금지.

**D-09 Funnel = 업로드 직후 `commentThreads.insert` 핀 댓글 + description CTA** — end-screen은 Data API v3 **미지원** (captions.insert 경로 없음). Phase 4 AGENT.md §"end_screen_subscribe_cta" 필드는 plan JSON의 **의도 표기**이며 API 호출로 번역되지 않음.

**D-10 Test 전략 = Phase 7 mock 스타일 + smoke 1회 실 업로드** — `privacyStatus=unlisted` + `videos.delete` cleanup. MockYouTube / MockGitHub에 D-3 `allow_fault_injection=False` 계승.

**D-11 Smoke gate = real YouTube adapter 교체 직전 1회 정지** — Wave 5 plan 내 `SMOKE-GATE` 마커. 대표님 "진행" 확인 후 실행.

### Claude's Discretion

**CD-01 Unit test 파일 네이밍** — `test_youtube_uploader.py`, `test_github_remote.py`, `test_publish_lock.py`, `test_kst_window.py`, `test_production_metadata.py`, `test_pinned_comment.py` (Phase 7 `test_{feature}.py` 관례 계승)

**CD-02 예외 클래스** — `PublishLockViolation`, `PublishWindowViolation`, `AIDisclosureViolation`, `SeleniumForbidden` (이미 존재), `SmokeCleanupFailed`, `GitHubRemoteError` (scripts/orchestrator/ 10-class hierarchy 스타일 계승)

**CD-03 submodule 내부 경로 충돌** — Wave 1 실행 중 발견 시 내부 판단

### Deferred Ideas (OUT OF SCOPE)

- 자동 재업로드 / 실패 복구 (v2)
- multi-channel publishing (v2)
- 핀 댓글 A/B variant 랜덤 할당 (Phase 10 KPI-03)
- Shorts 썸네일 커스터마이즈 별도 API (현재 `thumbnails.set`로 처리)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PUB-01 | AI disclosure 토글 자동 ON (A-P3 차단) | Research Area 1 — `status.containsSyntheticMedia=True` (2024-10-30 공식 필드) 하드코딩 + grep anchor. **Correction**: Phase 4 AGENT.md의 `syntheticMedia` 커스텀 키는 공식 필드 이름이 아님. 실 API body는 `status.containsSyntheticMedia` 여야 함. |
| PUB-02 | YouTube Data API v3 공식 사용 (Selenium 영구 금지 — AF-8) | Research Area 1 — `google-api-python-client` + `googleapiclient.discovery.build("youtube","v3",credentials=creds)` + `videos().insert(part=..., body=..., media_body=MediaFileUpload(path, chunksize=-1, resumable=True))`. AGENT-06 셀레늄 blocklist Hook + anchor test로 이중 차단. |
| PUB-03 | 주 3~4편, 48h+ 랜덤 간격, KST 피크 시간 | Research Area 2 — `publish_lock.json` atomic os.replace + `zoneinfo.ZoneInfo("Asia/Seoul")`. 일일 quota 10,000u / 업로드 1,600u = 최대 6편/일, 48h+ 랜덤으로 실제 3.5편/주 유지. |
| PUB-04 | Production metadata 첨부 (Reused content 증명 — E-P2 차단) | Research Area 4 — 4-field {script_seed, assets_origin, pipeline_version, checksum(sha256 mp4)}를 description 말미 HTML 주석 삽입. Phase 4 `ins-platform-policy` 이미 4-field enforcement 검증. |
| PUB-05 | 핀 댓글 + end-screen subscribe funnel | Research Area 1 — `commentThreads.insert`로 핀 댓글 작성 + description CTA 삽입. **Correction**: end-screen은 Data API v3 미지원(Studio UI 전용), D-9 대체 전략 필요. |
| REMOTE-01 | GitHub Private 저장소 생성 | Research Area 5 — `POST https://api.github.com/user/repos` + `{"name":"shorts_studio","private":true}` + Bearer PAT. 201 Created 또는 422 name-taken 멱등 처리. |
| REMOTE-02 | `git push -u origin main` | Research Area 5 — `git branch -m master main` → `git remote add origin https://github.com/kanno321-create/shorts_studio.git` → `GIT_ASKPASS` 또는 credential.helper로 PAT 주입 → `git push -u origin main`. |
| REMOTE-03 | naberal_harness v1.0.1 submodule 연결 | Research Area 6 — `git submodule add https://github.com/kanno321-create/naberal_harness harness/` → `cd harness && git checkout <v1.0.1 SHA>` → parent `git add .gitmodules harness && git commit`. `--recurse-submodules` clone 지원. |

## Standard Stack

### Core Python Libraries

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-api-python-client` | 2.161.0+ (2026-04 latest) | YouTube Data API v3 클라이언트 | Google 공식, `build("youtube","v3",...)` + `MediaFileUpload(resumable=True)` 업로드 프로토콜 | 
| `google-auth-oauthlib` | 1.2.1+ | OAuth 2.0 Installed App flow | `InstalledAppFlow.run_local_server(port=0)` — 브라우저 + 로컬 HTTP redirect, 수동 코드 붙여넣기 불필요 |
| `google-auth-httplib2` | 0.2.0+ | 인증된 HTTP transport | googleapiclient 의존성 |
| `google-auth` | 2.35.0+ | `Credentials.from_authorized_user_file` + `Request().refresh()` | refresh token 로드 + 만료 시 자동 갱신 |
| `requests` | 2.32.3+ | GitHub REST API 호출 (PAT Bearer) | 이미 shorts_naberal 유산 존재 확률 높음, stdlib `urllib.request`도 가능하나 헤더 관리 번잡 |

**Installation:**
```bash
pip install google-api-python-client==2.161.0 google-auth-oauthlib==1.2.1 google-auth-httplib2==0.2.0 requests==2.32.3
```

**Version verification (MUST before Wave 0):**
```bash
pip index versions google-api-python-client
pip index versions google-auth-oauthlib
pip index versions google-auth
pip index versions requests
```
레거시 `oauth2client` (Google 2019 deprecated) 사용 금지. 2026-04 시점 Python 3.11+ + google-api-python-client 2.x만 허용.

### Supporting Stack (Stdlib only)

| Library | Purpose | When to Use |
|---------|---------|-------------|
| `zoneinfo` | KST 타임존 (`ZoneInfo("Asia/Seoul")`) | Python 3.9+ 내장 — pytz 금지 |
| `subprocess` | git CLI 호출 (`git submodule add`, `git push`) | Wave 1 GitHub push/submodule |
| `hashlib.sha256` | production_metadata checksum | PUB-04 증명용 |
| `json` + `os.replace` | `publish_lock.json` atomic rw | Phase 5 Checkpointer 패턴 복제 |
| `pathlib.Path` | 경로 처리 | 기존 orchestrator 관례 |
| `datetime.timezone` / `datetime.datetime` | elapsed 계산 | KST + UTC 상호 변환 |
| `random.randint` | 48h~60h jitter | `random.randint(0, 720)` 분 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `google-api-python-client` | raw `requests` to REST | 거부 — multipart resumable 프로토콜 수작업 복잡, 공식 MediaFileUpload이 재시도 포함 |
| `InstalledAppFlow` | Service Account | **불가능** — YouTube Data API v3는 Service Account 채널 업로드 미지원 (공식 정책) |
| `PyGithub` | `requests` | PyGithub 간결하나 단일 엔드포인트(`POST /user/repos`) + submodule은 git CLI 필수 → 의존성 추가할 가치 없음 |
| `subprocess` git CLI | `pygit2` | pygit2는 libgit2 바인딩 필요, CI 휴대성 저하. subprocess + `git` CLI는 모든 Windows/Linux에서 동일 |
| `pytz.timezone("Asia/Seoul")` | `zoneinfo.ZoneInfo` | pytz는 Python 3.9+에서 deprecated, zoneinfo가 표준 |

## Architecture Patterns

### Recommended Project Structure

```
scripts/
├── publisher/                          # Phase 8 Wave 2-4 신규
│   ├── __init__.py
│   ├── oauth.py                        # InstalledAppFlow + token.json refresh
│   ├── youtube_uploader.py             # videos.insert + thumbnails.set + commentThreads.insert
│   ├── publish_lock.py                 # 48h+ jitter + os.replace
│   ├── kst_window.py                   # zoneinfo 평일/주말 판정
│   ├── production_metadata.py          # 4-field {script_seed, assets_origin, pipeline_version, checksum} + description 주입
│   └── github_remote.py                # POST /user/repos + subprocess git push + submodule add
├── orchestrator/                       # 기존 Phase 5+6+7 보존
│   ├── circuit_breaker.py              # youtube_uploader 가 재사용
│   └── checkpointer.py                 # publish_lock.py 가 atomic os.replace 패턴 복제
config/                                 # Phase 8 Wave 2 신규 (gitignored)
├── client_secret.json                  # Google Cloud Console OAuth 2.0 desktop
└── youtube_token.json                  # run_local_server 후 획득 refresh token
.planning/
└── publish_lock.json                   # Phase 8 Wave 3 신규 (gitignored — 업로드 이력 노출 방지)
tests/phase08/                          # Phase 8 신규
├── __init__.py
├── conftest.py                         # tmp_path + MockYouTube + MockGitHub fixture
├── mocks/
│   ├── __init__.py
│   ├── youtube_mock.py                 # allow_fault_injection=False default
│   └── github_mock.py                  # same pattern
├── fixtures/                           # sha256 반복성 확보 0-byte fixture
│   └── mock_video.mp4                  # Phase 7 mock_shotstack.mp4 재사용도 고려
└── test_*.py                           # feature별 unit + E2E
harness/                                # Phase 8 Wave 1 submodule 진입점
└── (v1.0.1 commit SHA로 pinned)
```

### Pattern 1: Resumable Upload with Exponential Backoff

**What:** YouTube `videos.insert`는 대용량 파일(최대 256GB — Shorts는 < 50MB 현실적) resumable 프로토콜 사용. 네트워크 절단 시 같은 upload URI로 재시도.

**When to use:** 모든 `videos.insert` 호출. Shorts 파일 크기(10~30MB)도 `chunksize=-1` (전체 1 request) + `resumable=True` 로 충분.

**Example:**
```python
# Source: https://github.com/youtube/api-samples/blob/master/python/upload_video.py
# Adapted: Phase 8 scripts/publisher/youtube_uploader.py
import random
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import httplib2

RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 10

def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if response is not None:
                if "id" in response:
                    return response["id"]  # videoId for downstream thumbnails.set
                raise RuntimeError(f"Unexpected upload response: {response}")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP {e.resp.status}: {e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable error: {e}"
        if error is not None:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError("MAX_RETRIES exceeded")
            max_sleep = 2**retry
            time.sleep(random.random() * max_sleep)
            error = None
```

### Pattern 2: OAuth 2.0 Refresh Token Persistence

**What:** `Credentials.from_authorized_user_file("youtube_token.json")` 로 저장된 refresh token 로드 → 만료 시 `creds.refresh(Request())` 자동 갱신 → 재저장.

**When to use:** 모든 세션 시작 시. 최초 1회만 `InstalledAppFlow.run_local_server(port=0)` 실행.

**Example:**
```python
# Source: google-auth-oauthlib README + upload_video.py
# Phase 8 scripts/publisher/oauth.py
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",    # videos.insert + thumbnails.set
    "https://www.googleapis.com/auth/youtube.force-ssl", # commentThreads.insert
]

CLIENT_SECRET_PATH = Path("config/client_secret.json")
TOKEN_PATH = Path("config/youtube_token.json")

def get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)  # 0 = OS 할당 free port
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds
```

### Pattern 3: 48h+ Jitter Publish Lock (Checkpointer Reuse)

**What:** `publish_lock.json` atomic read → elapsed_hours 계산 → < 48 + jitter 이면 `PublishLockViolation` raise. 업로드 성공 직후 `os.replace` 로 lock 갱신.

**When to use:** 모든 `videos.insert` 호출 직전. smoke test도 동일 (Wave 5).

**Example:**
```python
# Phase 8 scripts/publisher/publish_lock.py
# Pattern: scripts/orchestrator/checkpointer.py atomic os.replace (line 21-22)
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LOCK_PATH = Path(".planning/publish_lock.json")
KST = ZoneInfo("Asia/Seoul")
MIN_ELAPSED_HOURS = 48
MAX_JITTER_MIN = 720  # 0~12h 추가 지터 → 실효 48~60h

class PublishLockViolation(RuntimeError):
    def __init__(self, remaining_min: int):
        self.remaining_min = remaining_min
        super().__init__(f"Publish lock active, {remaining_min} min remaining")

def assert_can_publish() -> None:
    if not LOCK_PATH.exists():
        return  # 최초 업로드
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    last = datetime.fromisoformat(data["last_upload_iso"])
    jitter = data.get("jitter_applied_min", 0)
    required = MIN_ELAPSED_HOURS * 60 + jitter
    elapsed = (datetime.now(timezone.utc) - last).total_seconds() / 60
    if elapsed < required:
        raise PublishLockViolation(int(required - elapsed))

def record_upload() -> None:
    jitter = random.randint(0, MAX_JITTER_MIN)
    payload = {
        "last_upload_iso": datetime.now(timezone.utc).isoformat(),
        "jitter_applied_min": jitter,
        "_schema": 1,
    }
    tmp = LOCK_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, LOCK_PATH)  # atomic on Windows + Unix
```

### Pattern 4: KST Window Enforcement

**Example:**
```python
# Phase 8 scripts/publisher/kst_window.py
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

class PublishWindowViolation(RuntimeError):
    pass

def assert_in_window(now_kst: datetime | None = None) -> None:
    now = now_kst or datetime.now(KST)
    weekday = now.weekday()  # 0=Mon .. 6=Sun
    hour = now.hour
    is_weekday = weekday < 5
    if is_weekday:
        ok = 20 <= hour < 23
    else:
        ok = 12 <= hour < 15
    if not ok:
        raise PublishWindowViolation(
            f"Outside KST window (weekday={weekday} hour={hour})"
        )
```

### Pattern 5: Production Metadata HTML Comment Injection

**Example:**
```python
# Phase 8 scripts/publisher/production_metadata.py
import hashlib
import json
from pathlib import Path
from typing import TypedDict

PIPELINE_VERSION = "1.0.0"  # Phase 8 shipping version

class ProductionMetadata(TypedDict):
    script_seed: str         # Phase 5 orchestrator seed
    assets_origin: str       # e.g. "kling:primary" / "runway:fallback"
    pipeline_version: str
    checksum: str            # "sha256:<hex>"

def compute_checksum(mp4_path: Path) -> str:
    h = hashlib.sha256()
    with mp4_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"

def inject_into_description(description: str, meta: ProductionMetadata) -> str:
    # ins-platform-policy regex: r'<!-- production_metadata\n({.*?})\n-->'
    # 4 필드 누락 시 Phase 4 inspector FAIL.
    block = (
        "\n<!-- production_metadata\n"
        + json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        + "\n-->"
    )
    return description + block
```

### Pattern 6: Upload Plan JSON → API Call Translation

**Example:**
```python
# Phase 8 scripts/publisher/youtube_uploader.py (excerpt)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def build_insert_body(plan: dict) -> dict:
    """Translate Phase 4 publisher upload plan JSON into Data API body."""
    snippet = plan["snippet"].copy()
    # production_metadata 이미 description에 주입된 상태로 받는다.
    body = {
        "snippet": {
            "title": snippet["title"][:100],
            "description": snippet["description"][:5000],
            "tags": snippet.get("tags", []),
            "categoryId": snippet.get("categoryId", "24"),
            "defaultLanguage": snippet.get("defaultLanguage", "ko"),
            # NOTE: defaultAudioLanguage is NOT a writable snippet field per
            # official docs — drop or skip silently. (Research Pitfall 5)
        },
        "status": {
            "privacyStatus": plan["status"]["privacyStatus"],
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,   # D-05 HARDCODED — AI disclosure
            "license": "youtube",
            "embeddable": True,
            "publicStatsViewable": True,
        },
    }
    return body

def upload_video(youtube, plan: dict, video_path: Path) -> str:
    body = build_insert_body(plan)
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    request = youtube.videos().insert(
        part=",".join(body.keys()),  # "snippet,status"
        body=body,
        media_body=media,
    )
    return resumable_upload(request)  # returns video_id
```

### Anti-Patterns to Avoid

- **Selenium / webdriver import** — Hook block + anchor test. AF-8 YouTube ToS 위반 → 채널 영구정지 리스크.
- **`syntheticMedia` 커스텀 키** — Phase 4 AGENT.md에서 non-canonical 이름 사용. Body 빌더에서 반드시 공식 `status.containsSyntheticMedia` 로 변환.
- **`captions.insert`로 end-screen 삽입 시도** — 애초에 end-screen은 `videos` resource나 `captions` resource 어느 쪽에도 존재하지 않는 기능. YouTube Studio UI 전용.
- **PAT을 remote URL에 embed** — `https://<token>@github.com/...` 는 local git config에 평문 저장. `GIT_ASKPASS` 환경변수 또는 `git credential-manager` 사용.
- **Service Account 사용 시도** — Data API v3 채널 업로드 **지원 안 함** (공식 정책).
- **`pytz.timezone("Asia/Seoul")`** — deprecated. `zoneinfo.ZoneInfo`만 사용.
- **naive datetime 비교** — `datetime.now()` vs `datetime.fromisoformat("...+00:00")` 는 TypeError. 항상 `datetime.now(timezone.utc)` 또는 `datetime.now(KST)`.
- **Lock 파일을 commit** — `.planning/publish_lock.json` 은 gitignore에 추가 필수 (업로드 이력 노출 방지).
- **`client_secret.json` 또는 `youtube_token.json` commit** — `.gitignore` 이미 line 3-4에 등록. Wave 2 실행 시 재확인.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Resumable multipart upload to YouTube | `requests.post` with manual `Content-Range` / `Location` chasing | `googleapiclient.http.MediaFileUpload(resumable=True)` + `insert_request.next_chunk()` | Google 공식 프로토콜은 edge case(3xx resume, 308 progress) 다수. 수동 구현 시 네트워크 흔들림 = 전체 재시작. |
| OAuth 2.0 authorization code 교환 | `requests.post` to `oauth2.googleapis.com/token` with code+verifier | `InstalledAppFlow.run_local_server(port=0)` | PKCE + state token + loopback redirect 자동 처리. 수작업은 redirect_uri mismatch 함정. |
| Refresh token rotation | 수동 refresh + 만료시간 추적 | `google.auth.transport.requests.Request()` + `creds.refresh()` | 라이브러리가 만료 시점 판단 + 새 access_token 자동 교환. |
| git submodule 메타데이터 파싱 | `.gitmodules` INI 수작업 파싱 | `git submodule` CLI + `git config -f .gitmodules` | CLI는 중첩 submodule + pathspec + URL encoding 처리. |
| GitHub repo 존재 확인 | `GET /repos/:owner/:name` 404 pattern | `POST /user/repos` + 422 "name already exists" 멱등 처리 | 1 round-trip으로 create-or-skip. 2단계 check-then-create는 TOCTOU. |
| SHA256 checksum streaming | 파일 전체 read + hashlib.sha256 한번에 | `hashlib.sha256()` + 64KB chunk iter (Pattern 5 위 코드) | 대용량 파일 메모리 폭발 방지 (Shorts는 작으나 관례). |
| 타임존 변환 | naive + offset 수작업 | `zoneinfo.ZoneInfo` | DST / leap second / historical offset 자동 처리. |
| Filesystem atomic JSON write | `open("w")` + write | `os.replace(tmp, target)` (Phase 5 Checkpointer 패턴) | Windows에서 `os.rename`은 target 존재 시 실패, `os.replace`만 atomic. |

**Key insight:** 본 Phase에서 새로 짤 가치가 있는 것은 **publish_lock + kst_window + production_metadata 3종**과 이들을 묶는 `youtube_uploader.py` 오케스트레이션뿐이다. 나머지는 Google/Git 공식 도구가 이미 정답을 알고 있다.

## Runtime State Inventory

Phase 8은 **새로운 runtime state를 최초 생성**하는 phase (migration이 아닌 greenfield 연장). 그럼에도 런타임 잔존물이 남을 가능성이 있으므로 전수 감사.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | `.planning/publish_lock.json` (Wave 3 신규 생성, 업로드 이력 persistent) | gitignore 추가 + 최초 실행 시 파일 부재 허용 (first-upload path) |
| **Live service config** | (1) GitHub `shorts_studio` Private repo — 원격 존재 상태. (2) YouTube 채널 — 실 업로드 이력 영구 남음 (Wave 5 smoke는 unlisted + delete로 대응). (3) Google Cloud Console OAuth 2.0 client — client_secret.json 발급 수동 단계 필요 (대표님 수행). | 대표님 수동: (a) Google Cloud Console에서 OAuth 2.0 Desktop 클라이언트 생성 + `client_secret.json` 다운로드 → `config/`, (b) GitHub fine-grained PAT 생성 + `GITHUB_TOKEN` env. 자동: 레포 생성 + 첫 OAuth flow는 `run_local_server`가 브라우저 오픈. |
| **OS-registered state** | None — Phase 8은 Windows Task Scheduler / systemd / launchd 등록 없음. Phase 10에서 cron 도입 예정. | 없음 — 명시. |
| **Secrets/env vars** | (1) `GITHUB_TOKEN` — fine-grained PAT, env var 또는 `.env` (gitignored). (2) `config/client_secret.json` — Google OAuth 2.0 desktop credentials. (3) `config/youtube_token.json` — refresh token, Wave 2에서 생성. 세 개 모두 이미 `.gitignore` 등록 확인 완료 (line 3-4). | 검증 테스트: `git check-ignore -v config/client_secret.json` 로 gitignore hit 확인. Hook `check_failures_append_only` 는 이 경로 관여 없음. |
| **Build artifacts** | `__pycache__/` (이미 gitignore). submodule `harness/` 클론 후 로컬 state는 .git/modules/harness/ 에 위치 — 삭제 시 `git submodule deinit` 필요. | 없음 — 정상 동작. 단, submodule path 충돌(예: `harness/` 이미 존재) 시 Wave 1 CD-03 discretion 발동. |

**Nothing-found category:** OS-registered state (None — verified by inspection of ROADMAP Phase 8 goal + Phase 9/10 cron 도입 일정).

**The canonical question test:** *저장소 전체가 rename/delete되어도 외부에 남은 state는?* → **(a) YouTube 채널 영상(smoke는 delete, real은 의도적 영구)**, **(b) GitHub Private repo (의도적 영구)**. 둘 다 "의도된 상태"이며 undo 경로는 수동 (YouTube Studio / GitHub Settings).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | 전체 | ✓ | 3.11+ (Phase 5 기존 확인) | — |
| `pip install` network | Wave 0 의존성 | ✓ | — | 미설치 시 Plan 실행 전 블록 |
| `git` CLI | Wave 1 push + submodule | ✓ | Phase 3/6/7 모두 subprocess 호출 확인 | — |
| GitHub API 접속 | Wave 1 repo 생성 | ✓ | api.github.com | — |
| `GITHUB_TOKEN` env var | Wave 1 auth | ✗ (미발급) | — | **Blocking** — 대표님 fine-grained PAT 발급 수동 |
| Google Cloud OAuth 2.0 desktop client | Wave 2 token 획득 | ✗ (미발급) | — | **Blocking** — 대표님 Google Cloud Console 수동 |
| `config/client_secret.json` | Wave 2 InstalledAppFlow | ✗ (미존재) | — | **Blocking** — 상기 발급 후 저장 |
| Browser (for `run_local_server`) | Wave 2 1회 OAuth | ✓ (Windows default) | — | CLI fallback: `flow.run_console()` (deprecated 2022-10, 회피) |
| Port free for `run_local_server` | Wave 2 OAuth redirect | ✓ (port=0 OS 할당) | — | — |
| `naberal_harness v1.0.1` GitHub URL | Wave 1 submodule | TBD | TBD — 대표님 확인 필요 | **Blocking 가능성** — 레포 Public이 아니면 PAT에 naberal_harness read 권한 필요 |

**Missing dependencies with no fallback (BLOCKING):**
- `GITHUB_TOKEN` PAT — Wave 1 시작 전 발급 필수
- `config/client_secret.json` Google Cloud OAuth 2.0 Desktop — Wave 2 시작 전 발급 필수
- `naberal_harness` 원격 URL 및 접근 권한 — Wave 1 submodule 시도 시 확인

**Missing dependencies with fallback:** 없음 — 상기 3종 blocking으로 plan 실행 전 대표님 수동 단계 명시 필요.

## Common Pitfalls

### Pitfall 1: Redirect URI Mismatch in OAuth
**What goes wrong:** `run_local_server(port=0)` 가 할당한 랜덤 포트가 Google Cloud Console에 등록된 `http://localhost:PORT` 와 mismatch → `redirect_uri_mismatch` 에러.
**Why it happens:** Desktop client는 Google 2022+ 자동 loopback 허용, 그러나 레거시 설정에서 고정 포트만 허용하는 경우 존재.
**How to avoid:** Google Cloud Console → OAuth 2.0 Client ID → Desktop app type 선택 (Web app 금지). "Authorized redirect URIs"에 `http://localhost` 단일 entry 또는 비어있으면 OK.
**Warning signs:** `run_local_server` 실행 시 브라우저 "Error 400: redirect_uri_mismatch".

### Pitfall 2: PAT URL Embedding Leaks to Git Config
**What goes wrong:** `git remote add origin https://<TOKEN>@github.com/...` 로 설정하면 `.git/config` 평문 저장 → 로컬 저장소 공유 시 PAT 누출.
**Why it happens:** 초보자 안내 가이드가 이 패턴을 "간단한 방법"으로 홍보.
**How to avoid:** `GIT_ASKPASS` 환경변수 + shell script로 PAT 반환, 또는 `git credential-manager` 사용. Wave 1 Plan에서 env-var 전달 subprocess 호출로 통일:
```python
env = os.environ.copy()
env["GIT_ASKPASS"] = "scripts/publisher/_git_askpass.sh"  # echo $GITHUB_TOKEN
env["GITHUB_TOKEN"] = os.environ["GITHUB_TOKEN"]
subprocess.run(["git", "push", "-u", "origin", "main"], check=True, env=env)
```
**Warning signs:** `git config --list` 출력에 token 문자열 노출.

### Pitfall 3: Python CP949 Windows Encoding on Korean Metadata
**What goes wrong:** `publish_lock.json` 또는 `production_metadata` JSON에 한글 포함 시, Windows 기본 cp949 stdout에서 `UnicodeEncodeError`.
**Why it happens:** Phase 6 Plan 06-09 이미 맞닥뜨려 해결 (STATE #28). `sys.stdout.reconfigure(encoding="utf-8")` + `ensure_ascii=False` 관례.
**How to avoid:** Phase 6/7 관례 계승:
```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
# 모든 json.dumps에 ensure_ascii=False
```
**Warning signs:** subprocess 실행 시 `UnicodeEncodeError: 'cp949' codec`.

### Pitfall 4: Filter Order Non-Exact Assertion
**What goes wrong:** Phase 6 Plan 06-07의 `test_filter_order_preservation.py` 교훈 — D-19 canonical filter 순서는 **EXACT list equality** 로 검증해야 함.
**Why it happens:** `set()` 비교 / 부분 포함 검사는 순서 교란 놓침.
**How to avoid:** Phase 8은 `videos.insert` body part 순서가 API 레벨에서 무관하나, `"snippet,status,recordingDetails"` 파트 string 순서가 alphabetical vs plan 정의 순서 테스트 시 exact match 필수.
**Warning signs:** 테스트 pass but production에서 `part` 쿼리 파라미터 인코딩 변조.

### Pitfall 5: `defaultAudioLanguage` Silently Dropped
**What goes wrong:** Phase 4 AGENT.md snippet에 `defaultAudioLanguage: "ko"` 필드 포함. 그러나 `videos.insert` spec은 이 필드를 **writable로 명시하지 않음** (오직 `defaultLanguage`만 writable).
**Why it happens:** Google 문서 업데이트 지연 + REST 공식 docs는 v3 revision history에서 필드 변경 추적.
**How to avoid:** `build_insert_body()` 에서 `defaultAudioLanguage` 는 drop하고 주석 남기기. Phase 4 AGENT.md 수정은 별도 Phase (out of scope) — Phase 8은 publisher JSON 받을 때 alpha tolerant하게 unknown key 무시.
**Warning signs:** API 400 `invalidSnippetField`.

### Pitfall 6: `containsSyntheticMedia` vs Custom `syntheticMedia` Key
**What goes wrong:** Phase 4 publisher AGENT.md는 `ai_disclosure.syntheticMedia: true` 라는 **커스텀 구조** 사용. 실제 YouTube Data API v3 공식 필드는 `status.containsSyntheticMedia` (2024-10-30 추가).
**Why it happens:** Phase 4 에이전트는 계획 JSON만 생성, 실 API 호출 미포함 → 필드 이름 불일치 안 터짐.
**How to avoid:** `build_insert_body()` 변환 계층에서 `plan["ai_disclosure"]["syntheticMedia"]` → `body["status"]["containsSyntheticMedia"]` mapping. grep anchor test: `containsSyntheticMedia.*False` 0 hits AND `containsSyntheticMedia.*True` ≥ 1 hit in uploader source.
**Warning signs:** API accepts body but YouTube 내부에서 AI disclosure 플래그 미기록 → 나중에 채널 경고.

### Pitfall 7: `captions.insert` 오용으로 end-screen 시도
**What goes wrong:** Phase 4 AGENT.md §"funnel" 에 `end_screen_subscribe_cta: true` 언급 + CONTEXT D-09의 원문 주석 "captions.insert 체인". captions.insert는 **자막**만 가능, end-screen 조작 불가.
**Why it happens:** YouTube Studio는 end-screen을 UI로 편집 가능하나 **Data API v3 미지원**.
**How to avoid:** CONTEXT D-09 이미 "description 내 subscribe 링크 + pinned comment CTA로 대체" 확정. Plan 작성 시 end-screen API 호출 경로 생성 금지. 테스트 anchor: `captions.insert` grep 0 hits in scripts/publisher/.
**Warning signs:** 계획 단계에서 "end-screen API" 언급. Wave 4 플랜 시 제거.

### Pitfall 8: Hook pre_tool_use.py False Positive on "selenium" in Docs
**What goes wrong:** Phase 8 RESEARCH.md 본 문서가 "selenium 금지" 문장을 포함 → Hook 차단 시도.
**Why it happens:** Hook은 **import/require** 패턴만 차단하도록 설계되었으나, Plan 06-08 확장 후 일부 패턴이 substring match.
**How to avoid:** Plan 실행 시 Hook 테스트 케이스 (Phase 5 `verify_hook_blocks.py` 5/5) 재실행 → 신규 markdown docs는 차단되지 않음을 확인. 본 RESEARCH.md 작성 시 Hook은 이미 `.preserved/harvested/` + `_imported_from_shorts_naberal.md` exception 보유.
**Warning signs:** commit 시 Hook "denies markdown file mentioning selenium".

### Pitfall 9: Quota Exhaustion in Dev
**What goes wrong:** 개발 중 반복 `videos.insert` (1,600 quota / 호출) → 10,000 일일 quota 초과 → 403 `quotaExceeded` → 다음 날(PT midnight)까지 block.
**Why it happens:** Mock 없이 실 API 호출 반복.
**How to avoid:** Phase 7 MockShotstack 패턴 계승 — 모든 unit/integration 테스트는 `MockYouTube` 사용 (allow_fault_injection=False default). 실 호출은 Wave 5 smoke 단 1회.
**Warning signs:** `HttpError: <HttpError 403 when requesting ... "The request cannot be completed because you have exceeded your quota.">`.

### Pitfall 10: Submodule 경로 충돌 with 기존 `harness/` 폴더
**What goes wrong:** studios/shorts 내부에 `harness/` 폴더가 이미 존재하면 `git submodule add` 실패 → `already exists in the index`.
**Why it happens:** 기존 코드가 `../../harness/` 심볼릭 참조 또는 bare 폴더 생성.
**How to avoid:** Wave 1 Plan 실행 전 `ls harness/ 2>/dev/null` 확인. 존재 시 내용 sha256 비교 → identical이면 삭제 후 `git submodule add`, 다르면 CD-03 discretion 발동(사용자 확인).
**Warning signs:** `fatal: 'harness/' already exists in the index`.

## Code Examples

### Example A: End-to-End Upload Orchestration (Wave 4)

```python
# scripts/publisher/youtube_uploader.py (excerpt, ~120 lines target)
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from scripts.orchestrator.circuit_breaker import CircuitBreaker
from scripts.publisher.oauth import get_credentials
from scripts.publisher.publish_lock import assert_can_publish, record_upload
from scripts.publisher.kst_window import assert_in_window
from scripts.publisher.production_metadata import inject_into_description, compute_checksum


class YouTubeClient(Protocol):
    """MockYouTube (tests) and real googleapiclient.discovery resource share."""
    def videos(self): ...
    def thumbnails(self): ...
    def commentThreads(self): ...


def publish(
    youtube: YouTubeClient,
    plan: dict,
    video_path: Path,
    thumbnail_path: Path,
    channel_id: str,
) -> str:
    # Gate 1: 48h+ jitter + KST window
    assert_can_publish()
    assert_in_window()

    # Gate 2: description에 production_metadata 주입 (checksum = sha256 of mp4)
    meta = {
        "script_seed": plan["production_metadata"]["script_seed"],
        "assets_origin": plan["production_metadata"]["assets_origin"],
        "pipeline_version": "1.0.0",
        "checksum": compute_checksum(video_path),
    }
    plan["snippet"]["description"] = inject_into_description(
        plan["snippet"]["description"], meta,
    )

    # Gate 3: videos.insert (resumable)
    body = build_insert_body(plan)
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    insert_req = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )
    video_id = resumable_upload(insert_req)

    # Gate 4: thumbnails.set
    thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/png")
    youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()

    # Gate 5: pinned comment (D-09)
    pin_text = plan.get("funnel", {}).get("pinned_comment", "구독해주세요!")
    youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "channelId": channel_id,
                "videoId": video_id,
                "topLevelComment": {"snippet": {"textOriginal": pin_text}},
            },
        },
    ).execute()

    # Gate 6: publish_lock 갱신 (atomic)
    record_upload()

    return video_id
```

### Example B: GitHub Repo Create + Push (Wave 1)

```python
# scripts/publisher/github_remote.py (excerpt)
import os
import subprocess
from pathlib import Path

import requests

GITHUB_API = "https://api.github.com"


def create_private_repo(name: str, token: str) -> dict:
    """Idempotent: returns existing repo if 422 name-taken."""
    resp = requests.post(
        f"{GITHUB_API}/user/repos",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"name": name, "private": True, "auto_init": False},
        timeout=30,
    )
    if resp.status_code == 201:
        return resp.json()
    if resp.status_code == 422:
        # name already exists → fetch it
        owner = os.environ.get("GITHUB_USER", "kanno321-create")
        existing = requests.get(
            f"{GITHUB_API}/repos/{owner}/{name}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        existing.raise_for_status()
        return existing.json()
    resp.raise_for_status()


def push_to_remote(repo_url: str, token: str, branch: str = "main") -> None:
    env = os.environ.copy()
    # GIT_ASKPASS returns the token from stdin — avoids URL embedding.
    env["GIT_ASKPASS"] = str(Path("scripts/publisher/_git_askpass.sh").resolve())
    env["GITHUB_TOKEN"] = token
    subprocess.run(["git", "branch", "-M", branch], check=True)
    subprocess.run(["git", "remote", "add", "origin", repo_url],
                   check=False)  # idempotent
    subprocess.run(["git", "push", "-u", "origin", branch],
                   check=True, env=env)


def add_harness_submodule(harness_url: str, commit_sha: str) -> None:
    """Pin to v1.0.1 SHA (REMOTE-03)."""
    subprocess.run(["git", "submodule", "add", harness_url, "harness"],
                   check=True)
    subprocess.run(["git", "checkout", commit_sha],
                   check=True, cwd="harness")
    subprocess.run(["git", "add", ".gitmodules", "harness"], check=True)
```

### Example C: Smoke Test with Cleanup (Wave 5)

```python
# tests/phase08/test_smoke_real_upload.py — RUN ONLY WITH --run-smoke FLAG
import time
import pytest
from pathlib import Path

from scripts.publisher.oauth import get_credentials
from scripts.publisher.youtube_uploader import publish
from googleapiclient.discovery import build


@pytest.mark.smoke  # opt-in only, SMOKE-GATE user approval
def test_real_upload_unlisted_with_cleanup(tmp_path):
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    plan = {
        "snippet": {
            "title": "Smoke test — SHORTS_STUDIO Wave 5",
            "description": "Automated smoke; will delete.",
            "tags": ["smoke"],
            "categoryId": "24",
            "defaultLanguage": "ko",
        },
        "status": {"privacyStatus": "unlisted"},  # D-10 required
        "production_metadata": {
            "script_seed": "smoke_wave5",
            "assets_origin": "mock:fixture",
        },
        "funnel": {"pinned_comment": "smoke test"},
    }

    video_id = publish(
        youtube=youtube,
        plan=plan,
        video_path=Path("tests/phase07/fixtures/mock_shotstack.mp4"),
        thumbnail_path=Path("tests/phase07/fixtures/mock_thumbnail.png"),
        channel_id=_get_my_channel_id(youtube),
    )

    assert video_id
    # Wait for processing so delete succeeds reliably
    time.sleep(30)

    try:
        resp = youtube.videos().delete(id=video_id).execute()
    except Exception as exc:
        pytest.fail(
            f"SMOKE CLEANUP FAILED — manually delete at "
            f"https://studio.youtube.com/video/{video_id}/edit — {exc}"
        )


def _get_my_channel_id(youtube) -> str:
    resp = youtube.channels().list(part="id", mine=True).execute()
    return resp["items"][0]["id"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `oauth2client` library | `google-auth` + `google-auth-oauthlib` | 2019 (oauth2client deprecated) | 레거시 코드 금지 |
| `InstalledAppFlow.run_console()` | `InstalledAppFlow.run_local_server(port=0)` | 2022-10 (OOB flow deprecated by Google) | Browser-less CLI 환경에서는 manual paste 필요, Phase 8은 대표님 로컬 실행 → local_server OK |
| Custom `syntheticMedia` field | `status.containsSyntheticMedia` | 2024-10-30 YouTube Data API v3 revision | Phase 4 AGENT.md 필드 이름 mismatch 존재 — Pitfall 6 |
| `requests.post` to `/user/repos` with classic PAT | Fine-grained PAT + `X-GitHub-Api-Version` header | 2022-10 (fine-grained GA) | D-01 확정 |
| `pytz.timezone("Asia/Seoul")` | `zoneinfo.ZoneInfo("Asia/Seoul")` | Python 3.9 (2020) | stdlib 우선 |
| Comment pinning via Data API | **Not supported** — YouTube Studio UI만 | permanent since API v3 launch | D-09 이미 workaround 확정 |
| End-screen configuration via API | **Not supported** — YouTube Studio UI만 | permanent | D-09 description CTA 대체 확정 |

**Deprecated/outdated:**
- `from apiclient.discovery import build` — 구 모듈명. 현재는 `from googleapiclient.discovery import build`.
- `flow.run_console()` — deprecated 2022, removed later versions.
- `oauth2client.tools.run_flow` — 전체 라이브러리 deprecated.

## Open Questions

1. **naberal_harness v1.0.1 commit SHA 구체값**
   - What we know: CONTEXT specifics §"harness submodule 버전 고정" 에 "commit hash 확인 후 submodule add 시 해당 SHA로 checkout" 명시.
   - What's unclear: 실제 SHA (예: `a1b2c3d4...`) 아직 미확정. `git -C ../../harness rev-parse v1.0.1` 등으로 확인 필요.
   - Recommendation: Wave 1 Plan 실행 초두 task로 "harness 원격에서 v1.0.1 태그 SHA 조회" 명시.

2. **대표님 YouTube 채널 ID**
   - What we know: 기존 채널 존재 ("대표님의 기존 채널을 YPP 궤도에 올리는 스튜디오" — CLAUDE.md).
   - What's unclear: 실제 channel_id (UCxxxxxx 형식)가 CONTEXT에 미기록. `commentThreads.insert` 에 필수.
   - Recommendation: Wave 2 OAuth 성공 후 `youtube.channels().list(mine=True).execute()` 로 자동 조회 + `config/channel_info.json` 저장 (gitignored).

3. **Smoke test 업로드 timing**
   - What we know: D-10 "30초 대기 → videos.list → videos.delete".
   - What's unclear: 30초가 처리 완료 충분한지 YouTube 쪽에서 불명확. `processingStatus=succeeded` 보장 X.
   - Recommendation: Wave 5 테스트에서 `processingStatus in ('succeeded', 'processed')` 확인 + max 5분 polling, 실패 시 manual-delete URL 로깅.

4. **client_secret.json OAuth 2.0 consent screen "published" 상태**
   - What we know: Google Cloud OAuth 2.0 consent screen은 "Testing" vs "Published" 모드 존재.
   - What's unclear: Testing 모드면 refresh token 7일 만료 — 매주 재인증 필요. 단일 사용자라 testing 모드 유지 허용되나 재인증 번거로움.
   - Recommendation: 대표님 수동 단계에서 consent screen "Published" 로 전환(verification 과정 우회 가능 internal-use, 단일 사용자).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (이미 Phase 4~7에서 986/986 green) |
| Config file | pytest.ini 또는 pyproject.toml (Phase 5 기반) — Wave 0에서 확인 |
| Quick run command | `pytest tests/phase08/ -x -q` |
| Full suite command | `pytest tests/ -x -q` (Phase 4+5+6+7+8 회귀 포함, smoke 제외) |
| Smoke run command | `pytest tests/phase08/test_smoke_real_upload.py -v -m smoke --run-smoke` (opt-in) |
| Phase gate | `python .planning/phases/08-remote-publishing-production-metadata/phase08_acceptance.py` exit 0 |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PUB-01 | `status.containsSyntheticMedia=True` 하드코딩 + grep anchor | unit | `pytest tests/phase08/test_ai_disclosure_hardcoded.py -x` | ❌ Wave 0 |
| PUB-02 | `videos.insert` 호출 + selenium/webdriver 0 hits | unit+grep | `pytest tests/phase08/test_no_selenium.py -x` | ❌ Wave 0 |
| PUB-03 | 48h+ jitter + KST window 2종 guard | unit | `pytest tests/phase08/test_publish_lock.py tests/phase08/test_kst_window.py -x` | ❌ Wave 0 |
| PUB-04 | 4-field production_metadata HTML 주석 주입 | unit | `pytest tests/phase08/test_production_metadata.py -x` | ❌ Wave 0 |
| PUB-05 | `commentThreads.insert` 호출 + end-screen 경로 부재 | unit | `pytest tests/phase08/test_pinned_comment.py -x` | ❌ Wave 0 |
| REMOTE-01 | `POST /user/repos` 201 Created 또는 422 멱등 | integration (MockGitHub) | `pytest tests/phase08/test_github_repo_create.py -x` | ❌ Wave 0 |
| REMOTE-02 | `git push -u origin main` subprocess 성공 (no URL-embedded PAT) | integration | `pytest tests/phase08/test_github_push.py -x` | ❌ Wave 0 |
| REMOTE-03 | `git submodule add` + SHA checkout + `.gitmodules` 존재 | integration | `pytest tests/phase08/test_harness_submodule.py -x` | ❌ Wave 0 |

### Anchor Test Candidates (Phase 7의 "3 Corrections" 패턴 계승)

Phase 8은 **3 Anchor** 제안:

- **Anchor A: `containsSyntheticMedia` 공식 필드명 강제**
  - AST-based test: `scripts/publisher/youtube_uploader.py` 의 body["status"] 딕셔너리 리터럴에 `"containsSyntheticMedia": True` 존재 + `"containsSyntheticMedia": False` 부재 + `"syntheticMedia"` 커스텀 키 부재 (3 조건 AND).
  - Pitfall 6 방어.
  
- **Anchor B: End-screen API 경로 부재**
  - grep-based: `scripts/publisher/` 전체에서 `captions.insert` / `endScreen` / `end_screen.*upload` 0 hits (AST-based 확장 가능).
  - D-09 + Pitfall 7 방어.

- **Anchor C: Selenium/webdriver 0 hits + Hook 통합**
  - grep + subprocess: `scripts/publisher/` + `tests/phase08/` 전체에서 `selenium|webdriver|playwright` regex 0 hits. 추가로 `verify_hook_blocks.py` (Phase 5) 에 Phase 8 path 커버하는지 확인.
  - CLAUDE-06 + AF-8 방어.

### Blacklist Tokens (Phase 8 scope grep-block)

| Pattern | Reason | Test Location |
|---------|--------|---------------|
| `selenium` (case-insensitive) | AF-8 Selenium 영구 금지 | Anchor C + deprecated_patterns.json |
| `playwright` | AF-8 extended | Anchor C |
| `webdriver` | AF-8 extended | Anchor C |
| `skip_gates` | CLAUDE-04 | Hook 기존 enforcement |
| `TODO(next-session)` | CLAUDE-05 | Hook 기존 enforcement |
| `flow.run_console(` | 2022 deprecated OAuth flow | Anchor D (optional) |
| `oauth2client` | 2019 deprecated library | 의존성 grep |
| `pytz.timezone("Asia/Seoul")` | zoneinfo 우선 | 의존성 grep |

### Sampling Rate

- **Per task commit:** `pytest tests/phase08/ -x -q`
- **Per wave merge:** `pytest tests/ -x -q --ignore=tests/phase08/test_smoke_real_upload.py` (회귀 985/985+ Phase 8 테스트 전체)
- **Wave 5 smoke gate:** `pytest tests/phase08/test_smoke_real_upload.py -v -m smoke --run-smoke` (사용자 승인 후 1회)
- **Phase gate:** `phase08_acceptance.py` + `verify_hook_blocks.py` + 전체 full suite green

### Wave 0 Gaps

- [ ] `tests/phase08/__init__.py` — 패키지 마커 (기존 Phase 7 관례로 `__init__.py` 존재)
- [ ] `tests/phase08/conftest.py` — `tmp_path`, `mock_youtube`, `mock_github`, `clean_publish_lock` fixture
- [ ] `tests/phase08/mocks/__init__.py`
- [ ] `tests/phase08/mocks/youtube_mock.py` — D-3 `allow_fault_injection=False` default, `videos/thumbnails/commentThreads/channels` 메서드
- [ ] `tests/phase08/mocks/github_mock.py` — same pattern + `POST /user/repos` stub
- [ ] `tests/phase08/fixtures/` — `mock_video.mp4` (0-byte or Phase 7 mock_shotstack.mp4 재사용), `mock_thumbnail.png`
- [ ] `.planning/phases/08-remote-publishing-production-metadata/phase08_acceptance.py` — SC 1-6 aggregator (Wave 7 landing)
- [ ] `.planning/phases/08-remote-publishing-production-metadata/08-VALIDATION.md` — Wave 0 checkbox scaffold
- [ ] `.planning/phases/08-remote-publishing-production-metadata/08-TRACEABILITY.md` — 8-REQ matrix
- [ ] `.gitignore` 업데이트 — `config/youtube_token.json` + `.planning/publish_lock.json` 추가 (line 3-4 이미 `token.json` / `client_secret.json` 존재 확인됨)

## Pitfalls to Avoid — Additional Project-Specific

### Pitfall 11: Phase 7 986 Test Regression Break
Phase 8 Wave별 `pytest tests/` 전체 실행 필수. Wave 1 subprocess가 `git branch -m master main` 하면 Phase 7 테스트 중 branch-name 의존 테스트 존재 시 break 가능 (확률 낮으나 검증).

### Pitfall 12: `harness/` Submodule Clone Requires PAT for naberal_harness
naberal_harness 레포가 Private이면 submodule clone에 동일 PAT의 `contents:read` scope 필요. Fine-grained PAT은 **레포별 scope** 이므로 PAT 발급 시 `shorts_studio` + `naberal_harness` 둘 다 선택 필수. 대표님 수동 단계 문서화.

### Pitfall 13: `publish_lock.json` gitignore 누락 시 이력 누출
`.planning/publish_lock.json` 은 업로드 일시 기록 → 채널 발행 이력 유추 가능. `.gitignore` 에 반드시 `.planning/publish_lock.json` 추가.

## Plan Wave Decomposition (recommended)

Planner가 실제 PLAN.md 생성 시 base. CONTEXT D-11 "Wave 5 smoke gate" 유지.

### Wave 0: FOUNDATION (Plan 08-01)
- `tests/phase08/` scaffold (__init__ + conftest + 2 mocks + 2 fixtures)
- `.gitignore` 업데이트 (publish_lock.json + youtube_token.json 이미 있는지 확인)
- `08-VALIDATION.md` + `08-TRACEABILITY.md` scaffold
- `phase08_acceptance.py` stub (exit 1 gracefully)
- Pytest verify: `pytest tests/phase08/ -q` 1-2 smoke tests green + Phase 7 986/986 regression preserved
- **Blocking for 1~5**: `GITHUB_TOKEN` 발급 + `client_secret.json` 준비는 Wave 1/2 시작 전

### Wave 1: REMOTE (Plan 08-02) — parallel-safe with Wave 2
- `scripts/publisher/__init__.py`
- `scripts/publisher/github_remote.py` (`create_private_repo` + `push_to_remote` + `add_harness_submodule`)
- `tests/phase08/test_github_repo_create.py` (MockGitHub 422 멱등)
- `tests/phase08/test_github_push.py` (subprocess mock)
- `tests/phase08/test_harness_submodule.py` (fake harness URL + commit checkout)
- **Manual step** (대표님): `git branch -m master main` → `python -m scripts.publisher.github_remote create` → `git push -u origin main` → submodule add
- REMOTE-01/02/03 checkbox flip

### Wave 2: OAUTH (Plan 08-03) — parallel-safe with Wave 1
- `scripts/publisher/oauth.py` (`get_credentials` + SCOPES + TOKEN_PATH)
- `tests/phase08/test_oauth_load_refresh.py` (mock Credentials.from_authorized_user_file + Request().refresh)
- Manual step (대표님 1회): `python -m scripts.publisher.oauth --first-run` → 브라우저 OAuth consent → `config/youtube_token.json` 저장
- Verify: token.json 존재 + refresh 작동

### Wave 3: LOCK + WINDOW + DISCLOSURE (Plan 08-04)
- `scripts/publisher/publish_lock.py` (48h+ jitter, atomic os.replace)
- `scripts/publisher/kst_window.py` (zoneinfo 평일/주말)
- `scripts/publisher/_disclosure.py` (hardcoded `containsSyntheticMedia=True`)
- `tests/phase08/test_publish_lock.py` (first-upload + elapsed<48h FAIL + elapsed>=48h+jitter PASS + atomic write)
- `tests/phase08/test_kst_window.py` (boundary: Mon 19:59 FAIL, 20:00 PASS, 22:59 PASS, 23:00 FAIL; Sat 11:59/12:00/14:59/15:00)
- `tests/phase08/test_ai_disclosure_hardcoded.py` (Anchor A: containsSyntheticMedia True + no False + no syntheticMedia key)
- PUB-01/03 partial

### Wave 4: METADATA + FUNNEL + UPLOADER (Plan 08-05)
- `scripts/publisher/production_metadata.py` (4-field + checksum + description 주입)
- `scripts/publisher/youtube_uploader.py` (publish orchestration + resumable_upload + build_insert_body + thumbnails.set + commentThreads.insert)
- `tests/phase08/test_production_metadata.py` (4-field 필수 + sha256 스트리밍 + description HTML 주석 regex match)
- `tests/phase08/test_youtube_uploader_mock.py` (E2E with MockYouTube — Phase 7 style)
- `tests/phase08/test_pinned_comment.py` (MockYouTube.commentThreads.insert 호출 확인)
- `tests/phase08/test_no_selenium_no_end_screen.py` (Anchor B + C grep)
- PUB-02/04/05 완성

### Wave 5: SMOKE-GATE (Plan 08-06) — **USER APPROVAL REQUIRED**
- `tests/phase08/test_smoke_real_upload.py` (opt-in `-m smoke --run-smoke`)
- `pytest.ini` 에 `markers = smoke: real YouTube upload, requires manual approval` 추가
- Plan 헤더에 `SMOKE-GATE` 마커: orchestrator가 plan 실행 직전 "대표님 승인 필요 — 실 YouTube unlisted 업로드 + delete cleanup, video_id 로깅" 출력 후 정지
- 대표님 "진행" 확인 후: `pytest tests/phase08/test_smoke_real_upload.py -v -m smoke --run-smoke` 1회
- 실패 시: video_id 로깅 → manual delete URL 안내 → plan FAIL (Wave 6 진행 금지)
- 성공 시: VALIDATION.md row flip + Wave 6 unblock

### Wave 6: E2E + REGRESSION (Plan 08-07)
- `tests/phase08/test_e2e_happy_path_mock.py` (Phase 4 publisher JSON → youtube_uploader → MockYouTube 완전 경로)
- `tests/phase08/test_regression_phase7.py` (Phase 7 986/986 회귀)
- Hook enforcement Phase 8 path 추가: `verify_hook_blocks.py` 확장
- deprecated_patterns.json 확장 (optional): `flow.run_console(` + `oauth2client` 추가

### Wave 7: PHASE GATE (Plan 08-08)
- `phase08_acceptance.py` SC 1-6 aggregator (GitHub mirror + submodule + AI disclosure grep + 48h lock + production_metadata regex + pinned comment smoke confirmation)
- `08-TRACEABILITY.md` 8-REQ × source × test × SC matrix
- `08-VALIDATION.md` frontmatter flip: `status=complete`, `nyquist_compliant=true`, `wave_0_complete=true`, `completed=2026-04-XX`
- 6 Sign-Off checkboxes [x]
- `verify-work 8` agent audit
- Phase 9 unblock

## Sources

### Primary (HIGH confidence)
- **YouTube Data API v3 `videos.insert`** — https://developers.google.com/youtube/v3/docs/videos/insert — status fields list (privacyStatus / selfDeclaredMadeForKids / containsSyntheticMedia / license / embeddable / publicStatsViewable), quota 1600 units, 256GB max. Referenced 2026-04-19.
- **YouTube Data API v3 `commentThreads.insert`** — https://developers.google.com/youtube/v3/docs/commentThreads/insert — body shape {snippet: {channelId, videoId, topLevelComment.snippet.textOriginal}}, scope youtube.force-ssl, quota 50.
- **YouTube Data API v3 `thumbnails.set`** — https://developers.google.com/youtube/v3/docs/thumbnails/set — MediaFileUpload(mimetype=image/png|image/jpeg), 2MB max, quota 50.
- **YouTube API samples upload_video.py** — https://github.com/youtube/api-samples/blob/master/python/upload_video.py — canonical resumable_upload retry loop + HttpError status codes.
- **Google Auth OAuthlib InstalledAppFlow** — https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html — `run_local_server(port=0)` + `creds.to_json()` persistence.
- **Google API Python Client OAuth docs** — https://github.com/googleapis/google-api-python-client/blob/main/docs/oauth-installed.md — InstalledAppFlow canonical pattern.
- **YouTube Data API revision history** — https://developers.google.com/youtube/v3/revision_history — 2024-10-30 `containsSyntheticMedia` 필드 추가 확인.
- **GitHub REST API `POST /user/repos`** — https://docs.github.com/en/rest/repos/repos — private:true 옵션.
- **GitHub fine-grained PAT permissions** — https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens — Contents:Write + Administration:Write 필요.
- **Git submodule documentation** — https://git-scm.com/docs/git-submodule — `add` + commit pinning via checkout.
- **Python zoneinfo (3.9+)** — stdlib https://docs.python.org/3/library/zoneinfo.html — `ZoneInfo("Asia/Seoul")`.
- **Phase 7 STATE + VERIFICATION** — `.planning/phases/07-integration-test/07-VERIFICATION.md` + STATE.md (내부) — 986/986 tests, 3 Corrections anchored, MockShotstack D-3 pattern.

### Secondary (MEDIUM confidence)
- **Medium article "From Zero to First Upload 2025"** — https://medium.com/@dorangao/from-zero-to-first-upload-a-from-scratch-guide-to-publishing-videos-to-youtube-via-api-2025-73251a9324bd — Shorts 60s + 9:16 + #Shorts hashtag convention (cross-verified with official upload guide).
- **Phyllo quota guide 2026** — https://www.getphyllo.com/post/youtube-api-limits-how-to-calculate-api-usage-cost-and-fix-exceeded-api-quota — 10,000 unit 기본 quota + 1,600 업로드 단위.
- **GitHub API versioning header** — docs.github.com의 `X-GitHub-Api-Version: 2022-11-28` 관례.

### Tertiary (LOW confidence — FLAGGED)
- **30초 processing wait** (D-10 specifics) — YouTube 공식 문서 없음. empirical rule of thumb. Wave 5 에서 polling loop로 보강 권장.
- **Refresh token 7일 만료 (Testing consent screen)** — Google 정책 문서 다수 언급하나 공식 페이지 구체 명시 어려움. "Published" consent screen 전환 권장.

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — Google/Git 공식 docs 직접 확인 + Phase 7 pattern 레퍼런스.
- Architecture: HIGH — CONTEXT D-01..D-11 완전 locked + Phase 5/7 checkpointer/circuit_breaker 재사용.
- Pitfalls: MEDIUM-HIGH — 10 pitfalls 중 8개는 공식 docs + 2개는 커뮤니티 cross-verification.
- End-screen 미지원 확정: MEDIUM — 공식 docs에 "supported" 명시 없음 + 커뮤니티 consensus + Phase 4 AGENT.md 자체 회색지대.

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30일 — YouTube Data API v3는 2024-10-30 이후 안정, GitHub fine-grained PAT도 2022+ 안정). 단 Google OAuth 정책 변경이 잦으므로 Wave 2 실행 직전 `developers.google.com/youtube/v3/revision_history` 재확인 권장.

## RESEARCH COMPLETE
