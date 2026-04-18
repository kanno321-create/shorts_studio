import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { HighlightCardProps } from "../lib/props-schema";

/** Max Korean characters per line for highlight text. */
const HIGHLIGHT_MAX_CHARS_PER_LINE = 16;
/** Max lines for highlight text. */
const HIGHLIGHT_MAX_LINES = 2;

/**
 * Truncate highlight text to fit within max lines of max chars each.
 * Uses same pattern as QuoteCard formatCitation.
 */
function formatHighlightText(text: string): string {
  const maxTotal = HIGHLIGHT_MAX_CHARS_PER_LINE * HIGHLIGHT_MAX_LINES;
  const lines: string[] = [];
  let remaining = text;

  for (let i = 0; i < HIGHLIGHT_MAX_LINES; i++) {
    if (remaining.length === 0) break;

    if (i === HIGHLIGHT_MAX_LINES - 1) {
      // Last allowed line
      if (remaining.length > HIGHLIGHT_MAX_CHARS_PER_LINE) {
        lines.push(
          remaining.slice(0, HIGHLIGHT_MAX_CHARS_PER_LINE - 1) + "..."
        );
      } else {
        lines.push(remaining);
      }
    } else if (
      remaining.length >
      maxTotal - HIGHLIGHT_MAX_CHARS_PER_LINE * i
    ) {
      lines.push(remaining.slice(0, HIGHLIGHT_MAX_CHARS_PER_LINE));
      remaining = remaining.slice(HIGHLIGHT_MAX_CHARS_PER_LINE);
    } else {
      if (remaining.length <= HIGHLIGHT_MAX_CHARS_PER_LINE) {
        lines.push(remaining);
        remaining = "";
      } else {
        lines.push(remaining.slice(0, HIGHLIGHT_MAX_CHARS_PER_LINE));
        remaining = remaining.slice(HIGHLIGHT_MAX_CHARS_PER_LINE);
      }
    }
  }

  return lines.join("\n");
}

export const HighlightCard: React.FC<HighlightCardProps> = ({
  text,
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

  // Phase 1: fade-in opacity 0-1 over frames 0-20
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Phase 1: slide-up translateY 40-0 over frames 5-25
  const translateY = interpolate(frame, [5, 25], [40, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Phase 2: underline draws from 0% to 100% width over frames 25-55
  const underlineWidth = interpolate(frame, [25, 55], [0, 100], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const formattedText = formatHighlightText(text);

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
          opacity,
          transform: `translateY(${translateY}px)`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
          width: "100%",
        }}
      >
        {/* Highlight text */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: headingSize,
            lineHeight: 1.3,
            color: primaryColor,
            whiteSpace: "pre-line",
            wordBreak: "keep-all",
            position: "relative",
            display: "inline-block",
          }}
        >
          {formattedText}
        </div>

        {/* Animated underline — 4px height, 8px below text */}
        <div
          style={{
            width: `${underlineWidth}%`,
            height: 4,
            backgroundColor: accentColor,
            marginTop: 8,
            borderRadius: 2,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
