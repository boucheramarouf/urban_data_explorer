import { useState, useEffect } from 'react'
import { getIndicatorConfig } from '../utils/indicatorConfig.js'

const API = '/api'

export function useGeoJSON(indicator = 'IMQ', filters = {}) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const cfg = getIndicatorConfig(indicator)
  const labelField = cfg.labelField
  const scoreField = cfg.scoreField

  useEffect(() => {
    setLoading(true)
    setData(null)
    setError(null)

    const params = new URLSearchParams()

    if (indicator === 'IMQ') {
      if (filters.arrondissement) params.set('arrondissement', filters.arrondissement)
      if (filters.interpretation) params.set('interpretation', filters.interpretation)
      if (filters.score_min != null) params.set('score_min', filters.score_min)
      if (filters.score_max != null) params.set('score_max', filters.score_max)
    } else {
      if (filters.arrondissement) params.set('arrondissement', filters.arrondissement)
      if (filters[labelField]) params.set('label', filters[labelField])
      if (filters[`${scoreField}_min`] != null) params.set('score_min', filters[`${scoreField}_min`])
      if (filters[`${scoreField}_max`] != null) params.set('score_max', filters[`${scoreField}_max`])
      if (indicator === 'SVP' && filters.has_commerce != null) params.set('has_commerce', filters.has_commerce)
    }

    const url = `${API}${cfg.geojsonPath}${params.toString() ? '?' + params.toString() : ''}`

    fetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(json => { setData(json); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [
    indicator,
    filters.arrondissement,
    filters.interpretation,
    filters[labelField],
    filters[`${scoreField}_min`],
    filters[`${scoreField}_max`],
    filters.has_commerce,
  ])

  return { data, loading, error }
}
