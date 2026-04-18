/**
 * Shorts Naberal — Custom Transitions Library
 *
 * 7 custom transition presentations ported from digitalsamba video toolkit.
 * Use with @remotion/transitions TransitionSeries.
 *
 * Channel mapping:
 *   humor   → glitch, pixelate
 *   politics → clockWipe, zoomBlur
 *   trend   → rgbSplit, lightLeak
 *   all     → fade (from @remotion/transitions/fade), checkerboard
 *
 * Usage:
 *   import { TransitionSeries, linearTiming } from '@remotion/transitions';
 *   import { glitch, rgbSplit } from '../lib/transitions';
 *
 *   <TransitionSeries.Transition
 *     presentation={glitch({ intensity: 0.8 })}
 *     timing={linearTiming({ durationInFrames: 20 })}
 *   />
 */

export { glitch } from './presentations/glitch';
export type { GlitchProps } from './presentations/glitch';

export { rgbSplit } from './presentations/rgb-split';
export type { RgbSplitProps } from './presentations/rgb-split';

export { zoomBlur } from './presentations/zoom-blur';
export type { ZoomBlurProps } from './presentations/zoom-blur';

export { lightLeak } from './presentations/light-leak';
export type { LightLeakProps } from './presentations/light-leak';

export { clockWipe } from './presentations/clock-wipe';
export type { ClockWipeProps } from './presentations/clock-wipe';

export { pixelate } from './presentations/pixelate';
export type { PixelateProps } from './presentations/pixelate';

export { checkerboard } from './presentations/checkerboard';
export type { CheckerboardProps, CheckerboardPattern } from './presentations/checkerboard';

/**
 * Channel → transition mapping.
 * Used by the pipeline to auto-select transitions.
 */
export const CHANNEL_TRANSITIONS = {
  humor: ['glitch', 'pixelate'] as const,
  politics: ['clockWipe', 'zoomBlur'] as const,
  trend: ['rgbSplit', 'lightLeak'] as const,
} as const;

export type TransitionName =
  | 'glitch' | 'rgbSplit' | 'zoomBlur' | 'lightLeak'
  | 'clockWipe' | 'pixelate' | 'checkerboard'
  | 'fade' | 'cut' | 'none';
