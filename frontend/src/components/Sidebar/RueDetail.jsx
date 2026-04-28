import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

const IMQ_COLOR = (s) => s > 66 ? '#ef4444' : s > 33 ? '#f59e0b' : '#22c55e'
const ITR_COLOR = (s) => s <= 20 ? '#22c55e' : s <= 40 ? '#84cc16' : s <= 60 ? '#eab308' : s <= 80 ? '#f97316' : '#ef4444'

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

const Metric = ({ label, value, sub }) => (
  <div style={{ background: '#1a1d27', border: '1px solid #2e3348', borderRadius: 8, padding: '10px 12px' }}>
    <p style={{ fontSize: 10, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</p>
    <p style={{ fontSize: 16, fontWeight: 700, color: '#f0f2ff' }}>{value}</p>
    {sub && <p style={{ fontSize: 10, color: '#8b92b8', marginTop: 2 }}>{sub}</p>}
  </div>
)

const Row = ({ label, value }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #1a1d27' }}>
    <span style={{ fontSize: 12, color: '#8b92b8' }}>{label}</span>
    <span style={{ fontSize: 13, fontWeight: 600, color: '#c8cde8' }}>{value}</span>
  </div>
)

function IMQDetail({ f }) {
  const color = IMQ_COLOR(f.score_imq_100)
  const pct = (v) => `${Math.round((v || 0) * 100)}/100`
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Score IMQ</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 22, fontWeight: 800, color }}>{f.score_imq_100}</span>
          <span style={{ fontSize: 10, fontWeight: 600, color, background: color + '22', border: `1px solid ${color}44`, borderRadius: 20, padding: '2px 8px' }}>{f.interpretation}</span>
        </div>
      </div>
      <div style={{ height: 6, background: '#2e3348', borderRadius: 3, marginBottom: 16 }}>
        <div style={{ height: '100%', width: `${f.score_imq_100}%`, background: color, borderRadius: 3 }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        <Metric label="Prix DVF"    value={pct(f.delta_prix_norm)}  sub="Δ immobilier" />
        <Metric label="Commerce"    value={pct(f.ratio_comm_norm)}  sub="SIRENE" />
        <Metric label="Revenu"      value={pct(f.revenu_norm)}      sub="Filosofi" />
        <Metric label="Vacance"     value={pct(f.vacance_norm)}     sub="LOVAC" />
      </div>
      <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>Formule IMQ</p>
        <Row label="35% · Prix DVF"        value={pct(f.delta_prix_norm)} />
        <Row label="30% · Commerce SIRENE" value={pct(f.ratio_comm_norm)} />
        <Row label="20% · Revenu Filosofi" value={pct(f.revenu_norm)} />
        <Row label="15% · Vacance LOVAC"   value={pct(f.vacance_norm)} />
      </div>
    </>
  )
}

function ITRDetail({ f }) {
  const color = ITR_COLOR(f.itr_score)
  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Score ITR</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 22, fontWeight: 800, color }}>{f.itr_score}</span>
          <span style={{ fontSize: 10, fontWeight: 600, color, background: color + '22', border: `1px solid ${color}44`, borderRadius: 20, padding: '2px 8px' }}>{f.itr_label}</span>
        </div>
      </div>
      <div style={{ height: 6, background: '#2e3348', borderRadius: 3, marginBottom: 16 }}>
        <div style={{ height: '100%', width: `${f.itr_score}%`, background: color, borderRadius: 3 }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        <Metric label="Prix médian"   value={`${Math.round(f.prix_m2_median).toLocaleString('fr-FR')} €`} sub="par m²" />
        <Metric label="Revenu médian" value={`${Math.round(f.revenu_median_uc / 1000)}k €`}               sub="par an / UC" />
        <Metric label="Log. sociaux"  value={f.nb_logements_sociaux > 0 ? f.nb_logements_sociaux : 'Aucun'} sub="dans l'IRIS" />
        <Metric label="Transactions"  value={f.nb_transactions}                                             sub="ventes" />
      </div>
      <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>Composantes ITR</p>
        <Row label="Effort d'achat (prix/revenu)" value={(f.c1_effort || 0).toFixed(3)} />
        <Row label="Facteur logement social"      value={(f.c2_logsoc || 0).toFixed(3)} />
        <Row label="Score brut"                   value={(f.itr_brut  || 0).toFixed(4)} />
      </div>
    </>
  )
}

