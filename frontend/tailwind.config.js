/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        obsidian: '#08090C', slateBase: '#0B0F17', panel: 'var(--surface)',
        signal: '#00F0FF', electric: '#0070F3', ember: '#FF5722',
        warning: '#F59E0B', trusted: '#10B981', bob: '#8A3FFC',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      backgroundImage: {
        dots: 'radial-gradient(#ffffff0a 1px, transparent 1px)',
        grid: 'linear-gradient(#ffffff06 1px, transparent 1px), linear-gradient(90deg, #ffffff06 1px, transparent 1px)',
        radar: 'conic-gradient(from 0deg, transparent 0deg, transparent 270deg, currentColor 360deg)',
        glass: 'linear-gradient(135deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',
      },
      backgroundSize: { dots: '24px 24px', grid: '48px 48px', 'shine-size': '300% 300%' },
      boxShadow: {
        signal: '0 0 30px -5px rgba(0,240,255,.15)',
        'signal-strong': '0 0 25px rgba(0,240,255,.25)',
        violet: '0 0 30px -5px rgba(138,63,252,.2)',
        ember: '0 0 12px rgba(245,158,11,.2)',
        glass: 'inset 0 1px rgba(255,255,255,.04), 0 12px 36px rgba(0,0,0,.16)',
      },
      dropShadow: {
        signal: '0 0 8px rgba(0,240,255,.45)',
        violet: '0 0 8px rgba(138,63,252,.45)',
        emerald: '0 0 8px rgba(16,185,129,.45)',
      },
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-180%) skewX(-20deg)' },
          '100%': { transform: 'translateX(360%) skewX(-20deg)' },
        },
        radar: { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
        'signal-pulse': {
          '0%, 100%': { opacity: '.45', transform: 'scale(.96)' },
          '50%': { opacity: '1', transform: 'scale(1.04)' },
        },
        'ring-pulse': {
          '0%': { transform: 'scale(.8)', opacity: '.5' },
          '100%': { transform: 'scale(1.45)', opacity: '0' },
        },
        'ambient-drift': {
          from: { transform: 'translate3d(-24px,0,0) scale(.95)' },
          to: { transform: 'translate3d(50px,35px,0) scale(1.08)' },
        },
        scanline: { from: { transform: 'translateY(-100%)' }, to: { transform: 'translateY(100%)' } },
        shine: {
          '0%': { 'background-position': '0% 0%' },
          '50%': { 'background-position': '100% 100%' },
          to: { 'background-position': '0% 0%' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.5s ease-in-out infinite',
        radar: 'radar 4s linear infinite',
        'signal-pulse': 'signal-pulse 2.8s ease-in-out infinite',
        'ring-pulse': 'ring-pulse 3s ease-out infinite',
        'ambient-drift': 'ambient-drift 24s ease-in-out infinite alternate',
        scanline: 'scanline 8s linear infinite',
        shine: 'shine var(--duration) infinite linear',
      },
    },
  },
  plugins: [],
};
