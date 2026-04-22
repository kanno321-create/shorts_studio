// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

interface ImpactCutProps {
  text: string;
  color?: string;
  bgColor?: string;
  bgGradientTo?: string;
  fontFamily?: string;
}

/**
 * Scene Type C: Impact Cut (강조 컷)
 *
 * 충격적 사실, 전환점, 반전 등에 사용. 짧게 2-5초.
 * 검정 배경 + 큰 텍스트 (노란/빨간).
 *
 * Contract: CRIME_CHANNEL_VISUAL_CONTRACT.md Section 1 (씬 타입 C)
 */
export const ImpactCutScene: React.FC<ImpactCutProps> = ({
  text,
  color = "#FFC947",
  bgColor = "#0A0A0A",
  bgGradientTo,
  fontFamily = "Pretendard",
}) => {
  const frame = useCurrentFrame();

  const fadeIn = interpolate(frame, [0, 9], [0, 1], {
    extrapolateRight: "clamp",
  });

  // 그라데이션 배경: bgGradientTo가 있으면 bgColor → bgGradientTo (계약서 §1: #E53E3E → #0A0A0A)
  const background = bgGradientTo
    ? `linear-gradient(180deg, ${bgColor} 0%, ${bgGradientTo} 100%)`
    : bgColor;

  return (
    <AbsoluteFill
      style={{
        background,
        justifyContent: "center",
        alignItems: "center",
        fontFamily,
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          color,
          fontSize: 42,
          fontWeight: 900,
          textAlign: "center",
          paddingLeft: 50,
          paddingRight: 50,
          lineHeight: 1.4,
          textShadow: `0 0 30px ${color}40, 0 4px 12px rgba(0,0,0,0.8)`,
          maxWidth: 900,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
