import React, { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import Tooltip from './Tooltip.jsx'
import Legend from './Legend.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

// Free light map — no API key needed
const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

const LABEL_COLOR = {
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
}

function prepareGeoJSON(geojson) {
  if (!geojson?.features) return geojson
  return {
    ...geojson,
    features: geojson.features.map((f, i) => ({
      ...f,
      properties: {
        ...f.properties,
        __point_id: f.properties?.point_id ?? f.properties?.id ??
          `${f.geometry?.coordinates?.[0]}_${f.geometry?.coordinates?.[1]}_${i}`,
      },
    })),
  }
}

export default function MapView({ indicator, geojson, selectedFeature, onSelectFeature }) {
  const mapContainer = useRef(null)
  const map          = useRef(null)
  const isLoaded     = useRef(false)
  const pendingData  = useRef(null)
  const currentMode  = useRef(null)
  const selectedRef  = useRef(null)
  const [tooltip, setTooltip] = useState({ feature: null, x: 0, y: 0 })

  const cfg        = getIndicatorConfig(indicator)
  const labelField = cfg.labelField

  const safeGeoJSON = useMemo(() => prepareGeoJSON(geojson), [geojson])

  const colorExpression = useMemo(() => {
    const values = cfg.labels.flatMap(l => [l, LABEL_COLOR[l] || '#9ca3af'])
    return ['match', ['get', labelField], ...values, '#9ca3af']
  }, [cfg.labels, labelField])

  useEffect(() => { selectedRef.current = selectedFeature }, [selectedFeature])

  const removeLayers = (m) => {
    ['imq-fill', 'imq-border', 'imq-highlight', 'rues-points', 'rues-highlight']
      .forEach(id => { if (m.getLayer(id)) m.removeLayer(id) })
    ;['data-imq', 'rues'].forEach(src => { if (m.getSource(src)) m.removeSource(src) })
  }

  const buildLayers = (mode, data) => {
    const m = map.current
    if (!m) return
    removeLayers(m)
    currentMode.current = mode

    if (mode === 'IMQ') {
      m.addSource('data-imq', { type: 'geojson', data })
      m.addLayer({
        id: 'imq-fill', type: 'fill', source: 'data-imq',
        paint: {
          'fill-color': ['match', ['get', 'interpretation'],
            'Stable', '#16a34a',
            'Mutation modérée', '#d97706',
            'Mutation forte', '#dc2626',
            '#9ca3af'],
          'fill-opacity': 0.55,
        },
      })
      m.addLayer({
        id: 'imq-border', type: 'line', source: 'data-imq',
        paint: { 'line-color': 'rgba(28,25,22,0.15)', 'line-width': 0.8 },
      })
      m.addLayer({
        id: 'imq-highlight', type: 'line', source: 'data-imq',
        filter: ['==', 'iris_code', ''],
        paint: { 'line-color': '#1C1916', 'line-width': 2.5, 'line-opacity': 0.8 },
      })
      m.on('mousemove', 'imq-fill', (e) => {
        m.getCanvas().style.cursor = 'pointer'
        setTooltip({ feature: e.features[0], x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })
      m.on('mouseleave', 'imq-fill', () => {
        m.getCanvas().style.cursor = ''
        setTooltip({ feature: null, x: 0, y: 0 })
      })
      m.on('click', 'imq-fill', (e) => {
        const p = e.features[0].properties
        onSelectFeature(p)
        if (m.getLayer('imq-highlight')) m.setFilter('imq-highlight', ['==', 'iris_code', p.iris_code])
      })

    } else {
      const prepared = prepareGeoJSON(data)
      m.addSource('rues', { type: 'geojson', data: prepared })
      m.addLayer({
        id: 'rues-points', type: 'circle', source: 'rues',
        paint: {
          'circle-radius': [
            'case',
            ['has', 'nb_arbres'], ['interpolate', ['linear'], ['get', 'nb_arbres'], 0, 4, 10, 7, 50, 11],
            ['has', 'nb_transactions'], ['interpolate', ['linear'], ['get', 'nb_transactions'], 0, 4, 10, 7, 50, 11],
            4,
          ],
          'circle-color': colorExpression,
          'circle-opacity': 0.82,
          'circle-stroke-width': 1.5,
          'circle-stroke-color': 'rgba(255,255,255,0.8)',
        },
      })
      m.addLayer({
        id: 'rues-highlight', type: 'circle', source: 'rues',
        filter: ['==', '__point_id', ''],
        paint: {
          'circle-radius': 14,
          'circle-color': 'transparent',
          'circle-stroke-width': 2.5,
          'circle-stroke-color': '#1C1916',
        },
      })
      m.on('mousemove', 'rues-points', (e) => {
        m.getCanvas().style.cursor = 'pointer'
        const f = e.features[0]
        if (!f) return
        m.setFilter('rues-highlight', ['==', '__point_id', f.properties.__point_id])
        setTooltip({ feature: f, x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })
      m.on('mouseleave', 'rues-points', () => {
        m.getCanvas().style.cursor = ''
        const sel = selectedRef.current
        m.setFilter('rues-highlight', sel?.__point_id ? ['==', '__point_id', sel.__point_id] : ['==', '__point_id', ''])
        setTooltip({ feature: null, x: 0, y: 0 })
      })
      m.on('click', 'rues-points', (e) => {
        const f = e.features[0]
        if (!f) return
        const [lon, lat] = f.geometry.coordinates
        onSelectFeature({ ...f.properties, lon_centre: lon, lat_centre: lat })
        m.setFilter('rues-highlight', ['==', '__point_id', f.properties.__point_id])
      })
    }
  }

  useEffect(() => {
    if (map.current) return
    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: MAP_STYLE,
      center: [2.3488, 48.8534],
      zoom: 12, minZoom: 11, maxZoom: 18,
    })
    map.current.addControl(new maplibregl.NavigationControl({ showCompass: false }))
    map.current.on('load', () => {
      isLoaded.current = true
      if (pendingData.current) {
        buildLayers(pendingData.current.mode, pendingData.current.geojson)
        pendingData.current = null
      }
    })
    return () => { isLoaded.current = false; map.current?.remove(); map.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map.current || !isLoaded.current) return
    if (map.current.getLayer('rues-points'))
      map.current.setPaintProperty('rues-points', 'circle-color', colorExpression)
  }, [colorExpression])

  useEffect(() => {
    if (!safeGeoJSON) return
    const mode = indicator
    if (isLoaded.current && map.current) {
      if (currentMode.current !== mode) {
        buildLayers(mode, safeGeoJSON)
      } else {
        const src = map.current.getSource(mode === 'IMQ' ? 'data-imq' : 'rues')
        if (src) src.setData(safeGeoJSON)
      }
    } else {
      pendingData.current = { mode, geojson: safeGeoJSON }
    }
  }, [safeGeoJSON, indicator]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map.current || !selectedFeature || !isLoaded.current) return
    if (indicator === 'IMQ') {
      map.current.flyTo({ center: [selectedFeature.lon_centre, selectedFeature.lat_centre], zoom: 14, duration: 800 })
      if (map.current.getLayer('imq-highlight'))
        map.current.setFilter('imq-highlight', ['==', 'iris_code', selectedFeature.iris_code])
    } else {
      const lon = selectedFeature.lon_centre ?? selectedFeature.lon
      const lat = selectedFeature.lat_centre ?? selectedFeature.lat
      if (lon != null && lat != null) map.current.flyTo({ center: [lon, lat], zoom: 15, duration: 800 })
      if (map.current.getLayer('rues-highlight'))
        map.current.setFilter('rues-highlight', ['==', '__point_id', selectedFeature.__point_id || ''])
    }
  }, [selectedFeature]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      <Tooltip indicator={indicator} feature={tooltip.feature} x={tooltip.x} y={tooltip.y} />
      <Legend indicator={indicator} />
    </div>
  )
}
