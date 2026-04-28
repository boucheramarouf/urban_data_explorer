import React from 'react'
import ArrondChart from './ArrondChart.jsx'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const IMQ_COLOR = { 'Stable': '#22c55e', 'Mutation modérée': '#f59e0b', 'Mutation forte': '#ef4444' }
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
  Stable: '#22c55e',
  'Mutation modérée': '#f59e0b',
  'Mutation forte': '#ef4444',
}

const StatCard = ({ label, value, sub }) => (
  <div style={{ background: '#1a1d27', border: '1px solid #2e3348', borderRadius: 8, padding: '10px 12px', flex: 1, minWidth: 0 }}>
    <p style={{ fontSize: 10, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</p>
    <p style={{ fontSize: 18, fontWeight: 700, color: '#f0f2ff' }}>{value}</p>
    {sub && <p style={{ fontSize: 10, color: '#8b92b8', marginTop: 2 }}>{sub}</p>}
  </div>
)

export default function StatsPanel({ indicator, stats }) {
  if (!stats) return (
    <div style={{ padding: 16, color: '#555e80', fontSize: 12, textAlign: 'center' }}>Chargement des stats...</div>
  )

  const cfg = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'
  const scoreMedianKey = cfg.statsMedianKey || `${cfg.key}_score_median`
  const scoreValue = stats[scoreMedianKey]
  const total = Object.values(stats.distribution_label || {}).reduce((a, b) => a + b, 0)
  const nbSansCommerce = indicator === 'SVP' ? stats.nb_rues_sans_commerce ?? 0 : 0

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {isIMQ ? (
          <>
            <StatCard label="IRIS analysés"  value={(stats.nb_iris_total || 0).toLocaleString('fr-FR')} sub="Paris" />
            <StatCard label="Score médian"   value={scoreValue} sub="sur 100" />
          </>
        ) : (
          <>
            <StatCard label="Rues analysées" value={(stats.nb_rues_total || 0).toLocaleString('fr-FR')} sub="Paris 2021" />
            <StatCard label={`${cfg.scoreLabel} médian`} value={scoreValue} sub="sur 100" />
          </>
        )}
      </div>

      {indicator === 'SVP' && nbSansCommerce > 0 && (
        <div style={{
          background: 'rgba(249,115,22,0.06)', border: '1px solid rgba(249,115,22,0.2)',
          borderRadius: 8, padding: '7px 12px', marginBottom: 14,
        }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#f97316' }}>
            {nbSansCommerce.toLocaleString('fr-FR')} rues sans commerce OSM
          </p>
          <p style={{ fontSize: 10, color: '#8b92b8' }}>Score basé sur la verdure et les commerces détectés</p>
        </div>
      )}

      <div style={{ marginBottom: 20 }}>
        <p style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
          {isIMQ ? 'Distribution IMQ' : 'Distribution'}
        </p>
        {Object.entries(stats.distribution_label || {}).map(([label, count]) => {
          const pct = total > 0 ? Math.round((count / total) * 100) : 0
          const color = isIMQ ? (IMQ_COLOR[label] || '#6c7dff') : (LABEL_COLOR[label] || '#8b92b8')
          return (
            <div key={label} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{ fontSize: 11, color: '#c8cde8' }}>{label}</span>
                <span style={{ fontSize: 11, color: '#8b92b8' }}>{count} · {pct}%</span>
              </div>
              <div style={{ height: 4, background: '#2e3348', borderRadius: 2 }}>
                <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 2 }} />
              </div>
            </div>
          )
        })}
      </div>

      <ArrondChart indicator={indicator} data={stats.par_arrondissement} />
    </div>
  )
}
