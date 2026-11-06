import path from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      frontendRoute: '/customer-portal',
      frappeProxy: true,
      // Frappe's website context overwrites `boot`, so index.html reads csrf_token directly
      jinjaBootData: false,
      buildConfig: {
        outDir: '../customer_portal/public/frontend',
        indexHtmlPath: '../customer_portal/www/customer-portal.html',
      },
    }),
    vue(),
  ],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
})
