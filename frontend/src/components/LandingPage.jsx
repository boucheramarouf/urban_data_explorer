import React, { useEffect, useState } from 'react'

const STATS = [
  { value: '992',     label: 'IRIS analysés' },
  { value: '4',       label: 'indices composites' },
  { value: '12',      label: 'sources ouvertes' },
  { value: '2018–25', label: 'profondeur historique' },
]

const LIVE_EXAMPLES = [
  { lieu: 'Paris 4e · Saint-Paul',  label: 'Mutation modérée', score: 52.4, color: '#d97706' },
  { lieu: 'Paris 11e · Belleville', label: 'Mutation forte',   score: 68.9, color: '#dc2626' },
  { lieu: 'Paris 16e · Auteuil',    label: 'Stable',           score: 28.6, color: '#16a34a' },
]

// Decorative Paris-like map preview (stylized circles)
const IRIS_DOTS = [
  { x: 50, y: 42, r: 18, color: '#16a34a', op: 0.75 },
  { x: 74, y: 38, r: 14, color: '#d97706', op: 0.70 },
  { x: 62, y: 55, r: 22, color: '#dc2626', op: 0.70 },
  { x: 38, y: 55, r: 16, color: '#16a34a', op: 0.65 },
  { x: 84, y: 52, r: 12, color: '#d97706', op: 0.60 },
  { x: 28, y: 45, r: 14, color: '#dc2626', op: 0.55 },
  { x: 55, y: 70, r: 13, color: '#16a34a', op: 0.65 },
  { x: 68, y: 68, r: 16, color: '#d97706', op: 0.60 },
  { x: 42, y: 68, r: 11, color: '#16a34a', op: 0.55 },
  { x: 80, y: 65, r: 10, color: '#dc2626', op: 0.50 },
  { x: 22, y: 60, r: 12, color: '#d97706', op: 0.50 },
  { x: 58, y: 82, r: 9,  color: '#16a34a', op: 0.45 },
]

