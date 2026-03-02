import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/KR-WordRank/",
  build: {
    outDir: "../docs",
    emptyOutDir: true,
  },
});
