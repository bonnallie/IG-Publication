#!/usr/bin/env python3
"""Génère les JPEG publiables à partir des PNG de lieux/<lieu>/{1,2,3}.png.

story-N.jpg  : 1080x1920 (9:16), pour les stories.
grille-N.jpg : 1080x1440 (3:4), recadrage central pour la grille Instagram.
"""
from pathlib import Path
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent / "lieux"
HAUT_GRILLE = 240  # le contenu utile des visuels tient entre y=240 et y=1680

for dossier in sorted(p for p in RACINE.iterdir() if p.is_dir()):
    for n in (1, 2, 3):
        src = dossier / f"{n}.png"
        if not src.exists():
            print(f"MANQUANT {src}")
            continue
        img = Image.open(src).convert("RGB")
        if img.size != (1080, 1920):
            img = img.resize((1080, 1920), Image.LANCZOS)
        img.save(dossier / f"story-{n}.jpg", quality=92)
        img.crop((0, HAUT_GRILLE, 1080, HAUT_GRILLE + 1440)).save(dossier / f"grille-{n}.jpg", quality=92)
    print("ok", dossier.name)
