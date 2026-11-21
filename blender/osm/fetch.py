"""Télécharge les données OpenStreetMap de Marseille (API Overpass) dans osm/raw/.

Données © contributeurs OpenStreetMap (ODbL). Usage : python3 fetch.py [--force]
Une requête par couche, mise en cache : relancer ne retélécharge que ce qui manque.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(__file__).parent / "raw"
URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
BBOX = "43.15,5.20,43.40,5.60"  # sud, ouest, nord, est : la commune + Frioul + Plan-de-Cuques

QUERIES = {
    # limites : commune (8), arrondissements (9), Plan-de-Cuques
    "commune": 'rel["boundary"="administrative"]["admin_level"="8"]["name"="Marseille"];',
    "arrondissements": f'rel["boundary"="administrative"]["admin_level"="9"]["name"~"Marseille"]({BBOX});',
    "plan_de_cuques": 'rel["boundary"="administrative"]["admin_level"="8"]["name"="Plan-de-Cuques"];',
    # trait de côte et îles (Frioul, If, îlots)
    "cote": f'way["natural"="coastline"]({BBOX});',
    "iles": f'(way["place"~"island|islet"]({BBOX});rel["place"~"island|islet"]({BBOX}););',
    # routes principales
    "routes": f'way["highway"~"^(motorway|trunk|primary|secondary)$"]({BBOX});',
    # métro et tram : relations de ligne + stations
    "metro": f'rel["route"="subway"]({BBOX});',
    "metro_stations": f'rel["route"="subway"]({BBOX});node(r);',  # arrêts des lignes (stop_position)
    "tram": f'rel["route"="tram"]({BBOX});',
}


def overpass(q):
    data = urllib.parse.urlencode({"data": f"[out:json][timeout:180];{q}out geom;"}).encode()
    for url in URLS:
        for essai in range(3):
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": "osm-map-fetch/1.0"})
                with urllib.request.urlopen(req, timeout=200) as r:
                    return json.load(r)
            except Exception as e:  # 429/504 fréquents : on attend puis on change de serveur
                print(f"  {url} essai {essai + 1} : {e}")
                time.sleep(10 * (essai + 1))
    raise SystemExit("Overpass injoignable")


def main():
    RAW.mkdir(exist_ok=True)
    force = "--force" in sys.argv
    for name, q in QUERIES.items():
        out = RAW / f"{name}.json"
        if out.exists() and not force:
            print(f"{name} : déjà là")
            continue
        print(f"{name} …")
        res = overpass(q)
        out.write_text(json.dumps(res, ensure_ascii=False))
        print(f"  {len(res['elements'])} éléments, {out.stat().st_size // 1024} Ko")
        time.sleep(2)


if __name__ == "__main__":
    main()
