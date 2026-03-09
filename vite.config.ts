import build from '@hono/vite-build/cloudflare-pages'
import devServer from '@hono/vite-dev-server'
import adapter from '@hono/vite-dev-server/cloudflare'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    build(),
    devServer({
      adapter,
      entry: 'src/index.tsx'
    })
  ],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: 'src/index.tsx'
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})
