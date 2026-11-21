"""Outils communs pour construire un arrondissement fait main sur l'île fidèle.

Chargement (en direct, MCP) :
    for f in ("lib.py", "batiments.py", "fastkit.py", "quartier.py"): exec(open(DIR + f).read())
Puis un script build_arrNN.py utilise Quartier(n).
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import json
import math
from pathlib import Path

import bmesh
import bpy
from pyproj import Transformer
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box as sbox, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

DIR_BL = Path(BLENDER_DIR)
OSM = DIR_BL / "osm"
U = 1 / 250
_D = json.loads((OSM / "marseille.json").read_text())
_t = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
_OX, _OY = _t.transform(_D["origin"][1], _D["origin"][0])


def ll(lat, lon):
    """(lat, lon) -> coordonnées île (unités Blender)."""
    x, y = _t.transform(lon, lat)
    return (x - _OX) * U, (y - _OY) * U


def _proj_line(geom):
    return LineString([ll(p["lat"], p["lon"]) for p in geom])


# demi-largeurs de rue (unités) par type OSM
# (rues à l'échelle réelle ; les bâtiments, eux, sont un peu exagérés : on serre les rues)
HALF = {"primary": 0.1, "secondary": 0.06, "tertiary": 0.04, "residential": 0.028, "living_street": 0.025,
        "pedestrian": 0.022, "unclassified": 0.028}


class Quartier:
    def __init__(self, n, larg=None):
        self.n = n
        self.larg = larg or {}  # demi-largeur imposée par nom de rue (ex. {"La Canebière": 0.12})
        # n = 1..16 : arrondissement ; n = 17 : Plan-de-Cuques (commune voisine, en bordure du 13e)
        g_arr = _D["plan_de_cuques"] if n == 17 else next(a["geom"] for a in _D["arrondissements"] if a["num"] == n)
        arr = affinity.scale(shape(g_arr), U, U, origin=(0, 0)).buffer(0)
        terre = affinity.scale(shape(_D["terre"]), U, U, origin=(0, 0)).buffer(0)
        self.poly = arr if n == 17 else arr.intersection(terre)  # pas de construction sur l'eau (bassins du port)
        self._set_zone()
        raw = json.loads((OSM / "raw" / ("rues_pdc.json" if n == 17 else f"rues_{n}.json")).read_text())["elements"]
        self.rues = []  # (nom, type, ligne)
        for w in raw:
            if not w.get("geometry") or w["tags"].get("area") == "yes": continue
            if w["tags"].get("tunnel") == "yes": continue
            if w["geometry"][0] == w["geometry"][-1] and w["tags"]["highway"] == "pedestrian": continue  # places
            self.rues.append((w["tags"].get("name", ""), w["tags"]["highway"], _proj_line(w["geometry"])))
        self.k = FastKit(f"arr{n:02d}")
        self.placed = []          # emprises posées
        self._grid = {}
        self._tree = None
        self.exclu = []           # zones réservées (monuments, places, marché…)
        big = [l.buffer(self.half(nm, t)) for nm, t, l in self.rues]
        for r, w in (("1", .2), ("2", .12)):
            big += [affinity.scale(shape(g), U, U, origin=(0, 0)).buffer(w) for g in _D["routes"].get(r, [])]
        self.voirie = unary_union(big)
        self._vtree = STRtree(list(getattr(self.voirie, "geoms", [self.voirie])))
        self.nb = 0

    def _set_zone(self):
        from shapely.prepared import prep
        self._in = prep(self.poly.buffer(-0.03))
        self._in2 = prep(self.poly.buffer(0.15))

    def half(self, nom, t):
        return self.larg.get(nom, HALF.get(t, .05))

    # ---------- zones et collisions
    def reserve(self, geom):
        self.exclu.append(geom)

    def libre(self, fp, marge=0.01):
        if not self._in.contains(fp): return False
        if any(e.intersects(fp) for e in self.exclu): return False
        if any(self._vtree.geometries[i].intersects(fp) for i in self._vtree.query(fp)): return False
        g = fp.buffer(marge)
        return not any(p.intersects(g) for p in self._near(fp))

    def _near(self, fp):
        # recherche grossière : on garde une grille par case de 1 unité
        cx, cy = int(fp.centroid.x // 1), int(fp.centroid.y // 1)
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                out += self._grid.get((cx + dx, cy + dy), [])
        return out

    def occupe(self, fp):
        self.placed.append(fp)
        c = (int(fp.centroid.x // 1), int(fp.centroid.y // 1))
        self._grid.setdefault(c, []).append(fp)

    @staticmethod
    def emprise(x, y, r, w, d):
        return Polygon(
            [(x + px * math.cos(r) - py * math.sin(r), y + px * math.sin(r) + py * math.cos(r))
             for px, py in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]])

    # ---------- rues fines dessinées
    def dessine_rues(self, m="pave", larg=None):
        """Désormais vide : build_routes.py dessine toute la voirie d'un seul tenant (même largeurs)."""
        return
        mat("pave", "#e9e2d2")
        zone = self.poly.buffer(0.05).difference(unary_union(self.exclu)) if self.exclu else self.poly.buffer(0.05)
        for nom, t, l in self.rues:
            if t in ("primary", "secondary"): continue  # déjà dessinées par build_fidele
            seg = l.intersection(zone)  # pas sur l'eau ni sur les monuments
            for s in getattr(seg, "geoms", [seg]):
                if s.geom_type == "LineString" and s.length > 0.05:
                    pts = list(s.segmentize(0.3).coords)
                    self.k.ribbon(pts, (larg or self.half(nom, t)) * 2, m)

    # ---------- bâtiments le long des rues
    def le_long(self, style, ordre=None, gap=0.008, recul=0.006):
        """style(nom, type, i) -> (fonction_batiment, w, d, kwargs) ou None. Façade tournée vers la rue."""
        rues = sorted(self.rues, key=ordre or (lambda r: -self.half(r[0], r[1])))
        for nom, t, l in rues:
            seg = l.intersection(self.poly)
            for s in getattr(seg, "geoms", [seg]):
                if s.geom_type != "LineString" or s.length < 0.15: continue
                for side in (1, -1):
                    pos, i = 0.05, 0
                    while pos < s.length - 0.05:
                        st = style(nom, t, i)
                        if st is None: break
                        fn, w0, d0, kw = st
                        if fn is None:          # trou volontaire (jardin, respiration)
                            pos += w0; i += 1
                            continue
                        ok = False
                        for f in (1.0, 0.8, 0.6):  # taille adaptative pour les petits îlots
                            w, d = w0 * f, d0 * f
                            p = s.interpolate(pos + w / 2); q = s.interpolate(min(s.length, pos + w / 2 + 0.02))
                            tx, ty = q.x - p.x, q.y - p.y
                            nn = math.hypot(tx, ty) or 1
                            nx, ny = -ty / nn, tx / nn
                            off = self.half(nom, t) + d / 2 + recul
                            cx, cy = p.x + side * nx * off, p.y + side * ny * off
                            r = math.atan2(-side * nx, side * ny)
                            fp = self.emprise(cx, cy, r, w, d)
                            if self.libre(fp):
                                kw2 = dict(kw)
                                if "w" in kw2: kw2["w"] = w
                                if "d" in kw2: kw2["d"] = d
                                fn(self.k, cx, cy, r, **kw2)
                                self.occupe(fp); self.nb += 1; i += 1
                                pos += w + gap; ok = True
                                break
                        if not ok:
                            pos += 0.04

    def remplit(self, style, pas=0.3):
        """Cœurs d'îlots : grille régulière, bâtiments bas, orientés comme la rue la plus proche."""
        x0, y0, x1, y1 = self.poly.bounds
        lignes = [r[2] for r in self.rues]
        arbre = STRtree(lignes)
        i = 0
        y = y0
        while y < y1:
            x = x0
            while x < x1:
                st = style(i)
                fn, w, d, kw = st
                if fn is None:
                    x += pas; i += 1
                    continue
                p = Point(x, y)
                if not self._in.contains(p):
                    x += pas; continue
                near = lignes[arbre.nearest(p)]
                a = near.project(p); q0 = near.interpolate(max(0, a - .02)); q1 = near.interpolate(a + .02)
                r = math.atan2(q1.y - q0.y, q1.x - q0.x)
                fp = self.emprise(x, y, r, w, d)
                if self.libre(fp, 0.02):
                    fn(self.k, x, y, r, **kw); self.occupe(fp); self.nb += 1; i += 1
                x += pas
            y += pas

    # ---------- nettoyage du tissu provisoire de build_fidele
    def efface_tissu(self):
        for name in ("tissu", "arbres"):
            o = bpy.data.objects.get(name)
            if not o: continue
            bm = bmesh.new(); bm.from_mesh(o.data)
            bm.verts.ensure_lookup_table()
            # un bâtiment = un cube isolé : on teste le centre de chaque île de faces
            kill = set()
            seen = set()
            for v in bm.verts:
                if v in seen: continue
                stack, comp = [v], []
                while stack:
                    a = stack.pop()
                    if a in seen: continue
                    seen.add(a); comp.append(a)
                    stack += [e.other_vert(a) for e in a.link_edges]
                cx = sum(c.co.x for c in comp) / len(comp); cy = sum(c.co.y for c in comp) / len(comp)
                if self._in2.contains(Point(cx, cy)): kill.update(comp)
            bmesh.ops.delete(bm, geom=list(kill), context="VERTS")
            bm.to_mesh(o.data); bm.free(); o.data.update()

    def fini(self):
        ob = self.k.done()
        print(f"arrondissement {self.n} : {self.nb} bâtiments")
        return ob


