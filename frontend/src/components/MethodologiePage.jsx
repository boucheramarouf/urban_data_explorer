import React from 'react'

const PIPELINE = [
  {
    layer: 'Bronze',
    accentColor: '#b45309',
    bgColor: '#fef3c7',
    borderColor: '#fcd34d',
    title: 'Ingestion brute',
    desc: 'Les fichiers sources sont lus tels quels et sauvegardés en Parquet sans transformation. Cette couche garantit la traçabilité et la reproductibilité de la chaîne.',
    items: ['DVF+ — GeoPackage (mutations immobilières)', 'SIRENE — CSV.GZ (établissements actifs)', 'LOVAC — Excel (logements vacants)', 'Filosofi — CSV (revenus IRIS)', 'IRIS IGN — GeoJSON (découpage géographique)', 'GTFS IDF Mobilités (réseau transports)'],
  },
  {
    layer: 'Silver',
    accentColor: '#475569',
    bgColor: '#f1f5f9',
    borderColor: '#cbd5e1',
    title: 'Nettoyage & enrichissement',
    desc: 'Les données brutes sont filtrées sur Paris (coddep = 75), nettoyées, typées et enrichies par jointure géographique. Les agrégations à l\'échelle IRIS ou rue sont calculées ici.',
    items: ['Filtrage Paris (département 75)', 'Jointures géographiques IRIS & rue', 'Normalisation des types et encodages', 'Agrégation des transactions par IRIS', 'Calcul des distributions et percentiles', 'Fusion multimodale (GTFS + OSM)'],
  },
  {
    layer: 'Gold',
    accentColor: '#92400e',
    bgColor: '#fffbeb',
    borderColor: '#fbbf24',
    title: 'Indicateurs composites',
    desc: 'Les scores finaux sont calculés par combinaison pondérée de plusieurs dimensions silver. Chaque indicateur est normalisé sur 100 et accompagné d\'une interprétation qualitative.',
    items: ['IMQ — Indice de Mutation de Quartier (IRIS)', 'ITR — Indice de Tension Résidentielle (rue)', 'SVP — Score de Verdure et Proximité (rue)', 'IAML — Accessibilité Multimodale au Logement (rue)', 'Export Parquet & GeoJSON', 'Chargement API au démarrage'],
  },
]

const STACK = [
  { cat: 'Pipeline', items: ['Python 3.11', 'Pandas / GeoPandas', 'SQLAlchemy / psycopg', 'PyArrow (Parquet)'] },
  { cat: 'Stockage', items: ['PostgreSQL 16 (données tabulaires)', 'MongoDB 7 (données documentaires)', 'Parquet local (couches intermédiaires)'] },
  { cat: 'API', items: ['FastAPI (Python)', 'Uvicorn (ASGI)', 'GeoJSON natif', 'Docker / Docker Compose'] },
  { cat: 'Frontend', items: ['React 18', 'MapLibre GL JS 4', 'Vite', 'Inter + Cormorant Garamond'] },
]

function PipelineCard({ step, isLast }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, flex: 1 }}>
      <div style={{
        flex: 1, background: step.bgColor, border: `1.5px solid ${step.borderColor}`,
        borderRadius: 12, padding: '24px 22px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <span style={{
            background: step.accentColor, color: '#fff',
            fontFamily: 'Cormorant Garamond, serif', fontWeight: 700, fontSize: 13,
            padding: '3px 10px', borderRadius: 20, letterSpacing: '0.04em',
          }}>
            {step.layer}
          </span>
          <span style={{ fontWeight: 600, fontSize: 15, color: '#1A1511' }}>{step.title}</span>
        </div>
        <p style={{ fontSize: 13, color: '#6A5E52', lineHeight: 1.65, marginBottom: 16 }}>{step.desc}</p>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
          {step.items.map((item, i) => (
            <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: '#1A1511' }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: step.accentColor, flexShrink: 0, marginTop: 5 }} />
              {item}
            </li>
          ))}
        </ul>
      </div>
      {!isLast && (
        <div style={{ display: 'flex', alignItems: 'center', paddingTop: 32, flexShrink: 0, width: 36 }}>
          <svg width="36" height="16" viewBox="0 0 36 16" fill="none">
            <line x1="0" y1="8" x2="28" y2="8" stroke="#D1C8BB" strokeWidth="1.5" strokeDasharray="4 3" />
            <polygon points="26,4 36,8 26,12" fill="#D1C8BB" />
          </svg>
        </div>
      )}
    </div>
  )
}

