"""Necesidades físicas del protagonista (GDD §8).

Funciones puras sobre `PlayerState`: no manejan reloj ni persistencia, sólo
aplican deltas y recortan los valores a su rango válido.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - sólo para tipado
    from engine.state import PlayerState

# Escalas
HYDRATION_MAX = 100.0
NUTRITION_MAX = 100.0
FATIGUE_MAX = 100.0
HEALTH_MAX = 100.0
HYGIENE_MAX = 100.0
ATTRIBUTE_MAX = 100.0

# Desgaste por hora despierto (valores base, ajustables por esfuerzo/clima)
HYDRATION_PER_HOUR = 2.5
NUTRITION_PER_HOUR = 1.5
FATIGUE_PER_HOUR = 1.2
HYGIENE_PER_HOUR = 0.6

# Desgaste mientras duerme
SLEEP_HYDRATION_PER_HOUR = 1.0
SLEEP_NUTRITION_PER_HOUR = 0.8
SLEEP_FATIGUE_RECOVERY_PER_HOUR = 12.0

# GDD §8.3: tabla de sueño
MIN_SLEEP_HOURS = 3
SLEEP_HEALTH_PENALTY = {0: 15.0, 1: 10.0, 2: 5.0}
SLEEP_FATIGUE_PENALTY = {0: 30.0, 1: 20.0, 2: 10.0}
# Noches cortas consecutivas: castigo acumulado adicional.
SLEEP_DEBT_MAX_EXTRA = 4
SLEEP_DEBT_HEALTH_PENALTY = 3.0
SLEEP_DEBT_FATIGUE_PENALTY = 5.0


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def fatigue_recovery_multiplier(hours: float) -> float:
    """GDD §8.3: 4–5 h recuperan más fatiga; 6 h o más rinden menos."""
    if hours >= 6:
        return 0.75
    if hours >= 4:
        return 1.25
    return 1.0


def health_drift_per_hour(player: PlayerState) -> float:
    """Deriva lenta de salud según el estado físico actual."""
    drift = 0.0
    if player.hydration < 20:
        drift -= 1.5
    elif player.hydration < 40:
        drift -= 0.4

    if player.nutrition < 15:
        drift -= 1.0
    elif player.nutrition < 35:
        drift -= 0.3

    if player.fatigue > 90:
        drift -= 0.5

    if (
        player.hydration >= 60
        and player.nutrition >= 60
        and player.fatigue <= 40
        and player.health < HEALTH_MAX
    ):
        drift += 0.15
    return drift


def tick_awake(
    player: PlayerState,
    minutes: int,
    *,
    exertion: float = 1.0,
    temperature: float = 1.0,
    difficulty: int = 1,
) -> None:
    """Desgaste por estar despierto/activo durante `minutes`."""
    from engine import difficulty as diff

    hours = minutes / 60.0
    exertion = max(0.0, exertion)
    temperature = max(0.0, temperature)
    factor = diff.needs_decay(difficulty)

    player.hydration = clamp(
        player.hydration - HYDRATION_PER_HOUR * exertion * temperature * hours * factor,
        0,
        HYDRATION_MAX,
    )
    player.nutrition = clamp(
        player.nutrition - NUTRITION_PER_HOUR * (0.8 + 0.2 * exertion) * hours * factor,
        0,
        NUTRITION_MAX,
    )
    player.fatigue = clamp(
        player.fatigue + FATIGUE_PER_HOUR * exertion * hours * factor, 0, FATIGUE_MAX
    )
    player.hygiene = clamp(player.hygiene - HYGIENE_PER_HOUR * hours * factor, 0, HYGIENE_MAX)
    player.health = clamp(
        player.health + health_drift_per_hour(player) * hours, 0, HEALTH_MAX
    )


def tick_sleep(player: PlayerState, minutes: int, *, fatigue_per_hour: float) -> None:
    """Desgaste y recuperación mientras duerme."""
    hours = minutes / 60.0

    player.hydration = clamp(
        player.hydration - SLEEP_HYDRATION_PER_HOUR * hours, 0, HYDRATION_MAX
    )
    player.nutrition = clamp(
        player.nutrition - SLEEP_NUTRITION_PER_HOUR * hours, 0, NUTRITION_MAX
    )
    player.fatigue = clamp(
        player.fatigue - max(0.0, fatigue_per_hour) * hours, 0, FATIGUE_MAX
    )
    player.health = clamp(
        player.health + health_drift_per_hour(player) * hours, 0, HEALTH_MAX
    )


def day_close_consequences(hours_slept: float, sleep_debt_days: int) -> dict:
    """Consecuencias al cerrar la jornada (05:00).

    Devuelve deltas de salud/fatiga y el nuevo contador de deuda de sueño.
    """
    hours_slept = max(0.0, hours_slept)
    health_delta = 0.0
    fatigue_delta = 0.0
    debt = sleep_debt_days

    if hours_slept < MIN_SLEEP_HOURS:
        tramo = int(hours_slept)  # 0, 1 o 2
        health_delta -= SLEEP_HEALTH_PENALTY.get(tramo, 0.0)
        fatigue_delta += SLEEP_FATIGUE_PENALTY.get(tramo, 0.0)
        debt += 1
        if debt >= 2:
            extra = min(debt - 1, SLEEP_DEBT_MAX_EXTRA)
            health_delta -= SLEEP_DEBT_HEALTH_PENALTY * extra
            fatigue_delta += SLEEP_DEBT_FATIGUE_PENALTY * extra
    else:
        debt = 0

    return {
        "hours_slept": round(hours_slept, 3),
        "health_delta": round(health_delta, 3),
        "fatigue_delta": round(fatigue_delta, 3),
        "sleep_debt_days": debt,
        "penalized": hours_slept < MIN_SLEEP_HOURS,
    }