def reserve_monuments(q, marge=0.08):
    """Réserve l'emprise au sol (2D) de chaque monument fait main qui touche l'arrondissement."""
    from mathutils import Vector as V
    vp = bassin_vp().buffer(0.13)        # Vieux-Port : le bassin et ses quais, pas sa boîte englobante
    vp = vp.union(Point(*ll(43.2952, 5.3744)).buffer(0.3))   # ombrière
    if vp.intersects(q.poly): q.reserve(vp)
    for e in [o for o in bpy.data.objects if o.name.startswith("place_") and not o.name.startswith(("place_arr", "place_vieux_port"))]:
        for c in e.children_recursive:
            if c.type != "MESH": continue
            bb = [c.matrix_world @ V(v) for v in c.bound_box]
            g = sbox(min(p.x for p in bb), min(p.y for p in bb), max(p.x for p in bb), max(p.y for p in bb)).buffer(marge)
            if g.intersects(q.poly) and g.area < 30:
                q.reserve(g)


def bassin_vp():
    """Bassin du Vieux-Port = mer entre les quais (commune moins terre, autour du port)."""
    com = affinity.scale(shape(_D["commune"]), U, U, origin=(0, 0)).buffer(0)
    terre = affinity.scale(shape(_D["terre"]), U, U, origin=(0, 0)).buffer(0)
    x0, y0 = ll(43.2915, 5.3618); x1, y1 = ll(43.2975, 5.3752)
    eau = com.intersection(sbox(x0, y0, x1, y1)).difference(terre)
    return max(getattr(eau, "geoms", [eau]), key=lambda g_: g_.area)


