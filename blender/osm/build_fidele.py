"""Île « Marseille fidèle » en style tycoon, à partir de marseille.json (OSM). Relançable.

En direct (MCP) : exec(open(".../osm/build_fidele.py").read())
En ligne de commande : blender -b ../marseille.blend --python build_fidele.py  (rend aussi les vues)
Collection « Fidele » reconstruite à chaque passage ; monuments (empties place_*) posés à leur vraie place.
Ancienne île compressée : marseille_compresse_2026-11-17.blend.
"""
import json
import math
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from pyproj import Transformer
from shapely.geometry import MultiPoint, Point, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import delaunay_triangles, segmentize

HERE = Path(globals().get("__file__") or "blender/osm/x").parent
D = json.loads((HERE / "marseille.json").read_text())
U = 1 / 250  # 1 unité Blender = 250 m
BASE = 0.3   # hauteur du sol au-dessus de l'eau
MS = 1.6     # agrandissement des monuments (lisibilité tycoon)
random.seed(13)

_t = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
OX, OY = _t.transform(D["origin"][1], D["origin"][0])


def ll(lat, lon):
    x, y = _t.transform(lon, lat)
    return (x - OX) * U, (y - OY) * U


def sc(g):
    from shapely import affinity
    return affinity.scale(g, U, U, origin=(0, 0))


# ---------- géométrie ----------
commune = sc(shape(D["commune"]))
pdc = sc(shape(D["plan_de_cuques"])).buffer(0) if "plan_de_cuques" in D else None
terre = sc(shape(D["terre"])).buffer(0)  # commune moins la mer (bassins du port creusés)
if pdc:   # on bouche les fentes entre les deux contours, mais seulement près de Plan-de-Cuques (pas les bassins du port)
    ferme = unary_union([terre, pdc]).buffer(0.3).buffer(-0.3).intersection(pdc.buffer(1.0))
    land = unary_union([terre, pdc, ferme])
else:
    land = terre
land = max(land.geoms, key=lambda g: g.area) if land.geom_type == "MultiPolygon" else land
# Vieux-Port : le vrai bassin vient du trait de côte OSM (build_vieux_port.py construit quais et bateaux).
from shapely.geometry import Polygon
# esplanade du J4 (Mucem, fort Saint-Jean) : absente du trait de côte OSM, on la rajoute
J4 = Polygon([ll(a, b) for a, b in ((43.2948, 5.3588), (43.2978, 5.3588), (43.2978, 5.3632), (43.2948, 5.3632))])
land = unary_union([land, J4])
land = max(land.geoms, key=lambda g: g.area) if land.geom_type == "MultiPolygon" else land
arrs = [(a["num"], sc(shape(a["geom"])).buffer(0)) for a in D["arrondissements"]]
coast = land.exterior
from shapely.prepared import prep
coast_s = coast.simplify(0.15)            # assez précis pour le fondu du relief
LAND_IN = prep(land.buffer(-0.3))
LAND_RIB = prep(land.buffer(0.2))
LAND_P = prep(land)

HILLS = [  # lat, lon, rayon (unités), hauteur
    (43.372, 5.400, 12, 2.2), (43.366, 5.445, 10, 1.9), (43.376, 5.360, 9, 1.5),   # Étoile
    (43.310, 5.560, 10, 1.7), (43.285, 5.545, 8, 1.4),                            # Garlaban
    (43.245, 5.500, 12, 1.9), (43.290, 5.480, 6, 0.7),                            # Carpiagne, St-Marcel
    (43.212, 5.375, 10, 2.1), (43.215, 5.430, 10, 1.9), (43.220, 5.470, 9, 2.0),  # Marseilleveyre, Calanques
    (43.2840, 5.3713, 2.2, 2.3),                                                   # Notre-Dame
]
HILLS = [(*ll(a, b), r, h) for a, b, r, h in HILLS]


def height(x, y):
    h = sum(H * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / r ** 2) for hx, hy, r, H in HILLS)
    d = coast_s.distance(Point(x, y))
    return BASE + h * min(1.0, d / 1.5) ** 1.5


