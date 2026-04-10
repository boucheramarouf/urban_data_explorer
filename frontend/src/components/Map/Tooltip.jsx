import React from 'react'

const LABEL_COLOR = {
  'Très accessible': '#22c55e',
  'Accessible':      '#84cc16',
  'Modéré':          '#eab308',
  'Tendu':           '#f97316',
  'Très tendu':      '#ef4444',
}

export default function Tooltip({ feature, x, y }) {
  if (!feature) return null
  const p = feature.properties

  return (
    <div style={{
      position: 'fixed',
      left: x + 16,
      top: y - 8,
      background: 'rgba(21,24,36,0.97)',
      border: '1px solid #2e3348',
      borderRadius: 10,
      padding: '12px 16px',
      minWidth: 220,
      pointerEvents: 'none',
      zIndex: 999,
      backdropFilter: 'blur(12px)',
      boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
    }}>
      {/* Titre */}
      <p style={{ fontWeight: 600, fontSize: 13, color: '#f0f2ff', marginBottom: 2 }}>
        {p.nom_voie}
      </p>
      <p style={{ fontSize: 11, color: '#8b92b8', marginBottom: 10 }}>
        {p.code_postal} · arr. {p.arrondissement}
      </p>

      {/* Badge label */}
      <div style={{
        display: 'inline-block',
        background: LABEL_COLOR[p.itr_label] + '22',
        border: `1px solid ${LABEL_COLOR[p.itr_label]}55`,
        borderRadius: 20,
        padding: '2px 10px',
        marginBottom: 10,
      }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: LABEL_COLOR[p.itr_label] }}>
          {p.itr_label}
        </span>
      </div>

      {/* Score barre */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: '#8b92b8' }}>Score ITR</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: LABEL_COLOR[p.itr_label] }}>
            {p.itr_score}/100
          </span>
        </div>
        <div style={{ height: 4, background: '#2e3348', borderRadius: 2 }}>
          <div style={{
            height: '100%',
            width: `${p.itr_score}%`,
            background: LABEL_COLOR[p.itr_label],
            borderRadius: 2,
            transition: 'width 0.3s',
          }} />
        </div>
      </div>

      {/* Données clés */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px' }}>
        {[
          { label: 'Prix médian', value: `${Math.round(p.prix_m2_median).toLocaleString('fr-FR')} €/m²` },
          { label: 'Revenu médian', value: `${Math.round(p.revenu_median_uc).toLocaleString('fr-FR')} €/an` },
          { label: 'Log. sociaux', value: p.nb_logements_sociaux > 0 ? p.nb_logements_sociaux.toLocaleString('fr-FR') : 'Aucun' },
          { label: 'Ventes 2021', value: `${p.nb_transactions} trans.` },
        ].map(item => (
          <div key={item.label}>
            <p style={{ fontSize: 10, color: '#555e80', marginBottom: 1 }}>{item.label}</p>
            <p style={{ fontSize: 12, fontWeight: 500, color: '#c8cde8' }}>{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}