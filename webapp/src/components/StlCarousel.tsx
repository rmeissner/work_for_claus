import { lazy, Suspense, useState, type KeyboardEvent } from 'react'
import type { ModelFile } from '../models/types'
import { visibleDots } from './visibleDots'

// three.js is large, so the viewer is loaded in its own chunk and doesn't
// delay the first paint of the list.
const StlViewer = lazy(() =>
  import('./StlViewer').then((module) => ({ default: module.StlViewer })),
)

const ROUND_BUTTON =
  'grid size-8 cursor-pointer place-items-center rounded-full border border-border bg-bg text-fg hover:bg-hover focus-visible:outline-2 focus-visible:outline-accent'

function Chevron({ direction }: { direction: 'left' | 'right' }) {
  return (
    <svg viewBox="0 0 16 16" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={direction === 'left' ? 'M10 3 5 8l5 5' : 'M6 3l5 5-5 5'} />
    </svg>
  )
}

/** One file at a time in the 3D viewer, with dots and prev/next buttons below. */
export function StlCarousel({ files }: { files: ModelFile[] }) {
  const [index, setIndex] = useState(0)
  const length = files.length
  const current = files[index]
  const previous = () => setIndex((i) => (i - 1 + length) % length)
  const next = () => setIndex((i) => (i + 1) % length)

  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.target !== event.currentTarget) return
    if (event.key === 'ArrowLeft') previous()
    else if (event.key === 'ArrowRight') next()
    else return
    event.preventDefault()
  }

  return (
    <section
      aria-roledescription="carousel"
      aria-label="Model files"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className="flex h-full flex-col outline-none focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
    >
      <div
        role="group"
        aria-roledescription="slide"
        aria-label={`${index + 1} of ${length}: ${current.name}`}
        className="min-h-0 flex-1"
      >
        <Suspense fallback={<p className="m-0 grid h-full place-items-center text-muted">Loading viewer…</p>}>
          {/* A key per file resets the viewer's error state on switching. */}
          <StlViewer key={current.url} url={current.url} />
        </Suspense>
      </div>
      {length > 1 && (
        <div className="flex items-center justify-center gap-3 py-2">
          <button type="button" aria-label="Previous file" className={ROUND_BUTTON} onClick={previous}>
            <Chevron direction="left" />
          </button>
          <div className="flex items-center gap-2">
            {visibleDots(index, length).map((dot) => (
              <button
                key={dot.index}
                type="button"
                aria-label={`Show ${files[dot.index].name}`}
                title={files[dot.index].name}
                aria-current={dot.index === index ? 'true' : undefined}
                onClick={() => setIndex(dot.index)}
                className="grid size-4 cursor-pointer place-items-center rounded-full focus-visible:outline-2 focus-visible:outline-accent"
              >
                <span
                  className={`rounded-full ${dot.small ? 'size-1.5' : 'size-2.5'} ${dot.index === index ? 'bg-accent' : 'bg-muted opacity-50'}`}
                />
              </button>
            ))}
          </div>
          <button type="button" aria-label="Next file" className={ROUND_BUTTON} onClick={next}>
            <Chevron direction="right" />
          </button>
        </div>
      )}
    </section>
  )
}
