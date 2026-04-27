import React, { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import Tooltip from './Tooltip.jsx'
import Legend from './Legend.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const MAPTILER_KEY = 'get_your_own_OpIi9ZULNHzrESv6T2vL'

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

export default function MapView({ indicator, geojson, selectedRue, onSelectRue }) {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const isLoaded = useRef(false)
  const pendingData = useRef(null)
  const [tooltip, setTooltip] = useState({ feature: null, x: 0, y: 0 })

  const cfg = getIndicatorConfig(indicator)
  const scoreField = cfg.scoreField
  const labelField = cfg.labelField
  const safeGeoJSON = useMemo(() => prepareGeoJSON(geojson), [geojson])

  const colorExpression = useMemo(
    () => [
      'match',
      ['get', labelField],
      'Très accessible',
      '#22c55e',
      'Accessible',
      '#84cc16',
      'Modéré',
      '#eab308',
      'Tendu',
      '#f97316',
      'Très tendu',
      '#ef4444',
      'Très faible',
      '#ef4444',
      'Faible',
      '#f97316',
      'Bon',
      '#84cc16',
      'Excellent',
      '#22c55e',
      '#6b7280',
    ],
    [labelField]
  )

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
      map.current.addSource('rues', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })

      map.current.addLayer({
        id: 'rues-points',
        type: 'circle',
        source: 'rues',
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

      map.current.addLayer({
        id: 'rues-highlight',
        type: 'circle',
        source: 'rues',
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

      map.current.on('mousemove', 'rues-points', (e) => {
        map.current.getCanvas().style.cursor = 'pointer'
        const feature = e.features[0]
        if (!feature) return

        map.current.setFilter('rues-highlight', ['==', '__point_id', feature.properties.__point_id])
        setTooltip({ feature, x: e.originalEvent.clientX, y: e.originalEvent.clientY })
      })

      map.current.on('mouseleave', 'rues-points', () => {
        map.current.getCanvas().style.cursor = ''

        if (selectedRue?.__point_id) {
          map.current.setFilter('rues-highlight', ['==', '__point_id', selectedRue.__point_id])
        } else {
          map.current.setFilter('rues-highlight', ['==', '__point_id', ''])
        }

        setTooltip({ feature: null, x: 0, y: 0 })
      })

      map.current.on('click', 'rues-points', (e) => {
        const feature = e.features[0]
        if (!feature) return

        const [lon, lat] = feature.geometry.coordinates
        onSelectRue({
          ...feature.properties,
          lon_centre: lon,
          lat_centre: lat,
          lon,
          lat,
        })

        map.current.setFilter('rues-highlight', ['==', '__point_id', feature.properties.__point_id])
      })

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
  }, [colorExpression, onSelectRue, selectedRue, scoreField])

  useEffect(() => {
    if (!map.current || !isLoaded.current) return

    map.current.setPaintProperty('rues-points', 'circle-color', colorExpression)
  }, [colorExpression, scoreField])

  useEffect(() => {
    if (!safeGeoJSON) return

    if (isLoaded.current && map.current) {
      const source = map.current.getSource('rues')
      if (source) source.setData(safeGeoJSON)
    } else {
      pendingData.current = safeGeoJSON
    }
  }, [safeGeoJSON])

  useEffect(() => {
    if (!map.current || !selectedRue || !isLoaded.current) return

    const lon = selectedRue.lon_centre ?? selectedRue.lon
    const lat = selectedRue.lat_centre ?? selectedRue.lat
    if (lon == null || lat == null) return

    map.current.flyTo({
      center: [lon, lat],
      zoom: 15,
      duration: 800,
    })

    map.current.setFilter('rues-highlight', ['==', '__point_id', selectedRue.__point_id || ''])
  }, [selectedRue])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
      <Tooltip indicator={indicator} feature={tooltip.feature} x={tooltip.x} y={tooltip.y} />
      <Legend indicator={indicator} />
    </div>
  )
}
