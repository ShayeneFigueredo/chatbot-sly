import Badge from './Badge'
import { statusBadgeClass, cardBorderClass, formatPhone, isLID, formatClientId } from '../utils/helpers'
import { IconPhone, IconAlert, IconCheck, IconX, IconLock, IconUnlock, IconEye, IconCreditCard } from './Icons'
import '../styles/components/client-card.css'

function statusVariant(cls) {
  const map = {
    'status-ativo': 'info',
    'status-pagamento': 'warning',
    'status-humano': 'danger',
    'status-aguardando-humano': 'pink',
    'status-confirmado': 'cyan',
    'status-pix': 'warning',
    'status-shay': 'info',
    'status-shay-assumiu': 'purple',
  }
  return map[cls] || 'info'
}

export default function ClientCard({ client, onAction }) {
  const c = client
  const borderCls = cardBorderClass(c.situacao || '')
  const badgeVariant = statusVariant(c.statusCls || 'status-ativo')

  const extrasInfo = c.extras && c.extras !== '-' && c.extras !== 'Nenhum' ? (
    <div className="info-item">
      <span className="info-label">Extras</span>
      <span className="info-value">
        {c.extras.length > 60 ? c.extras.substring(0, 60) + '...' : c.extras}
      </span>
    </div>
  ) : null

  const helpBanner = c.quer_atendente && !c.shay_assumiu ? (
    <div className="help-banner">
      <IconAlert size={16} /> <strong>{c.nome || 'Cliente'}</strong> pediu para falar com um <strong>atendente humano</strong> &mdash; {isLID(c.telefone) ? `ID: ${(c.telefone || '').replace(/\D/g, '')}` : formatPhone(c.telefone)}
    </div>
  ) : null

  function renderActions() {
    const btns = []
    const tel = c.telefone

    if (c.quer_atendente) {
      if (c.shay_assumiu) {
        btns.push(
          <button key="aceitar" className="btn btn-success" onClick={() => onAction('aceitarPedido', tel)}><IconCheck size={15} /> Aceitar Pedido</button>,
          <button key="fin" className="btn btn-ghost btn-sm" onClick={() => onAction('finalizar', tel)}>Finalizar</button>
        )
      } else {
        btns.push(
          <button key="assumir" className="btn btn-danger" onClick={() => onAction('bloquear', tel)}><IconLock size={15} /> Assumir Atendimento</button>,
          <button key="fin" className="btn btn-ghost btn-sm" onClick={() => onAction('finalizar', tel)}>Finalizar</button>
        )
      }
    } else if (c.pedido_confirmado) {
      btns.push(
        <button key="aceitar" className="btn btn-success" onClick={() => onAction('aceitarPedido', tel)}><IconCheck size={15} /> Aceitar e Pedir Pagamento</button>,
        <button key="rej" className="btn btn-danger" onClick={() => onAction('rejeitar', tel)}><IconX size={15} /> Recusar</button>,
        <button key="fin" className="btn btn-ghost btn-sm" onClick={() => onAction('finalizar', tel)}>Finalizar</button>
      )
    } else if (c.aguardando_pix) {
      btns.push(
        <button key="confirmar" className="btn btn-success" onClick={() => onAction('confirmar', tel)}><IconCheck size={15} /> Confirmar Pedido</button>,
        <button key="cancel" className="btn btn-danger" onClick={() => onAction('cancelarPedidoCliente', tel)}><IconX size={15} /> Cancelar</button>,
        <button key="fin" className="btn btn-ghost btn-sm" onClick={() => onAction('finalizar', tel)}>Finalizar</button>
      )
    } else {
      if (c.aguardando) {
        btns.push(
          <button key="confirmar" className="btn btn-success" onClick={() => onAction('confirmar', tel)}><IconCheck size={15} /> Confirmar</button>,
          <button key="rej" className="btn btn-warning" onClick={() => onAction('rejeitar', tel)}>Rejeitar</button>
        )
      }
      btns.push(
        <button key="cutucar" className="btn btn-info" onClick={() => onAction('cutucar', tel)}><IconEye size={15} /> Cutucar</button>
      )
      if (c.humano) {
        btns.push(<button key="lib" className="btn btn-ghost" onClick={() => onAction('liberar', tel)}><IconUnlock size={15} /> Liberar Maya</button>)
      } else {
        btns.push(<button key="bloq" className="btn btn-danger" onClick={() => onAction('bloquear', tel)}><IconLock size={15} /> Bloquear Maya</button>)
      }
      btns.push(<button key="fin" className="btn btn-ghost btn-sm" onClick={() => onAction('finalizar', tel)}>Finalizar</button>)
    }
    return btns
  }

  return (
    <div className={`client-card ${borderCls}`}>
      <div className="card-top">
        <span className="card-phone">
          <span className="phone-icon"><IconPhone size={18} /></span>
          {isLID(c.telefone) && c.nome ? (
            <span>
              <span style={{ fontWeight: 700 }}>{c.nome}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '.7rem', marginLeft: 6 }}>
                [ID: {(c.telefone || '').replace(/\D/g, '')}]
              </span>
            </span>
          ) : isLID(c.telefone) ? (
            <span>
              <span style={{ fontWeight: 600 }}>ID: {(c.telefone || '').replace(/\D/g, '')}</span>
            </span>
          ) : (
            formatPhone(c.telefone)
          )}
        </span>
        <Badge variant={badgeVariant}>{c.statusTxt || 'Ativo'}</Badge>
      </div>

      {helpBanner}

      <div className="card-info">
        <div className="info-item">
          <span className="info-label">Tema</span>
          <span className="info-value">{c.tema || '-'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Modelo</span>
          <span className="info-value">{c.modelo || '-'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Prazo</span>
          <span className="info-value">{c.prazo || '-'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Valor</span>
          <span className="info-value price">{c.valor || '-'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Telefone</span>
          <span className="info-value"><IconPhone size={13} /> {formatClientId(c.telefone, '') || '-'}</span>
        </div>
        {extrasInfo}
      </div>

      <div className="action-bar">{renderActions()}</div>
    </div>
  )
}
