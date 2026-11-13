"""Reloj de simulación (GDD §6).

El día de simulación va de 05:00 a 05:00 del día siguiente. `clock_min`
son los minutos transcurridos desde las 05:00 del día 1 (día 0), así que
el índice de día es simplemente `clock_min // 1440`.

Este módulo es puro: no conoce FastAPI, ni la base de datos, ni el azar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
MINUTES_PER_DAY = MINUTES_PER_HOUR * HOURS_PER_DAY
DAY_START_MINUTE = 5 * MINUTES_PER_HOUR  # 05:00

MANANA = "manana"
TARDE = "tarde"
NOCHE = "noche"

PERIOD_LABELS = {
    MANANA: "Mañana",
    TARDE: "Tarde",
    NOCHE: "Noche",
}

# GDD §6.2: 7 PA de mañana, 7 de tarde, 10 de noche.
PERIOD_PA = {MANANA: 7, TARDE: 7, NOCHE: 10}

WEEKDAY_LABELS = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)


def period_of(minute_of_day: int) -> str:
    """Periodo al que pertenece un minuto del día (0..1439)."""
    if DAY_START_MINUTE <= minute_of_day < 12 * MINUTES_PER_HOUR:
        return MANANA
    if 12 * MINUTES_PER_HOUR <= minute_of_day < 19 * MINUTES_PER_HOUR:
        return TARDE
    return NOCHE


def minute_of_day(clock_min: int) -> int:
    """Hora del día (0..1439) correspondiente al reloj de simulación."""
    return (DAY_START_MINUTE + clock_min % MINUTES_PER_DAY) % MINUTES_PER_DAY


def day_index(clock_min: int) -> int:
    """Día de simulación: 0 es el día que empieza a las 05:00 iniciales."""
    return clock_min // MINUTES_PER_DAY


def minutes_until_day_close(clock_min: int) -> int:
    """Minutos que faltan para el próximo corte de jornada (05:00)."""
    restante = clock_min % MINUTES_PER_DAY
    return MINUTES_PER_DAY - restante


@dataclass(frozen=True)
class Moment:
    """Foto del reloj en un instante concreto."""

    clock_min: int
    day_index: int
    minute_of_day: int
    hour: int
    minute: int
    period: str
    date: date
    weekday: int

    @property
    def period_label(self) -> str:
        return PERIOD_LABELS[self.period]

    @property
    def weekday_label(self) -> str:
        return WEEKDAY_LABELS[self.weekday]

    @property
    def date_label(self) -> str:
        return f"{self.date.day:02d}/{self.date.month:02d}/{self.date.year}"

    @property
    def time_label(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    def to_dict(self) -> dict:
        return {
            "clock_min": self.clock_min,
            "day_index": self.day_index,
            "minute_of_day": self.minute_of_day,
            "hour": self.hour,
            "minute": self.minute,
            "time_label": self.time_label,
            "period": self.period,
            "period_label": self.period_label,
            "date": self.date.isoformat(),
            "date_label": self.date_label,
            "weekday": self.weekday,
            "weekday_label": self.weekday_label,
        }


def moment(clock_min: int, start_date: date) -> Moment:
    """Construye el `Moment` para un reloj y una fecha de inicio."""
    if clock_min < 0:
        raise ValueError("clock_min no puede ser negativo")

    idx = day_index(clock_min)
    mod = clock_min % MINUTES_PER_DAY
    mod_day = (DAY_START_MINUTE + mod) % MINUTES_PER_DAY
    # Después de medianoche (00:00–04:59) el calendario ya avanzó un día,
    # aunque la jornada de simulación todavía no terminó.
    offset = 1 if mod_day < DAY_START_MINUTE else 0
    calendar_date = start_date + timedelta(days=idx + offset)

    return Moment(
        clock_min=clock_min,
        day_index=idx,
        minute_of_day=mod_day,
        hour=mod_day // MINUTES_PER_HOUR,
        minute=mod_day % MINUTES_PER_HOUR,
        period=period_of(mod_day),
        date=calendar_date,
        weekday=calendar_date.weekday(),
    )
