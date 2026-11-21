"""Monuments faits main, même direction artistique que l'île :
blocs francs, couleurs unies de la palette, aucune texture, silhouettes très lisibles.

exec(lib.py) puis exec(build_monuments.py). Relançable (lot="MH").
Chaque monument est construit en pièces puis fusionné en un seul objet sous son empty place_<id>.
"""
import bpy, math
from mathutils import Vector

mat("vert_nd", "#5f8a64"); mat("gris_dome", "#cfc8b8"); mat("pierre_sombre", "#9a8f80")
mat("fenetre_sombre", "#2f3a4a"); mat("or_vif", "#f5c542", rough=0.35)


def gmax(x, y, r):
    """Sol le plus haut sous une emprise de rayon r (pour ne rien enterrer)."""
    return max(ground(x + dx, y + dy) for dx in (-r, 0, r) for dy in (-r, 0, r))


def reset_place(pid, x, y, z):
    """Supprime l'ancien contenu fait main du lieu ; crée l'empty s'il n'existe pas (sans déplacer un empty existant)."""
    for o in [o for o in bpy.data.objects if o.get("lot") == "MH" and o.get("place") == pid]:
        bpy.data.objects.remove(o, do_unlink=True)
    e = bpy.data.objects.get("place_" + pid)
    if e is None or e.type != 'EMPTY':
        remove("place_" + pid)  # ancien bloc provisoire
        e = empty("place_" + pid, (x, y, z), lot="MH")
    return e


class Kit:
    """Petit outil d'assemblage : les pièces sont en coordonnées locales (origine = (x, y, sol))."""

    def __init__(self, pid, x, y, z=None, rot=0.0):
        self.pid = pid
        z = ground(x, y) if z is None else z
        self.e = reset_place(pid, x, y, z)
        self.o = Vector((x, y, z))
        self.rot = rot
        self.parts = []

    def _w(self, lx, ly, lz):
        c, s = math.cos(self.rot), math.sin(self.rot)
        return (self.o.x + lx * c - ly * s, self.o.y + lx * s + ly * c, self.o.z + lz)

    def _keep(self, ob, rotate=True):
        ob["place"] = self.pid
        if rotate:  # pièces dont l'origine est restée au centre (cylindres, toits)
            ob.rotation_euler[2] += self.rot
        self.parts.append(ob)
        return ob

    def box(self, lx, ly, lz, sx, sy, sz, m, rz=0.0):
        """Boîte posée : (lx, ly) centre, lz = bas de la boîte."""
        # lib.box fige position + rotation : on donne directement la rotation finale
        return self._keep(box("mh", self._w(lx, ly, lz + sz / 2), (sx, sy, sz), m, None, "Monuments", "MH", rot=rz + self.rot), rotate=False)

    def cyl(self, lx, ly, lz, r, h, m, verts=8, r2=None):
        return self._keep(cyl("mh", self._w(lx, ly, lz + h / 2), r, h, m, None, "Monuments", "MH", verts=verts, r2=r2))

    def ball(self, lx, ly, lz, r, m, squash=1.0):
        return self._keep(blob("mh", self._w(lx, ly, lz), r, m, None, "Monuments", "MH", squash=squash), rotate=False)

    def gable(self, lx, ly, lz, sx, sy, h, m):
        """Toit à deux pans (faîtage selon x)."""
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0),
                                       (-sx / 2, 0, h), (sx / 2, 0, h)]]
        for f in [(v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[0], v[4], v[3]), (v[1], v[2], v[5]), (v[3], v[2], v[1], v[0])]:
            bm.faces.new(f)
        me = bpy.data.meshes.new("mh"); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("mh", me); bpy.context.scene.collection.objects.link(ob)
        ob.location = self._w(lx, ly, lz)
        _finish(ob, m, None, "Monuments", "MH")
        return self._keep(ob)

    def stripes(self, lx, ly, lz, sx, sy, h, m1, m2, band=0.055):
        """Tour ou mur à bandes alternées (pierre blanche / verte de Notre-Dame, la Major…)."""
        n = max(1, round(h / band)); bh = h / n
        for i in range(n):
            self.box(lx, ly, lz + i * bh, sx, sy, bh, m1 if i % 2 == 0 else m2)

    def ring(self, a, b, lz, h, depth, n, m, seg=None, hfn=None, tilt=0.0):
        """Anneau elliptique de blocs (gradins, toit ondulé…). hfn(theta) -> hauteur en plus."""
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = a * math.cos(t), b * math.sin(t)
            L = seg or 2 * math.pi * math.sqrt((a * a + b * b) / 2) / n * 1.08
            zz = lz + (hfn(t) if hfn else 0)
            ob = self.box(x, y, zz, depth, L, h, m, rz=math.atan2(a * math.sin(t), b * math.cos(t)) * 0 + t)
            if tilt:
                ob.rotation_euler[1] = 0  # (inclinaison non utilisée : look tycoon droit)

    def dome(self, lx, ly, lz, r, h, m, verts=12):
        """Coupole facettée en 3 cônes empilés."""
        self.cyl(lx, ly, lz, r, h * 0.45, m, verts=verts, r2=r * 0.86)
        self.cyl(lx, ly, lz + h * 0.45, r * 0.86, h * 0.33, m, verts=verts, r2=r * 0.55)
        self.cyl(lx, ly, lz + h * 0.78, r * 0.55, h * 0.22, m, verts=verts, r2=r * 0.12)

    def columns(self, pts, lz, r, h, m):
        for (x, y) in pts:
            self.cyl(x, y, lz, r, h, m, verts=6)

    def done(self):
        """Fusionne toutes les pièces en un seul objet (rapide à afficher), rattaché à l'empty du lieu."""
        for ob in bpy.context.selected_objects: ob.select_set(False)
        for ob in self.parts: ob.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.join()
        j = bpy.context.active_object
        j.name = f"mh_{self.pid}"; j["lot"] = "MH"; j["place"] = self.pid
        bpy.context.view_layer.update()
        j.parent = self.e; j.matrix_parent_inverse = self.e.matrix_world.inverted()
        print(self.pid, "faces", len(j.data.polygons))
        return j


