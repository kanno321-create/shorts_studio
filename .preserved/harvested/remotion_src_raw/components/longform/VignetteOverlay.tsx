/**
 * VignetteOverlay — Brown/sepia edge darkening effect
 *
 * Design doc: longform/WORK_HANDOFF.md (유명한탐정 분석 — 갈색 비네팅)
 * Adds cinematic vignette to the entire video frame.
 */
import React from "react";

interface VignetteOverlayProps {
  canvasWidth: number;
  canvasHeight: number;
  intensity?: number; // 0-1, default 0.6
  color?: string;     // default: warm brown
}

export const VignetteOverlay: React.FC<VignetteOverlayProps> = ({
  canvasWidth,
  canvasHeight,
  intensity = 0.6,
  color = "rgba(30, 15, 5, INTENSITY)",
}) => {
  const resolvedColor = color.replace("INTENSITY", String(intensity));

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: canvasWidth,
        height: canvasHeight,
        background: `radial-gradient(ellipse at center, transparent 40%, ${resolvedColor} 100%)`,
        pointerEvents: "none",
        zIndex: 10,
      }}
    />
  );
};
