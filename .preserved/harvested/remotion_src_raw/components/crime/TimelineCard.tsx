import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface TimelineCardProps {
  datetime: string;
  event: string;
  bgColor?: string;
  textColor?: string;
  subtextColor?: string;
  accentColor?: string;
  fontFamily?: string;
}

/**
 * Scene Type A variant: TimelineCard (타임라인)
 *
 * 용도: "2023년 5월 13일, 오후 12시 3분" + 이벤트 설명
 * 레이아웃: 좌측 시간 + 우측 이벤트, 수평선 연결
 * 애니메이션: 좌→우 slide-in 300ms
 *
 * Contract: CRIME_CHANNEL_VISUAL_CONTRACT.md §4-2
 */
export const TimelineCard: React.FC<TimelineCardProps> = ({
  datetime,
  event,
  bgColor = "#0A0A0A",
  textColor = "#FFFFFF",
  subtextColor = "#9CA3AF",
  accentColor = "#E53E3E",
  fontFamily = "Pretendard",
}) => {
  const frame = useCurrentFrame();

  // slide-in from left: 300ms = 9 frames @30fps
  const slideIn = interpolate(frame, [0, 9], [-200, 0], {
    extrapolateRight: "clamp",
  });
  const fadeIn = interpolate(frame, [0, 9], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bgColor,
        justifyContent: "center",
        alignItems: "center",
        fontFamily,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24,
          paddingLeft: 80,
          paddingRight: 80,
          opacity: fadeIn,
          transform: `translateX(${slideIn}px)`,
        }}
      >
        {/* 좌측: 시간 */}
        <div
          style={{
            color: accentColor,
            fontSize: 24,
            fontWeight: 700,
            whiteSpace: "nowrap",
            minWidth: 200,
            textAlign: "right",
          }}
        >
          {datetime}
        </div>

        {/* 수평 연결선 */}
        <div
          style={{
            width: 60,
            height: 2,
            backgroundColor: subtextColor,
            flexShrink: 0,
          }}
        />

        {/* 우측: 이벤트 */}
        <div
          style={{
            color: textColor,
            fontSize: 24,
            fontWeight: 500,
            lineHeight: 1.5,
          }}
        >
          {event}
        </div>
      </div>
    </AbsoluteFill>
  );
};