# ============================================================ Notre-Dame-de-la-Garde
def notre_dame():
    k = Kit("notre_dame", -2.6, 1.4, rot=-0.5)
    # rocher et terrasse fortifiée
    k.box(0, 0, -0.35, 1.25, 0.95, 0.42, "roche")
    k.box(0.1, -0.05, -0.35, 1.05, 1.1, 0.30, "roche_fonce", rz=0.25)
    k.box(0, 0, 0.05, 1.1, 0.8, 0.12, "pierre_quai")
    for sx in (-1, 1):  # créneaux
        for i in range(6):
            k.box(-0.5 + i * 0.2, sx * 0.39, 0.17, 0.08, 0.03, 0.05, "pierre_quai")
    base = 0.17
    # nef rayée + toit
    k.stripes(-0.15, 0, base, 0.62, 0.3, 0.28, "calcaire", "vert_nd")
    k.gable(-0.15, 0, base + 0.28, 0.66, 0.34, 0.12, "tuile")
    # coupole sur la croisée
    k.cyl(-0.33, 0, base + 0.28, 0.1, 0.1, "calcaire", verts=8)
    k.ball(-0.33, 0, base + 0.42, 0.1, "gris_dome", squash=0.9)
    k.cyl(-0.33, 0, base + 0.5, 0.012, 0.06, "or_vif", verts=6)
    # clocher rayé
    tx = 0.28
    k.stripes(tx, 0, base, 0.24, 0.24, 0.62, "calcaire", "vert_nd")
    for side in range(4):  # baies sombres
        a = side * math.pi / 2
        k.box(tx + math.cos(a) * 0.121, math.sin(a) * 0.121, base + 0.44, 0.06 if side % 2 == 0 else 0.012,
              0.012 if side % 2 == 0 else 0.06, 0.12, "fenetre_sombre")
    k.box(tx, 0, base + 0.62, 0.28, 0.28, 0.04, "calcaire")
    # lanterne octogonale + socle de la statue
    k.cyl(tx, 0, base + 0.66, 0.1, 0.12, "calcaire", verts=8)
    k.cyl(tx, 0, base + 0.78, 0.07, 0.08, "pierre_quai", verts=8)
    # la Bonne Mère dorée (robe, tête, couronne)
    k.cyl(tx, 0, base + 0.86, 0.05, 0.17, "or_vif", verts=8, r2=0.02)
    k.ball(tx, 0, base + 1.06, 0.03, "or_vif")
    k.cyl(tx, 0, base + 1.085, 0.022, 0.02, "or_vif", verts=6)
    # porche d'entrée
    k.box(tx + 0.17, 0, base, 0.1, 0.16, 0.16, "calcaire")
    k.box(tx + 0.22, 0, base, 0.012, 0.07, 0.11, "fenetre_sombre")
    return k.done()




