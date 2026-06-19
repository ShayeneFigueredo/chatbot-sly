import { IconRefresh, IconPlus, IconGlobe } from './Icons'

export default function TopBar({ onRefresh, onNewOrder, onTestWebhook, onMenuToggle }) {
  return (
    <div className="topbar">
      <div className="topbar-title">
        <button className="hamburger" onClick={onMenuToggle} aria-label="Menu">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        Painel de Controle
        <span className="status-dot" />
      </div>
      <div className="topbar-actions">
        <a href="/login" className="btn btn-ghost btn-sm" style={{ textDecoration: 'none' }}>
          ← Portal
        </a>
        <button className="btn btn-primary btn-sm" onClick={onRefresh}>
          <IconRefresh size={15} /> Atualizar
        </button>
        <button className="btn btn-success btn-sm" onClick={onNewOrder}>
          <IconPlus size={15} /> Novo Pedido
        </button>
        <button className="btn btn-ghost btn-sm" onClick={onTestWebhook}>
          <IconGlobe size={15} /> Webhook
        </button>
      </div>
    </div>
  )
}
