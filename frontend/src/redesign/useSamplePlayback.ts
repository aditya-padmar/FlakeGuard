import { useEffect, useRef, useState } from 'react';

export function useSamplePlayback(scenarioCount: number, reducedMotion: boolean | null) {
  const previewRef = useRef<HTMLElement>(null);
  const [position, setPosition] = useState(2);
  const [visible, setVisible] = useState(false);
  const [runProgress, setRunProgress] = useState(10);
  const activeStage = position % 4;
  const scenarioIndex = Math.floor(position / 4) % scenarioCount;

  useEffect(() => {
    const element = previewRef.current;
    if (!element) return;
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!visible || reducedMotion !== false) return;
    let timer: ReturnType<typeof setInterval> | undefined;
    const sync = () => {
      clearInterval(timer);
      timer = undefined;
      if (!document.hidden) timer = setInterval(() => setPosition(previous => (previous + 1) % (scenarioCount * 4)), 2800);
    };
    sync();
    document.addEventListener('visibilitychange', sync);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', sync); };
  }, [scenarioCount, visible, reducedMotion]);

  useEffect(() => {
    if (activeStage !== 1) { setRunProgress(activeStage === 0 ? 0 : 10); return; }
    if (!visible || reducedMotion !== false) return;
    let progress = 1;
    setRunProgress(progress);
    const timer = setInterval(() => {
      if (document.hidden) return;
      progress += 1;
      setRunProgress(progress);
      if (progress === 10) clearInterval(timer);
    }, 250);
    return () => clearInterval(timer);
  }, [activeStage, visible, reducedMotion]);

  return { previewRef, activeStage, scenarioIndex, runProgress };
}
