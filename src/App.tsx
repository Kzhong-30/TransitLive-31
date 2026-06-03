import { useState, useCallback, useMemo } from 'react'
import { Canvas } from '@react-three/fiber'
import * as THREE from 'three'
import Scene from './components/Scene'
import ControlPanel from './components/ControlPanel'
import BottomBar from './components/BottomBar'
import LoadingScreen from './components/LoadingScreen'
import './App.css'

const DEFAULT_CAMERA = {
  position: [3, 2, 4] as [number, number, number],
  target: [0, 0.5, 0] as [number, number, number],
}

function App() {
  const [color, setColor] = useState('#DC2626')
  const [materialType, setMaterialType] = useState<'matte' | 'glossy' | 'metallic'>('matte')
  const [autoRotate, setAutoRotate] = useState(true)
  const [loading, setLoading] = useState(true)
  const [cameraTarget, setCameraTarget] = useState(DEFAULT_CAMERA)
  const [currentView, setCurrentView] = useState('default')

  const handleViewChange = useCallback(
    (view: { position: [number, number, number]; target: [number, number, number]; key?: string }) => {
      setCameraTarget({ position: view.position, target: view.target })
      setCurrentView(view.key || 'custom')
    },
    []
  )

  const handleResetView = useCallback(() => {
    handleViewChange({ ...DEFAULT_CAMERA, key: 'default' })
  }, [handleViewChange])

  const shadowMapType = useMemo(() => THREE.PCFShadowMap, [])

  return (
    <div className="app-container">
      <LoadingScreen visible={loading} />

      <header className="app-header">
        <div className="header-left">
          <span className="brand-icon">◈</span>
          <span className="brand-name">3D SHOWCASE</span>
        </div>
        <div className="header-center">
          <h1>AirStep Pro 运动鞋</h1>
        </div>
        <div className="header-right">
          <span className="product-price">¥1,299</span>
        </div>
      </header>

      <main className="app-main">
        <div className="canvas-container">
          <Canvas
            shadows={{ type: shadowMapType }}
            camera={{ position: DEFAULT_CAMERA.position, fov: 45, near: 0.1, far: 100 }}
            gl={{ antialias: true, alpha: false }}
            dpr={[1, 2]}
          >
            <color attach="background" args={['#f0f0f0']} />
            <fog attach="fog" args={['#f0f0f0', 8, 20]} />
            <Scene
              color={color}
              materialType={materialType}
              autoRotate={autoRotate}
              cameraTarget={cameraTarget}
              onLoaded={() => setLoading(false)}
            />
          </Canvas>
        </div>

        <ControlPanel
          color={color}
          onColorChange={setColor}
          materialType={materialType}
          onMaterialChange={setMaterialType}
          autoRotate={autoRotate}
          onAutoRotateToggle={() => setAutoRotate(!autoRotate)}
          onResetView={handleResetView}
        />
      </main>

      <BottomBar onViewChange={handleViewChange} currentView={currentView} />
    </div>
  )
}

export default App
