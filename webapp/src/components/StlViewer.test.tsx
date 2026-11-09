import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { BufferGeometry, PerspectiveCamera } from 'three'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { DEFAULT_PREVIEW_SETTINGS } from './previewSettings'
import { StlViewer } from './StlViewer'

const settings = DEFAULT_PREVIEW_SETTINGS

// jsdom has no WebGL, so the canvas and drei helpers render plain DOM.
const useLoader = vi.hoisted(() => vi.fn())

vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: ReactNode }) => (
    <div data-testid="canvas">{children}</div>
  ),
  useLoader,
  useThree: (select: (state: unknown) => unknown) =>
    select({ get: () => ({ camera: new PerspectiveCamera() }) }),
}))

vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
}))

describe('StlViewer', () => {
  afterEach(() => {
    useLoader.mockReset()
    vi.restoreAllMocks()
  })

  it('shows a loading state while the model loads', () => {
    useLoader.mockImplementation(() => {
      throw new Promise(() => {})
    })

    render(<StlViewer url="/model.stl" settings={settings} />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading model…')
    expect(screen.queryByTestId('canvas')).not.toBeInTheDocument()
  })

  it('shows an error state when the model cannot be loaded', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    useLoader.mockImplementation(() => {
      throw new Error('Could not load /model.stl')
    })

    render(<StlViewer url="/model.stl" settings={settings} />)

    expect(screen.getByRole('alert')).toHaveTextContent('Could not load model')
    expect(screen.queryByTestId('canvas')).not.toBeInTheDocument()
  })

  it.each([
    [true, {}, '#ffffff'],
    [false, {}, '#b0b4ba'],
    [true, { usePartColors: false, modelColor: '#ff0000' }, '#ff0000'],
    [false, { usePartColors: false, modelColor: '#ff0000' }, '#ff0000'],
  ])('with hasColors %s and settings %j the color is %s', (hasColors, override, color) => {
    const geometry = new BufferGeometry() as BufferGeometry & {
      hasColors?: boolean
    }
    geometry.hasColors = hasColors
    useLoader.mockReturnValue(geometry)

    const { container } = render(
      <StlViewer url="/model.stl" settings={{ ...settings, ...override }} />,
    )

    // The mocked canvas renders the material as a plain element; boolean props
    // are dropped there, so the base color tells the cases apart.
    const material = container.querySelector('meshstandardmaterial')
    expect(material).toHaveAttribute('color', color)
  })

  it.each([
    [false, 0],
    [true, 1],
  ])('with showPlate %s renders %i plate meshes and grids', (showPlate, count) => {
    useLoader.mockReturnValue(new BufferGeometry())

    const { container } = render(
      <StlViewer url="/model.stl" settings={{ ...settings, showPlate }} />,
    )

    expect(container.querySelectorAll('[name="print-plate"]')).toHaveLength(count)
    expect(container.querySelectorAll('linesegments')).toHaveLength(count)
  })
})
