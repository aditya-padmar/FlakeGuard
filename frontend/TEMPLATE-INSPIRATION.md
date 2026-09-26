# Template-inspired workspace pass

## Public resources reviewed

- https://ui.shadcn.com/blocks — dashboard-01 and sidebar patterns: inset application frame, separate navigation, structured content hierarchy.
- https://magicui.design/docs/components/dot-pattern — masked geometric background texture.
- https://magicui.design/docs/components/border-beam — restrained edge highlighting; not installed or copied into this build.
- https://ui.aceternity.com/components/grid-and-dot-backgrounds — geometric grid/dot background examples, visual inspiration only.

No third-party template implementation or proprietary assets were copied. This pass adapts layout ideas to the existing React components. shadcn and Magic UI repositories were verified as MIT; separately sold templates may have different terms. Aceternity reuse terms were not verified, so its source code was not used.

## Changes

- Shared inset workspace with a rounded frame, clear sidebar separation and translucent surface backing.
- Decorative SVG contour lines and a masked perspective grid behind the application. No animation behind data is required to understand the interface.
- Dedicated `src/redesign/SourcesPage.tsx` / `sources.css`: repository heading, F1–F4 process illustration, preparation checklist, existing ingestion form child slot and useful navigation links.
- Cyan line/area reliability graph preserved unchanged.
- Repository ingestion dark-theme fixes preserved; no white form panels reintroduced.
- Mobile content stacks, and redundant header status is hidden to keep navigation readable. Existing page-level demo/API disclosures remain.
- Added optional status/errors/message fields to PipelineAnalysisResult to match current backend output consumed by existing ingestion error handling. This fixes compile errors without altering server behavior.

## Verification

Production build, scoped ESLint and 29 data-contract tests pass. Desktop and 390px mobile Repository Sources layouts checked in the browser. Mobile document width stays within its viewport. Backend analysis was not run for this styling pass.
