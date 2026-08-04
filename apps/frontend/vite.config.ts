import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server binds to loopback only (matches the backend's security posture).
export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8787",
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: [],
  },
});
