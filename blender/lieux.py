"""Bâtiments légers (quartiers étendus) et monuments génériques pour les arrondissements 3 à 16.

À charger après lib.py, batiments.py, fastkit.py, quartier.py.
Bâtiments légers = peu de faces (une ville entière doit tenir dans le navigateur).
Monuments génériques = gabarits paramétrés (palais, église, centre commercial…) posés sur un lieu réel ;
les gros monuments détaillés viendront de blender/model-try/ et les remplaceront.
"""
import math

mat("blanc_casse", "#f4f1ea"); mat("verre_bureau", "#8fc3dc", rough=0.2); mat("brique", "#c96f4a")
mat("parking", "#b9b4aa"); mat("sable_plage", "#f3e3b5"); mat("parasol_1", "#e9523f"); mat("parasol_2", "#f2c14e")


# ------------------------------------------------------------------ bâtiments légers
def maison(k, x, y, r=0.0, w=0.11, d=0.1, etages=1, facade="creme", toit="tuile"):
    """Pavillon / maison de village : volume + toit à deux pans + porte (≈17 faces)."""
    b = FB(k, x, y, r)
    hh = 0.07 * etages
    b.box(0, 0, -0.1, w, d, hh + 0.1, facade)
    b.gable(0, 0, hh, w + 0.012, d + 0.012, 0.045, toit)
    b.box(0, -d / 2 - 0.003, 0, w * 0.2, 0.006, 0.05, "bois")


def villa(k, x, y, r=0.0, w=0.13, d=0.11, facade="facade_ocre", toit="tuile"):
    """Villa / bastide basse avec toit à 4 pans et un arbre au jardin."""
    b = FB(k, x, y, r)
    b.box(0, 0, -0.1, w, d, 0.17, facade)
    b.hip(0, 0, 0.07, w + 0.014, d + 0.014, 0.045, toit)
    b.box(0, -d / 2 - 0.003, 0, w * 0.2, 0.006, 0.05, "volet_vert")
    b.ball(w / 2 + 0.05, d / 2, 0.06, 0.045, "feuillage", squash=1.1)


def immeuble(k, x, y, r=0.0, w=0.16, d=0.14, etages=4, facade="creme", toit="toit_plat"):
    """Petit immeuble simple : bandes de fenêtres (≈30 faces)."""
    b = FB(k, x, y, r)
    fh = 0.07; hh = etages * fh
    b.box(0, 0, -0.1, w, d, hh + 0.1, facade)
    for f in range(etages):
        b.box(0, -d / 2 - 0.002, f * fh + 0.022, w * 0.85, 0.004, fh * 0.4, "fenetre_sombre")
    b.box(0, 0, hh, w + 0.008, d + 0.008, 0.012, toit if toit in MATS else "beton_sombre")


def entrepot(k, x, y, r=0.0, w=0.3, d=0.2, facade="beton", toit="zinc"):
    """Hangar, zone d'activités."""
    b = FB(k, x, y, r)
    b.box(0, 0, -0.1, w, d, 0.2, facade)
    b.gable(0, 0, 0.1, w + 0.01, d + 0.01, 0.035, toit)
    b.box(0, -d / 2 - 0.003, 0, w * 0.35, 0.006, 0.08, "beton_sombre")


# ------------------------------------------------------------------ monuments génériques
def palais(k, x, y, r=0.0, w=0.6, d=0.35, h=0.32, colonnes=6, facade="creme", toit="zinc", dome=False):
    b = FB(k, x, y, r)
    b.box(0, 0, -0.1, w, d, h + 0.1, facade)
    b.box(0, -d / 2 - 0.04, -0.1, w * 0.6, 0.08, 0.1, "calcaire")
    for i in range(colonnes):
        b.cyl(-w * 0.27 + i * w * 0.54 / max(1, colonnes - 1), -d / 2 - 0.035, 0, 0.015, h * 0.75, "calcaire", verts=8)
    b.box(0, -d / 2 - 0.035, h * 0.75, w * 0.62, 0.08, 0.045, "calcaire")
    b.box(0, 0, h, w * 0.85, d * 0.8, 0.05, toit)
    _windows(b, w, d, 2, h * 0.4, 0.02, max(5, int(w / 0.07)))
    if dome:
        b.cyl(0, 0, h + 0.05, 0.08, 0.08, toit, verts=12, r2=0.02)
    return b


def eglise_ville(k, x, y, r=0.0, facade="calcaire", toit="ardoise", fleche=0.3):
    """Église de quartier : nef + clocher à flèche."""
    b = FB(k, x, y, r)
    b.box(0, 0.06, -0.1, 0.2, 0.42, 0.3, facade)
    b.gable(0, 0.06, 0.2, 0.22, 0.44, 0.08, toit)
    b.box(0, -0.17, -0.1, 0.1, 0.1, 0.48, facade)
    b.cyl(0, -0.17, 0.38, 0.06, fleche, toit, verts=8, r2=0.004)
    b.box(0, -0.222, 0, 0.04, 0.004, 0.09, "bois")
    return b


def centre_commercial(k, x, y, r=0.0, w=1.0, d=0.6, nom_couleur="rouge"):
    b = FB(k, x, y, r)
    b.box(0, 0.1, -0.1, w, d, 0.24, "blanc_casse")
    b.box(0, -d / 2 + 0.1 - 0.003, 0.08, w * 0.4, 0.006, 0.05, nom_couleur)          # enseigne
    b.box(0, -d / 2 + 0.1 - 0.004, 0, w * 0.6, 0.006, 0.06, "verre_bureau")
    b.box(0, -d / 2 - 0.25, -0.005, w * 1.1, 0.45, 0.012, "parking")                   # parking
    for i in range(6):
        b.box(-w * 0.45 + i * w * 0.18, -d / 2 - 0.25, 0.007, 0.004, 0.36, 0.002, "blanc")
    return b


