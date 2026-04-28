import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const imqColor = (s) => s > 66 ? '#ef4444' : s > 33 ? '#f59e0b' : '#22c55e'
const itrColor = (s) => s <= 20 ? '#22c55e' : s <= 40 ? '#84cc16' : s <= 60 ? '#eab308' : s <= 80 ? '#f97316' : '#ef4444'

function scoreColor(indicator, score) {
  if (indicator === 'IMQ') return imqColor(score)
  return itrColor(score)
}

function CustomTooltip({ active, payload, indicator }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  const cfg = getIndicatorConfig(indicator)
  const medianKey = cfg.statsMedianKey || `${cfg.key}_score_median`
  const isIMQ = indicator === 'IMQ'
  const score = d[medianKey]
  const color = scoreColor(indicator, score)
  return (
    <div style={{ background: '#21253a', border: '1px solid #2e3348', borderRadius: 6, padding: '6px 10px' }}>
      <p style={{ fontSize: 12, color: '#f0f2ff', fontWeight: 600 }}>{d.arrondissement}e arr.</p>
      <p style={{ fontSize: 11, color: '#8b92b8' }}>Score médian : <b style={{ color }}>{score}</b></p>
      <p style={{ fontSize: 11, color: '#8b92b8' }}>{isIMQ ? `${d.nb_iris} IRIS` : `${d.nb_rues} rues`}</p>
    </div>
  )
}

export default function ArrondChart({ indicator, data }) {
  if (!data) return null

  const cfg = getIndicatorConfig(indicator)
  const medianKey = cfg.statsMedianKey || `${cfg.key}_score_median`
  const colorFn = (score) => scoreColor(indicator, score)

  const sorted = [...data].sort((a, b) => b[medianKey] - a[medianKey])

  return (
    <div>
      <p style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>
        Classement par arrondissement
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={sorted} layout="vertical" margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis type="category" dataKey="arrondissement" tick={{ fontSize: 10, fill: '#8b92b8' }} tickFormatter={v => `${v}e`} width={28} />
          <Tooltip content={<CustomTooltip indicator={indicator} />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey={medianKey} radius={[0, 3, 3, 0]}>
            {sorted.map((entry, i) => (
              <Cell key={i} fill={colorFn(entry[medianKey])} opacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
