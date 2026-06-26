import React from 'react'

const NAV_LINKS = [
  { key: 'cartographie', label: 'Cartographie' },
  { key: 'comparateur',  label: 'Comparateur'  },
  { key: 'indicateurs',  label: 'Indicateurs'  },
  { key: 'methodologie', label: 'Méthodologie' },
  { key: 'sources',      label: 'Sources'      },
]

export default function Navbar({ page, onNavigate }) {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      height: 'var(--nav-h)',
      background: 'var(--bg-card)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center',
      padding: '0 28px',
      boxShadow: 'var(--shadow-sm)',
    }}>
      {/* Logo */}
      <button
        onClick={() => onNavigate('cartographie')}
        style={{
          background: 'none', border: 'none', cursor: 'pointer',
          display: 'flex', alignItems: 'baseline', gap: 6, padding: 0, marginRight: 40,
        }}
      >
        <span style={{
          fontFamily: 'Cormorant Garamond, serif',
          fontSize: 18, fontWeight: 700, color: 'var(--text)',
          letterSpacing: '-0.01em', lineHeight: 1,
        }}>
          Urban
        </span>
        <span style={{
          fontFamily: 'Cormorant Garamond, serif',
          fontSize: 18, fontWeight: 400, fontStyle: 'italic',
          color: 'var(--accent)', letterSpacing: '-0.01em', lineHeight: 1,
        }}>
          Data Explorer
        </span>
      </button>

      {/* Links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1 }}>
        {NAV_LINKS.map(link => {
          const isActive = page === link.key
          return (
            <button
              key={link.key}
              onClick={() => onNavigate(link.key)}
              style={{
                background: isActive ? 'rgba(29,78,107,0.08)' : 'none',
                border: 'none',
                borderRadius: 6,
                color: isActive ? 'var(--accent)' : 'var(--text-2)',
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                padding: '5px 12px',
                cursor: 'pointer',
                transition: 'all 0.15s',
                letterSpacing: '-0.01em',
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'var(--bg-hover)'
                  e.currentTarget.style.color = 'var(--text)'
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.background = 'none'
                  e.currentTarget.style.color = 'var(--text-2)'
                }
              }}
            >
              {link.label}
            </button>
          )
        })}
      </div>

      {/* Badge */}
      <div style={{
        fontSize: 10, fontWeight: 600, color: 'var(--text-3)',
        background: 'var(--bg)', border: '1px solid var(--border)',
        borderRadius: 20, padding: '3px 10px', letterSpacing: '0.06em',
        textTransform: 'uppercase',
      }}>
        Paris · 2021
      </div>
    </nav>
  )
}
