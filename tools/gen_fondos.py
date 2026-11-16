"""Genera fondos (backgrounds) para el cliente Ren'Py (Fase 4).

Fondos estilizados de Ybycuí, Paraguarí. Se guardan en
renpy/game/images/bg/ para usar como `image bg_plaza = "images/bg/bg_plaza.png"`.
"""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
OUT = Path("C:/visualnovel/renpy/game/images/bg")
OUT.mkdir(parents=True, exist_ok=True)

random.seed(7)


def base_sky(img, draw, warm=True):
    """Cielo con gradiente."""
    for y in range(H // 2):
        t = y / (H // 2)
        if warm:
            r = int(180 + 40 * t)
            g = int(140 + 60 * t)
            b = int(90 + 80 * t)
        else:
            r = int(120 + 30 * t)
            g = int(140 + 40 * t)
            b = int(170 + 60 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def ground(img, draw, color=(60, 75, 45)):
    """Suelo con variación."""
    for y in range(H // 2, H):
        for x in range(0, W, 2):
            v = random.randint(-5, 5)
            draw.point((x, y), fill=(color[0] + v, color[1] + v, color[2] + v))
            draw.point((x + 1, y), fill=(color[0] + v, color[1] + v, color[2] + v))


def draw_trees(draw, positions, size=30):
    for tx, ty in positions:
        # Tronco
        draw.rectangle([tx - 3, ty, tx + 3, ty + size], fill=(80, 60, 40))
        # Copa
        draw.ellipse([tx - size, ty - size, tx + size, ty + size // 2], fill=(40, 70, 35))
        draw.ellipse([tx - size + 5, ty - size + 5, tx + size - 5, ty + size // 2 - 5], fill=(55, 85, 45))  # noqa: E501


def draw_building(draw, x, y, w, h, color, roof_color=None):
    draw.rectangle([x, y, x + w, y + h], fill=color)
    if roof_color:
        draw.polygon([(x - 5, y), (x + w // 2, y - 20), (x + w + 5, y)], fill=roof_color)


# === PLAZA ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (55, 70, 42))
# Plaza central
draw.rectangle([400, 300, 880, 600], fill=(65, 80, 50))
draw.rectangle([440, 340, 840, 560], fill=(75, 90, 58))
# Árboles de lapacho
draw_trees(draw, [(460, 320), (520, 310), (600, 300), (680, 315), (760, 325), (500, 560), (650, 570)], 35)  # noqa: E501
# Banco
draw.rectangle([580, 420, 680, 440], fill=(100, 80, 55))
draw.rectangle([585, 415, 675, 420], fill=(90, 70, 45))
# Kiosco
draw.rectangle([700, 360, 780, 420], fill=(120, 90, 60))
draw.polygon([(690, 360), (740, 330), (790, 360)], fill=(100, 75, 50))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Plaza de Ybycuí", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_plaza.png")

# === ALMACÉN ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (70, 60, 45))
# Pared del almacén
draw.rectangle([200, 200, 1080, 600], fill=(110, 90, 65))
draw.rectangle([220, 220, 1060, 580], fill=(120, 100, 75))
# Toldo
draw.rectangle([180, 180, 1100, 220], fill=(140, 100, 60))
# Mostrador
draw.rectangle([300, 450, 980, 500], fill=(90, 70, 50))
# Bolsas
for i in range(5):
    draw.ellipse([250 + i * 60, 500, 310 + i * 60, 560], fill=(130, 110, 80))
# Estantes
for y in [240, 280, 320, 360]:
    draw.rectangle([240, y, 1040, y + 5], fill=(80, 65, 45))
# Botellas/frascos
for x in range(260, 1020, 40):
    for y in [230, 270, 310]:
        draw.ellipse([x, y, x + 12, y + 20], fill=(100, 130, 90))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Almacén de don Ramón", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_almacen.png")

# === CASA ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (65, 60, 45))
# Pared
draw.rectangle([250, 250, 1030, 620], fill=(130, 110, 85))
draw.rectangle([270, 270, 1010, 600], fill=(140, 120, 95))
# Puerta
draw.rectangle([580, 450, 700, 620], fill=(90, 70, 50))
# Ventana
draw.rectangle([320, 320, 420, 400], fill=(160, 180, 200))
draw.rectangle([860, 320, 960, 400], fill=(160, 180, 200))
# Mesa
draw.rectangle([400, 500, 650, 540], fill=(100, 80, 55))
# Cama (en el fondo)
draw.rectangle([750, 480, 980, 580], fill=(90, 75, 60))
draw.rectangle([760, 490, 970, 570], fill=(120, 100, 80))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Tu casa", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_casa.png")

# === IGLESIA ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=False)
ground(img, draw, (50, 60, 40))
# Nave
draw.rectangle([300, 200, 980, 620], fill=(90, 85, 75))
draw.rectangle([320, 220, 960, 600], fill=(100, 95, 85))
# Torre
draw.rectangle([560, 80, 720, 220], fill=(95, 90, 80))
draw.rectangle([580, 60, 700, 80], fill=(105, 100, 90))
# Puerta
draw.rectangle([590, 480, 690, 620], fill=(70, 60, 50))
# Ventanas
for x in [360, 480, 780, 900]:
    draw.rectangle([x, 300, x + 60, 400], fill=(160, 180, 200))
# Banco
draw.rectangle([400, 520, 880, 560], fill=(80, 70, 55))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Iglesia de Ybycuí", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_iglesia.png")

# === FUNDICIÓN (La Rosada) ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (50, 65, 40))
# Ruinas de hornos
for i in range(5):
    x = 200 + i * 120
    draw.rectangle([x, 300, x + 80, 450], fill=(90, 85, 80))
    draw.rectangle([x + 5, 305, x + 75, 445], fill=(80, 75, 70))
    # Arco
    draw.arc([x, 280, x + 80, 340], 180, 360, fill=(70, 65, 60), width=3)
# Vegetación sobre las ruinas
for tx, ty in [(230, 290), (350, 285), (470, 295), (590, 288), (710, 292)]:
    draw.ellipse([tx - 15, ty - 15, tx + 15, ty + 15], fill=(45, 70, 38))
    draw.ellipse([tx - 8, ty - 8, tx + 8, ty + 8], fill=(60, 85, 50))
# Sendero
draw.rectangle([0, 460, 1280, 475], fill=(90, 75, 55))
# Cartel
draw.rectangle([580, 440, 700, 470], fill=(100, 85, 65))
try:
    font = ImageFont.truetype("arial.ttf", 16)
    draw.text((590, 445), "La Rosada", fill=(230, 220, 200), font=font)
    draw.text((50, 50), "Ruinas de la Fundición", fill=(240, 230, 200), font=ImageFont.truetype("arial.ttf", 24))  # noqa: E501
except OSError:
    pass
img.save(OUT / "bg_fundicion.png")

# === RÍO ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (50, 65, 40))
# Río (ancho, serpenteante)
river_pts = [(0, 500), (100, 480), (200, 460), (300, 440), (400, 420),
             (500, 400), (600, 380), (700, 360), (800, 340), (900, 320),
             (1000, 300), (1100, 280), (1280, 260)]
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(50, 80, 55), width=20)
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(65, 110, 150), width=14)
for i in range(len(river_pts) - 1):
    draw.line([river_pts[i], river_pts[i + 1]], fill=(90, 145, 185), width=4)
# Piedras
for x, y in [(200, 470), (350, 430), (500, 395), (650, 370), (800, 335), (950, 305)]:
    draw.ellipse([x - 8, y - 5, x + 8, y + 5], fill=(100, 95, 85))
# Lavanderas
for lx, ly in [(150, 470), (400, 415), (700, 360)]:
    draw.ellipse([lx - 10, ly - 12, lx + 10, ly + 12], fill=(130, 100, 80))
    draw.rectangle([lx - 3, ly + 12, lx + 3, ly + 30], fill=(100, 80, 60))
# Vegetación
draw_trees(draw, [(50, 400), (300, 350), (600, 280), (900, 220), (1100, 180)], 25)
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Río Ybycuí", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_rio.png")

# === TALLER ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (70, 60, 45))
# Pared
draw.rectangle([200, 200, 1080, 620], fill=(100, 80, 55))
draw.rectangle([220, 220, 1060, 600], fill=(110, 90, 65))
# Puerta abierta
draw.rectangle([500, 400, 620, 620], fill=(60, 45, 30))
# Banco de trabajo
draw.rectangle([250, 460, 700, 500], fill=(90, 70, 45))
# Madera apilada
for i in range(6):
    draw.rectangle([750 + i * 15, 440, 765 + i * 15, 520], fill=(120, 90, 60))
# Herramientas
draw.rectangle([300, 380, 320, 460], fill=(80, 70, 55))  # serrucho
draw.rectangle([340, 390, 355, 460], fill=(90, 75, 60))  # martillo
# Virutas en el piso
for i in range(20):
    x = 230 + (i * 37) % 800
    y = 510 + (i * 13) % 60
    draw.ellipse([x, y, x + 8, y + 3], fill=(140, 110, 80))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Taller de carpintería", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_taller.png")

# === MERCADO ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (60, 65, 45))
# Puestos
for _i, (px, py, color) in enumerate([(200, 350, (130, 90, 60)), (350, 320, (100, 110, 70)),
                                      (500, 340, (120, 80, 55)), (650, 310, (90, 100, 65)),
                                      (800, 330, (110, 85, 50)), (950, 300, (100, 95, 60))]):
    draw.rectangle([px, py, px + 120, py + 80], fill=color)
    draw.polygon([(px - 10, py), (px + 60, py - 30), (px + 130, py)], fill=(color[0] - 20, color[1] - 20, color[2] - 20))  # noqa: E501
# Productos en los puestos
for px, py in [(220, 370), (370, 340), (520, 360), (670, 330), (820, 350), (970, 320)]:
    for dx in range(0, 80, 15):
        draw.ellipse([px + dx, py, px + dx + 10, py + 15], fill=(150, 130, 60))
# Gente (pequeñas figuras)
for gx, gy in [(250, 450), (400, 430), (550, 460), (700, 440), (850, 450), (1000, 420)]:
    draw.ellipse([gx - 6, gy - 15, gx + 6, gy - 3], fill=(120, 90, 70))
    draw.rectangle([gx - 4, gy - 3, gx + 4, gy + 15], fill=(100, 80, 60))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Mercado del pueblo", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_mercado.png")

# === CUARTEL ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=False)
ground(img, draw, (55, 55, 45))
# Edificio
draw.rectangle([350, 250, 930, 620], fill=(85, 75, 60))
draw.rectangle([370, 270, 910, 600], fill=(95, 85, 70))
# Puerta
draw.rectangle([580, 480, 700, 620], fill=(60, 50, 40))
# Ventanas con rejas
for x in [400, 500, 780, 880]:
    draw.rectangle([x, 320, x + 60, 400], fill=(120, 140, 160))
    for i in range(4):
        draw.line([(x + i * 15, 320), (x + i * 15, 400)], fill=(80, 80, 80), width=1)
# Bandera
draw.rectangle([920, 230, 925, 250], fill=(60, 50, 40))
draw.polygon([(925, 230), (960, 240), (925, 250)], fill=(200, 50, 50))
draw.polygon([(925, 230), (950, 235), (925, 240)], fill=(220, 220, 220))
# Guardia
draw.ellipse([500, 440, 520, 460], fill=(130, 100, 75))
draw.rectangle([498, 460, 522, 520], fill=(80, 70, 55))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Cuartel de reclutamiento", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_cuartel.png")

# === ESTACIÓN ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (60, 60, 45))
# Edificio de la estación
draw.rectangle([400, 300, 880, 550], fill=(110, 95, 75))
draw.rectangle([420, 320, 860, 530], fill=(120, 105, 85))
# Techo
draw.polygon([(380, 300), (640, 250), (900, 300)], fill=(90, 75, 55))
# Ventanas
for x in [450, 550, 650, 750]:
    draw.rectangle([x, 360, x + 60, 420], fill=(160, 180, 200))
# Puerta
draw.rectangle([600, 460, 680, 550], fill=(70, 55, 40))
# Vías
for i in range(8):
    y = 560 + i * 8
    draw.line([(0, y), (1280, y)], fill=(90, 80, 65), width=2)
# Tren (vagón)
draw.rectangle([200, 500, 400, 560], fill=(80, 70, 55))
draw.rectangle([210, 510, 390, 550], fill=(100, 85, 65))
# Ruedas
for x in [230, 280, 330, 380]:
    draw.ellipse([x, 555, x + 20, 575], fill=(60, 55, 45))
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Estación del ferrocarril", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_estacion.png")

