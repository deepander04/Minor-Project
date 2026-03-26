import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      // Route each API path to the correct backend service directly
      // This works both locally (no Nginx) and inside Docker
      '/api/auth': {
        target: process.env.AUTH_URL || 'http://localhost:5001',
        changeOrigin: true,
      },
      '/api/upload': {
        target: process.env.UPLOAD_URL || 'http://localhost:5002',
        changeOrigin: true,
      },
      '/api/scans': {
        target: process.env.UPLOAD_URL || 'http://localhost:5002',
        changeOrigin: true,
      },
      '/api/patients': {
        target: process.env.UPLOAD_URL || 'http://localhost:5002',
        changeOrigin: true,
      },
      '/api/preprocess': {
        target: process.env.PREPROCESS_URL || 'http://localhost:5003',
        changeOrigin: true,
      },
      '/api/analyze': {
        target: process.env.INFERENCE_URL || 'http://localhost:5004',
        changeOrigin: true,
      },
      '/api/results': {
        target: process.env.INFERENCE_URL || 'http://localhost:5004',
        changeOrigin: true,
      },
      '/api/heatmap': {
        target: process.env.INFERENCE_URL || 'http://localhost:5004',
        changeOrigin: true,
      },
      '/api/models': {
        target: process.env.INFERENCE_URL || 'http://localhost:5004',
        changeOrigin: true,
      },
      '/api/reports': {
        target: process.env.REPORT_URL || 'http://localhost:5005',
        changeOrigin: true,
      },
    },
  },
})
