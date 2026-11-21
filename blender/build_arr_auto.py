"""Arrondissements 3 à 16 : construction pilotée par une fiche par arrondissement (CONFIG).

En direct (MCP), pour l'arrondissement n :
    D = "chemin/du/depot/blender/"
    g = {"ARR": n}
    for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "lieux.py", "build_arr_auto.py"): exec(open(D + f).read(), g)
Relançable : reconstruit l'objet mh_arrNN. Les 1er et 2e ont leurs propres scripts (build_arr01/02.py).

Fiche = style des rues (par zone et par nom), cités (barres et tours), zones d'activités,
monuments génériques posés sur leur lieu réel (remplacés plus tard par les modèles détaillés).
"""
import math

from shapely.geometry import Point, box as _box

F_HAUSS = ("creme", "blanc", "facade_jaune", "creme", "calcaire", "facade_rose")
F_COUL = ("facade_ocre", "facade_rose", "facade_jaune", "facade_saumon", "creme", "facade_bleue", "facade_verte", "facade_terre")
F_VILLA = ("facade_ocre", "creme", "facade_rose", "facade_jaune", "blanc", "facade_saumon")
VOLETS = ("volet_bleu", "volet_vert", "volet_lavande", "volet_rouge")
STORES = ("store_rouge", "store_vert", "store_bleu")


# ------------------------------------------------------------------ familles de bâtiments
def s_hauss(j):
    return haussmannien, 0.24, 0.16, dict(w=0.24, d=0.16, etages=5 + j % 2, facade=F_HAUSS[j % 6], store=STORES[j % 3])


def s_ancien(j):
    if j % 4 == 0:
        return immeuble, 0.16, 0.14, dict(w=0.16, d=0.14, etages=4 + j % 2, facade=F_COUL[j % 8])
    return trois_fenetres, 0.13, 0.14, dict(w=0.13, d=0.14, etages=3 + j % 2, facade=F_COUL[j % 8], volets=VOLETS[j % 4], balcon=j % 2 == 0)


def s_residentiel(j):
    if j % 3 == 0:
        return immeuble, 0.18, 0.15, dict(w=0.18, d=0.15, etages=4 + j % 4, facade=F_COUL[(j * 3) % 8])
    if j % 7 == 0:
        return None, 0.1, 0, {}
    return maison, 0.11, 0.1, dict(w=0.11, d=0.1, etages=1 + j % 2, facade=F_VILLA[j % 6])


def s_pavillon(j):
    if j % 3 == 1:
        return None, 0.08 + (j % 4) * 0.03, 0, {}   # jardins
    if j % 5 == 0:
        return villa, 0.13, 0.11, dict(w=0.13, d=0.11, facade=F_VILLA[j % 6])
    return maison, 0.11, 0.1, dict(w=0.11, d=0.1, etages=1, facade=F_VILLA[(j * 5) % 6])


def s_cite(j):
    if j % 3 == 0:
        return tour, 0.18, 0.18, dict(w=0.18, etages=10 + j % 6, facade=("beton", "blanc_casse")[j % 2], accent=("bleu_loggia", "rouge_loggia")[j % 2])
    return barre, 0.7, 0.16, dict(long=0.7, d=0.16, etages=6 + j % 5, accents=(("rouge_loggia", "jaune_loggia"), ("bleu_loggia", "jaune_loggia"))[j % 2])


def s_activite(j):
    if j % 4 == 3: return None, 0.15, 0, {}
    return entrepot, 0.3, 0.2, dict(w=0.3, d=0.2, facade=("beton", "blanc_casse", "facade_terre")[j % 3])


FAM = {"hauss": s_hauss, "ancien": s_ancien, "residentiel": s_residentiel, "pavillon": s_pavillon,
       "cite": s_cite, "activite": s_activite}

