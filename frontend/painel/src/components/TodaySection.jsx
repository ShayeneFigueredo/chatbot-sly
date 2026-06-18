import Badge from './Badge'
import { badgeClass, pgClass, rowClass, esc } from '../utils/helpers'
import { IconCalendar } from './Icons'

export default function TodaySection({ pedidos, data }) {
  if (!pedidos || pedidos.length === 0) {
    return (
      <div className="today-section">
        <div className="section-header">
          <span className="section-title"><IconCalendar size={18} /> Slides para Hoje</span>
          <span className="section-count">{data}</span>
        </div>
        <div className="empty-state">
          <div className="empty-icon" style={{ fontSize: '2rem', opacity: 0.4 }}>&mdash;</div>
          <div className="empty-text">Nenhum slide para hoje</div>
          <div className="empty-sub">Aproveite o dia!</div>
        </div>
      </div>
    )
  }

  return (
    <div className="today-section">
      <div className="section-header">
        <span className="section-title"><IconCalendar size={18} /> Slides para Hoje</span>
        <span className="section-count">
          {data} &middot; {pedidos.length} slide{pedidos.length > 1 ? 's' : ''}
        </span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Entrega</th><th>Cliente</th><th>Arquivo</th>
              <th>Tema</th><th>Valor</th><th>Situacao</th><th>PG</th>
            </tr>
          </thead>
          <tbody>
            {pedidos.map((p, i) => (
              <tr key={i} className={rowClass(p.situacao || '')}>
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
                  <Badge variant={pgClass(p.pg || '').replace('badge-', '')} dot={false}>
                    {p.pg || ''}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
