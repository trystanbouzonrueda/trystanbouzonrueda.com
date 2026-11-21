"""FastKit : même API que Kit (build_monuments.py), mais la géométrie s'accumule dans un bmesh
(aucun bpy.ops par pièce) -> des centaines de bâtiments en quelques secondes.

À charger après lib.py et batiments.py :
    exec(fastkit.py)  # remplace B par FB pour que batiments.py utilise FastKit
Un FastKit = un objet final « mh_<pid> » (multi-matériaux) sous l'empty « place_<pid> ».
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector


def _ile_ground(x, y):
    ile = bpy.data.objects.get("ile_sol")
    ok, loc, *_ = ile.ray_cast(Vector((x, y, 40)), Vector((0, 0, -1)))
    return loc.z if ok else 0.3


ground = _ile_ground  # le sol est désormais l'île fidèle


class FastKit:
    def __init__(self, pid, x=0.0, y=0.0, z=0.0, rot=0.0, col="Quartiers"):
        self.pid, self.rot, self.col = pid, rot, col
        old = bpy.data.objects.get("mh_" + pid)
        if old: bpy.data.objects.remove(old, do_unlink=True)
        e = bpy.data.objects.get("place_" + pid)
        if e is None:
            e = bpy.data.objects.new("place_" + pid, None); e.empty_display_size = 0.3
            bpy.data.collections[col].objects.link(e)
        e.location = (x, y, z); e.rotation_euler = (0, 0, 0); e.scale = (1, 1, 1)
        self.e, self.o = e, Vector((x, y, z))
        self.bm = bmesh.new(); self.mats = []
        self.bm_main = self.bm
        self.bm_det = bmesh.new()   # petits éléments (fenêtres, balcons, stores…) : affichés de près seulement
        old = bpy.data.objects.get("mh_" + pid + "_det")
        if old: bpy.data.objects.remove(old, do_unlink=True)

    # --- outils internes
    def _mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)

    def _w(self, lx, ly, lz):
        c, s = math.cos(self.rot), math.sin(self.rot)
        return Vector((lx * c - ly * s, lx * s + ly * c, lz))  # local à l'empty (pas de décalage o)

    def _tag(self, faces, m):
        i = self._mi(m)
        for f in faces: f.material_index = i

    def _faces_of(self, verts):
        return {f for v in verts for f in v.link_faces}

    # --- primitives (mêmes signatures que Kit, + rz explicite pour gable/hip)
    SEUIL = 0.013  # plus petite dimension en dessous de laquelle une pièce est un « détail »

    def _bm_for(self, petit):
        return self.bm_det if petit else self.bm_main

    def box(self, lx, ly, lz, sx, sy, sz, m, rz=0.0):
        M = Matrix.Translation(self._w(lx, ly, lz + sz / 2)) @ Matrix.Rotation(rz + self.rot, 4, "Z") @ Matrix.Diagonal((sx, sy, sz, 1))
        r = bmesh.ops.create_cube(self._bm_for(min(sx, sy, sz) < self.SEUIL), size=1, matrix=M)
        self._tag(self._faces_of(r["verts"]), m)

    def cyl(self, lx, ly, lz, r, h, m, verts=8, r2=None):
        M = Matrix.Translation(self._w(lx, ly, lz + h / 2)) @ Matrix.Rotation(self.rot, 4, "Z")
        res = bmesh.ops.create_cone(self._bm_for(r < 0.02), cap_ends=True, segments=verts, radius1=r,
                                    radius2=r if r2 is None else r2, depth=h, matrix=M)
        self._tag(self._faces_of(res["verts"]), m)

    def ball(self, lx, ly, lz, r, m, squash=1.0):
        M = Matrix.Translation(self._w(lx, ly, lz)) @ Matrix.Diagonal((1, 1, squash, 1))
        res = bmesh.ops.create_icosphere(self._bm_for(r < 0.02), subdivisions=1, radius=r, matrix=M)
        self._tag(self._faces_of(res["verts"]), m)

    def _poly(self, pts, faces, lx, ly, lz, rz, m):
        M = Matrix.Translation(self._w(lx, ly, lz)) @ Matrix.Rotation(rz + self.rot, 4, "Z")
        v = [self.bm.verts.new(M @ Vector(p)) for p in pts]
        fs = []
        for f in faces:
            try: fs.append(self.bm.faces.new([v[i] for i in f]))
            except ValueError: pass
        self._tag(fs, m)

    def gable(self, lx, ly, lz, sx, sy, h, m, rz=0.0):
        """Toit à deux pans, faîtage selon x (avant rotation rz)."""
        pts = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0), (-sx / 2, 0, h), (sx / 2, 0, h)]
        self._poly(pts, [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (3, 2, 1, 0)], lx, ly, lz, rz, m)

    def hip(self, lx, ly, lz, sx, sy, h, m, rz=0.0):
        rx = max(0.002, (sx - sy) / 2)
        pts = [(-sx / 2, -sy / 2, 0), (sx / 2, -sy / 2, 0), (sx / 2, sy / 2, 0), (-sx / 2, sy / 2, 0), (-rx, 0, h), (rx, 0, h)]
        self._poly(pts, [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (3, 2, 1, 0)], lx, ly, lz, rz, m)

    def ribbon(self, pts, width, m, dz=0.02, thick=0.02):
        """Bande plate qui suit des points (x, y) locaux, posée sur le sol (rues fines)."""
        P = [Vector((x, y, ground(self.o.x + x, self.o.y + y) - self.o.z + dz)) for x, y in pts]
        L, R = [], []
        for i, p in enumerate(P):
            a = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
            n = Vector((-a.y, a.x, 0)).normalized() * width / 2
            L.append(self.bm.verts.new(p + n)); R.append(self.bm.verts.new(p - n))
        fs = []
        for i in range(len(P) - 1):
            try: fs.append(self.bm.faces.new((L[i], R[i], R[i + 1], L[i + 1])))
            except ValueError: pass
        self._tag(fs, m)

    def _obj(self, bm, nom, detail):
        me = bpy.data.meshes.new(nom)
        bm.normal_update(); bm.to_mesh(me); bm.free()
        for m in self.mats: me.materials.append(MATS[m])
        ob = bpy.data.objects.new(nom, me)
        bpy.data.collections[self.col].objects.link(ob)
        ob.parent = self.e; ob["lot"] = "ARR"; ob["place"] = self.pid; ob["detail"] = detail
        return ob

    def done(self):
        ob = self._obj(self.bm_main, "mh_" + self.pid, False)
        n_det = len(self.bm_det.faces)
        if n_det:
            self._obj(self.bm_det, "mh_" + self.pid + "_det", True)
        else:
            self.bm_det.free()
        print(self.pid, "faces", len(ob.data.polygons), "+ détails", n_det)
        return ob


class FB(B):
    """Repère de bâtiment pour FastKit (toits sans retouche d'objet après coup)."""

    def gable(self, lx, ly, lz, sx, sy, h, m, along_y=False):
        x, y = self._p(lx, ly)
        self.k.gable(x, y, self.z + lz, sx, sy, h, m, rz=self.r + (math.pi / 2 if along_y else 0))

    def hip(self, lx, ly, lz, sx, sy, h, m):
        x, y = self._p(lx, ly)
        self.k.hip(x, y, self.z + lz, sx, sy, h, m, rz=self.r)


B = FB
