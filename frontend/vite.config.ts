import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';
import svgLoader from 'vite-svg-loader';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
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
    },
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:3000'),
      'import.meta.env.VITE_WS_URL': JSON.stringify(env.VITE_WS_URL || 'ws://localhost:3000/ws')
    }
  };
}); 