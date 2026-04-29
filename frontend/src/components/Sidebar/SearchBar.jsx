import React, { useState, useMemo } from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

export default function SearchBar({ indicator, geojson, onSelectFeature }) {
  const [query, setQuery]     = useState('')
  const [focused, setFocused] = useState(false)
  const cfg    = getIndicatorConfig(indicator)
  const isIMQ  = indicator === 'IMQ'
  const nameField  = isIMQ ? 'iris_nom' : 'nom_voie'
  const scoreField = isIMQ ? 'score_imq_100' : cfg.scoreField

  const results = useMemo(() => {
    if (!geojson || query.trim().length < 2) return []
    const q = query.toUpperCase().trim()
    return geojson.features
      .filter(f => (f.properties[nameField] || '').toUpperCase().includes(q))
      .slice(0, 8)
      .map(f => f.properties)
  }, [query, geojson, indicator])

  const handleSelect = (item) => {
    onSelectFeature(item)
    setQuery(item[nameField] || '')
    setFocused(false)
  }

  return (
    <div style={{ position: 'relative', marginBottom: 14 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        background: 'var(--bg)', border: `1px solid ${focused ? 'var(--text)' : 'var(--border)'}`,
        borderRadius: 8, padding: '8px 12px', transition: 'border-color 0.15s',
      }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" strokeWidth="2.5">
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
          <button onClick={() => setQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', fontSize: 16, lineHeight: 1, padding: 0 }}>×</button>
        )}
      </div>

      {focused && results.length > 0 && (
        <div style={{
          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
          background: 'var(--bg-card)', border: '1px solid var(--border)', borderTop: 'none',
          borderRadius: '0 0 8px 8px', boxShadow: 'var(--shadow-md)', maxHeight: 240, overflowY: 'auto',
        }}>
          {results.map((item, i) => (
            <div
              key={i}
              onMouseDown={() => handleSelect(item)}
              style={{ padding: '9px 12px', cursor: 'pointer', borderBottom: '1px solid var(--border-light)', transition: 'background 0.1s' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{item[nameField]}</p>
              <p style={{ fontSize: 11, color: 'var(--text-3)' }}>
                arr. {item.arrondissement} · Score {Number(item[scoreField] || 0).toFixed(1)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
