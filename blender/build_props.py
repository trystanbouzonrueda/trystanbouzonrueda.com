"""Objets Meshy du 19/11 (Plan-de-Cuques, CESI, calanques, ciel) → un GLB « props » pour le site.

blender -b --python blender/build_props.py
Sources : blender/model-try/meshy-1119/<nom>.glb (hors git). Sortie : blender/export/props_raw.glb
(puis scripts/optimize.mjs → public/models/props.glb ; src/props.ts les pose, src/aerien.ts fait voler le Canadair).
Chaque objet « prop_<nom> » : soudé, allégé, texture 512, origine au centre du socle (au centre tout court pour un avion),
mis à la taille voulue ; un avion a le nez tourné vers +X (la queue = le bout le plus haut, à cause de la dérive).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import math
import os

import bpy
import mathutils

SRC = BLENDER_DIR + "model-try/meshy-1119/"
OUT = BLENDER_DIR + "export/props_raw.glb"
# nom : (mesure, valeur en unités de l'île, faces max, avion ?)   mesure = « emprise » (plus grand côté au sol) ou « longueur »
PROPS = {
    "mairie_pdc": ("emprise", 0.5, 5000, False),
    # "bastide" retirée : l'allègement de l'ancien modèle (3,4 M faces) abîme sa texture
    "cabanon": ("emprise", 0.12, 1500, False),
    "terrasse_cesi": ("emprise", 0.42, 5000, False),
    "canadair": ("longueur", 0.5, 4000, True),
}
TEX = 512

bpy.ops.wm.read_factory_settings(use_empty=True)
gardes = []
for i, (nom, (mesure, val, faces, avion)) in enumerate(PROPS.items()):
    f = SRC + nom + ".glb"
    if not os.path.exists(f):
        print("ABSENT", nom)
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
    if len(o.data.polygons) > faces * 3:
        # très lourds (anciens modèles, millions de faces) : d'abord fusion des faces coplanaires sans traverser
        # les coutures UV (garde la texture propre), la réduction classique ensuite
        m = o.modifiers.new("plan", "DECIMATE")
        m.decimate_type = "DISSOLVE"
        m.angle_limit = 0.06
        m.delimit = {"UV", "SEAM", "MATERIAL"}
        bpy.ops.object.modifier_apply(modifier="plan")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.mode_set(mode="OBJECT")
    if len(o.data.polygons) > faces:
        m = o.modifiers.new("dec", "DECIMATE")
        m.ratio = faces / len(o.data.polygons)
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier="dec")

    if avion:
        vs = [v.co.copy() for v in o.data.vertices]
        ex = max(v.x for v in vs) - min(v.x for v in vs)
        ey = max(v.y for v in vs) - min(v.y for v in vs)
        # envergure ≥ longueur sur un hydravion : l'axe du fuselage est celui où se trouve la dérive (point le plus haut)
        top = max(vs, key=lambda v: v.z)
        c = mathutils.Vector(((max(v.x for v in vs) + min(v.x for v in vs)) / 2, (max(v.y for v in vs) + min(v.y for v in vs)) / 2, 0))
        dx, dy = abs(top.x - c.x) / ex, abs(top.y - c.y) / ey
        if dy > dx:
            o.data.transform(mathutils.Matrix.Rotation(math.pi / 2, 4, "Z"))
        vs = [v.co.copy() for v in o.data.vertices]
        top = max(vs, key=lambda v: v.z)
        cx = (max(v.x for v in vs) + min(v.x for v in vs)) / 2
        if top.x > cx:  # la dérive est à l'arrière : le nez doit pointer vers +X
            o.data.transform(mathutils.Matrix.Rotation(math.pi, 4, "Z"))

    vs = [v.co.copy() for v in o.data.vertices]
    x0, x1 = min(v.x for v in vs), max(v.x for v in vs)
    y0, y1 = min(v.y for v in vs), max(v.y for v in vs)
    z0, z1 = min(v.z for v in vs), max(v.z for v in vs)
    taille = (x1 - x0) if mesure == "longueur" else max(x1 - x0, y1 - y0)
    k = val / taille
    zc = (z0 + z1) / 2 if avion else z0
    o.data.transform(mathutils.Matrix.Scale(k, 4) @ mathutils.Matrix.Translation((-(x0 + x1) / 2, -(y0 + y1) / 2, -zc)))
    o.name = o.data.name = "prop_" + nom
    for mt in o.data.materials:
        mt.name = "PROP_" + nom
    o.location = (0, 0, 0)  # à l'origine : le site garde la transformation du nœud (compression) et place un parent
    o.data.update()
    gardes.append(o)
    print(f"PROP {nom} : {n0} -> {len(o.data.polygons)} faces")

for img in bpy.data.images:
    if img.size[0] > TEX:
        img.scale(TEX, TEX)

# Canadair : Meshy a peint une croix suisse sur la dérive (deux zones de la texture) → repeinte en rouge
import numpy as np
for o in gardes:
    if o.name != "prop_canadair":
        continue
    imgs = {n.image for mt in o.data.materials if mt and mt.use_nodes for n in mt.node_tree.nodes if n.type == "TEX_IMAGE" and n.image}
    for img in imgs:
        w, h = img.size
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        rgb = px[..., :3]
        red = (rgb[..., 0] > 0.5) & (rgb[..., 1] < 0.35) & (rgb[..., 2] < 0.35)
        white = rgb.min(axis=2) > 0.68
        # les deux croix de la dérive, repérées à l'œil dans la texture (coordonnées 0–1, origine en haut à gauche)
        CROIX = [(0.046, 0.040, 0.100, 0.084), (0.383, 0.269, 0.427, 0.309)]
        cible = np.zeros((h, w), bool)
        for x0, y0, x1, y1 in CROIX:
            r0, r1 = int((1 - y1) * h), int((1 - y0) * h)  # Blender range les lignes de bas en haut
            c0, c1 = int(x0 * w), int(x1 * w)
            cible[r0:r1, c0:c1] = white[r0:r1, c0:c1]
        if cible.any():
            couleur = rgb[red].mean(axis=0)
            rgb[cible] = couleur
            px[..., :3] = rgb
            img.pixels[:] = px.ravel()
            img.pack()
        print(f"CANADAIR croix repeinte : {int(cible.sum())} pixels")
bpy.ops.object.select_all(action="DESELECT")
for o in gardes:
    o.select_set(True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_yup=True, export_apply=True)
print("EXPORT", OUT, len(gardes), "objets")
