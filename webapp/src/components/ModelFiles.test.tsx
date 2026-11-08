import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { ModelFile } from '../models/types'
import { ModelFiles } from './ModelFiles'

function makeFiles(count: number): ModelFile[] {
  return Array.from({ length: count }, (_, i) => ({
    name: `Part ${i + 1}`,
    fileName: `part-${i + 1}.stl`,
    url: `/assets/part-${i + 1}.stl`,
  }))
}

describe('ModelFiles', () => {
  it('renders download links with href and download name', () => {
    render(<ModelFiles files={makeFiles(2)} />)
    expect(screen.getByRole('heading', { name: 'Files' })).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /Part 2/ })
    expect(link).toHaveAttribute('href', '/assets/part-2.stl')
    expect(link).toHaveAttribute('download', 'part-2.stl')
    expect(link).toHaveTextContent('part-2.stl')
  })

  it('shows no button for up to 3 files', () => {
    render(<ModelFiles files={makeFiles(3)} />)
    expect(screen.getAllByRole('link')).toHaveLength(3)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('reveals the remaining files on demand', () => {
    render(<ModelFiles files={makeFiles(5)} />)
    expect(screen.getAllByRole('link')).toHaveLength(3)
    const button = screen.getByRole('button', { name: 'Show 2 more' })
    expect(button).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(button)
    expect(screen.getAllByRole('link')).toHaveLength(5)
    expect(screen.getByRole('button', { name: 'Show less' })).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(screen.getByRole('button', { name: 'Show less' }))
    expect(screen.getAllByRole('link')).toHaveLength(3)
  })
})
