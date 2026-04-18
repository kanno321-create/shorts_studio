import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { OutroCardProps } from "../lib/props-schema";

export const OutroCard: React.FC<OutroCardProps> = ({
  channelName,
  ctaText,
  logoUrl,
  primaryColor,
  accentColor,
  backgroundColor,
  fontFamily,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const is16x9 = width > 1080;

  // Spacing
  const horizontalPadding = is16x9 ? 100 : 60;
  const safeZone = is16x9 ? 60 : 80;

  // Typography
  const headingSize = is16x9 ? 44 : 48;
  const bodySize = is16x9 ? 32 : 36;

  // CTA emphasis line: draws in from center over frames 0-30
  const lineWidth = interpolate(frame, [0, 30], [0, 200], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Staggered fade-in: line first (0-20), CTA text delay 10 (10-30), channel name delay 20 (20-40)
  const lineOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const ctaOpacity = interpolate(frame, [10, 30], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const channelNameOpacity = interpolate(frame, [20, 40], [0, 1], {
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
        {/* Logo (if provided) */}
        {logoUrl && (
          <img
            src={logoUrl}
            style={{
              width: 80,
              height: 80,
              objectFit: "contain",
              marginBottom: 24,
              opacity: lineOpacity,
            }}
          />
        )}

        {/* CTA emphasis line — accentColor horizontal line */}
        <div
          style={{
            width: lineWidth,
            height: 4,
            backgroundColor: accentColor,
            borderRadius: 2,
            opacity: lineOpacity,
            marginBottom: 16,
          }}
        />

        {/* CTA text */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: headingSize,
            lineHeight: 1.3,
            color: primaryColor,
            wordBreak: "keep-all",
            opacity: ctaOpacity,
          }}
        >
          {ctaText}
        </div>

        {/* Channel name */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: bodySize,
            lineHeight: 1.4,
            color: accentColor,
            marginTop: 24,
            wordBreak: "keep-all",
            opacity: channelNameOpacity,
          }}
        >
          {channelName}
        </div>
      </div>
    </AbsoluteFill>
  );
};
