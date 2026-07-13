import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/

export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      'trend-chaser.madcamp-kaist.org'
    ]
  }
})

