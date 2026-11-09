import { Box3, Vector3 } from 'three'

/** Edge length of Claus' build plate, in mm. */
export const PLATE_SIZE_MM = 256

/** Thickness of the drawn plate, in mm. */
export const PLATE_THICKNESS_MM = 2

/** Distance between the grid lines, in mm. */
export const PLATE_GRID_STEP_MM = 10

/** The plate: centered on X/Z with its top at y = 0. */
export function plateBox(): Box3 {
  const half = PLATE_SIZE_MM / 2
  return new Box3(
    new Vector3(-half, -PLATE_THICKNESS_MM, -half),
    new Vector3(half, 0, half),
  )
}

/** The bounds the camera shows: the model, plus the plate when it is shown. */
export function viewBounds(modelBox: Box3, showPlate: boolean): Box3 {
  const box = modelBox.clone()
  return showPlate ? box.union(plateBox()) : box
}

/**
 * Grid line positions along one axis: from the plate's -size/2 edge every
 * `step` mm up to and including the +size/2 edge. The last square is cut off
 * when `step` does not divide `size`, like a slicer anchors its grid at the
 * bed corner.
 */
export function plateGridLines(
  size: number = PLATE_SIZE_MM,
  step: number = PLATE_GRID_STEP_MM,
): number[] {
  const half = size / 2
  const positions: number[] = []
  for (let p = -half; p < half; p += step) positions.push(p)
  positions.push(half)
  return positions
}
