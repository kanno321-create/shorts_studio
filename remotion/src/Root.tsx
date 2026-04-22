// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
// Shorts-only scope (Phase 16-02 Rule 2 deviation): long-form TitleCard/QuoteCard/...
// compositions are NOT ported — they belong to long-form pipeline (future phase).
import React from "react";
import { Composition } from "remotion";
import type { CalculateMetadataFunction } from "remotion";

// Side-effect import: loads Pretendard Bold 700 font
import "./lib/fonts";

import { ShortsVideo, shortsVideoSchema } from "./compositions/ShortsVideo";
import type { ShortsVideoProps } from "./compositions/ShortsVideo";

// Dynamic duration from props — Python pipeline sets durationInFrames
const shortsCalculateMetadata: CalculateMetadataFunction<ShortsVideoProps> = async ({
  props,
}) => {
  return {
    durationInFrames: props.durationInFrames || 900,
  };
};

/**
 * Remotion composition registry — Shorts-only (Phase 16-02).
 * Default resolution: 1080x1920 (9:16 shorts).
 * CLI --props overrides defaultProps for pipeline rendering.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ── ShortsVideo: main pipeline composition (dynamic duration) ── */}
      <Composition
        id="ShortsVideo"
        component={ShortsVideo}
        durationInFrames={900}
        fps={30}
        width={1080}
        height={1920}
        schema={shortsVideoSchema}
        calculateMetadata={shortsCalculateMetadata}
        defaultProps={{
          audioSrc: "narration.mp3",
          titleLine1: "제목을 입력하세요",
          subtitles: [],
          channelName: "사건기록부",
          durationInFrames: 900,
        }}
      />
    </>
  );
};
