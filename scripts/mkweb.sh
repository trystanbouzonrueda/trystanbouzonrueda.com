#!/usr/bin/env bash
# Copie d'aperçu publiable en artifact claude.ai : base relative, GLB stockés en JSON base64
# (les .glb ne sont pas servis) et un petit décodeur ajouté en tête de page.
#   bash scripts/mkweb.sh <dossier_sortie>      → écrit aussi <dossier_sortie>/../web_files.json (fichiers à publier)
set -euo pipefail
W="${1:?dossier de sortie}"
cd "$(dirname "$0")/.."
rm -rf "$W"
npx vite build --base=./ --outDir "$W" --emptyOutDir >/dev/null
cd "$W"
rm -rf cv/*.html recruteur mentions-legales 404.html cv/Trystan-* img/trystan-cv.jpg robots.txt sitemap.xml
python3 -I - <<'PY'
import base64, json, re
from pathlib import Path
for f in Path('models').glob('*.glb'):
    Path(str(f) + '.json').write_text(json.dumps({'b64': base64.b64encode(f.read_bytes()).decode()}))
    f.unlink()
h = Path('index.html').read_text()
h = re.sub(r'\s*<!-- la ville[^>]*-->\s*<link rel="preload"[^>]*>', '', h)
h = re.sub(r'\s*<link rel="preload" href="[^"]*\.glb"[^>]*>', '', h)
shim = r"""<script>
  // copie d'aperçu (artifact) : les .glb sont stockés en JSON base64, reconstitués ici à la volée
  (() => { const f = window.fetch.bind(window);
    window.fetch = (i, o) => { const u = typeof i === 'string' ? i : i.url;
      if (!/\.glb(\?|$)/.test(u)) return f(i, o);
      return f(u.replace(/\.glb/, '.glb.json'), o).then((r) => r.json()).then((j) => {
        const b = atob(j.b64), a = new Uint8Array(b.length);
        for (let k = 0; k < b.length; k++) a[k] = b.charCodeAt(k);
        return new Response(a.buffer, { headers: { 'Content-Type': 'model/gltf-binary', 'Content-Length': String(a.length) } });
      }); }; })();
</script>
"""
Path('index.html').write_text(h.replace('<head>', '<head>\n' + shim, 1))
files = {str(p): str(Path.cwd() / p) for p in sorted(Path('.').rglob('*')) if p.is_file() and p.name != 'index.html'}
Path('../web_files.json').write_text(json.dumps(files))
print(len(files), 'fichiers')
PY
