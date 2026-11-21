"""Bibliothèque de bâtiments marseillais faits main (même DA que les monuments).

À charger après lib.py et la partie outils de build_monuments.py (classe Kit).
Chaque fonction prend un Kit de quartier + une position/rotation locale et des paramètres :
chaque appel décrit UN bâtiment précis (couleurs, étages, détails) : pas de copies aléatoires.
Convention : la façade principale regarde -y (avant rotation).
"""
import math

mat("facade_ocre", "#e8b878"); mat("facade_rose", "#eab2a0"); mat("facade_jaune", "#f3d27a")
mat("facade_saumon", "#f0a07a"); mat("facade_terre", "#d98b5f"); mat("facade_bleue", "#9cc3d5")
mat("facade_verte", "#b5d3a0"); mat("volet_bleu", "#3f7fb0"); mat("volet_vert", "#4f8a5b")
mat("volet_lavande", "#8f86c9"); mat("volet_rouge", "#b9473b"); mat("zinc", "#7c8794")
mat("fer_noir", "#2b2d33"); mat("linge_1", "#ff6b6b"); mat("linge_2", "#ffd93d"); mat("linge_3", "#6bcBff")
mat("store_rouge", "#d9483b"); mat("store_vert", "#3c9a5f"); mat("store_bleu", "#3f7fd1")


class B:
    """Repère d'un bâtiment dans un Kit : position (x, y), rotation r, sol z (local au Kit)."""

    def __init__(self, k, x, y, r=0.0, z=None):
        self.k, self.x, self.y, self.r = k, x, y, r
        self.z = (ground(k.o.x + x, k.o.y + y) - k.o.z) if z is None else z

    def _p(self, lx, ly):
        c, s = math.cos(self.r), math.sin(self.r)
        return self.x + lx * c - ly * s, self.y + lx * s + ly * c

    def box(self, lx, ly, lz, sx, sy, sz, m, rz=0.0):
        x, y = self._p(lx, ly)
        return self.k.box(x, y, self.z + lz, sx, sy, sz, m, rz=rz + self.r)

    def cyl(self, lx, ly, lz, r, h, m, verts=8, r2=None):
        x, y = self._p(lx, ly)
        return self.k.cyl(x, y, self.z + lz, r, h, m, verts=verts, r2=r2)

    def ball(self, lx, ly, lz, r, m, squash=1.0):
        x, y = self._p(lx, ly)
        return self.k.ball(x, y, self.z + lz, r, m, squash=squash)

    def gable(self, lx, ly, lz, sx, sy, h, m, along_y=False):
        x, y = self._p(lx, ly)
        g = self.k.gable(x, y, self.z + lz, sx, sy, h, m)
        g.rotation_euler[2] += self.r + (math.pi / 2 if along_y else 0)
        return g

    def hip(self, lx, ly, lz, sx, sy, h, m):
        """Toit à 4 pans : base rectangulaire, faîtage court selon x."""
        x, y = self._p(lx, ly)
        rx = max(0.0, (sx - sy) / 2)
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0),
                                       (-rx, 0, h), (rx, 0, h)]]
        for f in [(v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[0], v[4], v[3]), (v[1], v[2], v[5]), (v[3], v[2], v[1], v[0])]:
            bm.faces.new(f)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        me = bpy.data.meshes.new("mh"); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("mh", me); bpy.context.scene.collection.objects.link(ob)
        ob.location = self.k._w(x, y, self.z + lz)
        _finish(ob, m, None, "Monuments", "MH")
        ob.rotation_euler[2] = self.r
        return self.k._keep(ob)


def _windows(b, w, d, floors, fh, z0, cols, m_win="fenetre_sombre", volets=None, face=-1):
    """Rangées de fenêtres (+ volets) sur la façade avant (face=-1) ou arrière (face=1)."""
    for f in range(floors):
        zz = z0 + f * fh + fh * 0.3
        for c in range(cols):
            xx = -w / 2 + (c + 0.5) * w / cols
            b.box(xx, face * (d / 2 + 0.003), zz, w / cols * 0.42, 0.006, fh * 0.45, m_win)
            if volets:
                for sx in (-1, 1):
                    b.box(xx + sx * w / cols * 0.33, face * (d / 2 + 0.004), zz, w / cols * 0.16, 0.006, fh * 0.45, volets)


# ------------------------------------------------------------------ types de bâtiments
def trois_fenetres(k, x, y, r=0.0, etages=3, facade="creme", volets="volet_bleu", toit="tuile", balcon=True, w=0.17, d=0.2):
    """La maison marseillaise typique : façade étroite à trois fenêtres par étage, génoise et tuiles."""
    b = B(k, x, y, r)
    fh = 0.075; h = etages * fh
    b.box(0, 0, -0.15, w, d, h + 0.15, facade)
    _windows(b, w, d, etages, fh, 0, 3, volets=volets)
    b.box(0, 0, h, w + 0.012, d + 0.012, 0.012, "calcaire")      # génoise
    b.gable(0, 0, h + 0.012, w + 0.02, d + 0.02, 0.05, toit, along_y=True)
    b.box(0, -d / 2 - 0.004, 0, w * 0.18, 0.006, fh * 0.75, "bois")  # porte
    if balcon:
        b.box(0, -d / 2 - 0.012, fh + 0.01, w * 0.5, 0.025, 0.006, "fer_noir")
    return b


