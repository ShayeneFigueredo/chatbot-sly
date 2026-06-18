import ClientCard from './ClientCard'

export default function ClientList({ clients, onAction }) {
  if (!clients || clients.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">✨</div>
        <div className="empty-text">Nenhum cliente aqui</div>
        <div className="empty-sub">Tudo em ordem!</div>
      </div>
    )
  }

  return (
    <div className="client-list">
      {clients.map((c) => (
        <ClientCard key={c.telefone} client={c} onAction={onAction} />
      ))}
    </div>
  )
}
