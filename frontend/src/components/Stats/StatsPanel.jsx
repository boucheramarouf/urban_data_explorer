import React from 'react'
import ArrondChart from './ArrondChart.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const LABEL_COLOR = {
  Stable: '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626',
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
}

const StatCard = ({ label, value, sub }) => (
  <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', flex: 1, minWidth: 0 }}>
    <p style={{ fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 3 }}>{label}</p>
    <p style={{ fontSize: 20, fontFamily: 'DM Serif Display, serif', color: 'var(--text)' }}>{value}</p>
    {sub && <p style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 2 }}>{sub}</p>}
  </div>
)

export default function StatsPanel({ indicator, stats }) {
  if (!stats) return (
    <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}>Chargement…</div>
  )

  const cfg          = getIndicatorConfig(indicator)
  const isIMQ        = indicator === 'IMQ'
  const medianKey    = cfg.statsMedianKey || `${cfg.key}_score_median`
  const scoreMedian  = stats[medianKey]
  const total        = Object.values(stats.distribution_label || {}).reduce((a, b) => a + b, 0)
  const nbSansCommerce = indicator === 'SVP' ? stats.nb_rues_sans_commerce ?? 0 : 0

  return (
    <div>
      {/* Score cards */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {isIMQ
          ? <><StatCard label="IRIS analysés" value={(stats.nb_iris_total || 0).toLocaleString('fr-FR')} sub="Paris" /><StatCard label="Score médian" value={scoreMedian} sub="sur 100" /></>
          : <><StatCard label="Rues analysées" value={(stats.nb_rues_total || 0).toLocaleString('fr-FR')} sub="Paris" /><StatCard label={`${cfg.scoreLabel} médian`} value={scoreMedian} sub="sur 100" /></>
        }
      </div>

      {/* SVP commerce warning */}
      {indicator === 'SVP' && nbSansCommerce > 0 && (
        <div style={{ background: '#d9770610', border: '1px solid #d9770630', borderRadius: 8, padding: '8px 12px', marginBottom: 14 }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#d97706' }}>{nbSansCommerce.toLocaleString('fr-FR')} rues sans commerce OSM</p>
          <p style={{ fontSize: 10, color: 'var(--text-3)' }}>Score basé sur la verdure et les commerces détectés</p>
        </div>
      )}

      {/* Distribution */}
      <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
        Distribution
      </p>
      {Object.entries(stats.distribution_label || {}).map(([label, count]) => {
        const pct   = total > 0 ? Math.round((count / total) * 100) : 0
        const color = LABEL_COLOR[label] || '#9ca3af'
        return (
          <div key={label} style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 12, color: 'var(--text)' }}>{label}</span>
              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{count.toLocaleString('fr-FR')} · {pct}%</span>
            </div>
            <div style={{ height: 4, background: 'var(--border)', borderRadius: 2 }}>
              <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 2, transition: 'width 0.5s ease' }} />
            </div>
          </div>
        )
      })}

      <div style={{ marginTop: 20 }}>
        <ArrondChart indicator={indicator} data={stats.par_arrondissement} />
      </div>
    </div>
  )
}
