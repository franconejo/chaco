"""Precios del almacén (GDD §12).

El catálogo trae un precio de referencia; la coyuntura lo mueve. La escasez no
se simula con una curva: la activa un acontecimiento con una bandera y el
multiplicador vive acá, en una sola función.

Esto mantiene el determinismo: mismo estado + mismas banderas = mismos precios.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data.items import Item

if TYPE_CHECKING:  # pragma: no cover
    from engine.state import GameState

# Banderas que encarecen el almacén.
MULTIPLICADORES: dict[str, float] = {
    "precios_altos": 1.5,
    "sin_provisiones": 2.0,
}


def multiplier(state: GameState) -> float:
    from engine import difficulty as diff

    valor = diff.price_multiplier(state.difficulty)
    for flag, factor in MULTIPLICADORES.items():
        if flag in state.flags:
            valor *= factor
    return round(valor, 3)


def price_of(state: GameState, item: Item) -> int:
    """Precio efectivo. Nunca baja de 1 peso si el objeto se vende."""
    if item.price <= 0:
        return 0
    return max(1, round(item.price * multiplier(state)))


def is_expensive(state: GameState) -> bool:
    return multiplier(state) > 1.0
