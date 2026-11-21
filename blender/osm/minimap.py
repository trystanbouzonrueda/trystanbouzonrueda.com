"""Carte de téléportation du site : public/data/minimap.svg (terre, arrondissements, grands axes, métro)
+ minimap.json (bornes en unités île, pour placer le point du personnage).

python3 minimap.py
"""
import json
from pathlib import Path

from shapely import affinity
from shapely.geometry import shape

HERE = Path(__file__).parent
PUB = HERE.parent.parent / "public" / "data"
D = json.loads((HERE / "marseille.json").read_text())
U = 1 / 250
S = lambda g: affinity.scale(shape(g), U, U, origin=(0, 0))

terre = S(D["terre"]).buffer(0)
pdc = S(D["plan_de_cuques"]).buffer(0) if "plan_de_cuques" in D else None
from shapely.geometry import Point
CESI = Point(2.0, 59.0).buffer(1.5, 8)   # mini-île du CESI (blender/build_cesi.py), au nord vers Aix
x0, y0, x1, y1 = (terre.union(pdc) if pdc else terre).union(CESI).buffer(1).bounds
W = 360
K = W / (x1 - x0)
H = (y1 - y0) * K


def pt(x, y):
    return f"{(x - x0) * K:.1f},{(y1 - y) * K:.1f}"


def path(g):
    out = []
    for gg in getattr(g, "geoms", [g]):
        if gg.geom_type == "Polygon":
            for r in [gg.exterior, *gg.interiors]:
                out.append("M" + "L".join(pt(*c) for c in r.simplify(0.05).coords) + "Z")
        elif gg.geom_type == "LineString":
            out.append("M" + "L".join(pt(*c) for c in gg.simplify(0.05).coords))
    return "".join(out)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H:.0f}">']
svg.append(f'<path d="{path(terre)}" fill="#efe3c8" stroke="#b99b6b" stroke-width="1.2"/>')
if pdc: svg.append(f'<path d="{path(pdc)}" fill="#e2ebc9" stroke="#b99b6b" stroke-width="1" stroke-dasharray="3 2"/>')
svg.append(f'<path d="{path(CESI)}" fill="#e2ebc9" stroke="#b99b6b" stroke-width="1"/>')
cx, cy = pt(2.0, 59.0).split(",")
svg.append(f'<text x="{cx}" y="{float(cy) + 14:.1f}" font-family="system-ui,sans-serif" font-size="9" font-weight="700" fill="#8a6d43" text-anchor="middle">CESI · Aix</text>')
for a in D["arrondissements"]:
    svg.append(f'<path d="{path(S(a["geom"]).intersection(terre))}" fill="none" stroke="#cdb48a" stroke-width="0.7"/>')
for r, w, c in (("2", 1.1, "#ffffff"), ("1", 1.8, "#f6c25b")):
    for g in D["routes"].get(r, []):
        svg.append(f'<path d="{path(S(g))}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>')
for ref, v in D["metro_path"].items():
    col = {"M1": "#1d5fbf", "M2": "#d6232a"}.get(ref, "#333")
    pts = "L".join(pt(x * U, y * U) for x, y in v["line"])
    svg.append(f'<path d="M{pts}" fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round"/>')
for s in D["metro_stations"]:
    svg.append(f'<circle cx="{pt(s["xy"][0] * U, s["xy"][1] * U).split(",")[0]}" cy="{pt(s["xy"][0] * U, s["xy"][1] * U).split(",")[1]}" r="1.6" fill="#fff" stroke="#333" stroke-width=".6"/>')
# numéros d'arrondissement, pour se repérer
for a in D["arrondissements"]:
    g = S(a["geom"]).intersection(terre)
    if g.is_empty: continue
    c = g.representative_point()
    n = a.get("num") or a.get("n") or a.get("ref") or ""
    svg.append(f'<text x="{pt(c.x, c.y).split(",")[0]}" y="{pt(c.x, c.y).split(",")[1]}" font-family="system-ui,sans-serif" font-size="9" font-weight="700" fill="#8a6d43" text-anchor="middle" dominant-baseline="middle" opacity=".75">{n}</text>')
svg.append("</svg>")
(PUB / "minimap.svg").write_text("".join(svg))
# bornes en coordonnées three.js : x = x île, z = -y île
(PUB / "minimap.json").write_text(json.dumps({"x0": x0, "x1": x1, "z0": -y1, "z1": -y0}))
print("minimap", W, round(H), (PUB / "minimap.svg").stat().st_size // 1024, "Ko")
