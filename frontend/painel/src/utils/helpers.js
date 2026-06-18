export function badgeClass(sit) {
  if (sit === 'Feito' || sit === 'Pago (Site)') return 'badge-success'
  if (sit === 'Em andamento') return 'badge-warning'
  if (sit === 'Cancelado') return 'badge-danger'
  if (sit === 'Novo') return 'badge-info'
  return 'badge-purple'
}

export function pgClass(pg) {
  if (pg === 'Pago') return 'badge-success'
  if (pg === '50% pago') return 'badge-warning'
  return 'badge-purple'
}

export function rowClass(sit) {
  if (sit === 'Feito' || sit === 'Pago (Site)') return 'row-feito'
  if (sit === 'Em andamento') return 'row-andamento'
  if (sit === 'Cancelado') return 'row-cancelado'
  if (sit === 'Novo') return 'row-novo'
  return ''
}

export function cardBorderClass(sit) {
  if (sit === 'Feito' || sit === 'Pago (Site)') return 'feito'
  if (sit === 'Em andamento') return 'andamento'
  if (sit === 'Cancelado') return 'cancelado'
  if (sit === 'Novo') return 'novo'
  return ''
}

export function statusBadgeClass(cls) {
  const map = {
    'status-ativo': 'badge-info',
    'status-pagamento': 'badge-warning',
    'status-humano': 'badge-danger',
    'status-aguardando-humano': 'badge-pink',
    'status-confirmado': 'badge-cyan',
    'status-pix': 'badge-warning',
    'status-shay': 'badge-info',
    'status-shay-assumiu': 'badge-purple',
  }
  return map[cls] || 'badge-info'
}

export function esc(s) {
  return (s || '').replace(/"/g, '&quot;').replace(/</g, '&lt;')
}

export function sel(id, opts, val) {
  return `<select id="${id}" class="form-select" style="width:100%">${opts.map(o => `<option ${o.trim() === String(val).trim() ? 'selected' : ''}>${o.trim()}</option>`).join('')}</select>`
}

export function formatCurrency(val) {
  if (val == null) return 'R$ 0,00'
  return 'R$ ' + Number(val).toFixed(2).replace('.', ',')
}

export function formatPhone(tel) {
  // Format: 5538997507651 -> (38) 99750-7651
  const cleaned = (tel || '').replace(/\D/g, '')
  if (cleaned.length >= 11) {
    const ddd = cleaned.slice(-11, -9)
    const p1 = cleaned.slice(-9, -4)
    const p2 = cleaned.slice(-4)
    return `(${ddd}) ${p1}-${p2}`
  }
  return tel
}
