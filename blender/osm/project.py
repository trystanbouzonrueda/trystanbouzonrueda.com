"""Projette les données OSM brutes (raw/) en coordonnées locales -> marseille.json.

Lambert 93 (EPSG:2154), origine au Vieux-Port, unités en mètres, puis simplification
Douglas-Peucker. Données © contributeurs OpenStreetMap (ODbL).
"""
import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, Point
from shapely.ops import linemerge, polygonize, unary_union, transform

HERE = Path(__file__).parent
RAW = HERE / "raw"
ORIGIN = (43.2951, 5.3740)  # Vieux-Port (lat, lon)
TOL = {"limite": 40, "route": 25, "metro": 10}  # tolérances de simplification (m)

_t = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
OX, OY = _t.transform(ORIGIN[1], ORIGIN[0])


def proj(lon, lat):
    x, y = _t.transform(lon, lat)
    return x - OX, y - OY


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())["elements"]


def way_line(geom):
    return LineString([proj(p["lon"], p["lat"]) for p in geom])


def rel_polygon(rel):
    """Assemble les ways « outer » d'une relation en (multi)polygone."""
    lines = [way_line(m["geometry"]) for m in rel["members"]
             if m["type"] == "way" and m.get("role") in ("outer", "") and m.get("geometry")]
    polys = list(polygonize(linemerge(lines)))
    return unary_union(polys) if polys else None


def metro_paths():
    """Un tracé continu par ligne : stations dans l'ordre (1er sens de la relation),
    voie OSM entre deux stations quand elle est d'un seul tenant, sinon segment droit."""
    from shapely.ops import substring
    res = {}
    for r in load("metro"):
        ref = r["tags"].get("ref", "?")
        if ref in res:
            continue
        ways = [way_line(m["geometry"]) for m in r["members"] if m["type"] == "way" and m.get("role", "") == ""]
        merged = linemerge(ways)
        pieces = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
        stops = [(m["lat"], m["lon"]) for m in r["members"] if m["type"] == "node" and m.get("role", "").startswith("stop")]
        stops = [Point(proj(lon, lat)) for lat, lon in stops]
        path = []
        for a, b in zip(stops, stops[1:]):
            seg = None
            for pc in pieces:
                if pc.distance(a) < 80 and pc.distance(b) < 80:
                    da, db = pc.project(a), pc.project(b)
                    seg = substring(pc, min(da, db), max(da, db))
                    cs = list(seg.coords)
                    seg = cs if da <= db else cs[::-1]
                    break
            seg = seg or [a.coords[0], b.coords[0]]
            path += seg if not path else seg[1:]
        line = simplify(LineString(path), TOL["metro"])
        res[ref] = {"line": list(line.coords), "stations": [s.coords[0] for s in stops]}
    return res


def terre(commune):
    """Commune moins la mer : découpe par le trait de côte OSM (terre à gauche du sens de la ligne).
    Creuse les bassins du port que la limite administrative englobe."""
    com = max(getattr(commune, "geoms", [commune]), key=lambda g: g.area)
    m = linemerge([way_line(w["geometry"]) for w in load("cote") if w.get("geometry")])
    parts = list(getattr(m, "geoms", [m]))

    def is_land(poly):
        pt = poly.representative_point()
        best = min(parts, key=lambda l: l.distance(pt))
        d = best.project(pt)
        a, b = best.interpolate(max(0, d - 5)), best.interpolate(min(best.length, d + 5))
        return (b.x - a.x) * (pt.y - a.y) - (b.y - a.y) * (pt.x - a.x) > 0

    polys = list(polygonize(unary_union([com.exterior] + parts)))
    land = unary_union([p for p in polys if com.contains(p.representative_point()) and is_land(p)])
    return max(getattr(land, "geoms", [land]), key=lambda g: g.area)


def simplify(g, tol):
    return g.simplify(tol, preserve_topology=True)


