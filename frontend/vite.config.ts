import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import svgLoader from 'vite-svg-loader';

export default defineConfig({
  plugins: [
    sveltekit(),
    svgLoader({
      defaultImport: 'url'
    })
  ],
  optimizeDeps: {
    exclude: ['devalue']
  },
  assetsInclude: ['**/*.svg', '**/*.SVG'],
  server: {
    fs: {
      // Allow serving files from the entire workspace
      allow: ['..']
    }
  }
}); 