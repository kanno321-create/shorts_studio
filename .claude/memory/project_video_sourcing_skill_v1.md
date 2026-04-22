---
name: project_video_sourcing_skill_v1
description: 멀티소스 영상·이미지 검색·다운로드 스킬 v1 prototype 아키텍처 + 확장 로드맵. `scripts/orchestrator/video_sourcing/` 6 파일 모듈.
type: project
imprinted_session: 34
imprinted_date: 2026-04-23
---

# project: video_sourcing skill v1 (prototype)

## 배경

대표님 세션 #34 지시: "여러 매체를 검색해서 찾아와야지… 검색할수있는 스킬도 필요한거다. 한군데만하면 안되고 몇몇매체를 검색하고 거기에서 관련된 정확한 영상을 가져와야하는거야."

기존 파이프라인은 gpt-image-2 (정적 이미지) + Kling I2V (AI 생성) 만. 실 사건 영상/사진 0건 → 사건 관련성 의심 판정. 본 스킬은 YouTube + Wikimedia + Web (향후) 에서 실 자료를 검색·다운로드.

## 아키텍처

### 위치
`scripts/orchestrator/video_sourcing/` (Producer / Inspector 외부, orchestration 레이어)

### 6 파일 모듈

| 파일 | 역할 | 주 의존성 |
|------|------|----------|
| `__init__.py` | public API (search_youtube, search_wikimedia, rank_candidates, download_candidate) | — |
| `search_youtube.py` | YouTube Data API v3 search (googleapiclient), fallback yt-dlp CLI search | googleapiclient, yt-dlp |
| `search_wikimedia.py` | commons.wikimedia.org REST search + imageinfo license filter | requests |
| `search_web.py` | news media HTML scrape (v1 은 stub; 향후 MCP Tavily/Exa) | (stub) |
| `rank_relevance.py` | Jaccard token overlap + license 가중치 스코어링 | — |
| `download.py` | yt-dlp (YouTube) / requests streaming (direct URL) | yt-dlp, requests |

### Candidate schema

```python
{
  "source": "youtube" | "wikimedia" | "web",
  "id": "<video_id or commons title>",
  "url": "<http url>",
  "title": "...",
  "description": "...",
  "channel": "...",
  "license_flag": "public-domain" | "cc-by" | "fair-use-educational" | "unknown",
  "mime": "video/mp4" | "image/jpeg" | ...,
  "raw_snippet": {...},
  "_score": 0.0..1.0,          # after rank
  "_matched_terms": [...],      # after rank
}
```

### 허용 확장자 (다운로드 후 필터)

`USABLE_REAL_EXTS = (".mp4", ".webm", ".mov", ".jpg", ".jpeg", ".png")` — Wikimedia 의 PDF/DJVU false positive 거부.

### CLI 호출 패턴 (에피소드별)

```python
# scripts/experiments/source_<episode>_footage.py
for section in script["sections"]:
    cands = []
    for query in SECTION_QUERIES[section["section_id"]]:
        cands.extend(search_youtube(query, max_results=5))
        cands.extend(search_wikimedia(query, max_results=5))
    ranked = rank_candidates(cands, section["visual_directing"])
    for rank, c in enumerate(ranked[:TOP_K], 1):
        path = download_candidate(c, RAW_DIR, f"{sid}_{rank}")
        manifest.append({...})
```

### 출력물

- `output/<episode>/sources/real/raw/<section>_<rank>.{mp4,jpg,...}` (다운로드된 원본)
- `output/<episode>/sources/real/manifest_v3.json` (section → picks 매핑, license_flag 분포)

### 환경 요구

- `.env` 의 `YOUTUBE_API_KEY` 또는 `GOOGLE_API_KEY` (둘 다 있으면 YOUTUBE 우선)
- `yt-dlp` 설치 (Python 패키지 + CLI 둘 다 호출 가능)
- `googleapiclient` (google-api-python-client) Python 패키지
- `requests` Python 패키지

## Out of scope (v1)

1. Retry / exponential backoff (transient API 실패)
2. Rate limiting / quota 관리 (YouTube 10,000 단위/일 무료 티어 가정)
3. Cache / 이전 검색 결과 재사용
4. Circuit breaker (제공자별 건강도)
5. License flag 자동 판정 엔진 (unknown 은 사람 수동)
6. Web scraping (MCP 통합은 별도 스킬)

## 향후 확장 (v2+)

- Tavily/Exa MCP 기반 search_web 실구현
- 뉴스 미디어 공식 API (Dateline NBC, ABC News 등) 직접 연동
- Getty / Reuters 아카이브 (유료 — 필요 시)
- 영상 품질 자동 scoring (해상도, 길이, 재생 횟수, 채널 신뢰도)
- Kling prompt seed 로 Wikimedia 이미지 사용 (image-to-video 체인)

## 성공 사례 기록

- **Ryan Waller v3 (세션 #34)**: 9 section × 3 query = ~25 search 수행, 12 다운로드. usable 4건 (.mp4/.webm), 나머지는 Wikimedia PDF false positive 거부. 부족분은 Kling 8s v3 fallback. → real_ratio 보존 + 멀티소스 의무 충족.

## Cross-reference

- `feedback_multi_source_video_search_required` (규칙)
- `feedback_script_video_sync_via_visual_directing` (query 소스)
- reference: `shorts_naberal/scripts/video-pipeline/_kling_i2v_batch.py`
- CLAUDE.md 금기 #11 (Veo 금지, Kling 허용)