# ---------- scène : on garde monuments, lumière, monde ----------
# (« Quartiers » n'est plus vidée : FastKit y range les arrondissements faits main)
for cname in ("Terrain", "Zonage", "Ilots", "Mer", "Vie"):
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
for n in ("place_planche",):
    o = bpy.data.objects.get(n)
    if o:
        for ch in o.children_recursive: bpy.data.objects.remove(ch, do_unlink=True)
        bpy.data.objects.remove(o, do_unlink=True)

col = bpy.data.collections.get("Fidele")
if col is None:
    col = bpy.data.collections.new("Fidele"); bpy.context.scene.collection.children.link(col)
for o in list(col.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for me in [m for m in bpy.data.meshes if m.users == 0]:
    bpy.data.meshes.remove(me)


def mat(name, hexcol, rough=0.85):
    m = bpy.data.materials.get("M_" + name) or bpy.data.materials.new("M_" + name)
    m.use_nodes = True
    h = hexcol.lstrip("#"); c = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)] + [1]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    m.diffuse_color = c
    return m


def obj(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    return o


# ---------- socle flottant : mer seulement du côté de la vraie mer (plateau.py) ----------
minx, miny, maxx, maxy = land.buffer(7).bounds
exec(open(HERE / "plateau.py").read())

# ---------- île : sol triangulé avec relief ----------
pts = list(segmentize(coast, 0.3).coords)
gx = np.arange(minx, maxx, 1.0); gy = np.arange(miny, maxy, 1.0)
inner = prep(land.buffer(-0.4))
pts += [(x + random.uniform(-.2, .2), y + random.uniform(-.2, .2)) for x in gx for y in gy if inner.contains(Point(x, y))]
# anneaux de points le long de la côte (vers l'intérieur) : sinon, sur une côte découpée, des triangles
# relient la côte à des points lointains, sortent des terres et sont jetés -> trous dans le sol
for d_ in (0.12, 0.3, 0.6):
    ring_ = land.buffer(-d_)
    for pg_ in getattr(ring_, "geoms", [ring_]):
        if pg_.geom_type == "Polygon" and pg_.area > 0.05:
            pts += list(segmentize(pg_.exterior, 0.3).coords)
            for it_ in pg_.interiors:
                pts += list(segmentize(it_, 0.3).coords)
for it_ in land.interiors:
    pts += list(segmentize(it_, 0.3).coords)
tris = [t for t in delaunay_triangles(MultiPoint(pts)).geoms if LAND_P.contains(t.centroid)]

TINT = {1: "#d9c9a3", 2: "#d6c49c", 3: "#d4c7a2", 4: "#dccca4", 5: "#d8caa6", 6: "#ddcea8", 7: "#c9d79a",
        8: "#c3d690", 9: "#b9cf86", 10: "#cbd598", 11: "#b6cd84", 12: "#c4d38f", 13: "#b3cb80",
        14: "#c8d295", 15: "#cfcf9c", 16: "#bfd08c", 0: "#c6d99b"}
gmats = [mat(f"sol_{k}", v) for k, v in TINT.items()] + [mat("garrigue", "#9fb873"), mat("calcaire", "#e8e1cf"),
                                                          mat("falaise", "#d9cdb2")]
gidx = {k: i for i, k in enumerate(TINT)}
atree = STRtree([g for _, g in arrs])
hcache = {}


def hz(p):
    k = (round(p[0], 3), round(p[1], 3))
    if k not in hcache: hcache[k] = height(*k)
    return hcache[k]


bm = bmesh.new(); vmap = {}
for t in tris:
    cs = list(t.exterior.coords)[:3]
    vs = []
    for p in cs:
        k = (round(p[0], 3), round(p[1], 3))
        if k not in vmap: vmap[k] = bm.verts.new((k[0], k[1], hz(k)))
        vs.append(vmap[k])
    try:
        f = bm.faces.new(vs)
    except ValueError:
        continue
    zc = sum(v.co.z for v in vs) / 3
    c = t.centroid
    if zc > BASE + 1.3: f.material_index = gidx[0] + len(TINT) + 1   # sommets calcaires
    elif zc > BASE + 0.6: f.material_index = len(TINT)               # garrigue
    else:
        hit = [i for i in atree.query(c) if arrs[i][1].contains(c)]
        f.material_index = gidx[arrs[hit[0]][0]] if hit else gidx[0]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
obj("ile_sol", bm, gmats)

# falaises : du trait de côte jusqu'à l'eau
cring = list(segmentize(coast, 0.3).coords)[:-1]
bm = bmesh.new()
up = [bm.verts.new((x, y, hz((x, y)))) for x, y in cring]
dn = [bm.verts.new((x, y, -0.05)) for x, y in cring]
for i in range(len(cring)):
    bm.faces.new((up[i - 1], up[i], dn[i], dn[i - 1]))
obj("ile_falaise", bm, [gmats[-1]])

# îles (Frioul, If, Riou…) : petits plateaux calcaires ; If élargie pour tenir le château
iles = []
for i in D["iles"]:
    g = sc(shape(i["geom"])).buffer(0)
    if g.area < 0.02 or g.intersects(commune.buffer(-1)): continue
    if "If" in i["name"] and "Frioul" not in i["name"]: g = g.buffer(0.7)
    iles.append(g)
bm = bmesh.new()
for g in iles:
    for poly in getattr(g, "geoms", [g]):
        r = list(poly.exterior.coords)[:-1]
        if len(r) < 3: continue
        h = 0.25 + min(0.6, poly.area * 0.05)
        t_ = [bm.verts.new((x, y, h)) for x, y in r]; b_ = [bm.verts.new((x, y, -0.05)) for x, y in r]
        try:
            bm.faces.new(t_)
        except ValueError:
            pass
        for k in range(len(r)): bm.faces.new((t_[k - 1], t_[k], b_[k], b_[k - 1]))
obj("iles", bm, [gmats[-2]])

# ---------- rubans : routes, tram, métro ----------
def ribbons(name, lines, width, m, dz, thick=0.05):
    bm = bmesh.new()
    for ln in lines:
        pts = [p for p in segmentize(ln, 0.5).coords if LAND_RIB.contains(Point(p))]
        if len(pts) < 2: continue
        P = [Vector((x, y, hz((x, y)) + dz)) for x, y in pts]
        L, R = [], []
        for i, p in enumerate(P):
            a = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
            n = Vector((-a.y, a.x, 0)).normalized() * width / 2
            L.append(bm.verts.new(p + n)); R.append(bm.verts.new(p - n))
        for i in range(len(P) - 1):
            try: bm.faces.new((L[i], R[i], R[i + 1], L[i + 1]))
            except ValueError: pass
    return obj(name, bm, [m])


def lines_of(geoms):
    out = []
    for g in geoms:
        g = sc(shape(g))
        out += list(getattr(g, "geoms", [g]))
    return out


route_lines = {r: lines_of(D["routes"].get(r, [])) for r in ("1", "2", "3")}
# (chaussées : build_routes.py dessine toute la voirie unifiée, collection « Voirie »)
tram = [l for v in D["tram"].values() for l in lines_of(v["lines"])]
ribbons("tram", tram, 0.12, mat("tram", "#7d8b99"), 0.055)
MCOL = {"M1": "#1d5fbf", "M2": "#d6232a"}
from shapely.geometry import LineString
metro_lines = {ref: LineString([(x * U, y * U) for x, y in v["line"]]) for ref, v in D["metro_path"].items()}
for ref, ln in metro_lines.items():
    ribbons("metro_" + ref, [ln], 0.3, mat("metro_" + ref, MCOL.get(ref, "#333")), 0.07)

# stations : édicule blanc + cube « M » bleu
bm = bmesh.new()
for s in D["metro_stations"]:
    x, y = s["xy"][0] * U, s["xy"][1] * U; z = hz((x, y))
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, y, z + 0.12)) @ Matrix.Diagonal((0.34, 0.34, 0.18, 1)))
st = obj("stations", bm, [mat("blanc_station", "#ffffff")])
bm = bmesh.new()
for s in D["metro_stations"]:
    x, y = s["xy"][0] * U, s["xy"][1] * U; z = hz((x, y))
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x + 0.2, y, z + 0.45)) @ Matrix.Diagonal((0.08, 0.2, 0.2, 1)))
obj("stations_M", bm, [mat("bleu_rtm", "#1d5fbf")])

