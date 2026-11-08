# Plan: Modernize the Webapp

Component: `webapp/` (Vite + React + TypeScript app).

PR strategy: merge each

---

## Overview

The model viewer epic left two follow-ups that move the webapp to current web app standards:

- rmeissner/work_for_claus#9: drive the model selection with **React Router** instead of the custom `useSelectedModel` hash hook.
- rmeissner/work_for_claus#8: pick a **styling and theming direction**, migrate the existing styles, and support **dark mode with an explicit light/dark/system toggle** instead of following the OS only.

This epic resolves both. The work is split into these PRs:

1. **Plan** (this PR): the epic specification only.
2. **Add React Router** (dependency only).
3. **Route the model selection** through React Router and remove `useSelectedModel`. Depends on 2.
4. **Add Tailwind CSS** (dependency and Vite plugin only). Can run in parallel with 2 and 3.
5. **Design tokens and app layout in Tailwind**: one `theme.css` with the tokens for both themes, the global layout moved from `index.css` to utilities. Depends on 4.
6. **Migrate the component styles** (`ModelList`, `ModelDetails`, `StlViewer`) to Tailwind and delete the CSS Modules. Depends on 5. Can run in parallel with 7.
7. **Theme toggle**: a light/dark/system switch in the header, persisted in `localStorage`, without a flash of the wrong theme on load. Depends on 5. Can run in parallel with 6.
8. **Cleanup**: remove this specification file. Depends on all other phases.

The router track (2–3) and the styling track (4–7) are independent of each other.

---

## Architecture Decision

### Routing: React Router in library mode with a hash router