# ------------------------------------------------------------------ fiches
# defaut : famille par défaut ; hauss : rues haussmanniennes ; cites / activite : (lat, lon, rayon en unités) ;
# zones : [(lat_min, lat_max, lon_min, lon_max, famille)] ; remplit : famille des cœurs d'îlots (ou None) ;
# lieux : [(fonction, lat, lon, rotation (rad) ou None = vers le sud, kwargs, (w, d) réservé)]
CONFIG = {
    3: dict(defaut="ancien", remplit="ancien",
            hauss={"Boulevard National", "Boulevard de Strasbourg", "Avenue Camille Pelletan", "Rue de Crimée", "Boulevard de Paris"},
            cites=[(43.3125, 5.3810, 0.6)],
            lieux=[(palais, 43.3106, 5.3907, 0.0, dict(w=0.9, d=0.35, h=0.24, colonnes=0, facade="brique", toit="beton_sombre"), (1.0, 0.5)),   # Friche la Belle de Mai
                   (tour, 43.3110, 5.3918, 0.0, dict(w=0.12, etages=9, facade="brique", accent="jaune_loggia"), (0.2, 0.2)),
                   (eglise_ville, 43.3125, 5.3860, 0.0, {}, (0.3, 0.55))]),
    4: dict(defaut="ancien", remplit="ancien",
            hauss={"Boulevard de la Libération - Général de Monsabert", "Boulevard Longchamp", "Avenue des Chartreux",
                   "Boulevard Philippon", "Avenue de Saint-Just", "Boulevard Françoise Duparc", "Boulevard de la Blancarde"},
            lieux=[(eglise_ville, 43.3108, 5.4005, 0.0, dict(facade="creme"), (0.3, 0.55)),          # Chartreux
                   (eglise_ville, 43.2995, 5.4050, 0.0, dict(facade="calcaire"), (0.3, 0.55))]),     # Blancarde
    5: dict(defaut="ancien", remplit="ancien",
            hauss={"Boulevard Baille", "Rue de Lodi", "Boulevard Jean Moulin", "Avenue de Toulon", "Boulevard Chave",
                   "Boulevard Eugène Pierre", "Rue Saint-Pierre"},
            lieux=[(place_marche, 43.2937, 5.3858, 0.0, dict(n=10, rayon=0.3), (0.75, 0.75)),        # place Jean-Jaurès (la Plaine)
                   (hopital, 43.2895, 5.4005, 0.0, dict(etages=12), (0.8, 0.45))]),                  # la Timone
    6: dict(defaut="hauss", remplit="ancien",
            hauss={"Rue de Rome", "Rue Paradis", "Boulevard Notre-Dame", "Cours Lieutaud", "Rue Breteuil", "Rue Edmond Rostand",
                   "Boulevard Périer", "Avenue du Prado", "Rue Saint-Ferréol", "Place Castellane"},
            zones=[(43.2870, 43.2960, 5.3800, 5.3900, "ancien")],                                     # Cours Julien, Notre-Dame-du-Mont
            lieux=[(palais, 43.2905, 5.3800, 0.0, dict(w=0.7, d=0.45, h=0.34, colonnes=8, dome=False), (0.85, 0.65)),   # Préfecture
                   (fontaine, 43.2853, 5.3836, None, dict(h=0.4), (0.4, 0.4)),                        # fontaine Cantini
                   (palais, 43.2895, 5.3730, 0.0, dict(w=0.55, d=0.35, h=0.3, colonnes=6), (0.65, 0.5)),   # palais de justice
                   (place_marche, 43.2935, 5.3832, 0.0, dict(n=6, rayon=0.2), (0.5, 0.5))]),          # Cours Julien
    7: dict(defaut="ancien", remplit="ancien",
            zones=[(43.2740, 43.2860, 5.3400, 5.3600, "pavillon")],                                   # Malmousque, Endoume haut
            lieux=[(palais, 43.2930, 5.3592, 0.5, dict(w=0.6, d=0.3, h=0.26, colonnes=0, facade="calcaire", toit="ardoise"), (0.7, 0.45)),   # Pharo
                   (fort, 43.2905, 5.3655, 0.0, dict(w=0.45, d=0.32), (0.6, 0.5)),                    # abbaye Saint-Victor
                   (fort, 43.2918, 5.3622, 0.0, dict(w=0.6, d=0.35), (0.7, 0.5))]),                   # fort Saint-Nicolas
    8: dict(defaut="residentiel", remplit=None,
            hauss={"Avenue du Prado", "Boulevard Michelet", "Avenue de Mazargues", "Rue Paradis", "Avenue du Prado 2"},
            zones=[(43.2050, 43.2300, 5.3300, 5.3700, "pavillon")],                                   # Goudes, Callelongue
            lieux=[]),
    9: dict(defaut="pavillon", remplit=None,
            cites=[(43.2340, 5.4280, 0.5), (43.2420, 5.4120, 0.4)],                                   # la Cayolle, Sainte-Marguerite
            zones=[(43.2450, 43.2700, 5.3950, 5.4200, "residentiel")],
            lieux=[(campus, 43.2320, 5.4370, 0.0, dict(n=5), (1.2, 1.2)),                             # Luminy
                   (fontaine, 43.2490, 5.4040, None, dict(h=0.5), (0.4, 0.4))]),                      # obélisque de Mazargues
    10: dict(defaut="residentiel", remplit=None,
             activite=[(43.2790, 5.4050, 0.6)],
             lieux=[(patinoire, 43.2826, 5.4170, 0.0, {}, (0.85, 0.6)),                               # palais omnisports
                    (eglise_ville, 43.2790, 5.4250, 0.0, {}, (0.3, 0.55))]),                          # Saint-Loup
    11: dict(defaut="pavillon", remplit=None,
             cites=[(43.2900, 5.4380, 0.5), (43.2920, 5.4900, 0.4)],                                  # Air-Bel, la Rouguière
             activite=[(43.2990, 5.4830, 0.9), (43.2900, 5.5100, 0.8)],                              # la Valentine, Saint-Menet
             lieux=[(centre_commercial, 43.2930, 5.4830, 0.0, dict(w=1.2, d=0.6), (1.4, 1.2)),        # centre commercial la Valentine
                    (eglise_ville, 43.3000, 5.5180, 0.0, dict(facade="creme", toit="tuile"), (0.3, 0.55))]),   # village des Camoins
    12: dict(defaut="pavillon", remplit=None,
             zones=[(43.2950, 43.3100, 5.4100, 5.4300, "residentiel")],
             lieux=[(eglise_ville, 43.3040, 5.4180, 0.0, dict(facade="creme", toit="tuile"), (0.3, 0.55)),   # Saint-Barnabé
                    (eglise_ville, 43.3170, 5.4270, 0.0, dict(facade="creme", toit="tuile"), (0.3, 0.55))]), # Trois-Lucs
    13: dict(defaut="pavillon", remplit=None,
             cites=[(43.3290, 5.4150, 0.6), (43.3390, 5.4210, 0.5), (43.3310, 5.4120, 0.5), (43.3370, 5.4260, 0.5)],   # Frais-Vallon, les Lauriers, Malpassé, la Rose
             zones=[(43.3200, 43.3450, 5.4050, 5.4350, "residentiel")],
             lieux=[(campus, 43.3420, 5.4370, 0.0, dict(n=5), (1.2, 1.2)),                            # technopôle de Château-Gombert
                    (eglise_ville, 43.3570, 5.4500, 0.0, dict(facade="creme", toit="tuile"), (0.3, 0.55))]), # Château-Gombert village
    14: dict(defaut="residentiel", remplit=None,
             cites=[(43.3380, 5.4040, 0.6), (43.3310, 5.3940, 0.5), (43.3360, 5.3920, 0.5), (43.3460, 5.3970, 0.5)],   # le Merlan, Font-Vert, la Busserine, Saint-Barthélemy
             lieux=[(centre_commercial, 43.3430, 5.4050, 0.3, dict(w=0.9, d=0.5, nom_couleur="bleu"), (1.1, 1.0))]),   # centre commercial du Merlan
    15: dict(defaut="residentiel", remplit=None,
             cites=[(43.3630, 5.3580, 0.6), (43.3720, 5.3690, 0.6), (43.3480, 5.3830, 0.5), (43.3520, 5.3820, 0.4),
                    (43.3600, 5.3600, 0.5), (43.3620, 5.3650, 0.4)],                                  # Plan d'Aou, la Savine, Bassens, la Solidarité, la Viste
             activite=[(43.3400, 5.3600, 1.2), (43.3330, 5.3700, 0.8)],                               # Arenc nord, Saint-Louis
             lieux=[(hopital, 43.3790, 5.3660, 0.0, dict(etages=11), (0.8, 0.45)),                    # hôpital Nord
                    (centre_commercial, 43.3600, 5.3460, 0.0, dict(w=1.3, d=0.6, nom_couleur="synth"), (1.5, 1.2))]),   # Grand Littoral
    16: dict(defaut="pavillon", remplit=None,
             cites=[(43.3612, 5.3484, 0.6)],                                                          # la Castellane
             zones=[(43.3550, 43.3680, 5.3080, 5.3250, "ancien")],                                    # village de l'Estaque
             activite=[(43.3550, 5.3350, 0.8)],
             lieux=[(eglise_ville, 43.3615, 5.3180, 0.0, dict(facade="creme", toit="tuile"), (0.3, 0.55)),
                    (centre_commercial, 43.3600, 5.3460, 0.0, dict(w=1.3, d=0.6, nom_couleur="synth"), (1.5, 1.2))]),   # Grand Littoral
    17: dict(defaut="pavillon", remplit=None,                                                         # Plan-de-Cuques
             zones=[(43.3455, 43.3500, 5.4590, 5.4680, "ancien")],                                    # le village autour de l'église
             lieux=[]),
}

