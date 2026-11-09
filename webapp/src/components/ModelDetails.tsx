import type { Model } from '../models/types'
import { ModelFiles } from './ModelFiles'
import { StlCarousel } from './StlCarousel'

/** Right pane: the 3D preview, then the model's name and description. */
export function ModelDetails({ model }: { model: Model }) {
  return (
    <article className="flex h-full flex-col">
      <div className="min-h-preview-min flex-1 border-b border-border bg-surface max-md:h-[50vh] max-md:flex-none" data-testid="model-preview">
        {/* A key per model resets the carousel to its first file. */}
        <StlCarousel key={model.slug} files={model.files} />
      </div>
      <div className="px-5 py-4">
        <h2 className="m-0 mb-2 text-title">
          {model.name}{' '}
          <span className="text-sm text-muted">{/^v/i.test(model.version) ? model.version : `v${model.version}`}</span>
        </h2>
        <p className="m-0 whitespace-pre-wrap">{model.description}</p>
        <ModelFiles files={model.files} />
      </div>
    </article>
  )
}
