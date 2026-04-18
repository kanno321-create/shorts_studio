import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { BarChartCardProps } from "../lib/props-schema";

/** Max bars displayed for readability. */
const MAX_BARS = 5;
/** Width reserved for label area in pixels. */
const LABEL_AREA_WIDTH = 200;
/** Bar height in pixels. */
const BAR_HEIGHT = 48;
/** Gap between bars in pixels. */
const BAR_GAP = 16;
/** Frame stagger between each bar growth. */
const STAGGER_FRAMES = 10;
/** Threshold for placing value annotation inside the bar. */
const INSIDE_THRESHOLD = 0.6;

export const BarChartCard: React.FC<BarChartCardProps> = ({
  bars,
  maxValue: maxValueProp,
  unit,
  primaryColor,
  accentColor,
  secondaryColor,
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
  const labelSize = is16x9 ? 24 : 28;

  // Limit to max bars
  const displayBars = bars.slice(0, MAX_BARS);

  // Auto-calculate maxValue if not provided
  const computedMaxValue =
    maxValueProp ?? Math.max(...displayBars.map((b) => b.value), 1);

  // Available width for bars (total width minus padding and label area)
  const barMaxWidth = width - horizontalPadding * 2 - LABEL_AREA_WIDTH;

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
          width: "100%",
          gap: BAR_GAP,
        }}
      >
        {displayBars.map((bar, i) => {
          // Staggered bar growth animation
          const springValue = spring({
            frame: frame - i * STAGGER_FRAMES,
            fps,
            config: { damping: 200 },
          });

          const barWidthRatio = bar.value / computedMaxValue;
          const targetBarWidth = barWidthRatio * barMaxWidth;
          const currentBarWidth = interpolate(
            springValue,
            [0, 1],
            [0, targetBarWidth]
          );

          // Bar color: odd index (0,2,4) = accentColor, even index (1,3) = secondaryColor
          const barColor = i % 2 === 0 ? accentColor : secondaryColor;

          // Value annotation: inside bar if bar > 60% of max, outside otherwise
          const isValueInside = barWidthRatio > INSIDE_THRESHOLD;
          const valueText = unit
            ? `${bar.value}${unit}`
            : String(bar.value);

          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                width: "100%",
              }}
            >
              {/* Label area — fixed width */}
              <div
                style={{
                  width: LABEL_AREA_WIDTH,
                  flexShrink: 0,
                  fontFamily,
                  fontWeight: 700,
                  fontSize: labelSize,
                  lineHeight: 1.4,
                  color: primaryColor,
                  wordBreak: "keep-all",
                  textAlign: "right",
                  paddingRight: 16,
                }}
              >
                {bar.label}
              </div>

              {/* Bar + value annotation */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  flex: 1,
                  position: "relative",
                }}
              >
                {/* Animated bar */}
                <div
                  style={{
                    width: currentBarWidth,
                    height: BAR_HEIGHT,
                    backgroundColor: barColor,
                    borderRadius: 4,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    paddingRight: isValueInside ? 12 : 0,
                  }}
                >
                  {/* Value inside bar */}
                  {isValueInside && (
                    <span
                      style={{
                        fontFamily,
                        fontWeight: 700,
                        fontSize: labelSize,
                        lineHeight: 1.4,
                        color: backgroundColor,
                      }}
                    >
                      {valueText}
                    </span>
                  )}
                </div>

                {/* Value outside bar */}
                {!isValueInside && (
                  <span
                    style={{
                      fontFamily,
                      fontWeight: 700,
                      fontSize: labelSize,
                      lineHeight: 1.4,
                      color: primaryColor,
                      marginLeft: 8,
                    }}
                  >
                    {valueText}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
