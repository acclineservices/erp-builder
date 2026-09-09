import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Docker bind mounts on Windows do not reliably emit file-change events.
    // Polling keeps the browser-served module graph aligned with mounted source.
    watch: { usePolling: true, interval: 300 },
  },
});
