"""Genera un mapa base atractivo de Ybycuí para el cliente web (Fase 4).

Produce web/mapa_ybycui.png y renpy/game/images/mapa_ybycui.png.
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 800, 600
OUT_WEB = Path("C:/visualnovel/web/mapa_ybycui.png")
OUT_RENPY = Path("C:/visualnovel/renpy/game/images/mapa_ybycui.png")

img = Image.new("RGB", (W, H), (50, 70, 45))
draw = ImageDraw.Draw(img)

# --- Terreno base con variación ---
random.seed(42)
for y in range(0, H, 2):
    for x in range(0, W, 2):
        v = random.randint(-6, 6)
        # Gradiente: más verde en el centro, más oscuro en los bordes
        cx, cy = W // 2, H // 2
        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        factor = max(0.7, 1.0 - dist / 600)
        r = int((45 + v) * factor)
        g = int((65 + v) * factor)
        b = int((40 + v) * factor)
        draw.rectangle([x, y, x + 1, y + 1], fill=(r, g, b))

# --- Zonas ---
# Barrio (izquierda, verde oscuro)
for y in range(340, 600):
    for x in range(0, 360):
        if (x + y) % 7 < 3:
            draw.point((x, y), fill=(38, 52, 32))
# Centro (medio, verde claro)
for y in range(100, 420):
    for x in range(300, 600):
        if (x + y) % 5 < 2:
            draw.point((x, y), fill=(60, 75, 50))
# Afueras (derecha, verde muy oscuro)
for y in range(0, 600):
    for x in range(550, 800):
        if (x + y) % 6 < 2:
            draw.point((x, y), fill=(30, 45, 25))

# --- Río Ybycuí (ancho, con orillas) ---
river_pts = [(30, 590), (70, 530), (110, 490), (150, 450), (190, 390),
             (250, 330), (310, 290), (370, 270), (410, 250), (450, 240)]
# Orillas (más ancho, color tierra)
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(55, 80, 55), width=14)
# Agua
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(65, 110, 150), width=8)
# Brillo
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(90, 140, 180), width=2)

# --- Caminos principales ---
roads = [
    [(160, 500), (220, 420), (280, 360), (350, 300), (420, 260)],
    [(350, 300), (420, 340), (500, 300)],
    [(350, 300), (400, 180), (440, 140)],
    [(420, 260), (580, 380), (700, 480)],
    [(100, 340), (160, 300), (220, 280)],
]
for road in roads:
    for i in range(len(road) - 1):
        draw.line([road[i], road[i + 1]], fill=(100, 80, 55), width=4)
    for i in range(len(road) - 1):
        draw.line([road[i], road[i + 1]], fill=(120, 95, 65), width=2)

# --- Plaza (cuadrado central con árboles) ---
draw.rectangle([375, 175, 465, 265], fill=(50, 70, 40))
draw.rectangle([385, 185, 455, 255], fill=(60, 80, 50))
# árboles (círculos)
for tx, ty in [(395, 195), (420, 190), (445, 200), (400, 230), (435, 240)]:
    draw.ellipse([tx - 8, ty - 8, tx + 8, ty + 8], fill=(40, 65, 35))
    draw.ellipse([tx - 5, ty - 5, tx + 5, ty + 5], fill=(55, 80, 45))

# --- Iglesia (con torre) ---
draw.rectangle([440, 130, 505, 205], fill=(95, 88, 78))
draw.rectangle([450, 115, 495, 130], fill=(105, 98, 88))
draw.rectangle([462, 95, 483, 115], fill=(115, 108, 98))
# puerta
draw.rectangle([465, 175, 480, 205], fill=(60, 50, 40))
# cruz
draw.line([(472, 95), (472, 80)], fill=(200, 190, 170), width=2)
draw.line([(465, 88), (479, 88)], fill=(200, 190, 170), width=2)

# --- Almacén (rectángulo marrón) ---
draw.rectangle([355, 275, 425, 335], fill=(100, 75, 50))
draw.rectangle([360, 280, 420, 330], fill=(110, 85, 60))
# toldo
draw.rectangle([350, 270, 430, 280], fill=(130, 90, 55))

# --- Taller (rectángulo con virutas) ---
draw.rectangle([425, 295, 495, 355], fill=(105, 82, 60))
draw.rectangle([430, 300, 490, 350], fill=(115, 90, 68))
# virutas (puntos)
for i in range(8):
    draw.point((435 + i * 7, 310 + (i % 3) * 10), fill=(140, 110, 80))

# --- Estación del ferrocarril ---
draw.rectangle([75, 335, 205, 385], fill=(110, 95, 75))
draw.rectangle([80, 340, 200, 380], fill=(120, 105, 85))
# vías
for i in range(5):
    draw.line([(80 + i * 30, 380), (80 + i * 30, 395)], fill=(80, 70, 55), width=2)
draw.line([(75, 395), (205, 395)], fill=(90, 80, 65), width=3)

# --- Ruinas de la Fundición (La Rosada) ---
for i in range(4):
    draw.rectangle([615 + i * 25, 335, 635 + i * 25, 370], fill=(95, 90, 85))
    draw.rectangle([618 + i * 25, 340, 632 + i * 25, 365], fill=(85, 80, 75))
# base
draw.rectangle([605, 370, 720, 385], fill=(80, 75, 70))
# vegetación sobre ruinas
for tx, ty in [(625, 330), (650, 325), (675, 335), (700, 328)]:
    draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(50, 70, 40))

# --- Salto Mbocaruzú (cascada) ---
draw.ellipse([695, 455, 765, 525], fill=(70, 120, 160))
draw.ellipse([705, 465, 755, 515], fill=(85, 140, 180))
# espuma
draw.ellipse([715, 475, 745, 505], fill=(180, 200, 220))

# --- Cuartel ---
draw.rectangle([535, 75, 605, 135], fill=(80, 70, 55))
draw.rectangle([540, 80, 600, 130], fill=(90, 80, 65))
# bandera
draw.rectangle([595, 70, 600, 80], fill=(60, 50, 40))
draw.polygon([(600, 70), (620, 75), (600, 80)], fill=(200, 50, 50))

# --- Casas (pequeños rectángulos con techos) ---
casas = [(110, 410), (170, 450), (210, 390), (270, 430), (310, 370),
         (95, 290), (155, 270), (195, 310), (245, 290), (130, 470)]
for cx, cy in casas:
    draw.rectangle([cx, cy, cx + 22, cy + 16], fill=(110, 90, 68))
    draw.polygon([(cx - 2, cy), (cx + 11, cy - 10), (cx + 24, cy)], fill=(90, 70, 50))

# --- Árboles dispersos ---
arboles = [(50, 200), (60, 260), (120, 180), (200, 150), (280, 120),
           (320, 160), (500, 60), (560, 40), (620, 100), (680, 50),
           (720, 120), (750, 200), (580, 200), (640, 250), (700, 300)]
for tx, ty in arboles:
    draw.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=(45, 68, 38))
    draw.ellipse([tx - 4, ty - 4, tx + 4, ty + 4], fill=(60, 82, 50))

# --- Título ---
try:
    from PIL import ImageFont
    font = ImageFont.truetype("arial.ttf", 18)
    font_small = ImageFont.truetype("arial.ttf", 12)
except OSError:
    font = None
    font_small = None
if font:
    draw.text((12, 10), "Ybycuí, Paraguarí", fill=(230, 220, 200), font=font)
    draw.text((12, 32), "Un pueblo lejos de la guerra", fill=(180, 170, 150), font=font_small)

img.save(OUT_WEB)
img.save(OUT_RENPY)
print(f"Mapa guardado en {OUT_WEB} y {OUT_RENPY}")
