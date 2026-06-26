import React from 'react'

const SOURCES = [
  {
    abbr: 'DVF+',
    full: 'Demandes de Valeurs Foncières enrichies',
    org: 'Ministère de l\'Économie — data.gouv.fr',
    desc: 'Base exhaustive des transactions immobilières en France. Chaque mutation contient l\'adresse, la surface, le type de bien, le prix de vente et la date. La version enrichie (DVF+) intègre des géolocalisations précises à la parcelle.',
    coverage: 'France entière · 2018 – 2023',
    usedFor: ['IMQ — volume et prix des mutations', 'ITR — score de tension par rue'],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#d97706',
  },
  {
    abbr: 'SIRENE',
    full: 'Système national d\'Identification et du Répertoire des Entreprises et de leurs Établissements',
    org: 'INSEE — data.gouv.fr (Géo-SIRET)',
    desc: 'Répertoire officiel de tous les établissements actifs en France, avec leur code APE (activité principale exercée) et leur géolocalisation. La version Géo-SIRET utilisée ici agrège les données par arrondissement parisien.',
    coverage: 'Paris (75) · Millésime 2023',
    usedFor: ['IMQ — diversité et densité commerciale'],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#7c3aed',
  },
  {
    abbr: 'Filosofi',
    full: 'Fichier Localisé Social et Fiscal',
    org: 'INSEE',
    desc: 'Statistiques de revenus et de niveaux de vie à l\'échelle IRIS. Contient le revenu médian par unité de consommation, le taux de pauvreté et la part des allocataires. Produit à partir du rapprochement des fichiers fiscaux et des données sociales.',
    coverage: 'France métropolitaine · Millésime 2021',
    usedFor: ['IMQ — niveau de revenu médian par IRIS'],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#059669',
  },
  {
    abbr: 'LOVAC',
    full: 'Logements Vacants',
    org: 'DHUP / DGALN — data.gouv.fr',
    desc: 'Recense les logements considérés comme vacants au sens fiscal (vacants depuis plus de 2 ans et soumis à la taxe sur les logements vacants). Données issues des fichiers fiscaux de la DGFIP, agrégées à la commune.',
    coverage: 'France · 2020 – 2025',
    usedFor: ['IMQ — taux de vacance résidentielle'],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#dc2626',
  },
  {
    abbr: 'IRIS IGN',
    full: 'Îlots Regroupés pour l\'Information Statistique — Contours',
    org: 'INSEE / IGN — Géoplateforme',
    desc: 'Découpage infracommunal produit par l\'INSEE pour diffuser les statistiques à une échelle fine. Chaque IRIS regroupe entre 1 800 et 5 000 habitants. Paris compte environ 870 IRIS. Les contours géographiques sont fournis par l\'IGN via le produit CONTOUR+.',
    coverage: 'France entière · 2023',
    usedFor: ['Référentiel géographique — tous indicateurs', 'Jointure DVF, Filosofi, LOVAC'],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#1d4e6b',
  },
  {
    abbr: 'OSM',
    full: 'OpenStreetMap',
    org: 'Contributeurs OpenStreetMap — OpenStreetMap Foundation',
    desc: 'Base de données géographiques collaborative mondiale. Utilisée pour extraire les espaces verts (parcs, jardins, squares), les arbres d\'alignement et le réseau viaire parisien, via des requêtes Overpass API ciblées sur Paris.',
    coverage: 'Paris (bbox) · Extraction avril 2024',
    usedFor: ['SVP — espaces verts et couvert arboré', 'IAML — réseau piéton et connectivité'],
    license: 'ODbL (Open Database Licence)',
    color: '#16a34a',
  },
  {
    abbr: 'GTFS IDF',
    full: 'General Transit Feed Specification — Île-de-France',
    org: 'Île-de-France Mobilités — data.iledefrance-mobilites.fr',
    desc: 'Données complètes du réseau de transport en commun francilien au format GTFS : arrêts, lignes, horaires théoriques. Couvre métro, RER, Transilien, bus, tramway. Complété par les données des stations Vélib\' Métropole.',
    coverage: 'Île-de-France · 2024',
    usedFor: ['IAML — accès métro/RER, couverture bus, stations Vélib\''],
    license: 'Licence Ouverte Etalab 2.0',
    color: '#2563eb',
  },
]