def haussmannien(k, x, y, r=0.0, etages=5, w=0.32, d=0.26, facade="creme", store="store_rouge", toit="zinc"):
    """Immeuble de la Canebière : pierre crème, balcons filants noirs, toit de zinc, commerce au rez-de-chaussée."""
    b = B(k, x, y, r)
    fh = 0.07; h = etages * fh
    b.box(0, 0, -0.15, w, d, h + 0.15, facade)
    _windows(b, w, d, etages - 1, fh, fh, 5)
    for f in (2, etages - 1):  # balcons filants
        b.box(0, -d / 2 - 0.012, f * fh + 0.004, w, 0.025, 0.006, "fer_noir")
    b.box(0, -d / 2 - 0.004, 0, w * 0.9, 0.006, fh * 0.75, "fenetre_sombre")   # vitrine
    b.box(0, -d / 2 - 0.03, fh * 0.75, w * 0.9, 0.06, 0.012, store)            # store
    b.box(0, 0, h, w - 0.03, d - 0.03, 0.05, toit)                             # mansarde
    b.box(0, 0, h + 0.05, w * 0.6, 0.02, 0.025, toit)
    return b


def panier(k, x, y, r=0.0, etages=4, w=0.12, d=0.16, facade="facade_ocre", volets="volet_vert", linge=False):
    """Maison étroite et haute du Panier, couleurs chaudes, linge tendu."""
    b = B(k, x, y, r)
    fh = 0.07; h = etages * fh
    b.box(0, 0, -0.15, w, d, h + 0.15, facade)
    _windows(b, w, d, etages, fh, 0, 2, volets=volets)
    b.gable(0, 0, h, w + 0.016, d + 0.016, 0.04, "tuile", along_y=True)
    if linge:
        zz = fh * 2 + 0.02
        b.box(0, -d / 2 - 0.03, zz + 0.03, w + 0.06, 0.003, 0.003, "blanc")
        for i, m in enumerate(("linge_1", "linge_2", "linge_3")):
            b.box(-0.03 + i * 0.03, -d / 2 - 0.03, zz, 0.018, 0.004, 0.026, m)
    return b


def cabanon(k, x, y, r=0.0, facade="blanc", porte="volet_bleu", terrasse=True):
    """Cabanon de pêcheur (Vallon des Auffes, Goudes, Estaque)."""
    b = B(k, x, y, r)
    b.box(0, 0, -0.08, 0.13, 0.1, 0.16, facade)
    b.gable(0, 0, 0.08, 0.15, 0.12, 0.045, "tuile")
    b.box(-0.025, -0.053, 0, 0.03, 0.006, 0.055, porte)
    b.box(0.035, -0.053, 0.025, 0.025, 0.006, 0.025, porte)
    if terrasse:
        b.box(0, -0.1, -0.02, 0.13, 0.08, 0.02, "bois")
    return b


def bastide(k, x, y, r=0.0, facade="facade_ocre", volets="volet_vert", cypres=2):
    """Bastide provençale : volume carré, toit 4 pans, volets pastel, cyprès."""
    b = B(k, x, y, r)
    b.box(0, 0, -0.12, 0.3, 0.22, 0.27, facade)
    _windows(b, 0.3, 0.22, 2, 0.07, 0.01, 4, volets=volets)
    b.hip(0, 0, 0.15, 0.34, 0.26, 0.07, "tuile")
    for i in range(cypres):
        b.cyl(0.22 + i * 0.07, 0.04, 0, 0.025, 0.2, "cypres", verts=6, r2=0.004)
    return b


def barre(k, x, y, r=0.0, long=0.8, etages=8, d=0.16, facade="beton", accents=("rouge_loggia", "jaune_loggia"), paraboles=True):
    """Barre de cité (Quartiers Nord) : longue, haute, bandes de couleur, paraboles."""
    b = B(k, x, y, r)
    fh = 0.06; h = etages * fh
    b.box(0, 0, -0.1, long, d, h + 0.1, facade)
    n = max(3, int(long / 0.07))
    for f in range(etages):
        for c in range(n):
            b.box(-long / 2 + (c + 0.5) * long / n, -d / 2 - 0.003, f * fh + 0.02, long / n * 0.5, 0.006, fh * 0.45, "fenetre_sombre")
    for i, a in enumerate(accents):  # bandes verticales colorées
        b.box(-long / 2 + long * (0.25 + 0.5 * i), -d / 2 - 0.005, 0, 0.05, 0.008, h, a)
    if paraboles:
        for c in range(0, n, 3):
            b.cyl(-long / 2 + (c + 0.5) * long / n, -d / 2 - 0.02, 2 * fh + (c % 4) * fh, 0.012, 0.004, "blanc", verts=8)
    b.box(0, 0, h, long + 0.01, d + 0.01, 0.015, "beton_sombre")
    return b


