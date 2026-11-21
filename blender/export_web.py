"""Export web de la maquette : deux GLB + les données du métro.

blender -b marseille.blend --python export_web.py
  -> export/marseille_base_raw.glb    : île, routes, monuments, volumes des quartiers (affiché tout de suite)
  -> export/marseille_details_raw.glb : objets *_det (fenêtres, balcons…), chargés ensuite, affichés de près
  -> ../public/data/metro.json         : tracés M1/M2 et stations, en coordonnées three.js (y vers le haut)
Puis : npm run models (glTF-Transform : meshopt, textures webp) -> public/models/.
"""
import json
from pathlib import Path

import bpy

HERE = Path(bpy.data.filepath).parent
OUT = HERE / "export"
OUT.mkdir(exist_ok=True)
PUB = HERE.parent / "public" / "data"
PUB.mkdir(parents=True, exist_ok=True)

garde = [o for o in bpy.data.objects if o.type in ("MESH", "EMPTY") and o.visible_get()]
details = [o for o in garde if o.name.endswith("_det")]
base = [o for o in garde if o not in details]


def export(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    sel = set(objs)
    for o in objs:  # les parents (empties place_*) gardent la hiérarchie et les noms
        p = o.parent
        while p:
            sel.add(p); p = p.parent
    for o in sel:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False,
                              export_extras=False, export_image_format="AUTO")
    faces = sum(len(o.data.polygons) for o in objs if o.type == "MESH")
    print(f"EXPORT {path.name} : {len(objs)} objets, {faces} faces")


export(base, OUT / "marseille_base_raw.glb")
export(details, OUT / "marseille_details_raw.glb")

# ------------------------------------------------------------------ métro (tracés au sol, y = hauteur)
import sys
sys.path.insert(0, str(HERE))
D = json.loads((HERE / "osm" / "marseille.json").read_text())
U = 1 / 250
ile = bpy.data.objects["ile_sol"]
from mathutils import Vector


def hz(x, y):
    ok, loc, *_ = ile.ray_cast(Vector((x, y, 40)), Vector((0, 0, -1)))
    return loc.z if ok else 0.3


def three(x, y, dz=0.09):
    return [round(x, 3), round(hz(x, y) + dz, 3), round(-y, 3)]   # Blender (x, y, z) -> three (x, z, -y)


noms = {tuple(round(c, 1) for c in s["xy"]): s["name"] for s in D["metro_stations"]}
metro = {}
for ref, v in D["metro_path"].items():
    stations = []
    for sx, sy in v["stations"]:
        name = min(D["metro_stations"], key=lambda s: (s["xy"][0] - sx) ** 2 + (s["xy"][1] - sy) ** 2)["name"]
        stations.append({"name": name, "p": three(sx * U, sy * U)})
    metro[ref] = {"color": {"M1": "#1d5fbf", "M2": "#d6232a"}.get(ref, "#333"),
                  "line": [three(x * U, y * U) for x, y in v["line"]], "stations": stations}
(PUB / "metro.json").write_text(json.dumps(metro, ensure_ascii=False))
print("METRO", {k: (len(v["line"]), len(v["stations"])) for k, v in metro.items()})

# ------------------------------------------------------------------ circulation (trajets préenregistrés)
# Voitures sur les grands axes : polylignes OSM (rangs 1 et 2) assez longues, posées sur la voirie.
import random
from shapely.geometry import shape as _shape
from shapely.ops import linemerge as _lm
random.seed(7)
voirie = [o for o in bpy.data.objects if o.name.startswith("voirie_") and o.type == "MESH"]


def sur_voirie(x, y):
    best = None
    for o in voirie:
        ok, loc, *_ = o.ray_cast(Vector((x, y, 40)) - o.location, Vector((0, 0, -1)))
        if ok and (best is None or loc.z > best): best = loc.z
    return best


lignes = []
for rang in ("1", "2"):
    for g in D["routes"].get(rang, []):
        l = _shape(g)
        for part in getattr(l, "geoms", [l]):
            if part.length * U > 3.0: lignes.append((rang, part))
random.shuffle(lignes)
trafic = []
for rang, l in lignes[:60]:
    pts = []
    n = max(2, int(l.length * U / 0.25))
    for i in range(n + 1):
        p = l.interpolate(i / n, normalized=True)
        x, y = p.x * U, p.y * U
        z = sur_voirie(x, y)
        if z is None:
            if len(pts) > 6: break
            pts = []; continue
        pts.append([round(x, 3), round(z + 0.012, 3), round(-y, 3)])
    if len(pts) > 6:
        trafic.append({"pts": pts, "voie": rang})
(PUB / "trafic.json").write_text(json.dumps(trafic))
print("TRAFIC", len(trafic), "trajets")

# ------------------------------------------------------------------ passants : trajets de rue préenregistrés (silhouettes instanciées)
from shapely.geometry import LineString as _LS
import pyproj as _pp
_t = _pp.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
_ox, _oy = _t.transform(D["origin"][1], D["origin"][0])


def _ll(lat, lon):
    x, y = _t.transform(lon, lat)
    return (x - _ox) * U, (y - _oy) * U


pietons = []
for n in list(range(1, 17)):
    f = HERE / "osm" / "raw" / f"rues_{n}.json"
    if not f.exists(): continue
    ways = [w for w in json.loads(f.read_text())["elements"]
            if w.get("geometry") and w["tags"].get("highway") in ("residential", "pedestrian", "living_street", "tertiary")
            and w["tags"].get("area") != "yes"]
    random.shuffle(ways)
    quota = 60 if n <= 7 else 25          # plus de monde dans le centre
    for w in ways[:quota * 2]:
        l = _LS([_ll(p["lat"], p["lon"]) for p in w["geometry"]])
        if l.length < 0.4: continue
        pts = []
        k = max(2, int(l.length / 0.12))
        for i in range(k + 1):
            p = l.interpolate(i / k, normalized=True)
            z = sur_voirie(p.x, p.y)
            if z is None:
                if len(pts) > 3: break
                pts = []; continue
            pts.append([round(p.x, 3), round(z, 3), round(-p.y, 3)])
        if len(pts) > 3:
            pietons.append(pts)
(PUB / "pietons.json").write_text(json.dumps(pietons))
print("PIETONS", len(pietons), "trajets")
