"""Puntos de acción (PA) — modelo literal del GDD §6 y §7.

Reglas implementadas tal como están escritas:

* 1 hora de actividad = 1 PA; la duración y el coste son la misma magnitud.
* El día tiene 24 horas = 24 PA. Tope de acumulación: 24.
* Los PA **no se recargan solos al cambiar de período ni al cambiar de día**.
  Sólo se recuperan durmiendo, comiendo o bebiendo.
* La recuperación no detiene el reloj: el tiempo de la actividad se
  contabiliza igual.

Consecuencia conocida (aceptada en diseño): como el tope es 24 y la jornada
también aporta 24 horas, en la práctica los PA dejan de ser un limitante una
vez que el personaje duerme y come con regularidad. El reloj sigue siendo el
límite real. Ver `docs/DECISIONES.md`.
"""

from __future__ import annotations

PA_MAX = 24
PA_INITIAL = 24
PA_PER_HOUR = 1

# Recuperación por PA invertido (GDD §7.1–7.3).
PA_RECOVERY_SLEEP = 2
PA_RECOVERY_EAT = 3
PA_RECOVERY_DRINK = 3


def clamp_pa(value: int) -> int:
    return max(0, min(PA_MAX, value))


def spend(pa: int, amount: int) -> int:
    """Descuenta PA. No valida: quien llama debe haber comprobado el saldo."""
    return clamp_pa(pa - amount)


def recover(pa: int, amount: int) -> int:
    """Suma PA respetando el tope de 24."""
    return clamp_pa(pa + amount)


# Umbral de saciedad: por encima de esto no hay sed y beber no rinde.
# Junto con el tope de 3 comidas diarias evita las explotaciones obvias
# sin apartarse del modelo literal del GDD.
THIRST_THRESHOLD = 95.0
