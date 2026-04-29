import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'
import ArrondChart from '../Stats/ArrondChart.jsx'

const IMQ_COLOR = (s) => s > 66 ? '#dc2626' : s > 33 ? '#d97706' : '#16a34a'
const SCORE_COLOR = (s) => s >= 70 ? '#dc2626' : s >= 45 ? '#d97706' : '#16a34a'

const LABEL_COLOR = {
  'Très accessible': '#16a34a', Accessible: '#65a30d', Modéré: '#d97706',
  Tendu: '#ea580c', 'Très tendu': '#dc2626',
  'Très faible': '#dc2626', Faible: '#ea580c', Bon: '#65a30d', Excellent: '#16a34a',
  Stable: '#16a34a', 'Mutation modérée': '#d97706', 'Mutation forte': '#dc2626',
}

const fmt = (v, d = 0) => Number(v || 0).toLocaleString('fr-FR', { maximumFractionDigits: d, minimumFractionDigits: d })

function MetricCard({ label, value, sub }) {
  return (
    <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px' }}>
      <p style={{ fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>{label}</p>
      <p style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{value}</p>
      {sub && <p style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 2 }}>{sub}</p>}
    </div>
  )
}

function ScoreRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border-light)' }}>
      <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{label}</span>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{value}</span>
    </div>
  )
}

function IMQContent({ f }) {
  const color = IMQ_COLOR(f.score_imq_100)
  const pct = (v) => `${Math.round((v || 0) * 100)}/100`
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        <MetricCard label="Prix DVF"   value={pct(f.delta_prix_norm)}  sub="variation immo." />
        <MetricCard label="Commerce"   value={pct(f.ratio_comm_norm)}  sub="SIRENE" />
        <MetricCard label="Revenu"     value={pct(f.revenu_norm)}      sub="Filosofi" />
        <MetricCard label="Vacance"    value={pct(f.vacance_norm)}     sub="LOVAC" />
      </div>
      <div style={{ background: 'var(--bg)', borderRadius: 8, padding: '12px 14px' }}>
        <p style={{ fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10, fontWeight: 600 }}>Formule IMQ</p>
        <ScoreRow label="35% · Prix DVF"         value={pct(f.delta_prix_norm)} />
        <ScoreRow label="30% · Commerce SIRENE"  value={pct(f.ratio_comm_norm)} />
        <ScoreRow label="20% · Revenu Filosofi"  value={pct(f.revenu_norm)} />
        <ScoreRow label="15% · Vacance LOVAC"    value={pct(f.vacance_norm)} />
      </div>
    </>
  )
}

function ITRContent({ f }) {
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        <MetricCard label="Prix médian"   value={`${fmt(f.prix_m2_median)} €`}             sub="par m²" />
        <MetricCard label="Revenu médian" value={`${fmt((f.revenu_median_uc || 0) / 1000)}k €`} sub="par an / UC" />
        <MetricCard label="Log. sociaux"  value={f.nb_logements_sociaux > 0 ? fmt(f.nb_logements_sociaux) : 'Aucun'} sub="dans l'IRIS" />
        <MetricCard label="Transactions"  value={fmt(f.nb_transactions)}                   sub="ventes 2021" />
      </div>
      <div style={{ background: 'var(--bg)', borderRadius: 8, padding: '12px 14px' }}>
        <p style={{ fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10, fontWeight: 600 }}>Composantes ITR</p>
        <ScoreRow label="Effort d'achat"       value={(f.c1_effort || 0).toFixed(3)} />
        <ScoreRow label="Facteur log. social"  value={(f.c2_logsoc || 0).toFixed(3)} />
        <ScoreRow label="Score brut"           value={(f.itr_brut  || 0).toFixed(4)} />
      </div>
    </>
  )
}

