"""Mesure de perf du site 3D (outil de dev).

uvx --from playwright python -I scripts/perf.py [url] [--soft]
Ouvre l'URL avec ?debug, place la caméra sur 3 vues et mesure fps, draw calls, triangles.
Par défaut essaie le vrai GPU (headless + ANGLE GL) ; --soft force SwiftShader (fps sans valeur).
--q=high --q=low : niveaux à mesurer (défaut high).
"""
import json
import sys
from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
soft = "--soft" in sys.argv
url = args[0] if args else "http://127.0.0.1:5173/"
url += ("&" if "?" in url else "?") + "debug"
NIVEAUX = [a.split("=")[1] for a in sys.argv if a.startswith("--q=")] or ["high"]

VUES = {
    "ouverture": None,  # vue HOME telle quelle
    "large": ([22, 16, 18], [0, 0, 2]),
    "rue": ([1.5, 1.6, 3.5], [0.3, 0.6, 5.5]),
}

flags = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] if soft else ["--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist", "--disable-gpu-vsync", "--disable-frame-rate-limit"]
with sync_playwright() as p:
    b = p.chromium.launch(args=flags)
    for q in NIVEAUX:
      for vw, vh, nom in ((1400, 850, "desktop"), (844, 390, "mobile-paysage")):
        page = b.new_page(viewport={"width": vw, "height": vh}, device_scale_factor=1 if nom == "desktop" else 3)
        page.goto(url + "&q=" + q)
        page.wait_for_selector(".loading.done", timeout=180000)
        gpu = page.evaluate("""() => { const gl = window.__perf.renderer.getContext();
            const e = gl.getExtension('WEBGL_debug_renderer_info'); return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : '?'; }""")
        page.wait_for_timeout(4000)  # détails chargés
        res = {}
        for vue, pt in VUES.items():
            if pt:
                page.evaluate("([p, t]) => window.__perf.setView(p, t)", list(pt))
            page.wait_for_timeout(1500)
            r = page.evaluate("""async () => { const d = window.__perf; const f0 = d.frames, c0 = d.cpu, t0 = performance.now();
                await new Promise(r => setTimeout(r, 4000));
                return { fps: +((d.frames - f0) / ((performance.now() - t0) / 1000)).toFixed(1), cpu_ms: +((d.cpu - c0) / (d.frames - f0)).toFixed(2), calls: d.calls, tri: d.triangles }; }""")
            res[vue] = r
        print(json.dumps({"q": q, "ecran": nom, "gpu": gpu, **res}, ensure_ascii=False))
        page.close()
    b.close()
