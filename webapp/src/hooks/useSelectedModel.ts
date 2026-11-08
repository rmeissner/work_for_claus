import { useCallback, useSyncExternalStore } from 'react'
import type { Model } from '../models/types'

function subscribe(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

/** Returns the slug in a hash like `#/<slug>`, or an empty string. */
function slugFromHash(): string {
  return decodeURIComponent(window.location.hash.replace(/^#\/?/, ''))
}

/**
 * Keeps the selected model in `location.hash` (`#/<slug>`), so links can be
 * shared and a reload keeps the selection. Falls back to the first model when
 * the hash is empty or names an unknown slug.
 */
export function useSelectedModel(models: Model[]) {
  const slug = useSyncExternalStore(subscribe, slugFromHash)
  const selected = models.find((model) => model.slug === slug) ?? models[0]
  const select = useCallback((next: string) => {
    window.location.hash = `/${encodeURIComponent(next)}`
  }, [])
  return { selected, select }
}
