import { useState } from 'react'
import { sel } from '../utils/helpers'
import { TIPOS, SITUACOES, PAGAMENTOS, RESP, MESES } from '../data/constants'
import { IconPlus, IconSparkle, IconBot } from './Icons'
import '../styles/components/modal.css'
import '../styles/components/forms.css'

export default function Modal({ mode, onClose, onAdd, onExtract, apiCall, toast }) {
  const [extracting, setExtracting] = useState(false)
  const [extractStatus, setExtractStatus] = useState('')
  const [extractTel, setExtractTel] = useState('')

  async function handleExtract() {
    if (!extractTel.trim()) {
      toast('Informe o numero do telefone')
      return
    }
    setExtracting(true)
    setExtractStatus('Analisando conversa com IA...')
    try {
      const r = await apiCall('/painel/extrair-pedido', { telefone: extractTel })
      if (r.status !== 'ok') {
        setExtractStatus(`Erro: ${r.msg}`)
        setExtracting(false)
        return
      }
      setExtractStatus('Extraido! Preenchendo formulario...')
      onExtract(r.pedido, extractTel)
    } catch (e) {
      setExtractStatus(`Erro: ${e.message}`)
    } finally {
      setExtracting(false)
    }
  }

  function handleSubmit() {
    const getVal = (id) => document.getElementById(id)?.value || ''
    const d = {
      cliente: getVal('mCliente'),
      data: getVal('mData'),
      arquivo: getVal('mArquivo'),
      tema: getVal('mTema'),
      valor: 'R$ ' + getVal('mValor'),
      nomes: getVal('mNomes'),
      extras: getVal('mExtras'),
      mes: MESES.indexOf(getVal('mMes')),
      situacao: getVal('mSit'),
      pg: getVal('mPg'),
      responsavel: getVal('mResp'),
      origem: 'manual',
    }
    if (!d.cliente || !d.tema) {
      toast('Preencha cliente e tema')
      return
    }
    // Data de entrega vira tanto data quanto prazo/entrega
    if (d.data) {
      d.entrega = d.data
      d.prazo = d.data
    }
    onAdd(d)
  }

  // Extract mode
  if (mode === 'extrair') {
    return (
      <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
        <div className="modal-box">
          <h3><IconBot size={22} /> Extrair Pedido da Conversa</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '.85rem', marginBottom: 16 }}>
            Informe o numero do WhatsApp do cliente.<br />
            A IA vai ler a conversa e preencher o formulario automaticamente.
          </p>
          <div className="form-group" style={{ marginBottom: 12 }}>
            <label className="form-label">Telefone do Cliente</label>
            <input
              className="form-input"
              placeholder="5538997507651"
              value={extractTel}
              onChange={(e) => setExtractTel(e.target.value)}
              style={{ fontSize: '1rem', padding: '14px' }}
            />
          </div>
          {extractStatus && (
            <div style={{
              color: extractStatus.includes('Erro') ? 'var(--danger)' : extractStatus.includes('Extraido') ? 'var(--success)' : 'var(--text-muted)',
              fontSize: '.8rem',
              margin: '8px 0'
            }}>
              {extractStatus}
            </div>
          )}
          <div className="modal-actions">
            <button className="btn btn-success" onClick={handleExtract} disabled={extracting}>
              <IconSparkle size={16} /> Extrair
            </button>
            <button className="btn btn-ghost" onClick={() => onClose('add')}>
              Voltar ao Formulario
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Add mode (default)
  const mesAtual = new Date().getMonth() + 1

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal-box">
        <h3><IconPlus size={22} /> Novo Pedido Manual</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Cliente (telefone)</label>
              <input className="form-input" placeholder="5538997507651" id="mCliente" />
            </div>
            <div className="form-group">
              <label className="form-label">Data de Entrega (dd/mm)</label>
              <input className="form-input" placeholder="25/06" id="mData" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Tipo de Arquivo</label>
              <div dangerouslySetInnerHTML={{ __html: `<select id="mArquivo" class="form-select">${TIPOS.map(t => `<option>${t}</option>`).join('')}</select>` }} />
            </div>
            <div className="form-group">
              <label className="form-label">Tema</label>
              <input className="form-input" placeholder="Ex: Egito Antigo" id="mTema" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Valor (ex: 25,00)</label>
              <input className="form-input" placeholder="25,00" id="mValor" />
            </div>
            <div className="form-group">
              <label className="form-label">Nomes (ex: Joao, Maria)</label>
              <input className="form-input" placeholder="Nomes dos alunos" id="mNomes" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Extras / Observacoes</label>
            <input className="form-input" placeholder="Info adicional..." id="mExtras" />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Situacao</label>
              <div dangerouslySetInnerHTML={{ __html: sel('mSit', SITUACOES, 'Em andamento') }} />
            </div>
            <div className="form-group">
              <label className="form-label">Pagamento</label>
              <div dangerouslySetInnerHTML={{ __html: sel('mPg', PAGAMENTOS, 'Aguardando') }} />
            </div>
            <div className="form-group">
              <label className="form-label">Responsavel</label>
              <div dangerouslySetInnerHTML={{ __html: sel('mResp', RESP, 'SF') }} />
            </div>
            <div className="form-group">
              <label className="form-label">Mes</label>
              <div dangerouslySetInnerHTML={{ __html: sel('mMes', MESES.slice(1), MESES[mesAtual]) }} />
            </div>
          </div>
          <div className="modal-actions">
            <button className="btn btn-success btn-lg" onClick={handleSubmit}>
              <IconPlus size={18} /> Adicionar Pedido
            </button>
            <button className="btn btn-info" onClick={() => onClose('extrair')}>
              <IconBot size={16} /> Extrair da Conversa
            </button>
            <button className="btn btn-ghost" onClick={() => onClose()}>
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
