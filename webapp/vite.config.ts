import { readFileSync } from 'node:fs'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { searchForWorkspaceRoot } from 'vite'
import { defineConfig } from 'vitest/config'

const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'))

/**
 * The short hash of the commit being built, from Cloudflare Pages' CF_PAGES_COMMIT_SHA
 * (set for production and preview builds), or `dev` for local and CI builds.
 */
function buildCommit(): string {
  return process.env.CF_PAGES_COMMIT_SHA?.slice(0, 7) || 'dev'
}

// https://vite.dev/config/
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
    __APP_COMMIT__: JSON.stringify(buildCommit()),
  },
  plugins: [react(), tailwindcss()],
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
