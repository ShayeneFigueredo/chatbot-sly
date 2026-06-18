import { useCallback } from 'react'

export function useApi() {
  const api = useCallback(async (path, body) => {
    const res = await fetch(path, {
      method: body ? 'POST' : 'GET',
      credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const text = await res.text()
    try {
      return JSON.parse(text)
    } catch (e) {
      console.error('API parse error:', text.slice(0, 100))
      return {}
    }
  }, [])

  return api
}
