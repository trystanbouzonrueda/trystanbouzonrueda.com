"""Carte de validation vue de dessus : marseille.json -> preview.svg (+ preview.png via magick)."""
import json
import subprocess
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import shape

HERE = Path(__file__).parent
D = json.loads((HERE / "marseille.json").read_text())

# Palette du site (blocs francs, couleurs unies)
MER, TERRE, LIMITE, ROUTE = "#7fc4d9", "#efe3c8", "#c9a877", "#ffffff"
ARR_COLS = ["#f2d9a6", "#e9c99a", "#f5e2b8", "#e3d3a3", "#ecd7b0", "#f0cf9c", "#e6dcb6", "#f3d6aa"]

# Monuments faits main, à leur vraie place (lat, lon)
MONUMENTS = {
    "Notre-Dame": (43.2840, 5.3713), "Vélodrome": (43.2698, 5.3959), "Mucem": (43.2967, 5.3611),
    "Major": (43.2995, 5.3653), "Dôme": (43.3069, 5.3967), "Longchamp": (43.3046, 5.3943),
    "St-Charles": (43.3027, 5.3806), "CMA CGM": (43.3123, 5.3658), "Cité Radieuse": (43.2613, 5.3963),
    "David": (43.2594, 5.3754), "Borély": (43.2560, 5.3829), "If": (43.2799, 5.3254),
    "Vieux-Port": (43.2951, 5.3740),
}

_t = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
ox, oy = _t.transform(D["origin"][1], D["origin"][0])

commune = shape(D["commune"])
minx, miny, maxx, maxy = commune.buffer(2500).bounds
S = 0.05  # px par mètre -> ~1500 px de large
W, H = (maxx - minx) * S, (maxy - miny) * S


def pt(x, y):
    return f"{(x - minx) * S:.1f},{(maxy - y) * S:.1f}"


def path(g):
    if g.geom_type == "GeometryCollection":
        return " ".join(path(x) for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon"))
    if g.geom_type in ("Polygon", "MultiPolygon"):
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        return " ".join("M" + " L".join(pt(*c) for c in ring.coords) + "Z"
                        for p in polys for ring in [p.exterior, *p.interiors])
    lines = [g] if g.geom_type == "LineString" else list(g.geoms)
    return " ".join("M" + " L".join(pt(*c) for c in l.coords) for l in lines)


svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
       f'font-family="sans-serif"><rect width="100%" height="100%" fill="{MER}"/>']

if "plan_de_cuques" in D:
    svg.append(f'<path d="{path(shape(D["plan_de_cuques"]))}" fill="#dfe8c8" stroke="{LIMITE}" stroke-width="2" stroke-dasharray="8 6"/>')
svg.append(f'<path d="{path(commune)}" fill="#bfe0ea" stroke="#8a6b3f" stroke-width="1"/>')
svg.append(f'<path d="{path(shape(D["terre"]))}" fill="{TERRE}" stroke="#8a6b3f" stroke-width="3"/>')
for a in D["arrondissements"]:
    svg.append(f'<path d="{path(shape(a["geom"]).intersection(shape(D["terre"])))}" fill="{ARR_COLS[a["num"] % len(ARR_COLS)]}" '
               f'stroke="{LIMITE}" stroke-width="2"/>')
for i in D.get("iles", []):
    svg.append(f'<path d="{path(shape(i["geom"]))}" fill="{TERRE}" stroke="#8a6b3f" stroke-width="1.5"/>')

for rang, w in (("3", 1.5), ("2", 2.5), ("1", 4.5)):
    for g in D.get("routes", {}).get(rang, []):
        g = shape(g)
        if g.intersects(commune.buffer(500)):
            svg.append(f'<path d="{path(g)}" fill="none" stroke="{ROUTE if rang != "1" else "#f6c25b"}" '
                       f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')

for ref, l in D.get("tram", {}).items():
    for g in l["lines"]:
        svg.append(f'<path d="{path(shape(g))}" fill="none" stroke="#7a7a7a" stroke-width="2" stroke-dasharray="5 3"/>')
METRO_COL = {"M1": "#1d5fbf", "M2": "#d6232a", "1": "#1d5fbf", "2": "#d6232a"}
for ref, l in D.get("metro", {}).items():
    for g in l["lines"]:
        svg.append(f'<path d="{path(shape(g))}" fill="none" stroke="{METRO_COL.get(ref, l["colour"] or "#000")}" '
                   f'stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
for s in D.get("metro_stations", []):
    svg.append(f'<circle cx="{pt(*s["xy"]).split(",")[0]}" cy="{pt(*s["xy"]).split(",")[1]}" r="6" fill="#fff" stroke="#222" stroke-width="2.5"/>'
               f'<text x="{float(pt(*s["xy"]).split(",")[0])+8}" y="{float(pt(*s["xy"]).split(",")[1])-6}" font-size="10" fill="#1a2b4a" '
               f'stroke="#fff" stroke-width="2.5" paint-order="stroke">{s["name"]}</text>')

for a in D["arrondissements"]:
    c = shape(a["geom"]).representative_point()
    x, y = pt(c.x, c.y).split(",")
    svg.append(f'<text x="{x}" y="{y}" font-size="30" font-weight="bold" fill="#6b4f2a" '
               f'text-anchor="middle" opacity="0.75">{a["num"]}</text>')
for name, (lat, lon) in MONUMENTS.items():
    mx, my = _t.transform(lon, lat)
    x, y = pt(mx - ox, my - oy).split(",")
    svg.append(f'<rect x="{float(x)-6}" y="{float(y)-6}" width="12" height="12" fill="#e8743b" stroke="#fff" stroke-width="2"/>'
               f'<text x="{float(x)+9}" y="{float(y)+5}" font-size="15" fill="#3a2a14" '
               f'stroke="#fff" stroke-width="3" paint-order="stroke">{name}</text>')
svg.append(f'<text x="12" y="{H-12:.0f}" font-size="14" fill="#234">© contributeurs OpenStreetMap</text></svg>')

(HERE / "preview.svg").write_text("\n".join(svg))
subprocess.run(["magick", str(HERE / "preview.svg"), str(HERE / "preview.png")], check=True)
print(f"preview.png {W:.0f}x{H:.0f}")
