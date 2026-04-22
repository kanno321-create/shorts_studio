// Ported-adjacent — Phase 16-03 Option A (Task 0 outro research findings).
//
// Programmatic OutroCard component. 3 seconds (90 frames @ 30fps).
// No external mp4 dependency — pure Remotion render.
//
// Rationale (Plan 16-03 Task 0 evidence):
//   1. shorts_naberal/_shared/signatures/ 에 incidents_outro*.mp4 부재
//   2. shorts_naberal/remotion/src/compositions/OutroCard.tsx 132 줄 프로그램적 구현 존재
//   3. CLAUDE.md forbid-11: Veo API 신규 호출 금지
//   4. harvested remotion_render.py 에 outro 처리 0건 (Python 계층 관심사 밖)
//
// Usage: ShortsVideo.tsx 마지막 clip 으로 삽입 또는 type="outro_card" sentinel 분기.
//        props schema 는 OutroCardProps (channelName, accentColor, seriesPart?, seriesTotal?).

import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface OutroCardProps {
  channelName: string;
  accentColor: string;
  seriesPart?: number | null;
  seriesTotal?: number | null;
}

export const OUTRO_DURATION_FRAMES = 90; // 3.0s @ 30fps — incidents.md section 7 마지막 2-5초

export const OutroCard: React.FC<OutroCardProps> = ({
  channelName,
  accentColor,
  seriesPart,
  seriesTotal,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Staggered fade-in/out:
  //   - opacity: 0 -> 1 during 0-10f, stay 1 until F-15, fade to 0.4 at F
  //   - textY: spring from 40 -> 0 over first ~20f
  //   - stripeW: grow 0 -> 864 during 0-30f
  const opacity = interpolate(
    frame,
    [0, 10, OUTRO_DURATION_FRAMES - 15, OUTRO_DURATION_FRAMES],
    [0, 1, 1, 0.4],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  const textY = spring({
    frame,
    fps,
    config: { damping: 14 },
    from: 40,
    to: 0,
  });

  const stripeWidth = interpolate(frame, [0, 30], [0, 864], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const partTextOpacity = interpolate(frame, [15, 35], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0A0A0A",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      {/* Channel name — primary text, large */}
      <div
        style={{
          color: accentColor,
          fontFamily: "BlackHanSans",
          fontSize: 120,
          opacity,
          transform: `translateY(${textY}px)`,
          letterSpacing: 4,
          textAlign: "center",
          fontWeight: 700,
        }}
      >
        {channelName}
      </div>

      {/* Optional series Part indicator (e.g., "Part 2 / 3") */}
      {seriesPart != null && seriesTotal != null && (
        <div
          style={{
            marginTop: 48,
            color: "#FFFFFF",
            fontFamily: "DoHyeon",
            fontSize: 64,
            opacity: partTextOpacity,
            letterSpacing: 2,
            textAlign: "center",
          }}
        >
          Part {seriesPart} / {seriesTotal}
        </div>
      )}

      {/* Accent stripe — horizontal bar, bottom area */}
      <div
        style={{
          position: "absolute",
          bottom: 240,
          width: stripeWidth,
          height: 8,
          backgroundColor: accentColor,
          opacity: opacity * 0.7,
          borderRadius: 4,
        }}
      />
    </AbsoluteFill>
  );
};