function MapPreview() {
  return (
    <div style={{
      position: 'relative', width: '100%', height: '100%',
      background: '#F7F3EC', borderRadius: 16,
      border: '1px solid var(--border)', overflow: 'hidden',
    }}>
      {/* Grid lines */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
        {[20, 40, 60, 80].map(p => (
          <React.Fragment key={p}>
            <line x1={`${p}%`} y1="0" x2={`${p}%`} y2="100%" stroke="#DDD8CF" strokeWidth="0.5"/>
            <line x1="0" y1={`${p}%`} x2="100%" y2={`${p}%`} stroke="#DDD8CF" strokeWidth="0.5"/>
          </React.Fragment>
        ))}
        {/* Circles */}
        {IRIS_DOTS.map((d, i) => (
          <circle key={i} cx={`${d.x}%`} cy={`${d.y}%`} r={d.r} fill={d.color} opacity={d.op} />
        ))}
        {/* Connections */}
        {IRIS_DOTS.slice(0, 8).map((d, i) => {
          const next = IRIS_DOTS[(i + 1) % 8]
          return <line key={i} x1={`${d.x}%`} y1={`${d.y}%`} x2={`${next.x}%`} y2={`${next.y}%`} stroke="var(--border)" strokeWidth="0.8" opacity="0.6"/>
        })}
      </svg>

      {/* Compass */}
      <div style={{ position: 'absolute', bottom: 16, right: 16 }}>
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="13" stroke="var(--border)" strokeWidth="1"/>
          <path d="M14 3 L16 13 L14 11 L12 13 Z" fill="var(--text)" opacity="0.6"/>
          <path d="M14 25 L16 15 L14 17 L12 15 Z" fill="var(--text-3)" opacity="0.4"/>
        </svg>
      </div>

      {/* PARIS label */}
      <div style={{ position: 'absolute', top: 16, left: '50%', transform: 'translateX(-50%)' }}>
        <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.2em', textTransform: 'uppercase' }}>PARIS</p>
      </div>
    </div>
  )
}

export default function LandingPage({ onNavigate }) {
  const [liveIdx, setLiveIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setLiveIdx(i => (i + 1) % LIVE_EXAMPLES.length), 3000)
    return () => clearInterval(t)
  }, [])

  const live = LIVE_EXAMPLES[liveIdx]

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', paddingTop: 'var(--nav-h)' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 40px' }}>

        {/* Hero */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 60, alignItems: 'center', minHeight: 'calc(100vh - var(--nav-h))', paddingBottom: 60 }}>

          {/* Left — Text */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 28 }}>
              Atlas de la qualité urbaine · 2024
            </p>

            <h1 style={{ fontFamily: 'DM Serif Display, serif', fontSize: 'clamp(48px, 6vw, 72px)', lineHeight: 1.08, color: 'var(--text)', marginBottom: 24 }}>
              Lire la ville,<br />
              <span style={{ fontStyle: 'italic', color: 'var(--accent)' }}>rue par rue.</span>
            </h1>

            <p style={{ fontSize: 16, lineHeight: 1.7, color: 'var(--text-2)', maxWidth: 460, marginBottom: 40 }}>
              Une plateforme d'analyse territoriale qui agrège les données ouvertes de la Ville de Paris, de l'INSEE et de l'APUR pour révéler les dynamiques de mutation, de tension résidentielle et de qualité de vie à l'échelle du quartier.
            </p>

            <button
              onClick={() => onNavigate('carte')}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 10,
                background: 'var(--text)', color: 'var(--bg)',
                border: 'none', borderRadius: 8,
                padding: '14px 28px', fontSize: 14, fontWeight: 600,
                cursor: 'pointer', transition: 'all 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#2c2925'}
              onMouseLeave={e => e.currentTarget.style.background = 'var(--text)'}
            >
              Explorer la cartographie
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            {/* Stats row */}
            <div style={{ display: 'flex', gap: 32, marginTop: 56, paddingTop: 32, borderTop: '1px solid var(--border)' }}>
              {STATS.map(s => (
                <div key={s.label}>
                  <p style={{ fontFamily: 'DM Serif Display, serif', fontSize: 28, color: 'var(--text)', lineHeight: 1 }}>{s.value}</p>
                  <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{s.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right — Map preview */}
          <div style={{ position: 'relative', height: 480 }}>
            <MapPreview />

            {/* EN DIRECT card */}
            <div style={{
              position: 'absolute', bottom: 24, left: 24,
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: 12, padding: '14px 18px',
              boxShadow: 'var(--shadow-md)',
              minWidth: 200,
              transition: 'all 0.4s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#16a34a', animation: 'pulse 2s infinite' }} />
                <p style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>En direct</p>
              </div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 3 }}>{live.lieu}</p>
              <p style={{ fontSize: 11, color: live.color, fontWeight: 500 }}>{live.label} · {live.score}/100</p>
            </div>
          </div>
        </div>

        {/* Feature cards row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, paddingBottom: 80 }}>
          {[
            { key: 'IMQ', label: 'Indice de Mutation de Quartier', desc: 'Dynamiques de transformation immobilière et commerciale par IRIS', color: '#d97706' },
            { key: 'ITR', label: 'Indice de Tension Résidentielle', desc: 'Pression sur le marché du logement rue par rue', color: '#dc2626' },
            { key: 'SVP', label: 'Score de Verdure et Proximité', desc: 'Accès à la nature et aux commerces de proximité', color: '#16a34a' },
            { key: 'IAML', label: "Accessibilité Multimodale", desc: 'Desserte en transports en commun et mobilités douces', color: '#2563eb' },
          ].map(ind => (
            <button
              key={ind.key}
              onClick={() => onNavigate('carte')}
              style={{
                background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12,
                padding: '20px 20px 18px', cursor: 'pointer', textAlign: 'left',
                transition: 'all 0.15s', boxShadow: 'var(--shadow-sm)',
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = ind.color; e.currentTarget.style.boxShadow = 'var(--shadow-md)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: ind.color, background: ind.color + '18', borderRadius: 4, padding: '3px 7px', letterSpacing: '0.05em' }}>{ind.key}</span>
              </div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 6, lineHeight: 1.3 }}>{ind.label}</p>
              <p style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 }}>{ind.desc}</p>
            </button>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.85); }
        }
      `}</style>
    </div>
  )
}
