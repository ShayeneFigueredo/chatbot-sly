import { useState } from 'react'
import Badge from './Badge'
import { badgeClass, pgClass, rowClass, esc, sel } from '../utils/helpers'
import { MESES, TIPOS, SITUACOES, PAGAMENTOS, RESP } from '../data/constants'
import { IconEdit, IconTrash } from './Icons'
import '../styles/components/table.css'
import '../styles/components/forms.css'

export default function MonthlyTable({ mes, pedidos, fat, onSave, onDelete, onBack }) {
  const [editing, setEditing] = useState(null)

  function handleEdit(id) {
    const p = pedidos.find((p) => p.id === id)
    if (!p) return
    setEditing(p)
  }

  function handleSave() {
    const el = (id) => document.getElementById(id)
    const d = { id: editing.id }
    const map = [
      ['ed_entrega', 'entrega'],
      ['ed_cliente', 'cliente'],
      ['ed_tema', 'tema'],
      ['ed_valor', 'valor'],
    ]
    map.forEach(([eid, key]) => {
      const v = el(eid)
      if (v) d[key] = v.value
    })
    if (editing.arquivo?.includes('Temas')) {
      const td = el('ed_tdesign')
      if (td) d.tema_design = td.value
    }
    const arquivoEl = document.getElementById('ed_arquivo')
    if (arquivoEl) {
      d.arquivo = arquivoEl.value
      if (d.arquivo?.includes('Temas') && d.tema_design) {
        d.arquivo = d.arquivo + ' — ' + d.tema_design
      }
    }
    const sitEl = document.getElementById('ed_sit')
    if (sitEl) d.situacao = sitEl.value
    const pgEl = document.getElementById('ed_pg')
    if (pgEl) d.pg = pgEl.value
    const respEl = document.getElementById('ed_resp')
    if (respEl) d.responsavel = respEl.value

    onSave(d)
    setEditing(null)
  }

  if (editing) {
    const p = editing
    const arquivo = p.arquivo || ''
    const ehTemas = arquivo.includes('Temas')

    return (
      <div style={{ maxWidth: 560, margin: '0 auto' }}>
        <h2 style={{ color: 'var(--purple-light)', marginBottom: 20 }}>
          <IconEdit size={20} /> Editando Pedido #{p.id}
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Entrega</label>
              <input className="form-input" defaultValue={p.entrega || p.data || ''} id="ed_entrega" />
            </div>
            <div className="form-group">
              <label className="form-label">Cliente</label>
              <input className="form-input" defaultValue={p.cliente || ''} id="ed_cliente" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Arquivo</label>
            <div dangerouslySetInnerHTML={{ __html: sel('ed_arquivo', TIPOS, arquivo) }} />
          </div>
          {ehTemas && (
            <div className="form-group">
              <label className="form-label">Tema Design</label>
              <input className="form-input" defaultValue={p.tema_design || ''} id="ed_tdesign" />
            </div>
          )}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Tema</label>
              <input className="form-input" defaultValue={p.tema || ''} id="ed_tema" />
            </div>
            <div className="form-group">
              <label className="form-label">Valor</label>
              <input className="form-input" defaultValue={p.valor || ''} id="ed_valor" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Situacao</label>
              <div dangerouslySetInnerHTML={{ __html: sel('ed_sit', SITUACOES, p.situacao || 'Novo') }} />
            </div>
            <div className="form-group">
              <label className="form-label">Pagamento</label>
              <div dangerouslySetInnerHTML={{ __html: sel('ed_pg', PAGAMENTOS, p.pg || 'Aguardando') }} />
            </div>
            <div className="form-group">
              <label className="form-label">Responsavel</label>
              <div dangerouslySetInnerHTML={{ __html: sel('ed_resp', RESP, p.responsavel || 'SF') }} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button className="btn btn-success" onClick={handleSave}>Salvar</button>
            <button className="btn btn-ghost" onClick={() => setEditing(null)}>Cancelar</button>
          </div>
        </div>
      </div>
    )
  }

  const rows = pedidos.map((p) => (
    <tr key={p.id} className={rowClass(p.situacao || '')}>
      <td className="date-cell">{p.entrega || p.data || ''}</td>
      <td>{esc(p.cliente || '')}</td>
      <td>{esc(p.arquivo || '')}</td>
      <td>{esc(p.tema || '')}</td>
      <td>{esc(p.valor || '')}</td>
      <td>
        <Badge variant={badgeClass(p.situacao || '').replace('badge-', '')}>
          {p.situacao || ''}
        </Badge>
      </td>
      <td>
        <Badge variant={pgClass(p.pg || '').replace('badge-', '')}>
          {p.pg || ''}
        </Badge>
      </td>
      <td style={{ fontWeight: 600 }}>{p.responsavel || 'SF'}</td>
      <td className="actions-cell">
        <button className="btn btn-info btn-sm" onClick={() => handleEdit(p.id)}><IconEdit size={14} /> Editar</button>
        <button className="btn btn-danger btn-sm" onClick={() => onDelete(p.id)}><IconTrash size={14} /></button>
      </td>
    </tr>
  ))

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ color: 'var(--purple-light)', margin: 0 }}>{MESES[mes]} 2026</h2>
        <span style={{ color: 'var(--text-muted)', fontSize: '.85rem' }}>{pedidos.length} pedidos</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Entrega</th><th>Cliente</th><th>Arquivo</th>
              <th>Tema</th><th>Valor</th><th>Situacao</th>
              <th>PG</th><th>Resp</th><th style={{ width: 110 }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.length > 0 ? rows : (
              <tr>
                <td colSpan={9}>
                  <div className="empty-state">
                    <div className="empty-icon">&mdash;</div>
                    <div className="empty-text">Nenhum pedido em {MESES[mes]}</div>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
