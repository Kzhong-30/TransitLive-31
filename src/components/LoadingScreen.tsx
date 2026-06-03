import { useEffect, useState } from 'react'

interface LoadingScreenProps {
  visible: boolean
}

export default function LoadingScreen({ visible }: LoadingScreenProps) {
  const [progress, setProgress] = useState(0)
  const [opacity, setOpacity] = useState(1)

  useEffect(() => {
    if (visible) {
      setOpacity(1)
      setProgress(0)
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev
          return prev + Math.random() * 15
        })
      }, 200)
      return () => clearInterval(interval)
    } else {
      setProgress(100)
      const fadeTimer = setTimeout(() => {
        setOpacity(0)
      }, 300)
      return () => clearTimeout(fadeTimer)
    }
  }, [visible])

  if (opacity <= 0) return null

  return (
    <div className="loading-screen" style={{ opacity }}>
      <div className="loading-content">
        <div className="skeleton-shoe">
          <div className="skeleton-sole skeleton-shimmer" />
          <div className="skeleton-midsole skeleton-shimmer" />
          <div className="skeleton-upper skeleton-shimmer" />
          <div className="skeleton-tongue skeleton-shimmer" />
        </div>
        <div className="loading-text">正在加载 3D 模型...</div>
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${Math.min(progress, 100)}%` }} />
        </div>
        <div className="progress-text">{Math.min(Math.round(progress), 100)}%</div>
      </div>
    </div>
  )
}
