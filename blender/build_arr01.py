"""1er arrondissement fait main : Canebière, Belsunce, Noailles, Opéra, Thiers.

En direct (MCP) :
    D = "chemin/du/depot/blender/"
    for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "build_arr01.py"): exec(open(D + f).read())
Relançable : reconstruit l'objet mh_arr01.
Phares : église des Réformés, palais de la Bourse, Opéra, marché de Noailles, Canebière (platanes, kiosques).
"""
import math

q = Quartier(1, larg={"La Canebière": 0.115})
q.efface_tissu()
reserve_monuments(q)
k = q.k


def facing(x, y, tx, ty):
    """Rotation r pour que la façade (-y local) regarde le point (tx, ty)."""
    dx, dy = tx - x, ty - y
    return math.atan2(dx, -dy)


# ------------------------------------------------------------------ phares
belges = ll(43.2952, 5.3744)


def reformes():
    x, y = ll(43.2990, 5.3840)
    b = FB(k, x, y, facing(x, y, *belges))
    b.box(0, 0.12, -0.1, 0.3, 0.6, 0.38, "gris_dome")                 # nef
    b.gable(0, 0.12, 0.28, 0.32, 0.62, 0.1, "ardoise", along_y=True)
    b.box(0, 0.42, -0.1, 0.2, 0.08, 0.3, "gris_dome")                  # chevet
    for sx in (-1, 1):                                                 # les deux flèches
        b.box(sx * 0.11, -0.17, -0.1, 0.11, 0.11, 0.72, "calcaire")
        b.box(sx * 0.11, -0.17, 0.62, 0.125, 0.125, 0.02, "gris_dome")
        b.cyl(sx * 0.11, -0.17, 0.64, 0.065, 0.32, "gris_dome", verts=8, r2=0.004)
        for f in range(3):
            b.box(sx * 0.11, -0.2255, 0.12 + f * 0.17, 0.03, 0.004, 0.09, "fenetre_sombre")
    b.box(0, -0.18, -0.1, 0.12, 0.08, 0.34, "calcaire")                 # portail
    b.box(0, -0.221, 0.02, 0.06, 0.004, 0.12, "bois")
    b.cyl(0, -0.222, 0.2, 0.035, 0.004, "verre", verts=10)             # rosace
    q.reserve(Quartier.emprise(x, y, b.r, 0.5, 0.85))


def bourse():
    x, y = ll(43.2966, 5.3756)
    b = FB(k, x, y, facing(x, y, x + 0.503, y - 0.864))
    b.box(0, 0, -0.1, 0.75, 0.4, 0.4, "creme")
    b.box(0, -0.25, -0.1, 0.5, 0.1, 0.1, "calcaire")                   # perron
    for i in range(8):
        b.cyl(-0.21 + i * 0.06, -0.24, 0.0, 0.016, 0.24, "calcaire", verts=8)
    b.box(0, -0.24, 0.24, 0.52, 0.1, 0.05, "calcaire")                 # entablement
    b.box(0, -0.02, 0.3, 0.78, 0.43, 0.03, "calcaire")
    b.box(0, 0, 0.33, 0.5, 0.3, 0.07, "zinc")
    b.box(0, -0.29, 0.29, 0.14, 0.01, 0.07, "or_vif")                  # horloge et groupe sculpté
    _windows(b, 0.7, 0.4, 3, 0.1, 0.0, 9)
    q.reserve(Quartier.emprise(x, y, b.r, 0.85, 0.65))


def opera():
    x, y = ll(43.2938, 5.3766)
    b = FB(k, x, y, facing(x, y, x + 1, y))
    b.box(0, 0.05, -0.1, 0.42, 0.5, 0.42, "creme")
    b.box(0, 0.08, 0.32, 0.36, 0.4, 0.1, "zinc")                       # cage de scène
    b.box(0, -0.24, -0.1, 0.42, 0.08, 0.1, "calcaire")
    for i in range(6):
        b.cyl(-0.175 + i * 0.07, -0.23, 0.0, 0.017, 0.22, "calcaire", verts=8)
    b.box(0, -0.23, 0.22, 0.44, 0.09, 0.06, "calcaire")
    b.box(0, -0.275, 0.24, 0.2, 0.005, 0.03, "or_vif")                 # « OPÉRA »
    q.reserve(Quartier.emprise(x, y, b.r, 0.55, 0.7))


def canebiere():
    lines = [l for n, t, l in q.rues if n == "La Canebière"]
    for l in lines:
        seg = l.intersection(q.poly)
        for s in getattr(seg, "geoms", [seg]):
            if s.geom_type != "LineString": continue
            # (la chaussée est dessinée par build_routes.py)
            q.reserve(s.buffer(0.112))
            d = 0.15
            while d < s.length - 0.1:
                p, p2 = s.interpolate(d), s.interpolate(d + 0.02)
                tx, ty = p2.x - p.x, p2.y - p.y; nn = math.hypot(tx, ty) or 1
                for side in (1, -1):
                    platane(k, p.x - side * ty / nn * 0.105, p.y + side * tx / nn * 0.105, s=0.7)
                d += 0.26
    for la, lo, c in ((43.2958, 5.3768, "store_vert"), (43.2968, 5.3790, "store_rouge"), (43.2979, 5.3812, "store_bleu")):
        kiosque(k, *ll(la, lo), couleur=c)