def h(nom):
    """Décalage stable (indépendant de PYTHONHASHSEED) pour varier les couleurs par rue."""
    return sum(map(ord, nom))


def debug_svg(q, path, S=60):
    """Plan 2D de contrôle : arrondissement, voirie (gris), zones réservées (rouge), bâtiments (brique)."""
    import subprocess
    P = unary_union(q.placed) if q.placed else None
    x0, y0, x1, y1 = q.poly.buffer(0.5).bounds

    def pth(geom):
        out = []
        for gg in getattr(geom, "geoms", [geom]):
            if gg.is_empty: continue
            rings = [gg.exterior, *gg.interiors] if gg.geom_type == "Polygon" else [gg]
            for rg in rings:
                out.append("M" + " L".join(f"{(x - x0) * S:.1f},{(y1 - y) * S:.1f}" for x, y in rg.coords) + ("Z" if gg.geom_type == "Polygon" else ""))
        return " ".join(out)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{(x1 - x0) * S:.0f}" height="{(y1 - y0) * S:.0f}">'
           '<rect width="100%" height="100%" fill="#fff"/>',
           f'<path d="{pth(q.poly)}" fill="#f3e6c8" stroke="#000" stroke-width="2"/>',
           f'<path d="{pth(q.voirie.intersection(q.poly.buffer(0.3)))}" fill="#bbb" fill-rule="evenodd"/>']
    svg += [f'<path d="{pth(e)}" fill="none" stroke="red" stroke-width="2"/>' for e in q.exclu]
    if P is not None: svg.append(f'<path d="{pth(P)}" fill="#c8643c"/>')
    svg.append("</svg>")
    Path(path).write_text("\n".join(svg))
    subprocess.run(["magick", path, path.replace(".svg", ".png")])
