import React, { useState, useCallback } from 'react'
import Navbar from './components/Navbar.jsx'
import LandingPage from './components/LandingPage.jsx'
import ComparateurPage from './components/ComparateurPage.jsx'
import MethodologiePage from './components/MethodologiePage.jsx'
import IndicateursPage from './components/IndicateursPage.jsx'
import SourcesPage from './components/SourcesPage.jsx'
import MapView from './components/Map/MapView.jsx'
import Sidebar from './components/Sidebar/Sidebar.jsx'
import RightPanel from './components/Sidebar/RightPanel.jsx'
import { useGeoJSON } from './hooks/useGeoJSON.js'
import { useStats } from './hooks/useStats.js'

// ── Cartography page ──────────────────────────────────────────
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

      {/* Left sidebar */}
      <Sidebar
        indicator={indicator}
        onIndicatorChange={handleIndicatorChange}
        geojson={geojson}
        stats={stats}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onSelectFeature={handleSelectFeature}
      />

      {/* Map */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {geoLoading && (
          <div style={{
            position: 'absolute', inset: 0, zIndex: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(239,233,223,0.75)', backdropFilter: 'blur(4px)',
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                width: 32, height: 32, border: '2.5px solid var(--border)', borderTop: '2.5px solid var(--text)',
                borderRadius: '50%', animation: 'spin 0.7s linear infinite', margin: '0 auto 12px',
              }} />
              <p style={{ color: 'var(--text-2)', fontSize: 13 }}>Chargement…</p>
            </div>
          </div>
        )}

        {geoError && !geoLoading && (
          <div style={{ position: 'absolute', inset: 0, zIndex: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(239,233,223,0.9)' }}>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, padding: '28px 36px', textAlign: 'center', maxWidth: 360, boxShadow: 'var(--shadow-md)' }}>
              <p style={{ fontSize: 28, marginBottom: 12 }}>⚠️</p>
              <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 8 }}>API introuvable</p>
              <p style={{ fontSize: 12, color: 'var(--text-2)', marginBottom: 16 }}>Le serveur FastAPI doit tourner sur le port 8000</p>
              <code style={{ display: 'block', background: 'var(--bg)', borderRadius: 6, padding: '8px 12px', fontSize: 11, color: 'var(--accent)', border: '1px solid var(--border)' }}>
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

      {/* Right panel — feature detail */}
      <RightPanel
        indicator={indicator}
        feature={selectedFeature}
        stats={stats}
        onClose={() => setSelectedFeature(null)}
      />

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

// ── Root ──────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState('landing')

  return (
    <>
      <Navbar page={page} onNavigate={setPage} />
      {page === 'landing'       && <LandingPage onNavigate={setPage} />}
      {page === 'carte'         && <CartographiePage />}
      {page === 'comparateur'   && <ComparateurPage />}
      {page === 'indicateurs'   && <IndicateursPage />}
      {page === 'methodologie'  && <MethodologiePage />}
      {page === 'sources'       && <SourcesPage />}
    </>
  )
}
