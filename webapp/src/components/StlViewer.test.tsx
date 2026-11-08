import { render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StlViewer } from './StlViewer'

// jsdom has no WebGL, so the canvas and drei helpers render plain DOM.
const useLoader = vi.hoisted(() => vi.fn())

vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: ReactNode }) => (
    <div data-testid="canvas">{children}</div>
  ),
  useLoader,
}))

vi.mock('@react-three/drei', () => ({
  Stage: ({ children }: { children: ReactNode }) => <>{children}</>,
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

    render(<StlViewer url="/model.stl" />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading model…')
    expect(screen.queryByTestId('canvas')).not.toBeInTheDocument()
  })

  it('shows an error state when the model cannot be loaded', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    useLoader.mockImplementation(() => {
      throw new Error('Could not load /model.stl')
    })

    render(<StlViewer url="/model.stl" />)

    expect(screen.getByRole('alert')).toHaveTextContent('Could not load model')
    expect(screen.queryByTestId('canvas')).not.toBeInTheDocument()
  })
})
