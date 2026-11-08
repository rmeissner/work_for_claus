import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import App from './App'
import type { Model } from './models/types'

const models: Model[] = [
  { slug: 'cube', name: 'Cube', description: 'A cube.', stlUrl: '/cube.stl' },
  { slug: 'pyramid', name: 'Pyramid', description: 'A pyramid.\nPointy.', stlUrl: '/p.stl' },
]

function setHash(hash: string) {
  act(() => {
    window.location.hash = hash
    window.dispatchEvent(new HashChangeEvent('hashchange'))
  })
}

const selectedOption = () => screen.getByRole('option', { selected: true })

describe('App', () => {
  afterEach(() => setHash(''))

  it('renders the heading, the model names and selects the first model', () => {
    render(<App models={models} />)
    expect(screen.getByRole('heading', { level: 1, name: 'Work for Claus' })).toBeInTheDocument()
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual(['Cube', 'Pyramid'])
    expect(selectedOption()).toHaveTextContent('Cube')
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Cube')
    expect(screen.getByTestId('model-preview')).toBeInTheDocument()
  })

  it('selects a clicked model, shows its description and updates the hash', async () => {
    render(<App models={models} />)
    fireEvent.click(screen.getByRole('option', { name: 'Pyramid' }))
    expect(await screen.findByRole('heading', { level: 2, name: 'Pyramid' })).toBeInTheDocument()
    expect(window.location.hash).toBe('#/pyramid')
    expect(selectedOption()).toHaveTextContent('Pyramid')
    expect(screen.getByText(/A pyramid\.\s+Pointy\./)).toBeInTheDocument()
  })

  it('selects the model named by the initial hash', () => {
    setHash('#/pyramid')
    render(<App models={models} />)
    expect(selectedOption()).toHaveTextContent('Pyramid')
  })

  it('follows hash changes, for example the back button', () => {
    render(<App models={models} />)
    setHash('#/pyramid')
    expect(selectedOption()).toHaveTextContent('Pyramid')
  })

  it('falls back to the first model for an unknown hash', () => {
    setHash('#/nope')
    render(<App models={models} />)
    expect(selectedOption()).toHaveTextContent('Cube')
  })

  it('shows an empty state without models', () => {
    render(<App models={[]} />)
    expect(screen.getByText('No models found')).toBeInTheDocument()
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('lists the repository models by default', () => {
    render(<App />)
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual([
      'Calibration cube',
      'Pyramid',
    ])
  })
})
