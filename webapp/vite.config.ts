import react from '@vitejs/plugin-react'
import { searchForWorkspaceRoot } from 'vite'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  assetsInclude: ['**/*.stl'],
  build: {
    // Always emit STL files as fingerprinted assets, even small ones.
    assetsInlineLimit: (file) => (file.endsWith('.stl') ? false : undefined),
  },
  server: {
    fs: {
      // Allow serving the STL files from ../models (the repository root).
      allow: [searchForWorkspaceRoot(process.cwd()), '..'],
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
