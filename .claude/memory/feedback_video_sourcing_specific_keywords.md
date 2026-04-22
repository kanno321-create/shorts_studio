---
name: feedback_video_sourcing_specific_keywords
description: 영상 수급 query 는 **구체적 고유명사·사건명** 써야 함. 일반 "police interrogation night" 같은 범용 query 는 누와르 stock video 만 반환. Ryan Waller / Dateline / Carver / Heather Quan / ABC 20/20 급 query 필수.
type: feedback
imprinted_session: 34
imprinted_date: 2026-04-23
source_refs:
  - output/ryan-waller/sources/real/manifest_v3.json (v3 — Wikimedia PDF + 일반 Noir Stock 만)
  - scripts/experiments/source_ryan_waller_footage.py SECTION_QUERIES (대부분 일반 query)
failure_mapping:
  - FAIL-v3-자료_엉뚱: 대표님 "범인의 얼굴, 사건현장, 피해자, 증거품 등등 가져올게 너무많은데 이상한것만붙혀놔서 이해안됨"
---

# feedback: 영상 수급 query = 구체 고유명사 기반

## 규칙

**YouTube/웹 검색 query 는 사건·인물 **고유명사** 위주.** 범용 영어 keyword ("police interrogation", "crime scene night") 는 무관한 누와르 stock video 만 반환. 실 사건 관련 자료 (뉴스 다큐, mugshot, CCTV, 피해자 사진) 는 고유명사 query 로만 접근 가능.

### 위반 예시 (v3)

```python
SECTION_QUERIES = {
    "hook": [
        "Ryan Waller Phoenix 2006 interrogation",     # OK
        "Ryan Waller wrongful arrest Phoenix Arizona", # OK
        "Phoenix police suburban neighborhood night",  # ❌ 너무 일반적 — Noir stock 반환
    ],
    "body_dalton": [
        "Paul Dalton Phoenix detective interrogation",                  # OK
        "police interrogation room fluorescent light wide shot",        # ❌ 일반
        "detective closeup interrogation moody lighting",               # ❌ 일반 = Noir stock
    ],
    "watson_q1": [
        "police interrogation suspect chair detective",                 # ❌ 완전 일반
        "취조실 CCTV 형사",                                             # ❌ 한국어 generic
    ],
}
```

결과: Wikimedia 에서 "Gunsight Pass oil book" PDF 반환, YouTube 에서 "Noir Detective Video" 일반 stock 반환 — 전부 사건 무관.

### 올바른 query 전략 (v3.1)

**Tier 1 (가장 구체)**: 사건명 + 인물명 + 매체
- `"Ryan Waller" Dateline`
- `"Ryan Waller" "ABC 20/20"`
- `"Richie Carver" mugshot Phoenix`
- `"Heather Quan" Phoenix 2006`
- `"Phoenix Police Department" "Paul Dalton"`

**Tier 2 (사건 상세 + 고유어)**: 특이 사실 + 위치/시점
- `"Waller case" Phoenix traumatic brain injury`
- `"Paul Dalton" wrongful arrest confession`
- `Phoenix 2006 December Christmas murder double homicide`

**Tier 3 (사건 배경 일반)**: 범용 stock (최후 수단만)
- `Phoenix suburban house Christmas lights 2006` (시대상 ambient)
- `US interrogation room 2000s` (시대상)

### 검색 대상 source 확장

v3 는 YouTube + Wikimedia 2 소스만. v3.1 은:
| source | 강점 | Ryan Waller 적합도 |
|--------|------|-------------------|
| YouTube | Dateline/ABC/CBS/NBC 뉴스 다큐 업로드 많음 | ⭐⭐⭐⭐⭐ |
| Wikimedia Commons | PD 역사/풍경 사진 | ⭐ (2006 미국 사건 거의 없음) |
| news-archive (wayback, IA) | 2006 당시 보도 기사 | ⭐⭐⭐ |
| US court records (PACER public) | 법정 문서 이미지 | ⭐⭐ |

v3.1 은 **YouTube Tier 1 query 전수 시도** + Wikimedia 는 ambient 용도로만.

### query 품질 채점 기준

- ⭐⭐⭐ : 사건 고유명사 2개+ 포함 (사건명 + 인물명 or 매체)
- ⭐⭐ : 고유명사 1개 + 사건 상세
- ⭐ : 일반 키워드만 (Noir stock 반환 위험)

section_queries 는 평균 ⭐⭐ 이상 유지.

## Why

세션 #34 v3 대표님 판정 원문:
> "범인의 얼굴이라던가, 사건현장 ,피해자라던가, 사건현장 영상 및 이미지, 증거품 등등 가져올게 너무많은데 이상한것만붙혀놔서 이해안됨"

실제로 Ryan Waller 사건은 미 주류 미디어 (Dateline NBC, ABC 20/20, CBS 48 Hours 등) 에서 대대적으로 다뤘고 YouTube 에 공개 뉴스 영상 많음. Richie Carver / Larry Carver 의 mugshot 도 법정 공개자료. Heather Quan 사진도 언론 공개. 내가 query 를 너무 generic 하게 만들어서 이를 놓침.

## How to apply

- **source_*_footage.py 작성 시**:
  - `SECTION_QUERIES` 는 Tier 1 우선 (사건명+인물명+매체)
  - Tier 2 보조 (범행 유형 + 위치 + 연도)
  - Tier 3 는 마지막 fallback (일반 ambient)
- **rank_relevance.py 측**:
  - 고유명사 매칭 가중치 ↑ (`Waller`, `Carver`, `Quan`, `Dalton` 매치 시 score +0.30)
- **ins-license / ins-mosaic 측 검증**:
  - manifest_v3.json 의 picks 에서 title + description 에 사건명 / 인물명 매치 ≥ 50% 확인

## 검증

```bash
python -c "
import json
m = json.load(open('output/<episode>/sources/real/manifest_v3_1.json'))
PROPER_NOUNS = ['Waller','Carver','Quan','Dalton','Phoenix','Dateline','20/20','48 Hours']
total_picks = 0
matched = 0
for s in m['sections']:
    for p in s.get('picks', []):
        total_picks += 1
        corpus = (p.get('title','') + ' ' + p.get('channel','')).lower()
        if any(n.lower() in corpus for n in PROPER_NOUNS):
            matched += 1
ratio = matched / max(1, total_picks)
print(f'{matched}/{total_picks} picks match proper nouns ({ratio:.0%})')
assert ratio >= 0.4, f'too few proper-noun-matched picks: {ratio:.0%}'
"
```

## Cross-reference

- `feedback_multi_source_video_search_required` (상위 규칙)
- `feedback_script_video_sync_via_visual_directing` (query source = visual_directing)
- `project_video_sourcing_skill_v1` (skill 확장 로드맵)
- 세션 #34 v3 대표님 직접 판정
