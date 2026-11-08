import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Model } from '../models/types'
import { ModelList } from './ModelList'

const models: Model[] = ['a', 'b', 'c'].map((slug) => ({
  slug,
  name: `Model ${slug.toUpperCase()}`,
  description: '',
  files: [{ name: `${slug}.stl`, fileName: `${slug}.stl`, url: `/${slug}.stl` }],
}))

function renderList(selectedSlug = 'b') {
  const onSelect = vi.fn()
  render(<ModelList models={models} selectedSlug={selectedSlug} onSelect={onSelect} />)
  return onSelect
}

describe('ModelList', () => {
  it('renders the names in a labelled listbox and marks the selected one', () => {
    renderList()
    expect(screen.getByRole('listbox', { name: 'Models' })).toBeInTheDocument()
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual([
      'Model A',
      'Model B',
      'Model C',
    ])
    const selected = screen.getByRole('option', { selected: true })
    expect(selected).toHaveTextContent('Model B')
    expect(selected).toHaveAttribute('tabindex', '0')
  })

  it('selects a model on click', () => {
    const onSelect = renderList()
    fireEvent.click(screen.getByRole('option', { name: 'Model C' }))
    expect(onSelect).toHaveBeenCalledWith('c')
  })

  it.each([
    ['ArrowDown', 'c'],
    ['ArrowUp', 'a'],
    ['Home', 'a'],
    ['End', 'c'],
  ])('moves selection and focus with %s', (key, slug) => {
    const onSelect = renderList()
    fireEvent.keyDown(screen.getByRole('option', { name: 'Model B' }), { key })
    expect(onSelect).toHaveBeenCalledWith(slug)
    expect(screen.getByRole('option', { name: `Model ${slug.toUpperCase()}` })).toHaveFocus()
  })

  it('stays on the last model at the end of the list', () => {
    const onSelect = renderList('c')
    fireEvent.keyDown(screen.getByRole('listbox'), { key: 'ArrowDown' })
    expect(onSelect).toHaveBeenCalledWith('c')
  })
})
