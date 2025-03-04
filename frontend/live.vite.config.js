import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
        "/api": {
            target: "http://127.0.0.1:5000", // Flask backend
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, "/api"),
        },
    },
},
  plugins: [
    vue(),
    vueDevTools(),
  ],
  server: {
    host: true, // or '0.0.0.0'
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
