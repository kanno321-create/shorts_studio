import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface SpeakerLine {
  speaker: string;
  speaker_role: string;
  line: string;
  timestamp_start: number;
  timestamp_end: number;
}

interface SpeakerSubtitleProps {
  speakerLines: SpeakerLine[];
  currentTimeMs: number;
  speakerColors?: Record<string, string>;
  speakerLabels?: Record<string, string>;
  fontFamily?: string;
}

const DEFAULT_SPEAKER_COLORS: Record<string, string> = {
  police: "#60A5FA",
  suspect: "#F87171",
  victim: "#FCD34D",
  civilian: "#A78BFA",
  judge: "#34D399",
  witness: "#A78BFA",
};

/**
 * Speaker Subtitle Overlay (화자 구분 자막)
 *
 * 실제 영상(씬 타입 B)에서 대화가 나올 때 사용.
 * 반투명 검정 배경 + 화자명(색상) + 대사(흰색).
 *
 * Contract: CRIME_CHANNEL_VISUAL_CONTRACT.md Section 3
 */
export const SpeakerSubtitle: React.FC<SpeakerSubtitleProps> = ({
  speakerLines,
  currentTimeMs,
  speakerColors = DEFAULT_SPEAKER_COLORS,
  speakerLabels,
  fontFamily = "Pretendard",
}) => {
  const frame = useCurrentFrame();

  const currentTimeSec = currentTimeMs / 1000;
  const activeLine = speakerLines.find(
    (line) =>
      currentTimeSec >= line.timestamp_start &&
      currentTimeSec < line.timestamp_end
  );

  if (!activeLine) return null;

  const lineProgress = interpolate(
    currentTimeSec,
    [activeLine.timestamp_start, activeLine.timestamp_start + 0.15],
    [0, 1],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  const speakerColor =
    speakerColors[activeLine.speaker_role] || "#FFFFFF";

  const displayName = speakerLabels?.[activeLine.speaker_role] || activeLine.speaker;

  return (
    <div
      style={{
        position: "absolute",
        bottom: "35%",
        left: "5%",
        right: "5%",
        display: "flex",
        justifyContent: "center",
        opacity: lineProgress,
        fontFamily,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(0,0,0,0.75)",
          paddingTop: 8,
          paddingBottom: 8,
          paddingLeft: 16,
          paddingRight: 16,
          borderRadius: 8,
          maxWidth: "90%",
        }}
      >
        <span
          style={{
            color: speakerColor,
            fontSize: 22,
            fontWeight: 600,
          }}
        >
          {displayName}
        </span>
        <span
          style={{
            color: "rgba(255,255,255,0.5)",
            fontSize: 22,
            fontWeight: 400,
            margin: "0 6px",
          }}
        >
          :
        </span>
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 22,
            fontWeight: 600,
          }}
        >
          {activeLine.line}
        </span>
      </div>
    </div>
  );
};
