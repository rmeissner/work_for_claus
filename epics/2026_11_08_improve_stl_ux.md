# Plan: Improve STL UX

Component: `webapp/` (model data, details pane), `models/` (`project.json` files, star ornament generator), `README.md`.

PR strategy: merge each

---

## Overview

A model can only have one STL file today: if a folder has several, `buildModels()` uses the first one alphabetically (rmeissner/work_for_claus#5). Many prints have several parts, so this epic lets a model have any number of STL files and improves how they are shown:

1. **Files in `project.json`:** every STL file of a model is listed, in order, in a new `files` key of its `project.json`. The webapp reads this list instead of picking one STL. This closes rmeissner/work_for_claus#5.
2. **Carousel:** the preview becomes a hero-banner-style wheel. One file is shown at a time. Below it, a row of dots marks the files, with round previous/next buttons with arrows on either side of the dots. It loops (next on the last file goes to the first). It never switches on its own.
3. **Downloads:** the details pane lists the model's files below the description, each as a download link. The first 3 are shown, the rest are behind a "Show N more" button.
4. **Star ornament parts:** the star ornament generator also writes one STL per part and a `combined.stl` of the assembled star, so the first multi-file model exists.
5. **Mobile model picker:** on small screens the model list collapses into one bar showing the current model. Tapping the bar opens the list as a sheet over the page. With many models the list no longer pushes the preview down.

Phases 3, 4 and 5 only depend on phase 2 and can run in parallel. Phase 6 only touches the layout and can run in parallel with 5.

---

## Architecture Decision

- **`project.json` is the source of truth for files.** It gets a required, non-empty `files` array. Its order is the order of the carousel slides and of the download list. Each entry is an object with the file name and an optional label:

  ```json
  {
    "name": "Star ornament",
    "description": "…",
    "files": [
      { "file": "combined.stl", "name": "Assembled star" },
      { "file": "star-ornament.stl", "name": "Print plate" },
      { "file": "part-a.stl", "name": "Part A" },
      { "file": "part-b.stl", "name": "Part B" }
    ]
  }
  ```

  `name` defaults to the file name. Only `.stl` files are allowed (the carousel can show every listed file).
- **Validation (in `buildModels`, with zod):**
  - `files` missing, empty, not an array, an entry without a string `file`, a `file` not ending in `.stl` (case-insensitive) or a duplicate `file` → `invalid project.json`, the model is skipped with a warning (same as an invalid `name` today).
  - A listed file that isn't in the folder → warning, the file is dropped. If no file is left, the model is skipped.
  - An STL in the folder that isn't listed → warning, the file is ignored.
  - `file` must be a plain file name (no `/`), because `import.meta.glob` only picks up `models/*/*.stl`.
- **Data model:** `Model.stlUrl: string` becomes `Model.files: ModelFile[]` with `ModelFile = { name: string; fileName: string; url: string }`. `files` is never empty.
- **Viewer stays single-file.** `StlViewer` keeps taking one `url`. The new `StlCarousel` holds the current index and renders one `StlViewer` for the current file (`key` = url, so its error state resets). Only the visible file is loaded; `useLoader` caches files that were already shown.
- **Downloads are plain links:** `<a href={url} download={fileName}>`. Vite already emits every STL as an asset, so nothing else is needed.

### Alternatives Considered

- **Use every `*.stl` in the folder (no list in `project.json`):** no way to set the order or labels. Rejected, the user wants the files listed in `project.json`.
- **A plain string array (`"files": ["a.stl"]`):** shorter, but no labels. Objects with an optional `name` keep the short form cheap and allow nicer labels in the download list.
- **Allow non-STL files (3MF, PDF) for download only:** rejected for now, `files` is STL-only. Easy to relax later by filtering the carousel to `.stl`.
- **All parts in one scene, laid out side by side:** needs layout logic and makes single parts hard to inspect. The star ornament gets a `combined.stl` instead, which shows the assembled print.
- **Mount all slides and animate between them:** one WebGL canvas per slide is heavy. Only the current slide is mounted; switching is instant.
- **A carousel library (Embla, Swiper):** too much for prev/next with looping; a small component is easier to test.

---

## User Flow

1. The user selects a model in the list. The preview shows its **first** file from `project.json`.
2. If the model has more than one file, a row below the canvas shows a round **‹** button, one dot per file (the current one filled) and a round **›** button. There is no title or counter; hovering a dot shows its file's name as a tooltip. Up to 2 dots are shown on each side of the current one. If more files lie beyond that in a direction, the outermost visible dot on that side is drawn smaller, to show that more are coming.
3. **›** shows the next file, **‹** the previous one. From the last file, **›** goes to the first; from the first, **‹** goes to the last. With the preview focused, the Left/Right arrow keys do the same. Nothing switches on its own.
4. Selecting another model starts at its first file again.
5. Below the description, a **Files** list shows the first 3 files as download links (label, file name). If there are more, a **Show N more** button reveals the rest (and turns into **Show less**).
6. A model with a single file shows no buttons, no dots and a one-item file list.

**On mobile (below the `md` breakpoint):**

1. Below the header there is one bar with the current model's name and a chevron (`Star ornament ▾`). The list itself is hidden, so the preview starts right below the bar, however many models there are.
2. Tapping the bar opens the model list as a sheet over the page, under the bar: at most 70% of the screen height, scrolling inside, with a dimmed backdrop. Focus moves to the selected model, and the arrow keys work as on desktop.
3. Picking a model navigates to it and closes the sheet. Tapping the backdrop, tapping the bar again or pressing Escape closes it without a change. Focus returns to the bar.
4. On desktop nothing changes: the bar is hidden and the list is always visible in the sidebar.

### Page Layout

```
┌───────────────┬──────────────────────────────────────────────┐
│ Work for Claus│                                              │
│      [theme]  │                 3D preview                   │
├───────────────┤                                              │
│ Calibration   │                                              │
│ Pyramid       │           ( ‹ )  ○ ○ ● ○  ( › )              │
│▌Star ornament ├──────────────────────────────────────────────┤
│               │ Star ornament                                │
│               │ Slot-together Christmas star: …              │
│               │                                              │
│               │ Files                                        │
│               │  ⤓ Assembled star   combined.stl             │
│               │  ⤓ Print plate      star-ornament.stl        │
│               │  ⤓ Part A           part-a.stl               │
│               │  [ Show 1 more ]                             │
└───────────────┴──────────────────────────────────────────────┘
```

---

## Tech Specs

### Types (`webapp/src/models/types.ts`)

```ts
export interface ModelFile {
  /** Label from project.json, or the file name. */
  name: string
  /** File name in the model folder, used as the download name. */
  fileName: string
  url: string
}

export interface Model {
  slug: string
  name: string
  description: string
  /** In project.json order; never empty. */
  files: ModelFile[]
}
```

### `buildModels` (`webapp/src/models/buildModels.ts`)

- `projectSchema` gains `files: z.array(z.object({ file, name? })).min(1)` with the checks listed above.
- Builds `files` from the list, looking up each `models/<slug>/<file>` in the glob result.
- Removes the "several STL files" warning and the TODO.

Tests (`buildModels.test.ts`):
- keeps the `project.json` order and uses `name` or falls back to the file name;
- skips a `project.json` with missing/empty `files`, a non-`.stl` entry, a path with `/`, a duplicate;
- drops a listed file that doesn't exist (warning), skips the model when none is left;
- warns about an unlisted STL;
- `loadModels` test: every repository model has at least one file and every url matches `.stl`.

### `StlCarousel` (`webapp/src/components/StlCarousel.tsx`)

- Props: `files: ModelFile[]`. State: current index. `ModelDetails` renders it with `key={model.slug}` so the index resets per model.
- A `section` with `aria-roledescription="carousel"` and `aria-label="Model files"`; the slide has `aria-roledescription="slide"` and `aria-label="3 of 4: Part A"`.
- A control row below the canvas: round **‹** button, the dots, round **›** button. The buttons are `rounded-full` with `aria-label="Previous file"` / `"Next file"` and an inline SVG chevron. The whole row is hidden when there is one file.
- Index changes use modulo: `(index + 1) % length`, `(index - 1 + length) % length`.
- Left/Right arrow keys on the carousel section (`tabIndex={0}`) move too, but not while the pointer drags the canvas (keys only, OrbitControls doesn't use them).
- No caption: file names only appear in the download list and in the dots' `title` (hover tooltip) and `aria-label`.
- Dots are buttons (`aria-label="Show Part B"`, `title="Part B"`, `aria-current` on the active one) that jump to a file.
- **Dot window:** a pure helper `visibleDots(index, length)` returns the dots to render with a size each. It includes the files from `index - 2` to `index + 2`, clamped to the list (by position, not wrapping around). On a side where more files lie beyond the window, the outermost dot is `small`. Examples for 7 files (0-based index): current 0 → `●○○`, the last one small; current 3 → `○○●○○`, both ends small; current 6 → `○○●`, the first one small. With 5 or fewer files every dot fits and none is small.
- No timers.

Tests (`StlCarousel.test.tsx`, with `StlViewer` mocked like in `App.test.tsx`): shows the first file; next/previous move and loop in both directions; arrow keys; dots jump and carry the file name as `title`; no title or counter text is rendered; no controls for one file; the index resets when the `key` changes. `visibleDots` gets table tests: few files (all full size), current at the start, in the middle and at the end of a long list.

### `ModelFiles` (`webapp/src/components/ModelFiles.tsx`)

- Props: `files: ModelFile[]`. Shows a `Files` heading and a list of `<a href={url} download={fileName}>` with the label and the file name.
- The first 3 are always shown. With more, a button `Show N more` / `Show less` (`aria-expanded`, `aria-controls`) toggles the rest. `VISIBLE_FILES = 3`.
- Rendered in `ModelDetails` below the description.

Tests (`ModelFiles.test.tsx`): links have the right `href` and `download`; with ≤ 3 files there is no button; with 5 files only 3 links are shown until the button is clicked, then 5, and the label switches to `Show less`.

### Star ornament (`models/star-ornament/`)

- `generate.py` writes, besides the plate `star-ornament.stl`:
  - `part-a.stl` and `part-b.stl`: each part on its own, flat on Z = 0 (printable, `assert_printable`);
  - `combined.stl`: the assembled star from `assembled()` (part B rotated 90°), both parts in one STL, standing on Z = 0. This one is for previewing, not for printing.
- `project.json` lists them: combined, plate, part A, part B (order taken from this list).
- `test_generate.py`: the committed-STL test checks all four files; part STLs are printable; `combined.stl`'s volume equals the sum of both parts (they don't overlap) and it fits the build volume.

### Mobile model picker (`webapp/src/components/ModelPicker.tsx`)

- Props: the same as `ModelList` (`models`, `selectedSlug`, `onSelect`). It wraps `ModelList` and replaces it in `App.tsx`'s sidebar `nav`.
- State: `open` (boolean), closed by default.
- Toggle button: `md:hidden`, full width, shows the selected model's name and a chevron that turns when open. It has `aria-expanded` and `aria-controls` pointing to the list wrapper, and `aria-label` "Choose model (current: <name>)".
- List wrapper: always visible from `md` up (`md:block`, laid out as today). Below `md` it is hidden unless `open`. When open, it is positioned absolutely under the bar (`max-h-[70vh] overflow-y-auto`, surface background, shadow, above the main area), with a fixed backdrop behind it that closes on click.
- `onSelect` closes the picker and calls the parent's `onSelect`. Escape closes it and moves focus back to the toggle. When it opens, focus moves to the selected option.
- `App.tsx`: the sidebar drops `max-md:max-h-[35vh]` and its scrolling on mobile, because only the bar takes space there. It gets `relative`, so the sheet is placed under the bar.

Tests (`ModelPicker.test.tsx`; jsdom ignores media queries, so they check behavior, not visibility):
- closed by default, with `aria-expanded="false"` and the current name on the toggle;
- the toggle opens it and focuses the selected option;
- picking a model calls `onSelect` and closes it;
- Escape and the backdrop close it without calling `onSelect`, and Escape returns focus to the toggle.

`App.test.tsx` keeps passing unchanged, because the list stays in the DOM.

### README

"Adding a model": replace "exactly one `.stl` file" with the `files` list, its order, the optional `name`, STL-only, and the warnings for missing/unlisted files.

---

## Implementation Phases

### Phase 1 — Plan

This file.

### Phase 2 — List model files in `project.json`

**Depends on:** 1. **Parallel:** no.

Closes rmeissner/work_for_claus#5 (data side).

- `webapp/src/models/types.ts`, `buildModels.ts`, `buildModels.test.ts`
- `models/*/project.json`: add `files` (calibration cube, pyramid, star ornament with its current single STL)
- `ModelDetails.tsx`: pass `model.files[0].url` to `StlViewer` (temporary, until phase 3)
- Test fixtures using `stlUrl` (`App.test.tsx`, `ModelList.test.tsx`) → `files`
- README "Adding a model"

Estimate: ~200 lines, 9 files.

### Phase 3 — STL carousel

**Depends on:** 2. **Parallel:** with 4 and 5.

- `webapp/src/components/StlCarousel.tsx`, `StlCarousel.test.tsx`
- `ModelDetails.tsx`: render `StlCarousel` instead of `StlViewer`
- Add a screenshot to the PR description (e.g. with a temporary multi-file model, or after phase 5 is merged)

Estimate: ~220 lines, 3 files.

### Phase 4 — Downloadable file list

**Depends on:** 2. **Parallel:** with 3 and 5.

- `webapp/src/components/ModelFiles.tsx`, `ModelFiles.test.tsx`
- `ModelDetails.tsx`: render `ModelFiles` below the description

Estimate: ~150 lines, 3 files. Phases 3 and 4 both touch `ModelDetails.tsx` with a small change; whichever merges second rebases.

### Phase 5 — Star ornament part files

**Depends on:** 2. **Parallel:** with 3 and 4.

- `models/star-ornament/generate.py`, `test_generate.py`, `project.json`
- Generated `part-a.stl`, `part-b.stl`, `combined.stl` (not counted for review size)

Estimate: ~80 lines of code and tests.

### Phase 6 — Mobile model picker

**Depends on:** 1 (only the existing layout). **Parallel:** with 5.

- `webapp/src/components/ModelPicker.tsx`, `ModelPicker.test.tsx`
- `webapp/src/App.tsx`: render `ModelPicker` in the sidebar, adjust the mobile sidebar classes
- Add a phone-sized screenshot (closed and open) to the PR description, e.g. with a temporary model list of ~20 entries.

Estimate: ~180 lines, 3 files.

### Phase 7 — Cleanup

**Depends on:** 3, 4, 5, 6. **Parallel:** no.

- Remove `epics/2026_11_08_improve_stl_ux.md`.

---

## Open Questions and Assumptions

- **Title:** "SLT" in the request is read as "STL".
- **Star ornament files:** read as "keep the print plate, add one STL per part and a `combined.stl` of the assembled star". The order (combined first, so the preview opens on the finished star) is a suggestion; change it in `project.json`.
- **`combined.stl` is not a print file:** it is the assembled 3D star (the slot clearance leaves the parts unconnected); its label says it is the assembled star.
- **Labels:** `name` in a `files` entry is optional; the existing single-file models don't set it.
- **Strict `files`:** a `project.json` without `files` makes the model invalid. All models in the repository are migrated in phase 2, so nothing disappears.
- **No transition animation** between slides; can be added later with a CSS fade if wanted.
- **Mobile picker:** desktop stays as it is. There is no search field yet; it can be added later if the list gets very long.
