import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxy = {
  "/api": {
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
    rewrite: (p) => p.replace(/^\/api/, ""),
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  // `vite preview` does not inherit server.proxy, so repeat it here: this makes
  // the production build served on :4173 talk to the API with no env baking.
  preview: {
    port: 4173,
    proxy: apiProxy,
  },
});