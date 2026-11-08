/** Number of dots shown on each side of the current one. */
const DOT_RADIUS = 2

export interface Dot {
  index: number
  /** More files lie beyond this (outermost) dot, so it is drawn smaller. */
  small: boolean
}

/**
 * The dots to render: the current file and up to DOT_RADIUS files on each
 * side, clamped to the list by position (no wrap-around). On a side where
 * more files lie beyond the window, the outermost dot is small.
 */
export function visibleDots(index: number, length: number): Dot[] {
  const first = Math.max(0, index - DOT_RADIUS)
  const last = Math.min(length - 1, index + DOT_RADIUS)
  const dots: Dot[] = []
  for (let i = first; i <= last; i++) {
    dots.push({ index: i, small: (i === first && first > 0) || (i === last && last < length - 1) })
  }
  return dots
}
