---
name: shorts-safety
description: Safety detection for YouTube Shorts content. Identifies political content, real name mentions, and defamation risk under Korean law.
user-invocable: false
---

# Shorts Safety Detection

YouTube Shorts 콘텐츠의 안전성을 평가한다. 정치 콘텐츠, 실명 언급, 한국 형법 기반 명예훼손 위험을 감지한다.

## Layer 1: Keyword Scan

키워드 기반 1차 필터링. 빠르고 광범위한 탐지를 수행한다.

### 절차
1. 이 스킬 디렉토리의 `references/political-keywords.json` 파일을 로드한다
2. 대본의 모든 narration 텍스트를 하나로 연결한다
3. 연결된 텍스트를 키워드 리스트와 대조한다
4. 매치된 키워드를 `keyword_matches` 배열에 기록한다

### 검사 카테고리
- `parties`: 정당명
- `political_figures`: 정치인 직위/호칭
- `political_events`: 정치적 사건
- `political_terms`: 정치 용어 (진영)
- `institutions_political_context`: 정치적 맥락의 기관
- `sensitive_topics`: 민감 주제

### 키워드 매치의 의미
- 키워드 매치가 있다고 자동으로 정치 콘텐츠로 판별하지 않는다
- 키워드 매치는 Layer 2 AI 문맥 판단을 트리거한다
- 키워드 매치가 없더라도 Layer 2는 반드시 수행한다

## Layer 2: AI Contextual Judgment

AI 기반 2차 판단. 문맥을 고려한 정밀 분석을 수행한다.

키워드 매치 여부와 무관하게 대본 전체를 아래 3가지 차원에서 평가한다.

### 1. 정치 콘텐츠 판별 (Political Content Check)
이 대본이 정치적 입장을 취하거나, 정치인을 정치적 맥락에서 다루거나, 정치적으로 분열적인 주제에 관여하는가?

**판별 기준:**
- "국회"를 건축 맥락에서 언급하는 것은 정치 콘텐츠가 아니다
- "국회 법안 통과"를 논하는 것은 정치 콘텐츠이다
- 핵심은 단어 자체가 아닌 문맥과 의도이다

### 2. 실명 감지 (Real Name Detection)
대본에 실제 살아있는 인물의 이름이 언급되는가?

**감지 규칙:**
- 실명이 감지되면 각 이름을 목록으로 나열한다
- 공인이 사실적/비정치적 맥락에서 언급된 경우에도 플래그를 설정한다
- 사용자 검토를 위해 반드시 플래그를 설정한다

### 3. 명예훼손 위험 평가 (Defamation Risk Assessment)
대한민국 형법 제307조 기준의 명예훼손 위험 평가.

**법률 근거:**
- **형법 제307조 제1항**: 공연히 사실을 적시하여 타인의 명예를 훼손한 자 = 2년 이하 징역 또는 500만원 이하 벌금
- **형법 제307조 제2항**: 공연히 허위의 사실을 적시하여 타인의 명예를 훼손한 자 = 5년 이하 징역, 10년 이하의 자격정지 또는 1천만원 이하 벌금
- **형법 제310조 면책**: 진실한 사실로서 오로지 공공의 이익에 관한 경우에는 처벌하지 않는다

**평가 규칙:**
- 특정 인물의 명예를 훼손할 수 있는 어떤 진술이든 플래그를 설정한다
- 사실 여부와 관계없이 (제307조 제1항: 사실 적시도 명예훼손 성립)
- 제310조 면책 해당 여부 판단은 AI가 하지 않는다 -- 사용자가 판단한다

## Decision Rules

안전 평가 결과에 따른 처리 규칙.

| 플래그 | 조치 |
|--------|------|
| `is_political: true` | `auto_publish_blocked: true`, 사용자 명시적 승인 필요 |
| `has_real_names: true` | 경고 표시, 사용자 판단 |
| `defamation_risk: true` | 강력 경고 표시, 사용자 판단 |
| **어떤 플래그든 존재** | `auto_publish_blocked: true` |

### 핵심 원칙
`AI NEVER auto-removes or auto-modifies content based on safety flags`

- AI는 콘텐츠를 자동으로 제거하거나 수정하지 않는다
- AI는 위험을 감지하고 경고할 뿐이다
- 콘텐츠의 수정/삭제/게시 결정은 사용자가 한다
- 안전 플래그는 정보 제공 목적이며, 자동 검열이 아니다

## Output Format

metadata.json의 safety_check 섹션에 결과를 기록한다.

```json
{
  "safety_check": {
    "status": "completed",
    "is_political": true,
    "keyword_matches": ["matched keyword 1", "matched keyword 2"],
    "context_judgment": "Brief explanation of why content is/isn't political",
    "has_real_names": true,
    "real_names_found": ["Name 1", "Name 2"],
    "defamation_risk": true,
    "defamation_details": "Brief explanation if defamation risk exists, null otherwise",
    "auto_publish_blocked": true,
    "flags": ["POLITICAL", "REAL_NAMES", "DEFAMATION_RISK"]
  }
}
```

### 필드 규칙
- `status`: 항상 "completed" (평가 완료 시)
- `is_political`: boolean -- Layer 2 판단 결과
- `keyword_matches`: Layer 1에서 매치된 키워드 배열 (매치 없으면 빈 배열)
- `context_judgment`: AI의 정치 콘텐츠 판단 이유 (1-2문장)
- `has_real_names`: boolean -- 실명 감지 여부
- `real_names_found`: 감지된 실명 배열 (없으면 빈 배열)
- `defamation_risk`: boolean -- 명예훼손 위험 여부
- `defamation_details`: 명예훼손 위험 설명 (위험 없으면 null)
- `auto_publish_blocked`: boolean -- 어떤 플래그든 true면 true
- `flags`: 해당하는 플래그만 포함 ("POLITICAL", "REAL_NAMES", "DEFAMATION_RISK"). 이슈 없으면 빈 배열

## YouTube Policy Compliance

유튜브 "비정상 콘텐츠" 정책 준수 사항 (SAFE-01).

### 요구사항
- 모든 쇼츠는 게시 전 사용자 검토(승인 게이트)를 거쳐야 한다
- 대본 템플릿 변형: 대본이 서로 복사본이 되어서는 안 된다
- 이 요구사항은 디렉터 스킬의 승인 게이트에서 강제한다 (safety 스킬 자체에서는 강제하지 않음)

### Phase 1 범위
- 텍스트 파이프라인만 해당 -- 영상/오디오 정책은 해당 Phase에서 처리

## Stock Media Licensing Note

스톡 미디어 라이선스 요구사항 (SAFE-03).

### 현재 상태
- Phase 1은 텍스트 파이프라인 전용 -- 미디어 없음

### 향후 요구사항 (Phase 3)
- 모든 스톡 영상, 이미지, 음악, 폰트는 검증된 상업적 사용 라이선스를 보유해야 한다
- 이 요구사항은 영상 조립 Phase에서 강제한다

## Credit Monitoring Note

TTS 크레딧 모니터링 요구사항 (SAFE-04).

### 현재 상태
- Phase 1은 텍스트 파이프라인 전용 -- TTS 없음

### 향후 요구사항 (Phase 2)
- ElevenLabs 크레딧 사용량을 모니터링해야 한다
- 크레딧이 부족할 때 EdgeTTS로 자동 전환하는 기능을 구현해야 한다
