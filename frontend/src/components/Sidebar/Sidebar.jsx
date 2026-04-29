import React, { useState, useMemo } from 'react'
import SearchBar from './SearchBar.jsx'
import Filters from './Filters.jsx'
import StatsPanel from '../Stats/StatsPanel.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const INDICATOR_BUTTONS = [
  { key: 'IMQ',  label: 'IMQ',  color: '#d97706' },
  { key: 'ITR',  label: 'ITR',  color: '#dc2626' },
  { key: 'SVP',  label: 'SVP',  color: '#16a34a' },
  { key: 'IAML', label: 'IAML', color: '#2563eb' },
]

const LABEL_COLOR = {
  'Stable': '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626',
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
}

function ScoreList({ indicator, geojson, onSelect }) {
  const cfg    = getIndicatorConfig(indicator)
  const isIMQ  = indicator === 'IMQ'
  const nameField  = isIMQ ? 'iris_nom'  : 'nom_voie'
  const scoreField = isIMQ ? 'score_imq_100' : cfg.scoreField
  const labelField = isIMQ ? 'interpretation' : cfg.labelField

  const items = useMemo(() => {
    if (!geojson?.features) return []
    return geojson.features
      .map(f => f.properties)
      .filter(p => p[scoreField] != null)
      .sort((a, b) => b[scoreField] - a[scoreField])
      .slice(0, 60)
  }, [geojson, scoreField])

  if (!items.length) return null

  return (
    <div>
      <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, marginTop: 16 }}>
        Résultats — {geojson?.features?.length || 0}
      </p>
      <div>
        {items.map((p, i) => {
          const score = p[scoreField]
          const label = p[labelField]
          const color = LABEL_COLOR[label] || '#9ca3af'
          return (
            <button
              key={i}
              onClick={() => onSelect(p)}
              style={{
                width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 10px', borderRadius: 7, marginBottom: 2,
                transition: 'background 0.12s', textAlign: 'left',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
              <span style={{ flex: 1, fontSize: 12, color: 'var(--text)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {p[nameField]}
              </span>
              <span style={{ fontSize: 12, fontWeight: 700, color, flexShrink: 0 }}>{Number(score).toFixed(1)}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default function Sidebar({ indicator, onIndicatorChange, geojson, stats, filters, onFiltersChange, onSelectFeature }) {
  const [tab, setTab] = useState('filtres')
  const cfg   = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'

  return (
    <div style={{
      width: 'var(--sidebar-w)', height: '100%', flexShrink: 0,
      background: 'var(--bg-card)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      {/* Header — indicator switcher */}
      <div style={{ padding: '14px 16px 12px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <p style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10, fontWeight: 500 }}>{cfg.subtitle}</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 4 }}>
          {INDICATOR_BUTTONS.map(btn => (
            <button
              key={btn.key}
              onClick={() => onIndicatorChange(btn.key)}
              style={{
                padding: '6px 4px', borderRadius: 6, border: 'none', cursor: 'pointer',
                fontSize: 11, fontWeight: 700, letterSpacing: '0.02em',
                transition: 'all 0.15s',
                background: indicator === btn.key ? btn.color : 'var(--bg)',
                color: indicator === btn.key ? '#fff' : 'var(--text-2)',
                boxShadow: indicator === btn.key ? `0 2px 8px ${btn.color}40` : 'none',
              }}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        {[{ key: 'filtres', label: 'Filtres' }, { key: 'stats', label: 'Statistiques' }].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              flex: 1, background: 'none', border: 'none', cursor: 'pointer',
              padding: '10px 0', fontSize: 12, fontWeight: tab === t.key ? 600 : 400,
              color: tab === t.key ? 'var(--text)' : 'var(--text-3)',
              borderBottom: `2px solid ${tab === t.key ? 'var(--text)' : 'transparent'}`,
              transition: 'all 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px' }}>
        {tab === 'filtres' && (
          <>
            <SearchBar indicator={indicator} geojson={geojson} onSelectFeature={onSelectFeature} />
            <Filters indicator={indicator} filters={filters} onChange={onFiltersChange} />
            <ScoreList indicator={indicator} geojson={geojson} onSelect={onSelectFeature} />
          </>
        )}
        {tab === 'stats' && <StatsPanel indicator={indicator} stats={stats} />}
      </div>

      {/* Footer */}
      <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <p style={{ fontSize: 10, color: 'var(--text-3)', textAlign: 'center', lineHeight: 1.5 }}>
          {isIMQ
            ? 'DVF · SIRENE · Filosofi · LOVAC · IGN'
            : 'DVF · INSEE · Open Data Paris · IGN · OSM'}
        </p>
      </div>
    </div>
  )
}
