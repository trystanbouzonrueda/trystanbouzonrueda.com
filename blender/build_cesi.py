"""Mini-île du CESI (campus d'Aix-en-Provence) : petite, sobre, flottant au nord de la ville, vers Aix.

En direct (MCP) : D = ".../blender/"; exec(open(D + "lib.py").read()); exec(open(D + "build_cesi.py").read())
Relançable (lot « CESI » + monument mh_cesi sous l'empty place_cesi).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import math
import random

import bmesh
import bpy
from mathutils import Vector

D = BLENDER_DIR
exec(open(D + "build_monuments.py").read().split("# ---------------------------------------------------------------- tout reconstruire")[0])

CX, CY = 2.0, 59.0          # au-delà du bord nord du plateau de mer (y = 53,6)
R = 1.5                     # rayon de l'île (petite et sobre)
ZT = 0.55                   # dessus de l'herbe
random.seed(13)

for n, c in (("herbe_cesi", "#8fc06a"), ("terre_ile", "#b48a5a"), ("roche_ile", "#9a8a72"), ("blanc", "#f6f4ee"),
             ("verre", "#7fa6c9"), ("verre_fonce", "#4d6f93"), ("jaune_cesi", "#f5c400"), ("fer_noir", "#2b2d33"),
             ("calcaire", "#e8dcc2"), ("asphalte", "#70747b"), ("beton", "#c9c4b8"), ("pin", "#4f9a46"),
             ("platane", "#6aa84f"), ("tronc", "#7a5a3a"), ("rouge", "#d6232a"), ("bleu", "#2a5bd7"),
             ("gris_cesi", "#3b3e44"), ("blanc_perfore", "#eceef0"), ("vitre_cesi", "#4f86cf"), ("sable", "#e3cf9e"),
             ("feuillage_automne", "#d9b43a"), ("bois", "#a07448")):
    mat(n, None if bpy.data.materials.get("M_" + n) else c)   # ne recolore pas la palette existante

# ---------- l'île : dessus d'herbe irrégulier, couche de terre, cône de roche qui flotte
for o in [o for o in bpy.data.objects if o.get("lot") == "CESI" or o.name.startswith("ile_cesi")]:
    bpy.data.objects.remove(o, do_unlink=True)


def ile():
    bm = bmesh.new()
    n = 18
    rs = [R * (0.88 + 0.14 * random.random()) for _ in range(n)]
    rings = [  # (facteur de rayon, z, matériau de la bande au-dessus)
        (1.0, ZT, 0), (1.0, ZT - 0.12, 1), (0.9, ZT - 0.4, 2), (0.66, ZT - 1.3, 2), (0.34, ZT - 2.6, 2), (0.07, ZT - 3.6, 2)]
    vs = []
    for f, z, _ in rings:
        vs.append([bm.verts.new((CX + rs[i] * f * math.cos(2 * math.pi * i / n),
                                 CY + rs[i] * f * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    top = bm.faces.new(vs[0]); top.material_index = 0
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            fc = bm.faces.new((vs[k][i], vs[k + 1][i], vs[k + 1][j], vs[k][j]))
            fc.material_index = 1 if k == 0 else 2
    bm.faces.new(list(reversed(vs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("ile_cesi"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("ile_cesi", me)
    bpy.data.collections["Monuments"].objects.link(o)
    for m in ("herbe_cesi", "terre_ile", "roche_ile"):
        me.materials.append(MATS[m])
    o["lot"] = "CESI"
    return o


ile()

# ---------- le campus, d'après la photo de Trystan : cube gris foncé sur 4 niveaux, bandeaux blancs en métal
# perforé à chaque étage (débords en quinconce), dalle de toit blanche en porte-à-faux, fenêtres bleues,
# logo « CESI » noir souligné de jaune sur le bandeau du 2ᵉ, rez-de-chaussée vitré derrière une grille.
k = Kit("cesi", CX, CY, z=ZT, rot=math.radians(-20))
C, H, N = 0.56, 0.1, 4                       # côté du cube, hauteur d'étage, niveaux
k.box(0, 0, 0, C, C, H * N, "gris_cesi")
k.box(0, 0, 0.004, C + 0.006, C + 0.006, 0.07, "vitre_cesi")   # rez-de-chaussée vitré
# fenêtres : mêmes faces des quatre côtés, rythme irrégulier comme sur la photo
FEN = [(-0.19, 0.07), (-0.06, 0.05), (0.06, 0.08), (0.2, 0.05)]
for et in range(1, N):
    z = et * H + 0.03
    for face in range(4):
        for j, (u, w) in enumerate(FEN):
            uu = u + (0.015 if (et + j) % 2 else -0.01)
            ox, oy = (uu, -C / 2 - 0.003) if face == 0 else (C / 2 + 0.003, uu) if face == 1 else (-uu, C / 2 + 0.003) if face == 2 else (-C / 2 - 0.003, -uu)
            sx, sy = (w, 0.006) if face in (0, 2) else (0.006, w)
            k.box(ox, oy, z, sx, sy, 0.045, "vitre_cesi")
# bandeaux perforés blancs : un par plancher, qui débordent un peu plus d'un côté à chaque niveau
for et, (dx, dy, deb) in enumerate(((0.02, 0.0, 0.07), (-0.03, 0.01, 0.09), (0.035, -0.01, 0.07)), start=1):
    k.box(dx, dy, et * H - 0.012, C + deb, C + deb, 0.034, "blanc_perfore")
k.box(-0.02, 0.01, H * N, C + 0.1, C + 0.08, 0.026, "blanc_perfore")   # dalle de toit en porte-à-faux
k.box(0, 0, H * N + 0.026, 0.14, 0.1, 0.03, "beton")                  # édicule technique
# logo sur le bandeau du 2ᵉ (face avant, -y) : C, E, S, I en traits noirs + soulignement jaune
y0 = 0.01 - (C + 0.09) / 2 - 0.0015   # face avant du bandeau du 2ᵉ (décalé de dy = 0,01)
zl, hl, t = 2 * H - 0.006, 0.02, 0.0035
def lettre(x, traits):
    for (a, b, w, h) in traits:
        k.box(x + a, y0, zl + b, w, 0.002, h, "fer_noir")
L = 0.014
lettre(-0.045, [(0, 0, t, hl), (L / 2, hl - t, L, t), (L / 2, 0, L, t)])                                    # C
lettre(-0.022, [(0, 0, t, hl), (L / 2, hl - t, L, t), (L / 2, hl / 2 - t / 2, L * 0.8, t), (L / 2, 0, L, t)])  # E
lettre(0.001, [(L / 2, hl - t, L, t), (0, hl / 2, t, hl / 2), (L / 2, hl / 2 - t / 2, L, t), (L, 0, t, hl / 2), (L / 2, 0, L, t)])  # S
lettre(0.026, [(0, 0, t, hl)])                                                                                # I
k.box(0.047, y0, zl, 0.014, 0.002, t * 1.2, "jaune_cesi")                                                     # _ jaune, détaché du I
# parvis, grille noire devant le rez-de-chaussée, lampadaire
k.box(0, -0.52, 0, 0.9, 0.4, 0.01, "calcaire")
k.box(0, -0.44, 0.04, 0.7, 0.005, 0.005, "fer_noir")                  # grille : main courante + barreaux
for i in range(15):
    k.box(-0.35 + i * 0.05, -0.44, 0.01, 0.004, 0.004, 0.03, "fer_noir")
k.cyl(-0.34, -0.5, 0.01, 0.005, 0.2, "fer_noir", verts=5)
k.box(-0.33, -0.5, 0.2, 0.03, 0.012, 0.008, "fer_noir")
# espace extérieur (tables et terrain de pétanque, comme sur le campus)
k.box(0.62, 0.15, 0, 0.32, 0.18, 0.008, "sable")
for (bx, by, c) in ((0.56, 0.12, "fer_noir"), (0.64, 0.18, "beton"), (0.7, 0.13, "rouge")):
    k.ball(bx, by, 0.014, 0.006, c)
for i in range(3):
    tx, ty = -0.62, -0.2 + i * 0.2
    k.box(tx, ty, 0.03, 0.12, 0.06, 0.008, "bois")
    k.box(tx, ty - 0.05, 0.015, 0.12, 0.02, 0.006, "bois")
    k.box(tx, ty + 0.05, 0.015, 0.12, 0.02, 0.006, "bois")
    k.box(tx, ty, 0, 0.01, 0.01, 0.03, "fer_noir")
# parking
k.box(0.5, -0.62, 0, 0.42, 0.36, 0.008, "asphalte")
for i in range(4):
    k.box(0.5, -0.76 + i * 0.1, 0.008, 0.3, 0.005, 0.002, "blanc")
for i, c in enumerate(("rouge", "blanc", "bleu")):
    k.box(0.44 + (i % 2) * 0.12, -0.71 + i * 0.1, 0.008, 0.09, 0.045, 0.03, c)
# arbres : le grand arbre doré de la photo à l'angle, platanes et pins autour
k.cyl(0.38, -0.36, 0, 0.018, 0.2, "tronc", verts=5)
k.ball(0.38, -0.36, 0.27, 0.12, "feuillage_automne", squash=0.85)
for (x, y) in ((-0.9, -0.6), (-0.95, 0.4), (-0.3, 0.8), (0.4, 0.75), (0.95, -0.2), (0.9, 0.55), (-0.6, -0.95)):
    k.cyl(x, y, 0, 0.018, 0.14, "tronc", verts=5)
    k.ball(x, y, 0.19, 0.1, "platane" if x < 0 else "pin", squash=0.8)
k.done()
print("île du CESI ok")
