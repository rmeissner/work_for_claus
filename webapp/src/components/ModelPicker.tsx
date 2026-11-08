import { useEffect, useId, useRef, useState, type KeyboardEvent } from 'react'
import type { Model } from '../models/types'
import { ModelList } from './ModelList'

interface ModelPickerProps {
  models: Model[]
  selectedSlug: string
  onSelect: (slug: string) => void
}

/**
 * Wraps the model list. From `md` up the list is always visible; below that
 * it collapses into a bar with the current model that opens the list as a sheet.
 */
export function ModelPicker({ models, selectedSlug, onSelect }: ModelPickerProps) {
  const [open, setOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)
  const listWrapperRef = useRef<HTMLDivElement>(null)
  // Arrow keys change the selection through onSelect; they must not close the sheet.
  const keyNavigation = useRef(false)
  const listId = useId()
  const selectedName = models.find((model) => model.slug === selectedSlug)?.name ?? ''

  useEffect(() => {
    if (open) {
      listWrapperRef.current
        ?.querySelector<HTMLElement>('[role="option"][aria-selected="true"]')
        ?.focus()
    }
  }, [open])

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape' && open) {
      setOpen(false)
      toggleRef.current?.focus()
    } else if (['ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) {
      keyNavigation.current = true
    }
  }

  function handleSelect(slug: string) {
    const viaKeyboard = keyNavigation.current
    keyNavigation.current = false
    if (!viaKeyboard) setOpen(false)
    onSelect(slug)
  }

  return (
    <div onKeyDownCapture={handleKeyDown} onClick={() => (keyNavigation.current = false)}>
      <button
        ref={toggleRef}
        type="button"
        aria-expanded={open}
        aria-controls={listId}
        aria-label={`Choose model (current: ${selectedName})`}
        className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left font-semibold hover:bg-hover focus-visible:-outline-offset-2 focus-visible:outline-2 focus-visible:outline-accent md:hidden"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="truncate">{selectedName}</span>
        <svg
          aria-hidden="true"
          viewBox="0 0 20 20"
          className={`size-4 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M5 8l5 5 5-5" />
        </svg>
      </button>
      {open && (
        <div
          data-testid="model-picker-backdrop"
          className="fixed inset-0 z-10 bg-black/40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <div
        ref={listWrapperRef}
        id={listId}
        className={`${open ? 'absolute inset-x-0 top-12 z-20 max-h-[70vh] overflow-y-auto border-b border-border bg-surface shadow-lg' : 'hidden'} md:static md:block md:max-h-none md:overflow-visible md:border-0 md:bg-transparent md:shadow-none`}
      >
        <ModelList models={models} selectedSlug={selectedSlug} onSelect={handleSelect} />
      </div>
    </div>
  )
}
