"""Lot A, fait main : Vieux-Port, Corniche, city stade de Jul, parc Borély.

exec(open(".../lib.py").read()); exec(open(".../build_lot_a.py").read())
Relançable : supprime d'abord tout ce qui porte lot="A".
"""
import bpy, math, random
random.seed(21)
clear_lot("A")
for n in ["place_vieux_port", "place_corniche", "place_city_jul", "place_borely"]:
    remove(n)
WL = -0.08
QZ = 0.34  # hauteur des quais

# ---------------- Vieux-Port
vp = empty("place_vieux_port", (-2.5, 4.75, QZ))
quai = [(-4.3, 6.25), (-2.5, 6.25), (-0.75, 6.25), (-0.75, 4.75), (-0.75, 3.25), (-2.5, 3.25), (-4.3, 3.25)]
ribbon("vp_quai", [(x, y, QZ) for x, y in quai], 0.5, "pierre_quai", vp, "Monuments", thick=0.7)
# ombrière (miroir sur pilotis) côté quai des Belges
for dx in (-0.2, 0.2):
    for dy in (-0.2, 0.2):
        cyl("vp_pilier", (-0.75 + dx, 4.75 + dy, QZ + 0.11), 0.008, 0.22, "blanc", vp, verts=6)
box("vp_ombriere", (-0.75, 4.75, QZ + 0.23), (0.55, 0.6, 0.012), "miroir", vp)
# pontons + pointus
couleurs = ["rouge", "bleu", "jaune", "blanc", "bleu_om"]
for y0, sens in ((6.0, -1), (3.5, 1)):
    for k, x in enumerate([-3.8, -3.2, -2.6, -2.0, -1.4]):
        box("vp_ponton", (x, y0 + sens * 0.32, WL + 0.03), (0.04, 0.64, 0.02), "bois", vp)
        for side in (-0.09, 0.09):
            if random.random() < 0.8:
                yb = y0 + sens * random.uniform(0.15, 0.55)
                b = box("vp_pointu", (x + side, yb, WL + 0.03), (0.06, 0.15, 0.04), random.choice(couleurs), vp)
                box("vp_pointu_pont", (x + side, yb, WL + 0.055), (0.045, 0.1, 0.01), "bois", vp)
# immeubles des quais (façades crème, toits tuiles)
for y, sens in ((6.75, 1), (2.75, -1)):
    x = -4.0
    while x < -0.9:
        w = random.uniform(0.25, 0.4); h = random.uniform(0.25, 0.45)
        z0 = ground(x, y)
        box("vp_immeuble", (x + w / 2, y, z0 + h / 2), (w - 0.02, 0.45, h + 0.1), random.choice(["creme", "calcaire", "sable"]), vp)
        box("vp_toit", (x + w / 2, y, z0 + h + 0.07), (w - 0.01, 0.47, 0.04), "tuile", vp)
        x += w

# ---------------- Corniche Kennedy
cn = empty("place_corniche", (-4.0, -1.5, 0.35))
def coast(y): return -5.2 + 1.0 * math.sin(y * 0.45) + (0.0 if y > -6 else (y + 6) * 0.35)
pts, rail = [], []
y = 2.9
while y > -6.3:
    x = coast(y) + 0.42
    z = max(ground(x, y), 0.30) + 0.03
    pts.append((x, y, z)); rail.append((x - 0.2, y, z + 0.05))
    y -= 0.2
ribbon("cn_route", pts, 0.32, "route", cn, "Monuments", thick=0.5)
ribbon("cn_balustrade", rail, 0.03, "blanc", cn, "Monuments", thick=0.07)
# ligne centrale
ribbon("cn_ligne", [(x, y, z + 0.002) for x, y, z in pts], 0.012, "blanc", cn, "Monuments", thick=0.004)
# pont de la Fausse-Monnaie (arche de pierre côté mer)
yb = -3.4; xb = coast(yb) + 0.25
box("cn_pont", (xb, yb, 0.18), (0.5, 0.5, 0.3), "pierre_quai", cn)
cyl("cn_arche", (xb, yb, 0.0), 0.16, 0.52, "mer_fond", cn, verts=12, rot=(0, math.pi / 2, 0))
# lampadaires
for i in range(0, len(pts), 4):
    x, y, z = pts[i]
    cyl("cn_lampe", (x - 0.17, y, z + 0.1), 0.006, 0.2, "route", cn, verts=5)
    blob("cn_lampe_tete", (x - 0.17, y, z + 0.2), 0.018, "jaune", cn, "Monuments")

