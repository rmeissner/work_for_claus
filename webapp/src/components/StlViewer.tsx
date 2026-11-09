import { OrbitControls } from '@react-three/drei'
import { Canvas, useLoader, useThree } from '@react-three/fiber'
import {
  Component,
  Suspense,
  useLayoutEffect,
  useMemo,
  type ReactNode,
} from 'react'
import { BufferGeometry, Float32BufferAttribute } from 'three'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import {
  DEFAULT_VIEW_DIRECTION,
  cameraFraming,
  placeOnBed,
  PREVIEW_FOV,
} from './cameraFraming'
import {
  PLATE_SIZE_MM,
  PLATE_THICKNESS_MM,
  plateGridLines,
  viewBounds,
} from './plate'
import { DEFAULT_PREVIEW_SETTINGS, type PreviewSettings } from './previewSettings'

export interface StlViewerProps {
  url: string
  settings: PreviewSettings
}

const STATUS_CLASS = 'flex h-full w-full items-center justify-center'

export function StlViewer({ url, settings }: StlViewerProps) {
  return (
    <div className="relative h-full w-full">
      <ErrorBoundary
        fallback={
          <p className={`${STATUS_CLASS} text-danger`} role="alert">
            Could not load model
          </p>
        }
      >
        <Suspense
          fallback={
            <p className={`${STATUS_CLASS} text-muted`} role="status">
              Loading model…
            </p>
          }
        >
          <ModelLoader url={url} settings={settings} />
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

/**
 * Loads the STL outside the canvas, so the loading and error states can be
 * plain DOM. useLoader caches by URL, so the scene inside the canvas reads the
 * same parsed geometry without loading it twice.
 */
function ModelLoader({ url, settings }: StlViewerProps) {
  useLoader(STLLoader, url)
  return (
    <Canvas
      camera={{
        position: [...DEFAULT_VIEW_DIRECTION],
        fov: PREVIEW_FOV,
      }}
    >
      {/* Plain non-decaying lights: drei's Stage lights decay with distance,
          which leaves mm-sized models nearly black. */}
      <ambientLight intensity={1} />
      <directionalLight position={[1, 2, 3]} intensity={2} />
      <ModelScene url={url} settings={settings} />
    </Canvas>
  )
}

/**
 * The model on the bed origin, with the camera and the orbit target framed on
 * it, so dragging turns the model around its own center.
 */
function ModelScene({ url, settings }: StlViewerProps) {
  const loaded = useLoader(STLLoader, url)
  const { geometry, box } = useMemo(() => {
    const placed = placeOnBed(loaded)
    placed.geometry.computeVertexNormals()
    return placed
  }, [loaded])
  const showPlate = settings.showPlate
  const framing = useMemo(
    () => cameraFraming(viewBounds(box, showPlate)),
    [box, showPlate],
  )
  const getState = useThree((state) => state.get)

  useLayoutEffect(() => {
    const { camera } = getState()
    camera.position.copy(framing.cameraPosition)
    camera.far = framing.far
    camera.updateProjectionMatrix()
  }, [getState, framing])

  // Per-part colors (Magics convention) arrive as a color attribute; a white
  // base lets the vertex colors through unchanged in light and dark themes.
  const colored = Boolean((loaded as { hasColors?: boolean }).hasColors) && settings.usePartColors
  const color = settings.usePartColors
    ? colored
      ? '#ffffff'
      : DEFAULT_PREVIEW_SETTINGS.modelColor
    : settings.modelColor
  return (
    <>
      <mesh geometry={geometry}>
        {/* three.js compiles the shader per material, so changing vertexColors on
            an existing material has no effect; the key remounts it instead. */}
        <meshStandardMaterial
          key={colored ? 'vertex-colors' : 'single-color'}
          color={color}
          vertexColors={colored}
          roughness={0.6}
          metalness={0.1}
        />
      </mesh>
      {showPlate && (
        <>
          <mesh name="print-plate" position={[0, -PLATE_THICKNESS_MM / 2, 0]}>
            <boxGeometry
              args={[PLATE_SIZE_MM, PLATE_THICKNESS_MM, PLATE_SIZE_MM]}
            />
            {/* Mid grey: visible on both the light and the dark background. */}
            <meshStandardMaterial color="#8a8f98" roughness={0.9} />
          </mesh>
          <PlateGrid />
        </>
      )}
      <OrbitControls makeDefault target={framing.target.toArray()} />
    </>
  )
}

/** The plate's grid lines along X and Z, just above the plate's top. */
function PlateGrid() {
  const geometry = useMemo(() => {
    const half = PLATE_SIZE_MM / 2
    const points: number[] = []
    for (const p of plateGridLines()) {
      points.push(p, 0, -half, p, 0, half) // along Z
      points.push(-half, 0, p, half, 0, p) // along X
    }
    return new BufferGeometry().setAttribute(
      'position',
      new Float32BufferAttribute(points, 3),
    )
  }, [])
  return (
    <lineSegments geometry={geometry} position={[0, 0.05, 0]}>
      <lineBasicMaterial color="#5c6068" />
    </lineSegments>
  )
}

interface ErrorBoundaryProps {
  fallback: ReactNode
  children: ReactNode
}

// Not reset on url change: callers remount the viewer with a `key` per model.
class ErrorBoundary extends Component<ErrorBoundaryProps, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}
