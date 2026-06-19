import { IconUsers, IconCheck, IconCreditCard, IconCalendar, IconChart } from './Icons'

const tabs = [
  { key: 'clientes', icon: <IconUsers size={20} />, label: 'Ativos' },
  { key: 'aceitar', icon: <IconCheck size={20} />, label: 'Aceitar' },
  { key: 'pix', icon: <IconCreditCard size={20} />, label: 'Pix' },
  { key: 'mes-6', icon: <IconCalendar size={20} />, label: 'Mes' },
  { key: 'faturamento', icon: <IconChart size={20} />, label: 'Fat' },
]

export default function MobileNav({ activeTab, onSelect }) {
  return (
    <nav className="bottom-nav">
      {tabs.map((t) => (
        <button
          key={t.key}
          className={`nav-item${activeTab === t.key || (t.key.startsWith('mes') && activeTab?.startsWith('mes')) ? ' active' : ''}`}
          onClick={() => onSelect(t.key)}
        >
          {t.icon}
          {t.label}
        </button>
      ))}
    </nav>
  )
}