# ---------------- City stade de Jul (stade Julien Baudon)
cx, cy = 0.9, 1.0
gz = max(ground(cx + dx, cy + dy) for dx in (-0.5, 0.5) for dy in (-0.32, 0.32))
cj = empty("place_city_jul", (cx, cy, gz))
box("cj_dalle", (cx, cy, gz - 0.15), (1.1, 0.7, 0.32), "calcaire", cj)
box("cj_terrain", (cx, cy, gz + 0.012), (0.9, 0.5, 0.02), "synth", cj)
box("cj_ligne_milieu", (cx, cy, gz + 0.024), (0.01, 0.5, 0.004), "blanc", cj)
cyl("cj_rond", (cx, cy, gz + 0.023), 0.07, 0.004, "blanc", cj, verts=16)
for s in (-1, 1):
    gx = cx + s * 0.43
    for dy in (-0.07, 0.07):
        cyl("cj_poteau_but", (gx, cy + dy, gz + 0.05), 0.006, 0.08, "blanc", cj, verts=5)
    box("cj_barre", (gx, cy, gz + 0.09), (0.012, 0.15, 0.012), "blanc", cj)
# grillage : poteaux + lisses
for k in range(11):
    for sy in (-0.27, 0.27):
        cyl("cj_poteau", (cx - 0.47 + k * 0.094, cy + sy, gz + 0.09), 0.005, 0.18, "grillage", cj, verts=4)
for sy in (-0.27, 0.27):
    for hz in (0.06, 0.18):
        box("cj_lisse", (cx, cy + sy, gz + hz), (0.95, 0.008, 0.008), "grillage", cj)
for sx in (-0.475, 0.475):
    for hz in (0.06, 0.18):
        box("cj_lisse", (cx + sx, cy, gz + hz), (0.008, 0.55, 0.008), "grillage", cj)
# mur tagué « JUL »
box("cj_mur", (cx, cy + 0.36, gz + 0.08), (0.6, 0.04, 0.16), "calcaire", cj)
bpy.ops.object.text_add(location=(cx - 0.17, cy + 0.335, gz + 0.03), rotation=(math.pi / 2, 0, 0))
t = bpy.context.active_object; t.data.body = "JUL ✌"; t.data.size = 0.13; t.data.extrude = 0.006
bpy.ops.object.convert(target='MESH'); t.name = "cj_tag"
_finish(t, "jaune", cj, "Monuments", "A")

# ---------------- Parc Borély
bx, by = -2.4, -6.0
gz = ground(bx, by)
pb = empty("place_borely", (bx, by, gz))
box("pb_pelouse", (bx, by, gz - 0.1), (2.0, 1.3, 0.24), "herbe", pb)
ribbon("pb_allee1", [(bx - 1.0, by, gz + 0.025), (bx + 1.0, by, gz + 0.025)], 0.08, "sable", pb, "Monuments", thick=0.02)
ribbon("pb_allee2", [(bx + 0.2, by - 0.65, gz + 0.025), (bx + 0.2, by + 0.65, gz + 0.025)], 0.08, "sable", pb, "Monuments", thick=0.02)
cyl("pb_lac", (bx + 0.55, by - 0.3, gz + 0.02), 0.28, 0.02, "mer", pb, verts=14)
blob("pb_ile", (bx + 0.6, by - 0.32, gz + 0.03), 0.05, "herbe_fonce", pb, "Monuments", squash=0.5)
# château Borély (provisoire, en attendant Meshy)
box("pb_chateau", (bx - 0.55, by + 0.35, gz + 0.12), (0.55, 0.22, 0.24), "creme", pb)
box("pb_chateau_toit", (bx - 0.55, by + 0.35, gz + 0.26), (0.57, 0.24, 0.05), "route", pb)
for i in range(16):
    a = random.uniform(0, 2 * math.pi)
    tx = bx + math.cos(a) * random.uniform(0.75, 0.95); ty = by + math.sin(a) * random.uniform(0.5, 0.6)
    tree(f"pb_arbre{i}", tx, ty, random.uniform(0.7, 1.0), pb, z=gz + 0.02)
print("lot A ok")
