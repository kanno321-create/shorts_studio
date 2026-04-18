/**
 * CTAOverlay — Call-to-Action overlay card for business traffic channels
 *
 * Design doc: channel-object-nag SKILL.md (CTA rules)
 * Appears during the last N frames of a video with fade+slide animation.
 * Used by object_nag channel to drive viewers to business landing pages.
 *
 * Usage: pass startFrame = totalDuration - durationInFrames
 */
import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

interface CTAOverlayProps {
  text: string;
  accentColor: string;
  durationInFrames: number;
  startFrame: number;
}

export const CTAOverlay: React.FC<CTAOverlayProps> = ({
  text,
  accentColor,
  durationInFrames,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Only render during CTA period
  if (frame < startFrame || frame > startFrame + durationInFrames) {
    return null;
  }

  const localFrame = frame - startFrame;

  // Fade in over 0.5 seconds
  const opacity = interpolate(localFrame, [0, fps * 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Slide up from bottom using spring
  const translateY = spring({
    frame: localFrame,
    fps,
    config: { damping: 15, stiffness: 80 },
  });
  const slideY = interpolate(translateY, [0, 1], [60, 0]);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 340,
        left: 40,
        right: 40,
        opacity,
        transform: `translateY(${slideY}px)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        zIndex: 20,
        pointerEvents: "none",
      }}
    >
      {/* CTA Card */}
      <div
        style={{
          background: "rgba(0, 0, 0, 0.85)",
          borderRadius: 16,
          padding: "20px 32px",
          border: `2px solid ${accentColor}`,
          width: "100%",
          textAlign: "center",
        }}
      >
        <div
          style={{
            color: "#FFFFFF",
            fontSize: 36,
            fontWeight: 700,
            fontFamily: "Pretendard, sans-serif",
            lineHeight: 1.3,
            marginBottom: 8,
          }}
        >
          {text}
        </div>
        <div
          style={{
            color: accentColor,
            fontSize: 28,
            fontWeight: 600,
            fontFamily: "Pretendard, sans-serif",
          }}
        >
          {"설명란 링크 확인 \u2193"}
        </div>
      </div>
    </div>
  );
};
