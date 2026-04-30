import React, { useState, useCallback } from 'react'
import ComparateurPage from './components/ComparateurPage.jsx'
import MethodologiePage from './components/MethodologiePage.jsx'
import IndicateursPage from './components/IndicateursPage.jsx'
import SourcesPage from './components/SourcesPage.jsx'
import MapView from './components/Map/MapView.jsx'
import Sidebar from './components/Sidebar/Sidebar.jsx'
import { useGeoJSON } from './hooks/useGeoJSON.js'
import { useStats } from './hooks/useStats.js'

const NAV_LINKS = [
  { key: 'carte',        label: 'Carte' },
  { key: 'comparateur',  label: 'Comparateur' },
  { key: 'indicateurs',  label: 'Indicateurs' },
  { key: 'methodologie', label: 'Méthodologie' },
  { key: 'sources',      label: 'Sources' },
]

function Navbar({ page, onNavigate }) {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      height: 'var(--nav-h)', background: 'var(--bg-card)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', padding: '0 24px', gap: 32,
    }}>
      <span
        onClick={() => onNavigate('carte')}
        style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 19, fontWeight: 700, color: 'var(--text)', cursor: 'pointer', userSelect: 'none', flexShrink: 0 }}
      >
        Urban Data Explorer
      </span>
      <div style={{ display: 'flex', gap: 4, flex: 1 }}>
        {NAV_LINKS.map(l => (
          <button
            key={l.key}
            onClick={() => onNavigate(l.key)}
            style={{
              background: page === l.key ? 'var(--bg-hover)' : 'transparent',
              border: 'none', cursor: 'pointer',
              padding: '6px 14px', borderRadius: 6, fontSize: 13,
              fontWeight: page === l.key ? 600 : 400,
              color: page === l.key ? 'var(--text)' : 'var(--text-2)',
              transition: 'all 0.15s',
            }}
          >{l.label}</button>
        ))}
      </div>
    </nav>
  )
}

function CartographiePage() {
  const [indicator, setIndicator]             = useState('IMQ')
  const [filters, setFilters]                 = useState({})
  const [selectedFeature, setSelectedFeature] = useState(null)

  const { data: geojson, loading: geoLoading, error: geoError } = useGeoJSON(indicator, filters)
  const { data: stats } = useStats(indicator)

  const handleSelectFeature   = useCallback((f) => setSelectedFeature(f), [])
  const handleFiltersChange   = useCallback((f) => { setFilters(f); setSelectedFeature(null) }, [])
  const handleIndicatorChange = useCallback((ind) => { setIndicator(ind); setFilters({}); setSelectedFeature(null) }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', paddingTop: 'var(--nav-h)', overflow: 'hidden' }}>
      <Sidebar
        indicator={indicator}
        onIndicatorChange={handleIndicatorChange}
        geojson={geojson}
        stats={stats}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        selectedFeature={selectedFeature}
        onSelectFeature={handleSelectFeature}
      />

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {geoLoading && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(15,17,23,0.7)', backdropFilter: 'blur(4px)',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: 36, height: 36,
                border: '3px solid #2e3348', borderTop: '3px solid #6c7dff',
                borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px',
              }} />
              <p style={{ color: '#8b92b8', fontSize: 13 }}>Chargement des données…</p>
            </div>
          </div>
        )}

        {geoError && !geoLoading && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(15,17,23,0.9)' }}>
            <div style={{ background: '#21253a', border: '1px solid #ef444444', borderRadius: 12, padding: '24px 32px', textAlign: 'center', maxWidth: 360 }}>
              <p style={{ fontSize: 32, marginBottom: 12 }}>⚠️</p>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#f0f2ff', marginBottom: 8 }}>Impossible de contacter l&apos;API</p>
              <p style={{ fontSize: 12, color: '#8b92b8', marginBottom: 16 }}>Assurez-vous que le serveur FastAPI tourne sur le port 8000</p>
              <code style={{ display: 'block', background: '#1a1d27', borderRadius: 6, padding: '8px 12px', fontSize: 11, color: '#6c7dff' }}>
                uvicorn api.main:app --port 8000
              </code>
            </div>
          </div>
        )}

        <MapView
          indicator={indicator}
          geojson={geojson}
          selectedFeature={selectedFeature}
          onSelectFeature={handleSelectFeature}
        />
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState('carte')

  return (
    <>
      <Navbar page={page} onNavigate={setPage} />
      {page === 'carte'         && <CartographiePage />}
      {page === 'comparateur'   && <ComparateurPage />}
      {page === 'indicateurs'   && <IndicateursPage />}
      {page === 'methodologie'  && <MethodologiePage />}
      {page === 'sources'       && <SourcesPage />}
    </>
  )
}
