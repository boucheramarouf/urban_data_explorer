import React, { useEffect, useRef, useState, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import Tooltip from './Tooltip.jsx'
import Legend from './Legend.jsx'

const MAPTILER_KEY = 'get_your_own_OpIi9ZULNHzrESv6T2vL'

export default function MapView({ geojson, selectedRue, onSelectRue }) {
  const mapContainer = useRef(null)
  const map          = useRef(null)
  const isLoaded     = useRef(false)
  const pendingData  = useRef(null)
  const [tooltip, setTooltip] = useState({ feature: null, x: 0, y: 0 })

  // ── Init carte (une seule fois)
  useEffect(() => {
    if (map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: `https://api.maptiler.com/maps/dataviz-dark/style.json?key=${MAPTILER_KEY}`,
      center: [2.3488, 48.8534],
      zoom: 12,
      minZoom: 11,
      maxZoom: 18,
    })

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }))

    map.current.on('load', () => {
      // Source vide
      map.current.addSource('rues', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      // Couche points
      map.current.addLayer({
        id: 'rues-points',
        type: 'circle',
        source: 'rues',
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'nb_transactions'],
            3, 4, 50, 7, 200, 11,
          ],
          'circle-color': [
            'interpolate', ['linear'], ['get', 'itr_score'],
            0,   '#22c55e',
            20,  '#22c55e',
            40,  '#84cc16',
            60,  '#eab308',
            80,  '#f97316',
            100, '#ef4444',
          ],
          'circle-opacity': 0.85,
          'circle-stroke-width': 1,
          'circle-stroke-color': 'rgba(255,255,255,0.15)',
        },
      })

      // Couche highlight
      map.current.addLayer({
        id: 'rues-highlight',
        type: 'circle',
        source: 'rues',
        filter: ['==', 'nom_voie', ''],
        paint: {
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'nb_transactions'],
            3, 7, 50, 11, 200, 16,
          ],
          'circle-color': '#ffffff',
          'circle-opacity': 0.2,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-opacity': 0.9,
        },
      })

      // Survol
      map.current.on('mousemove', 'rues-points', (e) => {
        map.current.getCanvas().style.cursor = 'pointer'
        const feature = e.features[0]
        map.current.setFilter('rues-highlight', ['==', 'nom_voie', feature.properties.nom_voie])
        setTooltip({ feature, x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })

      map.current.on('mouseleave', 'rues-points', () => {
        map.current.getCanvas().style.cursor = ''
        map.current.setFilter('rues-highlight', ['==', 'nom_voie', ''])
        setTooltip({ feature: null, x: 0, y: 0 })
      })

      // Clic
      map.current.on('click', 'rues-points', (e) => {
        onSelectRue(e.features[0].properties)
      })

      // Marquer comme chargé + injecter données en attente
      isLoaded.current = true
      if (pendingData.current) {
        map.current.getSource('rues').setData(pendingData.current)
        pendingData.current = null
      }
    })

    return () => {
      isLoaded.current = false
      map.current?.remove()
      map.current = null
    }
  }, [])

  // ── Mise à jour GeoJSON (sécurisée)
  useEffect(() => {
    if (!geojson) return

    if (isLoaded.current && map.current) {
      // Carte prête → injection directe
      const source = map.current.getSource('rues')
      if (source) source.setData(geojson)
    } else {
      // Carte pas encore prête → on met en attente
      pendingData.current = geojson
    }
  }, [geojson])

  // ── Zoom sur rue sélectionnée
  useEffect(() => {
    if (!map.current || !selectedRue || !isLoaded.current) return
    map.current.flyTo({
      center: [selectedRue.lon_centre, selectedRue.lat_centre],
      zoom: 15,
      duration: 800,
    })
    map.current.setFilter('rues-highlight', ['==', 'nom_voie', selectedRue.nom_voie])
  }, [selectedRue])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      <Tooltip feature={tooltip.feature} x={tooltip.x} y={tooltip.y} />
      <Legend />
    </div>
  )
}