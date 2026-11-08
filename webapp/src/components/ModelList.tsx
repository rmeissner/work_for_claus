import { useRef, type KeyboardEvent } from 'react'
import type { Model } from '../models/types'

interface ModelListProps {
  models: Model[]
  selectedSlug: string
  onSelect: (slug: string) => void
}

/** Listbox of models; arrow keys move the selection (roving tabindex). */
export function ModelList({ models, selectedSlug, onSelect }: ModelListProps) {
  const listRef = useRef<HTMLUListElement>(null)

  function handleKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    const current = models.findIndex((model) => model.slug === selectedSlug)
    const next = {
      ArrowDown: Math.min(current + 1, models.length - 1),
      ArrowUp: Math.max(current - 1, 0),
      Home: 0,
      End: models.length - 1,
    }[event.key]
    if (next === undefined) return
    event.preventDefault()
    onSelect(models[next].slug)
    listRef.current?.querySelectorAll<HTMLElement>('[role="option"]')[next]?.focus()
  }

  return (
    <ul
      ref={listRef}
      role="listbox"
      aria-label="Models"
      className="m-0 list-none p-1"
      onKeyDown={handleKeyDown}
    >
      {models.map((model) => {
        const selected = model.slug === selectedSlug
        return (
          <li
            key={model.slug}
            role="option"
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            className="cursor-pointer rounded-item px-3 py-2 select-none hover:bg-hover focus-visible:-outline-offset-2 focus-visible:outline-2 focus-visible:outline-accent aria-selected:bg-selected-bg aria-selected:font-semibold aria-selected:text-selected-fg"
            onClick={() => onSelect(model.slug)}
          >
            {model.name}
          </li>
        )
      })}
    </ul>
  )
}
