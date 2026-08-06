import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react({
    include: [/\.tsx?$/, /\.jsx?$/],
  })],
  optimizeDeps: {
    exclude: ['os'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/__tests__/setup.ts',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/tasks': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/query': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/team': {
        target: 'http://localhost:3004',
        changeOrigin: true,
      },
    },
  },
})
