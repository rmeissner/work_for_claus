import { useCallback, useEffect, useState } from 'react'

export type ThemePreference = 'system' | 'light' | 'dark'

export const THEME_STORAGE_KEY = 'theme'

const isPreference = (value: unknown): value is ThemePreference =>
  value === 'system' || value === 'light' || value === 'dark'

/** The stored preference; missing, invalid or unreadable storage means 'system'. */
function readPreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    return isPreference(stored) ? stored : 'system'
  } catch {
    return 'system'
  }
}

/**
 * Forces light/dark with `data-theme` on `<html>`; 'system' removes the attribute so the
 * CSS media query follows the OS live.
 */
function applyPreference(preference: ThemePreference) {
  if (preference === 'system') {
    delete document.documentElement.dataset.theme
  } else {
    document.documentElement.dataset.theme = preference
  }
}

/** The persisted theme preference and a setter that applies and stores it. */
export function useTheme() {
  const [preference, setPreferenceState] = useState(readPreference)

  useEffect(() => {
    applyPreference(preference)
  }, [preference])

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next)
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next)
    } catch {
      // Storage is unavailable (private mode, blocked): the choice only lasts for this visit.
    }
  }, [])

  return { preference, setPreference }
}
