import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { QuoteCardProps } from "../lib/props-schema";

/** Max Korean characters per line for citation text. */
const CITATION_MAX_CHARS_PER_LINE = 16;
/** Max lines for citation text. */
const CITATION_MAX_LINES = 3;

/**
 * Truncate citation text to fit within max lines of max chars each.
 * Inserts line breaks and appends "..." if text exceeds the limit.
 */
function formatCitation(text: string): string {
  const maxTotal = CITATION_MAX_CHARS_PER_LINE * CITATION_MAX_LINES;
  const lines: string[] = [];
  let remaining = text;

  for (let i = 0; i < CITATION_MAX_LINES; i++) {
    if (remaining.length === 0) break;

    if (i === CITATION_MAX_LINES - 1) {
      // Last allowed line
      if (remaining.length > CITATION_MAX_CHARS_PER_LINE) {
        lines.push(remaining.slice(0, CITATION_MAX_CHARS_PER_LINE - 1) + "...");
      } else {
        lines.push(remaining);
      }
    } else if (remaining.length > maxTotal - CITATION_MAX_CHARS_PER_LINE * i) {
      // More text coming, break at line boundary
      lines.push(remaining.slice(0, CITATION_MAX_CHARS_PER_LINE));
      remaining = remaining.slice(CITATION_MAX_CHARS_PER_LINE);
    } else {
      if (remaining.length <= CITATION_MAX_CHARS_PER_LINE) {
        lines.push(remaining);
        remaining = "";
      } else {
        lines.push(remaining.slice(0, CITATION_MAX_CHARS_PER_LINE));
        remaining = remaining.slice(CITATION_MAX_CHARS_PER_LINE);
      }
    }
  }

  return lines.join("\n");
}

export const QuoteCard: React.FC<QuoteCardProps> = ({
  citation,
  source,
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
  const bodySize = 36;
  const quoteMarkSize = 72;

  // Fade-in: opacity 0→1 over frames 0-20
  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const formattedCitation = formatCitation(citation);

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        padding: `${safeZone}px ${horizontalPadding}px`,
      }}
    >
      <div
        style={{
          opacity,
          display: "flex",
          flexDirection: "row",
          alignItems: "stretch",
          width: "100%",
          marginTop: "auto",
          marginBottom: "auto",
        }}
      >
        {/* Accent bar — 4px vertical line on left edge */}
        <div
          style={{
            width: 4,
            backgroundColor: accentColor,
            flexShrink: 0,
            borderRadius: 2,
            marginRight: 24,
          }}
        />

        {/* Citation and source content */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
          }}
        >
          {/* Opening quotation mark */}
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: quoteMarkSize,
              lineHeight: 0.8,
              color: accentColor,
              marginBottom: 16,
            }}
          >
            {"\u201C"}
          </div>

          {/* Citation text */}
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: headingSize,
              lineHeight: 1.3,
              color: primaryColor,
              whiteSpace: "pre-line",
              wordBreak: "keep-all",
            }}
          >
            {formattedCitation}
          </div>

          {/* Closing quotation mark */}
          <div
            style={{
              fontFamily,
              fontWeight: 700,
              fontSize: quoteMarkSize,
              lineHeight: 0.8,
              color: accentColor,
              textAlign: "right",
              marginTop: 16,
            }}
          >
            {"\u201D"}
          </div>

          {/* Source attribution */}
          {source && (
            <div
              style={{
                fontFamily,
                fontWeight: 700,
                fontSize: bodySize,
                lineHeight: 1.4,
                color: accentColor,
                marginTop: 24,
                wordBreak: "keep-all",
              }}
            >
              {"-- "}
              {source}
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
