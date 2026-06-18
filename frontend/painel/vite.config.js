import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Dev: serve at / (API calls via proxy to backend)
  // Build: use --base=/painel/ for production
  base: '/',
  server: {
    port: 5173,
    proxy: {
      '/painel': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  }
})
