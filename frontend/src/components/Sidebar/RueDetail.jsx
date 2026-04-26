import React from 'react'

const LABEL_COLOR = {
  'Très faible': '#22c55e',
  'Faible':      '#84cc16',
  'Modéré':      '#eab308',
  'Bon':         '#f97316',
  'Excellent':   '#ef4444',
}

const Metric = ({ label, value, sub }) => (
  <div style={{
    background: '#1a1d27',
    border: '1px solid #2e3348',
    borderRadius: 8,
    padding: '10px 12px',
  }}>
    <p style={{ fontSize: 10, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</p>
    <p style={{ fontSize: 16, fontWeight: 700, color: '#f0f2ff' }}>{value}</p>
    {sub && <p style={{ fontSize: 10, color: '#8b92b8', marginTop: 2 }}>{sub}</p>}
  </div>
)

const Component = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #1a1d27' }}>
    <span style={{ fontSize: 12, color: '#8b92b8' }}>{label}</span>
    <span style={{ fontSize: 13, fontWeight: 600, color: color || '#f0f2ff' }}>{value}</span>
  </div>
)

export default function RueDetail({ rue, onClose }) {
  if (!rue) return null
  const color = LABEL_COLOR[rue.itr_label] || '#8b92b8'

  return (
    <div style={{
      background: '#21253a',
      border: '1px solid #2e3348',
      borderRadius: 10,
      overflow: 'hidden',
      marginTop: 8,
    }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(135deg, ${color}22, transparent)`,
        borderBottom: '1px solid #2e3348',
        padding: '14px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
      }}>
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: '#f0f2ff', marginBottom: 2 }}>IRIS {rue.code_iris}</p>
          <p style={{ fontSize: 11, color: '#8b92b8' }}>{rue.code_postal} · {rue.arrondissement}e arrondissement</p>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#555e80', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}>×</button>
      </div>

      <div style={{ padding: 16 }}>
        {/* Score */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Score SVP</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 22, fontWeight: 800, color }}>
                {rue.svp_score}
              </span>
              <span style={{
                fontSize: 10, fontWeight: 600, color,
                background: color + '22',
                border: `1px solid ${color}44`,
                borderRadius: 20,
                padding: '2px 8px',
              }}>{rue.svp_label}</span>
            </div>
          </div>
          <div style={{ height: 6, background: '#2e3348', borderRadius: 3 }}>
            <div style={{ height: '100%', width: `${rue.svp_score}%`, background: color, borderRadius: 3 }} />
          </div>
        </div>

        {/* Métriques clés */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
          <Metric label="Arbres" value={rue.nb_arbres.toLocaleString('fr-FR')} sub="dans le rayon" />
          <Metric label="Espaces verts" value={rue.nb_espaces_verts.toLocaleString('fr-FR')} sub="dans le rayon" />
          <Metric label="Score vert" value={`${Math.round(rue.score_vert * 100)}/100`} sub="normalisé" />
          <Metric label="Score alim." value={`${Math.round(rue.score_acces_alim * 100)}/100`} sub="normalisé" />
        </div>

        {/* Composantes SVP */}
        <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
          <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>
            Composantes SVP
          </p>
          <Component label="Score vert (60%)" value={(rue.score_vert || 0).toFixed(3)} color="#c8cde8" />
          <Component label="Score accès alimentaire (40%)" value={(rue.score_acces_alim || 0).toFixed(3)} color="#c8cde8" />
          <Component label="Score final" value={(rue.svp_score || 0).toFixed(1)} color={color} />
        </div>
      </div>
    </div>
  )
}