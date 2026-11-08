import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ThemeToggle } from './ThemeToggle'

const html = document.documentElement

afterEach(() => {
  vi.restoreAllMocks()
  delete html.dataset.theme
  localStorage.clear()
})

const radio = (name: string) => screen.getByRole('radio', { name })

describe('ThemeToggle', () => {
  it('is a labelled radio group that defaults to system', () => {
    render(<ThemeToggle />)
    expect(screen.getByRole('group', { name: 'Theme' })).toBeInTheDocument()
    expect(screen.getAllByRole('radio').map((r) => r.getAttribute('value'))).toEqual([
      'system',
      'light',
      'dark',
    ])
    expect(radio('System')).toBeChecked()
    expect(html).not.toHaveAttribute('data-theme')
  })

  it('sets and removes data-theme and persists the choice', () => {
    render(<ThemeToggle />)
    fireEvent.click(radio('Dark'))
    expect(html.dataset.theme).toBe('dark')
    expect(localStorage.getItem('theme')).toBe('dark')
    expect(radio('Dark')).toBeChecked()

    fireEvent.click(radio('Light'))
    expect(html.dataset.theme).toBe('light')
    expect(localStorage.getItem('theme')).toBe('light')

    fireEvent.click(radio('System'))
    expect(html).not.toHaveAttribute('data-theme')
    expect(localStorage.getItem('theme')).toBe('system')
  })

  it('reflects a stored preference on the first render', () => {
    localStorage.setItem('theme', 'dark')
    render(<ThemeToggle />)
    expect(radio('Dark')).toBeChecked()
    expect(html.dataset.theme).toBe('dark')
  })

  it('falls back to system for an invalid stored value', () => {
    localStorage.setItem('theme', 'purple')
    render(<ThemeToggle />)
    expect(radio('System')).toBeChecked()
    expect(html).not.toHaveAttribute('data-theme')
  })

  it('keeps working when localStorage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    render(<ThemeToggle />)
    expect(radio('System')).toBeChecked()
    fireEvent.click(radio('Light'))
    expect(html.dataset.theme).toBe('light')
    expect(radio('Light')).toBeChecked()
  })
})
