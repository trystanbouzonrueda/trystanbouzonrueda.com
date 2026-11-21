"""Pose les modèles Meshy (déjà importés et simplifiés, objets « meshy_* ») sur l'île.

exec(lib.py) puis exec(place_monuments.py). Relançable : repositionne à chaque fois.
"""
import bpy
from mathutils import Vector


def bbox(o):
    bpy.context.view_layer.update()
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb))),
            Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb))))


def put(objname, x, y, width, place=None, zoff=0.0, rotz=0.0, z=None, parent=None):
    """Met l'objet à l'échelle (plus grande dimension au sol = width) et le pose au sol en (x, y)."""
    o = bpy.data.objects[objname]
    o.parent = None
    o.rotation_euler = (0, 0, rotz)
    o.scale = (1, 1, 1)
    mn, mx = bbox(o)
    s = width / max(mx.x - mn.x, mx.y - mn.y)
    o.scale = (s, s, s)
    mn, mx = bbox(o)
    if z is None:
        r = width / 3
        z = max(ground(x + dx, y + dy) for dx in (-r, 0, r) for dy in (-r, 0, r))
    o.location += Vector((x - (mn.x + mx.x) / 2, y - (mn.y + mx.y) / 2, z - mn.z + zoff))
    if place:
        e = bpy.data.objects.get("place_" + place)
        if e is None or e.type != 'EMPTY':
            remove("place_" + place)
            e = empty("place_" + place, (x, y, z), lot="M")
        parent = e
    if parent is not None:
        bpy.context.view_layer.update()
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    o["lot"] = "M"
    for c in o.users_collection: c.objects.unlink(o)
    COLS["Monuments"].objects.link(o)
    mn, mx = bbox(o)
    print(objname, "taille", tuple(round(v, 2) for v in mx - mn))
    return o


WL = -0.08
put("meshy_velodrome", 2.6, -3.4, 2.7, "velodrome", zoff=-0.05)
put("meshy_notre_dame", -2.6, 1.4, 1.5, "notre_dame", zoff=-0.25)
put("meshy_david", -4.6, -5.6, 0.35, "david")
put("meshy_mucem", -4.75, 7.15, 0.6, "mucem")
put("meshy_fort_saint_jean", -4.45, 6.45, 0.65, parent=bpy.data.objects.get("place_mucem"))
put("meshy_major", -3.0, 7.85, 0.9, "major")
put("meshy_dome", 5.2, 4.2, 1.1, "dome")
put("meshy_chateau_if", -13.0, -3.2, 1.3, z=-0.3)
# château Borély : remplace le volume provisoire du parc
for n in ("pb_chateau", "pb_chateau_toit"):
    remove(n)
put("meshy_chateau_borely", -2.95, -5.62, 0.65, parent=bpy.data.objects.get("place_borely"))
# bateaux : la navette entre le port et le Frioul, quelques pointus au Vieux-Port
put("meshy_navette_frioul", -7.2, 4.4, 0.55, z=WL - 0.02, rotz=0.2)
put("meshy_pointu", -1.25, 4.35, 0.22, z=WL - 0.01, rotz=1.57, parent=bpy.data.objects.get("place_vieux_port"))
src = bpy.data.objects["meshy_pointu"]
for k, (x, y, r) in enumerate([(-1.25, 5.15, 1.57), (-3.5, 4.5, 0.1), (-2.9, 5.05, -0.2)]):
    n = f"meshy_pointu_{k}"
    remove(n)
    d = src.copy()  # copie liée : même mesh, aucun poids en plus
    d.name = n
    COLS["Monuments"].objects.link(d)
    d.parent = None
    d.matrix_world = src.matrix_world.copy()
    d.location.x += x - (-1.25); d.location.y += y - 4.35
    d.rotation_euler[2] = r
    bpy.context.view_layer.update()
    d.parent = bpy.data.objects["place_vieux_port"]
    d.matrix_parent_inverse = d.parent.matrix_world.inverted()

# ---------------- lot Meshy 2 : nouveaux lieux, quartier, décor
def copies(src_name, spots, width, prefix=None, parent=None, zoff=0.0):
    """Copies liées (même mesh) d'un objet déjà posé, à d'autres endroits. spots = [(x, y, rotz), ...]."""
    src = bpy.data.objects[src_name]
    prefix = prefix or src_name
    out = []
    for k, (x, y, r) in enumerate(spots):
        n = f"{prefix}_{k}"
        remove(n)
        d = src.copy(); d.name = n
        COLS["Monuments"].objects.link(d)
        d.parent = None
        put_obj = d
        bpy.context.view_layer.update()
        out.append(put(n, x, y, width, zoff=zoff, rotz=r, parent=parent))
    return out


def has(n): return bpy.data.objects.get(n) is not None


# modèles validés (les autres seront refaits par image → Meshy)
if has("gen_tour_cma_cgm"): put("gen_tour_cma_cgm", -1.6, 8.6, 0.7, "cma_cgm")
if has("gen_cite_radieuse"): put("gen_cite_radieuse", 4.9, -4.9, 1.4, "cite_radieuse", rotz=0.3)
if has("gen_palais_longchamp"): put("gen_palais_longchamp", 6.0, 6.4, 1.6, "longchamp", rotz=3.14)
if has("gen_etal_poissons"): put("gen_etal_poissons", -0.9, 5.35, 0.16, parent=bpy.data.objects.get("place_vieux_port"))
print("monuments posés")
