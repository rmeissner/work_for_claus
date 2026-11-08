import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router'
import { ModelDetails } from './components/ModelDetails'
import { ModelList } from './components/ModelList'
import { loadModels } from './models/loadModels'
import type { Model } from './models/types'

const repositoryModels = loadModels()

const modelPath = (slug: string) => `/${encodeURIComponent(slug)}`

/** Shows the model named by the `:slug` route parameter, or redirects to the first model. */
function ModelRoute({ models }: { models: Model[] }) {
  const { slug } = useParams()
  const navigate = useNavigate()
  const selected = models.find((model) => model.slug === slug)

  if (!selected) {
    return <Navigate to={modelPath(models[0].slug)} replace />
  }

  return (
    <>
      <nav className="app-sidebar">
        <ModelList
          models={models}
          selectedSlug={selected.slug}
          onSelect={(next) => navigate(modelPath(next))}
        />
      </nav>
      <main className="app-main">
        <ModelDetails model={selected} />
      </main>
    </>
  )
}

function App({ models = repositoryModels }: { models?: Model[] }) {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Work for Claus</h1>
      </header>
      <Routes>
        {models.length > 0 ? (
          <>
            <Route path="/:slug" element={<ModelRoute models={models} />} />
            <Route path="*" element={<Navigate to={modelPath(models[0].slug)} replace />} />
          </>
        ) : (
          <Route path="*" element={<main className="app-main app-empty">No models found</main>} />
        )}
      </Routes>
    </div>
  )
}

export default App
