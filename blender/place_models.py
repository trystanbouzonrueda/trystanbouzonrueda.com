"""Pose les modèles détaillés (models/*.blend, préparés par process_models.py) dans la maquette.

En direct (MCP) : D = ".../blender/"; for f in ("lib.py", "fastkit.py", "quartier.py", "place_models.py"): exec(open(D + f).read())
Relançable. Remplace le monument fait main du lieu (même taille au sol) ou crée le lieu à sa vraie position.
Rotation : la façade des modèles Meshy regarde -y ; r = angle (rad) pour la tourner vers la direction voulue.
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import math

import bpy
from mathutils import Vector

DM = BLENDER_DIR + "models/"
# modèle -> (lieu, lat, lon, taille au sol voulue en unités ou None = celle du monument remplacé, rotation)
POSE = {
    "velodrome": ("velodrome", None, None, None, math.radians(10)),
    "cma_cgm": ("cma_cgm", None, None, None, math.radians(-90)),
    "david": ("david", None, None, None, math.radians(-45)),
    "tour_marseillaise": ("tour_marseillaise", 43.3105, 5.3655, 0.55, math.radians(-90)),
    "eglise_plan_de_cuques": ("eglise_plan_de_cuques", 43.3475, 5.4635, 0.75, 0.0),
}


def bbox_h(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return max(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts))


for nom, (pid, la, lo, taille, rot) in POSE.items():
    old = bpy.data.objects.get("mdl_" + nom)
    taille_old = bbox_h([old]) if old else None   # relance : on garde la taille déjà posée
    if old: bpy.data.objects.remove(old, do_unlink=True)
    e = bpy.data.objects.get("place_" + pid)
    anciens = [c for c in (e.children_recursive if e else []) if c.type == "MESH" and not c.name.startswith("mdl_")]
    if taille is None:
        taille = bbox_h(anciens) if anciens else (taille_old or 1.0)
    for c in anciens:
        bpy.data.objects.remove(c, do_unlink=True)
    if e is None:
        x, y = ll(la, lo)
        e = bpy.data.objects.new("place_" + pid, None); e.empty_display_size = 0.3
        bpy.data.collections["Monuments"].objects.link(e)
        e.location = (x, y, ground(x, y)); e.scale = (1, 1, 1)
    with bpy.data.libraries.load(DM + nom + ".blend", link=False) as (src, dst):
        dst.objects = ["mdl_" + nom]
    o = dst.objects[0]
    bpy.data.collections["Monuments"].objects.link(o)
    dim = max(o.dimensions.x, o.dimensions.y)
    s = taille / (dim * e.scale.x)
    o.parent = e
    o.location = (0, 0, (ground(e.location.x, e.location.y) - e.location.z) / e.scale.z)
    o.scale = (s, s, s); o.rotation_euler = (0, 0, rot)
    o["lot"] = "MDL"; o["place"] = pid
    print(f"{nom} : lieu {pid}, taille {taille:.2f} u, {len(o.data.polygons)} faces")
