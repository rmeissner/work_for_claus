# Plan: Model Viewer Webapp

Component: new `webapp/` Vite application and new `models/` content folder at the repository root.

---

## Overview

The repository is meant to hold the 3D models for our printer Claus, but there is no code and no models yet. This epic adds a small static web app for browsing those models:

- The **left pane** lists every model found in the repository.
- The **right pane** shows an interactive 3D preview of the selected model's STL file and its description.

Each model lives in its own folder under `models/`, and each folder holds one `.stl` file and one `project.json` with a `name` and a `description`.

The work is split into these PRs:

1. **Plan** (this PR): the epic specification only.
2. **Scaffold**: an empty Vite + React + TypeScript app in `webapp/` with lint, type check and test scripts.
3. **CI** (can run in parallel with 4–6 once 2 is merged): a GitHub Actions workflow that lints, type-checks, tests and builds the app.
4. **Model data**: the `models/` folder convention, two sample models, and a typed loader module with unit tests.
5. **Split layout and model list**: the two-pane layout, the model list, selection state and the description panel, with a placeholder where the 3D preview will go.
6. **STL viewer component** (can run in parallel with 4 and 5): a stand-alone three.js component that renders an STL file from a URL.
7. **Integrate the viewer**: replace the placeholder in the right pane with the STL viewer.
8. **Cleanup**: remove this specification file.

---

## Architecture Decision

**Static single-page app, with no backend.** The models are files in the repository, so the app can find them at build time. It uses Vite's `import.meta.glob` to collect `models/*/project.json` (imported eagerly as JSON) and `models/*/*.stl` (imported as asset URLs). Vite fingerprints and copies the STL files into `dist/` during the build. The result is a static bundle that any static host can serve, for example GitHub Pages. During development, adding a model folder updates the app through hot module reload.

**Folder layout.**

```
/
├── models/                 # content: one folder per model
│   └── <model-slug>/
│       ├── project.json    # { "name": string, "description": string }
│       └── <anything>.stl
├── webapp/                 # Vite app (own package.json)
└── epics/
```

`models/` sits at the repository root, outside the app, because the models are the main content of the repository and the app is only a viewer for them. `webapp/vite.config.ts` adds the repository root to `server.fs.allow` so the dev server can serve files from `../models`.

**Stack.**

- Vite with React and TypeScript (`npm create vite@latest -- --template react-ts`).
- three.js through `@react-three/fiber` and `@react-three/drei`. drei provides `OrbitControls`, `Stage` (auto-centering and lighting) and `Bounds`. The STL is parsed with `STLLoader` from `three/examples/jsm/loaders/STLLoader`.
- Vitest and React Testing Library for unit and component tests. Plain CSS (CSS modules) for styling, with no UI framework.
- npm as the package manager, with `package-lock.json` committed.

### Alternatives Considered

- **Small backend (Express or similar) that reads `models/` at runtime.** New models would appear without a rebuild, but we would have to host and run a server. Models only change through commits, so a rebuild on each commit is acceptable. Rejected.
- **Generated `manifest.json`, built by a pre-build script.** This works without Vite-specific features, but it adds a script and a generated file that has to be kept in sync. `import.meta.glob` does the same job natively. Rejected, but it remains the fallback if we ever leave Vite.
- **Plain three.js without React.** It has fewer dependencies, but managing state for the list, the selection and the viewer by hand takes more code than React plus react-three-fiber. Rejected.
- **`<model-viewer>` web component.** It only supports glTF/GLB, so every STL would need converting. Rejected.
- **Models inside `webapp/public/`.** This needs no `fs.allow` configuration, but it ties the content to the viewer and the files would not be fingerprinted. Rejected.

---

## User Flow

1. The user opens the app. The left pane lists every model by `name`, sorted alphabetically. The first model is selected by default.
2. The user clicks a model in the list. It is highlighted, the right pane shows its 3D preview, and the description appears below the preview.
3. The user rotates, zooms and pans the preview with the mouse or touch (orbit controls).
4. While an STL loads, the preview shows a loading indicator. If loading or parsing fails, the preview shows an error message and the description is still shown.
5. If `models/` contains no valid model, the app shows an empty state: "No models found".
6. The selected model is stored in the URL hash (`#/<model-slug>`), so a link to a model can be shared and reloading the page keeps the selection.

