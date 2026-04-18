import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { StatsCardProps } from "../lib/props-schema";

export const StatsCard: React.FC<StatsCardProps> = ({
  number,
  label,
  primaryColor,
  accentColor,
  backgroundColor,
  fontFamily,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();

  const is16x9 = width > 1080;

  // Spacing
  const horizontalPadding = is16x9 ? 100 : 60;
  const safeZone = is16x9 ? 60 : 80;

  // Typography
  const headingSize = is16x9 ? 44 : 48;
  const labelSize = 28;

  // Number scale: spring() from 1.2→1.0 over frames 0-30, damping 200
  const springValue = spring({
    frame,
    fps,
    config: {
      damping: 200,
    },
    durationInFrames: 30,
  });
  // spring() goes 0→1, map to scale 1.2→1.0
  const scale = interpolate(springValue, [0, 1], [1.2, 1.0]);

  // Label fade: opacity 0→1 over frames 10-30
  const labelOpacity = interpolate(frame, [10, 30], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: `${safeZone}px ${horizontalPadding}px`,
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          width: "100%",
        }}
      >
        {/* Primary number with spring scale animation */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: headingSize,
            lineHeight: 1.3,
            color: accentColor,
            transform: `scale(${scale})`,
            wordBreak: "keep-all",
          }}
        >
          {number}
        </div>

        {/* Metric label with fade-in */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: labelSize,
            lineHeight: 1.4,
            color: primaryColor,
            marginTop: 16,
            opacity: labelOpacity,
            wordBreak: "keep-all",
          }}
        >
          {label}
        </div>
      </div>
    </AbsoluteFill>
  );
};
