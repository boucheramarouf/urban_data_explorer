import React, { useState } from 'react'

const INDICATORS = [
  {
    key: 'IMQ',
    full: 'Indice de Mutation de Quartier',
    accentColor: '#d97706',
    bgColor: '#fffbeb',
    grain: 'IRIS',
    summary: 'Mesure le degré de transformation socio-économique et immobilière d\'un quartier parisien. Un score élevé signale une mutation en cours : hausse des prix, dynamisme commercial, rotation résidentielle.',
    sources: ['DVF+ (transactions)', 'SIRENE (commerces)', 'Filosofi (revenus)', 'LOVAC (vacance)'],
    dimensions: [
      { name: 'Volume transactionnel', weight: '25 %', desc: 'Nombre de mutations DVF par IRIS normalisé sur la surface bâtie. Capte l\'intensité de la rotation du parc immobilier.' },
      { name: 'Évolution des prix au m²', weight: '30 %', desc: 'Variation du prix médian par m² sur 5 ans (DVF). Indicateur direct de la pression de valorisation immobilière.' },
      { name: 'Diversité commerciale', weight: '20 %', desc: 'Indice de diversité des catégories SIRENE actives. Capte la vitalité et l\'attractivité de l\'offre commerciale locale.' },
      { name: 'Taux de vacance résidentielle', weight: '15 %', desc: 'Part des logements vacants taxés (LOVAC) sur le parc total estimé. Un taux faible accompagne souvent la mutation.' },
      { name: 'Niveau de revenu médian', weight: '10 %', desc: 'Revenu médian par unité de consommation (Filosofi 2021). Le niveau de revenu contextualise la nature de la mutation.' },
    ],
    labels: [
      { label: 'Stable', color: '#16a34a', range: '0 – 33', desc: 'Quartier peu transformé, dynamiques immobilières et commerciales modérées.' },
      { label: 'Mutation modérée', color: '#d97706', range: '34 – 66', desc: 'Signes de transformation visibles, évolution en cours.' },
      { label: 'Mutation forte', color: '#dc2626', range: '67 – 100', desc: 'Transformation intense : hausse des prix marquée, renouvellement rapide.' },
    ],
  },
  {
    key: 'ITR',
    full: 'Indice de Tension Résidentielle',
    accentColor: '#dc2626',
    bgColor: '#fef2f2',
    grain: 'Rue',
    summary: 'Quantifie la tension du marché immobilier à l\'échelle de la rue. Combine le niveau de prix absolus et leur vitesse de hausse pour identifier les rues les plus sous pression.',
    sources: ['DVF+ (transactions immobilières)'],
    dimensions: [
      { name: 'Prix médian au m²', weight: '50 %', desc: 'Prix médian des transactions DVF sur la rue ou dans un buffer de 150 m. Exprimé en percentile parisien.' },
      { name: 'Variation du prix sur 5 ans', weight: '30 %', desc: 'Évolution annualisée du prix médian par m² entre 2018 et 2023. Capte la dynamique récente de valorisation.' },
      { name: 'Densité transactionnelle', weight: '20 %', desc: 'Nombre de transactions par 100 m de tronçon sur la période. Reflète la liquidité du marché de la rue.' },
    ],
    labels: [
      { label: 'Très accessible', color: '#16a34a', range: '0 – 20', desc: 'Marché peu actif, prix sous la médiane parisienne.' },
      { label: 'Accessible', color: '#65a30d', range: '21 – 40', desc: 'Tension contenue, marché fluide.' },
      { label: 'Modéré', color: '#d97706', range: '41 – 60', desc: 'Tension intermédiaire, autour de la médiane parisienne.' },
      { label: 'Tendu', color: '#ea580c', range: '61 – 80', desc: 'Marché sous pression, prix en hausse soutenue.' },
      { label: 'Très tendu', color: '#dc2626', range: '81 – 100', desc: 'Secteur parmi les plus chers et les plus dynamiques de Paris.' },
    ],
  },
  {
    key: 'SVP',
    full: 'Score de Verdure et Proximité',
    accentColor: '#16a34a',
    bgColor: '#f0fdf4',
    grain: 'Rue',
    summary: 'Évalue l\'accessibilité aux espaces verts depuis chaque rue parisienne. Prend en compte la proximité aux parcs, jardins et coulées vertes, ainsi que le couvert arboré.',
    sources: ['OpenStreetMap (espaces verts, arbres)', 'IRIS IGN (emprise de référence)'],
    dimensions: [
      { name: 'Distance au parc le plus proche', weight: '40 %', desc: 'Distance à pied au jardin ou parc public le plus proche (OSM). Transformée en score décroissant avec la distance.' },
      { name: 'Superficie des espaces verts accessibles', weight: '35 %', desc: 'Surface cumulée des espaces verts dans un rayon de 500 m. Capte la richesse globale de l\'environnement vert.' },
      { name: 'Densité d\'arbres de rue', weight: '25 %', desc: 'Nombre d\'arbres d\'alignement OSM par 100 m de tronçon. Indicateur de verdure immédiate de la rue.' },
    ],
    labels: [
      { label: 'Très faible', color: '#dc2626', range: '0 – 20', desc: 'Environnement très minéral, peu d\'espaces verts accessibles.' },
      { label: 'Faible', color: '#ea580c', range: '21 – 40', desc: 'Accès limité à la verdure.' },
      { label: 'Modéré', color: '#d97706', range: '41 – 60', desc: 'Présence d\'espaces verts à distance raisonnable.' },
      { label: 'Bon', color: '#65a30d', range: '61 – 80', desc: 'Bonne accessibilité aux espaces verts.' },
      { label: 'Excellent', color: '#16a34a', range: '81 – 100', desc: 'Très forte densité de verdure, parcs et arbres à proximité immédiate.' },
    ],
  },
  {
    key: 'IAML',
    full: "Indice d'Accessibilité Multimodale au Logement",
    accentColor: '#2563eb',
    bgColor: '#eff6ff',
    grain: 'Rue',
    summary: 'Mesure la qualité de la desserte en transports en commun depuis chaque rue. Combine l\'accès au métro/RER, aux bus et aux stations Vélib\' pour produire un score d\'accessibilité multimodale.',
    sources: ['IDF Mobilités — GTFS (métro, RER, bus)', 'Vélib\' Métropole (stations)', 'OSM (voirie, isophones)', 'IRIS IGN (référentiel géographique)'],
    dimensions: [
      { name: 'Accès métro / RER', weight: '40 %', desc: 'Distance à la station métro ou RER la plus proche. Pondérée par le nombre de lignes et la fréquence (GTFS IDF Mobilités).' },
      { name: 'Couverture bus', weight: '30 %', desc: 'Nombre d\'arrêts de bus dans un rayon de 300 m et fréquence des passages. Capte la capillarité du réseau de surface.' },
      { name: 'Proximité Vélib\'', weight: '20 %', desc: 'Distance à la station Vélib\' la plus proche et capacité moyenne de la station.' },
      { name: 'Connectivité piétonne', weight: '10 %', desc: 'Densité du réseau piéton autour du tronçon (OSM). Capte la facilité de connexion aux arrêts.' },
    ],
    labels: [
      { label: 'Très accessible', color: '#16a34a', range: '0 – 20', desc: 'Desserte multimodale excellente, très proche des grandes stations.' },
      { label: 'Accessible', color: '#65a30d', range: '21 – 40', desc: 'Bonne couverture par les transports.' },
      { label: 'Modéré', color: '#d97706', range: '41 – 60', desc: 'Desserte correcte, quelques modes manquants.' },
      { label: 'Tendu', color: '#ea580c', range: '61 – 80', desc: 'Éloigné des grandes lignes, bus prépondérant.' },
      { label: 'Très tendu', color: '#dc2626', range: '81 – 100', desc: 'Faible desserte, dépendance à la marche ou au vélo.' },
    ],
  },
]

