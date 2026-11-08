# Work for Claus

This repo contains 3D models for our printer Claus

## Webapp

The `webapp/` folder contains a [Vite](https://vite.dev) + React + TypeScript app for browsing the models.

Requirements: Node.js 26 (see `.nvmrc`).

```bash
cd webapp
npm install
npm run dev        # start the dev server
npm run build      # type-check and build into webapp/dist
npm run lint       # lint with oxlint
npm run typecheck  # type-check only
npm test           # run the unit tests (Vitest)
```

## Adding a model

Each model lives in its own folder under `models/`. The folder name is the model's slug (used in links):

```
models/
└── calibration-cube/
    ├── project.json
    └── cube.stl
```

- `project.json` holds a non-empty `name` and a plain-text `description`; other keys are ignored:

  ```json
  {
    "name": "Calibration cube",
    "description": "20 mm cube to calibrate X/Y/Z steps."
  }
  ```

- Put exactly one `.stl` file in the folder. If there are several, the first one in alphabetical order is used.
- Folders with a missing or invalid `project.json`, or without an STL file, are skipped with a warning in the browser console.