mat("verre", "#4f86a8", rough=0.2); mat("beton", "#d8d4cb"); mat("beton_sombre", "#5b5f66"); mat("ardoise", "#5b6270")
mat("cypres", "#2f5e3a"); mat("rouge_loggia", "#d9483b"); mat("jaune_loggia", "#f2c14e"); mat("bleu_loggia", "#3f7fd1")


# ============================================================ Orange Vélodrome
def velodrome():
    x, y = 2.6, -3.4
    k = Kit("velodrome", x, y, z=gmax(x, y, 1.0) - 0.02, rot=0.3)
    a, b = 1.12, 0.88
    base = k.cyl(0, 0, -0.25, 1.0, 0.3, "pierre_quai", verts=28); base.scale = (a + 0.08, b + 0.08, 1)
    pitch = k.cyl(0, 0, 0.05, 1.0, 0.02, "synth", verts=24); pitch.scale = (0.6, 0.4, 1)
    k.box(0, 0, 0.07, 0.008, 0.78, 0.004, "blanc")
    k.cyl(0, 0, 0.07, 0.08, 0.004, "blanc", verts=16)
    for s in (-1, 1):  # buts
        k.box(s * 0.58, 0, 0.07, 0.01, 0.1, 0.035, "blanc")
    # gradins bleu ciel et blancs, en escalier
    k.ring(0.74, 0.54, 0.05, 0.06, 0.14, 30, "bleu_om")
    k.ring(0.86, 0.66, 0.05, 0.13, 0.12, 32, "blanc")
    k.ring(0.97, 0.76, 0.05, 0.21, 0.12, 34, "bleu_om")
    k.ring(1.07, 0.85, 0.05, 0.27, 0.06, 36, "calcaire")
    # le toit blanc ondulé, signature du stade
    k.ring(0.97, 0.77, 0.34, 0.035, 0.36, 44, "blanc", hfn=lambda t: 0.06 * math.sin(4 * t) + 0.04 * abs(math.sin(2 * t)))
    for i in range(10):  # poteaux
        t = 2 * math.pi * i / 10
        k.cyl(1.1 * math.cos(t), 0.87 * math.sin(t), 0.05, 0.012, 0.32, "blanc", verts=5)
    return k.done()


# ============================================================ Mucem + fort Saint-Jean
def mucem():
    x, y = -4.75, 7.15
    k = Kit("mucem", x, y, z=gmax(x, y, 0.3), rot=0.0)
    s, h = 0.5, 0.42
    k.box(0, 0, 0, s - 0.04, s - 0.04, h, "verre")
    for side in range(4):  # résille de béton (dentelle) sur les 4 faces
        a = side * math.pi / 2
        nx, ny = round(math.cos(a)), round(math.sin(a))
        for i in range(6):
            off = -0.22 + i * 0.088
            k.box(nx * s / 2 + ny * off, ny * s / 2 + nx * off, 0, 0.014 if nx else 0.02, 0.02 if nx else 0.014, h, "beton_sombre")
        for j in range(5):
            k.box(nx * s / 2, ny * s / 2, 0.04 + j * 0.085, 0.014 if nx else s, s if nx else 0.014, 0.014, "beton_sombre")
    k.box(0, 0, h, s + 0.02, s + 0.02, 0.025, "beton_sombre")
    for i in range(5):  # toit en résille
        k.box(-0.2 + i * 0.1, 0, h + 0.025, 0.012, s, 0.01, "beton")
    # passerelle vers le fort
    fx, fy = 0.38, -0.72
    fz = ground(x + fx, y + fy) - k.o.z
    k.box(fx / 2, fy / 2, h - 0.06, 0.05, math.hypot(fx, fy) - 0.25, 0.025, "beton", rz=math.atan2(-fx, fy))
    # fort Saint-Jean
    k.box(fx, fy, fz, 0.58, 0.46, 0.15, "pierre_quai")
    for i in range(7):
        for sy in (-1, 1):
            k.box(fx - 0.27 + i * 0.09, fy + sy * 0.22, fz + 0.15, 0.04, 0.03, 0.04, "pierre_quai")
    k.box(fx + 0.2, fy - 0.12, fz, 0.15, 0.15, 0.4, "sable")          # tour du Fanal (carrée)
    k.box(fx + 0.2, fy - 0.12, fz + 0.4, 0.17, 0.17, 0.03, "sable")
    k.cyl(fx - 0.22, fy + 0.1, fz, 0.1, 0.3, "pierre_quai", verts=10)  # tour du roi René (ronde)
    k.cyl(fx - 0.22, fy + 0.1, fz + 0.3, 0.11, 0.035, "pierre_quai", verts=10)
    return k.done()


