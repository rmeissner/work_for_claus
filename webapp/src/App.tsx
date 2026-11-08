import { ModelDetails } from './components/ModelDetails'
import { ModelList } from './components/ModelList'
import { useSelectedModel } from './hooks/useSelectedModel'
import { loadModels } from './models/loadModels'
import type { Model } from './models/types'

const repositoryModels = loadModels()

function App({ models = repositoryModels }: { models?: Model[] }) {
  const { selected, select } = useSelectedModel(models)

  return (
    <div className="app">
      <header className="app-header">
        <h1>Work for Claus</h1>
      </header>
      {selected ? (
        <>
          <nav className="app-sidebar">
            <ModelList models={models} selectedSlug={selected.slug} onSelect={select} />
          </nav>
          <main className="app-main">
            <ModelDetails model={selected} />
          </main>
        </>
      ) : (
        <main className="app-main app-empty">No models found</main>
      )}
    </div>
  )
}

export default App
