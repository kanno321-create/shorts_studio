import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import React from "react";

export type BracketCaptionProps = {
  text: string;
  startMs?: number;
  endMs?: number;
};

/**
 * Phase 42 — Bracket action description caption.
 *
 * Gray semi-transparent rounded box at bottom 25% (matches 사건기록부 bodycam style).
 * Renders text wrapped in parentheses, e.g. "(테이저를 꺼낸다)".
 *
 * Timing window optional: if startMs/endMs provided, only visible in that range.
 * Fades in/out over 180ms at window edges for smooth appearance.
 *
 * Intended to be mounted conditionally within clips where
 * `sceneType === "real_footage"` and `bracketCaption` is present.
 */
export const BracketCaption: React.FC<BracketCaptionProps> = ({ text, startMs, endMs }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tMs = (frame / fps) * 1000;

  if (startMs !== undefined && tMs < startMs) return null;
  if (endMs !== undefined && tMs > endMs) return null;

  // fade 180ms at each boundary
  const inOpacity = startMs !== undefined
    ? interpolate(tMs, [startMs, startMs + 180], [0, 1], { extrapolateRight: "clamp" })
    : 1;
  const outOpacity = endMs !== undefined
    ? interpolate(tMs, [endMs - 180, endMs], [1, 0], { extrapolateLeft: "clamp" })
    : 1;
  const opacity = Math.min(inOpacity, outOpacity);

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "25%" }}>
      <div
        data-testid="bracket-caption"
        style={{
          backgroundColor: "rgba(40, 40, 40, 0.72)",
          color: "#E8E8E8",
          padding: "14px 28px",
          borderRadius: 8,
          fontSize: 42,
          fontWeight: 500,
          letterSpacing: "0.02em",
          fontFamily: "'Noto Sans KR', 'Noto Sans JP', sans-serif",
          opacity,
          maxWidth: "88%",
          textAlign: "center",
        }}
      >
        {`(${text})`}
      </div>
    </AbsoluteFill>
  );
};
