# AI 영상 생성 프롬프트 가이드 (Veo 3.1 Lite / Kling / Wan)

영상수집 에이전트가 AI 영상 프롬프트를 작성할 때 반드시 참조.
**모델 우선순위**: Veo 3.1 Lite → (리미트 시) Veo 3.0 Fast → Kling 3.0 → Wan 2.5

---

## 프롬프트 공식 (필수 5요소)

```
[Camera shot+angle+movement] + [Subject 상세] + [Action] + [Setting+time+lighting] + [Style reference]
```

**하나라도 빠지면 모델이 추측 → 품질 하락. 모든 요소를 반드시 포함.**
**최적 길이**: 75-175 단어 (75 미만 = 모델이 너무 추측, 175 초과 = 지시 충돌)

---

## 카메라 용어 마스터 목록

### 샷 타입

| 용어 | 용도 | AI 모델 작동 팁 |
|------|------|----------------|
| Extreme close-up (ECU) | 눈, 손, 물체 디테일 | 단일 물체에 집중할 때 |
| Close-up (CU) | 얼굴, 디테일, 감정 | 표정/감정 강조 |
| Medium shot (MS) | 인물 상반신, 대화 | 가장 범용적 |
| Wide shot (WS) | 전체 상황, 공간감 | 배경 포함 상황 설명 |
| Establishing shot | 장소 전체 소개 | 첫 씬에 적합 |
| POV shot | 시청자/인물 시점 | "PoV"로 축약, 얼굴 묘사 최소화 |
| Over-the-shoulder | 대화 장면 | 두 인물 간 대화 |

### 카메라 움직임

| 용어 | 효과 | 적합한 장면 | AI 팁 |
|------|------|-----------|------|
| Static / Locked shot | 안정, 다큐 느낌 | 인터뷰, 증거물 | "Locked shot"이 더 잘 작동 |
| Dolly in / Push in | 긴장감, 집중 | 감정 고조, 클로즈업 | 반드시 방향 지정 |
| Dolly out / Pull back | 상황 공개 | 반전, 전체 상황 드러내기 | "gradually pull back to reveal" |
| Pan left/right | 수평 탐색 | 공간 소개, 군중 | "smooth pan" 또는 "slow pan" 추가 |
| Tilt up/down | 수직 탐색 | 건물, 인물 전신 | 방향 명시 필수 |
| Tracking shot | 피사체 추적 | 걷는 인물, 차량 | "camera follows the subject" |
| Orbit shot | 피사체 주위 회전 | 3D 느낌, 존재감 | **단독 사용** (다른 움직임 병행 금지) |
| Crane shot ascending | 크레인 상승 | 웅장함, 그랜드 리빌 | "sweeping crane shot" |
| Crash zoom | 급격한 줌 | 충격, 깨달음 | 임팩트 순간에만 |
| Aerial / Drone | 공중 촬영 | 풍경, 전경, 규모 | "aerial pan" 복합 가능 |
| Handheld | 수동, 흔들림 | 긴급, 현장감, 리얼리티 | 다큐/범죄 현장에 효과적 |
| Dolly zoom (Vertigo) | 줌+달리 반대 | 불안감, 심리적 압박 | 공포/서스펜스 특화 |
| Parallax | 전경/배경 속도차 | 깊이감, 물건 디테일 | 드론 샷에 적합 |

### 카메라 앵글

| 용어 | 느낌 | 채널별 활용 |
|------|------|-----------|
| Eye-level | 중립, 자연스러움 | 인터뷰, 객관적 장면 |
| Low angle | 위압감, 권력 | 판사, 검찰, 건물 (incidents/politics) |
| High angle | 나약함, 전체 조망 | 피해자, 범행 현장 조감 (incidents) |
| Dutch angle | 불안, 비정상 | 범인 묘사, 긴장 (incidents) |
| Overhead / Bird's eye | 패턴, 구도 | 증거물 배치, 지도 (incidents) |

---

## 라이팅 용어

| 용어 | 효과 | 채널 매칭 |
|------|------|----------|
| Warm natural light | 따뜻한 자연광 | humor |
| Golden hour | 일출/일몰 따뜻한 톤 | humor, 일상 |
| Dramatic side lighting | 극적 측면광 | politics, incidents |
| Harsh overhead light | 긴장감, 심문 느낌 | incidents (수사 장면) |
| Harsh fluorescent | 사무실, 병원, 수사실 | incidents, politics |
| Neon glow | 도시, 밤거리 | trend, MZ |
| Soft diffused light | 부드러운, 영화적 | humor, 감성 |
| Backlighting silhouette | 실루엣, 미스터리 | incidents (범인 묘사) |
| Cool blue-green grading | 차갑고 불안한 톤 | incidents |
| Muted desaturated | 탈색, 과거 느낌 | incidents (과거 회상) |

---

## 스타일 키워드

