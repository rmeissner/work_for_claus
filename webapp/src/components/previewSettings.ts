import { useCallback, useState } from 'react'
import { z } from 'zod'

const HEX_COLOR = /^#[0-9a-f]{6}$/i

/**
 * Each field falls back to its default on its own, and anything that is not an
 * object falls back to the defaults as a whole.
 */
export const previewSettingsSchema = z
  .object({
    showPlate: z.boolean().catch(false),
    usePartColors: z.boolean().catch(true),
    // `#rrggbb`; today's color for files without part colors.
    modelColor: z.string().regex(HEX_COLOR).catch('#b0b4ba'),
  })
  .catch(() => DEFAULT_PREVIEW_SETTINGS)

export type PreviewSettings = z.infer<typeof previewSettingsSchema>

export const PREVIEW_SETTINGS_STORAGE_KEY = 'preview_settings.v1.json_object'

export const DEFAULT_PREVIEW_SETTINGS: PreviewSettings = previewSettingsSchema.parse({})

/** The stored settings; missing, invalid or unreadable storage means the defaults. */
function readSettings(): PreviewSettings {
  try {
    const raw = localStorage.getItem(PREVIEW_SETTINGS_STORAGE_KEY)
    return previewSettingsSchema.parse(raw === null ? undefined : JSON.parse(raw))
  } catch {
    return DEFAULT_PREVIEW_SETTINGS
  }
}

/** The persisted preview settings and an updater that applies and stores a partial change. */
export function usePreviewSettings() {
  const [settings, setSettings] = useState(readSettings)

  const updateSettings = useCallback((patch: Partial<PreviewSettings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch }
      try {
        localStorage.setItem(PREVIEW_SETTINGS_STORAGE_KEY, JSON.stringify(next))
      } catch {
        // Storage is unavailable (private mode, blocked): the choice only lasts for this visit.
      }
      return next
    })
  }, [])

  return { settings, updateSettings }
}
