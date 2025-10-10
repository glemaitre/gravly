import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

export default defineConfig(() => {
  // Helper function to load env files
  const loadEnvFile = (filename) => {
    const env = {}
    try {
      const envPath = resolve(process.cwd(), `../.env/${filename}`)
      const envContent = readFileSync(envPath, 'utf-8')
      envContent.split('\n').forEach((line) => {
        const [key, ...valueParts] = line.split('=')
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join('=').trim()
        }
      })
    } catch (error) {
      console.warn(`Could not load .env/${filename} file:`, error.message)
    }
    return env
  }

  // Load env files
  const stravaEnv = loadEnvFile('strava')
  const thunderforestEnv = loadEnvFile('thunderforest')
  const serverEnv = loadEnvFile('server')

  // Parse port numbers with defaults
  const frontendPort = parseInt(serverEnv.FRONTEND_PORT || '3000', 10)
  const backendUrl = serverEnv.BACKEND_URL || 'http://localhost:8000'

  return {
    plugins: [vue()],
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: backendUrl,
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
