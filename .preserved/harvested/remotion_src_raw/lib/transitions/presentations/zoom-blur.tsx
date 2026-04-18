/**
 * Zoom Blur Transition
 *
 * Radial motion blur + scale for high-energy transitions.
 * Sense of speed, impact, forward momentum.
 *
 * Best for: politics channel (dramatic reveals)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type ZoomBlurProps = {
  direction?: 'in' | 'out';
  blurAmount?: number;
  scaleAmount?: number;
  origin?: 'center' | 'top' | 'bottom' | 'left' | 'right';
};

const ZoomBlurPresentation: React.FC<
  TransitionPresentationComponentProps<ZoomBlurProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    direction = 'in',
    blurAmount = 20,
    scaleAmount = 1.15,
    origin = 'center',
  } = passedProps;

  const progress = presentationDirection === 'exiting'
    ? 1 - presentationProgress
    : presentationProgress;

  const effectIntensity = useMemo(() => {
    return interpolate(progress, [0, 0.4, 1], [0, 1, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  }, [progress]);

  const scale = useMemo(() => {
    if (direction === 'in') {
      return interpolate(progress, [0, 0.5, 1], [1 / scaleAmount, scaleAmount, 1],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    }
    return interpolate(progress, [0, 0.5, 1], [scaleAmount, 1 / scaleAmount, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  }, [progress, direction, scaleAmount]);

  const blur = blurAmount * effectIntensity;

  const opacity = presentationDirection === 'exiting'
    ? interpolate(presentationProgress, [0, 1], [1, 0])
    : interpolate(presentationProgress, [0, 1], [0, 1]);

  const transformOrigin = useMemo(() => {
    switch (origin) {
      case 'top': return 'center top';
      case 'bottom': return 'center bottom';
      case 'left': return 'left center';
      case 'right': return 'right center';
      default: return 'center center';
    }
  }, [origin]);

  return (
    <AbsoluteFill style={{ overflow: 'hidden', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{
        width: '100%', height: '100%',
        transform: `scale(${scale})`,
        transformOrigin,
        filter: blur > 0.5 ? `blur(${blur}px)` : undefined,
        opacity,
      }}>
        {children}
      </div>

      {effectIntensity > 0.3 && (
        <AbsoluteFill
          style={{
            opacity: effectIntensity * 0.4,
            background: `radial-gradient(ellipse at ${origin === 'center' ? '50% 50%' : origin === 'top' ? '50% 0%' : origin === 'bottom' ? '50% 100%' : origin === 'left' ? '0% 50%' : '100% 50%'}, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0.1) 30%, transparent 70%)`,
            pointerEvents: 'none',
            mixBlendMode: 'overlay',
          }}
        />
      )}
    </AbsoluteFill>
  );
};

export const zoomBlur = (
  props: ZoomBlurProps = {}
): TransitionPresentation<ZoomBlurProps> => {
  return { component: ZoomBlurPresentation, props };
};
