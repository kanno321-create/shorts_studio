/**
 * DialogueBox — Game-style dialogue box (슈퍼로봇대전/비주얼노벨 스타일)
 *
 * Design doc: longform/SCRIPT_SKILL.md lines 45-66
 * - Semi-transparent dark panel at bottom 20% of screen
 * - Left: character portrait (detective or assistant)
 * - Speaker name with color (detective=white, assistant=#FFD000)
 * - Text with letter-by-letter typing effect synced to TTS timing
 */
import React, { useMemo } from "react";
import { Img, staticFile, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export interface DialogueCue {
  startMs: number;
  endMs: number;
  words: string[];
  highlightIndex: number;
  speaker: string;
  speakerColor: string;
}

interface DialogueBoxProps {
  cue: DialogueCue | null;
  detectivePortraitSrc?: string;
  assistantPortraitSrc?: string;
  canvasWidth: number;
  canvasHeight: number;
}

const SPEAKER_LABELS: Record<string, string> = {
  detective: "탐정",
  assistant: "조수",
  mascot: "조수",
};

const BOX_HEIGHT_RATIO = 0.18; // 18% of canvas height
const PORTRAIT_SIZE = 100;
const BOX_PADDING = 24;
const BOX_MARGIN = 20;

export const DialogueBox: React.FC<DialogueBoxProps> = ({
  cue,
  detectivePortraitSrc,
  assistantPortraitSrc,
  canvasWidth,
  canvasHeight,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  // All hooks must be called before any early return (React rules of hooks)
  const boxOpacity = useMemo(() => {
    if (!cue) return 0;
    const fadeInEnd = cue.startMs + 150;
    const fadeOutStart = cue.endMs - 150;
    if (currentTimeMs < cue.startMs) return 0;
    if (currentTimeMs < fadeInEnd) {
      return interpolate(currentTimeMs, [cue.startMs, fadeInEnd], [0, 1]);
    }
    if (currentTimeMs > fadeOutStart && currentTimeMs <= cue.endMs) {
      return interpolate(currentTimeMs, [fadeOutStart, cue.endMs], [1, 0]);
    }
    if (currentTimeMs > cue.endMs) return 0;
    return 1;
  }, [currentTimeMs, cue]);

  if (!cue) return null;

  const boxHeight = canvasHeight * BOX_HEIGHT_RATIO;
  const boxY = canvasHeight - boxHeight - BOX_MARGIN;

  const portraitSrc =
    cue.speaker === "detective" ? detectivePortraitSrc : assistantPortraitSrc;

  const speakerLabel = SPEAKER_LABELS[cue.speaker] || cue.speaker;
  const speakerColor = cue.speakerColor || "#FFFFFF";

  const fullText = cue.words.join(" ");

  const cueProgress = interpolate(
    currentTimeMs,
    [cue.startMs, cue.endMs],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const visibleChars = Math.floor(cueProgress * fullText.length);
  const displayText = fullText.slice(0, visibleChars);

  return (
    <div
      style={{
        position: "absolute",
        left: BOX_MARGIN,
        top: boxY,
        width: canvasWidth - BOX_MARGIN * 2,
        height: boxHeight,
        backgroundColor: "rgba(10, 10, 10, 0.85)",
        borderRadius: 12,
        border: "1px solid rgba(255, 255, 255, 0.15)",
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        padding: BOX_PADDING,
        gap: 20,
        opacity: boxOpacity,
        zIndex: 20,
      }}
    >
      {/* Character portrait */}
      {portraitSrc && (
        <div
          style={{
            width: PORTRAIT_SIZE,
            height: PORTRAIT_SIZE,
            borderRadius: "50%",
            border: `3px solid ${speakerColor}`,
            overflow: "hidden",
            flexShrink: 0,
          }}
        >
          <Img
            src={staticFile(portraitSrc)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </div>
      )}

      {/* Text area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
        {/* Speaker name */}
        <div
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: speakerColor,
            letterSpacing: 2,
            textShadow: "0 1px 4px rgba(0,0,0,0.6)",
          }}
        >
          {speakerLabel}
        </div>

        {/* Dialogue text with typing effect */}
        <div
          style={{
            fontSize: 28,
            fontWeight: 400,
            color: "#FFFFFF",
            lineHeight: 1.5,
            letterSpacing: 1,
            textShadow: "0 1px 3px rgba(0,0,0,0.5)",
            minHeight: 50,
          }}
        >
          {displayText}
          {/* Blinking cursor */}
          {visibleChars < fullText.length && (
            <span
              style={{
                opacity: Math.sin(frame * 0.3) > 0 ? 1 : 0,
                color: speakerColor,
              }}
            >
              |
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
