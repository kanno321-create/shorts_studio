import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Img } from "remotion";

interface ContextGraphicProps {
  title: string;
  subtitle?: string;
  imageUrl?: string;
  datetime?: string;
  bgColor?: string;
  textColor?: string;
  subtextColor?: string;
  accentColor?: string;
  fontFamily?: string;
}

/**
 * Scene Type A: Context Graphic — ContextCard variant (설명 그래픽)
 *
 * 배경 정보, 상황 설명, 법률 해설 등에 사용.
 * 검정 배경 + 이미지 + 메인 텍스트 + 서브 텍스트.
 *
 * Contract: CRIME_CHANNEL_VISUAL_CONTRACT.md §4-1
 */
export const ContextGraphicScene: React.FC<ContextGraphicProps> = ({
  title,
  subtitle,
  imageUrl,
  datetime,
  bgColor = "#0A0A0A",
  textColor = "#FFFFFF",
  subtextColor = "#9CA3AF",
  accentColor = "#E53E3E",
  fontFamily = "Pretendard",
}) => {
  const frame = useCurrentFrame();

  const fadeIn = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: bgColor,
        justifyContent: "center",
        alignItems: "center",
        fontFamily,
        opacity: fadeIn,
      }}
    >
      {/* DateTime (타임라인 상단) */}
      {datetime && (
        <div
          style={{
            position: "absolute",
            top: 80,
            left: 60,
            right: 60,
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            style={{
              width: 4,
              height: 40,
              backgroundColor: accentColor,
              borderRadius: 2,
            }}
          />
          <span
            style={{
              color: subtextColor,
              fontSize: 22,
              fontWeight: 500,
              letterSpacing: 2,
            }}
          >
            {datetime}
          </span>
        </div>
      )}

      {/* Center Image */}
      {imageUrl && (
        <Img
          src={imageUrl}
          style={{
            maxWidth: 600,
            maxHeight: 400,
            objectFit: "contain",
            borderRadius: 8,
            marginBottom: 40,
          }}
        />
      )}

      {/* Main Title */}
      <div
        style={{
          color: textColor,
          fontSize: 28,
          fontWeight: 700,
          textAlign: "center",
          paddingLeft: 60,
          paddingRight: 60,
          lineHeight: 1.5,
          textShadow: "0 2px 8px rgba(0,0,0,0.6)",
        }}
      >
        {title}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div
          style={{
            color: subtextColor,
            fontSize: 20,
            fontWeight: 400,
            textAlign: "center",
            paddingLeft: 80,
            paddingRight: 80,
            marginTop: 16,
            lineHeight: 1.4,
          }}
        >
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};
