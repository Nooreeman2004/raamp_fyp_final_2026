import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  // Dev server with proxy to avoid CORS and cookie issues during local development.
  // For any request starting with `/api`, the dev server will forward
  // it to the backend at http://localhost:8000 and return the response
  // to the browser as if it came from the same origin.
  server: {
    host: "::",
    port: 8080,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
