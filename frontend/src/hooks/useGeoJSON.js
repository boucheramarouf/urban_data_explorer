import { useState, useEffect } from 'react'

const API = '/api'

export function useGeoJSON(indicator = 'IMQ', filters = {}) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const prefix = indicator === 'ITR' ? 'itr' : 'imq'

  useEffect(() => {
    setLoading(true)
    setData(null)
    const params = new URLSearchParams()

    if (indicator === 'IMQ') {
      if (filters.arrondissement) params.set('arrondissement', filters.arrondissement)
      if (filters.interpretation) params.set('interpretation', filters.interpretation)
      if (filters.score_min != null) params.set('score_min', filters.score_min)
      if (filters.score_max != null) params.set('score_max', filters.score_max)
    } else {
      if (filters.arrondissement) params.set('arrondissement', filters.arrondissement)
      if (filters.label)          params.set('label', filters.label)
      if (filters.score_min != null) params.set('score_min', filters.score_min)
      if (filters.score_max != null) params.set('score_max', filters.score_max)
    }

    const url = `${API}/${prefix}/geojson${params.toString() ? '?' + params.toString() : ''}`

    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(json => { setData(json); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [indicator, filters.arrondissement, filters.interpretation, filters.label, filters.score_min, filters.score_max])

  return { data, loading, error }
}
