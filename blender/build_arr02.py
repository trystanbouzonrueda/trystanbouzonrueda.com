"""2e arrondissement fait main : le Panier, la Joliette, Euroméditerranée, le port jusqu'à Arenc.

En direct (MCP) :
    D = "chemin/du/depot/blender/"
    for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "build_arr02.py"): exec(open(D + f).read())
Relançable : reconstruit l'objet mh_arr02.
Phares neufs : Vieille Charité, Hôtel de Ville, clocher des Accoules, Docks, Terrasses du Port,
tour La Marseillaise, silo d'Arenc, grues du port. (Major, Mucem/fort, CMA CGM : déjà faits.)
"""
import math

from shapely.geometry import LineString, Point

q = Quartier(2, larg={"Rue de la République": 0.07, "Boulevard Jacques Saadé": 0.09})
q.efface_tissu()
reserve_monuments(q)
k = q.k
mat("verre_bureau", "#8fc3dc", rough=0.2); mat("blanc_casse", "#f4f1ea"); mat("brique", "#c96f4a")
mat("conteneur_bleu", "#2f6fb5"); mat("conteneur_rouge", "#c94a3a"); mat("conteneur_vert", "#3f8f5a")
mat("conteneur_jaune", "#e8b93a"); mat("rose_charite", "#e7b9a2")


def facing(x, y, tx, ty):
    return math.atan2(tx - x, -(ty - y))


def zone(x, y):
    if y < 2.7: return "panier"
    if x < -3.35: return "port"
    return "euromed"


# ------------------------------------------------------------------ phares
def vieille_charite():
    x, y = ll(43.2994, 5.3675)
    b = FB(k, x, y, 0.0)
    s, e = 0.5, 0.09                       # cour carrée, ailes de 3 niveaux à arcades
    for (cx, cy, w, d) in ((0, -s / 2, s, e), (0, s / 2, s, e), (-s / 2, 0, e, s), (s / 2, 0, e, s)):
        b.box(cx, cy, -0.1, w, d, 0.32, "rose_charite")
        b.box(cx, cy, 0.22, w + 0.01, d + 0.01, 0.02, "calcaire")
    for i in range(7):                     # arcades côté cour
        t = -s / 2 + 0.06 + i * (s - 0.12) / 6
        for (ax, ay) in ((t, -s / 2 + e / 2 + 0.003), (t, s / 2 - e / 2 - 0.003), (-s / 2 + e / 2 + 0.003, t), (s / 2 - e / 2 - 0.003, t)):
            b.box(ax, ay, 0.02, 0.03, 0.006, 0.06, "fenetre_sombre")
    b.box(0, 0, -0.1, 0.14, 0.2, 0.26, "rose_charite")      # chapelle ovale à coupole
    b.cyl(0, 0, 0.16, 0.08, 0.08, "rose_charite", verts=12)
    b.cyl(0, 0, 0.24, 0.08, 0.07, "calcaire", verts=12, r2=0.02)
    b.cyl(0, 0, 0.31, 0.015, 0.03, "calcaire", verts=6)
    q.reserve(Quartier.emprise(x, y, 0, s + 0.12, s + 0.12))


def hotel_de_ville():
    x, _ = ll(43.2961, 5.3697)
    col_ = bassin_vp().intersection(LineString([(x, -5), (x, 5)]))
    y = col_.bounds[3] + 0.13 + 0.11          # juste derrière le quai du Port (bord nord du bassin)
    b = FB(k, x, y, facing(x, y, x, y - 1))   # façade sur le quai du Port
    b.box(0, 0, -0.1, 0.34, 0.2, 0.3, "creme")
    _windows(b, 0.34, 0.2, 2, 0.09, 0.02, 7)
    b.box(0, -0.105, 0.1, 0.34, 0.02, 0.008, "fer_noir")
    b.box(0, 0, 0.2, 0.3, 0.16, 0.04, "zinc")
    b.box(0, -0.102, 0.15, 0.06, 0.006, 0.05, "or_vif")     # armoiries
    b.cyl(0, 0, 0.24, 0.004, 0.12, "fer_noir", verts=4)      # mât + drapeau
    b.box(0.03, 0, 0.32, 0.06, 0.004, 0.035, "bleu")
    q.reserve(Quartier.emprise(x, y, b.r, 0.42, 0.3))


