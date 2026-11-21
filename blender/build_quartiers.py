"""Grands axes (Canebière, Prado, boulevards) et leurs platanes.

exec(lib.py) puis exec(build_quartiers.py). Relançable (lot="Q").
Les immeubles sont construits dans UN seul mesh (rapide à afficher et à exporter).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
random.seed(5)
clear_lot("Q")

def R(t): return 10 + 0.7 * math.sin(3 * t + 0.4) + 0.45 * math.sin(5 * t + 1.3) + 0.25 * math.sin(9 * t)
def coast(y): return -5.2 + 1.0 * math.sin(y * 0.45) + (0.0 if y > -6 else (y + 6) * 0.35)

# zones réservées aux monuments (x, y, demi-largeur, demi-profondeur)
RESERVE = [(-2.5, 4.75, 2.3, 2.1), (-2.6, 1.4, 1.2, 1.2), (-4.6, -5.6, .6, .6), (-2.4, -6.0, 1.25, .9),
           (2.6, -3.4, 1.7, 1.3), (0.9, 1.0, .75, .55), (-4.9, 6.4, .8, .8), (-3.4, 7.7, .9, .6), (5.2, 4.2, 1.0, 1.0),
           # lot Meshy 2 (voir place_monuments.py)
           (1.6, 6.5, .9, .6),     # gare Saint-Charles
           (-1.6, 8.6, .45, .45),  # tour CMA CGM
           (4.9, -4.9, .8, .5),    # Cité Radieuse
           (6.0, 6.4, .9, .7),     # palais Longchamp
           ]
# grands axes
AXES = {
    "canebiere": [(-0.5, 4.75), (2.0, 4.75), (4.0, 4.6), (7.5, 4.4)],
    "prado": [(-0.3, 3.0), (0.2, 0.0), (0.0, -2.0), (-1.0, -4.6), (-3.0, -5.15), (-4.3, -5.15)],
    "rue_paradis": [(0.6, 3.6), (1.8, 1.8), (2.0, -1.5)],
    "boulevard": [(4.0, 4.6), (4.6, 1.0), (4.0, -3.4), (2.6, -5.2), (0.0, -6.0)],
}
def dist_seg(p, a, b):
    ab = b - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length
def near_axis(x, y, d):
    p = Vector((x, y))
    return any(dist_seg(p, Vector(a), Vector(b)) < d for pts in AXES.values() for a, b in zip(pts, pts[1:]))
def free(x, y, m=0.0):
    if math.hypot(x, y) > R(math.atan2(y, x)) - 0.7: return False
    if x < coast(y) + 0.9: return False
    if y < -6.6: return False
    return not any(abs(x - cx) < rx + m and abs(y - cy) < ry + m for cx, cy, rx, ry in RESERVE)

# ---------- routes
for name, pts in AXES.items():
    p3 = []
    for (a, b) in zip(pts, pts[1:]):
        n = max(2, int((Vector(b) - Vector(a)).length / 0.25))
        for k in range(n):
            q = Vector(a).lerp(Vector(b), k / n); p3.append((q.x, q.y, ground(q.x, q.y) + 0.02))
    p3.append((pts[-1][0], pts[-1][1], ground(*pts[-1]) + 0.02))
    ribbon("rue_" + name, p3, 0.26, "route", None, "Quartiers", "Q", thick=0.25)
    for i in range(0, len(p3), 3):  # platanes le long des axes
        x, y, z = p3[i]
        if name in ("prado", "canebiere") and free(x, y, -0.3):
            a = Vector(p3[min(i + 1, len(p3) - 1)]) - Vector(p3[max(i - 1, 0)])
            nrm = Vector((-a.y, a.x, 0)).normalized() * 0.2
            for s in (1, -1):
                tree(f"q_platane_{name}{i}{s}", x + nrm.x * s, y + nrm.y * s, 0.55, None, "Q")

# ---------- (immeubles génériques retirés le 2026-11-17 : chaque quartier est désormais fait main,
#             voir batiments.py et quartiers/*.py)
print("axes et platanes ok")
