// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface IconExplainerProps {
  iconEmoji: string;
  description: string;
  bgColor?: string;
  textColor?: string;
  subtextColor?: string;
  fontFamily?: string;
}

/**
 * Scene Type A variant: IconExplainer (아이콘 설명)
 *
 * 용도: 상황 시각화 (차+사람 충돌, 총기 사용 등)
 * 레이아웃: 중앙 큰 아이콘/이모지 + 하단 설명 텍스트
 * 애니메이션: fade-in 500ms
 *
 * Contract: CRIME_CHANNEL_VISUAL_CONTRACT.md §4-3
 * Note: Lucide React 대신 이모지/유니코드 사용 (의존성 최소화)
 */
export const IconExplainer: React.FC<IconExplainerProps> = ({
  iconEmoji,
  description,
  bgColor = "#0A0A0A",
  textColor = "#FFFFFF",
  subtextColor = "#9CA3AF",
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
      {/* 중앙 큰 아이콘 */}
      <div style={{ fontSize: 120, lineHeight: 1, marginBottom: 32 }}>
        {iconEmoji}
      </div>

      {/* 하단 설명 텍스트 */}
      <div
        style={{
          color: textColor,
          fontSize: 26,
          fontWeight: 600,
          textAlign: "center",
          paddingLeft: 60,
          paddingRight: 60,
          lineHeight: 1.5,
        }}
      >
        {description}
      </div>
    </AbsoluteFill>
  );
};
