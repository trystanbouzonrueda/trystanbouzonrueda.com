"""Génère les images de référence Meshy EN LOCAL : stable-diffusion.cpp (Vulkan) + FLUX.1-schnell Q4.

python3 -I gen_images_local.py <dossier meshy> [nom ...]
Binaire : ~/.local/opt/sdcpp/sd-cli ; modèles : ~/.local/share/sdcpp/models/
Lit les prompts dans PROMPTS.md, écrit images/<nom>_<n>.png, saute ce qui existe déjà.
"""
import os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(sys.argv[1]); ONLY = set(sys.argv[2:])
OUT = ROOT / "images"; OUT.mkdir(exist_ok=True)
BIN = Path.home() / ".local/opt/sdcpp"; MOD = Path.home() / ".local/share/sdcpp/models"
SUFFIX = (", isometric miniature 3D render, stylized tycoon game asset, soft studio lighting, "
          "single object centered, three-quarter view, plain light grey background, full object visible, "
          "no base plate, no sign, no text, no people")
SEEDS = [11, 42, 777]
SKIP = {"notre_dame"}  # image déjà faite à la main

prompts = dict(re.findall(r"\*\*(\w+)\.glb\*\*\s*```\s*(.+?)\s*```", (ROOT / "PROMPTS.md").read_text(), re.S))
env = dict(os.environ, LD_LIBRARY_PATH=str(BIN))
for name, prompt in prompts.items():
    if name in SKIP or (ONLY and name not in ONLY): continue
    for n, seed in enumerate(SEEDS, 1):
        dst = OUT / f"{name}_{n}.png"
        if dst.exists(): continue
        t = time.time()
        cmd = [str(BIN / "sd-cli"),
               "--diffusion-model", str(MOD / "flux1-schnell-Q4_K_S.gguf"),
               "--t5xxl", str(MOD / "t5xxl-Q4_K_M.gguf"), "--clip_l", str(MOD / "clip_l.safetensors"),
               "--vae", str(MOD / "ae.safetensors"),
               "-p", prompt + SUFFIX, "--cfg-scale", "1.0", "--sampling-method", "euler", "--steps", "4",
               "-W", "1024", "-H", "1024", "-s", str(seed),
               "--offload-to-cpu", "--vae-tiling", "--backend", "te=cpu", "--flash-attn", "on",
               "-o", str(dst)]
        r = subprocess.run(cmd, env=env, capture_output=True, text=True)
        ok = dst.exists() and r.returncode == 0
        print(("ok" if ok else "échec"), dst.name, f"{time.time() - t:.0f}s",
              "" if ok else r.stderr[-400:], flush=True)
print("terminé", flush=True)
