/**
 * Light Leak Transition
 *
 * Cinematic light leak/lens flare sweeping across the scene.
 * Warmth, nostalgia, organic film quality.
 *
 * Best for: trend channel (warm/aesthetic)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, random } from 'remotion';

export type LightLeakProps = {
  temperature?: 'warm' | 'cool' | 'rainbow';
  direction?: 'left' | 'right' | 'top' | 'bottom' | 'center';
  intensity?: number;
  flareArtifacts?: boolean;
};

const LightLeakPresentation: React.FC<
  TransitionPresentationComponentProps<LightLeakProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    temperature = 'warm',
    direction = 'right',
    intensity = 0.8,
    flareArtifacts = true,
  } = passedProps;

  const progress = presentationDirection === 'exiting'
    ? 1 - presentationProgress
    : presentationProgress;

  const leakProgress = useMemo(() => {
    return interpolate(progress, [0, 0.6, 1], [0, 1, 0.2], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
  }, [progress]);

  const exposure = useMemo(() => {
    return interpolate(progress, [0, 0.4, 0.6, 1], [1, 1.3, 1.3, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
  }, [progress]);

  const opacity = presentationDirection === 'exiting'
    ? interpolate(presentationProgress, [0, 1], [1, 0])
    : interpolate(presentationProgress, [0, 1], [0, 1]);

  const getGradientColors = () => {
    switch (temperature) {
      case 'warm': return {
        primary: 'rgba(255,180,80,0.9)', secondary: 'rgba(255,120,50,0.7)', tertiary: 'rgba(255,220,150,0.5)',
      };
      case 'cool': return {
        primary: 'rgba(100,180,255,0.9)', secondary: 'rgba(150,220,255,0.7)', tertiary: 'rgba(200,240,255,0.5)',
      };
      case 'rainbow': return {
        primary: 'rgba(255,100,150,0.8)', secondary: 'rgba(255,200,100,0.6)', tertiary: 'rgba(100,200,255,0.5)',
      };
    }
  };

  const colors = getGradientColors();

  const getGradientPosition = () => {
    const pos = leakProgress * 150 - 50;
    const stops = `${colors.primary} ${pos}%, ${colors.secondary} ${pos + 20}%, ${colors.tertiary} ${pos + 40}%, transparent ${pos + 60}%`;
    switch (direction) {
      case 'left': return `linear-gradient(90deg, ${stops})`;
      case 'right': return `linear-gradient(270deg, ${stops})`;
      case 'top': return `linear-gradient(180deg, ${stops})`;
      case 'bottom': return `linear-gradient(0deg, ${stops})`;
      case 'center': return `radial-gradient(ellipse at center, ${colors.primary} ${pos * 0.5}%, ${colors.secondary} ${pos * 0.7}%, ${colors.tertiary} ${pos}%, transparent ${pos + 30}%)`;
    }
  };

  const flarePositions = useMemo(() => {
    return Array.from({ length: 5 }, (_, i) => ({
      x: random(`flare-x-${i}`) * 100,
      y: random(`flare-y-${i}`) * 100,
      size: 20 + random(`flare-size-${i}`) * 60,
      delay: random(`flare-delay-${i}`) * 0.3,
    }));
  }, []);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ opacity, filter: `brightness(${exposure})` }}>
        {children}
      </AbsoluteFill>

      <AbsoluteFill style={{
        background: getGradientPosition(),
        opacity: intensity * leakProgress,
        mixBlendMode: 'screen',
        pointerEvents: 'none',
      }} />

      <AbsoluteFill style={{
        background: `radial-gradient(ellipse at ${direction === 'left' ? '20%' : direction === 'right' ? '80%' : '50%'} 50%, ${colors.tertiary}, transparent 70%)`,
        opacity: intensity * leakProgress * 0.5,
        mixBlendMode: 'overlay',
        pointerEvents: 'none',
      }} />

      {flareArtifacts && leakProgress > 0.2 && (
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          {flarePositions.map((flare, i) => {
            const flareOpacity = interpolate(
              progress,
              [flare.delay, flare.delay + 0.3, 0.7, 1],
              [0, 0.6, 0.6, 0],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            return (
              <div key={i} style={{
                position: 'absolute', left: `${flare.x}%`, top: `${flare.y}%`,
                width: flare.size, height: flare.size, borderRadius: '50%',
                background: `radial-gradient(circle, ${temperature === 'warm' ? 'rgba(255,255,200,0.8)' : temperature === 'cool' ? 'rgba(200,240,255,0.8)' : 'rgba(255,200,255,0.8)'}, transparent)`,
                opacity: flareOpacity * intensity,
                transform: 'translate(-50%, -50%)',
                mixBlendMode: 'screen',
              }} />
            );
          })}
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

export const lightLeak = (
  props: LightLeakProps = {}
): TransitionPresentation<LightLeakProps> => {
  return { component: LightLeakPresentation, props };
};
