"""Lance des constructions longues dans le Blender ouvert sans bloquer la connexion MCP.

    exec(open(D + "run_async.py").read()); lancer([4, 5, 6, ...])
Chaque arrondissement passe dans un minuteur bpy (un par tick) ; la progression va dans
blender/osm/build.log ; le fichier est enregistré à la fin. Suivi : tail -f blender/osm/build.log
"""
import os
BLENDER_DIR = os.environ.get("PORTFOLIO_BLENDER") or os.path.dirname(os.path.abspath(globals().get("__file__") or "blender/x")) + "/"  # dossier blender/ du dépôt (variable d'environnement si le script est lancé par exec)
import time
import traceback

import bpy

D = BLENDER_DIR
LOG = D + "osm/build.log"
COMMUN = ("lib.py", "batiments.py", "fastkit.py", "quartier.py", "lieux.py")


def _log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def _build(n):
    import io, contextlib
    g = {"__name__": f"arr{n}", "ARR": n,
         "DEBUG_SVG": f"/tmp/claude-1000/-home-trystan-tryzone/84ddccd1-2c42-4931-85c4-22d14636c502/scratchpad/arr{n}.svg"}
    files = COMMUN + ((f"build_arr{n:02d}.py",) if n in (1, 2) else ("build_arr_auto.py",)) if isinstance(n, int) else COMMUN + (n,)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for f in files:
            exec(compile(open(D + f).read(), D + f, "exec"), g)
    return out.getvalue().strip().replace("\n", " | ")


def lancer(liste, sauver=True):
    file = list(liste)
    open(LOG, "w").close()
    _log(f"début : {file}")

    def tick():
        if not file:
            if sauver: bpy.ops.wm.save_mainfile()
            _log("FIN")
            return None
        n = file.pop(0)
        t = time.time()
        try:
            res = _build(n)
            _log(f"{n} ok en {time.time() - t:.0f} s : {res}")
        except Exception:
            _log(f"{n} ERREUR : " + traceback.format_exc().replace("\n", " / "))
        return 0.5

    bpy.app.timers.register(tick, first_interval=0.5)
