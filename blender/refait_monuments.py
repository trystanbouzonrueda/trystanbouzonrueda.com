"""Monuments refaits main (remplacent les modèles Meshy) : Vélodrome, tour CMA CGM, David,
tour La Marseillaise (Jean Nouvel), église de Plan-de-Cuques.

En direct (MCP) : D = ".../blender/"; exec(open(D + "lib.py").read()); exec(open(D + "refait_monuments.py").read())
Relançable. Garde l'emplacement et l'emprise au sol de ce qui est déjà posé (modèle mdl_* ou mh_*).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import math

import bpy
from mathutils import Vector

D = BLENDER_DIR
_src = open(D + "build_monuments.py").read()
exec(_src.split("# ---------------------------------------------------------------- tout reconstruire")[0])

for n, c in (("bleu_om", "#5fb4e6"), ("blanc", "#f6f4ee"), ("calcaire", "#e8dcc2"), ("synth", "#3fa35a"),
             ("pierre_quai", "#cbbf9f"), ("verre", "#7fa6c9"), ("verre_fonce", "#4d6f93"), ("beton", "#c9c4b8"),
             ("herbe", "#8fc06a"), ("fer_noir", "#2b2d33"), ("bleu", "#2a5bd7"), ("rouge", "#d6232a"),
             ("blanc_casse", "#efe9dc"), ("tuile", "#c8643c"), ("facade_ocre", "#e3b77a"), ("cypres", "#2f5e3a")):
    mat(n, c)


def emprise(pid):
    """(x, y, z bas, taille au sol) de ce qui est posé pour ce lieu, puis on l'efface."""
    e = bpy.data.objects[f"place_{pid}"]
    olds = [c for c in e.children_recursive if c.type == "MESH"]
    pts = [c.matrix_world @ Vector(b) for c in olds for b in c.bound_box]
    if pts:
        foot = max(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts))
        z = min(p.z for p in pts)
    else:
        foot, z = None, ground(e.location.x, e.location.y)
    for c in olds:
        bpy.data.objects.remove(c, do_unlink=True)
    return e.location.x, e.location.y, z, foot


def ajuste(j, ox, oy, oz, foot):
    """Met le monument fusionné à l'emprise voulue (échelle uniforme autour de son pied)."""
    if not foot: return
    vs = j.data.vertices
    w = max(max(v.co.x for v in vs) - min(v.co.x for v in vs), max(v.co.y for v in vs) - min(v.co.y for v in vs))
    s = foot / w
    o = Vector((ox, oy, oz))
    for v in vs:
        v.co = o + (v.co - o) * s
    j.data.update()


def velodrome(k):
    a, b = 1.12, 0.88
    base = k.cyl(0, 0, 0, 1.0, 0.05, "pierre_quai", verts=32); base.scale = (a + 0.1, b + 0.1, 1)
    pitch = k.cyl(0, 0, 0.05, 1.0, 0.02, "synth", verts=28); pitch.scale = (0.6, 0.4, 1)
    for i in range(6):  # bandes de tonte
        k.box(-0.5 + i * 0.2, 0, 0.07, 0.1, 0.62, 0.002, "herbe")
    k.box(0, 0, 0.072, 0.008, 0.78, 0.004, "blanc")
    k.cyl(0, 0, 0.072, 0.08, 0.004, "blanc", verts=16)
    for s in (-1, 1):
        k.box(s * 0.58, 0, 0.07, 0.01, 0.1, 0.035, "blanc")
        k.box(s * 0.52, 0, 0.072, 0.12, 0.3, 0.003, "blanc")
    # gradins en escalier, bleu ciel et blanc
    k.ring(0.74, 0.54, 0.05, 0.06, 0.14, 36, "bleu_om")
    k.ring(0.86, 0.66, 0.05, 0.13, 0.12, 40, "blanc")
    k.ring(0.97, 0.76, 0.05, 0.21, 0.12, 44, "bleu_om")
    k.ring(1.08, 0.86, 0.05, 0.27, 0.07, 48, "calcaire")
    # le grand toit blanc ondulé (signature) : deux nappes, plus hautes sur les longueurs
    wave = lambda t: 0.07 * abs(math.sin(t)) + 0.03 * math.sin(4 * t)
    k.ring(0.98, 0.78, 0.34, 0.03, 0.34, 56, "blanc", hfn=wave)
    k.ring(1.12, 0.9, 0.31, 0.03, 0.12, 60, "blanc", hfn=wave)
    for i in range(16):
        t = 2 * math.pi * i / 16
        k.cyl(1.13 * math.cos(t), 0.91 * math.sin(t), 0.05, 0.012, 0.27 + wave(t), "blanc", verts=5)
    # parvis et lettrage
    k.box(0, -1.02, 0.0, 0.5, 0.12, 0.06, "calcaire")
    k.box(0, -0.98, 0.06, 0.32, 0.01, 0.04, "bleu_om")