def main():
    out = {"origin": ORIGIN, "units": "m", "credit": "© contributeurs OpenStreetMap"}

    commune = rel_polygon(load("commune")[0])
    out["commune"] = mapping(simplify(commune, TOL["limite"]))
    out["terre"] = mapping(simplify(terre(commune), 8))

    arr = []
    for r in load("arrondissements"):
        name = r["tags"].get("name", "")
        # « Marseille 1er Arrondissement » -> 1
        num = next((int(w.rstrip("eèrm")) for w in name.split() if w.rstrip("eèrm").isdigit()), None)
        p = rel_polygon(r)
        if num and p is not None:
            arr.append({"num": num, "name": name, "geom": mapping(simplify(p, TOL["limite"]))})
    out["arrondissements"] = sorted(arr, key=lambda a: a["num"])

    pdc = load("plan_de_cuques")
    if pdc:
        out["plan_de_cuques"] = mapping(simplify(rel_polygon(pdc[0]), TOL["limite"]))

    # îles : polygones fermés sous le niveau de la commune
    iles = []
    for e in load("iles"):
        g = None
        if e["type"] == "way" and e.get("geometry") and len(e["geometry"]) > 3:
            g = Polygon(way_line(e["geometry"]).coords)
        elif e["type"] == "relation":
            g = rel_polygon(e)
        if g is not None and g.is_valid and g.area > 2000:
            iles.append({"name": e.get("tags", {}).get("name", ""), "geom": mapping(simplify(g, 15))})
    out["iles"] = iles

    out["cote"] = [mapping(simplify(way_line(w["geometry"]), 15)) for w in load("cote") if w.get("geometry")]

    zone = commune.union(rel_polygon(pdc[0])) if pdc else commune
    rang = {"motorway": 1, "trunk": 1, "primary": 2, "secondary": 3}
    routes = {1: [], 2: [], 3: []}
    for w in load("routes"):
        hw = w["tags"]["highway"]
        if w.get("geometry"):
            g = way_line(w["geometry"]).intersection(zone)
            routes[rang[hw]] += [g] if g.geom_type == "LineString" and not g.is_empty else [x for x in getattr(g, "geoms", []) if x.geom_type == "LineString"]
    out["routes"] = {str(k): [mapping(simplify(g, TOL["route"])) for g in
                              (linemerge(v).geoms if hasattr(linemerge(v), "geoms") else [linemerge(v)])]
                     for k, v in routes.items() if v}

    def lignes(name):
        res = {}
        for r in load(name):
            ref = r["tags"].get("ref", "?")
            ways = [way_line(m["geometry"]) for m in r["members"] if m["type"] == "way" and m.get("geometry")
                    and m.get("role", "") in ("", "forward", "backward")]
            if not ways:
                continue
            m = linemerge(ways)
            geoms = list(m.geoms) if hasattr(m, "geoms") else [m]
            res.setdefault(ref, {"colour": r["tags"].get("colour"), "lines": []})["lines"] += [
                mapping(simplify(g, TOL["metro"])) for g in geoms]
        return res

    out["metro"] = lignes("metro")
    out["metro_path"] = metro_paths()
    out["tram"] = lignes("tram")
    st = {}  # un point par nom (moyenne des quais / directions)
    for n in load("metro_stations"):
        name = n.get("tags", {}).get("name")
        if name:
            st.setdefault(name, []).append(proj(n["lon"], n["lat"]))
    out["metro_stations"] = [{"name": k, "xy": (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v))}
                             for k, v in sorted(st.items())]

    (HERE / "marseille.json").write_text(json.dumps(out, ensure_ascii=False))
    b = commune.bounds
    print(f"commune {round((b[2]-b[0])/1000,1)} x {round((b[3]-b[1])/1000,1)} km, "
          f"{len(arr)} arrondissements, {len(iles)} îles, metro {list(out['metro'])}, tram {list(out['tram'])}, "
          f"{len(out['metro_stations'])} stations")


if __name__ == "__main__":
    main()
