// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
import { z } from "zod";

/**
 * Channel theme schema — base color/font props shared by all card types.
 * Defaults to trend channel identity (#2D1B69 / #FFFFFF / #00F5D4).
 * secondaryColor added for BarChartCard alternating bars and ComparisonCard right-side accent.
 */
export const channelThemeSchema = z.object({
  primaryColor: z.string().default("#FFFFFF"),
  accentColor: z.string().default("#00F5D4"),
  secondaryColor: z.string().default("#9B5DE5"),
  backgroundColor: z.string().default("#2D1B69"),
  fontFamily: z.string().default("Pretendard"),
});

/**
 * TitleCard props — full-bleed centered title with optional subtitle.
 */
export const titleCardSchema = channelThemeSchema.extend({
  title: z.string(),
  subtitle: z.string().optional(),
  durationInFrames: z.number().default(120),
});

/**
 * QuoteCard props — left-aligned citation with accent bar and optional source.
 */
export const quoteCardSchema = channelThemeSchema.extend({
  citation: z.string(),
  source: z.string().optional(),
  durationInFrames: z.number().default(120),
});

/**
 * StatsCard props — centered number with label, spring scale animation.
 */
export const statsCardSchema = channelThemeSchema.extend({
  number: z.string(),
  label: z.string(),
  durationInFrames: z.number().default(120),
});

/**
 * ListCard props — numbered or bullet-point list with staggered spring entrance.
 */
export const listCardSchema = channelThemeSchema.extend({
  items: z.array(z.string()),
  ordered: z.boolean().default(true),
  durationInFrames: z.number().default(120),
});

/**
 * HighlightCard props — key sentence with animated underline emphasis.
 */
export const highlightCardSchema = channelThemeSchema.extend({
  text: z.string(),
  highlightWord: z.string().optional(),
  durationInFrames: z.number().default(120),
});

/**
 * BarChartCard props — horizontal bar chart with staggered bar growth animation.
 */
export const barChartCardSchema = channelThemeSchema.extend({
  bars: z.array(
    z.object({
      label: z.string(),
      value: z.number(),
    })
  ),
  maxValue: z.number().optional(),
  unit: z.string().optional(),
  durationInFrames: z.number().default(150),
});

/**
 * ComparisonCard props — VS comparison with left/right slide-in animation.
 */
export const comparisonCardSchema = channelThemeSchema.extend({
  leftLabel: z.string(),
  leftValue: z.string(),
  rightLabel: z.string(),
  rightValue: z.string(),
  vsText: z.string().default("VS"),
  durationInFrames: z.number().default(120),
});

/**
 * IntroCard props — channel-branded intro with zoom-in animation.
 */
export const introCardSchema = channelThemeSchema.extend({
  channelName: z.string(),
  topicText: z.string(),
  logoUrl: z.string().optional(),
  durationInFrames: z.number().default(90),
});

/**
 * OutroCard props — subscribe/like CTA with staggered fade-in. Video only (D-04).
 */
export const outroCardSchema = channelThemeSchema.extend({
  channelName: z.string(),
  ctaText: z.string().default("구독과 좋아요 부탁드립니다"),
  logoUrl: z.string().optional(),
  durationInFrames: z.number().default(120),
});

export type ChannelTheme = z.infer<typeof channelThemeSchema>;
export type TitleCardProps = z.infer<typeof titleCardSchema>;
export type QuoteCardProps = z.infer<typeof quoteCardSchema>;
export type StatsCardProps = z.infer<typeof statsCardSchema>;
export type ListCardProps = z.infer<typeof listCardSchema>;
export type HighlightCardProps = z.infer<typeof highlightCardSchema>;
export type BarChartCardProps = z.infer<typeof barChartCardSchema>;
export type ComparisonCardProps = z.infer<typeof comparisonCardSchema>;
export type IntroCardProps = z.infer<typeof introCardSchema>;
export type OutroCardProps = z.infer<typeof outroCardSchema>;
