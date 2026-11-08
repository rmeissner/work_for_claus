import { lazy, Suspense } from 'react'
import type { Model } from '../models/types'
import styles from './ModelDetails.module.css'

// three.js is large, so the viewer is loaded in its own chunk and doesn't
// delay the first paint of the list.
const StlViewer = lazy(() =>
  import('./StlViewer').then((module) => ({ default: module.StlViewer })),
)

/** Right pane: the 3D preview, then the model's name and description. */
export function ModelDetails({ model }: { model: Model }) {
  return (
    <article className={styles.details}>
      <div className={styles.preview} data-testid="model-preview">
        <Suspense fallback={<p className={styles.loading}>Loading viewer…</p>}>
          {/* A key per model resets the viewer's error state on selection. */}
          <StlViewer key={model.slug} url={model.stlUrl} />
        </Suspense>
      </div>
      <div className={styles.text}>
        <h2 className={styles.name}>{model.name}</h2>
        <p className={styles.description}>{model.description}</p>
      </div>
    </article>
  )
}
