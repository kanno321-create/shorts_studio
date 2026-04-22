// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
/**
 * Glitch Transition
 *
 * Digital distortion: horizontal slice displacement, RGB channel separation,
 * scan line artifacts for authentic glitch aesthetic.
 *
 * Best for: humor channel (tech/cyberpunk/edgy)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo, useState } from 'react';
import { AbsoluteFill, random, interpolate, useCurrentFrame } from 'remotion';

export type GlitchProps = {
  intensity?: number;
  slices?: number;
  rgbShift?: boolean;
  scanLines?: boolean;
};

const GlitchPresentation: React.FC<
  TransitionPresentationComponentProps<GlitchProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    intensity = 0.8,
    slices = 8,
    rgbShift = true,
    scanLines = true,
  } = passedProps;

  const [filterId] = useState(() => `glitch-${String(random(null)).slice(2, 10)}`);
  const frame = useCurrentFrame();

  const glitchIntensity = useMemo(() => {
    const peak = interpolate(presentationProgress, [0, 0.5, 1], [0, 1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return peak * intensity;
  }, [presentationProgress, intensity]);

  const flickerFrame = Math.floor(frame / 2);

  const sliceOffsets = useMemo(() => {
    return Array.from({ length: slices }, (_, i) => {
      const seed = `glitch-slice-${i}-${flickerFrame}`;
      const baseOffset = (random(seed) - 0.5) * 200 * glitchIntensity;
      const jumpSeed = `jump-${i}-${flickerFrame}`;
      const jump = random(jumpSeed) > 0.4 ? (random(`${jumpSeed}-dir`) > 0.5 ? 2.5 : -2.5) : 1;
      return baseOffset * jump;
    });
  }, [slices, glitchIntensity, flickerFrame]);

  const rgbShiftAmount = rgbShift ? glitchIntensity * 25 : 0;
  const rgbFlicker = random(`rgb-${flickerFrame}`) > 0.3 ? 1 : 0.3;

  const opacity = presentationDirection === 'exiting'
    ? interpolate(presentationProgress, [0, 1], [1, 0])
    : interpolate(presentationProgress, [0, 1], [0, 1]);

  const sliceHeight = 100 / slices;

  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <AbsoluteFill style={{ opacity }}>
        {sliceOffsets.map((offset, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              top: `${i * sliceHeight}%`,
              left: 0,
              width: '100%',
              height: `${sliceHeight + 0.5}%`,
              overflow: 'hidden',
              transform: `translateX(${offset}px)`,
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${slices * 100}%`,
                transform: `translateY(-${i * (100 / slices)}%)`,
              }}
            >
              {children}
            </div>
          </div>
        ))}
      </AbsoluteFill>

      {rgbShift && glitchIntensity > 0.05 && (
        <>
          <AbsoluteFill
            style={{
              opacity: opacity * 0.6 * glitchIntensity * rgbFlicker,
              transform: `translateX(${-rgbShiftAmount}px) translateY(${(random(`rgb-y-${flickerFrame}`) - 0.5) * 10 * glitchIntensity}px)`,
              mixBlendMode: 'screen',
              filter: `url(#${filterId}-red)`,
            }}
          >
            {children}
          </AbsoluteFill>
          <AbsoluteFill
            style={{
              opacity: opacity * 0.6 * glitchIntensity * rgbFlicker,
              transform: `translateX(${rgbShiftAmount}px) translateY(${(random(`rgb-y2-${flickerFrame}`) - 0.5) * 10 * glitchIntensity}px)`,
              mixBlendMode: 'screen',
              filter: `url(#${filterId}-cyan)`,
            }}
          >
            {children}
          </AbsoluteFill>
        </>
      )}

      {scanLines && glitchIntensity > 0.1 && (
        <AbsoluteFill
          style={{
            opacity: glitchIntensity * 0.4,
            background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.4) 2px, rgba(0,0,0,0.4) 4px)`,
            pointerEvents: 'none',
          }}
        />
      )}

      {glitchIntensity > 0.15 && (
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          {Array.from({ length: 8 }, (_, i) => {
            const blockSeed = `block-${i}-${flickerFrame}`;
            if (random(blockSeed) <= 0.4) return null;
            const x = random(`${blockSeed}-x`) * 100;
            const y = random(`${blockSeed}-y`) * 100;
            const w = 5 + random(`${blockSeed}-w`) * 40;
            const h = 1 + random(`${blockSeed}-h`) * 15;
            const c = random(`${blockSeed}-c`);
            const bgColor = c > 0.7
              ? `rgba(255,255,255,${glitchIntensity * 0.5})`
              : c > 0.4
                ? `rgba(255,0,80,${glitchIntensity * 0.6})`
                : `rgba(0,255,255,${glitchIntensity * 0.6})`;
            return (
              <div key={i} style={{
                position: 'absolute', left: `${x}%`, top: `${y}%`,
                width: `${w}%`, height: `${h}%`,
                backgroundColor: bgColor, mixBlendMode: 'screen',
              }} />
            );
          })}
        </AbsoluteFill>
      )}

      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <filter id={`${filterId}-red`}>
            <feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" />
          </filter>
          <filter id={`${filterId}-cyan`}>
            <feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0" />
          </filter>
        </defs>
      </svg>
    </AbsoluteFill>
  );
};

export const glitch = (
  props: GlitchProps = {}
): TransitionPresentation<GlitchProps> => {
  return { component: GlitchPresentation, props };
};
