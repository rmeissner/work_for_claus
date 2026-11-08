import { OrbitControls, Stage } from '@react-three/drei'
import { Canvas, useLoader } from '@react-three/fiber'
import { Component, Suspense, useMemo, type ReactNode } from 'react'
import { STLLoader } from 'three/addons/loaders/STLLoader.js'
import styles from './StlViewer.module.css'

export interface StlViewerProps {
  url: string
}

export function StlViewer({ url }: StlViewerProps) {
  return (
    <div className={styles.viewer}>
      <ErrorBoundary
        fallback={
          <p className={`${styles.status} ${styles.error}`} role="alert">
            Could not load model
          </p>
        }
      >
        <Suspense
          fallback={
            <p className={styles.status} role="status">
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
 * plain DOM. useLoader caches by URL, so the mesh inside the canvas reads the
 * same parsed geometry without loading it twice.
 */
function ModelLoader({ url }: StlViewerProps) {
  useLoader(STLLoader, url)
  return (
    <Canvas camera={{ position: [60, 40, 80], fov: 45 }}>
      {/* Stage's own lights decay with distance, which leaves mm-sized
          models nearly black, and its default environment map is fetched
          from a CDN. Plain non-decaying lights avoid both. */}
      <ambientLight intensity={1} />
      <directionalLight position={[1, 2, 3]} intensity={2} />
      {/* adjustCamera is the fit margin; `true` means 1, which crops. */}
      <Stage adjustCamera={2} environment={null}>
        <StlMesh url={url} />
      </Stage>
      <OrbitControls makeDefault />
    </Canvas>
  )
}

function StlMesh({ url }: StlViewerProps) {
  const loaded = useLoader(STLLoader, url)
  const geometry = useMemo(() => {
    loaded.computeVertexNormals()
    return loaded
  }, [loaded])
  return (
    // STL files from slicers and CAD tools are Z-up; three.js is Y-up.
    <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]}>
      <meshStandardMaterial color="#b0b4ba" roughness={0.6} metalness={0.1} />
    </mesh>
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
