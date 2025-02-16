import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import path from "node:path"
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  resolve: {
    alias: {
      $icons: path.resolve("./src/icons"),
      $workers: path.resolve("./src/workers"),
      $components: path.resolve("./src/components"),
      $websockets: path.resolve("./src/websockets"),
      $states: path.resolve("./src/states"),
    },
  },
})
