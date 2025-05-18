// vite.config.js
import { defineConfig } from 'vite'            // ← 一定要这个
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,    // 或者 '0.0.0.0'
    port: 5173
  }
})