# ============================================================ La Major
def major():
    x, y = -3.0, 7.85
    k = Kit("major", x, y, z=gmax(x, y, 0.4), rot=0.15)
    k.box(0, 0, -0.1, 0.86, 0.5, 0.1, "pierre_quai")
    k.stripes(0, 0, 0, 0.66, 0.24, 0.22, "calcaire", "vert_nd")
    k.stripes(0.08, 0, 0, 0.22, 0.44, 0.22, "calcaire", "vert_nd")
    k.box(0, 0, 0.22, 0.68, 0.26, 0.025, "calcaire")
    # grande coupole rayée
    k.stripes(0.08, 0, 0.22, 0.17, 0.17, 0.09, "calcaire", "vert_nd", band=0.03)
    k.dome(0.08, 0, 0.31, 0.12, 0.16, "vert_nd", verts=10)
    k.cyl(0.08, 0, 0.46, 0.012, 0.06, "or_vif", verts=6)
    for dx in (-0.12, -0.24):  # petites coupoles de la nef
        k.dome(dx, 0, 0.245, 0.065, 0.08, "vert_nd", verts=8)
    # deux tours de façade
    for sy in (-1, 1):
        k.stripes(-0.37, sy * 0.1, 0, 0.11, 0.11, 0.36, "calcaire", "vert_nd")
        k.dome(-0.37, sy * 0.1, 0.36, 0.06, 0.08, "vert_nd", verts=8)
    k.cyl(0.36, 0, 0, 0.12, 0.2, "calcaire", verts=10)  # abside
    k.dome(0.36, 0, 0.2, 0.12, 0.09, "vert_nd", verts=10)
    return k.done()


# ============================================================ Le Dôme
def dome():
    x, y = 5.2, 4.2
    k = Kit("dome", x, y, z=gmax(x, y, 0.5) - 0.02)
    k.cyl(0, 0, 0, 0.56, 0.04, "beton", verts=20)
    k.cyl(0, 0, 0.04, 0.5, 0.07, "verre", verts=20)
    k.dome(0, 0, 0.11, 0.53, 0.34, "blanc", verts=20)
    for i in range(10):  # nervures
        t = 2 * math.pi * i / 10
        k.box(0.5 * math.cos(t), 0.5 * math.sin(t), 0.04, 0.03, 0.03, 0.12, "beton", rz=t)
    k.box(0, -0.55, 0, 0.3, 0.1, 0.09, "verre")  # entrée vitrée
    k.box(0, -0.55, 0.09, 0.32, 0.12, 0.015, "beton")
    return k.done()


# ============================================================ Le David (rond-point du Prado)
def david():
    k = Kit("david", -4.6, -5.6)
    k.cyl(0, 0, 0, 0.3, 0.03, "herbe", verts=16)
    k.cyl(0, 0, 0.03, 0.31, 0.012, "calcaire", verts=16)
    k.box(0, 0, 0.03, 0.1, 0.1, 0.26, "blanc")
    k.box(0, 0, 0.29, 0.12, 0.12, 0.02, "blanc")
    z = 0.31  # la statue, bien lisible : jambes, bassin, torse, tête, bras levé
    k.box(-0.016, 0, z, 0.022, 0.024, 0.15, "blanc")
    k.box(0.018, 0.006, z, 0.022, 0.024, 0.14, "blanc")
    k.box(0, 0, z + 0.14, 0.06, 0.035, 0.04, "blanc")
    k.box(0, 0, z + 0.18, 0.07, 0.04, 0.1, "blanc")
    k.ball(0, 0, z + 0.31, 0.026, "blanc")
    k.box(-0.048, 0, z + 0.13, 0.018, 0.02, 0.13, "blanc")      # bras le long du corps
    k.box(0.045, 0, z + 0.22, 0.018, 0.02, 0.1, "blanc")        # bras replié vers l'épaule
    return k.done()


