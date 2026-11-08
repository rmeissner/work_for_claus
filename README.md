# Work for Claus

This repo contains 3D models for our printer Claus

## Webapp

The `webapp/` folder contains a [Vite](https://vite.dev) + React + TypeScript app for browsing the models.

Requirements: Node.js 22 (see `.nvmrc`).

```bash
cd webapp
npm install
npm run dev        # start the dev server
npm run build      # type-check and build into webapp/dist
npm run lint       # lint with oxlint
npm run typecheck  # type-check only
npm test           # run the unit tests (Vitest)
```
