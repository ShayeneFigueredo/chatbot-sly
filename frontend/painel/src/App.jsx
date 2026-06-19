import { useState, useEffect, useCallback, useRef } from 'react'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import MobileNav from './components/MobileNav'
import StatsCards from './components/StatsCards'
import FilterBar from './components/FilterBar'
import TodaySection from './components/TodaySection'
import ClientList from './components/ClientList'
import MonthlyTable from './components/MonthlyTable'
import FatSidebar from './components/FatSidebar'
import FaturamentoView from './components/FaturamentoView'
import Modal from './components/Modal'
import Toast from './components/Toast'
import { useApi } from './hooks/useApi'
import { useToast } from './hooks/useToast'
import { MESES } from './data/constants'

import './styles/tokens.css'
import './styles/global.css'
import './styles/layout.css'
import './styles/components/buttons.css'
import './styles/components/empty-state.css'

const REFRESH_MS = 30000

export default function App() {
  const api = useApi()
  const { message, visible, toast } = useToast()

  // Tab state
  const [activeTab, setActiveTab] = useState('clientes')
  const [currentMes, setCurrentMes] = useState(new Date().getMonth() + 1)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Data state
  const [dados, setDados] = useState(null)
  const [faturamento, setFaturamento] = useState(null)
  const [hoje, setHoje] = useState(null)
  const [mesData, setMesData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Modal state
  const [modalMode, setModalMode] = useState(null) // null | 'add' | 'extrair'

  // Refs for auto-refresh
  const activeTabRef = useRef(activeTab)
  const currentMesRef = useRef(currentMes)

  useEffect(() => {
    activeTabRef.current = activeTab
  }, [activeTab])

  useEffect(() => {
    currentMesRef.current = currentMes
  }, [currentMes])

  // ========== DATA FETCHING ==========
  const loadMainData = useCallback(async () => {
    try {
      const [d, f, h] = await Promise.all([
        api('/painel/dados'),
        api('/painel/faturamento'),
        api('/painel/hoje'),
      ])
      setDados(d)
      setFaturamento(f)
      setHoje(h)
      setError(null)
    } catch (e) {
      console.error('Erro ao carregar dados:', e)
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [api])

  const loadMesData = useCallback(async (mes) => {
    try {
      const d = await api(`/painel/mes/${mes}`)
      setMesData(d)
      setError(null)
    } catch (e) {
      console.error('Erro ao carregar mês:', e)
      setError(e.message)
    }
  }, [api])

  const loadFaturamento = useCallback(async () => {
    try {
      const f = await api('/painel/faturamento')
      setFaturamento(f)
      setError(null)
    } catch (e) {
      console.error('Erro ao carregar faturamento:', e)
    }
  }, [api])

  // Initial load
  useEffect(() => {
    loadMainData()
  }, [loadMainData])

  // Auto-refresh
  useEffect(() => {
    const id = setInterval(() => {
      const tab = activeTabRef.current
      if (tab === 'clientes' || tab === 'aceitar' || tab === 'pix') {
        loadMainData()
      } else if (tab === 'faturamento') {
        loadFaturamento()
      } else if (tab.startsWith('mes-')) {
        loadMesData(currentMesRef.current)
      }
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [loadMainData, loadMesData, loadFaturamento])

  // ========== TAB NAVIGATION ==========
  function handleTabSelect(key) {
    setActiveTab(key)
    if (key === 'clientes' || key === 'aceitar' || key === 'pix') {
      loadMainData()
    } else if (key === 'faturamento') {
      loadMainData() // need faturamento too
    } else if (key.startsWith('mes-')) {
      const mes = parseInt(key.split('-')[1])
      setCurrentMes(mes)
      loadMesData(mes)
    }
  }

  function handleSidebarSelect(key) {
    handleTabSelect(key)
  }

  // ========== CLIENT ACTIONS ==========
  function getActiveFilter() {
    if (activeTab === 'aceitar') return 'confirmados'
    if (activeTab === 'pix') return 'pix'
    return 'ativos'
  }

  async function handleAction(action, tel) {
    const endpoints = {
      bloquear: '/painel/bloquear',
      liberar: '/painel/liberar',
      confirmar: '/painel/confirmar',
      rejeitar: null, // needs prompt
      cutucar: '/painel/cutucar',
      aceitarPedido: '/painel/aceitar-pedido',
      cancelarPedidoCliente: '/painel/cancelar-pedido-cliente',
      finalizar: '/painel/finalizar',
    }

    const messages = {
      bloquear: 'Maya bloqueada para este cliente',
      liberar: 'Maya liberada',
      confirmar: 'Pedido confirmado!',
      cutucar: 'Cutucando...',
      aceitarPedido: 'Pedido aceito! Mensagem enviada.',
      cancelarPedidoCliente: 'Pedido cancelado',
      finalizar: 'Finalizado',
    }

    try {
      if (action === 'rejeitar') {
        const motivo = prompt('Motivo da rejeição:')
        if (!motivo) return
        await api('/painel/rejeitar', { telefone: tel, motivo })
        toast('Rejeitado')
      } else if (action === 'aceitarPedido') {
        if (!confirm('Aceitar pedido e enviar Pix para ' + tel + '?')) return
        await api(endpoints[action], { telefone: tel })
        toast(messages[action])
      } else if (action === 'cancelarPedidoCliente') {
        if (!confirm('Cancelar pedido de ' + tel + '? O cliente será notificado.')) return
        await api(endpoints[action], { telefone: tel })
        toast(messages[action])
      } else if (action === 'finalizar') {
        if (!confirm('Finalizar atendimento de ' + tel + '?')) return
        await api(endpoints[action], { telefone: tel })
        toast(messages[action])
      } else {
        await api(endpoints[action], { telefone: tel })
        toast(messages[action] || 'OK')
      }
      loadMainData()
    } catch (e) {
      toast('Erro: ' + e.message)
    }
  }

  async function handleFinalizarTodos() {
    if (!confirm('ATENÇÃO: Isso vai finalizar TODOS os atendimentos ativos. Continuar?')) return
    try {
      const d = await api('/painel/dados')
      let count = 0
      for (const c of d.clientes || []) {
        await api('/painel/finalizar', { telefone: c.telefone })
        count++
      }
      toast(`✅ ${count} atendimentos finalizados`)
      loadMainData()
    } catch (e) {
      toast('Erro: ' + e.message)
    }
  }

  async function handleTestWebhook() {
    toast('🔌 Testando conexão com webhook do site...')
    try {
      const r = await (await fetch('/webhook/site', { credentials: 'same-origin' })).json()
      toast('✅ Webhook ativo! URL: ' + r.url)
    } catch (e) {
      toast('❌ Erro: ' + e.message)
    }
  }

  // ========== MODAL ACTIONS ==========
  function handleModalClose(subMode) {
    if (subMode === 'add') {
      setModalMode('add')
    } else if (subMode === 'extrair') {
      setModalMode('extrair')
    } else {
      setModalMode(null)
    }
  }

  async function handleModalAdd(d) {
    await api('/painel/adicionar-manual', d)
    toast('Pedido adicionado!')
    setModalMode(null)
    loadMainData()
  }

  function handleModalExtract(pedido, tel) {
    setModalMode(null)
    // Reopen with add mode and fill fields
    setTimeout(() => {
      setModalMode('add')
      setTimeout(() => {
        const set = (id, val) => {
          const el = document.getElementById(id)
          if (el && val) el.value = val
        }
        set('mCliente', pedido.cliente || tel)
        set('mTema', pedido.tema)
        set('mData', pedido.prazo || pedido.data || '')
        set('mNomes', pedido.nomes)
        set('mExtras', pedido.extras)
        if (pedido.arquivo) {
          const sel = document.getElementById('mArquivo')
          if (sel) {
            for (let i = 0; i < sel.options.length; i++) {
              const opt = sel.options[i].text
              let arq = pedido.arquivo.replace(/[🎬🎨📄]/g, '').trim().toLowerCase()
              let optClean = opt.replace(/[🎬🎨📄]/g, '').trim().toLowerCase()
              if (optClean.includes(arq) || arq.includes(optClean)) {
                sel.selectedIndex = i
                break
              }
            }
          }
        }
        if (pedido.valor) {
          const val = pedido.valor.replace(/[R$\s]/g, '').replace(',', '.')
          set('mValor', val)
        }
        toast('Formulario preenchido! Revise e clique Adicionar')
      }, 100)
    }, 200)
  }

  // ========== MONTHLY TABLE ACTIONS ==========
  async function handleSaveEdit(d) {
    await api('/painel/editar-pedido', d)
    toast('Salvo!')
    loadMesData(currentMes)
  }

  async function handleDeletePedido(id) {
    if (!confirm('Deletar permanentemente o pedido #' + id + '?')) return
    await api('/painel/deletar-pedido', { id })
    toast('Removido')
    loadMesData(currentMes)
  }

  // ========== FILTERED CLIENTS ==========
  function getFilteredClients() {
    if (!dados?.clientes) return []
    const filter = getActiveFilter()
    if (filter === 'confirmados') return dados.clientes.filter((c) => c.pedido_confirmado)
    if (filter === 'pix') return dados.clientes.filter((c) => c.aguardando_pix)
    return dados.clientes.filter((c) => !c.pedido_confirmado && !c.aguardando_pix)
  }

  // ========== RENDER CONTENT ==========
  function renderContent() {
    if (loading) {
      return (
        <div className="loading" style={{ padding: '60px 0' }}>
          <span className="loading-spinner" />
          Carregando...
        </div>
      )
    }

    if (error) {
      return (
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <div className="empty-text" style={{ color: 'var(--danger)' }}>Erro ao carregar</div>
          <div className="empty-sub">{error}</div>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={loadMainData}>
            Tentar Novamente
          </button>
        </div>
      )
    }

    // Monthly view
    if (activeTab.startsWith('mes-')) {
      const mes = parseInt(activeTab.split('-')[1])
      const pedidos = mesData?.pedidos || []
      const fat = mesData?.faturamento || {}

      return (
        <div className="content-grid">
          <div className="content-main">
            <MonthlyTable
              mes={mes}
              pedidos={pedidos}
              fat={fat}
              onSave={handleSaveEdit}
              onDelete={handleDeletePedido}
            />
          </div>
          <FatSidebar
            mesNome={MESES[mes]}
            mesFat={fat}
            faturamento={faturamento}
            dados={dados}
          />
        </div>
      )
    }

    // Faturamento view
    if (activeTab === 'faturamento') {
      return (
        <div className="content-grid">
          <div className="content-main">
            <FaturamentoView faturamento={faturamento} />
          </div>
          <FatSidebar faturamento={faturamento} dados={dados} />
        </div>
      )
    }

    // Client views (ativos, aceitar, pix)
    const clients = getFilteredClients()

    return (
      <div className="content-grid">
        <div className="content-main">
          {hoje && (
            <TodaySection pedidos={hoje.pedidos} data={hoje.data} />
          )}
          <ClientList clients={clients} onAction={handleAction} />
        </div>
        <FatSidebar faturamento={faturamento} dados={dados} />
      </div>
    )
  }

  // ========== RENDER ==========
  return (
    <div className="app">
      {/* Mobile sidebar overlay */}
      <div
        className={`sidebar-overlay${sidebarOpen ? ' open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      <Sidebar
        activeTab={activeTab}
        onSelect={(key) => { handleSidebarSelect(key); setSidebarOpen(false) }}
        onFinalizarTodos={handleFinalizarTodos}
        mobileOpen={sidebarOpen}
      />

      <main className="main">
        <TopBar
          onRefresh={loadMainData}
          onNewOrder={() => setModalMode('add')}
          onTestWebhook={handleTestWebhook}
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        <div className="content">
          {dados && faturamento && (
            <StatsCards faturamento={faturamento} dados={dados} />
          )}

          <FilterBar activeTab={activeTab} onSelect={handleTabSelect} />

          {renderContent()}
        </div>
      </main>

      {modalMode && (
        <Modal
          mode={modalMode}
          onClose={handleModalClose}
          onAdd={handleModalAdd}
          onExtract={handleModalExtract}
          apiCall={api}
          toast={toast}
        />
      )}

      <MobileNav activeTab={activeTab} onSelect={handleTabSelect} />
      <Toast message={message} visible={visible} />
    </div>
  )
}
