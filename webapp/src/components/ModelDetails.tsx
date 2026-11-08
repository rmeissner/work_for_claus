import { lazy, Suspense } from 'react'
import type { Model } from '../models/types'

// three.js is large, so the viewer is loaded in its own chunk and doesn't
// delay the first paint of the list.
const StlViewer = lazy(() =>
  import('./StlViewer').then((module) => ({ default: module.StlViewer })),
)

/** Right pane: the 3D preview, then the model's name and description. */
export function ModelDetails({ model }: { model: Model }) {
  return (
    <article className="flex h-full flex-col">
      <div className="min-h-preview-min flex-1 border-b border-border bg-surface max-md:h-[50vh] max-md:flex-none" data-testid="model-preview">
        <Suspense fallback={<p className="m-0 grid h-full place-items-center text-muted">Loading viewer…</p>}>
          {/* A key per model resets the viewer's error state on selection. */}
          <StlViewer key={model.slug} url={model.stlUrl} />
        </Suspense>
      </div>
      <div className="px-5 py-4">
        <h2 className="m-0 mb-2 text-title">{model.name}</h2>
        <p className="m-0 whitespace-pre-wrap">{model.description}</p>
      </div>
    </article>
  )
}
