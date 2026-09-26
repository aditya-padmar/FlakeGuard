'use client';

import { useEffect, useRef, type ReactNode } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { cn } from '@/lib/utils';
import { createAnimationClock } from './animation-clock';

export interface BeamsBackgroundProps {
  className?: string;
  children?: ReactNode;
  intensity?: 'subtle' | 'medium' | 'strong';
}

interface Beam {
  x: number;
  y: number;
  width: number;
  length: number;
  angle: number;
  speed: number;
  opacity: number;
  hue: number;
  pulse: number;
  pulseSpeed: number;
}

const opacityMap = { subtle: .7, medium: .85, strong: 1 };

function createBeam(width: number, height: number): Beam {
  return {
    x: Math.random() * width * 1.5 - width * .25,
    y: Math.random() * height - height * .9,
    width: 30 + Math.random() * 60,
    length: height * 2.5,
    angle: -35 + Math.random() * 10,
    speed: .6 + Math.random() * 1.2,
    opacity: .12 + Math.random() * .16,
    hue: 190 + Math.random() * 70,
    pulse: Math.random() * Math.PI * 2,
    pulseSpeed: .02 + Math.random() * .03,
  };
}

export function BeamsBackground({ className, children, intensity = 'strong' }: BeamsBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    let beams: Beam[] = [];
    let width = 0;
    let height = 0;
    let frame = 0;
    const clock = createAnimationClock();
    let intersecting = true;
    let disposed = false;

    const draw = (delta: number) => {
      ctx.clearRect(0, 0, width, height);
      beams.forEach((beam, index) => {
        beam.y -= beam.speed * delta;
        beam.pulse += beam.pulseSpeed * delta;
        if (beam.y + beam.length < -100) {
          const spacing = width / 3;
          beam.y = height + 100;
          beam.x = index % 3 * spacing + spacing / 2 + (Math.random() - .5) * spacing * .5;
          beam.width = 100 + Math.random() * 100;
          beam.speed = .5 + Math.random() * .4;
          beam.hue = 190 + index * 70 / beams.length;
          beam.opacity = .2 + Math.random() * .1;
        }
        ctx.save();
        ctx.translate(beam.x, beam.y);
        ctx.rotate(beam.angle * Math.PI / 180);
        ctx.globalAlpha = beam.opacity * (.8 + Math.sin(beam.pulse) * .2) * opacityMap[intensity];
        const gradient = ctx.createLinearGradient(0, 0, 0, beam.length);
        for (const [stop, strength] of [[0, 0], [.1, .5], [.4, 1], [.6, 1], [.9, .5], [1, 0]]) {
          gradient.addColorStop(stop, `hsla(${beam.hue}, 85%, 65%, ${strength})`);
        }
        ctx.fillStyle = gradient;
        ctx.fillRect(-beam.width / 2, 0, beam.width, beam.length);
        ctx.restore();
      });
    };
    const animate = (now: number) => {
      frame = 0;
      if (disposed || document.hidden || !intersecting || preference.matches) return;
      const delta = clock.tick(now);
      if (delta !== null) draw(delta);
      frame = requestAnimationFrame(animate);
    };
    const sync = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      clock.reset();
      if (disposed || !width || !height) return;
      draw(0);
      if (!document.hidden && intersecting && !preference.matches) frame = requestAnimationFrame(animate);
    };
    const resize = () => {
      width = container.clientWidth;
      height = container.clientHeight;
      if (!width || !height) return;
      // Beam coordinates stay in CSS pixels; only the drawing buffer uses DPR.
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5, Math.sqrt(2_000_000 / (width * height)));
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      beams = Array.from({ length: 30 }, () => createBeam(width, height));
      sync();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(container);
    const intersection = new IntersectionObserver(([entry]) => { intersecting = entry.isIntersecting; sync(); });
    intersection.observe(container);
    document.addEventListener('visibilitychange', sync);
    preference.addEventListener('change', sync);
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      intersection.disconnect();
      document.removeEventListener('visibilitychange', sync);
      preference.removeEventListener('change', sync);
    };
  }, [intensity]);

  return <div ref={containerRef} className={cn('relative min-h-screen w-full overflow-hidden bg-neutral-950', className)}>
    <canvas ref={canvasRef} aria-hidden="true" className="pointer-events-none absolute inset-0 h-full w-full" style={{ filter: 'blur(35px)' }} />
    <motion.div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-neutral-950/5" animate={{ opacity: reducedMotion ? .1 : [.05, .15, .05] }} transition={reducedMotion ? { duration: 0 } : { duration: 10, ease: 'easeInOut', repeat: Infinity }} style={{ backdropFilter: 'blur(35px)' }} />
    {children && <div className="relative z-10">{children}</div>}
  </div>;
}
