"""Genera retratos mejorados para el cliente Ren'Py (Fase 4).

Retratos estilizados con rostro, ropa y accesorios. Sirven como placeholder
mientras no haya arte definitivo de itch.io.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("C:/visualnovel/renpy/game/images")
OUT.mkdir(parents=True, exist_ok=True)

W, H = 300, 400

try:
    font_large = ImageFont.truetype("arial.ttf", 100)
    font_small = ImageFont.truetype("arial.ttf", 16)
except OSError:
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()


def draw_face(draw, cx, cy, skin, hair, eye_color, has_hat=False, hat_color=None):
    """Dibuja un rostro estilizado."""
    # Cabeza
    draw.ellipse([cx - 45, cy - 55, cx + 45, cy + 55], fill=skin)
    # Cabello
    draw.ellipse([cx - 50, cy - 70, cx + 50, cy - 10], fill=hair)
    draw.rectangle([cx - 50, cy - 70, cx + 50, cy - 30], fill=hair)
    # Ojos
    draw.ellipse([cx - 25, cy - 10, cx - 12, cy + 5], fill=(255, 255, 255))
    draw.ellipse([cx + 12, cy - 10, cx + 25, cy + 5], fill=(255, 255, 255))
    draw.ellipse([cx - 20, cy - 6, cx - 15, cy + 1], fill=eye_color)
    draw.ellipse([cx + 15, cy - 6, cx + 20, cy + 1], fill=eye_color)
    # Nariz
    draw.line([(cx, cy + 5), (cx - 3, cy + 15), (cx + 3, cy + 15)], fill=(skin[0] - 30, skin[1] - 30, skin[2] - 30), width=1)
    # Boca
    draw.arc([cx - 12, cy + 18, cx + 12, cy + 30], 0, 180, fill=(120, 60, 60), width=2)
    # Sombrero (opcional)
    if has_hat and hat_color:
        draw.ellipse([cx - 55, cy - 75, cx + 55, cy - 45], fill=hat_color)
        draw.rectangle([cx - 60, cy - 60, cx + 60, cy - 45], fill=hat_color)


def draw_body(draw, cx, cy, body_color, collar_color=None):
    """Dibuja el cuerpo/cuello."""
    # Cuello
    draw.rectangle([cx - 12, cy + 50, cx + 12, cy + 75], fill=(200, 170, 140))
    # Hombros/ropa
    draw.rectangle([cx - 70, cy + 70, cx + 70, cy + 180], fill=body_color)
    # Cuello de camisa
    if collar_color:
        draw.polygon([(cx - 15, cy + 70), (cx, cy + 90), (cx + 15, cy + 70)], fill=collar_color)


# Personajes: (id, skin, hair, eye, body, collar, hat, hat_color, gender)
PERSONAJES = [
    ("juana", (210, 175, 145), (60, 40, 25), (60, 40, 20), (160, 120, 80), (200, 180, 160), False, None, "f"),
    ("celia", (200, 165, 135), (40, 30, 20), (50, 35, 25), (120, 100, 140), (180, 170, 160), False, None, "f"),
    ("aurora", (220, 185, 155), (180, 140, 80), (70, 50, 30), (180, 140, 100), (210, 190, 170), False, None, "f"),
    ("aurelio", (195, 160, 130), (80, 55, 30), (60, 40, 20), (100, 80, 60), (170, 150, 130), False, None, "m"),
    ("ramon", (180, 150, 120), (90, 70, 45), (50, 35, 20), (80, 70, 60), (160, 150, 140), True, (60, 50, 40), "m"),
    ("ursula", (170, 140, 110), (100, 80, 55), (40, 30, 20), (90, 100, 70), (180, 170, 150), True, (50, 60, 40), "f"),
    ("nicanor", (190, 155, 125), (70, 50, 30), (50, 40, 25), (90, 95, 110), (170, 160, 150), False, None, "m"),
    ("vera", (185, 150, 120), (50, 40, 25), (40, 30, 20), (70, 80, 60), (160, 155, 145), True, (80, 70, 50), "m"),
    ("padre_ignacio", (175, 145, 115), (120, 100, 70), (50, 40, 25), (60, 55, 50), (180, 175, 165), False, None, "m"),
    ("dona_mercedes", (195, 160, 130), (60, 45, 30), (50, 35, 20), (140, 100, 120), (190, 180, 170), False, None, "f"),
    ("teniente_ortega", (190, 155, 125), (40, 30, 20), (40, 30, 20), (60, 70, 85), (170, 165, 155), True, (70, 60, 50), "m"),
    ("protagonista", (200, 165, 135), (70, 50, 30), (50, 35, 20), (130, 100, 70), (180, 170, 155), False, None, "m"),
]

for pid, skin, hair, eye, body, collar, has_hat, hat_color, gender in PERSONAJES:
    img = Image.new("RGB", (W, H), (40, 35, 30))
    draw = ImageDraw.Draw(img)

    # Fondo con gradiente
    for y in range(H):
        t = y / H
        r = int(35 + 15 * t)
        g = int(30 + 15 * t)
        b = int(25 + 15 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Cuerpo
    draw_body(draw, W // 2, 180, body, collar)
    # Rostro
    draw_face(draw, W // 2, 120, skin, hair, eye, has_hat, hat_color)

    # Nombre abajo
    try:
        draw.text((10, H - 25), pid.replace("_", " ").title(), fill=(180, 170, 150), font=font_small)
    except Exception:
        pass

    img.save(OUT / f"{pid}.png")
    print(f"  {pid}.png")

print(f"Listo: {len(PERSONAJES)} retratos en {OUT}")
