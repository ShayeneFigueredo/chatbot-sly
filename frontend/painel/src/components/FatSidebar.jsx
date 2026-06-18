import PieChart from './PieChart'
import { IconChart } from './Icons'
import '../styles/components/fat-sidebar.css'

// Mapeamento DDD → Regiao do Brasil
function dddToRegion(ddd) {
  const d = parseInt(ddd, 10)
  // Norte
  if ([68,69,91,92,93,94,95,96,97].includes(d)) return 'Norte'
  // Nordeste
  if ([71,73,74,75,77,79,81,82,83,84,85,86,87,88,89,98,99].includes(d)) return 'Nordeste'
  // Centro-Oeste
  if ([61,62,63,64,65,66,67].includes(d)) return 'Centro-Oeste'
  // Sudeste
  if ([11,12,13,14,15,16,17,18,19,21,22,24,27,28,31,32,33,34,35,37,38].includes(d)) return 'Sudeste'
  // Sul
  if ([41,42,43,44,45,46,47,48,49,51,53,54,55].includes(d)) return 'Sul'
  return null
}

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

function calcularGraficos(dados, faturamento) {
  const f = faturamento || {}
  const clientes = dados?.clientes || []

  // 1. Origem: Site vs WhatsApp (financeiro)
  const origemData = [
    { label: 'WhatsApp', value: (f.total_shay || 0) + (f.total_samuel || 0), color: ORIGEM_COLORS['WhatsApp'] },
    { label: 'Site', value: f.total_site_bruto || 0, color: ORIGEM_COLORS['Site'] },
  ].filter(d => d.value > 0)

  // 2. Regioes por DDD
  const regiaoCount = {}
  let comDdd = 0
  clientes.forEach(c => {
    const tel = (c.telefone || '').replace(/\D/g, '')
    // Extrai DDD: para numeros brasileiros: 55XX... ou 0XX... ou XX...
    let ddd = null
    if (tel.startsWith('55') && tel.length >= 13) {
      ddd = tel.substring(2, 4)
    } else if (tel.startsWith('0') && tel.length >= 11) {
      ddd = tel.substring(1, 3)
    } else if (tel.length >= 10 && !tel.startsWith('55') && !tel.startsWith('0')) {
      ddd = tel.substring(0, 2)
    }
    if (ddd) {
      const regiao = dddToRegion(ddd)
      if (regiao) {
        regiaoCount[regiao] = (regiaoCount[regiao] || 0) + 1
        comDdd++
      }
    }
  })

  const regioesData = Object.entries(regiaoCount)
    .map(([label, value]) => ({ label, value, color: REGION_COLORS[label] || '#636378' }))
    .sort((a, b) => b.value - a.value)

  return { origemData, regioesData }
}

export default function FatSidebar({ faturamento, dados, mesNome, mesFat }) {
  const f = faturamento || {}
  const d = dados || {}

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

  const { origemData, regioesData } = calcularGraficos(dados, faturamento)

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

      {/* Graficos */}
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

      {regioesData.length > 0 && (
        <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--border)' }}>
          <PieChart
            data={regioesData}
            size={180}
            innerRadius={0.55}
            label="Clientes por Regiao"
          />
        </div>
      )}
    </div>
  )
}