def noailles():
    """Marché des Capucins : étals sur la rue Longue des Capucins et la place."""
    lines = [l for n, t, l in q.rues if n in ("Rue Longue des Capucins", "Place du Marché des Capucins")]
    stores = ("store_rouge", "store_vert", "store_bleu", "store_rouge", "jaune")
    fruits = (("rouge", "jaune", "herbe"), ("jaune", "facade_saumon", "rouge"), ("herbe", "rouge", "facade_jaune"))
    i = 0
    for l in lines:
        seg = l.intersection(q.poly)
        for s in getattr(seg, "geoms", [seg]):
            if s.geom_type != "LineString": continue
            d = 0.06
            while d < s.length - 0.04:
                p, p2 = s.interpolate(d), s.interpolate(d + 0.02)
                r = math.atan2(p2.y - p.y, p2.x - p.x)
                for side in (1, -1):
                    nx, ny = -math.sin(r) * side, math.cos(r) * side
                    etal(k, p.x + nx * 0.035, p.y + ny * 0.035, r + (math.pi if side < 0 else 0),
                         store=stores[i % 5], fruits=fruits[i % 3])
                    i += 1
                d += 0.16


reformes(); bourse(); opera(); canebiere(); noailles()

# ------------------------------------------------------------------ tissu fait main, rue par rue
HAUSS = {"La Canebière", "Rue de Rome", "Rue Saint-Ferréol", "Cours Belsunce", "Boulevard Garibaldi",
         "Boulevard d'Athènes", "Boulevard Dugommier", "Cours Lieutaud", "Quai des Belges", "Rue Paradis",
         "Boulevard National", "Boulevard de la Libération - Général de Monsabert", "Allée Léon Gambetta",
         "Cours Saint-Louis", "Boulevard Voltaire", "Cours Joseph Thierry", "Rue Grignan", "Boulevard de la Liberté",
         "Rue de la République", "Rue Colbert", "Cours Jean Ballard", "Boulevard Maurice Bourdet"}
NOAILLES = {"Rue d'Aubagne", "Rue Longue des Capucins", "Rue des Récolettes", "Rue du Musée", "Rue Vacon",
            "Rue Rodolphe Pollak", "Rue de l'Arc", "Rue Moustier", "Rue Pavillon", "Rue des Feuillants",
            "Rue Estelle", "Rue Curiol", "Rue de la Palud", "Rue Jean Roque", "Rue Saint-Saëns", "Rue Fortia"}
BELSUNCE = {"Rue Thubaneau", "Rue Nationale", "Rue d'Aix", "Rue des Dominicaines", "Rue du Petit Saint-Jean",
            "Rue Bernard du Bois", "Rue des Petites Maries", "Rue Tapis Vert", "Rue du Baignoir",
            "Rue Puvis de Chavannes", "Rue Sainte-Barbe", "Rue des Récolettes", "Rue de la Fare", "Rue des Convalescents"}
F_HAUSS = ("creme", "blanc", "facade_jaune", "creme", "calcaire", "facade_rose")
F_COUL = ("facade_ocre", "facade_rose", "facade_jaune", "facade_saumon", "creme", "facade_bleue", "facade_verte", "facade_terre")
VOLETS = ("volet_bleu", "volet_vert", "volet_lavande", "volet_rouge")
STORES = ("store_rouge", "store_vert", "store_bleu")


def style(nom, t, i):
    j = i + h(nom)
    if nom in HAUSS or t in ("primary", "secondary"):
        return haussmannien, 0.24, 0.16, dict(w=0.24, d=0.16, etages=5 + j % 2, facade=F_HAUSS[j % 6], store=STORES[j % 3])
    if nom in BELSUNCE:
        return panier, 0.1, 0.12, dict(w=0.1, d=0.12, etages=4 + j % 2, facade=F_COUL[j % 8], volets=VOLETS[j % 4], linge=j % 3 == 0)
    if nom in NOAILLES:
        return trois_fenetres, 0.13, 0.14, dict(w=0.13, d=0.14, etages=3 + j % 2, facade=F_COUL[j % 8], volets=VOLETS[j % 4])
    return trois_fenetres, 0.13, 0.14, dict(w=0.13, d=0.14, etages=3 + j % 3 // 2, facade=F_COUL[(j * 3) % 8], volets=VOLETS[j % 4], balcon=j % 2 == 0)


def coeur(i):
    return trois_fenetres, 0.13, 0.13, dict(w=0.13, d=0.13, etages=2 + i % 2, facade=F_COUL[(i * 5) % 8], volets=VOLETS[i % 4], balcon=False)


q.dessine_rues()
q.le_long(style)
q.remplit(coeur, pas=0.17)
q.fini()
if "DEBUG_SVG" in globals(): debug_svg(q, DEBUG_SVG)
