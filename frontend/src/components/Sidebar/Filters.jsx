import React from 'react'

const ARRONDISSEMENTS = Array.from({ length: 20 }, (_, i) => i + 1)
const LABELS = ['Très accessible', 'Accessible', 'Modéré', 'Tendu', 'Très tendu']
const LABEL_COLOR = {
  'Très accessible': '#22c55e',
  'Accessible':      '#84cc16',
  'Modéré':          '#eab308',
  'Tendu':           '#f97316',
  'Très tendu':      '#ef4444',
}

const Select = ({ label, value, onChange, children }) => (
  <div style={{ marginBottom: 12 }}>
    <p style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
      {label}
    </p>
    <select
      value={value}
      onChange={e => onChange(e.target.value || null)}
      style={{
        width: '100%',
        background: '#1a1d27',
        border: '1px solid #2e3348',
        borderRadius: 7,
        color: '#f0f2ff',
        fontSize: 12,
        padding: '7px 10px',
        outline: 'none',
        cursor: 'pointer',
        appearance: 'none',
      }}
    >
      {children}
    </select>
  </div>
)

export default function Filters({ filters, onChange }) {
  const set = (key) => (val) => onChange({ ...filters, [key]: val })

  return (
    <div style={{ padding: '0 0 4px' }}>
      <Select label="Arrondissement" value={filters.arrondissement || ''} onChange={set('arrondissement')}>
        <option value="">Tous les arrondissements</option>
        {ARRONDISSEMENTS.map(n => (
          <option key={n} value={n}>{n}e arrondissement</option>
        ))}
      </Select>

      <Select label="Niveau de tension" value={filters.label || ''} onChange={set('label')}>
        <option value="">Tous les niveaux</option>
        {LABELS.map(l => <option key={l} value={l}>{l}</option>)}
      </Select>

      {/* Reset */}
      {(filters.arrondissement || filters.label) && (
        <button
          onClick={() => onChange({})}
          style={{
            width: '100%',
            background: 'transparent',
            border: '1px solid #2e3348',
            borderRadius: 7,
            color: '#8b92b8',
            fontSize: 12,
            padding: '6px',
            cursor: 'pointer',
            marginTop: 4,
            transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = '#6c7dff'; e.currentTarget.style.color = '#6c7dff' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = '#2e3348'; e.currentTarget.style.color = '#8b92b8' }}
        >
          Réinitialiser les filtres
        </button>
      )}
    </div>
  )
}