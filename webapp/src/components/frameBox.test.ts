import { Box3, BoxGeometry, Vector3 } from 'three'
import { describe, expect, it } from 'vitest'
import { frameBox, placeOnBed } from './frameBox'

const box = (min: [number, number, number], max: [number, number, number]) =>
  new Box3(new Vector3(...min), new Vector3(...max))

describe('frameBox', () => {
  it('targets the center of the box', () => {
    const { target } = frameBox(box([10, 0, -20], [30, 40, 20]))
    expect(target.toArray()).toEqual([20, 20, 0])
  })

  it('looks at the target from the given direction', () => {
    const { target, cameraPosition } = frameBox(
      box([-10, -10, -10], [10, 10, 10]),
      45,
      [0, 0, 1],
    )
    const offset = cameraPosition.clone().sub(target)
    expect(offset.x).toBeCloseTo(0)
    expect(offset.y).toBeCloseTo(0)
    expect(offset.z).toBeGreaterThan(0)
  })

  it('moves the camera further away for a bigger box', () => {
    const small = frameBox(box([-10, 0, -10], [10, 20, 10]))
    const big = frameBox(box([-110, 0, -110], [110, 20, 110]))
    expect(big.cameraPosition.distanceTo(big.target)).toBeGreaterThan(
      small.cameraPosition.distanceTo(small.target),
    )
  })

  it('keeps the whole box inside the far plane', () => {
    const { cameraPosition, far } = frameBox(
      box([-5000, 0, -5000], [5000, 10, 5000]),
    )
    expect(far).toBeGreaterThan(cameraPosition.length())
  })
})

describe('placeOnBed', () => {
  it('centers an offset geometry on X/Z with its bottom at y = 0', () => {
    // STL is Z-up: 10 wide (x), 20 deep (y), 30 tall (z), far from the origin.
    const source = new BoxGeometry(10, 20, 30).translate(100, 200, 300)

    const { geometry, box: placed } = placeOnBed(source)

    expect(placed.min.x).toBeCloseTo(-5)
    expect(placed.max.x).toBeCloseTo(5)
    expect(placed.min.y).toBeCloseTo(0)
    expect(placed.max.y).toBeCloseTo(30)
    expect(placed.min.z).toBeCloseTo(-10)
    expect(placed.max.z).toBeCloseTo(10)
    expect(geometry.boundingBox).toEqual(placed)
  })

  it('does not modify the source geometry', () => {
    const source = new BoxGeometry(10, 20, 30).translate(100, 200, 300)
    const before = Array.from(source.getAttribute('position').array)

    placeOnBed(source)

    expect(Array.from(source.getAttribute('position').array)).toEqual(before)
  })
})