def cma_cgm(k):
    k.box(0, 0, 0, 0.5, 0.42, 0.05, "beton")
    k.box(0.02, 0, 0.05, 0.6, 0.18, 0.12, "verre_fonce")          # socle bas, plus long
    # deux fuseaux de verre qui s'écartent, réunis par l'exosquelette blanc
    for s, h in ((-1, 1.5), (1, 1.32)):
        c = k.cyl(s * 0.07, 0, 0.05, 0.12, h, "verre", verts=14, r2=0.1); c.scale = (1, 0.82, 1)
        for i in range(int(h / 0.06)):                            # planchers visibles
            r = k.cyl(s * 0.07, 0, 0.05 + i * 0.06, 0.122 - 0.02 * i * 0.06 / h, 0.006, "verre_fonce", verts=14)
            r.scale = (1, 0.82, 1)
    for sy in (-1, 1):                                            # grandes lames blanches verticales
        k.box(0, sy * 0.11, 0.05, 0.03, 0.014, 1.55, "blanc")
        for i in range(9):                                        # entretoises en losange
            k.box(0, sy * 0.115, 0.15 + i * 0.16, 0.24, 0.01, 0.012, "blanc", rz=0.0)
    k.box(-0.19, 0, 0.05, 0.014, 0.2, 1.58, "blanc")
    k.box(-0.03, 0, 1.55, 0.26, 0.22, 0.025, "blanc")
    k.box(-0.08, 0, 1.575, 0.03, 0.03, 0.12, "blanc")             # mât


def david(k):
    k.cyl(0, 0, 0, 0.32, 0.03, "herbe", verts=20)
    k.cyl(0, 0, 0.03, 0.33, 0.012, "calcaire", verts=20)
    for i in range(8):                                            # massifs fleuris du rond-point
        t = 2 * math.pi * i / 8
        k.cyl(0.24 * math.cos(t), 0.24 * math.sin(t), 0.03, 0.035, 0.02, "rouge" if i % 2 else "cypres", verts=6)
    k.box(0, 0, 0.042, 0.13, 0.13, 0.04, "calcaire")
    k.box(0, 0, 0.082, 0.1, 0.1, 0.22, "blanc")
    k.box(0, 0, 0.302, 0.12, 0.12, 0.02, "blanc")
    z = 0.322  # statue : déhanché, bras gauche relevé vers l'épaule
    k.box(-0.017, 0, z, 0.022, 0.026, 0.15, "blanc")
    k.box(0.02, 0.008, z, 0.022, 0.026, 0.14, "blanc")
    k.box(0, 0, z + 0.14, 0.062, 0.036, 0.04, "blanc")
    k.box(0, 0, z + 0.18, 0.074, 0.042, 0.1, "blanc")
    k.box(0, 0, z + 0.28, 0.02, 0.02, 0.02, "blanc")
    k.ball(0, 0, z + 0.32, 0.026, "blanc")
    k.ball(0, 0.004, z + 0.338, 0.024, "blanc", squash=0.6)       # cheveux
    k.box(-0.05, 0, z + 0.13, 0.018, 0.02, 0.14, "blanc")
    k.box(0.043, 0, z + 0.2, 0.018, 0.02, 0.09, "blanc")
    k.box(0.04, -0.01, z + 0.27, 0.018, 0.022, 0.05, "blanc")