function IndicatorCard({ ind }) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 14, overflow: 'hidden', marginBottom: 20 }}>
      {/* Header */}
      <div
        style={{ padding: '24px 28px', borderBottom: `3px solid ${ind.accentColor}`, cursor: 'pointer', userSelect: 'none' }}
        onClick={() => setOpen(o => !o)}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <span style={{
                fontFamily: 'Cormorant Garamond, serif', fontSize: 22, fontWeight: 700,
                color: '#fff', background: ind.accentColor,
                padding: '2px 14px', borderRadius: 24,
              }}>{ind.key}</span>
              <span style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--text-3)', background: 'var(--bg)', border: '1px solid var(--border)', padding: '3px 9px', borderRadius: 20 }}>
                Maille {ind.grain}
              </span>
            </div>
            <h3 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>{ind.full}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.65, maxWidth: 680 }}>{ind.summary}</p>
          </div>
          <div style={{ color: 'var(--text-3)', fontSize: 18, flexShrink: 0, marginTop: 4 }}>{open ? '−' : '+'}</div>
        </div>

        {/* Legend pills */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
          {ind.labels.map(l => (
            <span key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 20, padding: '4px 12px', fontSize: 11, fontWeight: 500, color: 'var(--text)' }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: l.color, flexShrink: 0 }} />
              {l.label}
            </span>
          ))}
        </div>
      </div>

      {/* Detail (expandable) */}
      {open && (
        <div style={{ padding: '24px 28px', background: ind.bgColor }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            {/* Dimensions */}
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: ind.accentColor, marginBottom: 14 }}>Dimensions du score</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {ind.dimensions.map(dim => (
                  <div key={dim.name} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 9, padding: '14px 16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{dim.name}</span>
                      <span style={{ fontSize: 12, fontWeight: 700, color: ind.accentColor, flexShrink: 0, marginLeft: 8 }}>{dim.weight}</span>
                    </div>
                    <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.55 }}>{dim.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Labels + Sources */}
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: ind.accentColor, marginBottom: 14 }}>Interprétation</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 24 }}>
                {ind.labels.map(l => (
                  <div key={l.label} style={{ display: 'flex', gap: 12, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', alignItems: 'flex-start' }}>
                    <div style={{ flexShrink: 0, textAlign: 'center', minWidth: 48 }}>
                      <span style={{ display: 'block', width: 10, height: 10, borderRadius: '50%', background: l.color, margin: '3px auto 4px' }} />
                      <span style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 600 }}>{l.range}</span>
                    </div>
                    <div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: l.color, display: 'block', marginBottom: 2 }}>{l.label}</span>
                      <span style={{ fontSize: 11, color: 'var(--text-2)', lineHeight: 1.5 }}>{l.desc}</span>
                    </div>
                  </div>
                ))}
              </div>

              <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: ind.accentColor, marginBottom: 10 }}>Sources utilisées</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {ind.sources.map(s => (
                  <span key={s} style={{ fontSize: 11, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, padding: '4px 10px', color: 'var(--text-2)' }}>{s}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function IndicateursPage() {
  return (
    <div style={{ paddingTop: 'var(--nav-h)', minHeight: '100vh', background: 'var(--bg)' }}>

      {/* Hero */}
      <div style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '52px 0 44px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 32px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 14 }}>
            Méthode de calcul
          </p>
          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 46, fontWeight: 700, color: 'var(--text)', lineHeight: 1.15, marginBottom: 18 }}>
            Les indicateurs
          </h1>
          <p style={{ fontSize: 16, color: 'var(--text-2)', lineHeight: 1.75, maxWidth: 680 }}>
            Quatre indicateurs composites décrivent Paris sous des angles complémentaires : dynamique immobilière, tension du marché résidentiel, accès à la nature et desserte en transports. Cliquez sur un indicateur pour détailler ses dimensions.
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 32px' }}>
        {INDICATORS.map(ind => <IndicatorCard key={ind.key} ind={ind} />)}
      </div>
    </div>
  )
}
