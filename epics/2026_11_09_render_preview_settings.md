# Plan: Render Preview Settings

Component: `webapp/` (the 3D preview: `StlViewer`, `StlCarousel` and a new settings dialog).

PR strategy: merge each

---

## Overview

Three improvements to the 3D preview on the model page:

- **Rotation around the model:** today the camera orbits around the world origin `(0, 0, 0)`, which is not the center of the displayed model, so dragging swings the model around instead of turning it in place. The camera should orbit around the center of what is shown.
- **Single color:** assembled files (e.g. `combined.stl`) carry per-part colors. That looks great for seeing the parts, but a real print has one filament color. A setting overrides the part colors with one chosen color.
- **Print plate:** a setting draws Claus' build plate (220 × 220 mm) under the model, so you get a feeling for the size, e.g. how much of the plate a "Print plate" file fills.

The two settings live in a dialog opened by a cog button at the bottom right of the preview, on the same row as the prev/next arrows. The settings are stored in `localStorage` and apply to every model and file.

PRs:

1. **Plan** (this PR): the epic specification only.
2. **Orbit around the model:** place the model on the bed origin ourselves (replacing drei's `Stage`) and orbit around its center. Depends on 1.
3. **Settings dialog and single color:** the settings hook, the cog button, the dialog, and the color override. Depends on 1. **Can run in parallel with 2.**
4. **Print plate:** the plate setting and the plate mesh. Depends on 2 and 3.
5. **Cleanup:** remove this specification file. Depends on 4.

---

## Architecture Decision

### Own framing instead of drei's `Stage`

`Stage` centers its children and fits the camera to them, but it centers *everything* inside it: a plate inside `Stage` would be centered together with the model, and the model would no longer sit on the plate the way a slicer shows it. The `OrbitControls` target also stays at the world origin, which is where the rotation problem comes from.

So `StlViewer` drops `Stage` and frames the model itself:

1. Rotate the geometry from Z-up (STL) to Y-up (three.js) as today.
2. Translate it so its bounding box is centered on X/Z and its bottom is at `y = 0`. This is exactly where a slicer puts it on the bed. The generated plate files are already centered on the XY origin (`layout_on_plate`), so the plate preview matches the slicer.
3. Compute the bounding box of what is shown (the model, plus the plate when it is on), set the `OrbitControls` target to its center, and place the camera so the box fits (same fit margin as today's `adjustCamera={2}`).

The framing math is a pure function (`frameBox(box, fov) → { target, cameraPosition }`) so it can be unit tested without WebGL.

### Settings as one small persisted hook

`usePreviewSettings()` mirrors `useTheme()`: it reads a JSON object from `localStorage` (key `previewSettings`), validates it with `zod` (already a dependency), falls back to the defaults for missing, invalid or unreadable storage, and writes on change (ignoring storage errors). It is used in `StlCarousel`, which owns the cog button and the dialog and passes the settings to `StlViewer` as props. The settings survive switching files and models because the carousel key changes but the stored value does not.

### Native `<dialog>`

The dialog is a native `<dialog>` opened with `showModal()`: focus trapping, Escape to close and the backdrop come for free, and it needs no new dependency. It is styled with the existing theme tokens.

### Alternatives Considered

- **Keep `Stage` and only move the `OrbitControls` target:** fixes rotation, but blocks the plate (see above).
- **drei `Bounds` for camera fitting:** it animates and refits on every change, and its observed behavior with `makeDefault` controls is what we are fixing. A small pure function is easier to test and to reason about.
- **Plate only for files named "Print plate":** fragile (it relies on a label) and the size comparison is useful for the assembled model too. The setting applies to every file instead.
- **Preset color swatches instead of a color picker:** a native `<input type="color">` is simpler and covers any filament color.
- **A settings popover library (Radix, Headless UI):** a new dependency for one dialog.

---

## User Flow

1. The user opens a model. The preview looks as before (part colors, no plate), but dragging now turns the model around its own center.
2. The user clicks the cog button (bottom right, `aria-label="Preview settings"`). A modal dialog "Preview settings" opens.
3. In the dialog:
   - **Show print plate** (checkbox, off by default): draws the 220 × 220 mm plate under the model and refits the camera to the plate.
   - **Use part colors** (checkbox, on by default). When off, the color input next to it is enabled and **Model color** (`<input type="color">`, default `#b0b4ba`, today's color for uncolored files) is used for the whole model, colored or not.
4. Changes apply immediately to the preview behind the dialog. **Close** (or Escape, or a click on the backdrop) closes it.
5. On reload, or on another model, the same settings are used.

### Page Layout

The bottom row of the preview. The arrows and dots stay centered; the cog is right aligned on the same row. For a model with a single file there are no arrows and dots, but the row is still shown with the cog only.

```
┌──────────────────────────────────────────────────┐
│                                                  │
│                    3D preview                    │
│                                                  │
├──────────────────────────────────────────────────┤
│                 (‹)  • ● • •  (›)            (⚙) │
└──────────────────────────────────────────────────┘
```

The dialog:

```
┌ Preview settings ───────────────────┐
│                                     │
│ [ ] Show print plate (220 × 220 mm) │
│ [x] Use part colors                 │
│     Model color  [■ #b0b4ba]        │
│                                     │
│                            [Close]  │
└─────────────────────────────────────┘
```

---

## Tech Specs

### Settings

```ts
// webapp/src/components/previewSettings.ts
export interface PreviewSettings {
  showPlate: boolean      // default false
  usePartColors: boolean  // default true
  modelColor: string      // default '#b0b4ba', a `#rrggbb` string
}
export const PREVIEW_SETTINGS_STORAGE_KEY = 'previewSettings'
export function usePreviewSettings(): {
  settings: PreviewSettings
  updateSettings: (patch: Partial<PreviewSettings>) => void
}
```

Each field is validated on its own, so one bad field falls back to its default without resetting the others.

### Viewer props

`StlViewer` gets `settings: PreviewSettings` next to `url`. The material is:

| Case | `color` | `vertexColors` |
|---|---|---|
| File has colors, `usePartColors` | `#ffffff` | `true` |
| File has no colors, `usePartColors` | `#b0b4ba` | `false` |
| `usePartColors` off | `modelColor` | `false` |

### Plate

- Constant `PLATE_SIZE_MM = 220` in one place (`webapp/src/components/plate.ts`), with a comment that it is Claus' build plate.
- A thin box (220 × 2 × 220 mm) with its top at `y = 0`, centered on the origin, in a neutral grey that reads in light and dark themes, plus a 10 mm grid (`gridHelper`) just above its top (`y = 0.05`) to avoid z-fighting.
- When `showPlate` is on, the framed box is the union of the model's and the plate's boxes, so the camera shows the whole plate; the target is the center of that box.
- The camera far plane must cover the plate (e.g. `far` derived from the framed box size).

### Tests (Vitest, jsdom)

- `frameBox`: the target is the box center, the camera looks at it from the current direction, and a bigger box moves the camera further away.
- Model placement: a geometry offset from the origin ends up centered on X/Z with its bottom at `y = 0`.
- `usePreviewSettings`: defaults without storage, reads valid storage, per-field fallback for invalid values, writes on update, survives a throwing `localStorage`.
- `StlCarousel`: the cog is shown for one and for several files; clicking it opens the dialog; toggling a checkbox calls through to the viewer props; the color input is disabled while part colors are used. jsdom may lack `HTMLDialogElement.showModal`; stub it in `src/test/setup.ts` if needed.
- `StlViewer`: the material follows the table above; the plate is rendered only when `showPlate` is on (with the fiber/drei mocks the existing tests use).
- Manual: `npm run dev`, check rotation, the dialog, and the plate with `star-24`'s "Print plate" and "Assembled star" files in light and dark theme; screenshot for the PR.

### Docs

The README's webapp section gets one or two sentences about the preview settings (in phase 3) and the plate size (in phase 4).

---

## Implementation Phases

### Phase 1 — Plan

This PR: the specification only.

### Phase 2 — Orbit around the model

**Depends on:** 1 (merged plan). **Can run in parallel:** yes, with phase 3.

- `webapp/src/components/StlViewer.tsx`: remove `Stage`; place the model on the bed origin (centered on X/Z, bottom at `y = 0`); set the `OrbitControls` target and the camera from `frameBox`. Keep today's lights and loading/error states.
- `webapp/src/components/frameBox.ts` (new): the pure framing function and the placement helper.
- `webapp/src/components/frameBox.test.ts` (new), `StlViewer.test.tsx` (update the drei mock).

### Phase 3 — Settings dialog and single color

**Depends on:** 1 (merged plan). **Can run in parallel:** yes, with phase 2.

- `webapp/src/components/previewSettings.ts` (new) and its test: the settings type, defaults and `usePreviewSettings`. `showPlate` is part of the type and the storage already, but not shown in the dialog until phase 4.
- `webapp/src/components/PreviewSettingsDialog.tsx` (new): the cog button and the dialog with the color settings.
- `webapp/src/components/StlCarousel.tsx`: the bottom row as a three-column layout (arrows and dots centered, cog right), shown for one file too; pass the settings to `StlViewer`.
- `webapp/src/components/StlViewer.tsx`: the `settings` prop and the material table.
- Tests for the dialog, the carousel and the viewer material; README sentence.

### Phase 4 — Print plate

**Depends on:** 2 and 3. **Can run in parallel:** no.

- `webapp/src/components/plate.ts` (new): `PLATE_SIZE_MM` and the plate box.
- `webapp/src/components/StlViewer.tsx`: render the plate and grid when `showPlate` is on; frame the union box.
- `webapp/src/components/PreviewSettingsDialog.tsx`: the "Show print plate" checkbox.
- Tests and README sentence.

### Phase 5 — Remove the plan

**Depends on:** 4. **Can run in parallel:** no.

- Delete `epics/2026_11_09_render_preview_settings.md`.

---

## Open Questions and Assumptions

- **Plate size:** Claus' plate is assumed to be 220 × 220 mm (the glider epic says "Claus' 220 mm plate"). It is one constant, easy to change.
- **Plate position:** the model is centered on the plate, like a slicer does by default. The generated plate files are centered on the origin, so they line up; hand-drawn STLs are centered too, whatever their original position.
- **Orbit target with the plate:** with the plate on, the camera orbits around the center of the framed box (plate plus model), not the model alone, so the whole plate stays in view while rotating.
- **Settings are global:** one setting for all models and files, not per model.
- **Default color** `#b0b4ba` is today's color for uncolored files; the user can pick any other.
- **Version bump:** `webapp/package.json`'s version is bumped by hand; it is left to the user, not part of these phases.
