import { IconRefresh, IconPlus, IconGlobe } from './Icons'

export default function TopBar({ onRefresh, onNewOrder, onTestWebhook }) {
  return (
    <div className="topbar">
      <div className="topbar-title">
        Painel de Controle
        <span className="status-dot" />
      </div>
      <div className="topbar-actions">
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
