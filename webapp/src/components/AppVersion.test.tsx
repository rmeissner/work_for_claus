import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import pkg from '../../package.json'
import { AppVersion } from './AppVersion'

describe('AppVersion', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('shows the package version and dev without a link for local builds', () => {
    vi.stubGlobal('__APP_COMMIT__', 'dev')
    render(<AppVersion />)
    expect(screen.getByText(`v${pkg.version} · dev`)).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('links the commit of a Cloudflare Pages build to GitHub', () => {
    vi.stubGlobal('__APP_COMMIT__', '0123456')
    render(<AppVersion />)
    expect(screen.getByRole('link', { name: '0123456' })).toHaveAttribute(
      'href',
      'https://github.com/rmeissner/work_for_claus/commit/0123456',
    )
  })
})
