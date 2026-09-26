# Supplied animated gradient integration

The user-supplied WebGL2 fragment shader and six presets are retained in `src/components/ui/animated-gradient.tsx`. The landing page `/` uses a slow custom dark cyan/blue/violet configuration behind its content. Other routes are unchanged.

## Structure

- Reusable components: `src/components/ui/` (`@/components/ui`). This separates shared primitives from feature views and matches shadcn CLI conventions.
- Global styles: `src/redesign/design.css`.
- Landing background layers: `src/redesign/experience.css`.
- shadcn settings: `components.json`; TypeScript and Vite resolve `@/` to `src/`.
- `src/lib/utils.ts` provides `cn` using `clsx` and `tailwind-merge`.

React, TypeScript, and Tailwind were already installed; no project reinitialization was needed. No images or icon assets are required by this background.

```tsx
import AnimatedGradient from '@/components/ui/animated-gradient';

<div className="relative isolate min-h-[400px] overflow-hidden">
  <AnimatedGradient config={{ preset: 'Prism', speed: 10 }} />
  <div className="relative">Foreground content</div>
</div>
```

The supplied demo passed children to a component that does not accept children. The corrected example uses foreground siblings and is included as `animated-gradient-demo.tsx`.

## Safeguards

- Shader/program compilation checks and CSS gradient fallback.
- Device pixel ratio capped at 1.5 and drawing buffer capped at two million pixels.
- Animation pauses offscreen and in hidden tabs.
- Reduced motion and zero speed render a still frame.
- Resize, context restoration and unmount cleanups handled.
- Decorative canvas has no pointer events and is hidden from assistive technology.

Build and existing 29 data tests pass. New component passed scoped ESLint. Browser verified live shader appearance on desktop and mobile, readable foreground/navigation, and mobile width within viewport.
