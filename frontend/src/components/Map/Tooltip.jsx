import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const IMQ_COLOR = (score) => {
  if (score > 66) return '#ef4444'
  if (score > 33) return '#f59e0b'
  return '#22c55e'
}

const ITR_COLOR = (score) => {
  if (score <= 20) return '#22c55e'
  if (score <= 40) return '#84cc16'
  if (score <= 60) return '#eab308'
  if (score <= 80) return '#f97316'
  return '#ef4444'
}

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
}

const formatNumber = (value, digits = 0) =>
  Number(value || 0).toLocaleString('fr-FR', { maximumFractionDigits: digits, minimumFractionDigits: digits })

function TooltipIMQ({ p }) {
  const color = IMQ_COLOR(p.score_imq_100)
  return (
    <>
      <p style={{ fontWeight: 600, fontSize: 13, color: '#f0f2ff', marginBottom: 2 }}>{p.iris_nom}</p>
      <p style={{ fontSize: 11, color: '#8b92b8', marginBottom: 10 }}>arr. {p.arrondissement}</p>
      <div style={{ display: 'inline-block', background: color + '22', border: `1px solid ${color}55`, borderRadius: 20, padding: '2px 10px', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color }}>{p.interpretation}</span>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: '#8b92b8' }}>Score IMQ</span>
          <span style={{ fontSize: 13, fontWeight: 700, color }}>{p.score_imq_100}/100</span>
        </div>
        <div style={{ height: 4, background: '#2e3348', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${p.score_imq_100}%`, background: color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px' }}>
        {[
          { label: 'Prix DVF',   value: `${Math.round((p.delta_prix_norm || 0) * 100)}/100` },
          { label: 'Commerce',   value: `${Math.round((p.ratio_comm_norm || 0) * 100)}/100` },
          { label: 'Revenu',     value: `${Math.round((p.revenu_norm || 0) * 100)}/100` },
          { label: 'Vacance',    value: `${Math.round((p.vacance_norm || 0) * 100)}/100` },
        ].map(item => (
          <div key={item.label}>
            <p style={{ fontSize: 10, color: '#555e80', marginBottom: 1 }}>{item.label}</p>
            <p style={{ fontSize: 12, fontWeight: 500, color: '#c8cde8' }}>{item.value}</p>
          </div>
        ))}
      </div>
    </>
  )
}

function TooltipITR({ p }) {
  const color = ITR_COLOR(p.itr_score)
  return (
    <>
      <p style={{ fontWeight: 600, fontSize: 13, color: '#f0f2ff', marginBottom: 2 }}>{p.nom_voie}</p>
      <p style={{ fontSize: 11, color: '#8b92b8', marginBottom: 10 }}>arr. {p.arrondissement}</p>
      <div style={{ display: 'inline-block', background: color + '22', border: `1px solid ${color}55`, borderRadius: 20, padding: '2px 10px', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color }}>{p.itr_label}</span>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: '#8b92b8' }}>Score ITR</span>
          <span style={{ fontSize: 13, fontWeight: 700, color }}>{p.itr_score}/100</span>
        </div>
        <div style={{ height: 4, background: '#2e3348', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${p.itr_score}%`, background: color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px' }}>
        {[
          { label: 'Prix médian',   value: `${Math.round(p.prix_m2_median).toLocaleString('fr-FR')} €/m²` },
          { label: 'Revenu médian', value: `${Math.round(p.revenu_median_uc).toLocaleString('fr-FR')} €/an` },
          { label: 'Log. sociaux',  value: p.nb_logements_sociaux > 0 ? p.nb_logements_sociaux : 'Aucun' },
          { label: 'Transactions',  value: `${p.nb_transactions}` },
        ].map(item => (
          <div key={item.label}>
            <p style={{ fontSize: 10, color: '#555e80', marginBottom: 1 }}>{item.label}</p>
            <p style={{ fontSize: 12, fontWeight: 500, color: '#c8cde8' }}>{item.value}</p>
          </div>
        ))}
      </div>
    </>
  )
}

function TooltipGeneric({ indicator, p }) {
  const cfg = getIndicatorConfig(indicator)
  const score = Number(p[cfg.scoreField] || 0)
  const label = p[cfg.labelField]
  const color = LABEL_COLOR[label] || '#8b92b8'

  const rowsByIndicator = {
    SVP: [
      { label: 'Espaces verts', value: formatNumber(p.nb_espaces_verts) },
      { label: 'Arbres', value: formatNumber(p.nb_arbres) },
      { label: 'Score alim.', value: formatNumber(p.score_alim_brut, 1) },
      { label: 'Commerce', value: p.has_commerce ? 'Oui' : 'Non' },
    ],
    IAML: [
      { label: 'Prix médian', value: `${formatNumber(p.prix_m2_median)} €/m²` },
      { label: 'Accessibilité', value: formatNumber(p.score_accessibilite, 1) },
      { label: 'Lignes métro/bus', value: `${formatNumber(p.nb_lignes_metro)} / ${formatNumber(p.nb_lignes_bus)}` },
      { label: 'Points Vélib', value: formatNumber(p.nb_points_velib) },
    ],
  }

  const rows = rowsByIndicator[indicator] || []

  return (
    <>
      <p style={{ fontWeight: 600, fontSize: 13, color: '#f0f2ff', marginBottom: 2 }}>{p.nom_voie}</p>
      <p style={{ fontSize: 11, color: '#8b92b8', marginBottom: 10 }}>
        {p.code_postal} · arr. {p.arrondissement}
      </p>
      <div style={{ display: 'inline-block', background: `${color}22`, border: `1px solid ${color}55`, borderRadius: 20, padding: '2px 10px', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color }}>{label}</span>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: '#8b92b8' }}>{cfg.scoreLabel}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color }}>{formatNumber(score)}/100</span>
        </div>
        <div style={{ height: 4, background: '#2e3348', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px' }}>
        {rows.map(item => (
          <div key={item.label}>
            <p style={{ fontSize: 10, color: '#555e80', marginBottom: 1 }}>{item.label}</p>
            <p style={{ fontSize: 12, fontWeight: 500, color: '#c8cde8' }}>{item.value}</p>
          </div>
        ))}
      </div>
    </>
  )
}

export default function Tooltip({ indicator, feature, x, y }) {
  if (!feature) return null
  const p = feature.properties

  return (
    <div style={{
      position: 'fixed', left: x + 16, top: y - 8,
      background: 'rgba(21,24,36,0.97)', border: '1px solid #2e3348',
      borderRadius: 10, padding: '12px 16px', minWidth: 220,
      pointerEvents: 'none', zIndex: 999,
      backdropFilter: 'blur(12px)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
    }}>
      {indicator === 'IMQ'
        ? <TooltipIMQ p={p} />
        : indicator === 'ITR'
        ? <TooltipITR p={p} />
        : <TooltipGeneric indicator={indicator} p={p} />
      }
    </div>
  )
}