# ---------- monuments faits main à leur vraie place ----------
PLACES = {
    "notre_dame": (43.2840, 5.3713), "velodrome": (43.2698, 5.3959), "mucem": (43.2967, 5.3611),
    "major": (43.2995, 5.3653), "dome": (43.3069, 5.3967), "longchamp": (43.3046, 5.3943),
    "gare": (43.3027, 5.3806), "cma_cgm": (43.3123, 5.3658), "cite_radieuse": (43.2613, 5.3963),
    "david": (43.2594, 5.3754), "borely": (43.2560, 5.3829), "chateau_if": (43.2799, 5.3254),
"calanques": (43.2094, 5.4183),
    "navette": (43.2905, 5.3420), "city_jul": (43.2828, 5.3723),
}
SCALE = {"vieux_port": 1.0, "corniche": 1.15, "city_jul": 1.2}
cat_x, cat_y = ll(43.2915, 5.3600); dav_x, dav_y = ll(43.2700, 5.3735)
ROT = {"corniche": math.atan2(cat_y - dav_y, cat_x - dav_x) - math.pi / 2}
monus = []
for pid, (lat, lon) in PLACES.items():
    e = bpy.data.objects.get("place_" + pid)
    if e is None: continue
    x, y = ll(lat, lon)
    # (Corniche et Vieux-Port : construits par build_corniche.py / build_vieux_port.py, pas déplacés ici)
    if pid == "city_jul": x, y = 3.5, -14.7   # sur le plat des plages du Prado (sur la colline de Notre-Dame, son socle dépassait)
    # hauteur = sol (au point le plus haut de l'emprise) + décalage fixe : relançable sans dérive
    r_ = 0.5 if pid not in ("calanques", "borely", "velodrome", "longchamp") else 0.9
    sol_ = max(hz((x + dx_, y + dy_)) for dx_ in (-r_, 0, r_) for dy_ in (-r_, 0, r_)) if pid != "notre_dame" else hz((x, y))
    z = {"navette": -0.1, "chateau_if": 0.3}.get(pid, sol_)
    if pid == "chateau_if": z = 0.3
    s_ = SCALE.get(pid, MS)
    e.location = (x, y, z); e.scale = (s_, s_, s_); e.rotation_euler = (0, 0, ROT.get(pid, 0.0))
    if pid != "corniche": monus.append((x, y, 1.6 if pid != "vieux_port" else 2.6))

