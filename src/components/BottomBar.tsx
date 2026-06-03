interface BottomBarProps {
  onViewChange: (view: { position: [number, number, number]; target: [number, number, number]; key?: string }) => void
  currentView: string
}

const VIEWS = [
  {
    key: 'front',
    name: '正面',
    position: [0, 1.2, 4.5] as [number, number, number],
    target: [0, 0.5, 0] as [number, number, number],
    icon: '⬜',
  },
  {
    key: 'side',
    name: '侧面',
    position: [4.5, 1.2, 0] as [number, number, number],
    target: [0, 0.5, 0] as [number, number, number],
    icon: '▬',
  },
  {
    key: 'top',
    name: '顶部',
    position: [0.5, 4.5, 0.5] as [number, number, number],
    target: [0, 0, 0] as [number, number, number],
    icon: '⬛',
  },
  {
    key: 'detail',
    name: '细节特写',
    position: [1.8, 1.0, 2.0] as [number, number, number],
    target: [0.8, 0.3, 0] as [number, number, number],
    icon: '🔍',
  },
]

export default function BottomBar({ onViewChange, currentView }: BottomBarProps) {
  return (
    <div className="bottom-bar">
      <div className="bottom-bar-label">视角预设</div>
      <div className="view-thumbnails">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            className={`view-thumb ${currentView === v.key ? 'active' : ''}`}
            onClick={() => onViewChange({ position: v.position, target: v.target, key: v.key })}
          >
            <div className="view-thumb-icon">{v.icon}</div>
            <div className="view-thumb-name">{v.name}</div>
          </button>
        ))}
      </div>
    </div>
  )
}