function GenericDetail({ indicator, f }) {
  const cfg = getIndicatorConfig(indicator)
  const scoreField = cfg.scoreField
  const labelField = cfg.labelField
  const color = LABEL_COLOR[f[labelField]] || '#8b92b8'

  const panels = {
    SVP: {
      title: 'Composantes SVP',
      metrics: [
        { label: 'Espaces verts', value: formatNumber(f.nb_espaces_verts), sub: 'dans 200 m' },
        { label: 'Arbres', value: formatNumber(f.nb_arbres), sub: 'dans 200 m' },
        { label: 'Score alim.', value: formatNumber(f.score_alim_brut, 1), sub: 'dans 500 m' },
        { label: 'Commerce', value: f.has_commerce ? 'Oui' : 'Non', sub: 'détection OSM' },
      ],
      rows: [
        { label: 'Score vert', value: formatNumber(f.score_vert, 3) },
        { label: 'Accès commerces', value: formatNumber(f.score_acces_alim, 3) },
        { label: 'SVP score', value: formatNumber(f.svp_score, 1) },
      ],
    },
    IAML: {
      title: 'Composantes IAML',
      metrics: [
        { label: 'Prix médian', value: `${formatNumber(f.prix_m2_median)} €`, sub: 'par m²' },
        { label: 'Accessibilité', value: formatNumber(f.score_accessibilite, 1), sub: 'dans 500 m' },
        { label: 'Lignes métro', value: formatNumber(f.nb_lignes_metro), sub: 'médiane locale' },
        { label: 'Lignes bus', value: formatNumber(f.nb_lignes_bus), sub: 'médiane locale' },
        { label: 'Points Vélib', value: formatNumber(f.nb_points_velib), sub: 'médiane locale' },
        { label: 'Transactions', value: formatNumber(f.nb_transactions), sub: 'ventes en 2021' },
      ],
      rows: [
        { label: 'Score accessibilité transport', value: formatNumber(f.score_accessibilite, 1) },
        { label: 'IAML brut', value: formatNumber(f.iaml_brut, 2) },
        { label: 'IAML score', value: formatNumber(f.iaml_score, 1) },
      ],
    },
  }

  const panel = panels[indicator] || { title: cfg.scoreLabel, metrics: [], rows: [] }
  const score = Number(f[scoreField] || 0)

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{cfg.scoreLabel}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 22, fontWeight: 800, color }}>{formatNumber(score)}</span>
          <span style={{ fontSize: 10, fontWeight: 600, color, background: `${color}22`, border: `1px solid ${color}44`, borderRadius: 20, padding: '2px 8px' }}>{f[labelField]}</span>
        </div>
      </div>
      <div style={{ height: 6, background: '#2e3348', borderRadius: 3, marginBottom: 16 }}>
        <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 3 }} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
        {panel.metrics.map(m => <Metric key={m.label} label={m.label} value={m.value} sub={m.sub} />)}
      </div>
      <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>{panel.title}</p>
        {panel.rows.map(r => <Row key={r.label} label={r.label} value={r.value} />)}
      </div>
    </>
  )
}

export default function FeatureDetail({ indicator, feature, onClose }) {
  if (!feature) return null

  const isIMQ = indicator === 'IMQ'
  const isITR = indicator === 'ITR'
  const color = isIMQ
    ? IMQ_COLOR(feature.score_imq_100)
    : isITR
    ? ITR_COLOR(feature.itr_score)
    : LABEL_COLOR[feature[getIndicatorConfig(indicator).labelField]] || '#8b92b8'

  const title = isIMQ ? feature.iris_nom : feature.nom_voie
  const sub   = isIMQ
    ? `${feature.arr_insee} · ${feature.arrondissement}e arrondissement`
    : `${feature.code_postal} · ${feature.arrondissement}e arrondissement`

  return (
    <div style={{ background: '#21253a', border: '1px solid #2e3348', borderRadius: 10, overflow: 'hidden', marginTop: 8 }}>
      <div style={{
        background: `linear-gradient(135deg, ${color}22, transparent)`,
        borderBottom: '1px solid #2e3348', padding: '14px 16px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
      }}>
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: '#f0f2ff', marginBottom: 2 }}>{title}</p>
          <p style={{ fontSize: 11, color: '#8b92b8' }}>{sub}</p>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#555e80', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}>×</button>
      </div>
      <div style={{ padding: 16 }}>
        {isIMQ ? <IMQDetail f={feature} /> : isITR ? <ITRDetail f={feature} /> : <GenericDetail indicator={indicator} f={feature} />}
      </div>
    </div>
  )
}
