"""Place hors ligne les objets de src/props.ts marqués `free` : cherche autour du point visé un sol sans bâtiment
(9 sondes sur l'emprise, aucune ne doit toucher un bâtiment) et réécrit leurs dx/dz dans props.ts. À relancer si la ville ou un objet change.

uvx --from playwright python -I scripts/place_props.py [url]     (site lancé avec npm run dev)
"""
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROPS = Path(__file__).resolve().parent.parent / "src" / "props.ts"
url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173/") + "?debug&q=low"
src = PROPS.read_text()
LINE = re.compile(r"\{ prop: '(\w+)', anchor: '(\w+)', dx: (-?[\d.]+), dz: (-?[\d.]+)([^}]*?)free: ([\d.]+)([^}]*)\}")
poses = [(m.group(0), m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(6))) for m in LINE.finditer(src)]

JS = """([anchor, dx, dz, r]) => {
  const P = window.__perf;
  let n = null; P.scene.traverse(x => { if (!n && x.name === 'place_' + anchor) n = x; });
  const box = new P.THREE.Box3().setFromObject(n); const c = box.getCenter(new P.THREE.Vector3());
  const off = P.island.parent.position;  // décalage du monde (houle)
  const cx = c.x - off.x, cz = c.z - off.z;
  // libre = aucune des 9 sondes ne touche un bâtiment (maillages des arrondissements ou d'un monument), même en pente
  const ray = new P.THREE.Raycaster(), down = new P.THREE.Vector3(0, -1, 0), o = new P.THREE.Vector3();
  const bati = (x, z) => { ray.set(o.set(x + off.x, 60, z + off.z), down);
    const h = ray.intersectObject(P.island, true).find(h => h.object.isMesh && h.object.visible);
    for (let q = h && h.object; q; q = q.parent) if (q.name.startsWith('place_')) return true;
    return false; };
  const flat = (x, z) => [[0,0],[1,0],[-1,0],[0,1],[0,-1],[.7,.7],[-.7,.7],[.7,-.7],[-.7,-.7]].every(([ox, oz]) => !bati(x + ox * r, z + oz * r));
  let x = cx + dx, z = cz + dz;
  if (flat(x, z)) return [dx, dz, 0];
  for (let rr = 0.05; rr < 1.2; rr += 0.05) for (let a = 0; a < Math.PI * 2; a += 0.35) {
    const tx = x + Math.cos(a) * rr, tz = z + Math.sin(a) * rr;
    if (flat(tx, tz)) return [tx - cx, tz - cz, rr];
  }
  return [dx, dz, -1];
}"""

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 400, "height": 300})
    pg.set_default_timeout(600000)
    pg.goto(url)
    pg.wait_for_selector(".loading.done", timeout=180000)
    pg.wait_for_timeout(3000)
    pris = []  # emplacements déjà occupés par les objets précédents
    for whole, prop, anchor, dx, dz, r in poses:
        ndx, ndz, moved = pg.evaluate(JS, [anchor, dx, dz, r])
        # évite deux objets au même endroit : décale si trop proche d'un objet déjà posé
        for (an, ax, az, ar) in pris:
            if an == anchor and ((ndx - ax) ** 2 + (ndz - az) ** 2) ** 0.5 < ar + r:
                ndx, ndz, moved = pg.evaluate(JS, [anchor, ndx + (ar + r) * 1.1, ndz + (ar + r) * 0.4, r])
        pris.append((anchor, ndx, ndz, r))
        print(f"{prop:14} {anchor:22} ({dx:+.2f}, {dz:+.2f}) → ({ndx:+.2f}, {ndz:+.2f})  {'déjà libre' if moved == 0 else 'introuvable' if moved < 0 else f'décalé de {moved:.2f}'}")
        new = whole.replace(f"dx: {LINE.match(whole).group(3)}, dz: {LINE.match(whole).group(4)}", f"dx: {ndx:.2f}, dz: {ndz:.2f}")
        src = src.replace(whole, new, 1)
    b.close()
PROPS.write_text(src)
print("props.ts mis à jour")
