/**
 * ProgressBar — Thin progress indicator at bottom edge
 *
 * Design doc: longform/PIPELINE.md line 76 (progress bar)
 * Horizontal line showing current/total time at the very bottom of the video.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

interface ProgressBarProps {
  canvasWidth: number;
  accentColor?: string;
  height?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  canvasWidth,
  accentColor = "#E53E3E",
  height = 4,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const progress = Math.min(frame / durationInFrames, 1);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 0,
        left: 0,
        width: canvasWidth,
        height,
        backgroundColor: "rgba(255, 255, 255, 0.15)",
        zIndex: 25,
      }}
    >
      <div
        style={{
          width: `${progress * 100}%`,
          height: "100%",
          backgroundColor: accentColor,
          transition: "width 0.03s linear",
        }}
      />
    </div>
  );
};
