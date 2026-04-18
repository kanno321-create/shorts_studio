import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { TitleCardProps } from "../lib/props-schema";

/** Max Korean characters per line for title text. */
const TITLE_MAX_CHARS_PER_LINE = 12;
/** Max lines for title text. */
const TITLE_MAX_LINES = 2;

/**
 * Truncate text to fit within max lines of max chars each.
 * Inserts line breaks and appends "..." if text exceeds the limit.
 */
function formatTitle(text: string): string {
  const maxTotal = TITLE_MAX_CHARS_PER_LINE * TITLE_MAX_LINES;

  if (text.length <= TITLE_MAX_CHARS_PER_LINE) {
    return text;
  }

  if (text.length > maxTotal) {
    return (
      text.slice(0, TITLE_MAX_CHARS_PER_LINE) +
      "\n" +
      text.slice(TITLE_MAX_CHARS_PER_LINE, maxTotal - 1) +
      "..."
    );
  }

  // Split into two lines
  return (
    text.slice(0, TITLE_MAX_CHARS_PER_LINE) +
    "\n" +
    text.slice(TITLE_MAX_CHARS_PER_LINE)
  );
}

export const TitleCard: React.FC<TitleCardProps> = ({
  title,
  subtitle,
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
  const displaySize = is16x9 ? 56 : 64;
  const bodySize = 36;

  // Fade-in: opacity 0→1 over frames 0-20
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  // Slide-up: translateY 40px→0px over frames 5-25
  const translateY = interpolate(frame, [5, 25], [40, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const formattedTitle = formatTitle(title);

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
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: displaySize,
            lineHeight: 1.2,
            color: primaryColor,
            whiteSpace: "pre-line",
            wordBreak: "keep-all",
          }}
        >
          {formattedTitle}
        </div>

        {subtitle && (
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: bodySize,
              lineHeight: 1.4,
              color: accentColor,
              marginTop: 40,
              wordBreak: "keep-all",
            }}
          >
            {subtitle}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
