import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router'
import { ModelDetails } from './components/ModelDetails'
import { ModelList } from './components/ModelList'
import { ThemeToggle } from './components/ThemeToggle'
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
      <nav className="overflow-y-auto border-r border-border [grid-area:sidebar] max-md:max-h-[35vh] max-md:border-r-0 max-md:border-b">
        <ModelList
          models={models}
          selectedSlug={selected.slug}
          onSelect={(next) => navigate(modelPath(next))}
        />
      </nav>
      <main className="overflow-y-auto [grid-area:main] max-md:overflow-visible">
        <ModelDetails model={selected} />
      </main>
    </>
  )
}

function App({ models = repositoryModels }: { models?: Model[] }) {
  return (
    <div className="grid h-full grid-cols-[var(--spacing-sidebar)_minmax(0,1fr)] grid-rows-[auto_minmax(0,1fr)] [grid-template-areas:'header_main'_'sidebar_main'] max-md:h-auto max-md:min-h-full max-md:grid-cols-[minmax(0,1fr)] max-md:grid-rows-[auto_auto_1fr] max-md:[grid-template-areas:'header'_'sidebar'_'main']">
      <header className="flex items-center justify-between gap-2 border-r border-b border-border px-4 py-3 [grid-area:header] max-md:border-r-0">
        <h1 className="m-0 text-title whitespace-nowrap">Work for Claus</h1>
        <ThemeToggle />
      </header>
      <Routes>
        {models.length > 0 ? (
          <>
            <Route path="/:slug" element={<ModelRoute models={models} />} />
            <Route path="*" element={<Navigate to={modelPath(models[0].slug)} replace />} />
          </>
        ) : (
          <Route
            path="*"
            element={
              <main className="grid place-items-center overflow-y-auto text-muted [grid-area:main] max-md:overflow-visible">
                No models found
              </main>
            }
          />
        )}
      </Routes>
    </div>
  )
}

export default App
