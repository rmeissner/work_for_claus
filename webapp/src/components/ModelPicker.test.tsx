import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Model } from '../models/types'
import { ModelPicker } from './ModelPicker'

const models: Model[] = ['a', 'b', 'c'].map((slug) => ({
  slug,
  name: `Model ${slug.toUpperCase()}`,
  description: '',
  files: [{ name: `${slug}.stl`, fileName: `${slug}.stl`, url: `/${slug}.stl` }],
}))

function renderPicker() {
  const onSelect = vi.fn()
  render(<ModelPicker models={models} selectedSlug="b" onSelect={onSelect} />)
  const toggle = screen.getByRole('button', {
    name: 'Choose model (current: Model B)',
  })
  return { onSelect, toggle }
}

describe('ModelPicker', () => {
  it('is closed by default and shows the current name on the toggle', () => {
    const { toggle } = renderPicker()
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveTextContent('Model B')
    expect(toggle).toHaveAttribute('aria-controls', screen.getByRole('listbox').parentElement!.id)
    expect(screen.queryByTestId('model-picker-backdrop')).not.toBeInTheDocument()
  })

  it('opens with the toggle and focuses the selected option', () => {
    const { toggle } = renderPicker()
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('option', { name: 'Model B' })).toHaveFocus()
  })

  it('closes on the toggle again', () => {
    const { toggle } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('selects a model and closes', () => {
    const { toggle, onSelect } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.click(screen.getByRole('option', { name: 'Model C' }))
    expect(onSelect).toHaveBeenCalledWith('c')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps the sheet open while moving with the arrow keys', () => {
    const { toggle, onSelect } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.keyDown(screen.getByRole('option', { name: 'Model B' }), {
      key: 'ArrowDown',
    })
    expect(onSelect).toHaveBeenCalledWith('c')
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('still closes on a click after a non-navigation key', () => {
    const { toggle, onSelect } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.keyDown(screen.getByRole('option', { name: 'Model B' }), { key: 'Tab' })
    fireEvent.click(screen.getByRole('option', { name: 'Model C' }))
    expect(onSelect).toHaveBeenCalledWith('c')
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  it('closes on Escape without selecting and returns focus to the toggle', () => {
    const { toggle, onSelect } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.keyDown(screen.getByRole('option', { name: 'Model B' }), {
      key: 'Escape',
    })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveFocus()
    expect(onSelect).not.toHaveBeenCalled()
  })

  it('closes on a backdrop click without selecting', () => {
    const { toggle, onSelect } = renderPicker()
    fireEvent.click(toggle)
    fireEvent.click(screen.getByTestId('model-picker-backdrop'))
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(onSelect).not.toHaveBeenCalled()
  })
})