### Page Layout

Desktop (≥ 768px):

```
+----------------------+-----------------------------------------------+
| Work for Claus       |                                               |
+----------------------+                                               |
| > Benchy         [*] |              3D preview (canvas)              |
|   Calibration cube   |           drag: rotate, wheel: zoom           |
|   Filament clip      |                                               |
|   ...                |                                               |
|                      +-----------------------------------------------+
|                      | Benchy                                        |
|                      | A small boat used to benchmark print quality. |
|                      |                                               |
+----------------------+-----------------------------------------------+
   ~280px, scrolls                     fills remaining width
```

Mobile (< 768px): the panes stack. The list sits on top with a capped height and its own scrolling, and the preview and description sit below it.

```
+------------------------------+
| Work for Claus               |
| > Benchy                 [*] |
|   Calibration cube           |
+------------------------------+
|        3D preview            |
+------------------------------+
| Benchy                       |
| A small boat used to ...     |
+------------------------------+
```

---

## Tech Specs

**`project.json` schema**

```json
{
  "name": "Calibration cube",
  "description": "20 mm cube to calibrate X/Y/Z steps."
}
```

- `name` is a required, non-empty string.
- `description` is a required string. It is shown as plain text, with line breaks preserved (`white-space: pre-wrap`). It is not rendered as Markdown.
- Unknown keys are ignored, so the schema can be extended later.

**Model discovery (`webapp/src/models/loadModels.ts`)**

```ts
export interface Model {
  slug: string;        // folder name
  name: string;
  description: string;
  stlUrl: string;
}

export function loadModels(): Model[];
```

- It calls `import.meta.glob('../../../models/*/project.json', { eager: true, import: 'default' })` and `import.meta.glob('../../../models/*/*.stl', { eager: true, query: '?url', import: 'default' })`.
- It groups both results by folder name (the slug).
- A folder is skipped with a `console.warn` when its `project.json` is missing or invalid, or when it has no STL file.
- If a folder has more than one STL file, the first one in alphabetical order is used and a warning is logged.
- Models are sorted by `name`, using `localeCompare`.
- The pure grouping and validation logic is a separate function, `buildModels(projects, stls)`, so it can be unit-tested without Vite globs.
- Vite has to accept `.stl` as an asset (`assetsInclude: ['**/*.stl']`).

**Components (`webapp/src/components/`)**

| Component | Responsibility |
|---|---|
| `App` | Loads the models, owns the selected slug (synced with `location.hash`), and renders the layout. |
| `ModelList` | An accessible list (`role="listbox"`, buttons with `aria-selected`) with keyboard navigation (up and down arrows). |
| `ModelDetails` | Right pane: the preview slot plus the name and description. |
| `StlViewer` | Props: `{ url: string }`. A `<Canvas>` containing `<Stage>`, `<OrbitControls>`, and a mesh from `useLoader(STLLoader, url)`, wrapped in `<Suspense>` (loading state) and an error boundary (error state). The geometry gets `computeVertexNormals()` and a neutral `meshStandardMaterial`. |

**Scripts (`webapp/package.json`)**: `dev`, `build` (`tsc -b && vite build`), `preview`, `lint` (ESLint flat config from the Vite template), `typecheck`, and `test` (`vitest run`).

**CI (`.github/workflows/webapp.yml`)**: runs on pull requests and on pushes to `main` that touch `webapp/**` or `models/**`. It runs `npm ci`, `lint`, `typecheck`, `test` and `build` on Node 22 LTS.

**Tests**

- `buildModels`: valid folders, a missing `project.json`, a missing STL, an invalid JSON shape, several STL files in one folder, and sort order.
- `ModelList` and `App`: the list renders names, clicking an item selects it and updates the hash, the initial hash selects that model, and an unknown hash falls back to the first model. `StlViewer` is mocked here, because jsdom has no WebGL.
- `StlViewer`: renders the loading state and the error state (with the loader mocked). The actual WebGL rendering is checked by hand in `npm run dev`; there are no automated visual tests in this epic.

**Sample data**: two small ASCII STL files (a 20 mm cube and a simple pyramid, each under 100 lines) in `models/calibration-cube/` and `models/pyramid/`, so the app has something to show and the tests have fixtures.

