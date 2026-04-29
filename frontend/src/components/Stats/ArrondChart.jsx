import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const scoreColor = (s) => s >= 70 ? '#dc2626' : s >= 45 ? '#d97706' : '#16a34a'

const CustomTooltip = ({ active, payload, indicator }) => {
  if (!active || !payload?.length) return null
  const d   = payload[0].payload
  const cfg = getIndicatorConfig(indicator)
  const key = cfg.statsMedianKey || `${cfg.key}_score_median`
  const s   = d[key]
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', boxShadow: 'var(--shadow-md)' }}>
      <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', marginBottom: 2 }}>{d.arrondissement}e arr.</p>
      <p style={{ fontSize: 11, color: 'var(--text-3)' }}>Score médian : <b style={{ color: scoreColor(s) }}>{s}</b></p>
      {d.nb_iris && <p style={{ fontSize: 11, color: 'var(--text-3)' }}>{d.nb_iris} IRIS</p>}
      {d.nb_rues && <p style={{ fontSize: 11, color: 'var(--text-3)' }}>{d.nb_rues} rues</p>}
    </div>
  )
}

export default function ArrondChart({ indicator, data, compact }) {
  if (!data) return null

  const cfg    = getIndicatorConfig(indicator)
  const key    = cfg.statsMedianKey || `${cfg.key}_score_median`
  const sorted = [...data].sort((a, b) => (b[key] || 0) - (a[key] || 0))
  const height = compact ? 180 : 300

  return (
    <div>
      {!compact && (
        <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
          Classement par arrondissement
        </p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={sorted} layout="vertical" margin={{ left: 0, right: 4, top: 0, bottom: 0 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category" dataKey="arrondissement"
            tick={{ fontSize: 10, fill: 'var(--text-3)' }}
            tickFormatter={v => `${v}e`} width={26}
          />
          <Tooltip content={<CustomTooltip indicator={indicator} />} cursor={{ fill: 'rgba(28,25,22,0.04)' }} />
          <Bar dataKey={key} radius={[0, 3, 3, 0]} maxBarSize={10}>
            {sorted.map((entry, i) => (
              <Cell key={i} fill={scoreColor(entry[key] || 0)} opacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
