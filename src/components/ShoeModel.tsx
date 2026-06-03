import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface ShoeModelProps {
  color: string
  materialType: 'matte' | 'glossy' | 'metallic'
  interpolationSpeed: number
}

export default function ShoeModel({ color, materialType, interpolationSpeed }: ShoeModelProps) {
  const groupRef = useRef<THREE.Group>(null)
  const currentColor = useRef(new THREE.Color(color))

  const materialProps = useMemo(() => {
    switch (materialType) {
      case 'matte':
        return { roughness: 0.9, metalness: 0.0 }
      case 'glossy':
        return { roughness: 0.15, metalness: 0.1 }
      case 'metallic':
        return { roughness: 0.25, metalness: 0.9 }
    }
  }, [materialType])

  useFrame(() => {
    if (groupRef.current) {
      const target = new THREE.Color(color)
      currentColor.current.lerp(target, interpolationSpeed)
      groupRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh
          const mat = mesh.material as THREE.MeshStandardMaterial
          if (mat.color) {
            mat.color.copy(currentColor.current)
          }
          mat.roughness = THREE.MathUtils.lerp(mat.roughness, materialProps.roughness, interpolationSpeed)
          mat.metalness = THREE.MathUtils.lerp(mat.metalness, materialProps.metalness, interpolationSpeed)
        }
      })
    }
  })

  const soleMat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#1a1a1a', roughness: 0.95, metalness: 0.0 }),
    []
  )
  const accentMat = useMemo(
    () => new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 0.5, metalness: 0.0 }),
    []
  )

  return (
    <group ref={groupRef} position={[0, 0.55, 0]} rotation={[0, -Math.PI / 6, 0]}>
      {/* Outsole */}
      <mesh position={[0, -0.35, 0]} material={soleMat} castShadow receiveShadow>
        <boxGeometry args={[2.4, 0.15, 1.0]} />
      </mesh>

      {/* Midsole */}
      <mesh position={[0, -0.2, 0]} castShadow receiveShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[2.35, 0.18, 0.95]} />
      </mesh>

      {/* Midsole trim - side groove lines */}
      <mesh position={[0, -0.2, 0.49]} castShadow>
        <meshStandardMaterial color="#e0e0e0" roughness={0.6} metalness={0.0} />
        <boxGeometry args={[2.2, 0.12, 0.02]} />
      </mesh>
      <mesh position={[0, -0.2, -0.49]} castShadow>
        <meshStandardMaterial color="#e0e0e0" roughness={0.6} metalness={0.0} />
        <boxGeometry args={[2.2, 0.12, 0.02]} />
      </mesh>

      {/* Upper body - main shoe body */}
      <mesh position={[0.05, 0.1, 0]} castShadow receiveShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[2.1, 0.55, 0.9]} />
      </mesh>

      {/* Toe box - rounded front */}
      <mesh position={[1.0, 0.0, 0]} castShadow receiveShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <sphereGeometry args={[0.48, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
      </mesh>

      {/* Toe cap overlay */}
      <mesh position={[1.1, -0.12, 0]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[0.3, 0.2, 0.85]} />
      </mesh>

      {/* Heel counter */}
      <mesh position={[-1.05, 0.2, 0]} castShadow receiveShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[0.3, 0.65, 0.88]} />
      </mesh>

      {/* Heel tab */}
      <mesh position={[-1.15, 0.5, 0]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[0.08, 0.2, 0.3]} />
      </mesh>

      {/* Tongue */}
      <mesh position={[0.2, 0.5, 0]} rotation={[0.15, 0, 0]} castShadow>
        <meshStandardMaterial color={color} roughness={Math.min(materialProps.roughness + 0.15, 1)} metalness={materialProps.metalness} />
        <boxGeometry args={[0.9, 0.4, 0.5]} />
      </mesh>

      {/* Tongue top - slightly angled up */}
      <mesh position={[0.35, 0.68, 0]} rotation={[0.35, 0, 0]} castShadow>
        <meshStandardMaterial color={color} roughness={Math.min(materialProps.roughness + 0.15, 1)} metalness={materialProps.metalness} />
        <boxGeometry args={[0.5, 0.15, 0.45]} />
      </mesh>

      {/* Collar / opening rim */}
      <mesh position={[-0.2, 0.4, 0.42]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[1.2, 0.12, 0.08]} />
      </mesh>
      <mesh position={[-0.2, 0.4, -0.42]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[1.2, 0.12, 0.08]} />
      </mesh>

      {/* Swoosh / side stripe - left side */}
      <mesh position={[0.05, 0.08, 0.46]} rotation={[0, 0, 0.1]} castShadow>
        <meshStandardMaterial color="#ffffff" roughness={0.4} metalness={0.05} />
        <boxGeometry args={[1.6, 0.06, 0.02]} />
      </mesh>

      {/* Swoosh / side stripe - right side */}
      <mesh position={[0.05, 0.08, -0.46]} rotation={[0, 0, 0.1]} castShadow>
        <meshStandardMaterial color="#ffffff" roughness={0.4} metalness={0.05} />
        <boxGeometry args={[1.6, 0.06, 0.02]} />
      </mesh>

      {/* Second stripe */}
      <mesh position={[0.05, -0.02, 0.46]} rotation={[0, 0, -0.05]} castShadow>
        <meshStandardMaterial color="#ffffff" roughness={0.4} metalness={0.05} />
        <boxGeometry args={[1.4, 0.04, 0.02]} />
      </mesh>
      <mesh position={[0.05, -0.02, -0.46]} rotation={[0, 0, -0.05]} castShadow>
        <meshStandardMaterial color="#ffffff" roughness={0.4} metalness={0.05} />
        <boxGeometry args={[1.4, 0.04, 0.02]} />
      </mesh>

      {/* Eyelet panel - lace area */}
      <mesh position={[0.2, 0.4, 0.2]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[0.8, 0.06, 0.15]} />
      </mesh>
      <mesh position={[0.2, 0.4, -0.2]} castShadow>
        <meshStandardMaterial color={color} {...materialProps} />
        <boxGeometry args={[0.8, 0.06, 0.15]} />
      </mesh>

      {/* Lace dots */}
      {[-0.1, 0.1, 0.3, 0.5].map((x) => (
        <group key={`lace-${x}`}>
          <mesh position={[x, 0.44, 0.2]} material={accentMat}>
            <cylinderGeometry args={[0.025, 0.025, 0.03, 8]} />
          </mesh>
          <mesh position={[x, 0.44, -0.2]} material={accentMat}>
            <cylinderGeometry args={[0.025, 0.025, 0.03, 8]} />
          </mesh>
        </group>
      ))}

      {/* Lace bridge */}
      {[-0.1, 0.1, 0.3, 0.5].map((x) => (
        <mesh key={`bridge-${x}`} position={[x, 0.46, 0]} material={accentMat}>
          <boxGeometry args={[0.02, 0.015, 0.38]} />
        </mesh>
      ))}

      {/* Heel pull tab */}
      <mesh position={[-1.15, 0.58, 0]} material={accentMat} castShadow>
        <boxGeometry args={[0.06, 0.15, 0.2]} />
      </mesh>

      {/* Sole tread pattern */}
      {[-0.8, -0.4, 0, 0.4, 0.8].map((x) => (
        <mesh key={`tread-${x}`} position={[x, -0.43, 0]} material={soleMat}>
          <boxGeometry args={[0.2, 0.02, 0.8]} />
        </mesh>
      ))}
    </group>
  )
}
