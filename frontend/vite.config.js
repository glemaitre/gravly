import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

export default defineConfig(() => {
  // Load env file from .env/strava
  const stravaEnv = {}
  try {
    const envPath = resolve(process.cwd(), '../.env/strava')
    const envContent = readFileSync(envPath, 'utf-8')
    envContent.split('\n').forEach((line) => {
      const [key, ...valueParts] = line.split('=')
      if (key && valueParts.length > 0) {
        stravaEnv[key.trim()] = valueParts.join('=').trim()
      }
    })
  } catch (error) {
    console.warn('Could not load .env/strava file:', error.message)
  }

  // Load env file from .env/thunderforest
  const thunderforestEnv = {}
  try {
    const envPath = resolve(process.cwd(), '../.env/thunderforest')
    const envContent = readFileSync(envPath, 'utf-8')
    envContent.split('\n').forEach((line) => {
      const [key, ...valueParts] = line.split('=')
      if (key && valueParts.length > 0) {
        thunderforestEnv[key.trim()] = valueParts.join('=').trim()
      }
    })
  } catch (error) {
    console.warn('Could not load .env/thunderforest file:', error.message)
  }

  return {
    plugins: [vue()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          configure: (proxy) => {
            proxy.on('error', (err, req) => {
              console.error('Proxy error:', err.message, req.url)
            })
          }
        }
      }
    },
    logLevel: 'info',
    build: {
      rollupOptions: {
        input: {
          app: 'index.html',
          editor: 'editor.html'
        }
      }
    },
    css: {
      devSourcemap: true
    },
    optimizeDeps: {
      include: ['vue', 'chart.js']
    },
    define: {
      __VUE_OPTIONS_API__: true,
      __VUE_PROD_DEVTOOLS__: false,
      'import.meta.env.STRAVA_CLIENT_ID': JSON.stringify(stravaEnv.STRAVA_CLIENT_ID),
      'import.meta.env.STRAVA_CLIENT_SECRET': JSON.stringify(
        stravaEnv.STRAVA_CLIENT_SECRET
      ),
      'import.meta.env.THUNDERFOREST_API_KEY': JSON.stringify(
        thunderforestEnv.THUNDERFOREST_API_KEY
      )
    },
    esbuild: {
      sourcemap: true
    },
    resolve: {
      alias: {
        vue: 'vue/dist/vue.esm-bundler.js'
      }
    },
    envDir: '../.env',
    envPrefix: ['VITE_']
  }
})
