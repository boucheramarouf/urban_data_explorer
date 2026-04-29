import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const LABEL_COLOR = {
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
  Stable: '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626',
}
const fmt = (v, d = 0) => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: d, minimumFractionDigits: d })

function Row({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
      <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{label}</span>
      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)' }}>{value}</span>
    </div>
  )
}

function TooltipIMQ({ p }) {
  const score = p.score_imq_100
  const color = score > 66 ? '#dc2626' : score > 33 ? '#d97706' : '#16a34a'
  return (
    <>
      <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 1 }}>{p.iris_nom}</p>
      <p style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10 }}>arr. {p.arrondissement}</p>
      <div style={{ display: 'inline-block', background: color + '18', border: `1px solid ${color}30`, borderRadius: 20, padding: '2px 10px', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color }}>{p.interpretation}</span>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-3)' }}>Score IMQ</span>
          <span style={{ fontSize: 13, fontWeight: 700, color }}>{score}/100</span>
        </div>
        <div style={{ height: 3, background: 'var(--border)', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
        <Row label="Prix DVF"  value={`${Math.round((p.delta_prix_norm || 0) * 100)}/100`} />
        <Row label="Commerce"  value={`${Math.round((p.ratio_comm_norm || 0) * 100)}/100`} />
        <Row label="Revenu"    value={`${Math.round((p.revenu_norm || 0) * 100)}/100`} />
        <Row label="Vacance"   value={`${Math.round((p.vacance_norm || 0) * 100)}/100`} />
      </div>
    </>
  )
}

function TooltipGeneric({ indicator, p }) {
  const cfg = getIndicatorConfig(indicator)
  const score = Number(p[cfg.scoreField] || 0)
  const label = p[cfg.labelField]
  const color = LABEL_COLOR[label] || '#6b7280'

  const rowsByIndicator = {
    ITR:  [{ l: 'Prix médian', v: `${fmt(p.prix_m2_median)} €/m²` }, { l: 'Revenu médian', v: `${fmt(p.revenu_median_uc)} €/an` }, { l: 'Log. sociaux', v: p.nb_logements_sociaux > 0 ? fmt(p.nb_logements_sociaux) : 'Aucun' }, { l: 'Ventes 2021', v: `${fmt(p.nb_transactions)}` }],
    SVP:  [{ l: 'Espaces verts', v: fmt(p.nb_espaces_verts) }, { l: 'Arbres', v: fmt(p.nb_arbres) }, { l: 'Score alim.', v: fmt(p.score_alim_brut, 1) }, { l: 'Commerce', v: p.has_commerce ? 'Oui' : 'Non' }],
    IAML: [{ l: 'Prix médian', v: `${fmt(p.prix_m2_median)} €/m²` }, { l: 'Accessibilité', v: fmt(p.score_accessibilite, 1) }, { l: 'Métro/Bus', v: `${fmt(p.nb_lignes_metro)} / ${fmt(p.nb_lignes_bus)}` }, { l: 'Vélib', v: fmt(p.nb_points_velib) }],
  }
  const rows = rowsByIndicator[indicator] || []

  return (
    <>
      <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 1 }}>{p.nom_voie}</p>
      <p style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10 }}>{p.code_postal} · arr. {p.arrondissement}</p>
      <div style={{ display: 'inline-block', background: color + '18', border: `1px solid ${color}30`, borderRadius: 20, padding: '2px 10px', marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color }}>{label}</span>
      </div>
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{cfg.scoreLabel}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color }}>{fmt(score)}/100</span>
        </div>
        <div style={{ height: 3, background: 'var(--border)', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
        {rows.map(r => <Row key={r.l} label={r.l} value={r.v} />)}
      </div>
    </>
  )
}

export default function Tooltip({ indicator, feature, x, y }) {
  if (!feature) return null
  const p = feature.properties
  return (
    <div style={{
      position: 'fixed', left: x + 16, top: y - 8, zIndex: 999,
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 10, padding: '12px 16px', minWidth: 220,
      pointerEvents: 'none', boxShadow: 'var(--shadow-lg)',
    }}>
      {indicator === 'IMQ' ? <TooltipIMQ p={p} /> : <TooltipGeneric indicator={indicator} p={p} />}
    </div>
  )
}
