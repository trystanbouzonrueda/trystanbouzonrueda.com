"""Réseau de voirie unifié et cohérent (sert aussi de sol marchable pour le mode visite).

En direct : run_async.lancer(["build_routes.py"])  (ou exec après lib/batiments/fastkit/quartier)
Toutes les voies OSM (grands axes de marseille.json + rues fines des 16 arrondissements et de
Plan-de-Cuques) sont fusionnées par classe — autoroute, route, rue, quai — avec les mêmes largeurs
que celles utilisées pour poser les bâtiments (quartier.HALF). Une classe supérieure recouvre les
autres (pas de chevauchement ni de scintillement), carrefours propres, surface drapée sur le relief.
Découpage en tuiles de 6 unités : objets « voirie_<classe>_<i>_<j> » dans la collection « Voirie ».
Les anciens rubans de build_fidele (routes_1/2/3, autoroutes) sont supprimés.
"""
import math

import bmesh
import bpy
from shapely import affinity, constrained_delaunay_triangles
from shapely.geometry import LineString, MultiPolygon, Polygon, box as sbox, shape
from shapely.ops import unary_union

TUILE = 6.0
DENSIFIE = 0.28      # pas des bords : assez court pour suivre le relief, sans trop de triangles
CLASSES = [          # (nom, matériau, couleur, décalage au-dessus du sol)
    ("autoroute", "voirie_autoroute", "#8f949b", 0.040),
    ("route", "voirie_route", "#f4efe4", 0.034),
    ("rue", "voirie_rue", "#e9e2d2", 0.028),
    ("quai", "pierre_quai", "#d8c9a8", 0.030),
]
LARG = {"La Canebière": 0.09, "Rue de la République": 0.07, "Boulevard Jacques Saadé": 0.09}

for n in ("routes_1", "routes_2", "routes_3", "autoroutes"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
col = bpy.data.collections.get("Voirie")
if col is None:
    col = bpy.data.collections.new("Voirie"); bpy.context.scene.collection.children.link(col)
for o in list(col.objects):
    bpy.data.objects.remove(o, do_unlink=True)

S = lambda g: affinity.scale(shape(g), U, U, origin=(0, 0))
terre = S(_D["terre"]).buffer(0)
if "plan_de_cuques" in _D:
    terre = unary_union([terre, S(_D["plan_de_cuques"]).buffer(0.3)])

# ------------------------------------------------------------------ lignes par classe
auto, route, rue = [], [], []
for g in _D["routes"].get("1", []):
    auto.append(S(g).buffer(0.18, cap_style="round"))
for g in _D["routes"].get("2", []):
    route.append(S(g).buffer(0.11))
vus = set()
fichiers = [OSM / "raw" / f"rues_{n}.json" for n in range(1, 17)] + [OSM / "raw" / "rues_pdc.json"]
for f in fichiers:
    if not f.exists(): continue
    for w in json.loads(f.read_text())["elements"]:
        if w["id"] in vus or not w.get("geometry"): continue
        vus.add(w["id"])
        t = w["tags"]
        if t.get("area") == "yes" or t.get("tunnel") == "yes": continue
        if w["geometry"][0] == w["geometry"][-1] and t["highway"] == "pedestrian": continue
        l = LineString([ll(p["lat"], p["lon"]) for p in w["geometry"]])
        half = LARG.get(t.get("name", ""), HALF.get(t["highway"], 0.03))
        (route if t["highway"] in ("primary", "secondary") else rue).append(l.buffer(half))
print("voies", len(auto), len(route), len(rue))

A = unary_union(auto).intersection(terre)
R = unary_union(route).difference(A).intersection(terre)
P = unary_union(rue).difference(A).difference(R).intersection(terre)
b = bassin_vp()
Q = b.buffer(0.13).difference(b).difference(A).difference(R).difference(P)   # quais du Vieux-Port
# contours simplifiés (1,5 m) : moins de sommets, carrefours identiques à l'œil
A, R, P = (g.simplify(0.006, preserve_topology=True) for g in (A, R, P))
polys = {"autoroute": A, "route": R, "rue": P, "quai": Q}
print("surfaces", {k: round(v.area, 1) for k, v in polys.items()})

# ------------------------------------------------------------------ maillage drapé, par tuiles
mats = {nom: mat(m, c) for nom, m, c, _ in CLASSES}
dzs = {nom: dz for nom, _, _, dz in CLASSES}
ile = bpy.data.objects["ile_sol"]
from mathutils import Vector


def sol(x, y):
    ok, loc, *_ = ile.ray_cast(Vector((x, y, 40)), Vector((0, 0, -1)))
    return loc.z if ok else 0.3


def trianguler(poly):
    """Triangulation contrainte ; si GEOS échoue (polygone dégénéré), on nettoie et on réessaie,
    sinon Delaunay simple des sommets en ne gardant que les triangles intérieurs."""
    from shapely import delaunay_triangles, make_valid
    from shapely.geometry import MultiPoint
    for essai in (poly, poly.buffer(0).simplify(0.003), make_valid(poly.simplify(0.01))):
        try:
            out = []
            for pg in getattr(essai, "geoms", [essai]):
                if pg.geom_type != "Polygon" or pg.area < 1e-5: continue
                dense = Polygon(pg.exterior.segmentize(DENSIFIE), [r.segmentize(DENSIFIE) for r in pg.interiors])
                out += list(constrained_delaunay_triangles(dense).geoms)
            return out
        except Exception:
            continue
    pts = MultiPoint(list(poly.exterior.segmentize(DENSIFIE).coords))
    return [t for t in delaunay_triangles(pts).geoms if poly.contains(t.representative_point())]


x0, y0, x1, y1 = terre.bounds
nb_obj, nb_tri = 0, 0
for nom, geom in polys.items():
    if geom.is_empty: continue
    i = 0
    tx = x0
    while tx < x1:
        j = 0
        ty = y0
        while ty < y1:
            part = geom.intersection(sbox(tx, ty, tx + TUILE, ty + TUILE))
            if not part.is_empty:
                bm = bmesh.new(); vmap = {}
                for poly in getattr(part, "geoms", [part]):
                    if poly.geom_type != "Polygon" or poly.area < 1e-5: continue
                    for tri in trianguler(poly):
                        vs = []
                        for x, y in list(tri.exterior.coords)[:3]:
                            key = (round(x, 4), round(y, 4))
                            if key not in vmap:
                                vmap[key] = bm.verts.new((x, y, sol(x, y) + dzs[nom]))
                            vs.append(vmap[key])
                        try:
                            f = bm.faces.new(vs)
                            if f.normal.z < 0: f.normal_flip()
                            nb_tri += 1
                        except ValueError:
                            pass
                if len(bm.faces):
                    me = bpy.data.meshes.new(f"voirie_{nom}_{i}_{j}")
                    bm.to_mesh(me); me.materials.append(mats[nom])
                    o = bpy.data.objects.new(me.name, me); col.objects.link(o)
                    o["walkable"] = True
                    nb_obj += 1
                bm.free()
            ty += TUILE; j += 1
        tx += TUILE; i += 1
print(f"voirie : {nb_obj} tuiles, {nb_tri} triangles")
