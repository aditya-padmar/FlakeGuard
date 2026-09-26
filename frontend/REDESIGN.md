# FlakeGuard 2.0 frontend

## Run

Requires Node 20.19+ (Node 22.12+ or Node 24 recommended).

```sh
cd frontend
npm install
npm run dev
npm run build
npm test
npm run lint
```

Vite serves port 5173 and forwards `/api` to the existing FastAPI backend on port 8000. The demo does not need the backend. Production hosting must serve `dist`, provide SPA fallback to `index.html`, and route `/api` to the backend. `vite preview` alone does not configure a production API gateway.

## Component architecture

```text
main.tsx
├── redesign/design.css                 Global tokens, Tailwind layers, shared controls, shell
└── App.tsx
    ├── MotionConfig                    User reduced-motion preference
    ├── AuthProvider                    Existing browser-local demo identity
    ├── WorkspaceProvider               Shared results, cancellable requests, demo timer
    └── BrowserRouter / Shell
        ├── Brand / public header / workspace sidebar / mobile focus handling
        ├── Launchpad                   Repository validation and demo entry
        ├── AuthView                    Sign-in/sign-up, DAG illustration, password strength
        ├── PipelineView                Running/idle pipeline, specialist cards, console
        ├── DashboardView               Summary, analytics, filters, inventory, quarantine
        │   ├── ReliabilityChart        Observed per-test pass rates, not a time series
        │   ├── HistoryBars             Supplied pass/fail outcomes only
        │   └── TestDrawer              Radix dialog, evidence, confidence, diff and export
        └── Lazy legacy tools           RepositoryIngestion, RemediationPage, AuditPage

redesign/data.ts                        Typed view model, pure API adapter, explicit sample data
redesign/data.test.ts                   URL, normalization, joins and sample-integrity tests
redesign/experience.css                 Auth, launchpad, pipeline styles
redesign/dashboard.css                  Analytics, inventory and drawer styles
```

## Routes

| Route | View |
| --- | --- |
| `/` | Repository launchpad |
| `/login`, `/signup` | Local demo authentication |
| `/dashboard` | Trust overview |
| `/inventory` | Searchable test inventory |
| `/pipeline` | Running investigation or idle state |
| `/fixes` | Proposed and validated patches |
| `/quarantine` | Suppression source summary and quarantined test matrix |
| `/sources` | Existing GitHub, archive upload, backend-local path input |
| `/tools/remediation` | Existing backend evidence/strategy tools |
| `/tools/audit` | Existing backend audit tools |
| `/remediation`, `/audit` | Compatibility redirects to `/fixes`, `/quarantine` |

Unknown routes render a helpful 404. Navigating to the pipeline does not silently start a demo or overwrite existing results.

## Design tokens

The runtime source of truth is `src/redesign/design.css`. Tailwind aliases are in `tailwind.config.js`, and PostCSS configuration is in `postcss.config.js`.

| Token | Value | Purpose |
| --- | --- | --- |
| `--bg` | `#08090C` | Obsidian canvas |
| `--surface` | `#0E1117` | Panels |
| `--surface-raised` | `#141820` | Raised surfaces |
| `--border` | `rgba(255,255,255,.08)` | Hairline borders |
| `--text` | `#EEF2F7` | Primary text |
| `--muted` | `#8993A6` | Secondary text |
| `--cyan` | `#00F0FF` | Primary signals and interactions |
| `--blue` | `#0070F3` | Electric accent |
| `--ember` | `#FF5722` | Base warning accent |
| `--orange` | `#FF7849` | Readable warning foreground |
| `--green` | `#10B981` | Passed/validated states |
| `--bob` | `#8A3FFC` | IBM Bob accent |
| `--purple` | `#A78BFA` | Readable violet foreground |

Inter handles UI chrome; JetBrains Mono handles code, numeric data, logs and paths. Fonts load from Google Fonts with local/system fallbacks. Self-host the font files if deployment policy disallows third-party font requests.

Shared primitives: `.fg-button`, `.fg-button-primary`, `.fg-button-small`, `.fg-icon-button`, `.fg-panel`, `.fg-badge`, `.fg-eyebrow`, `.fg-mono`. Glass surfaces, controlled gradients, button sheen/press feedback, staggered reveals, animated pipeline connections and radar effects use CSS and Framer Motion. Reduced-motion preferences disable continuous animations.

## Data and safety boundaries

- Sample workspace: 126 total tests, eight flaky test records, seven diagnoses, five sample-validated patches, three quarantined records. These are explicitly sample values.
- Real repository analysis uses the existing `repositoryApi.cloneAndAnalyze` endpoint. An `AbortSignal` cancels client waiting. Cancellation may not stop server work that already began.
- The API currently returns a completed result, not a telemetry stream. Live mode shows that limitation instead of fictional milestones, logs, or outcomes.
- Real execution ordering is unavailable. Aggregate counts are shown without generating synthetic chronological history.
- The API adapter unions detected tests, quarantine-list records and audit records. Path-qualified identities prevent unrelated same-name tests from being joined. Ambiguous audit identities remain separate.
- Empty API collections clear sample records. Zero metrics remain zero. Missing metrics and categorical confidence are displayed as unknown rather than invented numbers.
- Demo validation is deliberately labeled simulation; it updates only demo state. No real sandbox validation endpoint is present.
- The drawer exports a `.patch` file and local Git instructions. It does **not** create/push branches, open PRs, auto-merge, or apply patches remotely.
- Auth remains the pre-existing browser-local demo profile, not a security boundary. Passwords never reach the provider. GitHub OAuth is not configured; its button explains this rather than reporting a false sign-in.
- Existing advanced backend tools are retained, not reimplemented. Their backend behavior was not end-to-end verified during this UI redesign.
- Workspace results are in memory. Reload returns to the sample dataset; profile persistence is best-effort localStorage.

## Accessibility and responsive behavior

- Named controls, explicit form labels, live feedback, visible focus indicators, skip link and a single main landmark.
- `Cmd/Ctrl+K` focuses repository input on the launchpad and test search in dashboard views.
- Radix detail dialog handles dismissal and focus; focus returns to the opening test control.
- Mobile navigation hides offscreen links, moves focus into the sidebar, makes background content inert, contains Tab focus, closes on Escape and restores focus.
- Tablet/mobile stacking, scroll-contained inventory table, full-width mobile drawer, reduced-motion support.

## Verification

2026-09-26:

- Production TypeScript/Vite build passed.
- ESLint passed for the redesign, application shell and auth context. The lint script intentionally scopes these surfaces; it does not assert that untouched legacy tools are lint-clean.
- 29 Vitest tests passed, covering URL rejection/normalization, confidence/cause normalization, zero/empty data, exact-path joins, ambiguous audit identities, list-only exclusions, audit deduplication and fixture consistency.
- `npm audit`: zero known vulnerabilities after updating Vite, Router, Vitest and TypeScript lint dependencies.
- Browser verified at desktop (1280/1440px) and mobile (390px): launchpad, demo pipeline completion, dashboard, search, detail drawer, patch tab, simulated validation, quarantine filters, signup/OAuth messaging, local demo registration, mobile navigation and Escape/focus restoration.
- Visual checks covered desktop launchpad/dashboard/auth/pipeline and mobile drawer/quarantine layouts. Mobile page width remained within viewport; inventory overflow is contained in its own scroller.
- No real repository cloning, OAuth, remote PR creation, or live sandbox validation was performed. Those are not implied by the frontend verification.