function SVPContent({ f }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
      <MetricCard label="Espaces verts"  value={fmt(f.nb_espaces_verts)}    sub="dans 200 m" />
      <MetricCard label="Arbres"         value={fmt(f.nb_arbres)}            sub="dans 200 m" />
      <MetricCard label="Score alim."    value={fmt(f.score_alim_brut, 1)}  sub="dans 500 m" />
      <MetricCard label="Commerce"       value={f.has_commerce ? 'Oui' : 'Non'} sub="OSM" />
    </div>
  )
}

function IAMLContent({ f }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
      <MetricCard label="Prix médian"    value={`${fmt(f.prix_m2_median)} €`}       sub="par m²" />
      <MetricCard label="Accessibilité"  value={fmt(f.score_accessibilite, 1)}      sub="score" />
      <MetricCard label="Lignes métro"   value={fmt(f.nb_lignes_metro)}             sub="médiane" />
      <MetricCard label="Lignes bus"     value={fmt(f.nb_lignes_bus)}               sub="médiane" />
      <MetricCard label="Points Vélib"   value={fmt(f.nb_points_velib)}             sub="médiane" />
      <MetricCard label="Transactions"   value={fmt(f.nb_transactions)}             sub="ventes 2021" />
    </div>
  )
}

export default function RightPanel({ indicator, feature, stats, onClose }) {
  const cfg = getIndicatorConfig(indicator)
  const isIMQ = indicator === 'IMQ'
  const isITR = indicator === 'ITR'

  const score = isIMQ ? feature?.score_imq_100 : feature?.[cfg.scoreField]
  const label = isIMQ ? feature?.interpretation : feature?.[cfg.labelField]
  const color = isIMQ ? IMQ_COLOR(score || 0) : (LABEL_COLOR[label] || SCORE_COLOR(score || 0))
  const title = isIMQ ? feature?.iris_nom : feature?.nom_voie
  const sub   = isIMQ
    ? `Paris · ${feature?.arrondissement}e arrondissement`
    : `${feature?.code_postal || ''} · ${feature?.arrondissement}e arrondissement`

  return (
    <div style={{
      width: feature ? 320 : 0,
      minWidth: feature ? 320 : 0,
      height: '100%',
      background: 'var(--bg-card)',
      borderLeft: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',
      transition: 'width 0.25s ease, min-width 0.25s ease',
    }}>
      {feature && (
        <>
          {/* Header */}
          <div style={{
            padding: '20px 20px 16px',
            borderBottom: '1px solid var(--border)',
            background: `linear-gradient(135deg, ${color}10, transparent)`,
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', marginBottom: 3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{title}</p>
                <p style={{ fontSize: 11, color: 'var(--text-3)' }}>{sub}</p>
              </div>
              <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', fontSize: 20, lineHeight: 1, padding: '0 0 0 12px', flexShrink: 0 }}>×</button>
            </div>

            {/* Score */}
            <div style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
                <span style={{ fontFamily: 'DM Serif Display, serif', fontSize: 36, color, lineHeight: 1 }}>{score}</span>
                <span style={{ fontSize: 12, color: 'var(--text-3)' }}>/100</span>
                <span style={{ fontSize: 11, fontWeight: 600, color, background: color + '18', border: `1px solid ${color}30`, borderRadius: 20, padding: '2px 10px', marginLeft: 4 }}>{label}</span>
              </div>
              <div style={{ height: 4, background: 'var(--border)', borderRadius: 2 }}>
                <div style={{ height: '100%', width: `${score || 0}%`, background: color, borderRadius: 2, transition: 'width 0.5s ease' }} />
              </div>
            </div>
          </div>

          {/* Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
            {isIMQ && <IMQContent f={feature} />}
            {isITR && <ITRContent f={feature} />}
            {indicator === 'SVP'  && <SVPContent  f={feature} />}
            {indicator === 'IAML' && <IAMLContent f={feature} />}
          </div>

          {/* Stats mini chart */}
          {stats?.par_arrondissement && (
            <div style={{ padding: '0 20px 20px', flexShrink: 0, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
              <ArrondChart indicator={indicator} data={stats.par_arrondissement} compact />
            </div>
          )}
        </>
      )}
    </div>
  )
}