# ------------------------------------------------------------------ construction
n = ARR
cfg = CONFIG[n]
q = Quartier(n)
q.efface_tissu()
reserve_monuments(q)
k = q.k
cites = [(Point(*ll(a, b)), r) for a, b, r in cfg.get("cites", [])]
activ = [(Point(*ll(a, b)), r) for a, b, r in cfg.get("activite", [])]
zones = [(ll(a0, o0), ll(a1, o1), fam) for a0, a1, o0, o1, fam in cfg.get("zones", [])]


def famille_at(x, y):
    p = Point(x, y)
    for c, r in cites:
        if c.distance(p) < r: return "cite"
    for c, r in activ:
        if c.distance(p) < r: return "activite"
    for (x0, y0), (x1, y1), fam in zones:
        if x0 <= x <= x1 and y0 <= y <= y1: return fam
    return cfg["defaut"]


# monuments génériques
for fn, la, lo, r, kw, (rw, rd) in cfg.get("lieux", []):
    x, y = ll(la, lo)
    if not q.poly.buffer(0.3).contains(Point(x, y)):
        print("hors arrondissement :", fn.__name__, la, lo); continue
    r = 0.0 if r is None else r
    if fn in (fontaine,): fn(k, x, y, **kw)
    elif fn in (place_marche, campus): fn(k, x, y, r, **kw)
    else: fn(k, x, y, r, **kw)
    q.reserve(Quartier.emprise(x, y, r, rw, rd))


