"""Bateaux Meshy (ferry, navette du Frioul, voilier) → un GLB léger pour vie.ts.

blender -b --python blender/build_bateaux.py
Sources : blender/model-try/meshy-1119/{ferry,navette,voilier}.glb (hors git, générés le 19/11).
Chaque bateau : sommets soudés, simplifié, texture 512, proue tournée vers +X (sens de marche dans vie.ts),
mis à la longueur voulue, origine au centre de la coque, ligne de flottaison à z = 0.
Sortie : blender/export/bateaux_raw.glb (puis scripts/optimize.mjs → public/models/bateaux.glb).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import math
import os

import bpy
import mathutils

SRC = BLENDER_DIR + "model-try/meshy-1119/"
OUT = BLENDER_DIR + "export/bateaux_raw.glb"
# nom : (longueur en unités de l'île, faces visées, part de la hauteur sous l'eau)
BATEAUX = {
    "ferry": (1.0, 3000, 0.16),
    "navette": (0.32, 2500, 0.2),
    "voilier": (0.2, 2000, 0.08),
}
TEX = 512

bpy.ops.wm.read_factory_settings(use_empty=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
gardes = []
for nom, (longueur, faces, immersion) in BATEAUX.items():
    avant = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC + nom + ".glb")
    nouveaux = [o for o in bpy.data.objects if o not in avant]
    mesh_objs = [o for o in nouveaux if o.type == "MESH"]
    # un seul objet par bateau, transformations appliquées
    bpy.ops.object.select_all(action="DESELECT")
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    if len(mesh_objs) > 1:
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
    if len(o.data.polygons) > faces:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = faces / len(o.data.polygons)
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier="dec")

    # axe long horizontal → X ; proue = bout le plus étroit (largeur des sommets dans les 15 % d'extrémité)
    vs = [v.co.copy() for v in o.data.vertices]
    ex = max(v.x for v in vs) - min(v.x for v in vs)
    ey = max(v.y for v in vs) - min(v.y for v in vs)
    rot = mathutils.Matrix.Rotation(math.pi / 2, 4, "Z") if ey > ex else mathutils.Matrix.Identity(4)
    o.data.transform(rot)
    vs = [v.co.copy() for v in o.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    bout = 0.15 * (x1 - x0)

    def largeur(cond):
        ys = [v.y for v in vs if cond(v)]
        return (max(ys) - min(ys)) if ys else 0

    if largeur(lambda v: v.x < x0 + bout) < largeur(lambda v: v.x > x1 - bout):
        o.data.transform(mathutils.Matrix.Rotation(math.pi, 4, "Z"))  # la proue était côté -X

    # échelle, origine au centre, flottaison
    vs = [v.co.copy() for v in o.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
    z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
    k = longueur / (x1 - x0)
    o.data.transform(mathutils.Matrix.Scale(k, 4) @ mathutils.Matrix.Translation(
        (-(x0 + x1) / 2, -(y0 + y1) / 2, -z0 - immersion * (z1 - z0))))
    o.location = (0, 0, 0)
    o.name = o.data.name = "boat_" + nom
    for mt in o.data.materials:
        mt.name = "BOAT_" + nom
    o.data.update()
    gardes.append(o)
    print(f"BATEAU {nom} : {n0} -> {len(o.data.polygons)} faces, dims {tuple(round(d, 3) for d in o.dimensions)}")

for img in bpy.data.images:
    if img.size[0] > TEX:
        img.scale(TEX, TEX)
# tous à l'origine : le site garde la transformation de chaque nœud (compression meshopt) et place un parent
bpy.ops.object.select_all(action="DESELECT")
for o in gardes:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_apply=True)
print("EXPORT", OUT)