def accoules():
    x, y = ll(43.2979, 5.3683)
    b = FB(k, x, y, 0.0)
    b.box(0, 0, -0.1, 0.09, 0.09, 0.62, "calcaire")
    b.box(0, 0, 0.52, 0.1, 0.1, 0.02, "gris_dome")
    for f in range(3):
        b.box(0, -0.0455, 0.1 + f * 0.13, 0.025, 0.004, 0.07, "fenetre_sombre")
    b.cyl(0, 0, 0.54, 0.055, 0.22, "gris_dome", verts=8, r2=0.004)
    q.reserve(Quartier.emprise(x, y, 0, 0.16, 0.16))


def docks():
    x, y = ll(43.3045, 5.3667)
    b = FB(k, x, y, facing(x, y, x - 1, y + 0.1))           # façade vers le port
    long = 1.3
    b.box(0, 0, -0.1, 0.24, long, 0.36, "pierre_quai")
    for j in range(4):                                       # les 4 corps de bâtiment
        yy = -long / 2 + (j + 0.5) * long / 4
        b.box(0, yy, 0.26, 0.25, long / 4 - 0.04, 0.03, "brique")
        for f in range(4):
            for c in range(5):
                b.box(-0.123, yy - 0.12 + c * 0.06, 0.02 + f * 0.065, 0.004, 0.025, 0.035, "fenetre_sombre")
    q.reserve(Quartier.emprise(x, y, b.r, 0.36, long + 0.1))


def terrasses():
    x, y = ll(43.3085, 5.3640)
    b = FB(k, x, y, facing(x, y, x - 1, y))
    b.box(0, 0, -0.1, 0.36, 0.95, 0.22, "blanc_casse")
    b.box(-0.18, 0, 0.0, 0.008, 0.9, 0.1, "verre_bureau")
    b.box(-0.05, 0, 0.12, 0.3, 0.9, 0.008, "bois")           # la grande terrasse
    for j in range(6):
        b.box(-0.12, -0.38 + j * 0.15, 0.128, 0.05, 0.05, 0.03, "herbe")
    q.reserve(Quartier.emprise(x, y, b.r, 0.46, 1.05))


def marseillaise():
    x, y = ll(43.3105, 5.3655)
    if bpy.data.objects.get("mdl_tour_marseillaise"):   # modèle détaillé posé par place_models.py
        q.reserve(Quartier.emprise(x, y, 0.4, 0.6, 0.6)); return
    b = FB(k, x, y, 0.4)
    b.box(0, 0, -0.1, 0.2, 0.2, 1.25, "blanc_casse")
    cols = ("bleu", "blanc", "rouge", "blanc_casse", "bleu", "rouge")
    for i in range(10):                                      # brise-soleil tricolores
        b.box(-0.09 + i * 0.02, -0.103, 0.0, 0.008, 0.006, 1.12, cols[i % 6])
    b.box(0, 0, 1.15, 0.21, 0.21, 0.02, "fer_noir")
    q.reserve(Quartier.emprise(x, y, 0.4, 0.3, 0.3))


def silo():
    x, y = ll(43.3127, 5.3630)
    b = FB(k, x, y, facing(x, y, x - 1, y))
    b.box(0, 0, -0.1, 0.24, 0.8, 0.3, "beton")
    for j in range(8):
        b.cyl(0, -0.35 + j * 0.1, 0.2, 0.045, 0.14, "beton", verts=10)
    b.box(0, 0, 0.34, 0.12, 0.82, 0.05, "beton_sombre")
    q.reserve(Quartier.emprise(x, y, b.r, 0.34, 0.9))


def conteneurs(k, x, y, r=0.0, n=0):
    b = FB(k, x, y, r)
    cols = ("conteneur_bleu", "conteneur_rouge", "conteneur_vert", "conteneur_jaune", "blanc_casse")
    for i in range(3):
        for j in range(2):
            for f in range(1 + (i + j + n) % 3):
                b.box(-0.06 + i * 0.06, -0.025 + j * 0.05, -0.02 + f * 0.035, 0.055, 0.045, 0.034, cols[(i * 2 + j + f + n) % 5])


def grues():
    """Grues portuaires le long du trait de côte du 2e (zone du port)."""
    from shapely import affinity
    coast = affinity.scale(shape(_D["terre"]), U, U, origin=(0, 0)).exterior   # quais du port
    seg = coast.intersection(q.poly.buffer(0.3))
    n = 0
    for s in getattr(seg, "geoms", [seg]):
        if s.geom_type != "LineString": continue
        d = 0.3
        while d < s.length:
            p = s.interpolate(d); p2 = s.interpolate(min(s.length, d + 0.05))
            if zone(p.x, p.y) == "port":
                tx, ty = p2.x - p.x, p2.y - p.y; nn = math.hypot(tx, ty) or 1
                ix, iy = p.x + ty / nn * 0.15, p.y - tx / nn * 0.15          # un peu dans les terres
                if not q.poly.contains(Point(ix, iy)): ix, iy = p.x - ty / nn * 0.15, p.y + tx / nn * 0.15
                fp = Quartier.emprise(ix, iy, 0, 0.14, 0.14)
                if q.poly.contains(Point(ix, iy)) and q.libre(fp):
                    grue(k, ix, iy, math.atan2(p.x - ix, -(p.y - iy)), h=0.7, couleur=("rouge", "bleu")[n % 2])
                    q.occupe(fp); n += 1
            d += 1.4
    print("grues", n)


