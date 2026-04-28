import React, { useState } from 'react'
import SearchBar from './SearchBar.jsx'
import Filters from './Filters.jsx'
import RueDetail from './RueDetail.jsx'
import StatsPanel from '../Stats/StatsPanel.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const TAB = ({ label, active, onClick }) => (
  <button
    onClick={onClick}
    style={{
      flex: 1,
      background: 'none',
      border: 'none',
      borderBottom: `2px solid ${active ? '#6c7dff' : 'transparent'}`,
      color: active ? '#f0f2ff' : '#8b92b8',
      fontSize: 12,
      fontWeight: active ? 600 : 400,
      padding: '10px 0',
      cursor: 'pointer',
      transition: 'all 0.2s',
    }}
  >
    {label}
  </button>
)

const INDICATOR_BUTTONS = [
  { key: 'itr', label: 'ITR' },
  { key: 'svp', label: 'SVP' },
  { key: 'iaml', label: 'IAML' },
]

export default function Sidebar({
  indicator,
  onIndicatorChange,
  geojson,
  stats,
  filters,
  onFiltersChange,
  selectedRue,
  onSelectRue,
}) {
  const [tab, setTab] = useState('filtres')
  const cfg = getIndicatorConfig(indicator)

  return (
    <div
      style={{
        width: 'var(--sidebar-width)',
        height: '100%',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid #2e3348' }}>
        <p style={{ fontSize: 16, fontWeight: 700, color: '#f0f2ff', letterSpacing: '-0.02em' }}>
          {cfg.title.split(' ')[0]} <span style={{ color: '#6c7dff' }}>Paris</span>
        </p>
        <p style={{ fontSize: 11, color: '#555e80', marginTop: 2 }}>{cfg.subtitle}</p>

        <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
          {INDICATOR_BUTTONS.map((item) => (
            <button
              key={item.key}
              onClick={() => onIndicatorChange(item.key)}
              style={{
                flex: 1,
                border: '1px solid #2e3348',
                borderRadius: 6,
                background: indicator === item.key ? '#6c7dff22' : '#1a1d27',
                color: indicator === item.key ? '#cfd6ff' : '#8b92b8',
                fontSize: 11,
                fontWeight: 600,
                padding: '6px 8px',
                cursor: 'pointer',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid #2e3348', padding: '0 20px' }}>
        <TAB label="Filtres" active={tab === 'filtres'} onClick={() => setTab('filtres')} />
        <TAB label="Statistiques" active={tab === 'stats'} onClick={() => setTab('stats')} />
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {tab === 'filtres' && (
          <>
            <SearchBar indicator={indicator} geojson={geojson} onSelectRue={onSelectRue} />
            <Filters indicator={indicator} filters={filters} onChange={onFiltersChange} />

            {geojson && (
              <div
                style={{
                  background: '#1a1d27',
                  borderRadius: 7,
                  padding: '8px 12px',
                  marginTop: 8,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span style={{ fontSize: 11, color: '#8b92b8' }}>Rues affichées</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#6c7dff' }}>
                  {geojson.features?.length || 0}
                </span>
              </div>
            )}

            {selectedRue && <RueDetail indicator={indicator} rue={selectedRue} onClose={() => onSelectRue(null)} />}
          </>
        )}

        {tab === 'stats' && <StatsPanel indicator={indicator} stats={stats} />}
      </div>

      <div style={{ padding: '10px 20px', borderTop: '1px solid #2e3348' }}>
        <p style={{ fontSize: 10, color: '#555e80', textAlign: 'center' }}>
          Sources : DVF · INSEE · Open Data Paris · IGN · OSM · 2021
        </p>
      </div>
    </div>
  )
}