def style(nom, t, i):
    j = i + h(nom)
    if nom in cfg.get("hauss", set()) and style.fam in ("ancien", "residentiel", "hauss"):
        return s_hauss(j)
    return FAM[style.fam](j)


# rues regroupées par famille (selon le milieu de la rue)
toutes = q.rues
groupes = {}
for r_ in toutes:
    m = r_[2].interpolate(0.5, normalized=True)
    groupes.setdefault(famille_at(m.x, m.y), []).append(r_)
for fam, rues in groupes.items():
    q.rues = rues; style.fam = fam
    gap = {"pavillon": 0.03, "residentiel": 0.02, "cite": 0.25, "activite": 0.08}.get(fam, 0.008)
    q.le_long(style, gap=gap)
q.rues = toutes
q.dessine_rues()

# cœurs d'îlots (quartiers denses) et cœurs de cités (barres en peigne)
poly0 = q.poly
if cfg.get("remplit"):
    fam = FAM[cfg["remplit"]]
    q.remplit(lambda i: fam(i * 7 + 3) if fam(i * 7 + 3)[0] else s_ancien(i), pas=0.17)
for c, r in cites:
    q.poly = poly0.intersection(c.buffer(r)); q._set_zone()
    if not q.poly.is_empty: q.remplit(lambda i: s_cite(i + 1), pas=0.45)
q.poly = poly0; q._set_zone()
q.fini()
if "DEBUG_SVG" in globals(): debug_svg(q, DEBUG_SVG)