# ---------- tissu urbain : blocs par arrondissement ----------
# (densité par unité², hauteur min, max, part de barres de cité)
TISSU = {1: (5, .35, .7, 0), 2: (4.5, .3, .65, .05), 3: (4, .3, .6, .05), 4: (4, .3, .6, 0), 5: (4.5, .3, .6, 0),
         6: (4.5, .3, .7, 0), 7: (2.6, .2, .45, 0), 8: (2.0, .18, .5, .05), 9: (1.2, .15, .45, .08),
         10: (2.4, .2, .55, .1), 11: (1.3, .15, .4, .05), 12: (1.8, .15, .4, .05), 13: (1.4, .15, .55, .15),
         14: (2.2, .2, .65, .25), 15: (2.0, .2, .6, .2), 16: (1.3, .15, .35, .05)}
FAC = [("facade_creme", "#f1e4c6"), ("facade_ocre", "#e3b77a"), ("facade_rose", "#e9b1a0"),
       ("facade_jaune", "#f0d58a"), ("facade_saumon", "#eaa784"), ("facade_blanche", "#f6f1e7")]
fmats = [mat(n, c) for n, c in FAC] + [mat("tuile_toit", "#c8643c"), mat("toit_plat", "#d9d4c8")]
roads_buf = unary_union([l.buffer(w) for r, w in (("1", .35), ("2", .25), ("3", .16)) for l in route_lines[r]]
                        + [l.buffer(.3) for l in metro_lines.values()])
