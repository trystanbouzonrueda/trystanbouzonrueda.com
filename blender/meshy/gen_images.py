"""Génère les images de référence Meshy avec FLUX.1-schnell (Hugging Face Space, gratuit).

uvx --with gradio_client python -I gen_images.py <dossier meshy>
Lit les prompts dans PROMPTS.md, écrit images/<nom>_<n>.png, saute ce qui existe déjà.
"""
import re, shutil, subprocess, sys, time
from pathlib import Path
from gradio_client import Client

ROOT = Path(sys.argv[1])
OUT = ROOT / "images"; OUT.mkdir(exist_ok=True)
SUFFIX = (", isometric miniature 3D render, stylized tycoon game asset, soft studio lighting, "
          "single object centered, three-quarter view, plain light grey background, full object visible, "
          "no base plate, no sign, no text, no people")
SEEDS = [11, 42, 777]
SKIP = {"notre_dame"}  # image déjà faite à la main

text = (ROOT / "PROMPTS.md").read_text()
prompts = dict(re.findall(r"\*\*(\w+)\.glb\*\*\s*```\s*(.+?)\s*```", text, re.S))
client = Client("black-forest-labs/FLUX.1-schnell")
for name, prompt in prompts.items():
    if name in SKIP: continue
    for n, seed in enumerate(SEEDS, 1):
        dst = OUT / f"{name}_{n}.png"
        if dst.exists(): continue
        for attempt in range(4):
            try:
                path, _ = client.predict(prompt=prompt + SUFFIX, seed=seed, randomize_seed=False,
                                         width=1024, height=1024, num_inference_steps=4, api_name="/infer")
                subprocess.run(["magick", path, str(dst)], check=True)
                print("ok", dst.name, flush=True)
                break
            except Exception as e:
                print("échec", dst.name, attempt, str(e)[:200], flush=True)
                time.sleep(60 * (attempt + 1))
print("terminé", flush=True)