# ============================================================ Château Borély (dans le parc)
def borely():
    x, y = -2.95, -5.62
    k = Kit("borely", x, y, z=gmax(x, y, 0.25))
    k.box(0, 0, 0, 0.5, 0.18, 0.17, "creme")
    k.gable(0, 0, 0.17, 0.52, 0.2, 0.07, "ardoise")
    for sx in (-1, 1):  # pavillons d'angle
        k.box(sx * 0.27, 0, 0, 0.12, 0.24, 0.2, "creme")
        k.cyl(sx * 0.27, 0, 0.2, 0.11, 0.07, "ardoise", verts=4, r2=0.01)
    k.box(0, -0.1, 0, 0.14, 0.04, 0.2, "creme")                 # avant-corps central
    k.gable(0, -0.1, 0.2, 0.16, 0.06, 0.04, "creme")
    for fl in (0.04, 0.11):
        for i in range(8):
            if abs(-0.21 + i * 0.06) < 0.07: continue
            k.box(-0.21 + i * 0.06, -0.092, fl, 0.025, 0.006, 0.04, "fenetre_sombre")
    k.box(0, -0.2, 0, 0.12, 0.08, 0.02, "calcaire")             # perron
    return k.done()


# ============================================================ Palais Longchamp
def longchamp():
    x, y = 6.0, 6.4
    k = Kit("longchamp", x, y, z=gmax(x, y, 0.6), rot=math.pi + 0.5)
    k.box(0, 0.05, -0.08, 1.4, 0.8, 0.1, "pierre_quai")
    # château d'eau central : arc, groupe sculpté doré, cascade
    k.box(0, 0.25, 0, 0.3, 0.2, 0.3, "creme")
    k.box(0, 0.14, 0.05, 0.12, 0.02, 0.18, "fenetre_sombre")
    k.cyl(0, 0.25, 0.3, 0.07, 0.12, "or_vif", verts=8, r2=0.03)
    for i in range(4):  # cascade en marches
        k.box(0, 0.08 - i * 0.08, 0.15 - i * 0.045, 0.16 + i * 0.03, 0.08, 0.02, "mer")
    k.cyl(0, -0.3, 0.0, 0.17, 0.03, "mer", verts=14)
    k.cyl(0, -0.3, 0.0, 0.19, 0.02, "calcaire", verts=14)
    # deux ailes à colonnade courbe jusqu'aux musées
    for sx in (-1, 1):
        pts = []
        for i in range(8):
            t = i / 7
            pts.append((sx * (0.17 + 0.48 * math.sin(t * math.pi / 2)), 0.25 - 0.5 * (1 - math.cos(t * math.pi / 2))))
        k.columns(pts, 0, 0.014, 0.17, "calcaire")
        for (ax, ay), (bx_, by_) in zip(pts, pts[1:]):
            k.box((ax + bx_) / 2, (ay + by_) / 2, 0.17, 0.09, math.hypot(bx_ - ax, by_ - ay) + 0.02, 0.025, "creme",
                  rz=math.atan2(bx_ - ax, -(by_ - ay)) * -1)
        ex, ey = pts[-1]
        k.box(ex + sx * 0.08, ey - 0.06, 0, 0.26, 0.24, 0.22, "creme")     # musées
        k.gable(ex + sx * 0.08, ey - 0.06, 0.22, 0.28, 0.26, 0.07, "tuile")
    return k.done()


# ============================================================ Tour CMA CGM
def cma_cgm():
    x, y = -1.6, 8.6
    k = Kit("cma_cgm", x, y, rot=0.6)
    k.box(0, 0, 0, 0.42, 0.34, 0.05, "beton")
    k.box(-0.04, 0, 0.05, 0.22, 0.24, 1.45, "verre")
    c = k.cyl(0.07, 0, 0.05, 0.14, 1.3, "verre", verts=12); c.scale = (1, 0.8, 1)
    for sy in (-1, 1):  # fines lames blanches verticales
        k.box(-0.04, sy * 0.122, 0.05, 0.22, 0.012, 1.47, "blanc")
    k.box(-0.15, 0, 0.05, 0.012, 0.25, 1.5, "blanc")
    k.box(-0.04, 0, 1.5, 0.24, 0.26, 0.03, "blanc")
    return k.done()