| 키워드 | 효과 | 채널 |
|--------|------|------|
| Cinematic | 영화적 품질 | 전 채널 |
| Documentary style | 다큐멘터리, 사실적 | incidents, politics |
| Film noir | 흑백, 하드보일드 | incidents |
| News broadcast | 뉴스 방송 느낌 | politics |
| Social media vertical | SNS 세로 영상 | trend |
| Shot on 16mm film stock | 거친 필름 입자, 과거 느낌 | incidents (80-90년대) |
| Shot on iPhone aesthetic | 날것, MZ 느낌 | trend |
| Inspired by [감독명] | 특정 비주얼 스타일 참조 | 전 채널 |

### 스타일 참조 감독 (효과적)
- **David Fincher** (Zodiac, Se7en): 범죄 수사, 어둡고 정교한 → incidents
- **Bong Joon-ho** (Memories of Murder): 한국 범죄, 스산한 시골 → incidents (한국 사건)
- **Adam McKay** (The Big Short): 정치 풍자, 빠른 편집 → politics
- **Wong Kar-wai**: 도시 감성, 네온, 외로움 → trend

---

## 시대/지역별 분위기 키워드 치트시트

| 시대+지역 | 핵심 시각 키워드 |
|----------|---------------|
| 1980s 한국 시골 | `16mm film grain, desaturated yellows, flickering fluorescent, unpaved road, concrete block houses, rice paddies` |
| 1990s 한국 도시 | `VHS aesthetic, neon signs with Korean text, cramped alleyways, orange sodium streetlights, tile-roofed houses` |
| 2000s 한국 현대 | `clean digital look, glass office buildings, subway platform, bright white lighting` |
| 2020s 한국 MZ | `iPhone aesthetic, neon-lit Gangnam, convenience store glow, rain-slicked pavement, AirPods` |
| 미국 FBI/수사 | `clinical fluorescent, stainless steel, glass evidence boards, navy suits, neutral tones` |
| 일본 도시 | `narrow residential streets, vending machine glow, overhead power lines, muted pastels` |
| 일본 시골 | `wooden houses, tatami floors, paper sliding doors, cicada sounds, warm summer light` |
| 법정 | `wooden judge bench elevated, dramatic overhead lighting, sharp shadows, empty gallery seats` |
| 해변 범죄현장 | `police tape fluttering, tall marsh grass, overcast sky, desolate shoreline` |

---

## 채널별 프롬프트 템플릿

### incidents (범죄/사건사고) — 7가지 포맷

#### 1. Case-File Cold Open (증거물 오프닝)
```
Extreme close-up of a gloved hand placing a sealed evidence bag on a stainless 
steel examination table. Harsh overhead laboratory lighting, clinical white 
environment. Camera static with shallow depth of field, background blurred. 
Forensic documentary style, cold sterile color grading.
```

#### 2. Faceless Scene Recreation (사건 재현, 얼굴 없이)
```
Wide shot of a dimly lit [시대] Korean [장소] at [시간]. [구체적 환경 묘사].
Camera slowly [움직임]. No faces visible, only silhouettes and shadows.
Documentary style, [시대별 필름 스타일]. [분위기] atmosphere.
```

예시 (화성 연쇄살인):
```
Static wide shot of a dimly lit rural Korean road at night, 1991. A single 
flickering streetlight casts long shadows on wet asphalt. Rice paddies stretch 
into darkness on both sides. No people visible. Atmospheric fog, muted 
desaturated color grading. Documentary style, shot on 16mm film stock with 
visible grain. Inspired by Bong Joon-ho's Memories of Murder.
```

#### 3. Timeline Snap-Through (시간순 전환)
```
[시점1 장면 묘사, 3초] --cut to-- [시점2 장면 묘사, 3초]
```
→ 시간 경과를 2-3개 컷으로 표현. 각 컷에 시대별 키워드 적용.

#### 4. Evidence Board Reveal (수사 보드 공개)
```
Medium shot of an investigation room wall covered in photos connected by red 
strings and sticky notes. Camera slowly dollies in to reveal key document. 
Harsh fluorescent overhead lighting, cluttered desk in foreground. 
Documentary style, cool blue-green color grading.
```

#### 5. Forensics Mini-Explainer (법의학 설명)
```
Extreme close-up of [증거물 종류] under [분석 장비]. [구체적 묘사]. Camera 
static. Clinical white environment with blue accent lighting. Scientific 
documentary style, sharp focus throughout.
```

#### 6. Authority Figure (수사관/판사)
```
Low angle shot of [인물 묘사] in [복장] standing in [장소]. [조명 묘사].
[인물]'s expression is [감정]. Camera [움직임]. News broadcast documentary 
style, sharp focus, shallow depth of field.
```

#### 7. Memorial/Aftermath (추모/여파)
```
Slow dolly out from [추모 물건 묘사] at [장소]. Soft natural lighting,
muted warm tones. Respectful, solemn atmosphere. Documentary style.
```

### politics (정치 풍자)

#### 국회/정부 외관
```
Wide aerial drone shot slowly descending toward the Korean National Assembly 
building dome at golden hour. Dramatic warm side lighting with long shadows.
Camera gradually pushes in. News broadcast cinematic style, vibrant colors.
```

