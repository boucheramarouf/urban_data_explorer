import React from 'react'

const IMQ_LEVELS = [
  { label: 'Mutation forte',   color: '#ef4444' },
  { label: 'Mutation modérée', color: '#f59e0b' },
  { label: 'Stable',           color: '#22c55e' },
]

const ITR_LEVELS = [
  { label: 'Très tendu',      color: '#ef4444' },
  { label: 'Tendu',           color: '#f97316' },
  { label: 'Modéré',          color: '#eab308' },
  { label: 'Accessible',      color: '#84cc16' },
  { label: 'Très accessible', color: '#22c55e' },
]

export default function Legend({ indicator }) {
  const levels = indicator === 'ITR' ? ITR_LEVELS : IMQ_LEVELS
  const title  = indicator === 'ITR' ? 'Tension résidentielle' : 'Indice de mutation'

  return (
    <div style={{
      position: 'absolute', bottom: 32, right: 16,
      background: 'rgba(26,29,39,0.95)', border: '1px solid #2e3348',
      borderRadius: 10, padding: '12px 16px',
      backdropFilter: 'blur(8px)', zIndex: 10,
    }}>
      <p style={{ fontSize: 11, fontWeight: 600, color: '#8b92b8', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
        {title}
      </p>
      {levels.map(l => (
        <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <div style={{
            width: indicator === 'ITR' ? 10 : 12,
            height: indicator === 'ITR' ? 10 : 12,
            borderRadius: indicator === 'ITR' ? '50%' : 2,
            background: l.color, flexShrink: 0,
          }} />
          <span style={{ fontSize: 12, color: '#c8cde8' }}>{l.label}</span>
        </div>
      ))}
    </div>
  )
}
