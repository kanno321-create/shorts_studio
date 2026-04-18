import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { ComparisonCardProps } from "../lib/props-schema";

export const ComparisonCard: React.FC<ComparisonCardProps> = ({
  leftLabel,
  leftValue,
  rightLabel,
  rightValue,
  vsText,
  primaryColor,
  accentColor,
  secondaryColor,
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
  const displaySize = is16x9 ? 56 : 64;
  const bodySize = is16x9 ? 32 : 36;

  // Left column slides in from left (-60px to 0px) over frames 0-25
  const leftTranslateX = interpolate(frame, [0, 25], [-60, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Right column slides in from right (+60px to 0px) over frames 0-25
  const rightTranslateX = interpolate(frame, [0, 25], [60, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Fade-in for both columns
  const columnOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // VS scales up from 0.5 to 1.0 with spring starting at frame 15
  const vsSpring = spring({
    frame: frame - 15,
    fps,
    config: { damping: 200 },
  });
  const vsScale = interpolate(vsSpring, [0, 1], [0.5, 1.0]);

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
          flexDirection: "row",
          alignItems: "center",
          width: "100%",
        }}
      >
        {/* Left column — 45% width */}
        <div
          style={{
            width: "45%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: columnOpacity,
            transform: `translateX(${leftTranslateX}px)`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: displaySize,
              lineHeight: 1.2,
              color: accentColor,
              wordBreak: "keep-all",
              textAlign: "center",
            }}
          >
            {leftValue}
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: bodySize,
              lineHeight: 1.4,
              color: primaryColor,
              marginTop: 16,
              wordBreak: "keep-all",
              textAlign: "center",
            }}
          >
            {leftLabel}
          </div>
        </div>

        {/* VS divider — 10% width */}
        <div
          style={{
            width: "10%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            transform: `scale(${vsScale})`,
          }}
        >
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: 40,
              backgroundColor: `${accentColor}26`,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <span
              style={{
                fontFamily,
                fontWeight: 700,
                fontSize: displaySize,
                lineHeight: 1.2,
                color: accentColor,
              }}
            >
              {vsText}
            </span>
          </div>
        </div>

        {/* Right column — 45% width */}
        <div
          style={{
            width: "45%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            opacity: columnOpacity,
            transform: `translateX(${rightTranslateX}px)`,
          }}
        >
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: displaySize,
              lineHeight: 1.2,
              color: secondaryColor,
              wordBreak: "keep-all",
              textAlign: "center",
            }}
          >
            {rightValue}
          </div>
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: bodySize,
              lineHeight: 1.4,
              color: primaryColor,
              marginTop: 16,
              wordBreak: "keep-all",
              textAlign: "center",
            }}
          >
            {rightLabel}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