def tour(k, x, y, r=0.0, etages=12, w=0.18, facade="beton", accent="bleu_loggia"):
    """Tour d'habitation (La Rose, Quartiers Nord)."""
    b = B(k, x, y, r)
    fh = 0.06; h = etages * fh
    b.box(0, 0, -0.1, w, w, h + 0.1, facade)
    for face in (-1, 1):
        for f in range(etages):
            for c in range(3):
                b.box(-w / 2 + (c + 0.5) * w / 3, face * (w / 2 + 0.003), f * fh + 0.02, w / 3 * 0.5, 0.006, fh * 0.45, "fenetre_sombre")
    b.box(w / 2 + 0.002, 0, 0, 0.006, 0.04, h, accent)
    b.box(0, 0, h, w + 0.01, w + 0.01, 0.015, "beton_sombre")
    return b


def dock(k, x, y, r=0.0, long=0.9, d=0.22, etages=3):
    """Les Docks de la Joliette : long entrepôt de pierre à fenêtres cintrées."""
    b = B(k, x, y, r)
    fh = 0.07; h = etages * fh
    b.box(0, 0, -0.1, long, d, h + 0.1, "pierre_quai")
    _windows(b, long, d, etages, fh, 0, int(long / 0.06))
    b.box(0, 0, h, long + 0.01, d + 0.01, 0.02, "tuile")
    return b


def grue(k, x, y, r=0.0, h=0.7, couleur="rouge"):
    """Grue portuaire (L'Estaque, Joliette)."""
    b = B(k, x, y, r)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box(sx * 0.06, sy * 0.06, 0, 0.018, 0.018, h * 0.55, couleur)
    b.box(0, 0, h * 0.55, 0.16, 0.16, 0.06, couleur)
    b.box(0, 0, h * 0.61, 0.06, 0.06, h * 0.32, couleur)
    b.box(0.18, 0, h * 0.9, 0.55, 0.03, 0.03, couleur)                # flèche
    b.box(-0.12, 0, h * 0.88, 0.12, 0.06, 0.05, "beton_sombre")       # contrepoids
    b.box(0.4, 0, h * 0.6, 0.004, 0.004, h * 0.3, "fer_noir")         # câble
    return b


def kiosque(k, x, y, r=0.0, couleur="store_vert"):
    """Kiosque (journaux, chichi-frégi, fleurs)."""
    b = B(k, x, y, r)
    b.cyl(0, 0, -0.02, 0.05, 0.09, "vert_nd", verts=8)
    b.cyl(0, 0, 0.07, 0.07, 0.035, couleur, verts=8, r2=0.01)
    return b


def etal(k, x, y, r=0.0, store="store_rouge", fruits=("rouge", "jaune", "herbe")):
    """Étal de marché (Noailles)."""
    b = B(k, x, y, r)
    b.box(0, 0, 0, 0.12, 0.06, 0.035, "bois")
    for i, m in enumerate(fruits):
        b.box(-0.035 + i * 0.035, 0, 0.035, 0.03, 0.05, 0.012, m)
    for sx in (-1, 1):
        b.box(sx * 0.055, 0.025, 0, 0.006, 0.006, 0.09, "fer_noir")
    b.box(0, 0.005, 0.09, 0.14, 0.08, 0.008, store)
    return b


def eglise(k, x, y, r=0.0, facade="creme"):
    """Église de village provençal (Plan-de-Cuques, Mazargues) avec clocher à campanile."""
    b = B(k, x, y, r)
    b.box(0, 0, -0.1, 0.36, 0.18, 0.26, facade)
    b.gable(0, 0, 0.16, 0.38, 0.2, 0.07, "tuile")
    b.box(-0.2, 0, -0.1, 0.1, 0.1, 0.42, facade)
    b.box(-0.2, 0, 0.32, 0.06, 0.06, 0.06, "fer_noir")   # campanile en fer forgé
    b.cyl(-0.2, 0, 0.38, 0.035, 0.05, "fer_noir", verts=6, r2=0.004)
    b.box(0.181, 0, 0, 0.006, 0.05, 0.09, "bois")
    return b


def olivier(k, x, y, s=1.0):
    b = B(k, x, y)
    b.cyl(0, 0, 0, 0.012 * s, 0.07 * s, "tronc", verts=5)
    b.ball(0, 0, 0.1 * s, 0.06 * s, "olivier", squash=0.7)
    return b


def platane(k, x, y, s=1.0):
    b = B(k, x, y)
    b.cyl(0, 0, 0, 0.014 * s, 0.12 * s, "platane_tronc", verts=5)
    b.ball(0, 0, 0.17 * s, 0.085 * s, "feuillage", squash=0.85)
    return b


mat("olivier", "#93a86a"); mat("platane_tronc", "#b7ab8f")
