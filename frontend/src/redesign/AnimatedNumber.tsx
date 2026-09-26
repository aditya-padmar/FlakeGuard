import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';

/** Only the visual numerator rolls up; assistive technology gets the real value. */
export function AnimatedNumber({ value, denominator }: { value: number | null; denominator?: number }) {
  const reducedMotion = useReducedMotion();
  const [frame, setFrame] = useState({ target: value, value: 0 });
  useEffect(() => {
    if (reducedMotion !== false || value === null || value === 0) return;
    let request = 0;
    let started: number | undefined;
    const tick = (now: number) => {
      started ??= now;
      const progress = Math.min(1, (now - started) / 700);
      setFrame({ target: value, value: Math.round(value * (1 - (1 - progress) ** 3)) });
      if (progress < 1) request = requestAnimationFrame(tick);
    };
    request = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(request);
  }, [value, reducedMotion]);
  const format = (number: number | null) => number === null ? '—' : number.toLocaleString();
  const suffix = denominator === undefined ? '' : ` / ${denominator.toLocaleString()}`;
  const visible = reducedMotion !== false || value === null || value === 0 ? value : frame.target === value ? frame.value : 0;
  return <><span aria-hidden="true">{format(visible)}{suffix}</span><span className="fg-dashboard-sr-only">{value === null ? 'Not reported' : format(value)}{suffix}</span></>;
}