#### 정치인 풍자 장면
```
Medium shot of a middle-aged Korean man in expensive [색상] suit, [구체적 동작] 
behind a podium. Harsh studio lighting from multiple angles, [디테일 묘사].
Bank of microphones in foreground. Camera static. Political satire documentary 
style, slightly exaggerated warm color grading.
```

#### 세금/예산 시각화
```
Overhead shot of stacked Korean won banknotes covering an entire desk surface.
A hand slowly removes bundles one by one. Dramatic side lighting creating 
sharp shadows. Camera static, shallow depth of field. Documentary style.
```

### humor (유머/썰)

#### 일상 상황 (배달, 편의점 등)
```
[Shot type] of a Korean [인물 나이/외모/복장], [구체적 행동] at [장소].
[시간대], [조명 묘사]. [인물 표정/감정 묘사]. Camera [움직임].
Slice-of-life documentary style, warm natural lighting, slightly comedic tone.
```

예시 (편의점 알바):
```
Medium shot of a young Korean convenience store clerk in red uniform, standing 
behind the counter with a deadpan expression while a customer gestures 
enthusiastically. Late night, harsh fluorescent overhead light, colorful 
snack shelves in background. Camera static. Slice-of-life style, warm 
but slightly desaturated color grading.
```

#### 음식/배달 클로즈업
```
Close-up of [음식 묘사] on [그릇/테이블]. Steam rising, [질감 묘사].
Warm overhead lighting, shallow depth of field. Food photography style.
Camera slowly dollies in.
```

### trend (MZ 트렌드)

#### MZ 라이프스타일
```
[Shot type] of a young Korean [인물 묘사] [행동] in [장소].
[시간대] lighting, [분위기]. [카메라 움직임]. Modern lifestyle social media 
vertical style, [색감 묘사]. Shot on iPhone aesthetic.
```

예시 (카페 문화):
```
Close-up tracking shot following a young Korean woman's hand holding an 
aesthetic iced latte, walking through a trendy Seongsu-dong cafe. Natural 
daylight streaming through large windows, exposed brick walls and hanging 
plants visible. Camera tracks alongside at hand height. Modern lifestyle 
vertical style, warm golden tones. Shot on iPhone aesthetic.
```

#### 테크/디지털
```
Extreme close-up of a smartphone screen showing [앱/콘텐츠 묘사]. Finger 
[동작 묘사]. Soft ambient glow from screen illuminating face partially 
visible in background. Camera static, very shallow depth of field. 
Modern tech documentary style.
```

---

## 모델별 특화 팁

### Veo 3.1 Lite / 3.0 Fast
- 카메라 타입 지정이 강력한 앵커: "security camera", "handheld documentary", "drone footage"
- `generate_audio` 파라미터로 앰비언트 사운드 자동 생성 가능
- 부정형 금지: "no buildings" → "empty landscape"

### Kling 3.0 (fal.ai)
- `++keyword++` 가중치: `"++sleek red convertible++ driving along coastal highway"`
- 카메라 설정을 스타일 큐로: "24mm, f/2.8"이 실제 광학이 아닌 학습 패턴 유발
- 동시 카메라 변환 금지: "360도 회전 + 줌인" → 왜곡 발생
- "stable camera movement" 명시로 불필요한 흔들림 방지

### Wan 2.5 (fal.ai)
- Pull-back이 강점: "close detail → movement → revealed wider scene"
- Tracking shot: "camera follows..." 표현이 효과적
- 네거티브 프롬프트: "Avoid: blurry footage, distorted facial features, watermarks"
- Panning 작동, 빠른 움직임은 피할 것

---

## 금지 사항

- **175 단어 초과 금지** — 75-175 단어 최적. 초과 시 지시 충돌
- **부정형 설명 금지** — "no buildings" 대신 "empty landscape"
- **추상적 설명 금지** — "sad scene" → "a woman looking down with tears in her eyes"
- **한국어 프롬프트 금지** — 영어만 (모든 모델이 영어 최적화)
- **동시 복합 카메라 금지** — "zoom in while orbiting while tilting" → 1개 움직임만
- **사람 얼굴 정면 금지 (incidents)** — 범죄 재현 시 실루엣/뒷모습만. 초상권 리스크

---

## 프롬프트 품질 체크리스트

```
□ Camera 지정했는가? (shot type + angle + movement)
□ Subject 구체적인가? (나이, 외모, 복장, 표정)
□ Action 명확한가? (뭘 하고 있는지, 어떤 동작인지)
□ Setting 상세한가? (장소, 시간, 날씨/조명, 시대)
□ Style 키워드 있는가? (cinematic, documentary, 감독 참조 등)
□ 시대별 키워드 적용했는가? (80년대 한국 vs 2020년대 미국)
□ 75-175 단어인가?
□ 영어로 작성했는가?
□ 카메라 움직임 1개만인가? (복합 동작 금지)
□ 부정형 없는가? ("no X" → "empty/quiet/bare")
```
