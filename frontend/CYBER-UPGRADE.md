# FlakeGuard cyber-dark visual upgrade

## Implemented components

- `src/redesign/AmbientBackground.tsx`: fixed decorative dot matrix and three blurred cyan/violet/emerald orbs. A passive pointer listener updates spotlight CSS variables through one animation frame, with cleanup and reduced-motion/touch opt-outs.
- `src/redesign/Launchpad.tsx`: layered glass hero and repository command panel, detection pulse, explicit API waiting state, shimmer primary actions.
- `src/redesign/PipelineView.tsx`: idle radar rings, simulated active conical scans, spring completion badges, color-coded agents and elapsed-gated terminal output. Console follows new output only while near its bottom and offers a Follow output control.
- `src/redesign/DashboardView.tsx`: glass KPI filter cards, rollup values, ember warning treatment, inventory and remediation integration.
- `src/redesign/AnimatedNumber.tsx`: 700ms visual numerator animation; assistive technology receives final values. Null and zero remain accurate, fraction denominator stays fixed.
- `src/redesign/Charts.tsx`: gradient reliability bars with top caps and height growth; focus/hover/tap exact outcomes; arrow/Home/End navigation; eight-test pagination; interactive root-cause donut using true SVG arc paths and centered statistics.
- `src/redesign/AuthView.tsx`: illustrated animated CI graph, glass form, floating labels and animated GitHub icon. Existing demo-only auth behavior preserved.

## Shared styling and Tailwind

`tailwind.config.js` provides the complete extension:
- Colors: obsidian, slateBase, signal, electric, ember, warning, trusted, bob.
- Background utilities: dots, grid, radar conic gradient, glass gradient.
- Shadows: signal, signal-strong, violet, ember, glass; matching drop-shadow utilities.
- Keyframes/animations: shimmer, radar, signal-pulse, ring-pulse, ambient-drift, scanline.

`src/redesign/design.css` defines the runtime primitives and reduced-motion guard. Feature styles remain in `experience.css` and `dashboard.css`.

```tsx
<div className="fg-panel fg-spotlight">
  <button className="fg-button fg-button-primary">Run diagnostics</button>
</div>
```

The spotlight is decorative, never intercepts clicks, and is disabled for touch and reduced motion. The dot layer and ambient orbs are hidden from assistive technology. Text and controls keep sufficient opaque backing instead of relying on glow for legibility.

## Data integrity

The existing backend returns completed analyses, not a progress stream. Real-mode pipeline cards therefore say status unavailable and do not pretend to scan or complete. Radar activity and scripted logs are explicitly simulated in demo mode. OAuth remains unconfigured and local demo passwords are neither sent nor saved. No patch is applied or auto-merged by this upgrade.

## Verification

- Production build and scoped lint passed.
- 29 existing data contract tests passed.
- Browser checked desktop glass dashboard, mobile cards/width, exact chart tooltip counts, keyboard donut filtering, floating auth labels, hero, and active four-agent radar phase.
- Mobile dashboard fits a 390px viewport; table overflow remains local to its scroller.
- Motion dependencies are split into a separate production chunk.
- Terminal scroll-follow uses the browser scroll position and a 48px near-bottom threshold; listener cleanup and elapsed log gating were reviewed in code. No real backend analysis or OAuth was exercised.
