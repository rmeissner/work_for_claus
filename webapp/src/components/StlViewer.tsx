import { OrbitControls } from '@react-three/drei'
import { Canvas, useLoader, useThree } from '@react-three/fiber'
import {
  Component,
  Suspense,
  useLayoutEffect,
  useMemo,
  type ReactNode,
} from 'react'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import {
  DEFAULT_VIEW_DIRECTION,
  frameBox,
  placeOnBed,
  PREVIEW_FOV,
} from './frameBox'

export interface StlViewerProps {
  url: string
}

const STATUS_CLASS = 'flex h-full w-full items-center justify-center'

export function StlViewer({ url }: StlViewerProps) {
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
          <ModelLoader url={url} />
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
function ModelLoader({ url }: StlViewerProps) {
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
      <ModelScene url={url} />
    </Canvas>
  )
}

/**
 * The model on the bed origin, with the camera and the orbit target framed on
 * it, so dragging turns the model around its own center.
 */
function ModelScene({ url }: StlViewerProps) {
  const loaded = useLoader(STLLoader, url)
  const { geometry, box } = useMemo(() => {
    const placed = placeOnBed(loaded)
    placed.geometry.computeVertexNormals()
    return placed
  }, [loaded])
  const framing = useMemo(() => frameBox(box), [box])
  const getState = useThree((state) => state.get)

  useLayoutEffect(() => {
    const { camera } = getState()
    camera.position.copy(framing.cameraPosition)
    camera.far = framing.far
    camera.updateProjectionMatrix()
  }, [getState, framing])

  // Per-part colors (Magics convention) arrive as a color attribute; a white
  // base lets the vertex colors through unchanged in light and dark themes.
  const colored = Boolean((loaded as { hasColors?: boolean }).hasColors)
  return (
    <>
      <mesh geometry={geometry}>
        <meshStandardMaterial
          color={colored ? '#ffffff' : '#b0b4ba'}
          vertexColors={colored}
          roughness={0.6}
          metalness={0.1}
        />
      </mesh>
      <OrbitControls makeDefault target={framing.target.toArray()} />
    </>
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
