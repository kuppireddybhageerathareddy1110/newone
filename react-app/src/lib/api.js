const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!res.ok) {
    let detail = `HTTP ${res.status}`
    try {
      const body = await res.json()
      detail = body.error || body.detail || detail
    } catch {}
    throw new Error(detail)
  }

  return res.json()
}

export { API_BASE, request }
