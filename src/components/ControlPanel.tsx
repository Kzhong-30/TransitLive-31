interface ControlPanelProps {
  color: string
  onColorChange: (color: string) => void
  materialType: 'matte' | 'glossy' | 'metallic'
  onMaterialChange: (type: 'matte' | 'glossy' | 'metallic') => void
  autoRotate: boolean
  onAutoRotateToggle: () => void
  onResetView: () => void
}

const COLORS = [
  { name: '烈焰红', value: '#DC2626' },
  { name: '海洋蓝', value: '#2563EB' },
  { name: '森林绿', value: '#059669' },
  { name: '午夜黑', value: '#1F2937' },
  { name: '云雾白', value: '#E5E7EB' },
]

const MATERIALS: { key: 'matte' | 'glossy' | 'metallic'; name: string; icon: string }[] = [
  { key: 'matte', name: '哑光', icon: '◉' },
  { key: 'glossy', name: '高光', icon: '◎' },
  { key: 'metallic', name: '金属', icon: '◆' },
]

export default function ControlPanel({
  color,
  onColorChange,
  materialType,
  onMaterialChange,
  autoRotate,
  onAutoRotateToggle,
  onResetView,
}: ControlPanelProps) {
  return (
    <div className="control-panel">
      <div className="control-section">
        <h3 className="control-title">配色方案</h3>
        <div className="color-grid">
          {COLORS.map((c) => (
            <button
              key={c.value}
              className={`color-swatch ${color === c.value ? 'active' : ''}`}
              style={{ backgroundColor: c.value }}
              onClick={() => onColorChange(c.value)}
              title={c.name}
            >
              {color === c.value && <span className="color-check">✓</span>}
            </button>
          ))}
        </div>
        <div className="color-name">
          {COLORS.find((c) => c.value === color)?.name}
        </div>
      </div>

      <div className="control-section">
        <h3 className="control-title">材质效果</h3>
        <div className="material-grid">
          {MATERIALS.map((m) => (
            <button
              key={m.key}
              className={`material-btn ${materialType === m.key ? 'active' : ''}`}
              onClick={() => onMaterialChange(m.key)}
            >
              <span className="material-icon">{m.icon}</span>
              <span className="material-name">{m.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="control-section">
        <h3 className="control-title">交互控制</h3>
        <div className="control-actions">
          <button
            className={`action-btn ${autoRotate ? 'active' : ''}`}
            onClick={onAutoRotateToggle}
          >
            <span className="action-icon">↻</span>
            <span>自动旋转</span>
            <span className="action-status">{autoRotate ? '开' : '关'}</span>
          </button>
          <button className="action-btn" onClick={onResetView}>
            <span className="action-icon">⟲</span>
            <span>重置视角</span>
          </button>
        </div>
      </div>

      <div className="control-section">
        <h3 className="control-title">操作提示</h3>
        <div className="tips">
          <div className="tip-item"><span className="tip-key">左键拖拽</span> 旋转模型</div>
          <div className="tip-item"><span className="tip-key">右键拖拽</span> 平移视角</div>
          <div className="tip-item"><span className="tip-key">滚轮缩放</span> 远近调节</div>
          <div className="tip-item"><span className="tip-key">热点标注</span> 点击查看详情</div>
        </div>
      </div>
    </div>
  )
}
