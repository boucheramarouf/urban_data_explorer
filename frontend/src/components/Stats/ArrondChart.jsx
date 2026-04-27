import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const scoreColor = (score) => {
  if (score <= 20) return '#22c55e'
  if (score <= 40) return '#84cc16'
  if (score <= 60) return '#eab308'
  if (score <= 80) return '#f97316'
  return '#ef4444'
}

const CustomTooltip = ({ active, payload, indicator }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  const cfg = getIndicatorConfig(indicator)
  const medianKey = `${cfg.key}_score_median`
  return (
    <div style={{ background: '#21253a', border: '1px solid #2e3348', borderRadius: 6, padding: '6px 10px' }}>
      <p style={{ fontSize: 12, color: '#f0f2ff', fontWeight: 600 }}>{d.arrondissement}e arr.</p>
      <p style={{ fontSize: 11, color: '#8b92b8' }}>Score médian : <b style={{ color: scoreColor(d[medianKey]) }}>{d[medianKey]}</b></p>
      <p style={{ fontSize: 11, color: '#8b92b8' }}>{d.nb_rues} rues analysées</p>
    </div>
  )
}

export default function ArrondChart({ indicator, data }) {
  if (!data) return null

  const cfg = getIndicatorConfig(indicator)
  const medianKey = `${cfg.key}_score_median`

  const sorted = [...data].sort((a, b) => b[medianKey] - a[medianKey])

  return (
    <div>
      <p style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
        Classement par arrondissement
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={sorted} layout="vertical" margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis
            type="category"
            dataKey="arrondissement"
            tick={{ fontSize: 10, fill: '#8b92b8' }}
            tickFormatter={v => `${v}e`}
            width={28}
          />
          <Tooltip content={<CustomTooltip indicator={indicator} />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey={medianKey} radius={[0, 3, 3, 0]}>
            {sorted.map((entry, i) => (
              <Cell key={i} fill={scoreColor(entry[medianKey])} opacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}