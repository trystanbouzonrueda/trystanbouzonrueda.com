"""Rues fines d'un arrondissement (tertiary, residential, piétonnes) -> raw/rues_<n>.json.

Usage : python3 fetch_rues.py 1 [2 3 ...]. Données © contributeurs OpenStreetMap (ODbL).
"""
import json
import sys
from pathlib import Path

from fetch import RAW, overpass

ARR = {}
for r in json.loads((RAW / "arrondissements.json").read_text())["elements"]:
    n = next((int(w.rstrip("eèrm")) for w in r["tags"]["name"].split() if w.rstrip("eèrm").isdigit()), None)
    if n: ARR[n] = r["id"]

for n in map(int, sys.argv[1:]):
    q = (f'rel({ARR[n]});map_to_area->.a;'
         'way["highway"~"^(primary|secondary|tertiary|residential|pedestrian|living_street|unclassified)$"](area.a);'
         'out geom;')
    q = q[:-len("out geom;")]  # overpass() ajoute « out geom; »
    res = overpass(q)
    out = RAW / f"rues_{n}.json"
    out.write_text(json.dumps(res, ensure_ascii=False))
    print(n, len(res["elements"]), "rues", out.stat().st_size // 1024, "Ko")
