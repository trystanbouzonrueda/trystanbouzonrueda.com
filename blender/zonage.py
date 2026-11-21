"""Aperçu du zonage des quartiers (plaques colorées + noms), collection « Zonage », jamais exportée.

QUARTIERS est la référence partagée par les scripts de quartiers/*.py.
"""
import bpy, math

QUARTIERS = {  # id: (nom, centre x, centre y, demi-largeur, demi-hauteur, couleur)
    "estaque":        ("L'Estaque",                    -3.4, 9.0, 1.0, 0.55, "#e2483d"),
    "joliette":       ("Joliette / Terrasses du Port", -1.0, 8.2, 1.0, 0.85, "#3f7fd1"),
    "quartiers_nord": ("Quartiers Nord",                1.8, 8.5, 1.2, 0.8,  "#f2c14e"),
    "la_rose":        ("La Rose",                       4.6, 7.6, 1.0, 0.9,  "#c86bd6"),
    "panier":         ("Le Panier",                    -1.7, 6.95, 0.85, 0.45, "#e8955a"),
    "canebiere":      ("Canebière & Noailles",          1.7, 4.3, 1.6, 0.8,  "#e04f7a"),
    "cours_julien":   ("Cours Julien / Belle de Mai",   3.8, 2.4, 1.0, 1.0,  "#7ac74f"),
    "plan_de_cuques": ("Plan-de-Cuques",                7.0, 1.6, 1.3, 1.6,  "#a3c45a"),
    "castellane":     ("Castellane / Prado",            0.9, -1.3, 1.3, 1.1, "#5bc0be"),
    "endoume":        ("Endoume / Vallon des Auffes",  -3.7, -1.0, 0.6, 1.7, "#2fb6d8"),
    "plages":         ("Plages du Prado",              -0.7, -5.3, 0.9, 0.6, "#f1dca0"),
    "goudes":         ("Les Goudes / Calanques",        0.6, -7.6, 1.7, 0.5, "#efe9dc"),
    "sainte_marguerite": ("Sainte-Marguerite / Le Rouet", 5.1, -2.5, 1.0, 0.9, "#9b8cf0"),
    "mazargues":      ("Mazargues / Sainte-Anne",       2.7, -6.0, 1.1, 0.55, "#f0a38c"),
}


def draw():
    col = bpy.data.collections.get("Zonage") or bpy.data.collections.new("Zonage")
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for qid, (nom, x, y, hw, hh, c) in QUARTIERS.items():
        m = mat("zone_" + qid, c)
        z = max(ground(x + dx, y + dy) for dx in (-hw, 0, hw) for dy in (-hh, 0, hh)) + 0.05
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
        o = bpy.context.active_object; o.name = "zone_" + qid; o.scale = (hw * 2, hh * 2, 0.04)
        o.data.materials.append(m)
        for cc in o.users_collection: cc.objects.unlink(o)
        col.objects.link(o)
        bpy.ops.object.text_add(location=(x - hw + 0.1, y, z + 0.05))
        t = bpy.context.active_object; t.data.body = nom; t.data.size = 0.28; t.name = "label_" + qid
        t.data.materials.append(MATS["route"])
        for cc in t.users_collection: cc.objects.unlink(t)
        col.objects.link(t)
    print("zonage dessiné :", len(QUARTIERS), "quartiers")
