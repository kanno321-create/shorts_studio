import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { IntroCardProps } from "../lib/props-schema";

/** Max Korean characters per line for topic text. */
const TOPIC_MAX_CHARS_PER_LINE = 12;
/** Max lines for topic text. */
const TOPIC_MAX_LINES = 2;

/**
 * Format topic text to fit within max lines of max chars each.
 * Uses same pattern as TitleCard formatTitle.
 */
function formatTopicText(text: string): string {
  const maxTotal = TOPIC_MAX_CHARS_PER_LINE * TOPIC_MAX_LINES;

  if (text.length <= TOPIC_MAX_CHARS_PER_LINE) {
    return text;
  }

  if (text.length > maxTotal) {
    return (
      text.slice(0, TOPIC_MAX_CHARS_PER_LINE) +
      "\n" +
      text.slice(TOPIC_MAX_CHARS_PER_LINE, maxTotal - 1) +
      "..."
    );
  }

  // Split into two lines
  return (
    text.slice(0, TOPIC_MAX_CHARS_PER_LINE) +
    "\n" +
    text.slice(TOPIC_MAX_CHARS_PER_LINE)
  );
}

export const IntroCard: React.FC<IntroCardProps> = ({
  channelName,
  topicText,
  logoUrl,
  primaryColor,
  accentColor,
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

  // Zoom-in entrance: scale 0.8 to 1.0 with spring
  const zoomSpring = spring({
    frame,
    fps,
    config: { damping: 200 },
  });
  const scale = interpolate(zoomSpring, [0, 1], [0.8, 1.0]);

  // Topic text fade-in + slide-up delayed 15 frames
  const topicOpacity = interpolate(frame, [15, 35], [0, 1], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });
  const topicTranslateY = interpolate(frame, [15, 35], [40, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  const formattedTopic = formatTopicText(topicText);

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
          transform: `scale(${scale})`,
        }}
      >
        {/* Logo (if provided) */}
        {logoUrl && (
          <img
            src={logoUrl}
            style={{
              width: 120,
              height: 120,
              objectFit: "contain",
              marginBottom: 24,
            }}
          />
        )}

        {/* Channel name — uppercase with letter-spacing */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: bodySize,
            lineHeight: 1.4,
            color: accentColor,
            textTransform: "uppercase",
            letterSpacing: 4,
            wordBreak: "keep-all",
            marginBottom: 40,
          }}
        >
          {channelName}
        </div>

        {/* Topic text — delayed fade-in + slide-up */}
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: displaySize,
            lineHeight: 1.2,
            color: primaryColor,
            whiteSpace: "pre-line",
            wordBreak: "keep-all",
            opacity: topicOpacity,
            transform: `translateY(${topicTranslateY}px)`,
          }}
        >
          {formattedTopic}
        </div>
      </div>
    </AbsoluteFill>
  );
};
