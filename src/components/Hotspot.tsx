import { useState, useRef, useEffect, useCallback } from 'react'
import { Html } from '@react-three/drei'

interface HotspotProps {
  position: [number, number, number]
  label: string
  description: string
}

type PopupPlacement = 'top' | 'bottom' | 'left' | 'right'

export default function Hotspot({ position, label, description }: HotspotProps) {
  const [active, setActive] = useState(false)
  const [placement, setPlacement] = useState<PopupPlacement>('top')
  const popupRef = useRef<HTMLDivElement>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)

  const computePlacement = useCallback(() => {
    if (!popupRef.current || !wrapperRef.current) return

    const wrapperRect = wrapperRef.current.getBoundingClientRect()
    const popupRect = popupRef.current.getBoundingClientRect()
    const vw = window.innerWidth
    const vh = window.innerHeight

    const overflowTop = wrapperRect.top - popupRect.height - 10
    const overflowBottom = wrapperRect.bottom + popupRect.height + 10
    const overflowLeft = wrapperRect.left - popupRect.width - 10
    const overflowRight = wrapperRect.right + popupRect.width + 10

    let newPlacement: PopupPlacement = 'top'

    if (overflowTop >= 0 && overflowBottom <= vh) {
      newPlacement = 'top'
    } else if (overflowBottom <= vh) {
      newPlacement = 'bottom'
    } else if (overflowRight <= vw) {
      newPlacement = 'right'
    } else if (overflowLeft >= 0) {
      newPlacement = 'left'
    } else {
      newPlacement = overflowTop >= 0 ? 'top' : 'bottom'
    }

    setPlacement(newPlacement)
  }, [])

  useEffect(() => {
    if (active) {
      requestAnimationFrame(() => {
        computePlacement()
      })
    }
  }, [active, computePlacement])

  const popupStyle = getPopupPositionStyle(placement)

  return (
    <Html position={position} center distanceFactor={8} style={{ pointerEvents: 'auto' }}>
      <div className="hotspot-wrapper" ref={wrapperRef}>
        <div
          className={`hotspot-marker ${active ? 'active' : ''}`}
          onClick={(e) => {
            e.stopPropagation()
            setActive(!active)
          }}
        >
          <div className="hotspot-ping" />
          <div className="hotspot-dot" />
        </div>
        {active && (
          <div
            ref={popupRef}
            className="hotspot-popup"
            data-placement={placement}
            style={popupStyle}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="hotspot-popup-header">
              <span className="hotspot-popup-title">{label}</span>
              <button className="hotspot-popup-close" onClick={() => setActive(false)}>
                ×
              </button>
            </div>
            <div className="hotspot-popup-body">{description}</div>
            <div className={`hotspot-popup-arrow hotspot-popup-arrow-${placement}`} />
          </div>
        )}
      </div>
    </Html>
  )
}

function getPopupPositionStyle(placement: PopupPlacement): React.CSSProperties {
  switch (placement) {
    case 'top':
      return { bottom: '40px', left: '50%', transform: 'translateX(-50%)' }
    case 'bottom':
      return { top: '40px', left: '50%', transform: 'translateX(-50%)' }
    case 'left':
      return { right: '40px', top: '50%', transform: 'translateY(-50%)' }
    case 'right':
      return { left: '40px', top: '50%', transform: 'translateY(-50%)' }
  }
}
