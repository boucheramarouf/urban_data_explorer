import { useState, useEffect } from 'react'
import { getIndicatorConfig } from '../utils/indicatorConfig.js'

const API = '/api'

export function useStats(indicator = 'itr') {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const cfg = getIndicatorConfig(indicator)

  useEffect(() => {
    fetch(`${API}${cfg.statsPath}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(json => { setData(json); setLoading(false) })
      .catch(e  => { setError(e.message); setLoading(false) })
  }, [indicator])

  return { data, loading, error }
}