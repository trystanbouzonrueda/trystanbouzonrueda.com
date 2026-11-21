"""Corniche Kennedy faite main sur son vrai tracé OSM : route posée au sol, balustrade blanche
(le « plus long banc du monde »), palmiers, lampadaires, pont de la Fausse-Monnaie, Vallon des Auffes.

En direct (MCP) : for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "lieux.py", "build_corniche.py"): exec(...)
Relançable. Remplace l'ancien groupe de l'île compressée (qui flottait au-dessus du nouveau terrain).
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge, unary_union

# 1. ancien groupe supprimé (reste dans marseille_compresse_2026-11-17.blend)
e = bpy.data.objects.get("place_corniche")
if e:
    for c in list(e.children_recursive):
        bpy.data.objects.remove(c, do_unlink=True)

# 2. tracé : tous les tronçons nommés « Corniche … Kennedy » des 7e et 8e, chaînés du nord au sud
morceaux = []
for n in (7, 8):
    for w in json.loads((OSM / "raw" / f"rues_{n}.json").read_text())["elements"]:
        if "Kennedy" in w["tags"].get("name", "") and w.get("geometry"):
            morceaux.append(LineString([ll(p["lat"], p["lon"]) for p in w["geometry"]]))
m = linemerge(unary_union(morceaux))
parts = sorted(getattr(m, "geoms", [m]), key=lambda l: -l.length)
nord = Point(*ll(43.2905, 5.3560))
coords = []
reste = list(parts)
cur = min(reste, key=lambda l: min(Point(l.coords[0]).distance(nord), Point(l.coords[-1]).distance(nord)))
while cur is not None:
    reste.remove(cur)
    cs = list(cur.coords)
    if coords and Point(cs[-1]).distance(Point(coords[-1])) < Point(cs[0]).distance(Point(coords[-1])): cs = cs[::-1]
    if not coords and Point(cs[-1]).distance(nord) < Point(cs[0]).distance(nord): cs = cs[::-1]
    coords += cs
    fin = Point(coords[-1])
    cand = [l for l in reste if min(Point(l.coords[0]).distance(fin), Point(l.coords[-1]).distance(fin)) < 0.25 and l.length > 0.1]
    cur = min(cand, key=lambda l: min(Point(l.coords[0]).distance(fin), Point(l.coords[-1]).distance(fin))) if cand else None
route = LineString(coords).simplify(0.02)
print("corniche", round(route.length, 2), "u")

c = route.interpolate(0.5, normalized=True)
k = FastKit("corniche", c.x, c.y, 0.0, col="Monuments")
terre = affinity.scale(shape(_D["terre"]), U, U, origin=(0, 0)).buffer(0)
L = lambda x, y: (x - c.x, y - c.y)
mat("lampadaire", "#2b2d33")

# 3. route + balustrade côté mer + lampadaires côté terre + palmiers
pts = list(route.segmentize(0.12).coords)
k.ribbon([L(*p) for p in pts], 0.17, "route", dz=0.045)
d, i = 0.0, 0
while d < route.length:
    p = route.interpolate(d); q2 = route.interpolate(min(route.length, d + 0.03))
    tx, ty = q2.x - p.x, q2.y - p.y; nn = math.hypot(tx, ty) or 1
    nx, ny = -ty / nn, tx / nn
    if terre.contains(Point(p.x + nx * 0.3, p.y + ny * 0.3)): nx, ny = -nx, -ny      # n = côté mer
    r = math.atan2(ty, tx)
    z = ground(p.x, p.y)
    bx, by = L(p.x + nx * 0.1, p.y + ny * 0.1)
    k.box(bx, by, z + 0.02, 0.13, 0.018, 0.035, "blanc", rz=r)                        # banc-balustrade
    if i % 3 == 0:
        lx, ly = L(p.x - nx * 0.1, p.y - ny * 0.1)
        k.cyl(lx, ly, z + 0.02, 0.004, 0.11, "lampadaire", verts=4)
        k.ball(lx, ly, z + 0.135, 0.012, "jaune")
    if i % 4 == 2:
        px, py = L(p.x + nx * 0.16, p.y + ny * 0.16)
        pz = max(ground(p.x + nx * 0.16, p.y + ny * 0.16), 0.3)
        for s in range(3):
            k.cyl(px + s * 0.006, py, pz + s * 0.07, 0.012 - s * 0.002, 0.07, "tronc", verts=6)
        for j in range(6):
            t = j * math.pi / 3 + i
            k.box(px + 0.018 + math.cos(t) * 0.05, py + math.sin(t) * 0.05, pz + 0.21, 0.1, 0.025, 0.008, "feuillage", rz=t)
    d += 0.13; i += 1

# 4. pont de la Fausse-Monnaie (arche blanche côté mer)
fx, fy = ll(43.2804, 5.3532)
pp = route.interpolate(route.project(Point(fx, fy)))
d0 = route.project(pp); a_ = route.interpolate(d0 - 0.05); b_ = route.interpolate(d0 + 0.05)
r = math.atan2(b_.y - a_.y, b_.x - a_.x)
z = ground(pp.x, pp.y)
cx_, cy_ = L(pp.x, pp.y)
for j in range(9):                                         # arche en demi-cercle sous la route
    t = math.pi * j / 8
    ox, oz = math.cos(t) * 0.22, math.sin(t) * 0.22
    k.box(cx_ + math.cos(r) * ox, cy_ + math.sin(r) * ox, z - 0.25 + oz, 0.07, 0.2, 0.04, "calcaire", rz=r)
for s in (-1, 1):
    k.box(cx_ + math.cos(r) * s * 0.25, cy_ + math.sin(r) * s * 0.25, -0.05, 0.08, 0.2, z, "calcaire", rz=r)

# 5. Vallon des Auffes : cabanons et pointus
vx, vy = ll(43.2853, 5.3497)
cab = [(L(vx - 0.25 + j * 0.12, vy + 0.18 + (j % 2) * 0.04) + (math.pi,)) for j in range(5)]
cabanons_bord(k, cab)
petit_port(k, [(L(vx - 0.2 + j * 0.1, vy) + (0.0,)) for j in range(5)])
k.done()
