"""Vieux-Port fait main sur le vrai bassin OSM : quais, pontons, pointus, ombrière, ferry-boat.

En direct (MCP) :
    D = "chemin/du/depot/blender/"
    for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "build_vieux_port.py"): exec(open(D + f).read())
Relançable. L'empty place_vieux_port (rubrique Contact du site) est recentré sur le bassin.
Remplace l'ancien groupe de l'île compressée (objets vp_*, trop grand pour le vrai bassin).
"""
import math

from shapely import affinity
from shapely.geometry import Point, box as sbox, shape

# 1. l'ancien groupe disparaît (il reste dans marseille_compresse_2026-11-17.blend)
e = bpy.data.objects.get("place_vieux_port")
if e:
    for c in list(e.children_recursive):
        bpy.data.objects.remove(c, do_unlink=True)

# 2. le bassin = la mer comprise entre les quais (commune moins terre, autour du port)
bassin = bassin_vp()
c = bassin.centroid
print("bassin", round(bassin.area, 2), "u², centre", round(c.x, 2), round(c.y, 2))

k = FastKit("vieux_port", c.x, c.y, 0.0, col="Monuments")
L = lambda x, y: (x - c.x, y - c.y)   # monde -> local à l'empty
QZ = 0.32                              # dessus des quais
WZ = 0.0                               # niveau de l'eau
mat("pierre_quai", "#d8c9a8"); mat("bois", "#b9825a"); mat("miroir", "#dfe8ee", rough=0.05)

# 3. quais : un ruban de pierre tout autour du bassin, côté terre
ring = bassin.exterior
pts = [L(*p) for p in ring.simplify(0.04).segmentize(0.2).coords]
bm_q = k.bm
for a, b in zip(pts, pts[1:]):
    ax, ay = a; bx, by = b
    mx, my = (ax + bx) / 2, (ay + by) / 2
    ln = math.hypot(bx - ax, by - ay)
    if ln < 1e-4: continue
    r = math.atan2(by - ay, bx - ax)
    # décalage vers la terre (extérieur du bassin)
    nx, ny = -math.sin(r), math.cos(r)
    if bassin.contains(Point(c.x + mx + nx * 0.06, c.y + my + ny * 0.06)): nx, ny = -nx, -ny
    k.box(mx + nx * 0.05, my + ny * 0.05, WZ - 0.2, ln + 0.02, 0.1, QZ + 0.2, "pierre_quai", rz=r)
    k.box(mx + nx * 0.004, my + ny * 0.004, QZ, ln + 0.01, 0.012, 0.012, "calcaire", rz=r)   # margelle

# 4. pontons + pointus, perpendiculaires aux quais nord et sud
minx, miny, maxx, maxy = bassin.bounds
couleurs = ("rouge", "bleu", "jaune", "blanc", "bleu_om", "volet_vert")
n = 0
xx = minx + 0.45
while xx < maxx - 0.35:
    col = bassin.intersection(sbox(xx - 0.001, miny - 1, xx + 0.001, maxy + 1))
    for part in getattr(col, "geoms", [col]):
        if part.is_empty: continue
        _, py0, _, py1 = part.bounds
        if py1 - py0 < 0.45: continue
        for (ys, sens) in ((py1, -1), (py0, 1)):      # depuis le quai nord vers le sud, et inversement
            lx, ly = L(xx, ys)
            lp = min(0.32, (py1 - py0) * 0.3)
            k.box(lx, ly + sens * lp / 2, WZ + 0.02, 0.035, lp, 0.02, "bois")
            for j in range(3):
                for side in (-1, 1):
                    if (n + j + side) % 4 == 0: continue
                    bx_, by_ = lx + side * 0.06, ly + sens * (0.06 + j * 0.09)
                    k.box(bx_, by_, WZ, 0.04, 0.075, 0.03, couleurs[(n + j) % 6])           # coque
                    k.box(bx_, by_ - sens * 0.008, WZ + 0.03, 0.026, 0.025, 0.018, "blanc")  # cabine
                    n += 1
    xx += 0.32
print("pointus", n)

# 5. ombrière (miroir sur pilotis) sur le quai des Belges, au fond du port
ox, oy = L(*ll(43.2952, 5.3744))
for dx in (-0.16, 0.16):
    for dy in (-0.2, 0.2):
        k.cyl(ox + dx, oy + dy, QZ, 0.008, 0.2, "blanc", verts=6)
k.box(ox, oy, QZ + 0.2, 0.42, 0.52, 0.012, "miroir")

# 6. le ferry-boat qui traverse le port
fx, fy = L(*ll(43.2950, 5.3725))
k.box(fx, fy, WZ, 0.07, 0.14, 0.035, "blanc")
k.box(fx, fy, WZ + 0.035, 0.05, 0.08, 0.03, "bleu")
k.box(fx, fy, WZ + 0.065, 0.055, 0.09, 0.008, "blanc")

k.done()
