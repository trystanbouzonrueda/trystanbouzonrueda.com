import { resolve } from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
  // lien court /cv → version recruteur (en production : redir dans le Caddyfile)
  plugins: [{ name: 'cv-court', configureServer(server) {
    server.middlewares.use((req, res, next) => {
      if (req.url === '/cv' || req.url === '/cv/') { res.statusCode = 302; res.setHeader('Location', '/recruteur/'); res.end(); return; }
      next();
    });
  } }],
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1200, // three + postprocessing ≈ 1 Mo (≈ 280 ko gzip)
    rolldownOptions: {
      // deux pages : le portfolio en 3D et la version simple pour les recruteurs
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        recruteur: resolve(import.meta.dirname, 'recruteur/index.html'),
        mentions: resolve(import.meta.dirname, 'mentions-legales/index.html'),
        notfound: resolve(import.meta.dirname, '404.html'),
      },
      // three + postprocessing à part : gardés en cache quand seul le code du site change
      output: { codeSplitting: { groups: [{ name: 'vendor', test: /node_modules[\\/](three|postprocessing)/ }] } },
    },
  },
});
