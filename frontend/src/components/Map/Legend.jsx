import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const COLORS = {
  'Stable': '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626',
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
}

export default function Legend({ indicator }) {
  const cfg   = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'

  return (
    <div style={{
      position: 'absolute', bottom: 24, right: 16, zIndex: 10,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '12px 16px', boxShadow: 'var(--shadow-md)',
      minWidth: 160,
    }}>
      <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
        {cfg.legendTitle}
      </p>
      {cfg.labels.map(label => (
        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
          <div style={{
            width: isIMQ ? 12 : 9, height: isIMQ ? 12 : 9,
            borderRadius: isIMQ ? 2 : '50%',
            background: COLORS[label] || '#9ca3af', flexShrink: 0,
            border: '1.5px solid rgba(255,255,255,0.6)',
          }} />
          <span style={{ fontSize: 11, color: 'var(--text-2)' }}>{label}</span>
        </div>
      ))}
    </div>
  )
}