function SourceCard({ src }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 14,
      overflow: 'hidden', display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ borderTop: `4px solid ${src.color}`, padding: '22px 24px 18px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
          <span style={{
            fontFamily: 'Cormorant Garamond, serif', fontSize: 22, fontWeight: 700, color: src.color,
          }}>{src.abbr}</span>
          <span style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-3)' }}>{src.coverage}</span>
        </div>
        <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', lineHeight: 1.4, marginBottom: 4 }}>{src.full}</p>
        <p style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 14 }}>{src.org}</p>
        <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.7, marginBottom: 16 }}>{src.desc}</p>
      </div>
      <div style={{ padding: '14px 24px 18px', background: 'var(--bg)', borderTop: '1px solid var(--border)', marginTop: 'auto' }}>
        <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-3)', marginBottom: 8 }}>
          Utilisé pour
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {src.usedFor.map(u => (
            <span key={u} style={{ display: 'flex', alignItems: 'flex-start', gap: 7, fontSize: 11, color: 'var(--text)', lineHeight: 1.4 }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: src.color, flexShrink: 0, marginTop: 4 }} />
              {u}
            </span>
          ))}
        </div>
        <p style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 12 }}>{src.license}</p>
      </div>
    </div>
  )
}

export default function SourcesPage() {
  return (
    <div style={{ paddingTop: 'var(--nav-h)', minHeight: '100vh', background: 'var(--bg)' }}>

      {/* Hero */}
      <div style={{ background: 'var(--bg-card)', borderBottom: '1px solid var(--border)', padding: '52px 0 44px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto', padding: '0 32px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 14 }}>
            Données ouvertes
          </p>
          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 46, fontWeight: 700, color: 'var(--text)', lineHeight: 1.15, marginBottom: 18 }}>
            Sources de données
          </h1>
          <p style={{ fontSize: 16, color: 'var(--text-2)', lineHeight: 1.75, maxWidth: 680 }}>
            Urban Data Explorer est entièrement fondé sur des données publiques et ouvertes. Toutes les sources proviennent de producteurs institutionnels (État, collectivités, organisations internationales) et sont accessibles librement sur les plateformes open data françaises.
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 960, margin: '0 auto', padding: '48px 32px' }}>

        {/* Summary row */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 40, flexWrap: 'wrap' }}>
          {[
            { label: '7 sources', sub: 'de données ouvertes' },
            { label: '100 %', sub: 'open data institutionnel' },
            { label: 'Paris', sub: 'département 75 · ~870 IRIS' },
            { label: '2018 – 2024', sub: 'période couverte' },
          ].map(stat => (
            <div key={stat.label} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 22px' }}>
              <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 2 }}>{stat.label}</p>
              <p style={{ fontSize: 11, color: 'var(--text-3)' }}>{stat.sub}</p>
            </div>
          ))}
        </div>

        {/* Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
          {SOURCES.map(src => <SourceCard key={src.abbr} src={src} />)}
        </div>

        {/* Note */}
        <div style={{ marginTop: 36, padding: '18px 24px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10 }}>
          <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--text)' }}>Note sur les licences.</strong> Les données Etalab (Licence Ouverte 2.0) autorisent la réutilisation, la transformation et la diffusion, y compris à des fins commerciales, sous réserve de mentionner la source. Les données OSM sont sous ODbL : toute utilisation dérivée doit rester sous la même licence. Le GTFS IDF Mobilités est distribué sous Licence Ouverte 2.0.
          </p>
        </div>
      </div>
    </div>
  )
}
