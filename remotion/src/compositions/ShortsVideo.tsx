// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
import React, { useMemo } from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  Audio,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  Img,
  interpolate,
  Easing,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { z } from "zod";
import { titleFont, subtitleFont, bodyFont, japaneseFont, englishFont, ensureJpTitleFont, ensureJpSubFont, jpTitleFontFamily, jpSubFontFamily } from "../lib/fonts";
import {
  ContextGraphicScene,
  ImpactCutScene,
  SpeakerSubtitle,
} from "../components/crime";
import { BracketCaption } from "../components/BracketCaption";
import { OutroCard, OUTRO_DURATION_FRAMES } from "../components/OutroCard";
import { glitch } from "../lib/transitions/presentations/glitch";
import { rgbSplit } from "../lib/transitions/presentations/rgb-split";
import { zoomBlur } from "../lib/transitions/presentations/zoom-blur";
import { lightLeak } from "../lib/transitions/presentations/light-leak";
import { clockWipe } from "../lib/transitions/presentations/clock-wipe";
import { pixelate } from "../lib/transitions/presentations/pixelate";
import { checkerboard } from "../lib/transitions/presentations/checkerboard";

// ─── Layout Constants (v12 — 하단 1/3 축소, 상단 확장) ──────────────

const CANVAS_W = 1080;
const CANVAS_H = 1920;

const TOP_BAR_H = 320;    // 상단 검은바 (270→320, 제목 공간 여유 확보)
const BOTTOM_BAR_H = 333;  // 하단 검은바 (500→333, 2/3로 축소)
const VIDEO_H = CANVAS_H - TOP_BAR_H - BOTTOM_BAR_H; // 1267px

// v12: 영어 자막 커버 제거됨 — 하단 축소로 불필요

// Subtitle Y position (video center area)
const DEFAULT_SUB_Y_RATIO = 0.65; // 영상 영역의 65% 지점 (벤치마킹: 하단 30-40%)

// ─── Schema ─────────────────────────────────

const wordSubCueSchema = z.object({
  startMs: z.number(),
  endMs: z.number(),
  words: z.array(z.string()),
  highlightIndex: z.number(),
});

const keywordSchema = z.object({
  text: z.string(),
  color: z.string(),
});

const speakerLineSchema = z.object({
  speaker: z.string(),
  speaker_role: z.string(),
  line: z.string(),
  timestamp_start: z.number(),
  timestamp_end: z.number(),
});

const graphicConfigSchema = z.object({
  title: z.string().optional(),
  subtitle: z.string().optional(),
  image_url: z.string().optional(),
  icon: z.string().optional(),
  datetime: z.string().optional(),
});

const clipSchema = z.object({
  type: z.enum(["video", "image"]),
  src: z.string(),
  durationInFrames: z.number(),
  // Phase 6: Ken Burns camera movement for image clips
  movement: z.enum(["zoom_in", "zoom_out", "pan_left", "pan_right"]).optional(),
  // Phase 7: per-clip transition (overrides global transitionType)
  transition: z.enum([
    "cut", "fade", "glitch", "rgbSplit", "zoomBlur",
    "lightLeak", "clockWipe", "pixelate", "checkerboard",
  ]).optional(),
  sceneType: z.enum(["default", "context_graphic", "real_footage", "impact_cut"]).optional(),
  speakerLines: z.array(speakerLineSchema).optional(),
  graphicConfig: graphicConfigSchema.optional(),
  impactText: z.string().optional(),
  impactColor: z.string().optional(),
  // Phase 42 real_footage layer: gray parenthesized action caption + optional timing window
  bracketCaption: z.string().optional(),
  bracketCaptionStartMs: z.number().optional(),
  bracketCaptionEndMs: z.number().optional(),
  // Phase 42 real_footage word-highlight subtitles (EN→KO/JA translated), passthrough payload
  realFootageSubtitles: z.array(z.any()).optional(),
});

