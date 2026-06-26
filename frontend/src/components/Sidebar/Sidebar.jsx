import React, { useState } from 'react'
import SearchBar from './SearchBar.jsx'
import Filters from './Filters.jsx'
import FeatureDetail from './RueDetail.jsx'
import StatsPanel from '../Stats/StatsPanel.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const TAB = ({ label, active, onClick }) => (
  <button onClick={onClick} style={{
    flex: 1, background: 'none', border: 'none',
    borderBottom: `2px solid ${active ? 'var(--accent)' : 'transparent'}`,
    color: active ? 'var(--accent)' : 'var(--text-2)',
    fontSize: 12, fontWeight: active ? 600 : 400,
    padding: '10px 0', cursor: 'pointer', transition: 'all 0.2s',
  }}>{label}</button>
)

const IndicatorBtn = ({ label, active, onClick }) => (
  <button onClick={onClick} style={{
    flex: 1, padding: '6px 0', fontSize: 11, fontWeight: active ? 700 : 400,
    background: active ? 'rgba(29,78,107,0.10)' : 'var(--bg)',
    color: active ? 'var(--accent)' : 'var(--text-2)',
    border: `1px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
    borderRadius: 6, cursor: 'pointer', transition: 'all 0.2s',
  }}>{label}</button>
)

const INDICATOR_BUTTONS = [
  { key: 'IMQ',  label: 'IMQ' },
  { key: 'ITR',  label: 'ITR' },
  { key: 'SVP',  label: 'SVP' },
  { key: 'IAML', label: 'IAML' },
]

export default function Sidebar({
  indicator,
  onIndicatorChange,
  geojson,
  stats,
  filters,
  onFiltersChange,
  selectedFeature,
  onSelectFeature,
}) {
  const [tab, setTab] = useState('filtres')
  const cfg = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'
  const count = geojson?.features?.length || 0

  return (
    <div style={{
      width: 'var(--sidebar-width)', height: '100%',
      background: 'var(--bg-card)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', flexShrink: 0,
    }}>
      {/* Titre */}
      <div style={{ padding: '16px 20px 12px', borderBottom: '1px solid var(--border)' }}>
        <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.02em' }}>
          Urban <span style={{ color: 'var(--accent)' }}>Data Explorer</span>
        </p>
        <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{cfg.subtitle}</p>

        {/* Switcher IMQ / ITR / SVP / IAML */}
        <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
          {INDICATOR_BUTTONS.map(item => (
            <IndicatorBtn
              key={item.key}
              label={item.label}
              active={indicator === item.key}
              onClick={() => onIndicatorChange(item.key)}
            />
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 20px' }}>
        <TAB label="Filtres"      active={tab === 'filtres'} onClick={() => setTab('filtres')} />
        <TAB label="Statistiques" active={tab === 'stats'}   onClick={() => setTab('stats')} />
      </div>

      {/* Contenu */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {tab === 'filtres' && (
          <>
            <SearchBar indicator={indicator} geojson={geojson} onSelectFeature={onSelectFeature} />
            <Filters indicator={indicator} filters={filters} onChange={onFiltersChange} />

            {geojson && (
              <div style={{
                background: 'var(--bg)', borderRadius: 7, padding: '8px 12px', marginTop: 8,
                border: '1px solid var(--border)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: 11, color: 'var(--text-2)' }}>
                  {isIMQ ? 'IRIS affichés' : 'Rues affichées'}
                </span>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent)' }}>{count}</span>
              </div>
            )}

            {selectedFeature && (
              <FeatureDetail indicator={indicator} feature={selectedFeature} onClose={() => onSelectFeature(null)} />
            )}
          </>
        )}

        {tab === 'stats' && <StatsPanel indicator={indicator} stats={stats} />}
      </div>

      <div style={{ padding: '10px 20px', borderTop: '1px solid var(--border)' }}>
        <p style={{ fontSize: 10, color: 'var(--text-3)', textAlign: 'center' }}>
          {isIMQ
            ? 'Sources : DVF · SIRENE · Filosofi INSEE · LOVAC · IGN'
            : 'Sources : DVF · INSEE · Open Data Paris · IGN · OSM · 2021'}
        </p>
      </div>
    </div>
  )
}
