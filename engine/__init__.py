"""Motor de simulación de la novela visual del Chaco.

Python puro y determinista: la API (FastAPI) y los clientes (web y Ren'Py)
sólo leen y escriben estado; las reglas viven acá.
"""

from engine.actions import ActionResult, perform, resolve_event
from engine.clock import (
    DAY_START_MINUTE,
    MANANA,
    MINUTES_PER_DAY,
    NOCHE,
    TARDE,
    Moment,
    day_index,
    moment,
    period_of,
)
from engine.energy import PA_INITIAL, PA_MAX, PA_PER_HOUR
from engine.errors import EngineError
from engine.inventory import Stack
from engine.npc import NpcState
from engine.state import GameState, PlayerState

__all__ = [
    "DAY_START_MINUTE",
    "MANANA",
    "TARDE",
    "NOCHE",
    "MINUTES_PER_DAY",
    "Moment",
    "moment",
    "period_of",
    "day_index",
    "PA_INITIAL",
    "PA_MAX",
    "PA_PER_HOUR",
    "GameState",
    "PlayerState",
    "NpcState",
    "Stack",
    "ActionResult",
    "EngineError",
    "perform",
    "resolve_event",
]
