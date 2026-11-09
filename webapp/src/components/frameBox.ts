import { Box3, Vector3, type BufferGeometry } from 'three'

/** Viewing direction the camera keeps when it is refitted (looking at the target). */
export const DEFAULT_VIEW_DIRECTION: readonly [number, number, number] = [
  60, 40, 80,
]

/** Vertical field of view of the preview camera, in degrees. */
export const PREVIEW_FOV = 45

/** Distance multiplier on top of the tight fit, so the model is not cropped. */
const FIT_MARGIN = 2

export interface Framing {
  target: Vector3
  cameraPosition: Vector3
  /** Far plane that covers the whole framed box from the camera position. */
  far: number
}

/**
 * Frames a box: orbit around its center and place the camera along
 * `direction` far enough that the whole box fits the vertical field of view.
 */
export function frameBox(
  box: Box3,
  fov: number = PREVIEW_FOV,
  direction: readonly [number, number, number] = DEFAULT_VIEW_DIRECTION,
): Framing {
  const target = box.getCenter(new Vector3())
  const size = box.getSize(new Vector3())
  const maxDim = Math.max(size.x, size.y, size.z)
  const distance =
    (maxDim / (2 * Math.tan((fov * Math.PI) / 360))) * FIT_MARGIN
  const cameraPosition = new Vector3(...direction)
    .normalize()
    .multiplyScalar(distance)
    .add(target)
  return { target, cameraPosition, far: Math.max(1000, distance + maxDim * 4) }
}

/**
 * Puts a Z-up STL geometry on the bed like a slicer does: converted to Y-up,
 * centered on X/Z and with its bottom at y = 0. Works on (and returns) a
 * clone, so the loader's cached geometry stays untouched.
 */
export function placeOnBed(source: BufferGeometry): {
  geometry: BufferGeometry
  box: Box3
} {
  const geometry = source.clone()
  geometry.rotateX(-Math.PI / 2)
  geometry.computeBoundingBox()
  const box = geometry.boundingBox ?? new Box3()
  if (box.isEmpty()) return { geometry, box: new Box3() }
  const center = box.getCenter(new Vector3())
  geometry.translate(-center.x, -box.min.y, -center.z)
  geometry.computeBoundingBox()
  return { geometry, box: geometry.boundingBox ?? new Box3() }
}
