import React from "react";
import { Composition } from "remotion";
import type { CalculateMetadataFunction } from "remotion";

// Side-effect import: loads Pretendard Bold 700 font
import "./lib/fonts";

import { TitleCard } from "./compositions/TitleCard";
import { QuoteCard } from "./compositions/QuoteCard";
import { StatsCard } from "./compositions/StatsCard";
import { ListCard } from "./compositions/ListCard";
import { HighlightCard } from "./compositions/HighlightCard";
import { BarChartCard } from "./compositions/BarChartCard";
import { ComparisonCard } from "./compositions/ComparisonCard";
import { IntroCard } from "./compositions/IntroCard";
import { OutroCard } from "./compositions/OutroCard";
import { ShortsVideo, shortsVideoSchema } from "./compositions/ShortsVideo";
import { LongformVideo, longformVideoSchema } from "./compositions/LongformVideo";
import type { LongformVideoProps } from "./compositions/LongformVideo";
import {
  titleCardSchema,
  quoteCardSchema,
  statsCardSchema,
  listCardSchema,
  highlightCardSchema,
  barChartCardSchema,
  comparisonCardSchema,
  introCardSchema,
  outroCardSchema,
} from "./lib/props-schema";

import testGfcarWordSubs from "./lib/test-gfcar-word-subs.json";
import type { ShortsVideoProps } from "./compositions/ShortsVideo";

// Dynamic duration from props — Python pipeline sets durationInFrames
const shortsCalculateMetadata: CalculateMetadataFunction<ShortsVideoProps> = async ({
  props,
}) => {
  return {
    durationInFrames: props.durationInFrames || 900,
  };
};

// Longform: dynamic duration (13-18 min = 23400-32400 frames at 30fps)
const longformCalculateMetadata: CalculateMetadataFunction<LongformVideoProps> = async ({
  props,
}) => {
  return {
    durationInFrames: props.durationInFrames || 27000, // default 15 min
  };
};

/**
 * Remotion composition registry for all graphic card types.
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
          audioSrc: "test-gfcar/narration.mp3",
          titleLine1: "제목을 입력하세요",
          subtitles: [],
          channelName: "채널명",
          durationInFrames: 900,
        }}
      />

      <Composition
        id="TitleCard"
        component={TitleCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={titleCardSchema}
        defaultProps={{
          title: "제목을 입력하세요",
          subtitle: undefined,
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="QuoteCard"
        component={QuoteCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={quoteCardSchema}
        defaultProps={{
          citation: "인용문을 입력하세요",
          source: undefined,
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="StatsCard"
        component={StatsCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={statsCardSchema}
        defaultProps={{
          number: "0",
          label: "통계 라벨",
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="ListCard"
        component={ListCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={listCardSchema}
        defaultProps={{
          items: ["항목 1", "항목 2", "항목 3"],
          ordered: true,
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="HighlightCard"
        component={HighlightCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={highlightCardSchema}
        defaultProps={{
          text: "핵심 문장을 입력하세요",
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="BarChartCard"
        component={BarChartCard}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
        schema={barChartCardSchema}
        defaultProps={{
          bars: [
            { label: "항목 A", value: 75 },
            { label: "항목 B", value: 50 },
          ],
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 150,
        }}
      />

      <Composition
        id="ComparisonCard"
        component={ComparisonCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={comparisonCardSchema}
        defaultProps={{
          leftLabel: "A",
          leftValue: "100",
          rightLabel: "B",
          rightValue: "50",
          vsText: "VS",
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      <Composition
        id="IntroCard"
        component={IntroCard}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
        schema={introCardSchema}
        defaultProps={{
          channelName: "채널명",
          topicText: "오늘의 주제",
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 90,
        }}
      />

      <Composition
        id="OutroCard"
        component={OutroCard}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
        schema={outroCardSchema}
        defaultProps={{
          channelName: "채널명",
          ctaText: "구독과 좋아요 부탁드립니다",
          primaryColor: "#FFFFFF",
          accentColor: "#00F5D4",
          secondaryColor: "#9B5DE5",
          backgroundColor: "#2D1B69",
          fontFamily: "Pretendard",
          durationInFrames: 120,
        }}
      />

      {/* ── Test: Full Shorts Video (여자친구 차 밀기) v2 ── */}
      <Composition
        id="ShortsVideo-GfCar"
        component={ShortsVideo}
        durationInFrames={1120}
        fps={30}
        width={1080}
        height={1920}
        schema={shortsVideoSchema}
        defaultProps={{
          videoSrc: "test-gfcar/video_h264.mp4",
          audioSrc: "test-gfcar/narration.mp3",
          titleLine1: "여자친구가 차를",
          titleLine2: "밀겠다고?",
          titleKeywords: [
            { text: "밀겠다고?", color: "#FFFFFF" },
          ],
          subtitles: testGfcarWordSubs,
          description: "남자친구한테 차 밀 수 있나고 내기를 걸었는데...",
          channelName: "썰 튜 브",
          hashtags: "#쇼츠 #유머 #레전드",
          fontFamily: "Pretendard",
          durationInFrames: 1120,
        }}
      />

      {/* ── LongformVideo: 16:9 longform composition (13-18 min) ── */}
      <Composition
        id="LongformVideo"
        component={LongformVideo}
        durationInFrames={27000}
        fps={30}
        width={1920}
        height={1080}
        schema={longformVideoSchema}
        calculateMetadata={longformCalculateMetadata}
        defaultProps={{
          clips: [],
          audioSrc: "longform/narration_full.mp3",
          chapters: [],
          subtitleCues: [],
          channelName: "사건기록부",
          accentColor: "#E53E3E",
          durationInFrames: 27000,
        }}
      />
    </>
  );
};
