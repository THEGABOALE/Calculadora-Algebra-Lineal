import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
      server: {
        // Use the default Vite port for dev (5173) to avoid colliding with Django (8000).
        port: 5173,
        // Proxy API calls to the Django backend running on port 8000 so the frontend can use
        // same-origin paths like `/matrix/operate` without CORS issues during development.
        proxy: {
          // forward /matrix/* -> /api/v1/matrix/* on the Django backend
          '/matrix': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            rewrite: (path) => path.replace(/^\/matrix/, '/api/v1/matrix'),
          },
          // forward /vectors/* -> /api/v1/vectors/*
          '/vectors': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            rewrite: (path) => path.replace(/^\/vectors/, '/api/v1/vectors'),
          },
          // add other rewrites if you expose different top-level paths
        },
    }
});
