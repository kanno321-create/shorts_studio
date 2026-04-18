/**
 * Pixelate Transition
 *
 * Digital pixelation/mosaic dissolving into blocks.
 * Randomized block reveals + glitch artifacts.
 *
 * Best for: humor channel (retro/gaming/digital)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, random } from 'remotion';

export type PixelateProps = {
  maxBlockSize?: number;
  gridSize?: number;
  scanlines?: boolean;
  glitchArtifacts?: boolean;
  randomness?: number;
};

const getCellRandom = (row: number, col: number, seed: number): number => {
  return random(`cell-${row}-${col}-${seed}`);
};

const PixelatePresentation: React.FC<
  TransitionPresentationComponentProps<PixelateProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    maxBlockSize = 60,
    gridSize = 12,
    scanlines = true,
    glitchArtifacts = true,
    randomness = 0.8,
  } = passedProps;

  const seed = 42;

  const progress = presentationDirection === 'exiting'
    ? 1 - presentationProgress
    : presentationProgress;

  const pixelIntensity = useMemo(() => {
    return interpolate(progress, [0, 0.4, 0.6, 1], [0, 1, 1, 0], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
  }, [progress]);

  const blockSize = useMemo(() => {
    return Math.max(8, Math.round(maxBlockSize * pixelIntensity));
  }, [maxBlockSize, pixelIntensity]);

  const blurAmount = pixelIntensity * (maxBlockSize / 2.5);

  const opacity = presentationDirection === 'exiting'
    ? interpolate(presentationProgress, [0, 0.6, 1], [1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
    : interpolate(presentationProgress, [0, 0.4, 1], [0, 1, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const cells = useMemo(() => {
    const result: Array<{ row: number; col: number; revealOrder: number; hueShift: number }> = [];
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        const baseOrder = (row + col) / (gridSize * 2);
        const randOffset = getCellRandom(row, col, seed) * randomness;
        result.push({
          row, col,
          revealOrder: baseOrder * (1 - randomness) + randOffset,
          hueShift: getCellRandom(row, col, seed + 1) * 30 - 15,
        });
      }
    }
    return result;
  }, [gridSize, randomness, seed]);

  const cellSize = 100 / gridSize;

  const glitchOffset = useMemo(() => {
    if (!glitchArtifacts || pixelIntensity < 0.3) return { x: 0, y: 0 };
    const i = (pixelIntensity - 0.3) / 0.7;
    return {
      x: Math.sin(progress * Math.PI * 8) * i * 15,
      y: Math.cos(progress * Math.PI * 6) * i * 8,
    };
  }, [glitchArtifacts, pixelIntensity, progress]);

  const shouldApplyEffect = pixelIntensity > 0.05;

  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      <AbsoluteFill style={{
        opacity,
        filter: shouldApplyEffect ? `blur(${blurAmount}px) saturate(140%) contrast(120%)` : undefined,
        transform: glitchArtifacts && pixelIntensity > 0.5
          ? `translate(${glitchOffset.x}px, ${glitchOffset.y}px)` : undefined,
      }}>
        {children}
      </AbsoluteFill>

      {shouldApplyEffect && (
        <AbsoluteFill style={{ pointerEvents: 'none' }}>
          {cells.map(({ row, col, revealOrder, hueShift }) => {
            const cellProgress = interpolate(
              pixelIntensity,
              [revealOrder * 0.5, revealOrder * 0.5 + 0.5],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            if (cellProgress < 0.1) return null;
            return (
              <div key={`${row}-${col}`} style={{
                position: 'absolute',
                left: `${col * cellSize}%`, top: `${row * cellSize}%`,
                width: `${cellSize}%`, height: `${cellSize}%`,
                backgroundColor: `hsla(${hueShift + 180}, 50%, 50%, ${cellProgress * 0.7 * 0.15})`,
                border: `1px solid rgba(0,0,0,${cellProgress * 0.7})`,
                boxSizing: 'border-box',
              }} />
            );
          })}
        </AbsoluteFill>
      )}

      {shouldApplyEffect && blockSize >= 8 && (
        <AbsoluteFill style={{
          opacity: pixelIntensity * 0.8,
          backgroundImage: `linear-gradient(to right, rgba(0,0,0,0.9) 2px, transparent 2px), linear-gradient(to bottom, rgba(0,0,0,0.9) 2px, transparent 2px)`,
          backgroundSize: `${blockSize}px ${blockSize}px`,
          pointerEvents: 'none',
        }} />
      )}

      {scanlines && pixelIntensity > 0.15 && (
        <AbsoluteFill style={{
          opacity: pixelIntensity * 0.5,
          backgroundImage: `repeating-linear-gradient(0deg, transparent 0px, transparent 3px, rgba(0,0,0,0.6) 3px, rgba(0,0,0,0.6) 6px)`,
          pointerEvents: 'none',
        }} />
      )}
    </AbsoluteFill>
  );
};

export const pixelate = (
  props: PixelateProps = {}
): TransitionPresentation<PixelateProps> => {
  return { component: PixelatePresentation, props };
};
