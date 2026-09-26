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
    <div className="fg-ambient-grid-plane" />
    <svg className="fg-ambient-contours" viewBox="0 0 1440 1000" preserveAspectRatio="xMidYMid slice" fill="none">
      <defs><linearGradient id="fg-contour-gradient" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#00f0ff" stopOpacity=".24" /><stop offset="1" stopColor="#8a3ffc" stopOpacity=".02" /></linearGradient></defs>
      {[0, 1, 2, 3, 4, 5].map(index => <path key={index} d={`M ${960 + index * 46} -80 C ${700 + index * 50} 220, ${1440 + index * 35} 300, ${1160 + index * 46} 640 S ${980 + index * 46} 860, ${1470 + index * 40} 1140`} stroke="url(#fg-contour-gradient)" strokeWidth="1" />)}
    </svg>
    <div className="fg-ambient-orb fg-ambient-cyan" />
    <div className="fg-ambient-orb fg-ambient-violet" />
    <div className="fg-ambient-orb fg-ambient-emerald" />
  </div>;
}
