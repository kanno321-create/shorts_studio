/**
 * Clock Wipe Transition
 *
 * Radial wipe revealing scene like clock hands sweeping.
 * Classic, dynamic quality.
 *
 * Best for: politics channel (authoritative/dramatic)
 * Ported from digitalsamba video toolkit
 */
import type {
  TransitionPresentation,
  TransitionPresentationComponentProps,
} from '@remotion/transitions';
import React, { useMemo, useId } from 'react';
import { AbsoluteFill, interpolate } from 'remotion';

export type ClockWipeProps = {
  startAngle?: number;
  direction?: 'clockwise' | 'counterclockwise';
  segments?: number;
};

const ClockWipePresentation: React.FC<
  TransitionPresentationComponentProps<ClockWipeProps>
> = ({ children, presentationDirection, presentationProgress, passedProps }) => {
  const {
    startAngle = 0,
    direction = 'clockwise',
    segments = 1,
  } = passedProps;

  const clipId = useId().replace(/:/g, '-');

  const sweptAngle = useMemo(() => {
    const totalSweep = 360 / segments;
    return interpolate(presentationProgress, [0, 1], [0, totalSweep], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
  }, [presentationProgress, segments]);

  const isEffectivelyHidden = useMemo(() => {
    return presentationDirection === 'entering' ? sweptAngle <= 0.1 : sweptAngle >= 359.9;
  }, [presentationDirection, sweptAngle]);

  const isFullyVisible = useMemo(() => {
    return presentationDirection === 'entering' ? sweptAngle >= 359.9 : sweptAngle <= 0.1;
  }, [presentationDirection, sweptAngle]);

  const clipPath = useMemo(() => {
    const cx = 50, cy = 50, r = 75;

    if (isEffectivelyHidden) return 'M 0 0 Z';
    if (isFullyVisible) return 'M 0 0 L 100 0 L 100 100 L 0 100 Z';

    const paths: string[] = [];

    if (presentationDirection === 'entering') {
      for (let i = 0; i < segments; i++) {
        const segmentOffset = i * 360 / segments;
        const pieStart = startAngle + segmentOffset;
        const pieEnd = pieStart + (direction === 'clockwise' ? sweptAngle : -sweptAngle);
        const startRad = (pieStart - 90) * Math.PI / 180;
        const endRad = (pieEnd - 90) * Math.PI / 180;
        const x1 = cx + r * Math.cos(startRad);
        const y1 = cy + r * Math.sin(startRad);
        const x2 = cx + r * Math.cos(endRad);
        const y2 = cy + r * Math.sin(endRad);
        const largeArc = sweptAngle > 180 ? 1 : 0;
        const sweepFlag = direction === 'clockwise' ? 1 : 0;
        paths.push(`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} ${sweepFlag} ${x2} ${y2} Z`);
      }
    } else {
      const remainingAngle = (360 / segments) - sweptAngle;
      for (let i = 0; i < segments; i++) {
        const segmentOffset = i * 360 / segments;
        const pieStart = startAngle + segmentOffset + (direction === 'clockwise' ? sweptAngle : -sweptAngle);
        const pieEnd = startAngle + segmentOffset + (direction === 'clockwise' ? 360 / segments : -360 / segments);
        const startRad = (pieStart - 90) * Math.PI / 180;
        const endRad = (pieEnd - 90) * Math.PI / 180;
        const x1 = cx + r * Math.cos(startRad);
        const y1 = cy + r * Math.sin(startRad);
        const x2 = cx + r * Math.cos(endRad);
        const y2 = cy + r * Math.sin(endRad);
        const largeArc = remainingAngle > 180 ? 1 : 0;
        const sweepFlag = direction === 'clockwise' ? 1 : 0;
        paths.push(`M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} ${sweepFlag} ${x2} ${y2} Z`);
      }
    }

    return paths.join(' ');
  }, [presentationDirection, sweptAngle, startAngle, direction, segments, isEffectivelyHidden, isFullyVisible]);

  const opacity = isEffectivelyHidden ? 0 : 1;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{
        clipPath: isFullyVisible ? undefined : `url(#${clipId})`,
        WebkitClipPath: isFullyVisible ? undefined : `url(#${clipId})`,
        opacity,
      }}>
        {children}
      </AbsoluteFill>

      {!isFullyVisible && !isEffectivelyHidden && (
        <svg style={{ position: 'absolute', width: 0, height: 0 }}>
          <defs>
            <clipPath id={clipId} clipPathUnits="objectBoundingBox">
              <path d={clipPath} transform="scale(0.01)" />
            </clipPath>
          </defs>
        </svg>
      )}
    </AbsoluteFill>
  );
};

export const clockWipe = (
  props: ClockWipeProps = {}
): TransitionPresentation<ClockWipeProps> => {
  return { component: ClockWipePresentation, props };
};
