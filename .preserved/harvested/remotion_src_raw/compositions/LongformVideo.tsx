/**
 * LongformVideo — 16:9 longform video composition (13-18 min)
 *
 * Design docs:
 *   - longform/PIPELINE.md lines 73-78 (Stage 5: Render)
 *   - longform/SCRIPT_SKILL.md lines 45-66 (DialogueBox)
 *   - longform/config/channels.yaml incidents.longform
 *
 * Resolution: 1920x1080, 30fps
 * Layout: Fullscreen video + chapter badge + dialogue box + progress bar + vignette
 */
import React, { useMemo } from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  Audio,
  Img,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
  interpolate,
  Easing,
} from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { z } from "zod";
import { bodyFont } from "../lib/fonts";
import {
  DialogueBox,
  ChapterBadge,
  ProgressBar,
  VignetteOverlay,
} from "../components/longform";
import type { DialogueCue } from "../components/longform";

// ─── Layout Constants (16:9) ────────────────────────────────────────────

const CANVAS_W = 1920;
const CANVAS_H = 1080;

// ─── Schema ─────────────────────────────────────────────────────────────

const longformClipSchema = z.object({
  type: z.enum(["video", "image"]),
  src: z.string(),
  durationInFrames: z.number(),
  movement: z.enum(["zoom_in", "zoom_out", "pan_left", "pan_right"]).optional(),
  transition: z.enum([
    "cut", "fade", "glitch", "rgbSplit", "zoomBlur",
    "lightLeak", "clockWipe", "pixelate", "checkerboard",
  ]).optional(),
});

const longformChapterSchema = z.object({
  id: z.string(),
  act: z.number(),
  title: z.string(),
  startFrame: z.number(),
  durationFrames: z.number(),
});

const longformSubCueSchema = z.object({
  startMs: z.number(),
  endMs: z.number(),
  words: z.array(z.string()),
  highlightIndex: z.number(),
  speaker: z.string().optional(),
  speakerColor: z.string().optional(),
});

export const longformVideoSchema = z.object({
  clips: z.array(longformClipSchema),
  audioSrc: z.string(),
  bgmSrc: z.string().optional(),
  bgmVolume: z.number().min(0).max(1).optional(),

  chapters: z.array(longformChapterSchema),
  subtitleCues: z.array(longformSubCueSchema),

  channelName: z.string(),
  channelLogoSrc: z.string().optional(),
  detectivePortraitSrc: z.string().optional(),
  assistantPortraitSrc: z.string().optional(),

  accentColor: z.string().optional(),
  durationInFrames: z.number(),

  // Phase 46 — chunked mode props (D-46-35)
  chunkMode: z.boolean().optional(),
  chunkIndex: z.number().int().min(1).max(4).optional(),
});

export type LongformVideoProps = z.infer<typeof longformVideoSchema>;

// ─── Ken Burns Image (reused from ShortsVideo) ─────────────────────────

type KenBurnsMovement = "zoom_in" | "zoom_out" | "pan_left" | "pan_right";

const KenBurnsImage: React.FC<{
  src: string;
  movement: KenBurnsMovement;
  durationInFrames: number;
}> = ({ src, movement, durationInFrames }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    easing: Easing.bezier(0.25, 0.1, 0.25, 1),
    extrapolateRight: "clamp",
  });

  const transforms: Record<KenBurnsMovement, { scale: number; x: number; y: number }> = {
    zoom_in:   { scale: 1 + progress * 0.12,   x: 0,              y: 0 },
    zoom_out:  { scale: 1.12 - progress * 0.12, x: 0,              y: 0 },
    pan_left:  { scale: 1.08,                    x: progress * -60, y: 0 },
    pan_right: { scale: 1.08,                    x: progress * 60,  y: 0 },
  };

  const t = transforms[movement];

  return (
    <Img
      src={src}
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        objectPosition: "center center",
        transform: `scale(${t.scale}) translate(${t.x}px, ${t.y}px)`,
      }}
    />
  );
};

// ─── Component ──────────────────────────────────────────────────────────

