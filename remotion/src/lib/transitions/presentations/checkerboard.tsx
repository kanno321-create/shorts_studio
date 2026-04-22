// Ported from .preserved/harvested/remotion_src_raw — Phase 16-02
// DO NOT modify layout constants (TOP_BAR_H=320, BOTTOM_BAR_H=333) — DESIGN_SPEC.md 기반
/**
 * Checkerboard Transition
 *
 * Grid of squares with various reveal patterns.
 * Classic video editing with modern flexibility.
 *
 * Best for: general purpose (playful/retro)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, Easing } from 'remotion';

export type CheckerboardPattern =
  | 'sequential' | 'random' | 'diagonal' | 'alternating'
  | 'spiral' | 'rows' | 'columns' | 'center-out' | 'corners-in';

export type CheckerboardProps = {
  gridSize?: number;
  pattern?: CheckerboardPattern;
  stagger?: number;
  squareAnimation?: 'fade' | 'scale' | 'flip';
  easing?: (t: number) => number;
};

const generateOrder = (
  row: number, col: number, gridSize: number, pattern: CheckerboardPattern, seed: number
): number => {
  const total = gridSize * gridSize;
  const index = row * gridSize + col;
  const centerRow = (gridSize - 1) / 2;
  const centerCol = (gridSize - 1) / 2;

  switch (pattern) {
    case 'sequential': return index / total;
    case 'random': {
      const hash = Math.sin(seed + index * 9999) * 10000;
      return hash - Math.floor(hash);
    }
    case 'diagonal': return (row + col) / (gridSize * 2 - 2);
    case 'alternating': {
      const isAlt = (row + col) % 2 === 0;
      const base = (row + col) / (gridSize * 2 - 2);
      return isAlt ? base * 0.5 : 0.5 + base * 0.5;
    }
    case 'spiral': {
      const dist = Math.max(Math.abs(row - centerRow), Math.abs(col - centerCol));
      const maxDist = Math.max(centerRow, centerCol);
      const ring = dist / maxDist;
      const angle = Math.atan2(row - centerRow, col - centerCol);
      return ring * 0.8 + ((angle + Math.PI) / (2 * Math.PI)) * 0.2;
    }
    case 'rows': return row / (gridSize - 1);
    case 'columns': return col / (gridSize - 1);
    case 'center-out': {
      const d = Math.sqrt(Math.pow(row - centerRow, 2) + Math.pow(col - centerCol, 2));
      return d / (Math.sqrt(2) * gridSize / 2);
    }
    case 'corners-in': {
      const d = Math.sqrt(Math.pow(row - centerRow, 2) + Math.pow(col - centerCol, 2));
      return 1 - d / (Math.sqrt(2) * gridSize / 2);
    }
    default: return index / total;
  }
};

const CheckerboardPresentation: React.FC<
  TransitionPresentationComponentProps<CheckerboardProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    gridSize = 8,
    pattern = 'diagonal',
    stagger = 0.6,
    squareAnimation = 'fade',
    easing = Easing.out(Easing.cubic),
  } = passedProps;

  const isEntering = presentationDirection === 'entering';
  const progress = isEntering ? presentationProgress : 1 - presentationProgress;
  const seed = 12345;

  const cells = useMemo(() => {
    const result: Array<{ row: number; col: number; order: number }> = [];
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        result.push({ row, col, order: generateOrder(row, col, gridSize, pattern, seed) });
      }
    }
    return result;
  }, [gridSize, pattern, seed]);

  const cellSize = 100 / gridSize;

  return (
    <AbsoluteFill>
      {!isEntering && <AbsoluteFill>{children}</AbsoluteFill>}

      <AbsoluteFill style={{ overflow: 'hidden' }}>
        {cells.map(({ row, col, order }) => {
          const cellStart = order * stagger;
          const cellEnd = cellStart + (1 - stagger);
          const cellProgress = interpolate(progress, [cellStart, cellEnd], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          });
          const easedProgress = easing(cellProgress);

          let cellOpacity = 1;
          let scale = 1;
          let rotateY = 0;

          switch (squareAnimation) {
            case 'fade': cellOpacity = easedProgress; break;
            case 'scale': scale = easedProgress; cellOpacity = easedProgress > 0 ? 1 : 0; break;
            case 'flip': rotateY = interpolate(easedProgress, [0, 1], [90, 0]); cellOpacity = easedProgress > 0.1 ? 1 : 0; break;
          }

          if (!isEntering) {
            cellOpacity = 1 - cellOpacity;
            scale = scale === 0 ? 1 : 2 - scale;
            rotateY = -rotateY;
          }

          return (
            <div key={`${row}-${col}`} style={{
              position: 'absolute',
              left: `${col * cellSize}%`, top: `${row * cellSize}%`,
              width: `${cellSize}%`, height: `${cellSize}%`,
              overflow: 'hidden',
              opacity: cellOpacity,
              transform: `scale(${scale}) perspective(500px) rotateY(${rotateY}deg)`,
              transformOrigin: 'center center',
            }}>
              {isEntering && (
                <div style={{
                  position: 'absolute',
                  left: `${-col * 100}%`, top: `${-row * 100}%`,
                  width: `${gridSize * 100}%`, height: `${gridSize * 100}%`,
                }}>
                  {children}
                </div>
              )}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const checkerboard = (
  props: CheckerboardProps = {}
): TransitionPresentation<CheckerboardProps> => {
  return { component: CheckerboardPresentation, props };
};
