"""Socle flottant de l'île : la mer seulement du côté de la vraie mer, la roche ailleurs.

Avant : un grand rectangle de mer entourait toute la ville (de l'eau jusque derrière Plan-de-Cuques).
Maintenant : socle = terre ∪ mer réelle ; la mer réelle = zone plus proche du trait de côte OSM
que des limites terrestres de la commune. Bords côté mer en bleu, bords côté terre en roche.

En direct (MCP) : exec(open(".../osm/plateau.py").read())   (remplace l'objet plateau_mer)
Appelé aussi par build_fidele.py.
"""
import json
from pathlib import Path

import bmesh
import bpy
import numpy as np
from pyproj import Transformer
from shapely import affinity
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union
from shapely.prepared import prep

_H = Path(globals().get("__file__") or "blender/osm/x").resolve().parent
_D = json.loads((_H / "marseille.json").read_text())
_U = 1 / 250
_t = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
_OX, _OY = _t.transform(_D["origin"][1], _D["origin"][0])
_sc = lambda g: affinity.scale(g, _U, _U, origin=(0, 0))


def _ll(lat, lon):
    x, y = _t.transform(lon, lat)
    return (x - _OX) * _U, (y - _OY) * _U


# ---------- terre (même construction que build_fidele.py)
_terre = _sc(shape(_D["terre"])).buffer(0)
_pdc = _sc(shape(_D["plan_de_cuques"])).buffer(0)
_ferme = unary_union([_terre, _pdc]).buffer(0.3).buffer(-0.3).intersection(_pdc.buffer(1.0))
_land = unary_union([_terre, _pdc, _ferme])
_land = max(_land.geoms, key=lambda g: g.area) if _land.geom_type == "MultiPolygon" else _land
_J4 = Polygon([_ll(a, b) for a, b in ((43.2948, 5.3588), (43.2978, 5.3588), (43.2978, 5.3632), (43.2948, 5.3632))])
_land = unary_union([_land, _J4])
_land = max(_land.geoms, key=lambda g: g.area) if _land.geom_type == "MultiPolygon" else _land

# ---------- mer réelle : cellules plus proches du trait de côte que des limites terrestres
_cote = unary_union([_sc(shape(g)) for g in (_D["cote"] if isinstance(_D["cote"], list) else [_D["cote"]])])
_cote = _cote.intersection(_land.buffer(0.4)).simplify(0.2)        # le trait de côte qui borde la ville
_interieur = _land.exterior.difference(_cote.buffer(0.25)).simplify(0.2)  # limites communales sur terre
plate = _land.buffer(9).envelope.buffer(-4).buffer(4, quad_segs=6)
x0, y0, x1, y1 = plate.bounds
_lp, _pp = prep(_land), prep(plate)
STEP = 0.8
cells = []
for x in np.arange(x0, x1, STEP):
    for y in np.arange(y0, y1, STEP):
        c = Point(x + STEP / 2, y + STEP / 2)
        if not _pp.contains(c) or _lp.contains(c):
            continue
        if c.distance(_cote) < c.distance(_interieur):
            cells.append(box(x, y, x + STEP, y + STEP))
mer = unary_union(cells).buffer(1.2).buffer(-1.2).intersection(plate).difference(_land.buffer(-0.05))
socle = unary_union([mer, _land.buffer(0.02)]).buffer(0.3).buffer(-0.3)
socle = max(socle.geoms, key=lambda g: g.area) if socle.geom_type == "MultiPolygon" else socle
socle = Polygon(socle.exterior).simplify(0.12)
MER_P = prep(mer.buffer(0.4))


def _mat(name, hexcol, rough=0.85):
    m = bpy.data.materials.get("M_" + name) or bpy.data.materials.new("M_" + name)
    m.use_nodes = True
    h = hexcol.lstrip("#"); c = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)] + [1]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    m.diffuse_color = c
    return m


def construit():
    old = bpy.data.objects.get("plateau_mer")
    cols = list(old.users_collection) if old else [bpy.data.collections.get("Fidele") or bpy.context.scene.collection]
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ring = list(socle.exterior.coords)[:-1]
    if Polygon(ring).exterior.is_ccw is False:
        ring.reverse()
    bm = bmesh.new()
    levels = [(0.0, 1.0), (-0.8, 1.0), (-3.0, 0.93), (-9.0, 0.6), (-16.0, 0.18)]
    cx, cy = socle.centroid.x, socle.centroid.y
    rings = [[bm.verts.new((cx + (x - cx) * s, cy + (y - cy) * s, z)) for x, y in ring] for z, s in levels]
    top = bm.faces.new(rings[0]); top.material_index = 0
    n = len(ring)
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(n):
            f = bm.faces.new((a[i - 1], a[i], b[i], b[i - 1]))
            mx, my = (ring[i][0] + ring[i - 1][0]) / 2, (ring[i][1] + ring[i - 1][1]) / 2
            cote_mer = MER_P.contains(Point(mx, my))
            f.material_index = (1 if cote_mer else 3) if k == 0 else 2   # bandeau d'eau côté mer, roche côté terre
    bm.faces.new(list(reversed(rings[-1]))).material_index = 2
    bmesh.ops.triangulate(bm, faces=[top])                              # dessus concave : triangulé proprement
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("plateau_mer"); bm.to_mesh(me); bm.free()
    for m in (_mat("mer", "#5bb8d6", 0.25), _mat("mer_bord", "#3b94b8"), _mat("roche_socle", "#9a8a72"),
              _mat("falaise", "#d9cdb2")):
        me.materials.append(m)
    o = bpy.data.objects.new("plateau_mer", me)
    for c in cols:
        c.objects.link(o)
    print("plateau_mer", len(ring), "points ; mer", round(mer.area), "u², socle", round(socle.area), "u²")
    return o


construit()