---

## Implementation Phases

Dependencies:

```
1 Plan ─► 2 Scaffold ─┬─► 3 CI
                      ├─► 4 Model data ─► 5 Layout & list ─┐
                      └─► 6 STL viewer ────────────────────┴─► 7 Integrate ─► 8 Cleanup
```

Phases 3, 4 and 6 can be worked on in parallel once phase 2 is merged.

### Phase 1: Plan (this PR)
- Adds `epics/2026_11_08_add_model_viewer_webapp.md`.

### Phase 2: Vite scaffold
- Generates `webapp/` from the `react-ts` Vite template and trims the demo content to a "Work for Claus" heading.
- Adds Vitest, React Testing Library and jsdom, plus the `test` and `typecheck` scripts and one smoke test that checks the heading renders.
- Adds `.nvmrc` (Node 22), a root `.gitignore` (`node_modules`, `dist`), and a README section on how to run the app.
- Files: `webapp/{package.json,package-lock.json,vite.config.ts,tsconfig*.json,eslint.config.js,index.html}`, `webapp/src/{main.tsx,App.tsx,App.test.tsx,index.css}`, `.nvmrc`, `.gitignore`, `README.md`.
- The lockfile is generated and should not be reviewed line by line. Apart from it, the PR is about 150 lines.

### Phase 3: CI workflow
- Adds `.github/workflows/webapp.yml` as described in Tech Specs.
- Files: 1.

### Phase 4: Model data and loader
- Adds `models/calibration-cube/{project.json,cube.stl}` and `models/pyramid/{project.json,pyramid.stl}`.
- Adds `webapp/src/models/{types.ts,buildModels.ts,buildModels.test.ts,loadModels.ts}`.
- Updates `vite.config.ts`: `assetsInclude` and `server.fs.allow`.
- Adds a "Adding a model" section to `README.md` that documents the folder convention.
- The UI does not change in this PR.

### Phase 5: Split layout and model list
- Adds `ModelList` and `ModelDetails` (with a placeholder `<div>` for the preview), the hash-based selection hook `useSelectedModel`, the layout CSS (two-pane on desktop, stacked on mobile), the empty state, and tests.
- Files: `webapp/src/App.tsx`, `webapp/src/components/{ModelList,ModelDetails}.{tsx,module.css}`, `webapp/src/hooks/useSelectedModel.ts`, and tests. That is about 8 files and roughly 250 lines.

### Phase 6: STL viewer component
- Adds the `three`, `@react-three/fiber` and `@react-three/drei` dependencies. A dependency-only change, so it can be its own commit within the PR or a separate PR if the reviewer prefers.
- Adds `webapp/src/components/StlViewer.tsx` with the loading and error states and an `ErrorBoundary`, plus tests with the loader mocked.
- The component is not used anywhere yet, so the app does not change visibly.

### Phase 7: Integrate the viewer
- Replaces the placeholder in `ModelDetails` with `<StlViewer url={model.stlUrl} key={model.slug} />`.
- Lazy-loads the viewer (`React.lazy`) so the three.js bundle doesn't block the first paint of the list.
- Updates the `App` tests to mock the viewer module.
- Small PR: about 3 files.

### Phase 8: Cleanup
- Removes `epics/2026_11_08_add_model_viewer_webapp.md`.

---

## Open Questions and Assumptions

- **Assumption:** `models/` at the repository root is the right place for the models. If they belong somewhere else, only the glob path in `loadModels.ts` and `fs.allow` change.
- **Assumption:** each folder contains exactly one STL file. Several STL files per model (for example, multi-part prints) are out of scope; the loader picks the first one and logs a warning.
- **Assumption:** descriptions are plain text. Markdown rendering can be added later.
- **Assumption:** STL files are small enough to commit directly (a few MB at most). If they grow large, consider Git LFS. That is a separate decision and does not change the app.
- **Open:** do we need extra `project.json` fields soon, such as a thumbnail, print settings, material or tags? The loader ignores unknown keys, so we can add them later.
- **Open:** where is the app deployed? GitHub Pages would need a `base` path in `vite.config.ts` and a deploy workflow. Not part of this epic.
- **Open:** should the model's units or dimensions be shown? STL has no units; we assume millimetres.
