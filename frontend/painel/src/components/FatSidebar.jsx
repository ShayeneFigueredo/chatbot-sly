import { useState, useEffect } from 'react'
import PieChart from './PieChart'
import { IconChart } from './Icons'
import { useApi } from '../hooks/useApi'
import '../styles/components/fat-sidebar.css'

const REGION_COLORS = {
  'Sudeste':      '#a78bfa',
  'Nordeste':     '#60a5fa',
  'Sul':          '#34d399',
  'Centro-Oeste': '#fbbf24',
  'Norte':        '#f87171',
}

const ORIGEM_COLORS = {
  'WhatsApp': '#a78bfa',
  'Site':     '#34d399',
}

export default function FatSidebar({ faturamento, dados, mesNome, mesFat }) {
  const api = useApi()
  const f = faturamento || {}
  const d = dados || {}
  const [regioesData, setRegioesData] = useState(null)

  // Carrega dados de regioes do endpoint dedicado (ano inteiro)
  useEffect(() => {
    if (!mesNome) {
      api('/painel/regioes').then(r => {
        if (r && r.regioes) {
          const data = Object.entries(r.regioes)
            .filter(([, v]) => v > 0)
            .map(([label, value]) => ({ label, value, color: REGION_COLORS[label] || '#636378' }))
            .sort((a, b) => b.value - a.value)
          setRegioesData(data)
        }
      }).catch(() => {})
    }
  }, [mesNome])

  // Se for view de mes especifico
  if (mesNome && mesFat) {
    return (
      <div className="fat-sidebar">
        <h3><IconChart size={18} /> {mesNome} 2026</h3>
        <div className="fat-year-card">
          <div className="fat-year-label">Total do Mes</div>
          <div className="fat-year-value">R$ {(mesFat.total || 0).toFixed(2)}</div>
        </div>
        <div className="fat-row">
          <span>Pedidos</span>
          <span className="fat-val">R$ {(mesFat.pedidos || 0).toFixed(2)}</span>
        </div>
        <div className="fat-row fat-site">
          <span>Site</span>
          <span className="fat-val">R$ {(mesFat.site || 0).toFixed(2)}</span>
        </div>
        <div className="fat-total">
          <span className="fat-label">Total</span>
          <span className="fat-number">R$ {(mesFat.total || 0).toFixed(2)}</span>
        </div>
      </div>
    )
  }

  // Origem: Site vs WhatsApp (financeiro)
  const origemData = [
    { label: 'WhatsApp', value: (f.total_shay || 0) + (f.total_samuel || 0), color: ORIGEM_COLORS['WhatsApp'] },
    { label: 'Site', value: f.total_site_bruto || 0, color: ORIGEM_COLORS['Site'] },
  ].filter(d => d.value > 0)

  return (
    <div className="fat-sidebar">
      <h3><IconChart size={18} /> Resumo do Ano</h3>
      <div className="fat-year-card">
        <div className="fat-year-label">Faturamento Total 2026</div>
        <div className="fat-year-value">R$ {(f.total_ano || 0).toFixed(2)}</div>
      </div>
      <div className="fat-row">
        <span>Shayene (SF)</span>
        <span className="fat-val" style={{ color: 'var(--purple-light)' }}>
          R$ {(f.total_shay || 0).toFixed(2)}
        </span>
      </div>
      <div className="fat-row">
        <span>Equipe (SA)</span>
        <span className="fat-val">R$ {(f.total_samuel || 0).toFixed(2)}</span>
      </div>
      <div className="fat-row fat-site">
        <span>Site (liquido)</span>
        <span className="fat-val">R$ {(f.total_site || 0).toFixed(2)}</span>
      </div>
      <div className="fat-row">
        <span>Bruto Site</span>
        <span className="fat-val">R$ {(f.total_site_bruto || 0).toFixed(2)}</span>
      </div>
      <div className="fat-row">
        <span>Taxas Site</span>
        <span className="fat-val">R$ {(f.taxas_site || 0).toFixed(2)}</span>
      </div>
      <div className="fat-total">
        <span className="fat-label">A Receber (50%)</span>
        <span className="fat-number" style={{ color: 'var(--warning)' }}>
          R$ {(f.a_receber || 0).toFixed(2)}
        </span>
      </div>
      <div className="fat-detail">
        <div><strong>{d.pedido_realizado || 0}</strong> pedidos realizados</div>
        <div><strong>{d.aguardando_pix || 0}</strong> aguardando pagamento</div>
        <div><strong>{d.aguardando || 0}</strong> aguardando confirmacao</div>
        <div><strong>{d.aguardando_humano || 0}</strong> querem atendente</div>
      </div>

      {/* Grafico Origem Faturamento */}
      {origemData.length > 0 && (
        <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
          <PieChart
            data={origemData}
            size={180}
            innerRadius={0.55}
            label="Origem do Faturamento"
          />
        </div>
      )}

      {/* Grafico Regioes — dados completos do ano (pedidos.json + clientes ativos) */}
      {regioesData && regioesData.length > 0 && (
        <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
          <PieChart
            data={regioesData}
            size={180}
            innerRadius={0.55}
            label="Clientes por Regiao (Janeiro a Dezembro)"
          />
        </div>
      )}
    </div>
  )
}