# === SALTO MBOCARUZÚ ===
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)
base_sky(img, draw, warm=True)
ground(img, draw, (45, 60, 38))
# Roca
draw.polygon([(200, 200), (400, 150), (600, 180), (800, 160), (1000, 200), (1080, 620), (200, 620)], fill=(90, 85, 78))  # noqa: E501
draw.polygon([(220, 210), (400, 165), (600, 195), (780, 175), (980, 210), (1060, 600), (220, 600)], fill=(100, 95, 88))  # noqa: E501
# Cascada
draw.rectangle([480, 180, 560, 420], fill=(70, 120, 160))
draw.rectangle([490, 190, 550, 410], fill=(85, 140, 180))
# Espuma
for y in range(380, 430, 5):
    draw.line([(485, y), (555, y)], fill=(200, 220, 240), width=2)
# Pozo
draw.ellipse([460, 410, 580, 470], fill=(60, 100, 140))
draw.ellipse([470, 420, 570, 460], fill=(80, 130, 170))
# Vegetación
draw_trees(draw, [(100, 300), (250, 250), (700, 200), (900, 250), (1100, 300)], 30)
draw_trees(draw, [(150, 450), (300, 480), (800, 470), (950, 500)], 25)
try:
    font = ImageFont.truetype("arial.ttf", 24)
    draw.text((50, 50), "Salto Mbocaruzú", fill=(240, 230, 200), font=font)
except OSError:
    pass
img.save(OUT / "bg_salto.png")

print(f"Fondos guardados en {OUT}")
print(f"Total: {len(list(OUT.glob('*.png')))} imágenes")
