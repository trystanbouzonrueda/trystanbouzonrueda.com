"""Image de partage (Open Graph) : vue d'ouverture sans interface, 1200×630 → public/img/og.jpg.

uvx --from playwright python -I scripts/og.py [url]
"""
import sys
from playwright.sync_api import sync_playwright

url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173/") + "?debug&q=high"
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist"])
    page = b.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
    page.goto(url)
    page.wait_for_selector(".loading.done", timeout=180000)
    # vue d'ouverture (depuis la mer, au coucher de soleil par défaut), une fois l'arrivée du ciel terminée
    page.wait_for_timeout(9000)
    page.add_style_tag(content=".hud-top,.hud-bottom,.bulles,.credits,.hint,.pad{display:none!important}")
    page.wait_for_timeout(600)
    page.screenshot(path="public/img/og.jpg", type="jpeg", quality=86)
    b.close()
print("public/img/og.jpg")
