import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 前端默认 http://127.0.0.1:8000；可通过环境变量 VITE_API_BASE 覆盖
const API_TARGET = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
});
