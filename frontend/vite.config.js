import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import { visualizer } from 'rollup-plugin-visualizer'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { VitePWA } from 'vite-plugin-pwa'
import Inspect from 'vite-plugin-inspect'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    Inspect(),
    Components({
      dirs: ['src/components'],
      extensions: ['vue'],
      deep: true,
      dts: 'src/components.d.ts',
    }),
    AutoImport({
      imports: ['vue', 'vue-router'],
      dts: 'src/auto-imports.d.ts',
    }),
    visualizer({
      filename: 'stats.html',
      template: 'treemap',
      open: true,
    }),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'My Cool App',
        short_name: 'CoolApp',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 3353,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // Optional rewrite example:
        // rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
    // 🔥 THIS PART IS NEW — THIS FIXES RELOADS
    historyApiFallback: true,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})