# ============================================================ Gare Saint-Charles + grand escalier
def gare():
    x, y = 1.6, 6.5
    k = Kit("gare", x, y, z=gmax(x, y, 0.6), rot=0.0)
    k.box(0, 0.1, 0, 1.2, 0.6, 0.16, "pierre_quai")               # parvis surélevé
    k.box(0, 0.22, 0.16, 1.0, 0.34, 0.2, "sable")                  # halle
    for i in range(9):
        k.box(-0.4 + i * 0.1, 0.05, 0.2, 0.05, 0.006, 0.1, "fenetre_sombre")
    roof = k.cyl(0, 0.22, 0.29, 0.17, 0.98, "verre", verts=12); roof.rotation_euler[1] = math.pi / 2  # verrière en arc
    k.box(0, 0.04, 0.16, 0.36, 0.06, 0.3, "creme")                 # façade centrale
    k.cyl(0, 0.008, 0.38, 0.035, 0.01, "blanc", verts=12).rotation_euler[0] = math.pi / 2  # horloge
    # le grand escalier qui descend vers le boulevard
    for i in range(7):
        k.box(0, -0.22 - i * 0.07, 0.16 - (i + 1) * 0.023, 0.36 - i * 0.0, 0.07, 0.023, "calcaire")
    for sx in (-1, 1):
        k.box(sx * 0.2, -0.43, 0, 0.04, 0.5, 0.06, "calcaire")
        k.box(sx * 0.2, -0.24, 0.06, 0.06, 0.06, 0.05, "calcaire")
        k.ball(sx * 0.2, -0.24, 0.15, 0.03, "blanc")               # statues
        k.box(sx * 0.2, -0.64, 0.06, 0.06, 0.06, 0.05, "calcaire")
        k.ball(sx * 0.2, -0.64, 0.15, 0.03, "blanc")
    return k.done()


# ============================================================ Cité Radieuse
def cite_radieuse():
    x, y = 4.9, -4.9
    k = Kit("cite_radieuse", x, y, z=gmax(x, y, 0.6), rot=0.3)
    for i in range(7):  # pilotis
        for sy in (-1, 1):
            k.cyl(-0.54 + i * 0.18, sy * 0.07, 0, 0.028, 0.13, "beton", verts=6, r2=0.04)
    k.box(0, 0, 0.13, 1.25, 0.26, 0.46, "beton")
    random.seed(4)
    cols = ["rouge_loggia", "jaune_loggia", "bleu_loggia", "herbe", "beton"]
    for sy in (-1, 1):  # loggias colorées
        for r in range(6):
            for c in range(15):
                k.box(-0.56 + c * 0.08, sy * 0.132, 0.16 + r * 0.07, 0.05, 0.006, 0.04, random.choice(cols))
    k.box(0, 0, 0.59, 1.2, 0.22, 0.02, "beton")                    # toit-terrasse
    k.cyl(0.35, 0, 0.61, 0.06, 0.12, "beton", verts=8, r2=0.035)   # cheminée-sculpture
    k.box(-0.3, 0, 0.61, 0.16, 0.12, 0.07, "beton")
    return k.done()


# ============================================================ Château d'If (îlot)
def chateau_if():
    k = Kit("chateau_if", -13.0, -3.2, z=-0.3)
    k.box(0, 0, 0, 0.62, 0.62, 0.17, "pierre_quai")
    k.box(0, 0, 0.17, 0.28, 0.28, 0.17, "sable")
    for (cx, cy) in ((-0.31, -0.31), (0.31, -0.31), (-0.31, 0.31)):
        k.cyl(cx, cy, 0, 0.11, 0.28, "pierre_quai", verts=10)
        k.cyl(cx, cy, 0.28, 0.12, 0.03, "pierre_quai", verts=10)
    for i in range(6):
        for (sx, sy) in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            o = -0.25 + i * 0.1
            k.box(sx * 0.3 + (o if sy else 0), sy * 0.3 + (o if sx else 0), 0.17, 0.04, 0.04, 0.04, "pierre_quai")
    return k.done()


