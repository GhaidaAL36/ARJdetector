import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // keeps the browser on one origin in dev, so no CORS setup is needed on FastAPI
    proxy: {
      '/analyze': 'http://127.0.0.1:8000',
    },
  },
})
