import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

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
}

export default function Legend({ indicator }) {
  const cfg = getIndicatorConfig(indicator)

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
      {cfg.labels.map((label) => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: COLORS_BY_LABEL[label], flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: '#c8cde8' }}>{label}</span>
        </div>
      ))}
    </div>
  )
}
