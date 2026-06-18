import { MESES, LOGO_URL, MAYA_URL } from '../data/constants'
import { IconUsers, IconCheck, IconCreditCard, IconCalendar, IconChart, IconAlert } from './Icons'

export default function Sidebar({ activeTab, onSelect, onFinalizarTodos }) {
  const clientItems = [
    { key: 'clientes', icon: <IconUsers size={18} />, label: 'Ativos' },
    { key: 'aceitar', icon: <IconCheck size={18} />, label: 'Aceitar Pedido' },
    { key: 'pix', icon: <IconCreditCard size={18} />, label: 'Confirmar Pagamento' },
  ]

  const monthItems = Array.from({ length: 12 }, (_, i) => ({
    key: `mes-${i + 1}`,
    icon: <IconCalendar size={18} />,
    label: MESES[i + 1],
  }))

  const finItems = [
    { key: 'faturamento', icon: <IconChart size={18} />, label: 'Faturamento 2026' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <img src={LOGO_URL} alt="Sly Design" onError={(e) => { e.target.style.display = 'none' }} />
        <div className="brand-text">
          <span className="brand-name">Sly Design</span>
          <span className="brand-sub">Painel de Controle</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">Clientes</div>
        {clientItems.map((item) => (
          <button
            key={item.key}
            className={`nav-item${activeTab === item.key ? ' active' : ''}`}
            onClick={() => onSelect(item.key)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        <div className="nav-section">Meses</div>
        {monthItems.map((item) => (
          <button
            key={item.key}
            className={`nav-item${activeTab === item.key ? ' active' : ''}`}
            onClick={() => onSelect(item.key)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        <div className="nav-section">Financeiro</div>
        {finItems.map((item) => (
          <button
            key={item.key}
            className={`nav-item${activeTab === item.key ? ' active' : ''}`}
            onClick={() => onSelect(item.key)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}

        <button className="nav-item danger" onClick={onFinalizarTodos}>
          <span className="nav-icon"><IconAlert size={18} /></span>
          Finalizar Todos
        </button>
      </nav>

      <div className="sidebar-footer">
        <img src={MAYA_URL} alt="Maya" onError={(e) => { e.target.style.display = 'none' }} />
        <div className="maya-info">
          <span className="maya-name">Maya</span>
          <span className="maya-status"><span className="dot" /> Online</span>
        </div>
      </div>
    </aside>
  )
}