export const shortsVideoSchema = z.object({
  // 다중 클립 (우선) — clips가 있으면 videoSrc/imageSrc 무시
  clips: z.array(clipSchema).optional(),
  // 하위호환: 단일 소스 (clips 없을 때 폴백)
  videoSrc: z.string().optional(),
  imageSrc: z.string().optional(),
  audioSrc: z.string(),

  // BGM (optional) — 제공 시 내레이션 구간 자동 더킹
  bgmSrc: z.string().optional(),
  bgmVolume: z.number().min(0).max(1).optional(),

  titleLine1: z.string(),
  titleLine2: z.string().optional(),
  titleKeywords: z.array(keywordSchema).optional(),
  // 제목 아래 태그라인 (예: "미스터리 수첩 #01", "범죄수첩 #01")
  titleTagline: z.string().optional(),

  subtitles: z.array(wordSubCueSchema),
  description: z.string().optional(),

  channelName: z.string(),
  hashtags: z.string().optional(),
  accentColor: z.string().optional(),

  // Character avatars for top bar (detective right, assistant left)
  characterLeftSrc: z.string().optional(),
  characterRightSrc: z.string().optional(),

  // Series info (Part N / M) — displayed as badge on bottom-left
  seriesPart: z.number().optional(),
  seriesTotal: z.number().optional(),

  // 하단 바 텍스트 (기본: 한국어, 일본어 채널은 일본어로 오버라이드)
  subscribeText: z.string().optional(),
  likeText: z.string().optional(),

  // Channel logo (top-left corner)
  channelLogoSrc: z.string().optional(),
  fontFamily: z.string().optional(),
  subtitlePosition: z.number().min(0).max(1).optional(), // 0.65=기본(중하단), 0.80=하단(차분한 톤)
  subtitleHighlightColor: z.string().optional(),          // 기본 #FFD000, 채널별 커스텀
  subtitleFontSize: z.number().optional(),                // 기본 80, 작게=60
  durationInFrames: z.number(),
  transitionType: z.enum([
    "cut", "fade", "none",
    "glitch", "rgbSplit", "zoomBlur", "lightLeak",
    "clockWipe", "pixelate", "checkerboard",
  ]).optional(),
});

export type ShortsVideoProps = z.infer<typeof shortsVideoSchema>;

// ─── Subtle noise pattern (CSS background) ──

const SUBTLE_PATTERN = `
  radial-gradient(circle at 20% 30%, rgba(255,255,255,0.015) 0%, transparent 50%),
  radial-gradient(circle at 80% 70%, rgba(255,255,255,0.01) 0%, transparent 50%),
  repeating-linear-gradient(
    0deg,
    transparent,
    transparent 3px,
    rgba(255,255,255,0.008) 3px,
    rgba(255,255,255,0.008) 4px
  ),
  repeating-linear-gradient(
    90deg,
    transparent,
    transparent 3px,
    rgba(255,255,255,0.008) 3px,
    rgba(255,255,255,0.008) 4px
  )
`;

// ─── Title keyword highlighter ──────────────

function renderTitleWithKeywords(
  text: string,
  keywords: Array<{ text: string; color: string }>
): React.ReactNode[] {
  if (!keywords || keywords.length === 0) return [text];

  const result: React.ReactNode[] = [];
  let remaining = text;
  let keyIndex = 0;

  while (remaining.length > 0) {
    let earliestPos = remaining.length;
    let matched: (typeof keywords)[0] | null = null;

    for (const kw of keywords) {
      const pos = remaining.indexOf(kw.text);
      if (pos !== -1 && pos < earliestPos) {
        earliestPos = pos;
        matched = kw;
      }
    }

    if (!matched) {
      result.push(remaining);
      break;
    }

    if (earliestPos > 0) result.push(remaining.slice(0, earliestPos));

    result.push(
      <span key={`kw-${keyIndex++}`} style={{ color: matched.color }}>
        {matched.text}
      </span>
    );

    remaining = remaining.slice(earliestPos + matched.text.length);
  }

  return result;
}

// ─── Text shadow helper ─────────────────────

