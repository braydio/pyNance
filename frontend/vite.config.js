import { fileURLToPath, URL } from 'node:url'
import process from 'node:process'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import visualizer from 'rollup-plugin-visualizer'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Inspect from 'vite-plugin-inspect'
import tailwindcss from '@tailwindcss/vite'

// Conditionally load PWA plugin so dev doesn't fail
// Use a variable-based dynamic import to avoid esbuild/vite config bundling
// from trying to resolve the package when it's not installed or mis-versioned.
async function maybePWA() {
  const enablePwa = process.env.ENABLE_PWA === '1'
  if (!enablePwa) {
    return null
  }
  try {
    const pwaPkg = 'vite-plugin' + '-pwa'
    // @ts-ignore - avoid static analysis/bundling
    const mod = await import(/* @vite-ignore */ pwaPkg)
    const { VitePWA } = mod
    return VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'pyNance',
        short_name: 'pyNance',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    })
  } catch (err) {
    console.warn('[vite] vite-plugin-pwa not available; continuing without PWA')
    return null
  }
}

export default defineConfig(async () => {
  const pwa = await maybePWA()

  return {
    plugins: [
      vue(),
      vueDevTools(),
      tailwindcss(),
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
        open: false, // set to true only when analyzing
      }),
      ...(pwa ? [pwa] : []),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      allowedHosts: [
        '.ngrok-free.app',
      ],
      host: '0.0.0.0',
      port: 3353,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true,
        },
      },
    },
  }
})
