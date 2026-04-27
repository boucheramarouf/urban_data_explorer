import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const LEVELS = [
  { label: 'Très accessible', color: '#22c55e' },
  { label: 'Accessible',      color: '#84cc16' },
  { label: 'Modéré',          color: '#eab308' },
  { label: 'Tendu',           color: '#f97316' },
  { label: 'Très tendu',      color: '#ef4444' },
]

export default function Legend({ indicator }) {
  const cfg = getIndicatorConfig(indicator)
  return (
    <div style={{
      position: 'absolute',
      bottom: 32,
      right: 16,
      background: 'rgba(26,29,39,0.95)',
      border: '1px solid #2e3348',
      borderRadius: 10,
      padding: '12px 16px',
      backdropFilter: 'blur(8px)',
      zIndex: 10,
    }}>
      <p style={{ fontSize: 11, fontWeight: 600, color: '#8b92b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
        {cfg.legendTitle}
      </p>
      {LEVELS.map(l => (
        <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: l.color, flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: '#c8cde8' }}>{l.label}</span>
        </div>
      ))}
    </div>
  )
}