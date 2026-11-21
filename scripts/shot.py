"""Captures du site 3D avec Playwright (outil de dev).

uvx --from playwright python -I scripts/shot.py <dossier_sortie> [url]
Prend : vue d'ensemble, puis un clic sur une rubrique (Projets), puis la nuit.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5173/"
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    page = b.new_page(viewport={"width": 1400, "height": 850})
    logs = []
    page.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
    page.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
    page.goto(url)
    page.wait_for_selector(".loading.done", timeout=120000)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(out / "1_ensemble.png"))
    page.get_by_role("button", name="Projets").click()
    page.wait_for_timeout(3500)
    page.screenshot(path=str(out / "2_projets.png"))
    page.get_by_role("button", name="Nuit").click()
    page.wait_for_timeout(3000)
    page.screenshot(path=str(out / "3_nuit.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(2000)
    page.screenshot(path=str(out / "4_mobile.png"))
    b.close()
print("\n".join(logs[-15:]) or "aucun message console")
