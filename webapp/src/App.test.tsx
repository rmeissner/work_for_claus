import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation, useNavigate } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

// jsdom has no WebGL, so the 3D viewer is replaced by a stub showing its URL.
vi.mock('./components/StlViewer', () => ({
  StlViewer: ({ url }: { url: string }) => <div data-testid="stl-viewer">{url}</div>,
}))
import type { Model } from './models/types'

const models: Model[] = [
  { slug: 'cube', name: 'Cube', version: '1.0', description: 'A cube.', files: [{ name: 'cube.stl', fileName: 'cube.stl', url: '/cube.stl' }] },
  { slug: 'pyramid', name: 'Pyramid', version: 'v2', description: 'A pyramid.\nPointy.', files: [{ name: 'p.stl', fileName: 'p.stl', url: '/p.stl' }] },
]

const selectedOption = () => screen.getByRole('option', { selected: true })

/** Exposes the current location and a back button next to the app. */
function LocationProbe() {
  const location = useLocation()
  const navigate = useNavigate()
  return (
    <>
      <div data-testid="location">{location.pathname}</div>
      <button type="button" onClick={() => navigate(-1)}>
        back
      </button>
    </>
  )
}

function renderApp(initialEntries: string[], appModels?: Model[], initialIndex?: number) {
  return render(
    <MemoryRouter initialEntries={initialEntries} initialIndex={initialIndex}>
      <App models={appModels} />
      <LocationProbe />
    </MemoryRouter>,
  )
}

const pathname = () => screen.getByTestId('location').textContent

describe('App', () => {
  it('renders the heading, the model names and selects the first model', () => {
    renderApp(['/'], models)
    expect(screen.getByRole('heading', { level: 1, name: 'Work for Claus' })).toBeInTheDocument()
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual(['Cube', 'Pyramid'])
    expect(selectedOption()).toHaveTextContent('Cube')
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Cube v1.0')
    expect(screen.getByTestId('model-preview')).toBeInTheDocument()
    expect(pathname()).toBe('/cube')
  })

  it('shows the 3D viewer for the selected model', async () => {
    renderApp(['/'], models)
    expect(await screen.findByTestId('stl-viewer')).toHaveTextContent('/cube.stl')
    fireEvent.click(screen.getByRole('option', { name: 'Pyramid' }))
    expect(await screen.findByText('/p.stl')).toBeInTheDocument()
  })

  it('selects a clicked model, shows its description and updates the URL', async () => {
    renderApp(['/'], models)
    fireEvent.click(screen.getByRole('option', { name: 'Pyramid' }))
    expect(await screen.findByRole('heading', { level: 2, name: 'Pyramid v2' })).toBeInTheDocument()
    expect(pathname()).toBe('/pyramid')
    expect(selectedOption()).toHaveTextContent('Pyramid')
    expect(screen.getByText(/A pyramid\.\s+Pointy\./)).toBeInTheDocument()
  })

  it('selects the model named by the initial entry', () => {
    renderApp(['/pyramid'], models)
    expect(selectedOption()).toHaveTextContent('Pyramid')
  })

  it('follows history navigation, for example the back button', () => {
    renderApp(['/cube', '/pyramid'], models, 1)
    expect(selectedOption()).toHaveTextContent('Pyramid')
    fireEvent.click(screen.getByRole('button', { name: 'back' }))
    expect(selectedOption()).toHaveTextContent('Cube')
    expect(pathname()).toBe('/cube')
  })

  it('goes back to the previous model after selecting one', () => {
    renderApp(['/'], models)
    fireEvent.click(screen.getByRole('option', { name: 'Pyramid' }))
    fireEvent.click(screen.getByRole('button', { name: 'back' }))
    expect(selectedOption()).toHaveTextContent('Cube')
  })

  it('redirects an unknown slug to the first model', () => {
    renderApp(['/nope'], models)
    expect(selectedOption()).toHaveTextContent('Cube')
    expect(pathname()).toBe('/cube')
  })

  it('shows an empty state without models', () => {
    renderApp(['/pyramid'], [])
    expect(screen.getByText('No models found')).toBeInTheDocument()
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('lists the repository models by default', () => {
    renderApp(['/'])
    expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual([
      '24-point star',
      'Calibration cube',
      'Glider',
      'Pyramid',
      'Star Destroyer',
      'Star ornament',
    ])
  })
})
