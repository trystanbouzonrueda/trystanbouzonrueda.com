"""Monuments Meshy (image DA → 3D, 19/11) → un GLB pour le site (island.ts les met à la place des monuments faits main).

blender -b --python blender/build_monuments_meshy.py
Sources : blender/model-try/meshy-1119/<id>.glb (hors git). Sortie : blender/export/monuments_raw.glb
(puis scripts/optimize.mjs → public/models/monuments.glb).
Chaque modèle : un seul objet « mon_<id> », sommets soudés, ≤ 8 000 faces, texture 1024, origine au centre du socle,
plus grande emprise au sol ramenée à 1 (le site le remet à la taille du monument qu'il remplace).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import os

import bpy
import mathutils

SRC = BLENDER_DIR + "model-try/meshy-1119/"
OUT = BLENDER_DIR + "export/monuments_raw.glb"
IDS = ["notre_dame", "velodrome", "gare", "cma_cgm", "dome", "mucem", "major", "longchamp", "cite_radieuse",
       "tour_marseillaise", "eglise_plan_de_cuques", "chateau_if"]
FACES = 8000
TEX = 1024

bpy.ops.wm.read_factory_settings(use_empty=True)
gardes = []
for i, mid in enumerate(IDS):
    f = SRC + mid + ".glb"
    if not os.path.exists(f):
        print("ABSENT", mid)
        continue
    avant = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    nouveaux = [o for o in bpy.data.objects if o not in avant]
    meshes = [o for o in nouveaux if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for x in nouveaux:
        if x != o and x.name in bpy.data.objects:
            bpy.data.objects.remove(x, do_unlink=True)
    n0 = len(o.data.polygons)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")
    if len(o.data.polygons) > FACES:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = FACES / len(o.data.polygons)
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier="dec")
    vs = [v.co for v in o.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
    z0 = min(v.z for v in vs)
    k = 1 / max(x1 - x0, y1 - y0)
    o.data.transform(mathutils.Matrix.Scale(k, 4) @ mathutils.Matrix.Translation((-(x0 + x1) / 2, -(y0 + y1) / 2, -z0)))
    o.name = o.data.name = "mon_" + mid
    for mt in o.data.materials:
        mt.name = "MON_" + mid
    o.location = (0, 0, 0)  # à l'origine : le site garde la transformation du nœud (compression) et place un parent
    o.data.update()
    gardes.append(o)
    print(f"MONUMENT {mid} : {n0} -> {len(o.data.polygons)} faces")

for img in bpy.data.images:
    if img.size[0] > TEX:
        img.scale(TEX, TEX)
bpy.ops.object.select_all(action="DESELECT")
for o in gardes:
    o.select_set(True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_apply=True)
print("EXPORT", OUT, len(gardes), "monuments")
