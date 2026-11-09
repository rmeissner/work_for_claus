# Plan: Cleanup and UX improvements

Component: Python tests (`models/*/test_generate.py`, `tools/stlkit/tests/`), `webapp/` (model schema, header, model details, icons), `models/*/project.json`, `README.md`.

PR strategy: merge each

---

## Overview

Three small, independent improvements:

1. **Shared tests only:** the model-specific tests (`models/*/test_generate.py`) are removed. Models are reviewed through the rendered preview, and these tests mostly restate the generator's parameters. The only check worth keeping, "the committed STLs match what `generate.py` writes", becomes one generic test in `tools/stlkit/tests/` that covers every model script.
2. **Versions:** every model gets a hand-maintained `version` in its `project.json`, shown next to its name. The app shows its `package.json` version and the commit it was built from (e.g. `v0.1.0 · 3f73489`) in the header.
3. **App icon:** the Vite placeholder favicon is replaced by a minimal icon of Claus, our printer (a dark frame with two googly eyes), plus PNG app icons and a web manifest so it can be added to a home screen.

Phases 1–4 don't depend on each other and can run in parallel. Phase 5 (remove this plan) depends on all of them.

---

## Architecture Decision

- **One generic "STLs are up to date" test.** `tools/stlkit/tests/test_models.py` is parametrized over `models/*/generate.py`. For each script it copies the model folder into `tmp_path`, loads the copy with `load_script` and calls its `main()`. The scripts write next to `__file__` (`Path(__file__).with_name(...)`), so the fresh STLs land in the copy without changing any script. The test then asserts that every `.stl` in the copy is byte-identical to the committed one. This keeps `load_script` in use; the scripts already put `tools/` on `sys.path` themselves.
- **Model version is a manual field.** `project.json` gets a required, non-empty `version` string (free form, e.g. `"1.0"`), bumped by hand when a model changes. It is validated by the existing zod schema in `buildModels.ts`; a folder without it is skipped with a warning like other invalid `project.json` files. All existing models start at `"1.0"`.
- **App version = `package.json` version + git hash, injected at build time.** `vite.config.ts` reads `version` from `package.json` and the commit from `CF_PAGES_COMMIT_SHA` (set by the Cloudflare Pages build that deploys the app and its PR previews), else `git rev-parse HEAD`, else `dev`; the hash is shortened to 7 characters, and passes `__APP_VERSION__` and `__APP_COMMIT__` through Vite's `define`. They are declared in `src/vite-env.d.ts` (or a new `src/globals.d.ts`). `package.json` moves from the placeholder `0.0.0` to `0.1.0`; it is bumped by hand.
- **Icons are static files in `webapp/public/`.** One hand-written SVG (`favicon.svg`) is the source; the PNGs are rendered from it once with the pre-installed Chromium/Playwright and committed. No new npm dependency. The icon has its own dark background, so it reads on light and dark browser tabs.

### Alternatives Considered

- **Model version from a content hash or the last git commit of the folder:** no manual bumps, but not a version a human can talk about; the git variant also needs full history in CI and hosting (shallow clones). Rejected in favour of a manual field.
- **Keep a slimmed `test_generate.py` per model with only the up-to-date check:** still one test file per model to copy around; the generic test covers new models automatically.
- **A `favicon.ico`:** every current browser supports SVG favicons; the 32 px PNG covers the rest. No `.ico` tool is needed.
- **Generate PNGs in the build (e.g. `vite-plugin-pwa` or `sharp`):** a new dependency for files that change once.

---

## User Flow

- The header shows the app version under the title.
- The model details show the version next to the model's name.
- The browser tab and the home-screen shortcut show Claus.

### Page Layout

```
+---------------------------+-------------------------------------+
| Work for Claus      [◐]   |                                     |
| v0.1.0 · 3f73489          |          3D preview                 |
+---------------------------+                                     |
| Calibration cube          |                                     |
| > 24-point star           +-------------------------------------+
| Pyramid                   | 24-point star  v1.0                 |
| Star ornament             | Star with 24 points …               |
|                           | Files …                             |
+---------------------------+-------------------------------------+
```

The versions use the muted text color and a smaller font size.

---

## Tech Specs

### Shared STL test (phase 1)

```python
# tools/stlkit/tests/test_models.py
MODELS = Path(__file__).resolve().parents[3] / "models"
SCRIPTS = sorted(MODELS.glob("*/generate.py"))

@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.parent.name)
def test_committed_stls_are_up_to_date(tmp_path, script):
    copy = shutil.copytree(script.parent, tmp_path / script.parent.name)
    load_script(copy / "generate.py").main()
    for stl in sorted(script.parent.glob("*.stl")):
        assert (copy / stl.name).read_bytes() == stl.read_bytes(), stl.name
```

The test fails when a model script has no `main()` (every generator must be runnable). The `.stl` files are compared after `main()` rewrote the copies, so a script that stops writing a committed file would pass; that is acceptable (the webapp warns about listed but missing files).

Removed: `models/star-24/test_generate.py`, `models/star-ornament/test_generate.py`. `pytest.ini` keeps `testpaths = tools models`, so a model that adds its own tests later still runs; `--import-mode=importlib` stays.

### Model version (phase 2)