# ============================================================ Bateaux : navette du Frioul + pointus
def navette():
    k = Kit("navette", -7.2, 4.4, z=-0.1, rot=0.2)
    k.box(-0.02, 0, 0, 0.44, 0.16, 0.07, "bleu")
    k.box(0.2, 0, 0, 0.11, 0.11, 0.07, "bleu", rz=math.pi / 4)     # proue pointue
    k.box(-0.04, 0, 0.07, 0.3, 0.14, 0.07, "blanc")
    k.box(-0.04, 0, 0.1, 0.305, 0.145, 0.025, "fenetre_sombre")
    k.box(-0.08, 0, 0.14, 0.16, 0.11, 0.05, "blanc")
    k.box(-0.08, 0, 0.19, 0.17, 0.12, 0.01, "bleu")
    return k.done()


def pointus():
    k = Kit("vieux_port", -2.5, 4.75, z=-0.08)
    random.seed(12)
    spots = [(1.25, -0.4, 1.57), (1.25, 0.4, 1.57), (-1.0, -0.25, 0.1), (-0.4, 0.3, -0.2), (0.3, -0.1, 0.3)]
    for (px, py, r) in spots:
        c, s = math.cos(r), math.sin(r)
        col = random.choice(["rouge", "bleu", "jaune", "bleu_om"])
        k.box(px, py, 0, 0.13, 0.055, 0.03, col, rz=r)
        for d in (1, -1):  # pointes avant/arrière
            k.box(px + d * 0.065 * c, py + d * 0.065 * s, 0, 0.04, 0.04, 0.03, col, rz=r + math.pi / 4)
        k.box(px, py, 0.03, 0.15, 0.045, 0.008, "blanc", rz=r)
        k.box(px - 0.02 * c, py - 0.02 * s, 0.038, 0.04, 0.035, 0.025, "bois", rz=r)
    return k.done()


# ============================================================ Cabanons des Calanques
def cabanons():
    k = Kit("calanques", 0.2, -7.6)
    for (cx, cy, r) in ((-1.8, 0.1, 0.2), (1.7, -0.2, -0.4), (-0.6, 0.4, 1.2), (0.6, -0.1, 0.4)):
        z = ground(k.o.x + cx, k.o.y + cy) - k.o.z
        c, s = math.cos(r), math.sin(r)
        k.box(cx, cy, z - 0.02, 0.15, 0.11, 0.1, "blanc", rz=r)
        g = k.gable(cx, cy, z + 0.08, 0.17, 0.13, 0.05, "tuile"); g.rotation_euler[2] += r
        k.box(cx - 0.056 * s, cy + 0.056 * c, z, 0.035, 0.006, 0.06, "bleu", rz=r)
    return k.done()


# ============================================================ Palmiers de la Corniche
def palmiers():
    def coast(y): return -5.2 + 1.0 * math.sin(y * 0.45) + (0.0 if y > -6 else (y + 6) * 0.35)
    k = Kit("corniche", -4.0, -1.5, z=0.0)
    random.seed(3)
    yy = 2.4
    while yy > -6.0:
        px = coast(yy) + 0.7; z = max(ground(px, yy), 0.3)
        lx, ly, lz = px - k.o.x, yy - k.o.y, z - k.o.z
        for i in range(3):  # tronc légèrement penché, en 3 tronçons
            k.cyl(lx + i * 0.008, ly, lz + i * 0.1, 0.017 - i * 0.003, 0.1, "tronc", verts=6)
        top = lz + 0.3
        r0 = random.uniform(0, 1)
        for j in range(7):  # palmes en étoile, deux étages
            t = r0 + j * 2 * math.pi / 7
            k.box(lx + 0.024 + math.cos(t) * 0.07, ly + math.sin(t) * 0.07, top, 0.14, 0.035, 0.01, "feuillage", rz=t)
            k.box(lx + 0.024 + math.cos(t + 0.45) * 0.11, ly + math.sin(t + 0.45) * 0.11, top - 0.035, 0.1, 0.03, 0.01, "herbe_fonce", rz=t + 0.45)
        k.ball(lx + 0.024, ly, top + 0.005, 0.02, "tronc")
        yy -= 0.75
    return k.done()


# ---------------------------------------------------------------- tout reconstruire
for o in [o for o in bpy.data.objects if o.name.startswith(("meshy_", "gen_"))]:
    bpy.data.objects.remove(o, do_unlink=True)
for fn in (notre_dame, velodrome, mucem, major, dome, david, borely, longchamp, cma_cgm, gare,
           cite_radieuse, chateau_if, navette, pointus, cabanons, palmiers):
    fn()
print("monuments faits main ok")
