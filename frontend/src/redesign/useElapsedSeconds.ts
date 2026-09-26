import { useEffect, useState } from 'react';

export function useElapsedSeconds(startedAt?: number) {
  const elapsed = () => startedAt === undefined ? 0 : Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  const [seconds, setSeconds] = useState(elapsed);

  useEffect(() => {
    if (startedAt === undefined) return;
    let timer: ReturnType<typeof setInterval> | undefined;
    const tick = () => setSeconds(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    const sync = () => {
      clearInterval(timer);
      timer = undefined;
      if (document.hidden) return;
      tick();
      timer = setInterval(tick, 1000);
    };
    sync();
    document.addEventListener('visibilitychange', sync);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', sync); };
  }, [startedAt]);

  return seconds;
}