vieille_charite(); hotel_de_ville(); accoules(); docks(); terrasses(); marseillaise(); silo(); grues()

# ------------------------------------------------------------------ tissu rue par rue
HAUSS = {"Rue de la République", "Boulevard des Dames", "Place Sadi Carnot", "Quai du Port", "Rue de la Joliette",
         "Boulevard de Paris", "Place de la Joliette", "Rue Colbert", "Place Jules Guesde", "Rue Méry",
         "Rue Jean-François Leca", "Avenue Robert Schuman", "Rue Montolieu"}
F_HAUSS = ("creme", "blanc", "facade_jaune", "creme", "calcaire", "facade_rose")
F_COUL = ("facade_ocre", "facade_rose", "facade_jaune", "facade_saumon", "creme", "facade_bleue", "facade_verte", "facade_terre")
VOLETS = ("volet_bleu", "volet_vert", "volet_lavande", "volet_rouge")
STORES = ("store_rouge", "store_vert", "store_bleu")


def bureau(k, x, y, r=0.0, etages=5, w=0.24, d=0.18, verre="verre_bureau"):
    """Immeuble de bureaux d'Euroméditerranée : bandes blanches et verre."""
    b = FB(k, x, y, r)
    fh = 0.07
    b.box(0, 0, -0.1, w, d, etages * fh + 0.1, "blanc_casse")
    for f in range(etages):
        b.box(0, 0, f * fh + 0.015, w + 0.006, d + 0.006, fh * 0.55, verre)
    b.box(0, 0, etages * fh, w * 0.5, d * 0.5, 0.04, "beton")


def style(nom, t, i):
    j = i + h(nom)
    st = getattr(style, "zone", "panier")
    if nom in HAUSS:
        return haussmannien, 0.24, 0.16, dict(w=0.24, d=0.16, etages=5 + j % 2, facade=F_HAUSS[j % 6], store=STORES[j % 3])
    if st == "panier":
        return panier, 0.1, 0.12, dict(w=0.1, d=0.12, etages=3 + j % 3, facade=F_COUL[j % 8], volets=VOLETS[j % 4], linge=j % 3 == 0)
    if st == "port":
        return dock, 0.6, 0.22, dict(long=0.6, d=0.22, etages=2 + j % 2)
    if j % 9 == 0:
        return tour, 0.18, 0.18, dict(w=0.18, etages=8 + j % 5, facade=("blanc_casse", "beton")[j % 2], accent="bleu_loggia")
    return bureau, 0.24, 0.18, dict(w=0.24, d=0.18, etages=4 + j % 4, verre=("verre_bureau", "fenetre_sombre")[j % 2])


# le_long par zone : on filtre les rues dont le milieu tombe dans la zone
toutes = q.rues
for z in ("panier", "euromed", "port"):
    q.rues = [r for r in toutes if zone(r[2].interpolate(0.5, normalized=True).x, r[2].interpolate(0.5, normalized=True).y) == z]
    style.zone = z
    q.le_long(style)
q.rues = toutes
q.dessine_rues()


def coeur(i):
    return panier, 0.1, 0.11, dict(w=0.1, d=0.11, etages=3 + i % 2, facade=F_COUL[(i * 5) % 8], volets=VOLETS[i % 4])


# cœurs d'îlots : maisons au Panier, conteneurs au port, rien à Euroméditerranée (esplanades)
reste = q.poly
q_poly = q.poly
from shapely.geometry import box as _box
x0, y0, x1, y1 = q.poly.bounds
q.poly = q_poly.intersection(_box(x0, y0, x1, 2.7)); q._set_zone(); q.remplit(coeur, pas=0.15)
q.poly = q_poly.intersection(_box(x0, 2.7, -3.35, y1)); q._set_zone(); q.remplit(lambda i: (conteneurs, 0.2, 0.12, dict(n=i)), pas=0.24)
q.poly = q_poly; q._set_zone()
q.fini()
if "DEBUG_SVG" in globals(): debug_svg(q, DEBUG_SVG)