const titleShadow = (px: number) => `
  -${px}px -${px}px 0 #000,
   ${px}px -${px}px 0 #000,
  -${px}px  ${px}px 0 #000,
   ${px}px  ${px}px 0 #000,
   0 0 ${px * 2}px rgba(0,0,0,0.8),
   0 0 ${px * 3}px rgba(0,0,0,0.4)
`;

// ─── Ken Burns Image (Phase 6) ──────────────────
// 정지 이미지에 수학적 보간 카메라 동선을 적용한다.
// P(t) = P_start + (P_end - P_start) * f(t),  f = cubic-bezier ease-in-out

type KenBurnsMovement = "zoom_in" | "zoom_out" | "pan_left" | "pan_right";

const KenBurnsImage: React.FC<{
  src: string;
  movement: KenBurnsMovement;
  durationInFrames: number;
  style?: React.CSSProperties;
}> = ({ src, movement, durationInFrames, style }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    easing: Easing.bezier(0.25, 0.1, 0.25, 1),
    extrapolateRight: "clamp",
  });

  const transforms: Record<KenBurnsMovement, { scale: number; x: number; y: number }> = {
    zoom_in:   { scale: 1 + progress * 0.15,       x: 0,               y: 0 },
    zoom_out:  { scale: 1.15 - progress * 0.15,     x: 0,               y: 0 },
    pan_left:  { scale: 1.1,                         x: progress * -80,  y: 0 },
    pan_right: { scale: 1.1,                         x: progress * 80,   y: 0 },
  };

  const t = transforms[movement];

  return (
    <Img
      src={src}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: "center 45%",
        transform: `scale(${t.scale}) translate(${t.x}px, ${t.y}px)`,
        ...style,
      }}
    />
  );
};

// ─── Component ───────────────────────────────

