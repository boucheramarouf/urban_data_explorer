import React, { useState, useMemo } from 'react'

export default function SearchBar({ geojson, onSelectRue }) {
  const [query, setQuery]     = useState('')
  const [focused, setFocused] = useState(false)

  const results = useMemo(() => {
    if (!geojson || query.trim().length < 2) return []
    const q = query.toUpperCase().trim()
    return geojson.features
      .filter(f => f.properties.code_iris.includes(q))
      .slice(0, 8)
      .map(f => f.properties)
  }, [query, geojson])

  const handleSelect = (rue) => {
    onSelectRue(rue)
    setQuery(rue.nom_voie)
    setFocused(false)
  }

  return (
    <div style={{ position: 'relative', marginBottom: 16 }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        background: '#1a1d27',
        border: `1px solid ${focused ? '#6c7dff' : '#2e3348'}`,
        borderRadius: 8,
        padding: '8px 12px',
        transition: 'border-color 0.2s',
      }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8b92b8" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          placeholder="Rechercher une rue..."
          style={{
            background: 'none',
            border: 'none',
            outline: 'none',
            color: '#f0f2ff',
            fontSize: 13,
            width: '100%',
          }}
        />
        {query && (
          <button onClick={() => setQuery('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#555e80', fontSize: 16, lineHeight: 1 }}>×</button>
        )}
      </div>

      {/* Dropdown résultats */}
      {focused && results.length > 0 && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          background: '#1a1d27',
          border: '1px solid #2e3348',
          borderTop: 'none',
          borderRadius: '0 0 8px 8px',
          zIndex: 100,
          maxHeight: 240,
          overflowY: 'auto',
        }}>
          {results.map((rue, i) => (
            <div
              key={i}
              onMouseDown={() => handleSelect(rue)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #2e3348',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#21253a'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <p style={{ fontSize: 12, fontWeight: 500, color: '#f0f2ff' }}>{rue.nom_voie}</p>
              <p style={{ fontSize: 11, color: '#8b92b8' }}>{rue.code_postal} · Score {rue.itr_score}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}