"""Catálogo de actividades: disponibilidad y validación (GDD §6.5 y §13).

La restricción horaria es sobre la hora de **inicio**. Una actividad puede
terminar en el período siguiente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data.activities import ACTIVITIES, Activity
from data.items import ITEMS
from engine import inventory as inv

if TYPE_CHECKING:  # pragma: no cover
    from engine.state import GameState


def by_id(activity_id: str) -> Activity | None:
    return ACTIVITIES.get(activity_id)


def can_start(state: GameState, activity: Activity) -> tuple[bool, str | None]:
    if not activity.implemented:
        return False, "Todavía no está disponible."

    if state.pending:
        return False, "Hay una escena pendiente de resolver."

    if state.moment().period not in activity.start_periods:
        etiqueta = " / ".join(p.capitalize() for p in activity.start_periods)
        return False, f"Sólo se puede empezar en: {etiqueta}."

    if state.pa < activity.duration_hours:
        return False, f"Necesitás {activity.duration_hours} PA y tenés {state.pa}."

    item_requerido = (activity.requires or {}).get("item")
    if item_requerido:
        dia = state.moment().day_index
        if inv.available_count(state.inventory, item_requerido, dia) <= 0:
            nombre = ITEMS[item_requerido].name
            return False, f"Necesitás {nombre}."

    if activity.kind == "buy" and state.player.money <= 0:
        return False, "No tenés dinero."

    return True, None


def available(state: GameState) -> list[dict]:
    salida = []
    for activity in ACTIVITIES.values():
        puede, motivo = can_start(state, activity)
        salida.append(
            {
                "id": activity.id,
                "name": activity.name,
                "description": activity.description,
                "duration_hours": activity.duration_hours,
                "location": activity.location,
                "kind": activity.kind,
                "implemented": activity.implemented,
                "available": puede,
                "reason": motivo,
            }
        )
    return salida
