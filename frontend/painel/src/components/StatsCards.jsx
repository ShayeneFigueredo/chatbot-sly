import { IconMoney, IconPackage, IconCreditCard, IconHeadset } from './Icons'
import '../styles/components/stats-cards.css'

function StatCard({ icon, iconColor, label, value, sub, subColor }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${iconColor}`}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className={`stat-sub ${subColor || ''}`}>{sub}</div>}
    </div>
  )
}

export default function StatsCards({ faturamento, dados }) {
  const f = faturamento || {}
  const d = dados || {}

  return (
    <div className="stats-grid">
      <StatCard
        icon={<IconMoney size={22} />} iconColor="purple"
        label="Faturamento 2026"
        value={`R$ ${(f.total_ano || 0).toFixed(2)}`}
        sub={`SF: R$ ${(f.total_shay || 0).toFixed(2)} | Equipe: R$ ${(f.total_samuel || 0).toFixed(2)}`}
      />
      <StatCard
        icon={<IconPackage size={22} />} iconColor="green"
        label="Pedidos Realizados"
        value={`${d.pedido_realizado || 0} clientes`}
        sub={`Site (liquido): R$ ${(f.total_site || 0).toFixed(2)}`}
        subColor="green"
      />
      <StatCard
        icon={<IconCreditCard size={22} />} iconColor="yellow"
        label="Aguardando Pagamento"
        value={`${d.aguardando_pix || 0} clientes`}
        sub={`A receber: R$ ${(f.a_receber || 0).toFixed(2)}`}
        subColor="yellow"
      />
      <StatCard
        icon={<IconHeadset size={22} />} iconColor="red"
        label="Precisam de Atendente"
        value={`${d.aguardando_humano || 0} clientes`}
        sub={`Aguardando: ${d.aguardando || 0} clientes`}
        subColor="red"
      />
    </div>
  )
}
