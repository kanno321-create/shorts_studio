/**
 * EndingSequence — Fixed detective office ending scene
 *
 * Design doc: longform/SCRIPT_SKILL.md lines 163-168
 * - Detective sits in chair with notebook and cigarette
 * - Mascot sweeps with broom in background
 * - Channel logo + subscribe overlay → fade out
 *
 * This is a placeholder component. The actual office scene visuals
 * will be provided as video/image clips by the Video Sourcer agent.
 * This component handles the overlay text and fade-out logic.
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

interface EndingSequenceProps {
  channelName: string;
  accentColor?: string;
  canvasWidth: number;
  canvasHeight: number;
  durationFrames?: number; // How long the ending lasts (default: 5s = 150 frames)
  startFrame: number;      // When this sequence starts in absolute frames
}

const FADE_DURATION = 30; // 1 second fade

export const EndingSequence: React.FC<EndingSequenceProps> = ({
  channelName,
  accentColor = "#E53E3E",
  canvasWidth,
  canvasHeight,
  durationFrames = 150,
  startFrame,
}) => {
  const frame = useCurrentFrame();
  const localFrame = frame - startFrame;

  if (localFrame < 0 || localFrame > durationFrames) return null;

  // Fade in at start, fade out at end
  const opacity = interpolate(
    localFrame,
    [0, FADE_DURATION, durationFrames - FADE_DURATION, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  // Subscribe button appears after 1 second
  const subscribeOpacity = interpolate(
    localFrame,
    [30, 50],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: canvasWidth,
        height: canvasHeight,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 30,
        opacity,
      }}
    >
      {/* Channel logo text */}
      <div
        style={{
          fontSize: 64,
          fontWeight: 700,
          color: "#FFFFFF",
          letterSpacing: 6,
          textShadow: "0 3px 12px rgba(0,0,0,0.8)",
          marginBottom: 30,
        }}
      >
        {channelName}
      </div>

      {/* Subscribe button overlay */}
      <div
        style={{
          opacity: subscribeOpacity,
          display: "flex",
          gap: 20,
        }}
      >
        <div
          style={{
            backgroundColor: accentColor,
            color: "#FFFFFF",
            fontSize: 24,
            fontWeight: 700,
            padding: "12px 32px",
            borderRadius: 8,
            letterSpacing: 2,
          }}
        >
          구독
        </div>
        <div
          style={{
            backgroundColor: "rgba(255, 255, 255, 0.15)",
            color: "#FFFFFF",
            fontSize: 24,
            fontWeight: 400,
            padding: "12px 32px",
            borderRadius: 8,
            letterSpacing: 2,
          }}
        >
          알림 설정
        </div>
      </div>
    </div>
  );
};
