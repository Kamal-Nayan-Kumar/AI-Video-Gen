import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Proxy API calls to the FastAPI backend so the browser sees a single origin.
// This matters for SSE: EventSource cannot set custom headers, and a
// cross-origin event stream is easily buffered by the browser.
//
// The target is configurable because port 8000 is often already taken by
// another local project. Point it wherever the backend is actually listening:
//   API_TARGET=http://127.0.0.1:8010 npm run dev
const target = process.env.API_TARGET ?? "http://127.0.0.1:8000";

const proxy = {
  "/api": { target, changeOrigin: true },
  "/health": { target, changeOrigin: true },
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    proxy,
  },
  preview: {
    port: 4173,
    strictPort: true,
    proxy,
  },
});