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
  // Formata numero brasileiro: 5538997507651 -> (38) 99750-7651
  const cleaned = (tel || '').replace(/\D/g, '')
  // Detecta padrao BR: 55XXXXXXXXXXX (13 digitos) ou 55XXXXXXXXXX (12 digitos)
  if (cleaned.startsWith('55') && cleaned.length >= 12 && cleaned.length <= 13) {
    const ddd = cleaned.substring(2, 4)
    const p1 = cleaned.substring(4, cleaned.length - 4)
    const p2 = cleaned.substring(cleaned.length - 4)
    return `(${ddd}) ${p1}-${p2}`
  }
  // Pode ser 0XX... (11 digitos)
  if (cleaned.startsWith('0') && cleaned.length >= 11) {
    const ddd = cleaned.substring(1, 3)
    const p1 = cleaned.substring(3, cleaned.length - 4)
    const p2 = cleaned.substring(cleaned.length - 4)
    return `(${ddd}) ${p1}-${p2}`
  }
  return tel
}

export function isLID(tel) {
  const cleaned = (tel || '').replace(/\D/g, '')
  // Se nao parece telefone brasileiro, provavelmente é LID
  return !(cleaned.startsWith('55') && cleaned.length >= 12 && cleaned.length <= 13)
}
