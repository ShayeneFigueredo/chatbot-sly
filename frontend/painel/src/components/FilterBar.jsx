import { MESES } from '../data/constants'
import { IconUsers, IconCheck, IconCreditCard, IconChart } from './Icons'
import '../styles/components/filter-bar.css'

export default function FilterBar({ activeTab, onSelect }) {
  const pills = [
    { key: 'clientes', label: 'Ativos', icon: <IconUsers size={14} />, cls: '' },
    { key: 'aceitar', label: 'Aceitar Pedido', icon: <IconCheck size={14} />, cls: '' },
    { key: 'pix', label: 'Confirmar Pagamento', icon: <IconCreditCard size={14} />, cls: '' },
  ]

  const months = Array.from({ length: 12 }, (_, i) => ({
    key: `mes-${i + 1}`,
    label: MESES[i + 1].substring(0, 3),
    cls: 'month',
  }))

  const extraPills = [
    { key: 'faturamento', label: 'Faturamento', icon: <IconChart size={14} />, cls: 'accent' },
  ]

  return (
    <div className="filter-bar">
      {pills.map((p) => (
        <button
          key={p.key}
          className={`filter-pill${activeTab === p.key ? ' active' : ''}${p.cls ? ` ${p.cls}` : ''}`}
          onClick={() => onSelect(p.key)}
        >
          {p.icon} {p.label}
        </button>
      ))}

      <span className="filter-divider" />

      {months.map((m) => (
        <button
          key={m.key}
          className={`filter-pill month${activeTab === m.key ? ' active' : ''}`}
          onClick={() => onSelect(m.key)}
        >
          {m.label}
        </button>
      ))}

      <span className="filter-divider" />

      {extraPills.map((p) => (
        <button
          key={p.key}
          className={`filter-pill${activeTab === p.key ? ' active' : ''}${p.cls ? ` ${p.cls}` : ''}`}
          onClick={() => onSelect(p.key)}
        >
          {p.icon} {p.label}
        </button>
      ))}
    </div>
  )
}
