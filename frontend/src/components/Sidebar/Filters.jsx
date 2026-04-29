import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const ARRONDISSEMENTS = Array.from({ length: 20 }, (_, i) => i + 1)
const IMQ_LABELS = ['Stable', 'Mutation modérée', 'Mutation forte']
const IMQ_COLORS = { Stable: '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626' }

const Select = ({ label, value, onChange, children }) => (
  <div style={{ marginBottom: 12 }}>
    <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</p>
    <select
      value={value}
      onChange={e => onChange(e.target.value || null)}
      style={{
        width: '100%', background: 'var(--bg)', border: '1px solid var(--border)',
        borderRadius: 7, color: 'var(--text)', fontSize: 12, padding: '7px 10px',
        outline: 'none', cursor: 'pointer', appearance: 'none',
      }}
    >{children}</select>
  </div>
)

export default function Filters({ indicator, filters, onChange }) {
  const cfg   = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'
  const set   = key => val => onChange({ ...filters, [key]: val })

  const hasFilter = filters.arrondissement || filters.interpretation ||
    filters[cfg.labelField] || (indicator === 'SVP' && filters.has_commerce != null)

  return (
    <div>
      <Select label="Arrondissement" value={filters.arrondissement || ''} onChange={set('arrondissement')}>
        <option value="">Tous les arrondissements</option>
        {ARRONDISSEMENTS.map(n => <option key={n} value={n}>{n}e arr.</option>)}
      </Select>

      {isIMQ ? (
        <>
          <div style={{ marginBottom: 12 }}>
            <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Interprétation</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {IMQ_LABELS.map(l => (
                <button
                  key={l}
                  onClick={() => onChange({ ...filters, interpretation: filters.interpretation === l ? null : l })}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    background: filters.interpretation === l ? IMQ_COLORS[l] + '15' : 'var(--bg)',
                    border: `1px solid ${filters.interpretation === l ? IMQ_COLORS[l] + '60' : 'var(--border)'}`,
                    borderRadius: 7, padding: '7px 10px', cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left',
                  }}
                >
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: IMQ_COLORS[l], flexShrink: 0 }} />
                  <span style={{ fontSize: 12, color: 'var(--text)', fontWeight: filters.interpretation === l ? 600 : 400 }}>{l}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <>
          <div style={{ marginBottom: 12 }}>
            <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Niveau</p>
            <select
              value={filters[cfg.labelField] || ''}
              onChange={e => onChange({ ...filters, [cfg.labelField]: e.target.value || null })}
              style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 7, color: 'var(--text)', fontSize: 12, padding: '7px 10px', outline: 'none', cursor: 'pointer', appearance: 'none' }}
            >
              <option value="">Tous les niveaux</option>
              {cfg.labels.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          {indicator === 'SVP' && (
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Commerce</p>
              <div style={{ display: 'flex', gap: 4 }}>
                {[{ l: 'Tous', v: null }, { l: 'Avec', v: 'true' }, { l: 'Sans', v: 'false' }].map(opt => (
                  <button
                    key={String(opt.v)}
                    onClick={() => onChange({ ...filters, has_commerce: opt.v })}
                    style={{
                      flex: 1, padding: '6px 4px', borderRadius: 6, cursor: 'pointer', fontSize: 11, fontWeight: 500,
                      transition: 'all 0.15s', border: 'none',
                      background: String(filters.has_commerce) === String(opt.v) ? 'var(--text)' : 'var(--bg)',
                      color: String(filters.has_commerce) === String(opt.v) ? '#fff' : 'var(--text-2)',
                    }}
                  >{opt.l}</button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {hasFilter && (
        <button
          onClick={() => onChange({})}
          style={{
            width: '100%', background: 'none', border: '1px solid var(--border)', borderRadius: 7,
            color: 'var(--text-2)', fontSize: 12, padding: '7px', cursor: 'pointer', transition: 'all 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--text)'; e.currentTarget.style.color = 'var(--text)' }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}
        >
          Réinitialiser les filtres
        </button>
      )}
    </div>
  )
}
