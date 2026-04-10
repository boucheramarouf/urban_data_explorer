import { useState, useEffect } from 'react'

const API = '/api'

export function useGeoJSON(filters = {}) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filters.arrondissement) params.set('arrondissement', filters.arrondissement)
    if (filters.label)          params.set('label', filters.label)
    if (filters.score_min != null) params.set('score_min', filters.score_min)
    if (filters.score_max != null) params.set('score_max', filters.score_max)

    const url = `${API}/geojson${params.toString() ? '?' + params.toString() : ''}`

    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(json => { setData(json); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [filters.arrondissement, filters.label, filters.score_min, filters.score_max])

  return { data, loading, error }
}