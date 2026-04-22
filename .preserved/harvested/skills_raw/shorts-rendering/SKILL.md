---
name: shorts-rendering
description: Remotion 렌더링 규칙, 3-Zone 레이아웃, 자막 워드하이라이트, OffthreadVideo, TransitionSeries. ShortsVideo.tsx 수정 시 반드시 참조.
metadata:
  tags: remotion, rendering, layout, subtitle, design, tsx
---

## When to use

Remotion/영상 렌더링 관련 작업 전에 이 스킬을 읽는다:
- ShortsVideo.tsx 수정 시
- remotion_render.py 수정 시
- 자막 스타일/위치 변경 시
- 전환 효과 추가/수정 시
- 3-zone 레이아웃 변경 시

Remotion 공식 API 패턴은 `remotion` 스킬(rules/ 38개 파일)을 참조.
이 스킬은 **우리 프로젝트 고유** 렌더링 규칙이다.

---

## Remotion 필수 패턴

### 절대 규칙
- **`<OffthreadVideo>` 필수** — `<Video>` 사용 금지 (frame-accurate 렌더링 불가)
- **`TransitionSeries`** — 수동 Sequence+opacity 계산 대신 Remotion 공식 API
- **30fps** — `durationInFrames = seconds × 30`
- **1080×1920** (9:16 세로)

### OffthreadVideo vs Video

```tsx
// 금지
<Video src={videoSrc} />

// 필수
import { OffthreadVideo } from 'remotion';
<OffthreadVideo src={videoSrc} style={{ objectFit: 'cover' }} />
```

이유: `<Video>`는 렌더링 시 frame-accurate하지 않음. `<OffthreadVideo>`는 별도 스레드에서 정확한 프레임을 추출.

### TransitionSeries 패턴

```tsx
import { TransitionSeries, linearTiming } from '@remotion/transitions';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={clip1Frames}>
    <Clip1 />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={fade()}
    timing={linearTiming({ durationInFrames: 15 })}
  />
  <TransitionSeries.Sequence durationInFrames={clip2Frames}>
    <Clip2 />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

---

## 3-Zone Layout (ShortsVideo.tsx)

```
┌─────────────────────┐ 0px
│ 상단 검은바 (320px)    │  제목 2줄 + 미세 그리드 패턴
│  1줄: 85px / 2줄: 110px│  ExtraBold, 키워드 색상 강조
├─────────────────────┤ 320px
│ 영상 센터 (1267px)     │  objectFit:cover
│  워드하이라이트 자막    │  현재 단어=#FFD000, 나머지=흰색
├─────────────────────┤ 1587px
│ 하단 검은바 (333px)    │  요약+구분선+채널명+구독+해시태그
└─────────────────────┘ 1920px
```

### 상단 제목 (320px 영역)
- 2줄 구성: **1줄 85px** (상황/맥락), **2줄 110px** (핵심 키워드)
- 폰트: BlackHanSans, fontWeight: 800 (ExtraBold)
- 외곽선: 검정 **5-6px** (textShadow 다중 방향)
- 키워드 색상: 노랑(#FFD000), 빨강(#FF2200), 주황(#FF9700)
- 나머지: 흰색(#FFFFFF)
- 배경: #0a0a0a + 미세 그리드

### 영상 센터 (1267px 영역)
- objectFit: cover
- 다중 클립: clips 배열 + TransitionSeries
- 자막 오버레이: 영상 영역 65% 지점

### 하단 채널 (333px 영역)
- 요약 텍스트: 24px, 반투명
- 채널명: 36px, Bold, letterSpacing 8px
- 구독/좋아요: 24px, #FF3B30
- 해시태���: 20px, 반투명
- 배경: #0a0a0a + 미세 그리드

---

## 자막 규칙

### 워드 하이라이트
- **현재 단어**: #FFD000, 72px, DoHyeon
- **나머지 단어**: 흰색, 64px, DoHyeon
- 외곽선: 5-6px (textShadow)
- 5-8글자씩 빠른 전환

### 타이밍
- faster-whisper 단어 단위 타이밍 사용 (스크립트 추정 금지)
- 내레이션 속도와 정확히 싱크
- **잔존 시간 800ms** — 음성 끝나도 페이드아웃으로 유지

### 금지
- spring/scale 애니메이션 금지 — **색상 변경만 허용**
- 문장 통째 표시 금지 — 단어/구 단위 전환 필수
- 한 화면 최대 8글자 (1줄)

---

## 채널별 디자인 차이

| 항목 | humor | politics | trend |
|------|-------|----------|-------|
| 전환 | glitch, pixelate | clockWipe, checkerboard | zoomBlur, rgbSplit |
| 키워드 색상 | #FFD000 (노랑) | #FF2200 (빨강) | #00F5D4 (네온) |
| 자막 크기 | 88px | 80px | 84px |

---

## 제출 전 체크리스트 (하나라도 NO면 제출 금지)

```
□ Pexels/Pixabay 스톡 사용 안 했는가? (메모리 feedback_pexels_banned 완전 금지)
□ 인물 매칭: 언급 인물이 화면에 나오는가?
□ 내용 매칭: 각 장면 영상이 내레이션과 관련 있는가?
□ 자막: 단어/구 단위 빠른 전환인가?
□ 상단 제목: 2줄, 굵은 폰트, 키워드 색상 강조, 고정?
□ 음성: 채널별 지정 보이스 사용?
□ 구조: 훅 → 본론 → CTA?
□ 증거: 실제 영상/사진/캡처 포함?
□ OffthreadVideo 사용? (Video 금지)
□ 자막 잔존 800ms 적용?
```
