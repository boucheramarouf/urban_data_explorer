import React from 'react'

const IMQ_COLOR = (s) => s > 66 ? '#ef4444' : s > 33 ? '#f59e0b' : '#22c55e'
const ITR_COLOR = (s) => s <= 20 ? '#22c55e' : s <= 40 ? '#84cc16' : s <= 60 ? '#eab308' : s <= 80 ? '#f97316' : '#ef4444'

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
        <Metric label="Transactions"  value={f.nb_transactions}                                            sub="ventes" />
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

export default function FeatureDetail({ indicator, feature, onClose }) {
  if (!feature) return null
  const isIMQ = indicator === 'IMQ'
  const color = isIMQ ? IMQ_COLOR(feature.score_imq_100) : ITR_COLOR(feature.itr_score)
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
        {isIMQ ? <IMQDetail f={feature} /> : <ITRDetail f={feature} />}
      </div>
    </div>
  )
}
