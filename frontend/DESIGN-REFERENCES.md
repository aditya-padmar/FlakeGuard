# UI refinement — 26 September 2026

The second design pass replaces the cyber-demo aesthetic with a quieter working interface. These public references were read to guide the work; no third-party template source, proprietary assets, or branding was copied.

## References consulted

- [Linear: How we redesigned the Linear UI](https://linear.app/now/how-we-redesigned-the-linear-ui) — neutral navigation, separation of app chrome from content, alignment and reduced clutter.
- [Vercel Geist: Introduction](https://vercel.com/geist/introduction) — shared typography, spacing, surfaces, and component foundations.
- [Vercel Geist: Colors](https://vercel.com/geist/colors) — semantic resting, hover and active surfaces rather than independent gray values.
- [Radix Themes: Getting started](https://www.radix-ui.com/themes/docs/overview/getting-started) — consistent scale, radius and palette across controls. Existing Radix dialog integration retained; no competing component framework installed.
- [Motion: Hover animation](https://motion.dev/docs/react-hover-animation) — reversible feedback, restrained motion, avoiding emulated touch-hover behavior.
- [Motion: Accessibility](https://motion.dev/docs/react-accessibility) — respect reduced motion globally and in CSS.

## Applied changes

- Charcoal canvas `#101113`, panel `#17181b`, raised controls `#202226`, readable secondary text `#9a9ca5`, muted teal `#65cdb5`.
- Off-white primary buttons with 150 ms background/border changes, light shadow, small pressed state and a 2 px directional-arrow hover movement.
- Shared metrics strip with separators instead of five glowing cards. Metrics are actual filter buttons, with explicit pressed state and keyboard focus.
- Inventory quick filters with a spring-driven underline. Table hover/focus highlights the row and brings the detail arrow forward without moving the row.
- Per-test reliability columns replace the connected line, avoiding the visual implication of a time trend.
- Readable 12–13 px dashboard controls, 13 px drawer text and 12 px code. Stronger hierarchy and fewer tiny, all-uppercase labels.
- Product-specific language, consistent shield branding, no rotated decorative labels, no marketing headline inside every card, and removal of duplicate footer copy.
- Reduced-motion support retained. Hover animations on public/auth controls are gated to fine pointers; no essential action requires hover.

## Verification

- ESLint, TypeScript/Vite production build, and 29 existing data-contract tests passed.
- Browser verified metric filters (quarantined -> 3 records), quick filters (validated -> 5 records), primary-button pointer hover, desktop layout, mobile dashboard and mobile launchpad.
- Mobile dashboard fresh render and launchpad remained within a 390 px viewport. Table overflow stays in its own scroller.
- Real backend behavior, authentication boundaries and patch safety were not changed by this visual pass.
