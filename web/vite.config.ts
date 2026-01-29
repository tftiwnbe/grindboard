import { sveltekit } from "@sveltejs/kit/vite";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";
import path from "node:path";
import { defineConfig, type ProxyOptions, type UserConfig } from "vite";

const upstream = {
  target: "http://localhost:3000/",
  changeOrigin: true,
  secure: false,
  ws: true,
} satisfies ProxyOptions;

const proxy: Record<string, string | ProxyOptions> = {
  "/api": upstream,
  "/custom.css": upstream,
  "/socket.io": { ...upstream, ws: true },
};

export default defineConfig({
  build: { target: "es2022" },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: { proxy, allowedHosts: true },
  preview: { proxy },
  plugins: [
    tailwindcss(),
    sveltekit(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Grindboard",
        short_name: "Grindboard",
        description: "Minimal tasks management app",
        theme_color: "#000000",
        icons: [
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
    }),
  ],
  optimizeDeps: {
    entries: ["src/**/*.{svelte,ts,html}"],
  },
} as UserConfig);
