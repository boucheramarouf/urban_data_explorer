import React, { useState, useMemo } from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

export default function SearchBar({ indicator, geojson, onSelectFeature }) {
  const [query, setQuery]     = useState('')
  const [focused, setFocused] = useState(false)
  const cfg = getIndicatorConfig(indicator)
  const scoreField = cfg.scoreField

  const isIMQ = indicator === 'IMQ'

  const results = useMemo(() => {
    if (!geojson || query.trim().length < 2) return []
    const q = query.toUpperCase().trim()
    const field = isIMQ ? 'iris_nom' : 'nom_voie'
    return geojson.features
      .filter(f => (f.properties[field] || '').toUpperCase().includes(q))
      .slice(0, 8)
      .map(f => f.properties)
  }, [query, geojson, indicator])

  const handleSelect = (item) => {
    onSelectFeature(item)
    setQuery(isIMQ ? item.iris_nom : item.nom_voie)
    setFocused(false)
  }

  return (
    <div style={{ position: 'relative', marginBottom: 16 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        background: 'var(--bg)',
        border: `1px solid ${focused ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 8, padding: '8px 12px', transition: 'border-color 0.2s',
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          placeholder={isIMQ ? 'Rechercher un IRIS…' : 'Rechercher une rue…'}
          style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--text)', fontSize: 13, width: '100%' }}
        />
        {query && (
          <button onClick={() => setQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', fontSize: 16, lineHeight: 1 }}>×</button>
        )}
      </div>

      {focused && results.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0,
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderTop: 'none',
          borderRadius: '0 0 8px 8px', zIndex: 100, maxHeight: 240, overflowY: 'auto',
          boxShadow: 'var(--shadow-md)',
        }}>
          {results.map((item, i) => (
            <div key={i} onMouseDown={() => handleSelect(item)}
              style={{ padding: '8px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <p style={{ fontSize: 12, fontWeight: 500, color: 'var(--text)' }}>
                {isIMQ ? item.iris_nom : item.nom_voie}
              </p>
              <p style={{ fontSize: 11, color: 'var(--text-2)' }}>
                {isIMQ
                  ? `arr. ${item.arrondissement} · IMQ ${item.score_imq_100}/100`
                  : `${item.code_postal} · Score ${item[scoreField]}`}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
