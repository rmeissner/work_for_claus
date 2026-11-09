import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  DEFAULT_PREVIEW_SETTINGS,
  PREVIEW_SETTINGS_STORAGE_KEY,
  usePreviewSettings,
} from './previewSettings'

const store = (value: unknown) =>
  localStorage.setItem(PREVIEW_SETTINGS_STORAGE_KEY, JSON.stringify(value))

describe('usePreviewSettings', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => vi.restoreAllMocks())

  it('uses the defaults without storage', () => {
    const { result } = renderHook(() => usePreviewSettings())
    expect(result.current.settings).toEqual(DEFAULT_PREVIEW_SETTINGS)
  })

  it('reads valid stored settings', () => {
    store({ showPlate: true, usePartColors: false, modelColor: '#00ff00' })
    const { result } = renderHook(() => usePreviewSettings())
    expect(result.current.settings).toEqual({ showPlate: true, usePartColors: false, modelColor: '#00ff00' })
  })

  it('falls back per field for invalid values', () => {
    store({ showPlate: true, usePartColors: 'no', modelColor: 'red' })
    const { result } = renderHook(() => usePreviewSettings())
    expect(result.current.settings).toEqual({ ...DEFAULT_PREVIEW_SETTINGS, showPlate: true })
  })

  it.each(['not json', '[]', '5'])('uses the defaults for stored %s', (raw) => {
    localStorage.setItem(PREVIEW_SETTINGS_STORAGE_KEY, raw)
    const { result } = renderHook(() => usePreviewSettings())
    expect(result.current.settings).toEqual(DEFAULT_PREVIEW_SETTINGS)
  })

  it('applies and stores a partial update', () => {
    const { result } = renderHook(() => usePreviewSettings())
    act(() => result.current.updateSettings({ modelColor: '#123456' }))
    expect(result.current.settings.modelColor).toBe('#123456')
    expect(JSON.parse(localStorage.getItem(PREVIEW_SETTINGS_STORAGE_KEY) ?? '')).toEqual({
      ...DEFAULT_PREVIEW_SETTINGS,
      modelColor: '#123456',
    })
  })

  it('survives a throwing localStorage', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    const { result } = renderHook(() => usePreviewSettings())
    expect(result.current.settings).toEqual(DEFAULT_PREVIEW_SETTINGS)
    act(() => result.current.updateSettings({ usePartColors: false }))
    expect(result.current.settings.usePartColors).toBe(false)
  })
})
