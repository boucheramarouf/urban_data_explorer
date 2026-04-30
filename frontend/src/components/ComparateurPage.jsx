import React, { useEffect, useState } from 'react'

const INDICATORS = [
  { key: 'IMQ',  label: 'Indice de Mutation de Quartier', sub: 'Mutation',         color: '#d97706', statsKey: 'score_imq_median',  path: '/api/imq/stats' },
  { key: 'ITR',  label: 'Indice de Tension Résidentielle', sub: 'Tension résid.',  color: '#dc2626', statsKey: 'itr_score_median',  path: '/api/itr/stats' },
  { key: 'SVP',  label: 'Score de Verdure et Proximité',  sub: 'Vie pratique',    color: '#16a34a', statsKey: 'svp_score_median',  path: '/api/svp/stats' },
  { key: 'IAML', label: "Accessibilité Multimodale",       sub: 'Multimodal',      color: '#2563eb', statsKey: 'iaml_score_median', path: '/api/iaml/stats' },
]

function scoreColor(score) {
  if (score >= 70) return '#dc2626'
  if (score >= 45) return '#d97706'
  return '#16a34a'
}

function ScoreBar({ score, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6 }}>
      <div style={{ flex: 1, height: 3, background: 'var(--border)', borderRadius: 2 }}>
        <div style={{ height: '100%', width: `${score || 0}%`, background: color, borderRadius: 2, transition: 'width 0.6s ease' }} />
      </div>
      <span style={{ fontSize: 11, color: 'var(--text-3)', minWidth: 28 }}>{(score || 0).toFixed(1)}</span>
    </div>
  )
}

const ARRONDISSEMENTS = Array.from({ length: 20 }, (_, i) => ({ value: i + 1, label: `${i + 1}e arrondissement` }))

export default function ComparateurPage() {
  const [allData, setAllData]       = useState({})
  const [loading, setLoading]       = useState(true)
  const [selection, setSelection]   = useState([4, 11, 16])

  useEffect(() => {
    Promise.all(INDICATORS.map(ind =>
      fetch(ind.path).then(r => r.ok ? r.json() : null).catch(() => null)
    )).then(results => {
      const merged = {}
      INDICATORS.forEach((ind, i) => {
        const stats = results[i]
        if (!stats?.par_arrondissement) return
        stats.par_arrondissement.forEach(row => {
          const arr = row.arrondissement
          if (!merged[arr]) merged[arr] = { arrondissement: arr }
          merged[arr][ind.statsKey] = row[ind.statsKey]
        })
      })
      setAllData(merged)
      setLoading(false)
    })
  }, [])

  const handleSelect = (idx, val) => {
    setSelection(prev => { const next = [...prev]; next[idx] = Number(val); return next })
  }

  const selectedData = selection.map(arr => allData[arr])
  const hasData = !loading && Object.keys(allData).length > 0

  return (
    <div style={{ paddingTop: 'var(--nav-h)', minHeight: '100vh', background: 'var(--bg)' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 40px' }}>

        {/* Header */}
        <div style={{ marginBottom: 48 }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 12 }}>
            Comparateur · {selection.length} arrondissements · 4 indices
          </p>
          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 48, color: 'var(--text)', lineHeight: 1.1 }}>
            Confronter les{' '}
            <span style={{ fontStyle: 'italic', color: 'var(--accent)' }}>signatures</span>{' '}
            urbaines.
          </h1>
        </div>

        {loading && (
          <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-3)' }}>
            <p style={{ fontSize: 14 }}>Chargement des données…</p>
          </div>
        )}

        {hasData && (
          <>
            {/* Comparison table */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 16, overflow: 'hidden', boxShadow: 'var(--shadow-sm)', marginBottom: 32 }}>
              {/* Header row */}
              <div style={{ display: 'grid', gridTemplateColumns: '200px repeat(3, 1fr)', borderBottom: '1px solid var(--border)' }}>
                <div style={{ padding: '20px 24px', borderRight: '1px solid var(--border)' }}>
                  <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Quartier</p>
                </div>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{ padding: '16px 20px', borderRight: i < 2 ? '1px solid var(--border)' : 'none', background: 'var(--bg)' }}>
                    <select
                      value={selection[i]}
                      onChange={e => handleSelect(i, e.target.value)}
                      style={{
                        width: '100%', background: 'var(--bg-card)', border: '1px solid var(--border)',
                        borderRadius: 6, color: 'var(--text)', fontSize: 13, fontWeight: 600,
                        padding: '7px 10px', outline: 'none', cursor: 'pointer',
                      }}
                    >
                      {ARRONDISSEMENTS.map(a => (
                        <option key={a.value} value={a.value}>{a.label}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              {/* Indicator rows */}
              {INDICATORS.map((ind, iRow) => (
                <div key={ind.key} style={{ display: 'grid', gridTemplateColumns: '200px repeat(3, 1fr)', borderBottom: iRow < INDICATORS.length - 1 ? '1px solid var(--border-light)' : 'none' }}>
                  <div style={{ padding: '20px 24px', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: ind.color, marginBottom: 3, letterSpacing: '0.05em' }}>{ind.key}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-2)' }}>{ind.sub}</span>
                  </div>
                  {[0, 1, 2].map(i => {
                    const row = selectedData[i]
                    const score = row?.[ind.statsKey]
                    const c = score != null ? scoreColor(score) : 'var(--text-3)'
                    return (
                      <div key={i} style={{ padding: '16px 20px', borderRight: i < 2 ? '1px solid var(--border-light)' : 'none' }}>
                        {score != null ? (
                          <>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                              <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 28, color: c }}>{score.toFixed(1)}</span>
                              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>/100</span>
                            </div>
                            <ScoreBar score={score} color={c} />
                          </>
                        ) : (
                          <span style={{ fontSize: 12, color: 'var(--text-3)' }}>—</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>

            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              {[0, 1, 2].map(i => {
                const row = selectedData[i]
                if (!row) return <div key={i} />
                const scores = INDICATORS.map(ind => row[ind.statsKey]).filter(s => s != null)
                const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null
                return (
                  <div key={i} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 12, padding: '20px 20px 16px', boxShadow: 'var(--shadow-sm)' }}>
                    <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', marginBottom: 8 }}>Paris {selection[i]}e arr.</p>
                    <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 22, color: avg != null ? scoreColor(avg) : 'var(--text)', marginBottom: 4 }}>
                      {avg != null ? `${avg.toFixed(1)}/100` : '—'}
                    </p>
                    <p style={{ fontSize: 11, color: 'var(--text-3)' }}>Score composite moyen</p>
                    <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {INDICATORS.map(ind => {
                        const s = row[ind.statsKey]
                        return s != null ? (
                          <span key={ind.key} style={{ fontSize: 10, fontWeight: 600, color: ind.color, background: ind.color + '15', borderRadius: 4, padding: '2px 6px' }}>
                            {ind.key} {s.toFixed(0)}
                          </span>
                        ) : null
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
