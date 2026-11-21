"""Captures rapides sur le vrai GPU, à des vues précises (outil de dev).

uvx --from playwright python -I scripts/look.py <dossier> [url] [--q=high] [--w=1400x850]
Vues : ouverture, figurine (Notre-Dame), port (bateaux), large, nuit.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

pos = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
out = Path(pos[0]); out.mkdir(parents=True, exist_ok=True)
url = pos[1] if len(pos) > 1 else "http://127.0.0.1:5173/"
url += ("&" if "?" in url else "?") + "debug&q=" + opt.get("q", "high")
w, h = map(int, opt.get("w", "1400x850").split("x"))

VUES = [
    ("1_ouverture", None),
    ("2_figurine", "trystan"),
    ("3_port", ([-1.5, 2.2, 1.0], [-2.6, 0.2, 4.2])),
    ("4_large", ([22, 16, 18], [0, 0, 2])),
]
logs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-angle=gl", "--enable-gpu", "--ignore-gpu-blocklist"])
    page = b.new_page(viewport={"width": w, "height": h})
    page.on("console", lambda m: m.type in ("error", "warning") and logs.append(f"{m.type}: {m.text}"))
    page.on("pageerror", lambda e: logs.append(f"pageerror: {e}"))
    page.goto(url)
    page.wait_for_selector(".loading.done", timeout=180000)
    page.wait_for_timeout(4000)
    for nom, v in VUES:
        if v == "trystan":
            page.evaluate("""() => { const d = window.__perf; let t = null;
              d.scene.traverse(o => { if (o.name === 'trystan' || o.name === 'hanches') t = t || o; });
              if (!t) return; const p = t.getWorldPosition(new t.position.constructor());
              d.setView([p.x + 0.55, p.y + 0.3, p.z + 0.55], [p.x, p.y + 0.1, p.z]); }""")
        elif v:
            page.evaluate("([p, t]) => window.__perf.setView(p, t)", list(v))
        page.wait_for_timeout(1800)
        page.screenshot(path=str(out / f"{nom}.png"))
    page.get_by_role("button", name="Projets").click()
    page.wait_for_timeout(3500)
    page.screenshot(path=str(out / "6_projets.png"))
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Nuit").click()
    page.evaluate("() => window.__perf.setView([6.8, 6.2, -1.0], [0.3, 1.4, 6.0])")
    page.wait_for_timeout(3500)
    page.screenshot(path=str(out / "5_nuit.png"))
    b.close()
print("\n".join(logs[-15:]) or "console propre")
