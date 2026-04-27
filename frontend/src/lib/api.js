const explicitBase = import.meta.env.VITE_API_BASE?.replace(/\/$/, '')

// En dev Vite, on passe par le proxy `/api` pour eviter les problemes
// de localhost/127.0.0.1/Docker. Un override reste possible via VITE_API_BASE.
const defaultBase = import.meta.env.DEV ? '/api' : 'http://127.0.0.1:8000'

export const API_BASE = explicitBase || defaultBase
export const API_PREFIX = (import.meta.env.VITE_API_PREFIX || '/svp').replace(/\/$/, '')

export function buildApiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE}${API_PREFIX}${normalizedPath}`
}
