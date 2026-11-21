"""Prépare les modèles détaillés de model-try/ pour la maquette : renommage, simplification,
textures réduites, un .blend léger par modèle dans models/.

blender -b --python process_models.py
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import os

import bpy

SRC = BLENDER_DIR + "model-try/"
DST = BLENDER_DIR + "models/"
# fichier source (début du nom) -> (nom du modèle, faces visées)
MODELES = {
    "Meshy_AI_Marble_Muse": ("david", 9000),
    "Meshy_AI_Stylized_low_poly_3D_model_of_cma_cgm": ("cma_cgm", 14000),
    "Meshy_AI_Stylized_low_poly_3D_model_of_plan_de": ("eglise_plan_de_cuques", 18000),
    "Meshy_AI_Stylized_low_poly_3D_model_of_stade": ("velodrome", 22000),
    "Meshy_AI_Stylized_low_poly_3D_model_of_tour_la": ("tour_marseillaise", 12000),
}
TEX = 1024
os.makedirs(DST, exist_ok=True)

for f in sorted(os.listdir(SRC)):
    if not f.endswith(".blend"): continue
    key = next((k for k in MODELES if f.startswith(k)), None)
    if key is None: continue
    nom, cible = MODELES[key]
    bpy.ops.wm.open_mainfile(filepath=SRC + f)
    o = next(o for o in bpy.data.objects if o.type == "MESH")
    for x in [x for x in bpy.data.objects if x != o]:
        bpy.data.objects.remove(x, do_unlink=True)
    o.name = o.data.name = "mdl_" + nom
    n0 = len(o.data.polygons)
    # soudure des sommets dupliqués (Meshy sort des triangles disjoints) puis simplification
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")
    m = o.modifiers.new("dec", "DECIMATE"); m.ratio = min(1.0, cible / len(o.data.polygons)); m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="dec")
    # textures : couleur de base 1K, on garde aussi rugosité/normale réduites
    for img in bpy.data.images:
        if img.size[0] > TEX:
            img.scale(TEX, TEX)
        img.pack()
    mt = o.data.materials[0]; mt.name = "MDL_" + nom
    # origine au centre du socle (bas du modèle)
    bpy.context.scene.cursor.location = (0, 0, 0)
    xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]; zs = [v.co.z for v in o.data.vertices]
    import mathutils
    off = mathutils.Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    o.data.transform(mathutils.Matrix.Translation(-off)); o.location = (0, 0, 0)
    o.data.update()
    for b in [b for b in bpy.data.meshes if b.users == 0]: bpy.data.meshes.remove(b)
    bpy.ops.wm.save_as_mainfile(filepath=DST + nom + ".blend", compress=True)
    print(f"MODELE {nom} : {n0} -> {len(o.data.polygons)} faces, dims {tuple(round(d, 2) for d in o.dimensions)}")