def tour_marseillaise(k):
    W, H = 0.22, 1.2
    k.box(0, 0, 0, W + 0.06, W + 0.06, 0.04, "beton")
    k.box(0, 0, 0.04, W - 0.02, W - 0.02, H, "verre_fonce")
    cols = ("rouge", "blanc", "bleu", "blanc_casse", "bleu", "rouge", "blanc", "bleu", "rouge", "blanc_casse", "blanc")
    n = 11
    for face in range(4):                                         # brise-soleil tricolores sur les 4 faces
        for i in range(n):
            u = -W / 2 + (i + 0.5) * W / n
            hh = H * (0.92 + 0.08 * ((i * 7 + face * 3) % 5) / 4)
            lx, ly = (u, -W / 2) if face == 0 else (W / 2, u) if face == 1 else (-u, W / 2) if face == 2 else (-W / 2, -u)
            sx, sy = (0.008, 0.012) if face in (0, 2) else (0.012, 0.008)
            k.box(lx, ly, 0.04, sx, sy, hh, cols[(i + face * 2) % len(cols)])
    k.box(0, 0, 0.04 + H, W + 0.01, W + 0.01, 0.02, "blanc")
    k.box(0, 0, 0.06 + H, W * 0.6, W * 0.6, 0.04, "fer_noir")


def eglise_plan_de_cuques(k):
    # nef provençale ocre, toit de tuiles, clocher carré à campanile en fer forgé
    k.box(0, 0, 0, 0.52, 0.86, 0.02, "calcaire")                  # parvis
    k.box(0, 0.06, 0.02, 0.3, 0.6, 0.2, "facade_ocre")
    k.gable(0, 0.06, 0.22, 0.6, 0.32, 0.1, "tuile").rotation_euler[2] += math.pi / 2
    k.box(0, -0.245, 0.02, 0.32, 0.02, 0.27, "calcaire")          # façade, fronton
    k.cyl(0, -0.257, 0.19, 0.035, 0.006, "fer_noir", verts=12).rotation_euler[0] = math.pi / 2
    k.box(0, -0.258, 0.02, 0.07, 0.006, 0.11, "fer_noir")         # porte
    for s in (-1, 1):
        k.box(s * 0.16, 0.06, 0.02, 0.02, 0.62, 0.17, "calcaire")  # contreforts
    k.box(0.21, 0.24, 0.02, 0.12, 0.12, 0.42, "facade_ocre")      # clocher
    k.box(0.21, 0.24, 0.44, 0.13, 0.13, 0.02, "calcaire")
    for dx, dy in ((-0.045, -0.045), (0.045, -0.045), (0.045, 0.045), (-0.045, 0.045)):
        k.box(0.21 + dx, 0.24 + dy, 0.46, 0.012, 0.012, 0.09, "fer_noir")
    k.cyl(0.21, 0.24, 0.55, 0.07, 0.07, "fer_noir", verts=4, r2=0.005)   # campanile
    k.ball(0.21, 0.24, 0.5, 0.025, "or_vif")                      # cloche
    for s in (-1, 1):
        k.cyl(s * 0.32, -0.3, 0.02, 0.025, 0.22, "cypres", verts=6, r2=0.004)


ROT = {"velodrome": math.radians(100), "cma_cgm": math.radians(-20), "david": math.radians(-45),
       "tour_marseillaise": math.radians(-20), "eglise_plan_de_cuques": 0.0}
for pid, fn in (("velodrome", velodrome), ("cma_cgm", cma_cgm), ("david", david),
                ("tour_marseillaise", tour_marseillaise), ("eglise_plan_de_cuques", eglise_plan_de_cuques)):
    x, y, z, foot = emprise(pid)
    k = Kit(pid, x, y, z=z, rot=ROT[pid])
    fn(k)
    ajuste(k.done(), x, y, z, foot)
print("monuments refaits main ok")
