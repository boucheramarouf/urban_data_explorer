import React from 'react'

const NAV_LINKS = [
  { key: 'carte',        label: 'Cartographie' },
  { key: 'indicateurs',  label: 'Indicateurs' },
  { key: 'comparateur',  label: 'Comparateur' },
  { key: 'methodologie', label: 'Méthodologie' },
  { key: 'sources',      label: 'Sources' },
]

export default function Navbar({ page, onNavigate }) {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      height: 'var(--nav-h)',
      background: 'rgba(239,233,223,0.92)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center',
      padding: '0 28px',
    }}>
      {/* Logo */}
      <button
        onClick={() => onNavigate('landing')}
        style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, marginRight: 40 }}
      >
        <div style={{
          width: 28, height: 28, borderRadius: 7,
          background: 'var(--text)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="5.5" stroke="#EFE9DF" strokeWidth="1.5"/>
            <circle cx="7" cy="7" r="2" fill="#EFE9DF"/>
          </svg>
        </div>
        <div style={{ textAlign: 'left' }}>
          <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', letterSpacing: '-0.01em', lineHeight: 1.1 }}>Urban Data</p>
          <p style={{ fontSize: 10, color: 'var(--text-3)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Paris</p>
        </div>
      </button>

      {/* Nav links */}
      <div style={{ display: 'flex', gap: 2, flex: 1 }}>
        {NAV_LINKS.map(link => (
          <button
            key={link.key}
            onClick={() => onNavigate(link.key)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '6px 14px', borderRadius: 6,
              fontSize: 13, fontWeight: page === link.key ? 600 : 400,
              color: page === link.key ? 'var(--text)' : 'var(--text-2)',
              background: page === link.key ? 'var(--bg-hover)' : 'transparent',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { if (page !== link.key) e.currentTarget.style.color = 'var(--text)' }}
            onMouseLeave={e => { if (page !== link.key) e.currentTarget.style.color = 'var(--text-2)' }}
          >
            {link.label}
          </button>
        ))}
      </div>

      {/* Version badge */}
      <span style={{
        fontSize: 10, color: 'var(--text-3)', fontWeight: 500,
        background: 'var(--bg-hover)', borderRadius: 4,
        padding: '3px 7px', letterSpacing: '0.04em',
      }}>v0.4.2</span>
    </nav>
  )
}