rtree = STRtree(list(getattr(roads_buf, "geoms", [roads_buf])))
mon_buf = unary_union([Point(x, y).buffer(r) for x, y, r in monus])
bm = bmesh.new(); trees = []
nb = 0
for num, g in arrs:
    if bpy.data.objects.get(f"mh_arr{num:02d}"):  # arrondissement déjà fait main (build_arrNN.py)
        continue
    dens, h0, h1, barres = TISSU[num]
    gx0, gy0, gx1, gy1 = g.bounds
    n = int(g.area * dens)
    for _ in range(n * 3):
        if n <= 0: break
        x, y = random.uniform(gx0, gx1), random.uniform(gy0, gy1)
        p = Point(x, y)
        if not g.contains(p) or not LAND_IN.contains(p) or mon_buf.contains(p): continue
        if any(rtree.geometries[i].contains(p) for i in rtree.query(p)): continue
        z = hz((x, y))
        if z > BASE + 0.55:
            if random.random() < 0.15: trees.append((x, y, z))
            continue
        n -= 1
        if random.random() < barres:
            w, d, h, roof = random.uniform(.9, 1.4), .28, random.uniform(.6, 1.1), 7
        else:
            w, d = random.uniform(.22, .42), random.uniform(.22, .42)
            h = random.uniform(h0, h1); roof = 6 if random.random() < .7 else 7
        rot = random.uniform(0, math.pi)
        M = Matrix.Translation((x, y, z + h / 2 - 0.02)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((w, d, h, 1))
        r = bmesh.ops.create_cube(bm, size=1, matrix=M)
        fm = random.randrange(len(FAC))
        for f in {f for v in r["verts"] for f in v.link_faces}:
            f.material_index = roof if f.calc_center_median().z > z + h - 0.03 else fm
        nb += 1
        if random.random() < 0.25: trees.append((x + random.uniform(-.4, .4), y + random.uniform(-.4, .4), z))
obj("tissu", bm, fmats)

# arbres : villes + pinèdes sur les reliefs
for _ in range(2500):
    x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
    p = Point(x, y)
    if LAND_IN.contains(p) and not mon_buf.contains(p):
        z = hz((x, y))
        # pinèdes des reliefs partout ; en ville seulement si l'arrondissement n'est pas encore fait main
        en_ville = any(bpy.data.objects.get(f"mh_arr{n:02d}") and g.contains(p) for n, g in arrs)
        if BASE + 0.15 < z < BASE + 1.6 and (not en_ville or z > BASE + 0.5): trees.append((x, y, z))
bm = bmesh.new()
for x, y, z in trees:
    s = random.uniform(.12, .2)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s, matrix=Matrix.Translation((x, y, z + s * 1.1)))
obj("arbres", bm, [mat("pin", "#4f9a46")])

# ---------- lumière, monde, caméras, rendu ----------
sc_ = bpy.context.scene
w = sc_.world
if w and w.use_nodes:
    bg = next((n for n in w.node_tree.nodes if n.type == "BACKGROUND"), None)
    if bg: bg.inputs[0].default_value = (0.62, 0.80, 0.93, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects["Soleil"]; sun.data.energy = 3.2
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))


def camera(name, target, offset, lens):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); col.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_end = 2000
    cam.location = Vector(target) + Vector(offset)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


ccx, ccy = land.centroid.x, land.centroid.y
shots = {
    "ensemble": camera("Cam_ensemble", (ccx, ccy - 6, 0), (38, -105, 92), 32),
    "centre": camera("Cam_centre", (3, 1, 0.5), (14, -26, 19), 36),
    "nord": camera("Cam_nord", (2, 22, 0.5), (-34, -30, 30), 35),
}
sc_.render.resolution_x, sc_.render.resolution_y = 1600, 1000
try:
    sc_.eevee.taa_render_samples = 48
except AttributeError:
    pass
sc_.view_settings.view_transform = "Standard"
for k, cam in (shots.items() if bpy.app.background else []):
    sc_.camera = cam
    sc_.render.filepath = str(HERE / f"preview_3d_{k}.png")
    bpy.ops.render.render(write_still=True)
print(f"FIDELE OK : {len(tris)} triangles de sol, {nb} bâtiments, {len(trees)} arbres")
