/**
 * ChapterBadge — Chapter/Act indicator overlay
 *
 * Design doc: longform/PIPELINE.md line 76 (chapter badge)
 * Displays "Act.N — Title" on upper-right with fade in/out.
 * Reference: 유명한탐정 channel Part tag placement.
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

interface ChapterBadgeProps {
  act: number;
  title: string;
  startFrame: number;
  durationFrames: number;
  accentColor?: string;
}

const BADGE_FADE_FRAMES = 15; // 0.5s at 30fps

export const ChapterBadge: React.FC<ChapterBadgeProps> = ({
  act,
  title,
  startFrame,
  durationFrames,
  accentColor = "#E53E3E",
}) => {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  if (localFrame < 0 || localFrame > durationFrames) return null;

  const opacity = interpolate(
    localFrame,
    [0, BADGE_FADE_FRAMES, durationFrames - BADGE_FADE_FRAMES, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 30,
        right: 30,
        display: "flex",
        alignItems: "center",
        gap: 10,
        opacity,
        zIndex: 15,
      }}
    >
      <div
        style={{
          backgroundColor: accentColor,
          color: "#FFFFFF",
          fontSize: 18,
          fontWeight: 700,
          padding: "6px 14px",
          borderRadius: 6,
          letterSpacing: 1,
        }}
      >
        Act.{act}
      </div>
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.7)",
          color: "#FFFFFF",
          fontSize: 18,
          fontWeight: 400,
          padding: "6px 14px",
          borderRadius: 6,
          letterSpacing: 1,
        }}
      >
        {title}
      </div>
    </div>
  );
};
