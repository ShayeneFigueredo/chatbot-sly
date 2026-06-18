import '../styles/components/badges.css'

const CLASS_MAP = {
  success: 'badge-success',
  warning: 'badge-warning',
  info: 'badge-info',
  danger: 'badge-danger',
  purple: 'badge-purple',
  cyan: 'badge-cyan',
  pink: 'badge-pink',
}

export default function Badge({ variant = 'info', children, dot = true }) {
  const cls = CLASS_MAP[variant] || 'badge-info'
  return (
    <span className={`badge ${cls}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  )
}
