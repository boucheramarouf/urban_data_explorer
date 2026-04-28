import React, { useState, useCallback } from 'react'
import MapView from './components/Map/MapView.jsx'
import Sidebar from './components/Sidebar/Sidebar.jsx'
import { useGeoJSON } from './hooks/useGeoJSON.js'
import { useStats } from './hooks/useStats.js'

export default function App() {
  const [indicator, setIndicator] = useState('itr')
  const [filters, setFilters] = useState({})
  const [selectedRue, setSelectedRue] = useState(null)

  const { data: geojson, loading: geoLoading, error: geoError } = useGeoJSON(filters, indicator)
  const { data: stats } = useStats(indicator)

  const handleSelectRue = useCallback((rue) => {
    setSelectedRue(rue)
  }, [])

  const handleFiltersChange = useCallback((newFilters) => {
    setFilters(newFilters)
    setSelectedRue(null)
  }, [])

  const handleIndicatorChange = useCallback((nextIndicator) => {
    setIndicator(nextIndicator)
    setFilters({})
    setSelectedRue(null)
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Sidebar
        indicator={indicator}
        onIndicatorChange={handleIndicatorChange}
        geojson={geojson}
        stats={stats}
        filters={filters}
        onFiltersChange={handleFiltersChange}
        selectedRue={selectedRue}
        onSelectRue={handleSelectRue}
      />

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {geoLoading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 50,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(15,17,23,0.7)',
              backdropFilter: 'blur(4px)',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  border: '3px solid #2e3348',
                  borderTop: '3px solid #6c7dff',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  margin: '0 auto 12px',
                }}
              />
              <p style={{ color: '#8b92b8', fontSize: 13 }}>Chargement des données…</p>
            </div>
          </div>
        )}

        {geoError && !geoLoading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 50,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(15,17,23,0.9)',
            }}
          >
            <div
              style={{
                background: '#21253a',
                border: '1px solid #ef444444',
                borderRadius: 12,
                padding: '24px 32px',
                textAlign: 'center',
                maxWidth: 360,
              }}
            >
              <p style={{ fontSize: 32, marginBottom: 12 }}>⚠️</p>
              <p style={{ fontSize: 14, fontWeight: 600, color: '#f0f2ff', marginBottom: 8 }}>
                Impossible de contacter l&apos;API
              </p>
              <p style={{ fontSize: 12, color: '#8b92b8', marginBottom: 16 }}>
                Assurez-vous que le serveur FastAPI tourne sur le port 8000
              </p>
              <code
                style={{
                  display: 'block',
                  background: '#1a1d27',
                  borderRadius: 6,
                  padding: '8px 12px',
                  fontSize: 11,
                  color: '#6c7dff',
                }}
              >
                uvicorn api.main:app --port 8000
              </code>
            </div>
          </div>
        )}

        <MapView
          indicator={indicator}
          geojson={geojson}
          selectedRue={selectedRue}
          onSelectRue={handleSelectRue}
        />
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
