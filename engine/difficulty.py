"""Dificultad del juego (Fase 5).

Afecta el desgaste de necesidades, los precios y el dinero inicial. El motor
lee `state.difficulty` (0=fácil, 1=normal, 2=difícil) y aplica los
multiplicadores correspondientes. Todo lo demás (reglas, eventos) sigue igual.
"""

from __future__ import annotations

# 0 = fácil, 1 = normal, 2 = difícil
DIFFICULTY_LABELS = {0: "Fácil", 1: "Normal", 2: "Difícil"}

# Multiplicador de desgaste de necesidades por hora.
NEEDS_DECAY: dict[int, float] = {0: 0.7, 1: 1.0, 2: 1.3}

# Multiplicador de precios del almacén.
PRICE_MULTIPLIER: dict[int, float] = {0: 0.8, 1: 1.0, 2: 1.2}

# Dinero inicial.
STARTING_MONEY: dict[int, int] = {0: 8, 1: 5, 2: 3}

# PA inicial de la jornada.
STARTING_PA: dict[int, int] = {0: 24, 1: 24, 2: 20}

# Multiplicador de probabilidad de eventos negativos.
NEGATIVE_EVENT_CHANCE: dict[int, float] = {0: 0.7, 1: 1.0, 2: 1.3}

# Días consecutivos con salud en 0 antes de morir.
# 0 = difícil: muerte inmediata al llegar a 0.
DEATH_THRESHOLD: dict[int, int] = {0: 2, 1: 1, 2: 0}


def label(difficulty: int) -> str:
    return DIFFICULTY_LABELS.get(difficulty, "Normal")


def needs_decay(difficulty: int) -> float:
    return NEEDS_DECAY.get(difficulty, 1.0)


def price_multiplier(difficulty: int) -> float:
    return PRICE_MULTIPLIER.get(difficulty, 1.0)


def starting_money(difficulty: int) -> int:
    return STARTING_MONEY.get(difficulty, 5)


def starting_pa(difficulty: int) -> int:
    return STARTING_PA.get(difficulty, 24)


def death_threshold(difficulty: int) -> int:
    return DEATH_THRESHOLD.get(difficulty, 2)
