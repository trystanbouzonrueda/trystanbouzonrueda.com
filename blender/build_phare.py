"""Phare Meshy (aperçu sans texture) → phare léger aux couleurs de l'île.

blender -b --python blender/build_phare.py
Source : blender/model-try/meshy-1119/phare.glb (hors git). Sortie : blender/export/phare_raw.glb
(puis scripts/optimize.mjs → public/models/phare.glb, posé par src/vie.ts au phare Sainte-Marie).
Couleurs par hauteur, en aplats : rochers calcaires, tour blanche, lanterne sombre, coupole rouge.
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import bpy
import mathutils

SRC = BLENDER_DIR + "model-try/meshy-1119/phare.glb"
OUT = BLENDER_DIR + "export/phare_raw.glb"
FACES = 2500
HAUTEUR = 0.75  # unités de l'île (échelle « monument » ×1,6 comme le reste, lisible de loin)
# (hauteur relative max, nom, couleur)
BANDES = [
    (0.30, "rocher", (0.80, 0.76, 0.66)),
    (0.74, "tour", (0.96, 0.95, 0.92)),
    (0.81, "lanterne", (0.20, 0.24, 0.30)),
    (1.01, "coupole", (0.78, 0.16, 0.13)),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
objs = [o for o in bpy.data.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
if len(objs) > 1:
    bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for x in [x for x in bpy.data.objects if x != o]:
    bpy.data.objects.remove(x, do_unlink=True)
n0 = len(o.data.polygons)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=0.001)
bpy.ops.object.mode_set(mode="OBJECT")
m = o.modifiers.new("dec", "DECIMATE")
m.ratio = min(1.0, FACES / len(o.data.polygons))
m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier="dec")

# échelle et origine au centre du socle
vs = [v.co for v in o.data.vertices]
x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
k = HAUTEUR / (z1 - z0)
o.data.transform(mathutils.Matrix.Scale(k, 4) @ mathutils.Matrix.Translation((-(x0 + x1) / 2, -(y0 + y1) / 2, -z0)))

# matériaux en aplats selon la hauteur de chaque face
o.data.materials.clear()
for _, nom, col in BANDES:
    mt = bpy.data.materials.new("M_phare_" + nom)
    mt.use_nodes = True
    bsdf = next(n for n in mt.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*col, 1)
    bsdf.inputs["Roughness"].default_value = 0.85
    o.data.materials.append(mt)
for f in o.data.polygons:
    h = f.center.z / HAUTEUR
    f.material_index = next(i for i, (lim, _, _) in enumerate(BANDES) if h <= lim)
o.data.update()
o.name = o.data.name = "phare"
bpy.ops.object.select_all(action="DESELECT")
o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_apply=True)
print(f"PHARE : {n0} -> {len(o.data.polygons)} faces")
