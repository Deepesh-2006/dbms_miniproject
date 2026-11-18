const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
export type ApiList = { items: Record<string, unknown>[]; total: number; page: number; page_size: number }
export const token = () => (typeof window === 'undefined' ? null : localStorage.getItem('fleet_token'))
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...options.headers } })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Request failed') }
  return response.status === 204 ? (undefined as T) : response.json()
}
export async function login(username: string, password: string) { return api<{access_token:string; role:string}>('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }) }
