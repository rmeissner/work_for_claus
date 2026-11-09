import { Box3, Vector3 } from 'three'
import { describe, expect, it } from 'vitest'
import {
  PLATE_SIZE_MM,
  PLATE_THICKNESS_MM,
  plateBox,
  plateGridLines,
  viewBounds,
} from './plate'

describe('plate', () => {
  it('is centered with its top at y = 0', () => {
    const size = plateBox().getSize(new Vector3())
    expect(size.x).toBe(PLATE_SIZE_MM)
    expect(size.z).toBe(PLATE_SIZE_MM)
    expect(plateBox().max.y).toBe(0)
    expect(plateBox().getCenter(new Vector3()).x).toBe(0)
  })

  const model = new Box3(new Vector3(-10, 0, -10), new Vector3(10, 30, 10))

  it('frames only the model without the plate', () => {
    expect(viewBounds(model, false).equals(model)).toBe(true)
  })

  it('frames the union of model and plate with the plate', () => {
    const box = viewBounds(model, true)
    const half = PLATE_SIZE_MM / 2
    expect(box.min.toArray()).toEqual([-half, -PLATE_THICKNESS_MM, -half])
    expect(box.max.toArray()).toEqual([half, 30, half])
  })

  describe('plateGridLines', () => {
    it('anchors at the -edge and ends with a cut-off square at the +edge', () => {
      const lines = plateGridLines(256, 10)
      expect(lines).toHaveLength(27)
      expect(lines[0]).toBe(-128)
      expect(lines.at(-1)).toBe(128)
      expect(lines.at(-1)! - lines.at(-2)!).toBe(6)
    })

    it('has no duplicate edge line when the step divides the size', () => {
      const lines = plateGridLines(200, 10)
      expect(lines).toHaveLength(21)
      expect(new Set(lines).size).toBe(lines.length)
      expect(lines.at(-1)).toBe(100)
    })
  })

  it('frames a model bigger than the plate completely', () => {
    const big = new Box3(new Vector3(-200, 0, -5), new Vector3(200, 300, 5))
    const box = viewBounds(big, true)
    expect(box.max.y).toBe(300)
    expect(box.min.x).toBe(-200)
    expect(box.min.z).toBe(-PLATE_SIZE_MM / 2)
  })
})
