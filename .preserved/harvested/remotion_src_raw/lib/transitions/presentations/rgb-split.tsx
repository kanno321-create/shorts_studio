/**
 * RGB Split Transition
 *
 * Chromatic aberration with directional displacement.
 * Modern tech aesthetic reminiscent of CRT/analog video glitches.
 *
 * Best for: trend channel (modern/energetic)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type RgbSplitProps = {
  direction?: 'horizontal' | 'vertical' | 'diagonal';
  displacement?: number;
};

const RgbSplitPresentation: React.FC<
  TransitionPresentationComponentProps<RgbSplitProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    direction = 'horizontal',
    displacement = 50,
  } = passedProps;

  const splitIntensity = useMemo(() => {
    return interpolate(presentationProgress, [0, 0.5, 1], [0, 1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }, [presentationProgress]);

  const getOffset = (multiplier: number) => {
    const offset = displacement * splitIntensity * multiplier;
    switch (direction) {
      case 'horizontal': return { x: offset, y: 0 };
      case 'vertical': return { x: 0, y: offset };
      case 'diagonal': return { x: offset * 0.7, y: offset * 0.7 };
    }
  };

  const redOffset = getOffset(-1);
  const cyanOffset = getOffset(1);

  const opacity = presentationDirection === 'exiting'
    ? interpolate(presentationProgress, [0, 1], [1, 0])
    : interpolate(presentationProgress, [0, 1], [0, 1]);

  const ghostOpacity = splitIntensity * 0.7;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>

      {splitIntensity > 0.05 && (
        <AbsoluteFill
          style={{
            opacity: opacity * ghostOpacity,
            transform: `translate(${redOffset.x}px, ${redOffset.y}px)`,
            filter: 'saturate(2) hue-rotate(-30deg) brightness(1.2)',
            mixBlendMode: 'screen',
          }}
        >
          {children}
        </AbsoluteFill>
      )}

      {splitIntensity > 0.05 && (
        <AbsoluteFill
          style={{
            opacity: opacity * ghostOpacity,
            transform: `translate(${cyanOffset.x}px, ${cyanOffset.y}px)`,
            filter: 'saturate(2) hue-rotate(150deg) brightness(1.2)',
            mixBlendMode: 'screen',
          }}
        >
          {children}
        </AbsoluteFill>
      )}

      {splitIntensity > 0.3 && (
        <AbsoluteFill
          style={{
            opacity: splitIntensity * 0.15,
            background: `repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)`,
            pointerEvents: 'none',
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const rgbSplit = (
  props: RgbSplitProps = {}
): TransitionPresentation<RgbSplitProps> => {
  return { component: RgbSplitPresentation, props };
};
