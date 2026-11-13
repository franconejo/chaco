"""Genera retratos provisorios para el cliente Ren'Py (Fase 4).

Son rectángulos de color con la inicial del personaje: sirven para que el
cliente Ren'Py tenga algo que mostrar mientras no haya arte definitivo.
Se guardan en renpy/game/images/.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("C:/visualnovel/renpy/game/images")
OUT.mkdir(parents=True, exist_ok=True)

# (id, iniciales, color de fondo, color de texto)
PERSONAJES = [
    ("juana", "J", (180, 140, 90), (40, 30, 20)),
    ("celia", "C", (120, 130, 150), (30, 30, 40)),
    ("aurora", "A", (200, 160, 100), (40, 30, 20)),
    ("aurelio", "Au", (140, 110, 80), (30, 20, 10)),
    ("ramon", "R", (100, 90, 80), (240, 230, 210)),
    ("ursula", "Ú", (130, 150, 120), (30, 40, 30)),
    ("nicanor", "N", (110, 120, 140), (20, 30, 40)),
    ("vera", "V", (160, 80, 70), (240, 230, 210)),
    ("padre_ignacio", "PI", (90, 80, 70), (240, 230, 210)),
    ("dona_mercedes", "M", (170, 130, 150), (40, 30, 40)),
    ("teniente_ortega", "O", (80, 100, 120), (240, 230, 210)),
    ("protagonista", "P", (150, 130, 100), (40, 30, 20)),
]

W, H = 300, 400

try:
    font = ImageFont.truetype("arial.ttf", 120)
except OSError:
    font = ImageFont.load_default()

for pid, iniciales, bg, fg in PERSONAJES:
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    # borde
    draw.rectangle([0, 0, W - 1, H - 1], outline=fg, width=4)
    # iniciales centradas
    bbox = draw.textbbox((0, 0), iniciales, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((W - tw) / 2, (H - th) / 2 - 20), iniciales, fill=fg, font=font)
    # nombre abajo
    try:
        small = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        small = ImageFont.load_default()
    draw.text((10, H - 30), pid, fill=fg, font=small)
    img.save(OUT / f"{pid}.png")
    print(f"  {pid}.png")

print(f"Listo: {len(PERSONAJES)} retratos en {OUT}")
