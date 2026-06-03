import { useRef, useEffect } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import * as THREE from 'three'
import ShoeModel from './ShoeModel'
import Hotspot from './Hotspot'

const INTERPOLATION_SPEED = 0.08

interface SceneProps {
  color: string
  materialType: 'matte' | 'glossy' | 'metallic'
  autoRotate: boolean
  cameraTarget: { position: [number, number, number]; target: [number, number, number] }
  onLoaded: () => void
}

const HOTSPOTS = [
  {
    position: [1.4, 0.8, 0.4] as [number, number, number],
    label: '透气网面',
    description: '采用高弹性透气网面材质，提供出色的空气流通性，让双脚在运动中保持干爽舒适，减少闷热感。',
  },
  {
    position: [0, 0.1, 1.0] as [number, number, number],
    label: '缓震中底',
    description: '搭载全掌缓震科技中底，采用轻量化泡棉材料，有效吸收地面冲击力，提供卓越的能量回弹与舒适脚感。',
  },
  {
    position: [-1.4, 1.0, 0.3] as [number, number, number],
    label: '稳固后跟',
    description: '一体化后跟稳定片设计，紧密包裹脚踝，提供强劲支撑力，防止运动中的侧翻，保护双脚安全。',
  },
  {
    position: [0.4, 1.3, 0] as [number, number, number],
    label: '动态鞋舌',
    description: '符合人体工学的动态鞋舌设计，贴合脚背曲线，内置缓震衬垫，避免鞋带压迫，提升穿着舒适度。',
  },
  {
    position: [0, -0.1, -1.0] as [number, number, number],
    label: '耐磨外底',
    description: '采用高耐磨橡胶外底，结合科学纹路设计，提供强劲抓地力与防滑性能，适应多种地形与天气条件。',
  },
]

export default function Scene({ color, materialType, autoRotate, cameraTarget, onLoaded }: SceneProps) {
  const controlsRef = useRef<any>(null)
  const { camera } = useThree()
  const animating = useRef(false)
  const animProgress = useRef(0)
  const startPos = useRef(new THREE.Vector3())
  const endPos = useRef(new THREE.Vector3())
  const startTarget = useRef(new THREE.Vector3())
  const endTarget = useRef(new THREE.Vector3())

  useEffect(() => {
    startPos.current.copy(camera.position)
    endPos.current.set(...cameraTarget.position)
    if (controlsRef.current) {
      startTarget.current.copy(controlsRef.current.target)
    }
    endTarget.current.set(...cameraTarget.target)
    animProgress.current = 0
    animating.current = true
  }, [cameraTarget, camera])

  useFrame((_, delta) => {
    if (animating.current && controlsRef.current) {
      animProgress.current += delta * 1.8
      const t = Math.min(animProgress.current, 1)
      const eased = 1 - Math.pow(1 - t, 3)

      camera.position.lerpVectors(startPos.current, endPos.current, eased)
      controlsRef.current.target.lerpVectors(startTarget.current, endTarget.current, eased)
      controlsRef.current.update()

      if (t >= 1) {
        animating.current = false
      }
    }
  })

  useEffect(() => {
    const timer = setTimeout(() => {
      onLoaded()
    }, 1500)
    return () => clearTimeout(timer)
  }, [onLoaded])

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[5, 8, 5]}
        intensity={1.2}
        castShadow
        shadow-mapSize-width={4096}
        shadow-mapSize-height={4096}
        shadow-camera-far={30}
        shadow-camera-left={-5}
        shadow-camera-right={5}
        shadow-camera-top={5}
        shadow-camera-bottom={-5}
      />
      <directionalLight position={[-3, 4, -2]} intensity={0.4} />
      <pointLight position={[0, 5, 0]} intensity={0.3} />

      <Environment preset="studio" />

      <ShoeModel color={color} materialType={materialType} interpolationSpeed={INTERPOLATION_SPEED} />

      {HOTSPOTS.map((h) => (
        <Hotspot key={h.label} position={h.position} label={h.label} description={h.description} />
      ))}

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial color="#f0f0f0" transparent opacity={0.6} />
      </mesh>

      <OrbitControls
        ref={controlsRef}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        autoRotate={autoRotate}
        autoRotateSpeed={2}
        minDistance={2}
        maxDistance={10}
        minPolarAngle={0.2}
        maxPolarAngle={Math.PI / 2 - 0.05}
        target={[0, 0.5, 0]}
      />
    </>
  )
}
