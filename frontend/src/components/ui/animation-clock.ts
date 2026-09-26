const FRAME_INTERVAL = 1000 / 30;
const REFERENCE_FRAME = 1000 / 60;

export function createAnimationClock() {
  let lastFrame: number | undefined;
  return {
    tick(now: number): number | null {
      if (lastFrame === undefined) { lastFrame = now; return 0; }
      const elapsed = now - lastFrame;
      if (elapsed < FRAME_INTERVAL) return null;
      lastFrame = now;
      return Math.min(elapsed / REFERENCE_FRAME, 3);
    },
    reset() { lastFrame = undefined; },
  };
}
