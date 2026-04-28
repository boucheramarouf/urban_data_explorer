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

const formatNumber = (value, digits = 0) => Number(value || 0).toLocaleString('fr-FR', { maximumFractionDigits: digits, minimumFractionDigits: digits })

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

  const panels = {
    itr: {
      title: 'Composantes ITR',
      metrics: [
        { label: 'Prix médian', value: `${formatNumber(rue.prix_m2_median)} €`, sub: 'par m²' },
        { label: 'Revenu médian', value: `${formatNumber((rue.revenu_median_uc || 0) / 1000)}k €`, sub: 'par an / UC' },
        { label: 'Log. sociaux', value: rue.nb_logements_sociaux > 0 ? formatNumber(rue.nb_logements_sociaux) : 'Aucun', sub: "dans l'IRIS" },
        { label: 'Transactions', value: formatNumber(rue.nb_transactions), sub: 'ventes en 2021' },
      ],
      components: [
        { label: "Effort d'achat", value: formatNumber(rue.c1_effort, 3), color: '#c8cde8' },
        { label: 'Facteur logement social', value: formatNumber(rue.c2_logsoc, 3), color: '#c8cde8' },
        { label: 'Score brut', value: formatNumber(rue.itr_brut, 4), color },
      ],
    },
    svp: {
      title: 'Composantes SVP',
      metrics: [
        { label: 'Espaces verts', value: formatNumber(rue.nb_espaces_verts), sub: 'dans 200 m' },
        { label: 'Arbres', value: formatNumber(rue.nb_arbres), sub: 'dans 200 m' },
        { label: 'Score alim.', value: formatNumber(rue.score_alim_brut, 1), sub: 'dans 500 m' },
        { label: 'Commerce', value: rue.has_commerce ? 'Oui' : 'Non', sub: 'détection OSM' },
      ],
      components: [
        { label: 'Score vert', value: formatNumber(rue.score_vert, 3), color: '#c8cde8' },
        { label: 'Accès commerces', value: formatNumber(rue.score_acces_alim, 3), color: '#c8cde8' },
        { label: 'SVP brut', value: formatNumber(rue.svp_brut, 3), color: '#c8cde8' },
        { label: 'SVP score', value: formatNumber(rue.svp_score, 1), color },
      ],
    },
    iaml: {
      title: 'Composantes IAML',
      metrics: [
        { label: 'Prix médian', value: `${formatNumber(rue.prix_m2_median)} €`, sub: 'par m²' },
        { label: 'Accessibilité', value: formatNumber(rue.score_accessibilite, 1), sub: 'dans 500 m' },
        { label: 'Lignes métro', value: formatNumber(rue.nb_lignes_metro), sub: 'médiane locale' },
        { label: 'Lignes bus', value: formatNumber(rue.nb_lignes_bus), sub: 'médiane locale' },
        { label: 'Points Vélib', value: formatNumber(rue.nb_points_velib), sub: 'médiane locale' },
        { label: 'Transactions', value: formatNumber(rue.nb_transactions), sub: 'ventes en 2021' },
      ],
      components: [
        { label: 'Score accessibilité transport', value: formatNumber(rue.score_accessibilite, 1), color: '#c8cde8' },
        { label: 'IAML brut', value: formatNumber(rue.iaml_brut, 2), color: '#c8cde8' },
        { label: 'IAML score', value: formatNumber(rue.iaml_score, 1), color },
      ],
    },
  }

  const panel = panels[indicator] || panels.itr

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
              <span style={{ fontSize: 22, fontWeight: 800, color }}>{formatNumber(rue[scoreField])}</span>
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
            <div style={{ height: '100%', width: `${Number(rue[scoreField] || 0)}%`, background: color, borderRadius: 3 }} />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
          {panel.metrics.map((metric) => (
            <Metric key={metric.label} label={metric.label} value={metric.value} sub={metric.sub} />
          ))}
        </div>

        <div style={{ background: '#1a1d27', borderRadius: 8, padding: '10px 14px' }}>
          <p style={{ fontSize: 11, color: '#555e80', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, fontWeight: 600 }}>
            {panel.title}
          </p>
          {panel.components.map((item) => (
            <Component key={item.label} label={item.label} value={item.value} color={item.color} />
          ))}
        </div>
      </div>
    </div>
  )
}