- `project.json`: `"version": "1.0"` after `"name"` in all four models.
- `buildModels.ts`: `version: z.string().refine((v) => v.trim() !== '', 'version must not be empty')`.
- `types.ts`: `Model.version: string`.
- `ModelDetails.tsx`: `<h2>{model.name} <span className="text-muted text-sm">v{model.version}</span></h2>` (no `v` prefix if the version already starts with `v`).
- Tests: `buildModels.test.ts` (missing and empty version skip the model), `App.test.tsx` fixtures get a version, and the details show it.

### App version (phase 3)

```ts
// vite.config.ts
const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'))
function gitCommit(): string {
  // Cloudflare Pages sets CF_PAGES_COMMIT_SHA for production and preview builds.
  if (process.env.CF_PAGES_COMMIT_SHA) return process.env.CF_PAGES_COMMIT_SHA.slice(0, 7)
  try {
    return execSync('git rev-parse --short=7 HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim()
  } catch {
    return 'dev'
  }
}
// defineConfig({ define: { __APP_VERSION__: JSON.stringify(pkg.version), __APP_COMMIT__: JSON.stringify(gitCommit()) }, … })
```

- A small `AppVersion` component renders `v{__APP_VERSION__} · {__APP_COMMIT__}` under the `<h1>` in the header, muted and small, and links the commit to `https://github.com/rmeissner/work_for_claus/commit/<hash>` unless it is `dev`.
- Test: the header shows `v` + the version from `package.json` (Vitest uses the same config, so `define` applies).

### App icon (phase 4)

- `webapp/public/favicon.svg` (replaces the Vite logo), `viewBox="0 0 64 64"`:
  - a rounded square in the printer's dark gray (`#2f3237`), the frame;
  - a darker inner opening (`#17191c`) below a thick top bar;
  - two googly eyes on the top bar: white circles with black pupils, the pupils slightly off-center in different directions;
  - a thin teal (`#1fb5a5`, the filament in the photo) build plate line in the opening.
  - No text or logo; recognizable at 16 px.
- PNGs rendered from the SVG: `favicon-32.png`, `apple-touch-icon.png` (180), `icon-192.png`, `icon-512.png`.
- `webapp/public/manifest.webmanifest`: `name` "Work for Claus", `short_name` "Claus", the 192/512 icons, `display: standalone`, `background_color`/`theme_color` `#2f3237`.
- `index.html`: SVG icon, 32 px PNG fallback, `apple-touch-icon`, `manifest` and `<meta name="theme-color">`.
- README: one line on how the PNGs were rendered from the SVG (Playwright screenshot of the SVG at each size), so they can be regenerated.

---

## Implementation Phases

### Phase 1 — Replace the model tests with a shared STL check

- **Depends on:** nothing. **Can run in parallel** with phases 2, 3 and 4.
- Add `tools/stlkit/tests/test_models.py` (see Tech Specs), delete `models/star-24/test_generate.py` and `models/star-ornament/test_generate.py`.
- README **Generating models**: model folders hold only `generate.py` and the STLs; model scripts are not unit tested, `pytest` checks the toolkit and that the committed STLs are up to date; every `generate.py` must have a `main()` that writes next to the script. Drop the `test_generate.py` / `load_script` instructions.
- About −320 / +40 lines, 4 files.

### Phase 2 — Show a version per model

- **Depends on:** nothing. **Can run in parallel** with phases 1, 3 and 4.
- `project.json` × 4, `buildModels.ts`, `types.ts`, `ModelDetails.tsx`, `buildModels.test.ts`, `App.test.tsx` (fixtures and a version assertion), other test fixtures that build a `Model`, README **Adding a model** (the new required key).
- About 60–90 lines, ≤ 10 files.

### Phase 3 — Show the app version

- **Depends on:** nothing. **Can run in parallel** with phases 1, 2 and 4.
- `package.json` version `0.1.0` (and `package-lock.json`'s root entries), `vite.config.ts`, the global declarations, a new `AppVersion.tsx` with a test, `App.tsx` header, README **Webapp** (where the version comes from, bump `package.json` by hand).
- About 60–80 lines.

### Phase 4 — Add the Claus app icon

- **Depends on:** nothing. **Can run in parallel** with phases 1, 2 and 3.
- `webapp/public/favicon.svg`, the four PNGs, `manifest.webmanifest`, `index.html`, README.
- About 40 lines plus binary files. Include a screenshot of the icon at 16, 32 and 180 px in the PR.

### Phase 5 — Remove the epic plan

- **Depends on:** phases 1–4.
- Delete `epics/2026_11_09_cleanup_ux.md` after checking every phase is merged.

---

## Open Questions and Assumptions

- **Version bumps are not enforced.** Nothing checks that a changed model or app bumps its version. A CI check (a changed `models/<slug>/` must change `version`) could follow later if versions get forgotten.
- The app version uses the commit the build ran on: on Cloudflare Pages (production and PR previews) the pushed commit; in GitHub CI for a pull request GitHub's merge commit, which only matters for the CI build, not for anything users see.
- The GitHub link in the app version assumes the repository stays at `rmeissner/work_for_claus`.
- The icon is drawn by hand as SVG from the photo; the result is shown in the phase 4 PR for feedback.
