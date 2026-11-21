"""Construit l'île flottante de Marseille (blockout) dans Blender.

Lancer dans Blender : exec(open("<chemin>/build_island.py").read())
Repart d'une scène vide à chaque fois.
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

random.seed(7)

# ---------- reset
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
scene = bpy.context.scene
cols = {}
for n in ["Terrain", "Mer", "Monuments", "Quartiers", "Vie", "Lumieres", "Ilots"]:
    c = bpy.data.collections.new(n); scene.collection.children.link(c); cols[n] = c

# ---------- palette (couleurs unies, partagées)
PAL = {
    "herbe": "#7cc456", "herbe_fonce": "#4f9a3c", "roche": "#c9b79c", "roche_fonce": "#8a7864",
    "calcaire": "#efe9dc", "sable": "#f1dca0", "mer": "#2fb6d8", "mer_fond": "#1a7fa8", "cascade": "#bfefff",
    "route": "#5d6168", "creme": "#f3e3c3", "tuile": "#d9714a", "blanc": "#f7f7f2", "or": "#f2c14e",
    "bleu_om": "#2aa7e0", "rouge": "#e2483d", "vert_city": "#3fae5a",
}
def hex2rgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x ** 2.2 for x in c] + [1]
MATS = {}
for k, v in PAL.items():
    m = bpy.data.materials.get("M_" + k) or bpy.data.materials.new("M_" + k)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = hex2rgb(v)
    b.inputs["Roughness"].default_value = 0.15 if k == "mer" else 0.85
    m.diffuse_color = hex2rgb(v)
    MATS[k] = m

# ---------- géographie
def R(t): return 10 + 0.7 * math.sin(3 * t + 0.4) + 0.45 * math.sin(5 * t + 1.3) + 0.25 * math.sin(9 * t)
def inside(x, y): return math.hypot(x, y) <= R(math.atan2(y, x))
def is_sea(x, y):
    coast = -5.2 + 1.0 * math.sin(y * 0.45) + (0.0 if y > -6 else (y + 6) * 0.35)
    return x < coast or (3.5 < y < 6.0 and x < -1.0)  # côte ouest + Vieux-Port
def gauss(x, y, cx, cy, s, h): return h * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s * s))
def height(x, y):
    if is_sea(x, y): return -0.55
    h = 0.25 + 0.12 * noise.noise(Vector((x * 0.3, y * 0.3, 0.5)))
    h += gauss(x, y, -2.6, 1.4, 1.5, 2.6)  # colline Notre-Dame
    h += max(0, (-y - 6.8)) * 0.9 * (0.7 + 0.3 * noise.noise(Vector((x * 0.6, y * 0.6, 2))))  # calanques
    h += gauss(x, y, 6.5, 4.5, 2.2, 0.6)  # collines est
    return h

STEP, N, WL = 0.5, 44, -0.08

# ---------- dessus de l'île + socle rocheux
bm = bmesh.new(); verts = {}
for i in range(N):
    for j in range(N):
        cx = -11 + (i + .5) * STEP; cy = -11 + (j + .5) * STEP
        if not inside(cx, cy): continue
        quad = []
        for a, b in [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]:
            if (a, b) not in verts:
                jx = (random.random() - .5) * .15; jy = (random.random() - .5) * .15
                verts[a, b] = bm.verts.new((-11 + a * STEP + jx, -11 + b * STEP + jy, 0))
            quad.append(verts[a, b])
        bm.faces.new(quad)
for v in bm.verts: v.co.z = height(v.co.x, v.co.y)
me = bpy.data.meshes.new("ile_dessus")
for k in ["herbe", "herbe_fonce", "roche", "calcaire", "sable", "roche_fonce"]: me.materials.append(MATS[k])
for f in bm.faces:
    c = f.calc_center_median()
    sea = all(is_sea(v.co.x, v.co.y) for v in f.verts)
    anysea = any(is_sea(v.co.x, v.co.y) for v in f.verts)
    if sea: f.material_index = 4
    elif anysea: f.material_index = 3 if c.y < -6 else 4
    elif c.y < -6.5 and c.z > 0.8: f.material_index = 3
    elif c.z > 1.6: f.material_index = 2
    else: f.material_index = 0
boundary = [e for e in bm.edges if e.is_boundary]
loop = [boundary[0].verts[0]]; used = {boundary[0]}; cur = boundary[0].verts[1]
while cur != loop[0]:
    loop.append(cur)
    nxt = [e for e in cur.link_edges if e.is_boundary and e not in used]
    if not nxt: break
    used.add(nxt[0]); cur = nxt[0].other_vert(cur)
def snap_to_outline(v, k=1.0):
    a = math.atan2(v.co.y, v.co.x); r = R(a) * k
    v.co.x, v.co.y = math.cos(a) * r, math.sin(a) * r
for v in loop:  # bord lisse au lieu d'escaliers
    snap_to_outline(v)
    v.co.z = height(v.co.x, v.co.y)
rings = [loop]
for d, s in zip([1.0, 2.6, 4.6, 6.8, 8.8], [0.98, 0.88, 0.66, 0.40, 0.17]):
    ring = []
    for v in loop:
        a = math.atan2(v.co.y, v.co.x); r = math.hypot(v.co.x, v.co.y) * s
        r *= 1 + 0.12 * noise.noise(Vector((math.cos(a) * 2, math.sin(a) * 2, d)))
        ring.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, -d - 0.6 * random.random())))
    rings.append(ring)
n = len(loop)
for k in range(len(rings) - 1):
    A, B = rings[k], rings[k + 1]
    for i in range(n):
        f = bm.faces.new((A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]))
        f.material_index = random.choice((2, 5)) if k >= 2 else 2
tip = bm.verts.new((0.4, -0.3, -11.5))
for i in range(n):
    bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], tip)).material_index = 5
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
ile = bpy.data.objects.new("Ile", me); cols["Terrain"].objects.link(ile)

# ---------- mer + cascade
bm = bmesh.new(); V = {}
def gv(i, j):
    if (i, j) not in V: V[i, j] = bm.verts.new((-11 + i * STEP, -11 + j * STEP, WL))
    return V[i, j]
for i in range(N):
    for j in range(N):
        cx = -11 + (i + .5) * STEP; cy = -11 + (j + .5) * STEP
        if inside(cx, cy) and (is_sea(cx, cy) or is_sea(cx - .4, cy)):
            bm.faces.new([gv(i, j), gv(i + 1, j), gv(i + 1, j + 1), gv(i, j + 1)])
outer = []
for e in [e for e in bm.edges if e.is_boundary]:
    m = (e.verts[0].co + e.verts[1].co) / 2
    if math.hypot(m.x, m.y) > R(math.atan2(m.y, m.x)) - 0.8: outer.append(e)
for v in {v for e in outer for v in e.verts}:
    snap_to_outline(v, 1.0)
newv = {}; casc = []
def drop(v, k):
    if (v, k) in newv: return newv[v, k]
    d = Vector((v.co.x, v.co.y, 0)).normalized(); t = k / 6
    newv[v, k] = bm.verts.new(v.co + d * (0.6 * t + 0.9 * t * t) + Vector((0, 0, -7.5 * t)))
    return newv[v, k]
for e in outer:
    a, b = e.verts; prev = (a, b)
    for k in range(1, 7):
        na, nb = drop(a, k), drop(b, k)
        casc.append(bm.faces.new((prev[1], prev[0], na, nb))); prev = (na, nb)
me = bpy.data.meshes.new("mer"); me.materials.append(MATS["mer"]); me.materials.append(MATS["cascade"])
cs = set(casc)
for f in bm.faces: f.material_index = 1 if f in cs else 0
bm.to_mesh(me); bm.free()
cols["Mer"].objects.link(bpy.data.objects.new("Mer", me))

# ---------- emplacements des lieux (blockout)
def ground(x, y):
    ok, loc, *_ = ile.ray_cast(Vector((x, y, 20)), Vector((0, 0, -1)))
    return loc.z if ok else 0
PLACES = {  # id: (x, y, sx, sy, sz, matériau)
    "vieux_port": (-0.6, 4.7, 1.0, 1.6, 0.3, "blanc"),
    "notre_dame": (-2.6, 1.4, 0.6, 0.6, 1.4, "or"),
    "corniche": (-4.3, -2.2, 0.5, 3.0, 0.15, "route"),
    "david": (-4.6, -5.6, 0.3, 0.3, 0.8, "calcaire"),
    "borely": (-2.4, -6.0, 1.8, 1.2, 0.2, "herbe_fonce"),
    "velodrome": (2.6, -3.4, 2.2, 1.6, 0.8, "blanc"),
    "city_jul": (0.9, 1.0, 0.8, 0.5, 0.15, "vert_city"),
    "mucem": (-4.9, 6.4, 0.8, 0.8, 0.5, "roche_fonce"),
    "major": (-3.4, 7.7, 1.0, 0.6, 0.9, "creme"),
    "dome": (5.2, 4.2, 0.9, 0.9, 0.6, "blanc"),
    "calanques": (0.5, -8.6, 1.2, 0.6, 0.3, "calcaire"),
}
def to_col(o, col):
    for c in o.users_collection: c.objects.unlink(o)
    cols[col].objects.link(o)
for pid, (x, y, sx, sy, sz, mat) in PLACES.items():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, ground(x, y) + sz / 2))
    o = bpy.context.active_object; o.name = "place_" + pid; o.scale = (sx, sy, sz)
    o.data.materials.append(MATS[mat]); to_col(o, "Monuments")

# ---------- îlots Frioul / If
for name, (x, y, r) in {"ilot_frioul": (-14.5, 2.5, 2.2), "ilot_if": (-13.0, -3.2, 1.1)}.items():
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=r, radius2=0.05, depth=r * 2.2,
                                    location=(x, y, -r * 1.1 - 0.6), rotation=(math.pi, 0, 0))
    o = bpy.context.active_object; o.name = name + "_socle"; o.data.materials.append(MATS["roche"]); to_col(o, "Ilots")
    bpy.ops.mesh.primitive_cylinder_add(vertices=9, radius=r, depth=0.3, location=(x, y, -0.45))
    t = bpy.context.active_object; t.name = name; t.data.materials.append(MATS["calcaire"]); to_col(t, "Ilots")

# ---------- lumière, ciel, caméra
sun_d = bpy.data.lights.new("Soleil", "SUN"); sun_d.energy = 3.5; sun_d.angle = 0.2
sun = bpy.data.objects.new("Soleil", sun_d); cols["Lumieres"].objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
w = scene.world or bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.45, 0.68, 0.95, 1); bg.inputs[1].default_value = 0.9
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam)
cam.location = (22, -30, 20)
cam.rotation_euler = (Vector((-2, 0, -1)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
print("île construite")