export const LongformVideo: React.FC<LongformVideoProps> = ({
  clips,
  audioSrc,
  bgmSrc,
  bgmVolume = 0.15,
  chapters,
  subtitleCues,
  channelName,
  channelLogoSrc,
  detectivePortraitSrc,
  assistantPortraitSrc,
  accentColor = "#E53E3E",
  durationInFrames: totalDuration,
  chunkMode,
  chunkIndex,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeMs = (frame / fps) * 1000;

  // ── Current subtitle cue ──
  const currentDialogueCue: DialogueCue | null = useMemo(() => {
    const cue = subtitleCues.find(
      (s) => currentTimeMs >= s.startMs && currentTimeMs < s.endMs,
    );
    if (!cue) return null;
    return {
      startMs: cue.startMs,
      endMs: cue.endMs,
      words: cue.words,
      highlightIndex: cue.highlightIndex,
      speaker: cue.speaker || "detective",
      speakerColor: cue.speakerColor || "#FFFFFF",
    };
  }, [subtitleCues, currentTimeMs]);

  // ── Current chapter (for badge) ──
  const currentChapter = useMemo(() => {
    return chapters.find(
      (ch) => frame >= ch.startFrame && frame < ch.startFrame + ch.durationFrames,
    );
  }, [chapters, frame]);

  // ── BGM volume ducking (narration present → duck to 25%) ──
  const bgmDuckedVolume = useMemo(() => {
    if (!bgmSrc) return 0;
    const baseVol = bgmVolume;
    // Check if we're in a narration segment
    const inNarration = subtitleCues.some(
      (s) => currentTimeMs >= s.startMs - 200 && currentTimeMs <= s.endMs + 200,
    );
    return inNarration ? baseVol * 0.25 : baseVol;
  }, [bgmSrc, bgmVolume, subtitleCues, currentTimeMs]);

  // ── Gentle fade-in ──
  const fadeIn = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a0a",
        fontFamily: bodyFont.fontFamily,
        opacity: fadeIn,
      }}
    >
      {/* ═══ FULLSCREEN VIDEO AREA ═══ */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: CANVAS_W,
          height: CANVAS_H,
          overflow: "hidden",
        }}
      >
        {clips.length === 1 ? (
          <AbsoluteFill>
            {clips[0].type === "video" ? (
              <OffthreadVideo
                src={staticFile(clips[0].src)}
                volume={0}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : clips[0].movement ? (
              <KenBurnsImage
                src={staticFile(clips[0].src)}
                movement={clips[0].movement}
                durationInFrames={clips[0].durationInFrames}
              />
            ) : (
              <Img
                src={staticFile(clips[0].src)}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            )}
          </AbsoluteFill>
        ) : clips.length > 1 ? (
          <TransitionSeries>
            {clips.map((clip, i) => {
              const transitionDuration = 15; // 0.5s transition
              return (
                <React.Fragment key={`clip-${i}`}>
                  <TransitionSeries.Sequence durationInFrames={clip.durationInFrames}>
                    <AbsoluteFill>
                      {clip.type === "video" ? (
                        <OffthreadVideo
                          src={staticFile(clip.src)}
                          volume={0}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
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
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      )}
                    </AbsoluteFill>
                  </TransitionSeries.Sequence>
                  {i < clips.length - 1 && (
                    <TransitionSeries.Transition
                      presentation={fade()}
                      timing={linearTiming({ durationInFrames: transitionDuration })}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </TransitionSeries>
        ) : null}
      </div>

      {/* ═══ VIGNETTE OVERLAY ═══ */}
      <VignetteOverlay
        canvasWidth={CANVAS_W}
        canvasHeight={CANVAS_H}
        intensity={0.5}
      />

      {/* ═══ CHANNEL LOGO (top-left) ═══ */}
      <div
        style={{
          position: "absolute",
          top: 20,
          left: 24,
          display: "flex",
          alignItems: "center",
          gap: 10,
          zIndex: 15,
          opacity: 0.85,
        }}
      >
        {channelLogoSrc && (
          <Img
            src={staticFile(channelLogoSrc)}
            style={{ width: 40, height: 40, borderRadius: "50%" }}
          />
        )}
        <div
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: "#FFFFFF",
            letterSpacing: 2,
            textShadow: "0 1px 6px rgba(0,0,0,0.8)",
          }}
        >
          {channelName}
        </div>
      </div>

      {/* ═══ CHAPTER BADGE (top-right) ═══ */}
      {currentChapter && (
        <ChapterBadge
          act={currentChapter.act}
          title={currentChapter.title}
          startFrame={currentChapter.startFrame}
          durationFrames={currentChapter.durationFrames}
          accentColor={accentColor}
        />
      )}

      {/* ═══ DIALOGUE BOX (bottom, game-style) ═══ */}
      <DialogueBox
        cue={currentDialogueCue}
        detectivePortraitSrc={detectivePortraitSrc}
        assistantPortraitSrc={assistantPortraitSrc}
        canvasWidth={CANVAS_W}
        canvasHeight={CANVAS_H}
      />

      {/* ═══ PROGRESS BAR (bottom edge) ═══ */}
      <ProgressBar canvasWidth={CANVAS_W} accentColor={accentColor} />

      {/* ═══ AUDIO ═══ */}
      <Audio src={staticFile(audioSrc)} volume={1} />
      {/* Phase 46: BGM only in non-chunked mode (D-46-35) */}
      {!chunkMode && bgmSrc && (
        <Audio src={staticFile(bgmSrc)} volume={bgmDuckedVolume} />
      )}
    </AbsoluteFill>
  );
};
