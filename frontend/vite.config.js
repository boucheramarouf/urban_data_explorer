import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_BASE      = 'http://localhost:8000'
const CLIENT_ID     = 'urban-frontend'
const CLIENT_SECRET = 'urban-data-explorer-2026'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: API_BASE,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy) => {
          let bearerToken  = null
          let tokenExpiry  = 0

          const fetchToken = () =>
            fetch(`${API_BASE}/token?client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}`, { method: 'POST' })
              .then(r => r.json())
              .then(data => {
                bearerToken = data.access_token
                tokenExpiry = Date.now() + (data.expires_in - 120) * 1000 // refresh 2min avant exp
                console.log('[vite-proxy] JWT obtenu, expire dans', data.expires_in, 's')
              })
              .catch(e => console.warn('[vite-proxy] Impossible de fetch le JWT:', e))

          // Fetch initial au démarrage
          fetchToken()

          proxy.on('proxyReq', (proxyReq) => {
            // Renouvelle si expiré
            if (!bearerToken || Date.now() > tokenExpiry) fetchToken()
            if (bearerToken) proxyReq.setHeader('Authorization', `Bearer ${bearerToken}`)
          })
        }
      }
    }
  }
})