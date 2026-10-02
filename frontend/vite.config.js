import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    quasar({
      sassVariables: path.resolve(__dirname, 'src/quasar-variables.sass')
    })
  ],
  resolve: {
    alias: {
      src: path.resolve(__dirname, 'src'),
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
      host: '0.0.0.0',
      port: 5426
  }
})
