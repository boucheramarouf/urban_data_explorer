import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const IMQ_LEVELS = [
  { label: 'Mutation forte',   color: '#ef4444' },
  { label: 'Mutation modérée', color: '#f59e0b' },
  { label: 'Stable',           color: '#22c55e' },
]

const COLORS_BY_LABEL = {
  'Très accessible': '#22c55e',
  Accessible: '#84cc16',
  Modéré: '#eab308',
  Tendu: '#f97316',
  'Très tendu': '#ef4444',
  'Très faible': '#ef4444',
  Faible: '#f97316',
  Bon: '#84cc16',
  Excellent: '#22c55e',
  'Stable': '#22c55e',
  'Mutation modérée': '#f59e0b',
  'Mutation forte': '#ef4444',
}

export default function Legend({ indicator }) {
  const cfg = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'
  const levels = isIMQ
    ? IMQ_LEVELS
    : cfg.labels.map(label => ({ label, color: COLORS_BY_LABEL[label] || '#6b7280' }))

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 32,
        right: 16,
        background: 'rgba(26,29,39,0.95)',
        border: '1px solid #2e3348',
        borderRadius: 10,
        padding: '12px 16px',
        backdropFilter: 'blur(8px)',
        zIndex: 10,
      }}
    >
      <p
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: '#8b92b8',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          marginBottom: 10,
        }}
      >
        {cfg.legendTitle}
      </p>
      {levels.map(l => (
        <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <div style={{
            width: isIMQ ? 12 : 10,
            height: isIMQ ? 12 : 10,
            borderRadius: isIMQ ? 2 : '50%',
            background: l.color,
            flexShrink: 0,
          }} />
          <span style={{ fontSize: 12, color: '#c8cde8' }}>{l.label}</span>
        </div>
      ))}
    </div>
  )
}
