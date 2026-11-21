"""Outils communs pour les scripts de construction (à exec() après build_island.py)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

MATS = {m.name[2:]: m for m in bpy.data.materials if m.name.startswith("M_")}
COLS = {c.name: c for c in bpy.data.collections}


def mat(name, hexcol=None, rough=0.85, emit=0.0):
    """Récupère (ou crée) un matériau de la palette."""
    m = bpy.data.materials.get("M_" + name)
    if m is None:
        m = bpy.data.materials.new("M_" + name); m.use_nodes = True
    if hexcol:
        h = hexcol.lstrip('#'); c = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)] + [1]
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = c
        b.inputs["Roughness"].default_value = rough
        if emit:
            b.inputs["Emission Color"].default_value = c
            b.inputs["Emission Strength"].default_value = emit
        m.diffuse_color = c
    MATS[name] = m
    return m


def ground(x, y):
    ile = bpy.data.objects["Ile"]
    ok, loc, *_ = ile.ray_cast(Vector((x, y, 30)), Vector((0, 0, -1)))
    return loc.z if ok else 0.0


def clear_lot(lot):
    for o in [o for o in bpy.data.objects if o.get("lot") == lot]:
        bpy.data.objects.remove(o, do_unlink=True)


def _finish(o, mname, parent, col, lot):
    if mname: o.data.materials.append(MATS[mname])
    for c in o.users_collection: c.objects.unlink(o)
    COLS[col].objects.link(o)
    if parent is not None:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    o["lot"] = lot
    return o


def empty(name, loc, col="Monuments", lot="A"):
    o = bpy.data.objects.new(name, None); o.location = loc
    COLS[col].objects.link(o); o["lot"] = lot; o.empty_display_size = 0.3
    bpy.context.view_layer.update()  # sinon matrix_world reste à l'identité et les enfants se décalent
    return o


def box(name, loc, size, mname, parent=None, col="Monuments", lot="A", rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rot))
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, mname, parent, col, lot)


def cyl(name, loc, r, depth, mname, parent=None, col="Monuments", lot="A", verts=10, rot=(0, 0, 0), r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    return _finish(o, mname, parent, col, lot)


def blob(name, loc, r, mname, parent=None, col="Quartiers", lot="A", squash=1.0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (1, 1, squash)
    bpy.ops.object.transform_apply(scale=True)
    return _finish(o, mname, parent, col, lot)


def tree(name, x, y, s=1.0, parent=None, lot="A", z=None):
    z = ground(x, y) if z is None else z
    cyl(name + "_tronc", (x, y, z + 0.08 * s), 0.025 * s, 0.16 * s, "tronc", parent, "Quartiers", lot, verts=5)
    blob(name + "_feuilles", (x, y, z + 0.24 * s), 0.13 * s, random.choice(["herbe_fonce", "feuillage"]),
         parent, "Quartiers", lot, squash=1.15)


def palm(name, x, y, s=1.0, parent=None, lot="A", z=None):
    z = ground(x, y) if z is None else z
    cyl(name + "_tronc", (x, y, z + 0.17 * s), 0.018 * s, 0.34 * s, "tronc", parent, "Quartiers", lot, verts=5)
    for k in range(5):
        a = k * 2 * math.pi / 5
        o = box(name + f"_palme{k}", (x + math.cos(a) * 0.08 * s, y + math.sin(a) * 0.08 * s, z + 0.33 * s),
                (0.18 * s, 0.05 * s, 0.01 * s), "feuillage", parent, "Quartiers", lot, rot=a)
        o.rotation_euler[1] = 0.35


def ribbon(name, pts, width, mname, parent=None, col="Quartiers", lot="A", thick=0.04):
    """Bande (route, quai) qui suit une liste de points (x, y, z)."""
    bm = bmesh.new(); top, bot = [], []
    for i, p in enumerate(pts):
        p = Vector(p)
        a = Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])
        nrm = Vector((-a.y, a.x, 0)).normalized() * width / 2
        top += [bm.verts.new(p + nrm), bm.verts.new(p - nrm)]
        bot += [bm.verts.new(p + nrm - Vector((0, 0, thick))), bm.verts.new(p - nrm - Vector((0, 0, thick)))]
    for i in range(len(pts) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        bm.faces.new((top[a], top[b], top[c], top[d]))
        bm.faces.new((bot[d], bot[c], bot[b], bot[a]))
        bm.faces.new((top[a], top[d], bot[d], bot[a]))
        bm.faces.new((top[b], bot[b], bot[c], top[c]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return _finish(o, mname, parent, col, lot)


def remove(name):
    o = bpy.data.objects.get(name)
    if o: bpy.data.objects.remove(o, do_unlink=True)


# couleurs complémentaires
mat("tronc", "#8a5a3b"); mat("feuillage", "#5fb04a"); mat("pierre_quai", "#d8c9a8")
mat("miroir", "#dfe8ee", rough=0.05); mat("bois", "#b9825a"); mat("grillage", "#2f4f3a")
mat("synth", "#3fae5a"); mat("terre_battue", "#d98a4e"); mat("jaune", "#f4c430"); mat("bleu", "#2a6fdb")
