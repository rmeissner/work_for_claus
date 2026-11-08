import type { Model } from '../models/types'
import styles from './ModelDetails.module.css'

/** Right pane: the 3D preview slot, then the model's name and description. */
export function ModelDetails({ model }: { model: Model }) {
  return (
    <article className={styles.details}>
      <div className={styles.preview} data-testid="model-preview">
        3D preview
      </div>
      <div className={styles.text}>
        <h2 className={styles.name}>{model.name}</h2>
        <p className={styles.description}>{model.description}</p>
      </div>
    </article>
  )
}
