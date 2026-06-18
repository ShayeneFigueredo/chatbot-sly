import { MESES } from '../data/constants'
import { IconChart } from './Icons'
import '../styles/components/fat-sidebar.css'

export default function FaturamentoView({ faturamento }) {
  const f = faturamento || {}
  const mensal = f.mensal || {}

  return (
    <div style={{ maxWidth: 560, margin: '0 auto' }}>
      <h2 style={{ color: 'var(--purple-light)', marginBottom: 16 }}>
        <IconChart size={22} /> Faturamento 2026
      </h2>
      <div className="fat-sidebar" style={{ position: 'static' }}>
        <div className="fat-year-card">
          <div className="fat-year-label">TOTAL 2026</div>
          <div className="fat-year-value">R$ {(f.total_ano || 0).toFixed(2)}</div>
        </div>
        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => {
          const v = mensal[m] || { pedidos: 0, site: 0, total: 0 }
          return (
            <div key={m} className="fat-row">
              <span>{MESES[m]}</span>
              <span className="fat-val">R$ {v.total.toFixed(2)}</span>
            </div>
          )
        })}
        <div className="fat-total">
          <span className="fat-label">TOTAL</span>
          <span className="fat-number">R$ {(f.total_ano || 0).toFixed(2)}</span>
        </div>
        <div className="fat-detail">
          <div>
            <strong>Shayene (SF):</strong>{' '}
            <span style={{ color: 'var(--purple-light)' }}>R$ {(f.total_shay || 0).toFixed(2)}</span>
          </div>
          <div>
            <strong>Equipe (SA):</strong> R$ {(f.total_samuel || 0).toFixed(2)}
          </div>
          <div className="fat-site">
            <strong>Site (liquido):</strong> R$ {(f.total_site || 0).toFixed(2)}
          </div>
          <div style={{ fontSize: '.72em', color: 'var(--text-muted)' }}>
            Bruto: R$ {(f.total_site_bruto || 0).toFixed(2)} | Taxas: R$ {(f.taxas_site || 0).toFixed(2)}
          </div>
          <div style={{ color: 'var(--warning)', marginTop: 4 }}>
            <strong>A receber:</strong> R$ {(f.a_receber || 0).toFixed(2)}{' '}
            <span style={{ fontSize: '.72em' }}>(50% restante)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
