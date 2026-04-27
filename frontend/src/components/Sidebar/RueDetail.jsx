import React from 'react'
import { getIndicatorConfig } from '../../utils/indicatorConfig.js'

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

const Metric = ({ label, value, sub }) => (
  <div
    style={{
      background: '#1a1d27',
      border: '1px solid #2e3348',
      borderRadius: 8,
      padding: '10px 12px',
    }}
  >
    <p style={{ fontSize: 10, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</p>
    <p style={{ fontSize: 16, fontWeight: 700, color: '#f0f2ff' }}>{value}</p>
    {sub && <p style={{ fontSize: 10, color: '#8b92b8', marginTop: 2 }}>{sub}</p>}
  </div>
)

const Component = ({ label, value, color }) => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '6px 0',
      borderBottom: '1px solid #1a1d27',
    }}
  >
    <span style={{ fontSize: 12, color: '#8b92b8' }}>{label}</span>
    <span style={{ fontSize: 13, fontWeight: 600, color: color || '#f0f2ff' }}>{value}</span>
  </div>
)

export default function RueDetail({ indicator, rue, onClose }) {
  if (!rue) return null

  const cfg = getIndicatorConfig(indicator)
  const scoreField = cfg.scoreField
  const labelField = cfg.labelField
  const color = LABEL_COLOR[rue[labelField]] || '#8b92b8'

  return (
    <div
      style={{
        background: '#21253a',
        border: '1px solid #2e3348',
        borderRadius: 10,
        overflow: 'hidden',
        marginTop: 8,
      }}
    >
      <div
        style={{
          background: `linear-gradient(135deg, ${color}22, transparent)`,
          borderBottom: '1px solid #2e3348',
          padding: '14px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: '#f0f2ff', marginBottom: 2 }}>{rue.nom_voie}</p>
          <p style={{ fontSize: 11, color: '#8b92b8' }}>
            {rue.code_postal} · {rue.arrondissement}e arrondissement
          </p>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#555e80', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}>
          ×
        </button>
      </div>

      <div style={{ padding: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: '#8b92b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {cfg.scoreLabel}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 22, fontWeight: 800, color }}>{rue[scoreField]}</span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  color,
                  background: `${color}22`,
                  border: `1px solid ${color}44`,
                  borderRadius: 20,
                  padding: '2px 8px',
                }}
              >
                {rue[labelField]}
              </span>
            </div>
          </div>
          <div style={{ height: 6, background: '#2e3348', borderRadius: 3 }}>
            <div style={{ height: '100%', width: `${rue[scoreField]}%`, background: color, borderRadius: 3 }} />
          </div>
        </div>

        {indicator === 'itr' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              <Metric label="Prix médian" value={`${Math.round(rue.prix_m2_median || 0).toLocaleString('fr-FR')} €`} sub="par m²" />
              <Metric label="Revenu médian" value={`${Math.round((rue.revenu_median_uc || 0) / 1000).toLocaleString('fr-FR')}k €`} sub="par an / UC" />
              <Metric label="Log. sociaux" value={rue.nb_logements_sociaux > 0 ? rue.nb_logements_sociaux.toLocaleString('fr-FR') : 'Aucun'} sub="dans l'IRIS" />
              <Metric label="Transactions" value={rue.nb_transactions || 0} sub="ventes en 2021" />
            </div>

            <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
              <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>
                Composantes ITR
              </p>
              <Component label="Effort d'achat" value={Number(rue.c1_effort || 0).toFixed(3)} color="#c8cde8" />
              <Component label="Facteur logement social" value={Number(rue.c2_logsoc || 0).toFixed(3)} color="#c8cde8" />
              <Component label="Score brut" value={Number(rue.itr_brut || 0).toFixed(4)} color={color} />
            </div>
          </>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              <Metric label="Espaces verts" value={rue.nb_espaces_verts || 0} sub="dans 200 m" />
              <Metric label="Arbres" value={rue.nb_arbres || 0} sub="dans 200 m" />
              <Metric label="Score alim." value={Number(rue.score_alim_brut || 0).toFixed(1)} sub="dans 500 m" />
              <Metric label="Commerce" value={rue.has_commerce ? 'Oui' : 'Non'} sub="détection OSM" />
            </div>

            <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
              <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>
                Composantes SVP
              </p>
              <Component label="Score vert" value={Number(rue.score_vert || 0).toFixed(3)} color="#c8cde8" />
              <Component label="Accès commerces" value={Number(rue.score_acces_alim || 0).toFixed(3)} color="#c8cde8" />
              <Component label="SVP brut" value={Number(rue.svp_brut || 0).toFixed(3)} color="#c8cde8" />
              <Component label="SVP score" value={Number(rue.svp_score || 0).toFixed(1)} color={color} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
