import React, { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import Tooltip from './Tooltip.jsx'
import Legend from './Legend.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const MAPTILER_KEY = 'get_your_own_OpIi9ZULNHzrESv6T2vL'

const LABEL_COLOR = {
  'Très accessible': '#22c55e',
  Accessible: '#84cc16',
  Modéré: '#eab308',
  Tendu: '#f97316',
  'Très tendu': '#ef4444',
  'Très faible': '#ef4444',
  Faible: '#f97316',
  Bon: '#84cc16',
  Excellent: '#22c55e',
}

function prepareGeoJSON(geojson) {
  if (!geojson?.features) return geojson
  return {
    ...geojson,
    features: geojson.features.map((feature, index) => ({
      ...feature,
      properties: {
        ...feature.properties,
        __point_id:
          feature.properties?.point_id ??
          feature.properties?.id ??
          `${feature.geometry?.coordinates?.[0]}_${feature.geometry?.coordinates?.[1]}_${index}`,
      },
    })),
  }
}

export default function MapView({ indicator, geojson, selectedFeature, onSelectFeature }) {
  const mapContainer  = useRef(null)
  const map           = useRef(null)
  const isLoaded      = useRef(false)
  const pendingData   = useRef(null)
  const currentMode   = useRef(null)
  const selectedRef   = useRef(null)
  const [tooltip, setTooltip] = useState({ feature: null, x: 0, y: 0 })

  const cfg        = getIndicatorConfig(indicator)
  const labelField = cfg.labelField

  const safeGeoJSON = useMemo(() => prepareGeoJSON(geojson), [geojson])

  const colorExpression = useMemo(() => {
    const values = cfg.labels.flatMap(label => [label, LABEL_COLOR[label] || '#6b7280'])
    return ['match', ['get', labelField], ...values, '#6b7280']
  }, [cfg.labels, labelField])

  useEffect(() => {
    selectedRef.current = selectedFeature
  }, [selectedFeature])

  // ── Supprime tous les layers liés aux deux sources
  const removeLayers = (m) => {
    const ids = [
      'imq-fill', 'imq-border', 'imq-highlight',
      'rues-points', 'rues-highlight',
    ]
    ids.forEach(id => { if (m.getLayer(id)) m.removeLayer(id) })
    ;['data-imq', 'rues'].forEach(src => { if (m.getSource(src)) m.removeSource(src) })
  }

  // ── Construit les layers selon l'indicateur
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
          'fill-color': [
            'interpolate', ['linear'], ['get', 'score_imq_100'],
            0, '#22c55e', 33, '#22c55e', 34, '#f59e0b', 66, '#f59e0b', 67, '#ef4444', 100, '#ef4444',
          ],
          'fill-opacity': 0.65,
        },
      })
      m.addLayer({
        id: 'imq-border', type: 'line', source: 'data-imq',
        paint: { 'line-color': 'rgba(255,255,255,0.15)', 'line-width': 0.8 },
      })
      m.addLayer({
        id: 'imq-highlight', type: 'line', source: 'data-imq',
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
      m.on('click', 'imq-fill', (e) => {
        const props = e.features[0].properties
        onSelectFeature(props)
        if (m.getLayer('imq-highlight'))
          m.setFilter('imq-highlight', ['==', 'iris_code', props.iris_code])
      })

    } else {
      // ITR / SVP / IAML — cercles
      const prepared = prepareGeoJSON(data)
      m.addSource('rues', { type: 'geojson', data: prepared })

      m.addLayer({
        id: 'rues-points', type: 'circle', source: 'rues',
        paint: {
          'circle-radius': [
            'case',
            ['all', ['has', 'nb_arbres'], ['!=', ['get', 'nb_arbres'], null]],
            ['interpolate', ['linear'], ['get', 'nb_arbres'], 0, 4, 10, 7, 50, 11],
            ['all', ['has', 'nb_transactions'], ['!=', ['get', 'nb_transactions'], null]],
            ['interpolate', ['linear'], ['get', 'nb_transactions'], 0, 4, 10, 7, 50, 11],
            4,
          ],
          'circle-color': colorExpression,
          'circle-opacity': 0.85,
          'circle-stroke-width': 1,
          'circle-stroke-color': 'rgba(255,255,255,0.15)',
        },
      })
      m.addLayer({
        id: 'rues-highlight', type: 'circle', source: 'rues',
        filter: ['==', '__point_id', ''],
        paint: {
          'circle-radius': [
            'case',
            ['all', ['has', 'nb_arbres'], ['!=', ['get', 'nb_arbres'], null]],
            ['interpolate', ['linear'], ['get', 'nb_arbres'], 0, 7, 10, 11, 50, 16],
            ['all', ['has', 'nb_transactions'], ['!=', ['get', 'nb_transactions'], null]],
            ['interpolate', ['linear'], ['get', 'nb_transactions'], 0, 7, 10, 11, 50, 16],
            9,
          ],
          'circle-color': '#ffffff',
          'circle-opacity': 0.25,
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
          'circle-stroke-opacity': 1,
        },
      })

      m.on('mousemove', 'rues-points', (e) => {
        m.getCanvas().style.cursor = 'pointer'
        const feature = e.features[0]
        if (!feature) return
        m.setFilter('rues-highlight', ['==', '__point_id', feature.properties.__point_id])
        setTooltip({ feature, x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })
      m.on('mouseleave', 'rues-points', () => {
        m.getCanvas().style.cursor = ''
        const sel = selectedRef.current
        if (sel?.__point_id) {
          m.setFilter('rues-highlight', ['==', '__point_id', sel.__point_id])
        } else {
          m.setFilter('rues-highlight', ['==', '__point_id', ''])
        }
        setTooltip({ feature: null, x: 0, y: 0 })
      })
      m.on('click', 'rues-points', (e) => {
        const feature = e.features[0]
        if (!feature) return
        const [lon, lat] = feature.geometry.coordinates
        onSelectFeature({ ...feature.properties, lon_centre: lon, lat_centre: lat })
        m.setFilter('rues-highlight', ['==', '__point_id', feature.properties.__point_id])
      })
    }
  }

  // ── Init carte
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
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Mise à jour couleurs quand colorExpression change (mode cercle)
  useEffect(() => {
    if (!map.current || !isLoaded.current) return
    if (map.current.getLayer('rues-points')) {
      map.current.setPaintProperty('rues-points', 'circle-color', colorExpression)
    }
  }, [colorExpression])

  // ── Mise à jour quand geojson ou indicator changent
  useEffect(() => {
    if (!safeGeoJSON) return
    const mode = indicator

    if (isLoaded.current && map.current) {
      if (currentMode.current !== mode) {
        buildLayers(mode, safeGeoJSON)
      } else if (mode === 'IMQ') {
        const source = map.current.getSource('data-imq')
        if (source) source.setData(safeGeoJSON)
      } else {
        const source = map.current.getSource('rues')
        if (source) source.setData(safeGeoJSON)
      }
    } else {
      pendingData.current = { mode, geojson: safeGeoJSON }
    }
  }, [safeGeoJSON, indicator]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Zoom sur feature sélectionnée
  useEffect(() => {
    if (!map.current || !selectedFeature || !isLoaded.current) return

    if (indicator === 'IMQ') {
      map.current.flyTo({ center: [selectedFeature.lon_centre, selectedFeature.lat_centre], zoom: 14, duration: 800 })
      if (map.current.getLayer('imq-highlight'))
        map.current.setFilter('imq-highlight', ['==', 'iris_code', selectedFeature.iris_code])
    } else {
      const lon = selectedFeature.lon_centre ?? selectedFeature.lon
      const lat = selectedFeature.lat_centre ?? selectedFeature.lat
      if (lon != null && lat != null)
        map.current.flyTo({ center: [lon, lat], zoom: 15, duration: 800 })
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
