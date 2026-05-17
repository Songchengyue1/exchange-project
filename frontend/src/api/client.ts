const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

function getStoredToken(): string | null {
  if (typeof localStorage === 'undefined') return null
  return localStorage.getItem('access_token')
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text()
  if (!text) return undefined as T
  return JSON.parse(text) as T
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const auth = init.auth !== false
  if (auth) {
    const token = getStoredToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  const hadAuth = !!headers.get('Authorization')

  if (res.status === 401 && hadAuth) {
    localStorage.removeItem('access_token')
    const path = window.location.pathname
    const onAuthPage = path.endsWith('/login') || path.endsWith('/register')
    if (!onAuthPage) {
      const next = encodeURIComponent(window.location.pathname + window.location.search)
      window.location.assign(`/login?redirect=${next}`)
    }
    throw new Error('登录已失效')
  }

  if (!res.ok) {
    let detail: unknown = res.statusText
    try {
      detail = (await res.json()) as { detail?: unknown }
    } catch {
      /* ignore */
    }
    const msg =
      typeof detail === 'object' && detail !== null && 'detail' in detail
        ? (detail as { detail: unknown }).detail
        : detail
    const text =
      typeof msg === 'string' ? msg : Array.isArray(msg) ? JSON.stringify(msg) : JSON.stringify(msg)
    throw new Error(text)
  }

  if (res.status === 204) return undefined as T
  return parseJson<T>(res)
}