- Add `react-router` (current major, 8.x; issue #9 mentions v7, the hash router and test APIs it relies on are unchanged in v8). It's used in **library (declarative) mode**: no framework mode, no file-based routes, no Vite plugin.
- Use **`HashRouter`**. The app is a static build with no server-side rewrites, so URLs stay `#/<slug>`, existing links keep working and no hosting configuration is needed.
- The router wraps `App` in `main.tsx`. `App` itself only declares `<Routes>`, so tests can wrap it in a `MemoryRouter` instead.
- `ModelList` keeps its current props (`selectedSlug`, `onSelect`) and its listbox semantics with roving tabindex and arrow/Home/End keys. `App` maps the route to these props with `useParams()` and `useNavigate()`. Turning the options into `<NavLink>`s would break the listbox pattern (`role="option"` elements can't be links), so this is not done.

### Styling: Tailwind CSS v4 with CSS variables for the theme tokens

- Add `tailwindcss` and `@tailwindcss/vite` (v4). Tailwind v4 is configured in CSS (`@import "tailwindcss"`, `@theme`), has no runtime and no JavaScript config file.
- **One source of design tokens:** `webapp/src/theme.css` defines semantic color tokens (`--color-fg`, `--color-bg`, `--color-surface`, `--color-border`, `--color-muted`, `--color-hover`, `--color-selected-bg`, `--color-selected-fg`, `--color-accent`, `--color-danger`) as CSS custom properties for each theme, and exposes them to Tailwind with `@theme inline`. Components use semantic utilities like `bg-surface`, `text-muted`, `border-border`, so they don't need `dark:` variants: the variables switch, the classes stay the same. Spacing, typography and radii use Tailwind's default scale.
- **Theme selection** with a `data-theme` attribute on `<html>`:
  - no attribute (system): light tokens, overridden by dark tokens under `@media (prefers-color-scheme: dark)`;
  - `data-theme="light"` / `data-theme="dark"`: forces that theme, independent of the OS.
  - `color-scheme` is set to match, so native controls and scrollbars follow the theme.
  - A `@custom-variant dark` that matches both forced-dark and system-dark is added for the rare case a component needs a theme-specific style that isn't a token.
- **react-three-fiber:** the canvas isn't styled by CSS. Its WebGL clear color stays transparent, so the preview shows the `bg-surface` of its container in both themes. The mesh color (`#b0b4ba`) is readable on both backgrounds and stays a constant.
- **Preflight:** Tailwind's base reset removes default margins and list styles. The migration phases set them explicitly where the current UI relies on them (headings, the model list, the description).

### Alternatives Considered

- **Custom hash hook (status quo)** for routing: works for one route, but every new page (about page, per-part views from #5) would grow it into a hand-written router.
- **`BrowserRouter` with clean URLs:** needs a rewrite to `index.html` on every host (GitHub Pages has none) and would break the existing `#/<slug>` links.
- **React Router framework mode:** brings a Vite plugin, server rendering and file routes; too much for a static two-pane app.
- **Keep CSS Modules + a `theme.css`:** smallest change and no dependency, but keeps hand-written CSS for every layout and doesn't give reusable primitives.
- **vanilla-extract / Panda CSS:** type-safe theme contracts, but add a build plugin and a CSS-in-TS authoring model for little gain at this size.
- **Mantine / Radix Themes / Chakra UI:** ready-made components and theming, but a much larger dependency (and for some a runtime) for a UI that has one list and one panel.

---

## User Flow

- **Select a model:** clicking a model or using the arrow keys, Home and End in the list navigates to `#/<slug>`. Back/forward and reloads restore the selection, as today.
- **Open `#/` or an unknown slug:** the app shows the first model, and replaces the URL with `#/<first slug>`.
- **Switch the theme:** the header has a three-way toggle (System, Light, Dark). The choice applies immediately, is stored in `localStorage` and is restored on the next visit before the first paint. "System" follows the OS, including live changes.

### Page Layout

```
┌──────────────────────┬──────────────────────────────────────────┐
│ Work for Claus  [◐▾] │                                          │
├──────────────────────┤          3D preview (bg-surface)          │
│ ▸ Calibration cube   │                                          │
│   Pyramid            ├──────────────────────────────────────────┤
│                      │ Calibration cube                         │
│                      │ 20 mm cube to calibrate X/Y/Z steps.     │
└──────────────────────┴──────────────────────────────────────────┘
[◐▾] = theme toggle: System / Light / Dark (radio group)
```

The layout is unchanged otherwise, including the stacked layout below 768 px.

---

## Tech Specs

### Routes (phase 3)

| Path | Renders |
|---|---|
| `/` | `<Navigate to="/<first slug>" replace />` |
| `/:slug` (known) | the list with that model selected, and its details |
| `/:slug` (unknown) | `<Navigate to="/<first slug>" replace />` |
| any path, no models | "No models found" |

- `main.tsx`: `<HashRouter><App /></HashRouter>`.
- `App.tsx`: `<Routes>` with the routes above; a `ModelRoute` component reads `useParams().slug`, finds the model, and passes `onSelect={(slug) => navigate('/' + slug)}` to `ModelList`. Slugs are encoded with `encodeURIComponent`.
- Remove `webapp/src/hooks/useSelectedModel.ts`.
- Tests: `App.test.tsx` renders `<MemoryRouter initialEntries={[...]}><App models={models} /></MemoryRouter>`. The current cases are kept: initial selection, click → URL changes (checked with a small location probe or `useLocation`), initial entry selects a model, history navigation (`initialEntries` with two entries and `initialIndex`, or `navigate(-1)`), unknown slug → first model, empty state, repository models.

### Tokens (phase 5)

`webapp/src/theme.css`, imported once from `index.css` after `@import "tailwindcss"`:

```css
:root { --fg: #1f2328; --bg: #ffffff; /* … light values from today's index.css … */ color-scheme: light; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) { /* dark values */ color-scheme: dark; }
}
:root[data-theme='dark'] { /* dark values */ color-scheme: dark; }

@theme inline {
  --color-fg: var(--fg);
  --color-bg: var(--bg);
  /* … one entry per token … */
}
@custom-variant dark (&:where([data-theme='dark'], [data-theme='dark'] *));
```

The values are today's colors from `index.css`, plus `--danger` (today's hard-coded `#b00020` in `StlViewer.module.css`, with a lighter dark-mode value) and `--muted` replacing the hard-coded `#666`. If the system-dark case can't be expressed in the custom variant without duplication, the variant is dropped; tokens are the primary mechanism.

`index.css` keeps only the imports and the `html, body, #root { height: 100% }` base. The grid layout (`.app`, `.app-header`, `.app-sidebar`, `.app-main`, `.app-empty` and the `max-width: 767px` media query) moves into Tailwind classes in `App.tsx` (`grid`, `grid-cols-[280px_minmax(0,1fr)]`, `[grid-template-areas:…]` or explicit row/column placement, `max-md:` variants).

### Theme toggle (phase 7)

- `webapp/src/theme/useTheme.ts`: `type ThemePreference = 'system' | 'light' | 'dark'`. Reads/writes `localStorage['theme']` (wrapped in try/catch; storage can throw), sets or removes `document.documentElement.dataset.theme`.
- `webapp/src/components/ThemeToggle.tsx`: a labelled radio group ("Theme") with three options, rendered in the header.
- `webapp/index.html`: a small inline script in `<head>` that applies the stored preference before the first paint (no flash of the wrong theme).
- Tests: `useTheme`/`ThemeToggle` set and clear `data-theme` and persist the choice; an invalid stored value falls back to `system`; a throwing `localStorage` doesn't break rendering.
- README: one line on the theme toggle.

### Checks

Every phase keeps `npm run lint`, `npm run typecheck`, `npm test` and `npm run build` green (the Webapp CI workflow). Styling phases are additionally checked visually in light and dark mode at desktop and phone width (screenshots in the PR).

---

## Implementation Phases

### Phase 1: Plan

- This file.

### Phase 2: Add React Router

- **Depends on:** 1. **Can run in parallel with:** 4–7.
- `npm install react-router` in `webapp/`: `package.json` and `package-lock.json` only.

### Phase 3: Route the model selection through React Router

- **Depends on:** 2. **Can run in parallel with:** 4–7 (expect a small rebase conflict in `App.tsx` with phase 5; whichever merges second resolves it).
- Files: `main.tsx`, `App.tsx`, `App.test.tsx`, delete `hooks/useSelectedModel.ts`. `ModelList` and its tests stay unchanged.
- Closes #9.

### Phase 4: Add Tailwind CSS

- **Depends on:** 1. **Can run in parallel with:** 2, 3.
- `npm install -D tailwindcss @tailwindcss/vite`; register `tailwindcss()` in `vite.config.ts`. No CSS import yet, so the app looks unchanged.

### Phase 5: Design tokens and app layout in Tailwind

- **Depends on:** 4. **Can run in parallel with:** 2, 3.
- New `theme.css`; `index.css` reduced to the imports and the base; `App.tsx` layout classes. Component CSS Modules keep working because the old variable names (`--border`, `--muted`, …) are the token variables themselves, so they stay defined until phase 6.
- Visual check: the app looks the same as before in light and dark (OS) mode.

### Phase 6: Migrate the component styles

- **Depends on:** 5. **Can run in parallel with:** 3, 7.
- `ModelList.tsx`, `ModelDetails.tsx`, `StlViewer.tsx` use Tailwind classes; delete their `.module.css` files. Selected/hover/focus-visible states use the tokens (`aria-selected:bg-selected-bg`, `focus-visible:outline-accent`, …).
- Visual check as in phase 5.

### Phase 7: Theme toggle

- **Depends on:** 5. **Can run in parallel with:** 3, 6.
- New `theme/useTheme.ts`, `components/ThemeToggle.tsx` and tests; header in `App.tsx`; inline script in `index.html`; README line.
- Closes #8.

### Phase 8: Remove the plan

- **Depends on:** 2–7.
- Delete `epics/2026_11_08_modernize_webapp.md`.

---

## Open Questions and Assumptions

- **React Router major version:** the issue names v7; the plan uses the current 8.x, whose `HashRouter`, `MemoryRouter`, `useParams` and `useNavigate` cover everything needed.
- **Unknown slugs** redirect to the first model (replacing the history entry) instead of showing a "not found" state, matching today's fallback.
- **Theme toggle UI:** a three-option radio group (System/Light/Dark) rather than a single cycling button, so the current state is always visible and accessible.
- **No component library:** reusable primitives (button, panel) are introduced only when a second use appears; the toggle is the only new control in this epic.
- **Phase sizes:** all phases are expected to stay well below 300 changed lines, excluding `package-lock.json`.
