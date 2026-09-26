import { useEffect } from 'react';

export default function AmbientBackground() {
  useEffect(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const pointer = window.matchMedia('(hover: hover) and (pointer: fine)');
    let frame = 0;
    let active: HTMLElement | null = null;
    let x = 0;
    let y = 0;
    const clear = () => {
      active?.removeAttribute('data-spotlight');
      active = null;
      cancelAnimationFrame(frame);
      frame = 0;
    };
    const move = (event: PointerEvent) => {
      if (motion.matches || !pointer.matches || event.pointerType === 'touch') { clear(); return; }
      const target = event.target instanceof Element ? event.target.closest<HTMLElement>('.fg-spotlight') : null;
      if (target !== active) { clear(); active = target; }
      if (!active) return;
      x = event.clientX;
      y = event.clientY;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        if (!active) return;
        const bounds = active.getBoundingClientRect();
        active.style.setProperty('--spotlight-x', `${x - bounds.left}px`);
        active.style.setProperty('--spotlight-y', `${y - bounds.top}px`);
        active.setAttribute('data-spotlight', 'active');
      });
    };
    document.addEventListener('pointermove', move, { passive: true });
    document.addEventListener('pointerleave', clear);
    window.addEventListener('blur', clear);
    motion.addEventListener('change', clear);
    return () => {
      clear();
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerleave', clear);
      window.removeEventListener('blur', clear);
      motion.removeEventListener('change', clear);
    };
  }, []);

  return <div className="fg-ambient" aria-hidden="true">
    <div className="fg-ambient-dots" />
    <div className="fg-ambient-orb fg-ambient-cyan" />
    <div className="fg-ambient-orb fg-ambient-violet" />
    <div className="fg-ambient-orb fg-ambient-emerald" />
  </div>;
}
