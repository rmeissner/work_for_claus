import { useEffect, useRef, useState } from 'react'
import { CogIcon } from './icons/CogIcon'
import { PLATE_SIZE_MM } from './plate'
import type { PreviewSettings } from './previewSettings'

export const ROUND_BUTTON =
  'grid size-8 cursor-pointer place-items-center rounded-full border border-border bg-bg text-fg hover:bg-hover focus-visible:outline-2 focus-visible:outline-accent'

interface PreviewSettingsDialogProps {
  settings: PreviewSettings
  onChange: (patch: Partial<PreviewSettings>) => void
}

/** The cog button and the modal dialog with the preview settings. */
export function PreviewSettingsDialog({ settings, onChange }: PreviewSettingsDialogProps) {
  const [open, setOpen] = useState(false)
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    else if (!open && element.open) element.close()
  }, [open])

  return (
    <>
      <button type="button" aria-label="Preview settings" className={ROUND_BUTTON} onClick={() => setOpen(true)}>
        <CogIcon />
      </button>
      <dialog
        ref={dialog}
        aria-labelledby="preview-settings-title"
        onClose={() => setOpen(false)}
        // A click on the backdrop targets the dialog element itself.
        onClick={(event) => {
          if (event.target === event.currentTarget) setOpen(false)
        }}
        className="m-auto rounded-item border border-border bg-bg p-0 text-fg backdrop:bg-black/40"
      >
        <div className="p-4" data-testid="preview-settings-content">
        <h2 id="preview-settings-title" className="m-0 mb-3 text-base font-semibold">
          Preview settings
        </h2>
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.showPlate}
              onChange={(event) => onChange({ showPlate: event.target.checked })}
            />
            Show print plate ({PLATE_SIZE_MM} × {PLATE_SIZE_MM} mm)
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.usePartColors}
              onChange={(event) => onChange({ usePartColors: event.target.checked })}
            />
            Use part colors
          </label>
          <label className="flex items-center gap-2 pl-6">
            Model color
            <input
              type="color"
              value={settings.modelColor}
              disabled={settings.usePartColors}
              onChange={(event) => onChange({ modelColor: event.target.value })}
              className="disabled:cursor-not-allowed disabled:opacity-50"
            />
          </label>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="cursor-pointer rounded-item border border-border bg-surface px-3 py-1 text-fg hover:bg-hover focus-visible:outline-2 focus-visible:outline-accent"
          >
            Close
          </button>
        </div>
        </div>
      </dialog>
    </>
  )
}
