"""Trystan en figurine (mascotte de la rubrique À propos), même DA en blocs que la ville.
D'après sa photo : grosse chevelure brune bouclée, moustache et barbe courte, veste noire à zip vert fluo,
t-shirt vert, écusson jaune-vert, jean, baskets blanches. Clips « idle » et « coucou » (salut de la main).

blender -b --python build_trystan.py  ->  models/trystan.blend + ../public/models/trystan.glb
Taille : 1 unité de haut (le site le met à l'échelle). Façade vers -y.
"""
import math
import random
from pathlib import Path

import bpy

HERE = Path(__file__).parent
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 24
random.seed(8)


def mat(name, hexcol, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    h = hexcol.lstrip("#"); c = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)] + [1]
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    m.diffuse_color = c
    return m


M = {k: mat("TR_" + k, v) for k, v in {
    "peau": "#e3ae88", "cheveux": "#2b1d14", "cheveux2": "#3d2a1d", "barbe": "#3a2819", "veste": "#1d1e22",
    "zip": "#59e33b", "tshirt": "#2e8b3a", "ecusson": "#c9d33b", "jean": "#34465f", "basket": "#f4f4f0",
    "semelle": "#d9d4c8", "yeux": "#1d2430", "bouche": "#b5524a"}.items()}


def bloc(name, size, offset, m, parent=None, pivot=(0, 0, 0)):
    """Boîte dont l'origine est au pivot (articulation) ; offset = centre de la boîte par rapport au pivot."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    for v in o.data.vertices:
        v.co.x += offset[0]; v.co.y += offset[1]; v.co.z += offset[2]
    o.location = pivot
    o.data.materials.append(M[m])
    if parent:
        o.parent = parent
    return o


root = bpy.data.objects.new("trystan", None); sc.collection.objects.link(root)
hanches = bloc("hanches", (0.34, 0.2, 0.12), (0, 0, 0), "jean", root, (0, 0, 0.46))
torse = bloc("torse", (0.4, 0.23, 0.42), (0, 0, 0.27), "veste", hanches)
bloc("tshirt", (0.12, 0.01, 0.16), (0, -0.117, 0.4), "tshirt", torse)          # col ouvert : t-shirt vert
bloc("zip", (0.018, 0.012, 0.3), (0, -0.119, 0.16), "zip", torse)
for sx in (-1, 1):
    bloc(f"col_{sx}", (0.03, 0.012, 0.17), (sx * 0.07, -0.119, 0.39), "zip", torse)  # bords du col verts
bloc("ecusson", (0.07, 0.012, 0.08), (-0.11, -0.12, 0.2), "ecusson", torse)

tete = bloc("tete", (0.25, 0.24, 0.27), (0, 0, 0.15), "peau", torse, (0, 0, 0.47))
for sx in (-1, 1):
    bloc(f"oeil_{sx}", (0.04, 0.01, 0.03), (sx * 0.055, -0.123, 0.18), "yeux", tete)
    bloc(f"sourcil_{sx}", (0.06, 0.012, 0.014), (sx * 0.055, -0.124, 0.215), "cheveux", tete)
bloc("nez", (0.04, 0.03, 0.05), (0, -0.13, 0.13), "peau", tete)
bloc("moustache", (0.12, 0.012, 0.022), (0, -0.124, 0.085), "barbe", tete)
bloc("bouche", (0.07, 0.01, 0.02), (0, -0.123, 0.06), "bouche", tete)
bloc("barbe", (0.2, 0.05, 0.05), (0, -0.105, 0.02), "barbe", tete)              # barbe courte sur la mâchoire
bloc("bouc", (0.06, 0.04, 0.05), (0, -0.115, -0.005), "barbe", tete)
# chevelure bouclée : un nuage de petits blocs autour du crâne (volume ≈ 1,6× la tête)
for i in range(120):
    th = random.uniform(0, 2 * math.pi)
    ph = random.uniform(-0.45, 1.4)                                           # du bas des oreilles au sommet
    rx, ry, rz = 0.24, 0.23, 0.2
    x, y, z = rx * math.cos(ph) * math.cos(th), ry * math.cos(ph) * math.sin(th), 0.2 + rz * math.sin(ph)
    if y < -0.06 and z < 0.29:                                                 # dégager le visage
        continue
    s = random.uniform(0.07, 0.12)
    bloc(f"boucle_{i}", (s, s, s), (x, y, z), "cheveux" if i % 3 else "cheveux2", tete)
bloc("crane", (0.3, 0.3, 0.12), (0, 0.01, 0.31), "cheveux", tete)

bras, jambes, avbras = {}, {}, {}
for sx, cote in ((-1, "d"), (1, "g")):   # façade vers -y : son côté droit est en -x
    b = bloc(f"bras_{cote}", (0.11, 0.12, 0.2), (0, 0, -0.09), "veste", torse, (sx * 0.26, 0, 0.4))
    ab = bloc(f"avbras_{cote}", (0.1, 0.11, 0.18), (0, 0, -0.08), "veste", b, (0, 0, -0.18))
    bloc(f"poignet_{cote}", (0.105, 0.115, 0.02), (0, 0, -0.17), "zip", ab)
    bloc(f"main_{cote}", (0.09, 0.09, 0.09), (0, 0, -0.22), "peau", ab)
    bras[cote], avbras[cote] = b, ab
    j = bloc(f"jambe_{cote}", (0.15, 0.17, 0.42), (0, 0, -0.21), "jean", hanches, (sx * 0.095, 0, -0.04))
    bloc(f"basket_{cote}", (0.16, 0.24, 0.07), (0, -0.03, -0.43), "basket", j)
    bloc(f"semelle_{cote}", (0.165, 0.245, 0.02), (0, -0.03, -0.47), "semelle", j)
    jambes[cote] = j


# ------------------------------------------------------------------ animations
def piste(obj, nom, n, clefs):
    """clefs(u) -> (rot_x, rot_y, rot_z, dz) pour u de 0 à 1 ; une piste NLA par clip."""
    obj.animation_data_create()
    act = bpy.data.actions.new(f"{nom}_{obj.name}")
    obj.animation_data.action = act
    base = obj.location.copy()
    for f in range(0, n + 1, 2):
        rx, ry, rz, dz = clefs(f / n)
        obj.rotation_euler = (rx, ry, rz)
        obj.location = (base.x, base.y, base.z + dz)
        obj.keyframe_insert("rotation_euler", frame=f)
        obj.keyframe_insert("location", frame=f)
    obj.rotation_euler = (0, 0, 0); obj.location = base
    tr = obj.animation_data.nla_tracks.new(); tr.name = nom
    tr.strips.new(nom, 1, act)
    obj.animation_data.action = None


T = 2 * math.pi
S = lambda u: math.sin(T * u)
# idle (2 s) : respiration, tête qui dodeline, bras détendus
n = 48
piste(hanches, "idle", n, lambda u: (0, 0, 0, 0.006 * S(u)))
piste(torse, "idle", n, lambda u: (0.02 * S(u), 0, 0.03 * S(u / 2), 0))
piste(tete, "idle", n, lambda u: (0.04 * S(u), 0, 0.12 * S(u / 2), 0))
for cote, s in (("g", -1), ("d", 1)):
    piste(bras[cote], "idle", n, lambda u, s=s: (0.05 * S(u), s * 0.08, 0, 0))
    piste(avbras[cote], "idle", n, lambda u: (0.15, 0, 0, 0))
    piste(jambes[cote], "idle", n, lambda u: (0, 0, 0, 0))
# coucou (1,5 s) : bras droit levé, l'avant-bras balance, petit sautillement, tête penchée
n = 36
piste(hanches, "coucou", n, lambda u: (0, 0, 0, 0.02 * abs(S(u))))
piste(torse, "coucou", n, lambda u: (0, 0.06, 0.05 * S(u), 0))
piste(tete, "coucou", n, lambda u: (0, -0.18, 0.05 * S(u), 0))
piste(bras["d"], "coucou", n, lambda u: (0, 2.6, 0, 0))                  # bras droit levé sur le côté
piste(avbras["d"], "coucou", n, lambda u: (0, -0.5 * S(2 * u), 0, 0))      # la main fait coucou
piste(bras["g"], "coucou", n, lambda u: (0.05, -0.1, 0, 0))
piste(avbras["g"], "coucou", n, lambda u: (0.2, 0, 0, 0))
for cote in ("g", "d"):
    piste(jambes[cote], "coucou", n, lambda u: (0, 0, 0, 0))

(HERE / "models").mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "models" / "trystan.blend"))
bpy.ops.object.select_all(action="SELECT")
out = HERE.parent / "public" / "models" / "trystan.glb"
bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True, export_yup=True,
                          export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True,
                          export_cameras=False, export_lights=False)
print("TRYSTAN", out, out.stat().st_size // 1024, "Ko")