export default function MethodologiePage() {
  return (
    <div style={{ paddingTop: 'var(--nav-h)', minHeight: '100vh', background: 'var(--bg)' }}>

      {/* Hero */}
      <div style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '52px 0 44px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 32px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 14 }}>
            Architecture du projet
          </p>
          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 46, fontWeight: 700, color: 'var(--text)', lineHeight: 1.15, marginBottom: 18 }}>
            Méthodologie
          </h1>
          <p style={{ fontSize: 16, color: 'var(--text-2)', lineHeight: 1.75, maxWidth: 640 }}>
            Urban Data Explorer s'appuie sur une architecture médaillon en trois couches — Bronze, Silver, Gold — pour produire des indicateurs urbains composites à l'échelle du quartier et de la rue à Paris.
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 32px' }}>

        {/* Pipeline */}
        <section style={{ marginBottom: 56 }}>
          <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 28, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
            Pipeline de données
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-2)', marginBottom: 28, lineHeight: 1.6 }}>
            Chaque couche enrichit les données de la précédente, de l'ingestion brute jusqu'aux indicateurs prêts à être exposés via l'API.
          </p>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0 }}>
            {PIPELINE.map((step, i) => (
              <PipelineCard key={step.layer} step={step} isLast={i === PIPELINE.length - 1} />
            ))}
          </div>

          {/* Arrow to API */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 20, padding: '16px 22px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10 }}>
            <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
              <line x1="0" y1="6" x2="18" y2="6" stroke="#D1C8BB" strokeWidth="1.5" />
              <polygon points="16,2 24,6 16,10" fill="#D1C8BB" />
            </svg>
            <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>API</span>
                <p style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 2 }}>FastAPI charge les Parquet Gold au démarrage et expose des endpoints GeoJSON filtrables par arrondissement</p>
              </div>
              <div style={{ width: 1, background: 'var(--border)' }} />
              <div>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Frontend</span>
                <p style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 2 }}>React + MapLibre GL JS consomme l'API pour afficher les indicateurs sur carte interactive</p>
              </div>
            </div>
          </div>
        </section>

        {/* IRIS grain */}
        <section style={{ marginBottom: 56 }}>
          <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 28, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
            Granularité géographique
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { level: 'IRIS', indicator: 'IMQ', desc: 'Les ~870 IRIS parisiens constituent la maille de base pour l\'IMQ. Chaque IRIS regroupe 2 000 à 5 000 habitants, correspondant à un sous-quartier. Le découpage est fourni par l\'IGN via le produit CONTOUR+.' },
              { level: 'Rue', indicator: 'ITR · SVP · IAML', desc: 'Les trois autres indicateurs sont calculés à la rue (tronçon de voirie). Cette granularité fine permet d\'identifier des disparités infra-quartier invisibles à l\'échelle IRIS.' },
            ].map(row => (
              <div key={row.level} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, padding: '22px 24px' }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
                  <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 20, fontWeight: 700, color: 'var(--text)' }}>{row.level}</span>
                  <span style={{ fontSize: 11, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 20, padding: '2px 10px', color: 'var(--accent)', fontWeight: 600 }}>{row.indicator}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.65 }}>{row.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Tech stack */}
        <section>
          <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 28, fontWeight: 700, color: 'var(--text)', marginBottom: 20 }}>
            Stack technique
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
            {STACK.map(col => (
              <div key={col.cat} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: '18px 18px' }}>
                <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--accent)', marginBottom: 12 }}>{col.cat}</p>
                <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 7 }}>
                  {col.items.map((item, i) => (
                    <li key={i} style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.4 }}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