def hopital(k, x, y, r=0.0, etages=10):
    b = FB(k, x, y, r)
    b.box(0, 0, -0.1, 0.7, 0.35, 0.25, "blanc_casse")
    tour(k, x + math.cos(r) * 0.0, y + math.sin(r) * 0.0, r, etages=etages, w=0.24, facade="blanc_casse", accent="bleu")
    b.box(0.25, -0.18, 0.15, 0.08, 0.004, 0.08, "rouge")                                 # croix
    b.box(0.25, -0.18, 0.15, 0.025, 0.005, 0.08, "blanc")
    return b


def campus(k, x, y, r=0.0, n=4):
    for i in range(n):
        a = r + i * 0.4
        bureau_simple(k, x + math.cos(a) * 0.35 * (i % 2 + 1), y + math.sin(a) * 0.35 * (i % 2 + 1), a, etages=3 + i % 3)


def bureau_simple(k, x, y, r=0.0, etages=4, w=0.24, d=0.18):
    b = FB(k, x, y, r)
    fh = 0.07
    b.box(0, 0, -0.1, w, d, etages * fh + 0.1, "blanc_casse")
    for f in range(etages):
        b.box(0, 0, f * fh + 0.015, w + 0.006, d + 0.006, fh * 0.55, "verre_bureau")


def place_marche(k, x, y, r=0.0, n=8, rayon=0.25):
    """Place avec platanes et étals (La Plaine, places de village)."""
    stores = ("store_rouge", "store_vert", "store_bleu", "jaune")
    for i in range(n):
        a = r + 2 * math.pi * i / n
        platane(k, x + math.cos(a) * rayon, y + math.sin(a) * rayon, s=0.8)
        etal(k, x + math.cos(a) * rayon * 0.55, y + math.sin(a) * rayon * 0.55, a + math.pi / 2, store=stores[i % 4])
    kiosque(k, x, y)


def fontaine(k, x, y, h=0.35):
    b = FB(k, x, y, 0)
    b.cyl(0, 0, -0.02, 0.16, 0.04, "calcaire", verts=16)
    b.cyl(0, 0, 0.0, 0.14, 0.025, "mer", verts=16)
    b.cyl(0, 0, 0.02, 0.035, h, "calcaire", verts=8)
    b.ball(0, 0, h + 0.04, 0.035, "calcaire")


def fort(k, x, y, r=0.0, w=0.5, d=0.4):
    b = FB(k, x, y, r)
    b.box(0, 0, -0.15, w, d, 0.3, "calcaire")
    for i in range(int(w / 0.06)):
        b.box(-w / 2 + 0.03 + i * 0.06, -d / 2, 0.15, 0.03, 0.03, 0.035, "calcaire")
        b.box(-w / 2 + 0.03 + i * 0.06, d / 2, 0.15, 0.03, 0.03, 0.035, "calcaire")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.cyl(sx * w / 2, sy * d / 2, -0.15, 0.06, 0.38, "calcaire", verts=8)


def stade(k, x, y, r=0.0, a=0.35, b_=0.25):
    b = FB(k, x, y, r)
    b.box(0, 0, -0.02, a * 1.6, b_ * 1.6, 0.03, "synth")
    for sx in (-1, 1):
        b.box(sx * a * 0.85, 0, -0.02, 0.06, b_ * 1.7, 0.08, "beton")
        b.box(0, sx * b_ * 0.85, -0.02, a * 1.7, 0.06, 0.08, "beton")


def patinoire(k, x, y, r=0.0):
    b = FB(k, x, y, r)
    b.box(0, 0, -0.1, 0.7, 0.45, 0.22, "blanc_casse")
    b.box(0, 0, 0.12, 0.72, 0.47, 0.03, "bleu")
    b.box(0, -0.226, 0.02, 0.3, 0.006, 0.05, "verre_bureau")


def petit_port(k, pts, couleurs=("rouge", "bleu", "jaune", "blanc", "volet_vert")):
    """Pointus amarrés le long d'une liste de points (x, y, r) au bord de l'eau."""
    for i, (x, y, r) in enumerate(pts):
        b = FB(k, x, y, r)
        b.box(0, 0, -0.3, 0.04, 0.08, 0.03, couleurs[i % len(couleurs)])
        b.box(0, 0.01, -0.27, 0.026, 0.025, 0.018, "blanc")


def plage(k, pts):
    """Parasols sur une plage (points x, y)."""
    for i, (x, y) in enumerate(pts):
        b = FB(k, x, y, 0)
        b.cyl(0, 0, 0, 0.004, 0.07, "blanc", verts=4)
        b.cyl(0, 0, 0.07, 0.04, 0.02, ("parasol_1", "parasol_2")[i % 2], verts=8, r2=0.004)


def cabanons_bord(k, pts):
    """Cabanons du bord de mer (Goudes, Sormiou, Vallon des Auffes) : points (x, y, r)."""
    fac = ("blanc", "facade_bleue", "creme", "facade_rose", "facade_jaune")
    for i, (x, y, r) in enumerate(pts):
        cabanon(k, x, y, r, facade=fac[i % 5], porte=("volet_bleu", "volet_vert", "volet_rouge")[i % 3])
