import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
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
    __VUE_PROD_DEVTOOLS__: false
  },
  esbuild: {
    sourcemap: true
  },
  resolve: {
    alias: {
      vue: 'vue/dist/vue.esm-bundler.js'
    }
  }
})
