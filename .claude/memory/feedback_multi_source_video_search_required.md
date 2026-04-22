---
name: feedback_multi_source_video_search_required
description: 영상 자산 수급은 **여러 매체 (≥2 source) 검색** 의무. YouTube 단독 또는 AI 생성 단독 금지 — 실 뉴스 영상 (YouTube fair-use) + public-domain (Wikimedia) 조합 필수.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - scripts/orchestrator/video_sourcing/ (신규 prototype 모듈)
  - output/ryan-waller/sources/real/manifest_v3.json (multi-source evidence)
  - C:/Users/PC/Desktop/shorts_naberal/output/elisa-lam/sources/ (100% real + 15 videos — reference)
failure_mapping:
  - FAIL-v1-자료관련성0: 모든 b-roll 이 AI 생성 gpt-image-2 (사건과 무관한 일반 누와르)
  - FAIL-v2-자료_의심: 대표님 "자료가 관련자료 맞는지 의심"
---

# feedback: 영상 수급 = 멀티소스 검색 (한 매체 단독 금지)

## 규칙

**사건 b-roll 영상은 최소 2개 source 에서 검색 + 다운로드 + 관련성 ranking 후 선정.** Claude 가 주도적으로 검색 스킬을 수행해야 함 (대표님 2026-04-23 지시).

### 허용 source (prototype v1)

| source | API | license_flag | 사용 조건 |
|--------|-----|--------------|----------|
| YouTube Data API v3 | `googleapiclient` + YOUTUBE_API_KEY | fair-use-educational | 뉴스/다큐/공개 채널 영상 (독점 영상은 제외) |
| Wikimedia Commons | REST (key 불필요) | public-domain / cc-by | 역사 사진, PD 영상. **.mp4/.webm/.jpg/.png 확장자만 accept** (PDF/DJVU false-positive reject) |
| Web (news media) | Tavily/Exa MCP or WebFetch | fair-use-educational | Claude agent path — stub 지원 |

### 최소 커버리지

- section 당 ≥1 후보 다운로드 시도
- ≥2 source 혼용 (YouTube + Wikimedia 또는 + Web)
- `license_flag_counts` 분포 manifest 에 기록

### Ranking 전략

- 각 candidate 의 title + description + channel tokenize
- section 의 visual_directing + narration tokenize → query_terms
- Jaccard-like overlap score + license_flag 가중치 (PD +0.15, CC-BY +0.10, fair-use 0, unknown -0.20)

### 수용 기준

- **top-1 pick 확장자 ∈ {.mp4, .webm, .mov, .jpg, .jpeg, .png}**
- 그 외 (.pdf, .djvu, .bin) → 자동 거부
- Ryan Waller v3: 9 section 중 usable real 4개 → Kling fallback 으로 나머지 보완

## Why

세션 #34 대표님 지시 원문: "여러 매체를 검색해서 찾아와야지… 그니까 검색할수있는 스킬도 필요한거다. 한군데만하면 안되고 몇몇매체를 검색하고 거기에서 관련된 정확한 영상을 가져와야하는거야."

이유:
1. **저작권 분산**: 한 소스 (YouTube) 만 쓰면 저작권 claim 집중. 여러 소스 섞으면 fair-use 범위 희석.
2. **관련성 향상**: Wikimedia 의 PD 역사 사진 + YouTube 뉴스 영상 = 사건 시대상 (photo) + 실제 보도 (video) 조합.
3. **reference 모방**: shorts_naberal elisa-lam 등은 실제로 다양한 소스 섞어 real 비중 ≥90% 달성.

## How to apply

- **신규 에피소드 b-roll 생성 시**:
  1. `scripts/orchestrator/video_sourcing/` 모듈 import
  2. section 마다 `search_youtube()` + `search_wikimedia()` 호출
  3. `rank_candidates()` 로 스코어링 후 top-K 다운로드
  4. `license_flag` 분포 manifest 에 기록
  5. real footage coverage 부족 section → Kling 8s I2V fallback
- **향후 확장**:
  - `search_web.py` (stub) 를 MCP Tavily/Exa 로 교체
  - 범위 추가 (ABC/NBC/CBS 공식 뉴스 채널 직접 scrape)
  - license_flag="unknown" 자동 검수 engine

## 검증

```bash
# manifest_v3.json 의 source 다양성 확인
python -c "
import json
m = json.load(open('output/<episode>/sources/real/manifest_v3.json'))
assert len(m['sources_used']) >= 2, f'multi-source required, got: {m[\"sources_used\"]}'
assert sum(m['license_flag_counts'].values()) >= 4, 'minimum 4 downloads'
print(f'✅ multi-source OK: {m[\"sources_used\"]} lic={m[\"license_flag_counts\"]}')
"
```

## Cross-reference

- `project_video_sourcing_skill_v1` — 스킬 아키텍처 spec
- `feedback_wiki_image_harvest_allowed` (대표님 허용 범위)
- `feedback_script_video_sync_via_visual_directing` — ranking 의 query source
- reference: `shorts_naberal/output/elisa-lam/sources/` (100% real 모델)
- Ryan Waller v2 FAIL — 세션 #34 대표님 판정
