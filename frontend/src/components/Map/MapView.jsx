import React, { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import Tooltip from './Tooltip.jsx'
import Legend from './Legend.jsx'

const MAPTILER_KEY = 'get_your_own_OpIi9ZULNHzrESv6T2vL'

export default function MapView({ indicator, geojson, selectedFeature, onSelectFeature }) {
  const mapContainer = useRef(null)
  const map          = useRef(null)
  const isLoaded     = useRef(false)
  const pendingData  = useRef(null)
  const currentMode  = useRef(null)
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
      map.current.addSource('data', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      isLoaded.current = true
      if (pendingData.current) {
        buildLayers(pendingData.current.mode, pendingData.current.geojson)
        pendingData.current = null
      }
    })

    return () => {
      isLoaded.current = false
      map.current?.remove()
      map.current = null
    }
  }, [])

  // ── Supprime tous les layers liés à la source 'data'
  const removeLayers = () => {
    const m = map.current
    if (!m) return
    const ids = ['imq-fill', 'imq-border', 'imq-highlight', 'itr-circles', 'itr-highlight']
    ids.forEach(id => { if (m.getLayer(id)) m.removeLayer(id) })
    // Supprimer les listeners précédents en réinstallant (on remplace les layers)
  }

  // ── Construit les layers selon l'indicateur
  const buildLayers = (mode, data) => {
    const m = map.current
    if (!m) return

    removeLayers()
    m.getSource('data').setData(data)
    currentMode.current = mode

    if (mode === 'IMQ') {
      m.addLayer({
        id: 'imq-fill', type: 'fill', source: 'data',
        paint: {
          'fill-color': [
            'interpolate', ['linear'], ['get', 'score_imq_100'],
            0, '#22c55e', 33, '#22c55e', 34, '#f59e0b', 66, '#f59e0b', 67, '#ef4444', 100, '#ef4444',
          ],
          'fill-opacity': 0.65,
        },
      })
      m.addLayer({
        id: 'imq-border', type: 'line', source: 'data',
        paint: { 'line-color': 'rgba(255,255,255,0.15)', 'line-width': 0.8 },
      })
      m.addLayer({
        id: 'imq-highlight', type: 'line', source: 'data',
        filter: ['==', 'iris_code', ''],
        paint: { 'line-color': '#ffffff', 'line-width': 2.5, 'line-opacity': 0.9 },
      })

      m.on('mousemove', 'imq-fill', (e) => {
        m.getCanvas().style.cursor = 'pointer'
        setTooltip({ feature: e.features[0], x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })
      m.on('mouseleave', 'imq-fill', () => {
        m.getCanvas().style.cursor = ''
        setTooltip({ feature: null, x: 0, y: 0 })
      })
      m.on('click', 'imq-fill', (e) => onSelectFeature(e.features[0].properties))

    } else {
      m.addLayer({
        id: 'itr-circles', type: 'circle', source: 'data',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'nb_transactions'], 3, 4, 50, 7, 200, 11],
          'circle-color': [
            'interpolate', ['linear'], ['get', 'itr_score'],
            0, '#22c55e', 20, '#22c55e', 40, '#84cc16', 60, '#eab308', 80, '#f97316', 100, '#ef4444',
          ],
          'circle-opacity': 0.85,
          'circle-stroke-width': 1,
          'circle-stroke-color': 'rgba(255,255,255,0.15)',
        },
      })
      m.addLayer({
        id: 'itr-highlight', type: 'circle', source: 'data',
        filter: ['==', 'nom_voie', ''],
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'nb_transactions'], 3, 7, 50, 11, 200, 16],
          'circle-color': '#ffffff', 'circle-opacity': 0.2,
          'circle-stroke-width': 2, 'circle-stroke-color': '#ffffff', 'circle-stroke-opacity': 0.9,
        },
      })

      m.on('mousemove', 'itr-circles', (e) => {
        m.getCanvas().style.cursor = 'pointer'
        const feature = e.features[0]
        m.setFilter('itr-highlight', ['==', 'nom_voie', feature.properties.nom_voie])
        setTooltip({ feature, x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })
      m.on('mouseleave', 'itr-circles', () => {
        m.getCanvas().style.cursor = ''
        m.setFilter('itr-highlight', ['==', 'nom_voie', ''])
        setTooltip({ feature: null, x: 0, y: 0 })
      })
      m.on('click', 'itr-circles', (e) => onSelectFeature(e.features[0].properties))
    }
  }

  // ── Mise à jour quand geojson ou indicator changent
  useEffect(() => {
    if (!geojson) return
    const mode = indicator

    if (isLoaded.current && map.current) {
      if (currentMode.current !== mode) {
        buildLayers(mode, geojson)
      } else {
        const source = map.current.getSource('data')
        if (source) source.setData(geojson)
      }
    } else {
      pendingData.current = { mode, geojson }
    }
  }, [geojson, indicator])

  // ── Zoom sur feature sélectionnée
  useEffect(() => {
    if (!map.current || !selectedFeature || !isLoaded.current) return

    if (indicator === 'IMQ') {
      map.current.flyTo({ center: [selectedFeature.lon_centre, selectedFeature.lat_centre], zoom: 14, duration: 800 })
      if (map.current.getLayer('imq-highlight'))
        map.current.setFilter('imq-highlight', ['==', 'iris_code', selectedFeature.iris_code])
    } else {
      map.current.flyTo({ center: [selectedFeature.lon_centre, selectedFeature.lat_centre], zoom: 15, duration: 800 })
      if (map.current.getLayer('itr-highlight'))
        map.current.setFilter('itr-highlight', ['==', 'nom_voie', selectedFeature.nom_voie])
    }
  }, [selectedFeature])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      <Tooltip indicator={indicator} feature={tooltip.feature} x={tooltip.x} y={tooltip.y} />
      <Legend indicator={indicator} />
    </div>
  )
}