export const ShortsVideo: React.FC<ShortsVideoProps> = ({
  clips,
  videoSrc,
  imageSrc,
  audioSrc,
  bgmSrc,
  bgmVolume = 0.2,
  titleLine1,
  titleLine2,
  titleKeywords = [],
  titleTagline,
  subtitles,
  description,
  channelName,
  hashtags,
  accentColor = "#FF3B30",
  characterLeftSrc,
  characterRightSrc,
  seriesPart,
  seriesTotal,
  subscribeText = "구독",
  likeText = "좋아요",
  channelLogoSrc,
  fontFamily,
  subtitlePosition = 0.65,
  subtitleHighlightColor = "#FFD000",
  subtitleFontSize = 80,
  durationInFrames: totalDuration,
  transitionType = "cut",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  // 채널별 자막 위치 (prop 기반, 기본 65%)
  const subY = TOP_BAR_H + VIDEO_H * subtitlePosition;

  // Build resolved clips: use clips array or fallback to single source
  const resolvedClips = useMemo(() => {
    if (clips && clips.length > 0) return clips;
    // Fallback: single source → 1-clip array
    if (videoSrc) return [{ type: "video" as const, src: videoSrc, durationInFrames: totalDuration }];
    if (imageSrc) return [{ type: "image" as const, src: imageSrc, durationInFrames: totalDuration }];
    return [];
  }, [clips, videoSrc, imageSrc, totalDuration]);

  // Font families from Google Fonts (loaded in fonts.ts)
  // 일본어 채널: Dela Gothic One (제목) + M PLUS Rounded 1c (자막)
  // 영어 채널: Inter (wildlife/documentary)
  const isJapanese = fontFamily === "Noto Sans JP";
  const isEnglish = fontFamily === "Inter";
  if (isJapanese) {
    ensureJpTitleFont();
    ensureJpSubFont();
  }
  const titleFontFamily = isJapanese ? jpTitleFontFamily : (isEnglish ? englishFont.fontFamily : titleFont.fontFamily);
  const subFontFamily = isJapanese ? jpSubFontFamily : (isEnglish ? englishFont.fontFamily : subtitleFont.fontFamily);
  const bodyFontFamily = isJapanese ? japaneseFont.fontFamily : (isEnglish ? englishFont.fontFamily : (fontFamily || bodyFont.fontFamily));

  // Subtitle: instant switch, no linger/fade (깜빡임 완전 제거)
  const currentSub = useMemo(() => {
    const exact = subtitles.find(
      (s) => currentTimeMs >= s.startMs && currentTimeMs < s.endMs
    );
    if (exact) return { cue: exact, isFading: false };
    return null;
  }, [subtitles, currentTimeMs]);

  // Dynamic title font sizing — prevent 3-line overflow in 320px top bar
  // Available width = 1080 - avatars(200*2) - margins(~40) ≈ 640px
  const hasAvatars = !!(characterLeftSrc || characterRightSrc);
  const titleAreaW = hasAvatars ? 620 : 900;
  const calcTitleFontSize = (text: string, maxSize: number) => {
    if (!text) return maxSize;
    const charCount = text.length;
    // CJK char width ≈ fontSize * 0.9, letterSpacing 2-3px
    const maxForWidth = Math.floor(titleAreaW / (charCount * 0.92));
    return Math.min(maxSize, Math.max(maxForWidth, 36)); // floor 36px
  };
  const line1MaxSize = isJapanese ? 60 : 85;
  const line2MaxSize = isJapanese ? 80 : 110;
  const dynLine1Size = calcTitleFontSize(titleLine1, line1MaxSize);
  const dynLine2Size = calcTitleFontSize(titleLine2 || "", line2MaxSize);

  // Gentle fade-in (no bounce)
  const fadeIn = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a", fontFamily: bodyFontFamily }}>

      {/* ════════ TOP BLACK BAR (제목 + 캐릭터) ════════ */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: CANVAS_W,
          height: TOP_BAR_H,
          backgroundColor: "#0a0a0a",
          background: SUBTLE_PATTERN,
          zIndex: 5,
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          alignItems: "center",
          padding: "0 10px",
          opacity: fadeIn,
        }}
      >
        {/* Channel logo (top-left) — wildlife lion symbol etc. */}
        {channelLogoSrc && (
          <div
            style={{
              position: "absolute",
              left: 20,
              top: "50%",
              transform: "translateY(-50%)",
              width: 160,
              height: 160,
              zIndex: 6,
            }}
          >
            <Img
              src={staticFile(channelLogoSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                filter: "drop-shadow(0 2px 6px rgba(0,0,0,0.5))",
              }}
            />
          </div>
        )}
        {/* Left character (pet — face zoom: 전신→얼굴~목 나비넥타이 크롭) */}
        {characterLeftSrc && (
          <div
            style={{
              width: 200,
              height: 200,
              borderRadius: "50%",
              border: `3px solid ${accentColor}`,
              flexShrink: 0,
              marginRight: 10,
              overflow: "hidden",
            }}
          >
            <Img
              src={staticFile(characterLeftSrc)}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                objectPosition: "center 15%",
                transform: "scale(1.8)",
                transformOrigin: "center 25%",
              }}
            />
          </div>
        )}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            fontSize: dynLine1Size,
            fontWeight: 400,
            fontFamily: titleFontFamily,
            color: "#FFFFFF",
            textAlign: "center",
            lineHeight: 1.3,
            textShadow: "0 2px 8px rgba(0,0,0,0.6)",
            letterSpacing: isJapanese ? 4 : 2,
            maxWidth: titleAreaW,
            whiteSpace: "nowrap",
            overflow: "hidden",
          }}
        >
          {renderTitleWithKeywords(titleLine1, titleKeywords)}
        </div>
        {titleLine2 && (
          <div
            style={{
              fontSize: dynLine2Size,
              fontWeight: 400,
              fontFamily: titleFontFamily,
              color: "#FFFFFF",
              textAlign: "center",
              lineHeight: 1.2,
              textShadow: "0 2px 10px rgba(0,0,0,0.6)",
              letterSpacing: isJapanese ? 5 : 3,
              marginTop: 8,
              maxWidth: titleAreaW,
              whiteSpace: "nowrap",
              overflow: "hidden",
            }}
          >
            {renderTitleWithKeywords(titleLine2, titleKeywords)}
          </div>
        )}
        {/* 카테고리 수첩 태그라인 (예: 미스터리 수첩 #01) */}
        {titleTagline && (
          <div
            style={{
              fontSize: 36,
              fontWeight: 400,
              fontFamily: bodyFontFamily,
              color: "#FFD000",
              textAlign: "center",
              letterSpacing: 4,
              marginTop: 6,
              textShadow: "0 1px 4px rgba(0,0,0,0.5)",
            }}
          >
            {titleTagline}
          </div>
        )}
        </div>
        {/* Right character (detective — 크기만 확대) */}
        {characterRightSrc && (
          <Img
            src={staticFile(characterRightSrc)}
            style={{
              width: 200,
              height: 200,
              borderRadius: "50%",
              objectFit: "cover",
              border: `3px solid ${accentColor}`,
              flexShrink: 0,
              marginLeft: 10,
            }}
          />
        )}
      </div>

      {/* ════════ CENTER VIDEO AREA (multi-clip with TransitionSeries) ════════ */}
      <div
        style={{
          position: "absolute",
          top: TOP_BAR_H,
          left: 0,
          width: CANVAS_W,
          height: VIDEO_H,
          overflow: "hidden",
        }}
      >
        {resolvedClips.length === 1 ? (
          // Single clip: no TransitionSeries needed
          <AbsoluteFill>
            {resolvedClips[0].type === "video" ? (
              <OffthreadVideo
                src={staticFile(resolvedClips[0].src)}
                volume={0}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: "center 45%",
                }}
              />
            ) : resolvedClips[0].movement ? (
              <KenBurnsImage
                src={staticFile(resolvedClips[0].src)}
                movement={resolvedClips[0].movement}
                durationInFrames={resolvedClips[0].durationInFrames}
              />
            ) : (
              <Img
                src={staticFile(resolvedClips[0].src)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: "center 45%",
                }}
              />
            )}
          </AbsoluteFill>
        ) : resolvedClips.length > 1 ? (
          <TransitionSeries>
            {resolvedClips.flatMap((clip, idx) => {
              const isLast = idx === resolvedClips.length - 1;
              const elements: React.ReactNode[] = [];

              elements.push(
                <TransitionSeries.Sequence key={`clip-${idx}`} durationInFrames={clip.durationInFrames}>
                  <AbsoluteFill>
                    {/* Scene Type branching (Crime Visual Contract) */}
                    {clip.sceneType === "context_graphic" && clip.graphicConfig ? (
                      <ContextGraphicScene
                        title={clip.graphicConfig.title || ""}
                        subtitle={clip.graphicConfig.subtitle}
                        imageUrl={clip.graphicConfig.image_url ? staticFile(clip.graphicConfig.image_url) : undefined}
                        datetime={clip.graphicConfig.datetime}
                        fontFamily={bodyFontFamily}
                      />
                    ) : clip.sceneType === "impact_cut" && clip.impactText ? (
                      <ImpactCutScene
                        text={clip.impactText}
                        color={clip.impactColor || "#FFC947"}
                        fontFamily={bodyFontFamily}
                      />
                    ) : clip.type === "video" ? (
                      <OffthreadVideo
                        src={staticFile(clip.src)}
                        volume={0}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          objectPosition: "center 45%",
                        }}
                      />
                    ) : clip.movement ? (
                      <KenBurnsImage
                        src={staticFile(clip.src)}
                        movement={clip.movement}
                        durationInFrames={clip.durationInFrames}
                      />
                    ) : (
                      <Img
                        src={staticFile(clip.src)}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                          objectPosition: "center 45%",
                        }}
                      />
                    )}
                    {/* Speaker Subtitle overlay (real_footage scenes) */}
                    {clip.sceneType === "real_footage" && clip.speakerLines && clip.speakerLines.length > 0 && (
                      <SpeakerSubtitle
                        speakerLines={clip.speakerLines}
                        currentTimeMs={currentTimeMs}
                        fontFamily={bodyFontFamily}
                      />
                    )}
                    {/* Phase 42 — Bracket action caption (real_footage gray overlay at bottom 25%) */}
                    {clip.sceneType === "real_footage" && clip.bracketCaption && (
                      <BracketCaption
                        text={clip.bracketCaption}
                        startMs={clip.bracketCaptionStartMs}
                        endMs={clip.bracketCaptionEndMs}
                      />
                    )}
                  </AbsoluteFill>
                </TransitionSeries.Sequence>
              );

              // Add transition between clips (not after the last one)
              if (!isLast && transitionType !== "none") {
                // Phase 7: per-clip transition (clip.transition > global transitionType)
                const clipTransition = clip.transition || transitionType;
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const getTransitionConfig = (tt: string): { p: any; dur: number } => {
                  switch (tt) {
                    case "glitch":       return { p: glitch({ intensity: 0.8 }),            dur: 20 };
                    case "pixelate":     return { p: pixelate({ maxBlockSize: 60 }),         dur: 20 };
                    case "rgbSplit":     return { p: rgbSplit({ direction: "horizontal" }),  dur: 20 };
                    case "lightLeak":    return { p: lightLeak({ temperature: "warm" }),     dur: 35 };
                    case "clockWipe":    return { p: clockWipe(),                            dur: 25 };
                    case "zoomBlur":     return { p: zoomBlur({ direction: "in" }),          dur: 20 };
                    case "checkerboard": return { p: checkerboard({ pattern: "diagonal" }),  dur: 25 };
                    case "fade":         return { p: fade(),                                 dur: 15 };
                    case "cut":
                    default:             return { p: fade(),                                 dur: 1  };
                  }
                };
                const { p: presentation, dur } = getTransitionConfig(clipTransition);
                elements.push(
                  <TransitionSeries.Transition
                    key={`transition-${idx}`}
                    presentation={presentation}
                    timing={linearTiming({ durationInFrames: dur })}
                  />
                );
              }

              return elements;
            })}
          </TransitionSeries>
        ) : null}
      </div>

      {/* ════════ WORD HIGHLIGHT SUBTITLES (instant switch, no fade) ════════ */}
      {currentSub && (() => {
        return (
          <div
            style={{
              position: "absolute",
              top: subY,
              left: 40,
              right: 40,
              zIndex: 10,
              display: "flex",
              justifyContent: "center",
              gap: isJapanese ? 0 : 12,
            }}
          >
            {currentSub.cue.words.map((word, i) => {
              const isHighlighted = i === currentSub.cue.highlightIndex;
              return (
                <span
                  key={`${currentSub.cue.startMs}-${i}`}
                  style={{
                    fontSize: subtitleFontSize,
                    fontWeight: 400,
                    fontFamily: subFontFamily,
                    color: isHighlighted ? subtitleHighlightColor : "#FFFFFF",
                    textShadow: titleShadow(5),
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        );
      })()}

      {/* ════════ BOTTOM BLACK BAR ════════ */}
      <div
        style={{
          position: "absolute",
          top: TOP_BAR_H + VIDEO_H,
          left: 0,
          width: CANVAS_W,
          height: BOTTOM_BAR_H,
          backgroundColor: "#0a0a0a",
          background: SUBTLE_PATTERN,
          zIndex: 5,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          paddingTop: 20,
        }}
      >
        {/* Description (요약 텍스트) */}
        {description && (
          <div
            style={{
              fontSize: 24,
              color: "rgba(255,255,255,0.55)",
              textAlign: "center",
              padding: "0 220px",
              lineHeight: 1.4,
              marginBottom: 14,
            }}
          >
            {description}
          </div>
        )}

        {/* Separator line */}
        <div
          style={{
            width: 140,
            height: 2,
            backgroundColor: "rgba(255,255,255,0.2)",
            marginBottom: 14,
          }}
        />

        {/* Channel name */}
        <div
          style={{
            fontSize: 52,
            fontWeight: 800,
            color: "#FFFFFF",
            letterSpacing: 10,
            marginBottom: 14,
          }}
        >
          {channelName}
        </div>

        {/* Subscribe / Like with decorative accents */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 20,
            marginBottom: 10,
            width: "100%",
            padding: "0 40px",
          }}
        >
          {/* Left decorative line */}
          <div style={{ flex: 1, height: 1, background: `linear-gradient(to right, transparent, ${accentColor}40)` }} />
          <span style={{ fontSize: 40, fontWeight: 800, color: accentColor }}>
            {subscribeText}
          </span>
          <span style={{ fontSize: 32, color: "rgba(255,255,255,0.35)" }}>|</span>
          <span style={{ fontSize: 40, fontWeight: 800, color: accentColor }}>
            {likeText}
          </span>
          {/* Right decorative line */}
          <div style={{ flex: 1, height: 1, background: `linear-gradient(to left, transparent, ${accentColor}40)` }} />
        </div>

        {/* Hashtags */}
        {hashtags && (
          <div
            style={{
              fontSize: 22,
              color: "rgba(255,255,255,0.4)",
              letterSpacing: 2,
            }}
          >
            {hashtags}
          </div>
        )}

        {/* PART badge (좌측 하단 바 내부) */}
        {seriesPart && seriesTotal && (
          <div
            style={{
              position: "absolute",
              left: 32,
              top: "50%",
              transform: "translateY(-50%)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 4,
              padding: "14px 24px",
              border: "3px solid rgba(255, 208, 0, 0.9)",
              borderRadius: 12,
              background: "rgba(0,0,0,0.3)",
            }}
          >
            <div
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: "rgba(255,255,255,0.85)",
                letterSpacing: 3,
                marginBottom: 2,
              }}
            >
              PART
            </div>
            <div
              style={{
                fontSize: 68,
                fontWeight: 900,
                color: "#FFD000",
                lineHeight: 0.9,
              }}
            >
              {seriesPart}
            </div>
            <div
              style={{
                fontSize: 18,
                fontWeight: 600,
                color: "rgba(255,255,255,0.55)",
              }}
            >
              of {seriesTotal}
            </div>
          </div>
        )}

        {/* Total series label (우측 하단 바 내부) */}
        {seriesPart && seriesTotal && (
          <div
            style={{
              position: "absolute",
              right: 32,
              top: "50%",
              transform: "translateY(-50%)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
            }}
          >
            <div
              style={{
                fontSize: 22,
                fontWeight: 700,
                color: "rgba(255,255,255,0.55)",
                letterSpacing: 4,
              }}
            >
              TOTAL
            </div>
            <div
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: "rgba(255,255,255,0.9)",
                letterSpacing: 1,
              }}
            >
              {seriesTotal}부작
            </div>
          </div>
        )}
      </div>

      {/* ════════ AUDIO (narration) ════════ */}
      <Audio src={staticFile(audioSrc)} />

      {/* ════════ BGM with voice ducking ════════ */}
      {bgmSrc && (
        <Audio
          src={staticFile(bgmSrc)}
          volume={(f) => {
            const timeMs = (f / fps) * 1000;
            const base = bgmVolume;
            const ducked = base * 0.25;
            const FADE_MS = 500;

            let inNarration = false;
            let closestDist = Infinity;

            for (const sub of subtitles) {
              if (timeMs >= sub.startMs && timeMs <= sub.endMs) {
                inNarration = true;
                break;
              }
              closestDist = Math.min(
                closestDist,
                Math.abs(timeMs - sub.startMs),
                Math.abs(timeMs - sub.endMs),
              );
            }

            if (inNarration) return ducked;
            if (closestDist <= FADE_MS) {
              return ducked + (base - ducked) * (closestDist / FADE_MS);
            }
            return base;
          }}
        />
      )}
    </AbsoluteFill>
  );
};
