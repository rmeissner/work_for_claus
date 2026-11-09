import { fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ModelFile } from '../models/types'
import type { PreviewSettings } from './previewSettings'
import { StlCarousel } from './StlCarousel'
import { visibleDots } from './visibleDots'

// jsdom has no WebGL, so the 3D viewer is replaced by a stub showing its URL.
vi.mock('./StlViewer', () => ({
  StlViewer: ({ url, settings }: { url: string; settings: PreviewSettings }) => (
    <div
      data-testid="stl-viewer"
      data-show-plate={String(settings.showPlate)}
      data-use-part-colors={String(settings.usePartColors)}
      data-model-color={settings.modelColor}
    >
      {url}
    </div>
  ),
}))

const file = (n: string): ModelFile => ({ name: `File ${n}`, fileName: `${n}.stl`, url: `/${n}.stl` })
const files = ['a', 'b', 'c'].map(file)

const shown = async () => (await screen.findByTestId('stl-viewer')).textContent

describe('StlCarousel', () => {
  beforeEach(() => localStorage.clear())

  it('shows the first file', async () => {
    render(<StlCarousel files={files} />)
    expect(await shown()).toBe('/a.stl')
    expect(screen.getByRole('group')).toHaveAccessibleName('1 of 3: File a')
  })

  it('moves to the next and previous file and loops in both directions', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    fireEvent.click(screen.getByRole('button', { name: 'Previous file' }))
    expect(await shown()).toBe('/c.stl')
    fireEvent.click(screen.getByRole('button', { name: 'Next file' }))
    expect(await shown()).toBe('/a.stl')
    fireEvent.click(screen.getByRole('button', { name: 'Next file' }))
    expect(await shown()).toBe('/b.stl')
  })

  it('moves with the arrow keys', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    const carousel = screen.getByRole('region', { name: 'Model files' })
    fireEvent.keyDown(carousel, { key: 'ArrowRight' })
    expect(await shown()).toBe('/b.stl')
    fireEvent.keyDown(carousel, { key: 'ArrowLeft' })
    fireEvent.keyDown(carousel, { key: 'ArrowLeft' })
    expect(await shown()).toBe('/c.stl')
  })

  it('jumps with the dots, which carry the file name as title', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    const dot = screen.getByRole('button', { name: 'Show File c' })
    expect(dot).toHaveAttribute('title', 'File c')
    fireEvent.click(dot)
    expect(await shown()).toBe('/c.stl')
    expect(dot).toHaveAttribute('aria-current', 'true')
  })

  it('renders no title or counter text', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    expect(screen.queryByText('File a')).not.toBeInTheDocument()
    expect(screen.queryByText(/1\s*\/\s*3|1 of 3/)).not.toBeInTheDocument()
  })

  it('shows only the settings button for a single file', async () => {
    render(<StlCarousel files={[file('a')]} />)
    await shown()
    expect(screen.getByRole('button', { name: 'Preview settings' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Next file' })).not.toBeInTheDocument()
  })

  it('shows the settings button next to the arrows', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    expect(screen.getByRole('button', { name: 'Preview settings' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Next file' })).toBeInTheDocument()
  })

  it('closes the dialog on a backdrop click but not on a click inside the content', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    const dialog = screen.getByRole('dialog', { hidden: true })
    fireEvent.click(screen.getByRole('button', { name: 'Preview settings' }))
    fireEvent.click(within(dialog).getByTestId('preview-settings-content'))
    expect(dialog).toHaveAttribute('open')
    fireEvent.click(dialog)
    expect(dialog).not.toHaveAttribute('open')
  })

  it('opens the settings dialog and passes the color settings on to the viewer', async () => {
    render(<StlCarousel files={files} />)
    await shown()
    const dialog = screen.getByRole('dialog', { hidden: true })
    expect(dialog).not.toHaveAttribute('open')

    fireEvent.click(screen.getByRole('button', { name: 'Preview settings' }))
    expect(dialog).toHaveAttribute('open')
    const ui = within(dialog)
    const colorInput = ui.getByLabelText('Model color')
    expect(colorInput).toBeDisabled()

    fireEvent.click(ui.getByLabelText('Show print plate (256 × 256 mm)'))
    expect(await screen.findByTestId('stl-viewer')).toHaveAttribute('data-show-plate', 'true')

    fireEvent.click(ui.getByLabelText('Use part colors'))
    expect(colorInput).toBeEnabled()
    fireEvent.change(colorInput, { target: { value: '#ff0000' } })
    const viewer = await screen.findByTestId('stl-viewer')
    expect(viewer).toHaveAttribute('data-use-part-colors', 'false')
    expect(viewer).toHaveAttribute('data-model-color', '#ff0000')

    fireEvent.click(ui.getByRole('button', { name: 'Close' }))
    expect(dialog).not.toHaveAttribute('open')
  })

  it('starts over when remounted with another key', async () => {
    const { rerender } = render(<StlCarousel key="one" files={files} />)
    await shown()
    fireEvent.click(screen.getByRole('button', { name: 'Next file' }))
    expect(await shown()).toBe('/b.stl')
    rerender(<StlCarousel key="two" files={files} />)
    expect(await shown()).toBe('/a.stl')
  })
})

describe('visibleDots', () => {
  const summarize = (index: number, length: number) =>
    visibleDots(index, length).map((d) => `${d.index}${d.small ? 's' : ''}`)

  it.each([
    [0, 1, ['0']],
    [0, 3, ['0', '1', '2']],
    [2, 3, ['0', '1', '2']],
    [0, 4, ['0', '1', '2s']],
    [3, 4, ['1s', '2', '3']],
    [0, 5, ['0', '1', '2s']],
    [2, 5, ['0', '1', '2', '3', '4']],
    [4, 5, ['2s', '3', '4']],
  ])('current %i of %i files', (index, length, expected) => {
    expect(summarize(index, length)).toEqual(expected)
  })

  it.each([
    [0, 7, ['0', '1', '2s']],
    [1, 7, ['0', '1', '2', '3s']],
    [2, 7, ['0', '1', '2', '3', '4s']],
    [3, 7, ['1s', '2', '3', '4', '5s']],
    [4, 7, ['2s', '3', '4', '5', '6']],
    [5, 7, ['3s', '4', '5', '6']],
    [6, 7, ['4s', '5', '6']],
  ])('current %i of %i files', (index, length, expected) => {
    expect(summarize(index, length)).toEqual(expected)
  })
})
