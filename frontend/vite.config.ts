import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 7501,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://app:7500',
        changeOrigin: true,
      },
    },
  },
})
