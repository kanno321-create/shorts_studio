import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { ListCardProps } from "../lib/props-schema";

/** Max Korean characters per list item. */
const LIST_ITEM_MAX_CHARS = 14;
/** Max items displayed for readability on portrait format. */
const MAX_ITEMS = 5;
/** Frame stagger between each item entrance. */
const STAGGER_FRAMES = 10;

/**
 * Truncate a list item to fit within max chars.
 * Appends "..." if text exceeds the limit.
 */
function formatListItem(text: string): string {
  if (text.length <= LIST_ITEM_MAX_CHARS) {
    return text;
  }
  return text.slice(0, LIST_ITEM_MAX_CHARS - 1) + "...";
}

export const ListCard: React.FC<ListCardProps> = ({
  items,
  ordered,
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
  const headingSize = is16x9 ? 44 : 48;

  // Limit to max items
  const displayItems = items.slice(0, MAX_ITEMS);

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
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          width: "100%",
          marginTop: "auto",
          marginBottom: "auto",
          gap: 16,
        }}
      >
        {displayItems.map((item, i) => {
          // Staggered spring entrance for each item
          const springValue = spring({
            frame: frame - i * STAGGER_FRAMES,
            fps,
            config: { damping: 200 },
          });

          const translateX = interpolate(springValue, [0, 1], [-40, 0]);
          const opacity = interpolate(springValue, [0, 1], [0, 1]);

          const prefix = ordered ? `${i + 1}. ` : "\u2022 ";
          const formattedItem = formatListItem(item);

          return (
            <div
              key={i}
              style={{
                opacity,
                transform: `translateX(${translateX}px)`,
                display: "flex",
                flexDirection: "row",
                alignItems: "baseline",
              }}
            >
              {/* Item prefix: number or bullet */}
              <span
                style={{
                  fontFamily,
                  fontWeight: 700,
                  fontSize: headingSize,
                  lineHeight: 1.3,
                  color: accentColor,
                  whiteSpace: "pre",
                  flexShrink: 0,
                }}
              >
                {prefix}
              </span>

              {/* Item text */}
              <span
                style={{
                  fontFamily,
                  fontWeight: 700,
                  fontSize: headingSize,
                  lineHeight: 1.3,
                  color: primaryColor,
                  wordBreak: "keep-all",
                }}
              >
                {formattedItem}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
