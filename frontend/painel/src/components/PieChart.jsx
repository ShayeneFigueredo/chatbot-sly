// Gráfico de pizza SVG simples e profissional
// Recebe: data = [{ label, value, color }]

export default function PieChart({ data, size = 180, innerRadius = 0.55, label = '' }) {
  if (!data || data.length === 0) return null

  const total = data.reduce((sum, d) => sum + d.value, 0)
  if (total === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)', fontSize: '.8rem' }}>
        Sem dados para exibir
      </div>
    )
  }

  const center = size / 2
  const radius = size / 2 - 2
  const inner = radius * innerRadius

  // Generate SVG arc paths
  let cumulative = 0
  const slices = data.map((d, i) => {
    const startAngle = (cumulative / total) * 2 * Math.PI - Math.PI / 2
    cumulative += d.value
    const endAngle = (cumulative / total) * 2 * Math.PI - Math.PI / 2

    const x1 = center + radius * Math.cos(startAngle)
    const y1 = center + radius * Math.sin(startAngle)
    const x2 = center + radius * Math.cos(endAngle)
    const y2 = center + radius * Math.sin(endAngle)

    const largeArc = d.value / total > 0.5 ? 1 : 0

    // Donut path
    const ix1 = center + inner * Math.cos(startAngle)
    const iy1 = center + inner * Math.sin(startAngle)
    const ix2 = center + inner * Math.cos(endAngle)
    const iy2 = center + inner * Math.sin(endAngle)

    const path = [
      `M ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${ix2} ${iy2}`,
      `A ${inner} ${inner} 0 ${largeArc} 0 ${ix1} ${iy1}`,
      'Z'
    ].join(' ')

    const percent = ((d.value / total) * 100).toFixed(1)

    return { path, color: d.color, label: d.label, value: d.value, percent }
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      {label && (
        <span style={{ fontSize: '.78rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '.05em' }}>
          {label}
        </span>
      )}
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {slices.map((s, i) => (
          <path
            key={i}
            d={s.path}
            fill={s.color}
            stroke="var(--bg)"
            strokeWidth="2"
            style={{ transition: 'opacity .15s', cursor: 'pointer' }}
            onMouseEnter={(e) => { e.target.style.opacity = '0.85' }}
            onMouseLeave={(e) => { e.target.style.opacity = '1' }}
          />
        ))}
        {/* Center text */}
        <text x={center} y={center - 6} textAnchor="middle" fill="var(--text)" fontSize="1.05rem" fontWeight="700" fontFamily="Montserrat, sans-serif">
          {total.toLocaleString()}
        </text>
        <text x={center} y={center + 12} textAnchor="middle" fill="var(--text-muted)" fontSize=".62rem" fontWeight="500" textTransform="uppercase" letterSpacing=".05em">
          TOTAL
        </text>
      </svg>
      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px', justifyContent: 'center' }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '.75rem' }}>
            <span style={{ width: 10, height: 10, borderRadius: 3, background: s.color, flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
            <span style={{ fontWeight: 600, color: 'var(--text)' }}>{s.percent}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
