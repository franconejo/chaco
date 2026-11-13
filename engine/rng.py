"""Azar determinista (GDD §18).

Toda tirada del juego pasa por acá. La semilla vive en el estado de la partida
y el flujo se deriva por etiqueta, de modo que repetir la misma partida con la
misma semilla da exactamente los mismos resultados, aunque cambie el orden en
que se consultan los sistemas.
"""

from __future__ import annotations

import hashlib
import random


class GameRandom:
    """Generador estable derivado de (semilla, etiqueta, contador)."""

    def __init__(self, seed: int):
        self.seed = seed

    def _rng(self, *parts: object) -> random.Random:
        clave = "|".join([str(self.seed), *map(str, parts)])
        digest = hashlib.blake2b(clave.encode("utf-8"), digest_size=8).digest()
        return random.Random(int.from_bytes(digest, "big"))

    def chance(self, probability: float, *parts: object) -> bool:
        return self._rng(*parts).random() < probability

    def randint(self, low: int, high: int, *parts: object) -> int:
        return self._rng(*parts).randint(low, high)

    def choice(self, options: list, *parts: object):
        return self._rng(*parts).choice(options)
