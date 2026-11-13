"""Motor de acontecimientos (GDD §14).

Un acontecimiento se dispara cuando se cumplen sus condiciones. Si tiene
opciones queda **pendiente** y bloquea nuevas acciones hasta que el jugador
elija: es una escena, no un aviso de fondo. Los que no tienen opciones se
resuelven solos y quedan en el registro.

Algunas escenas cuestan tiempo (`time_cost`): la tarde que pasás en un velorio
o la mañana que perdés en el cuartel se descuentan del reloj. Ese avance no
dispara otros acontecimientos (`queue=False`) para no encadenar escenas dentro
de una escena.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data import events as event_catalog
from data.events import Choice, EventDef
from engine import effects
from engine import inventory as inv
from engine import npc as npc_runtime
from engine.errors import EngineError
from engine.rng import GameRandom

if TYPE_CHECKING:  # pragma: no cover
    from engine.state import GameState

MAX_PENDING = 3
MAX_FIRES_PER_TICK = 1


# ---------- lectura de estado ----------


def stat_value(state: GameState, key: str) -> float | None:
    """Resuelve una clave de condición a un número.

    Claves soportadas: `pa`, `days`, `suspicion`, `credibility`, `item:<id>`,
    `npc:<id>:<campo>` y cualquier campo del jugador (`health`, `fatigue`, …).
    """
    if key.startswith("item:"):
        item_id = key.split(":", 1)[1]
        return float(
            inv.available_count(
                state.inventory, item_id, state.moment().day_index
            )
        )
    if key.startswith("npc:"):
        partes = key.split(":")
        if len(partes) != 3:
            return None
        _, npc_id, campo = partes
        estado = npc_runtime.ensure(state, npc_id)
        if not hasattr(estado, campo):
            return None
        return float(getattr(estado, campo))
    if key == "pa":
        return float(state.pa)
    if key in ("days", "closed_days"):
        return float(state.closed_days)
    if key in ("suspicion", "credibility"):
        return float(state.identity.get(key, 0.0))
    if hasattr(state.player, key):
        return float(getattr(state.player, key))
    return None


def _in_range(value: float | None, rango: list | tuple) -> bool:
    if value is None:
        return False
    minimo, maximo = (list(rango) + [None, None])[:2]
    if minimo is not None and value < float(minimo):
        return False
    if maximo is not None and value > float(maximo):
        return False
    return True


def choice_available(state: GameState, choice: Choice) -> bool:
    if choice.requires_flags and not set(choice.requires_flags) <= set(state.flags):
        return False
    dia = state.moment().day_index
    for item_id, cantidad in choice.requires_items:
        if inv.available_count(state.inventory, item_id, dia) < cantidad:
            return False
    return True


def available_choices(state: GameState, ev: EventDef) -> list[Choice]:
    return [choice for choice in ev.choices if choice_available(state, choice)]


# ---------- condiciones ----------


def conditions_ok(state: GameState, ev: EventDef, rng: GameRandom) -> bool:
    ahora = state.moment()

    if ev.once and ev.id in state.fired:
        return False
    if ahora.day_index < ev.day_min:
        return False
    if ev.day_max is not None and ahora.day_index > ev.day_max:
        return False
    if ev.periods and ahora.period not in ev.periods:
        return False
    if ev.locations and state.location not in ev.locations:
        return False
    if ev.requires_flags and not set(ev.requires_flags) <= set(state.flags):
        return False
    if ev.any_flags and not set(ev.any_flags) & set(state.flags):
        return False
    if ev.forbids_flags and set(ev.forbids_flags) & set(state.flags):
        return False
    if ev.requires_events and not set(ev.requires_events) <= set(state.fired):
        return False

    # Si todas las opciones dependen de algo que el jugador no tiene, el evento
    # no puede presentarse: sería una escena sin salida.
    if ev.choices and not available_choices(state, ev):
        return False

    ultimo = state.event_history.get(ev.id)
    if ultimo is not None and ev.cooldown_days:
        if state.clock_min - ultimo < ev.cooldown_days * 24 * 60:
            return False

    for clave, rango in (ev.conditions or {}).items():
        if not _in_range(stat_value(state, clave), rango):
            return False

    if ev.chance < 1.0:
        if not rng.chance(ev.chance, ev.id, ahora.day_index, ahora.hour):
            return False

    return True


# ---------- disparo ----------


def collect(state: GameState) -> list[dict]:
    """Dispara como mucho un acontecimiento por avance de tiempo."""
    if state.pending:
        return []

    rng = GameRandom(state.seed)
    candidatos = [
        ev for ev in event_catalog.EVENTS.values() if conditions_ok(state, ev, rng)
    ]
    if not candidatos:
        return []
    candidatos.sort(key=lambda ev: (-ev.priority, ev.id))

    disparados = []
    for ev in candidatos[:MAX_FIRES_PER_TICK]:
        disparados.append(fire(state, ev))
    return disparados


def fire(state: GameState, ev: EventDef) -> dict:
    state.event_history[ev.id] = state.clock_min
    if ev.id not in state.fired:
        state.fired.append(ev.id)

    cambios = effects.apply(state, ev.effects)
    opciones = available_choices(state, ev)

    # Con opciones, el tiempo se cobra al resolver la escena; sin opciones, acá.
    if ev.time_cost and not opciones:
        state.advance(ev.time_cost, exertion=1.0, queue=False)

    entrada = {
        "id": ev.id,
        "title": ev.title,
        "text": ev.text,
        "priority": ev.priority,
        "clock_min": state.clock_min,
        "changes": cambios,
        "time_cost": ev.time_cost,
    }

    if opciones:
        entrada["uid"] = f"{ev.id}:{state.clock_min}"
        entrada["choices"] = [
            {"id": c.id, "text": c.text} for c in opciones
        ]
        state.pending.append(entrada)
        state.log.append(
            {
                "kind": "event_pending",
                "id": ev.id,
                "title": ev.title,
                "clock_min": state.clock_min,
            }
        )
    else:
        state.log.append(
            {
                "kind": "event",
                "id": ev.id,
                "title": ev.title,
                "text": ev.text,
                "clock_min": state.clock_min,
            }
        )
    return entrada


def resolve(state: GameState, uid: str, choice_id: str) -> dict:
    entrada = next((item for item in state.pending if item.get("uid") == uid), None)
    if entrada is None:
        raise EngineError("evento_inexistente", "Esa escena ya no está pendiente.")

    ev = event_catalog.get(entrada["id"])
    opcion: Choice | None = next((c for c in ev.choices if c.id == choice_id), None)
    if opcion is None:
        raise EngineError("opcion_invalida", "Esa opción no existe en la escena.")
    if not choice_available(state, opcion):
        raise EngineError(
            "opcion_no_disponible",
            "No tenés lo necesario para elegir esa opción.",
        )

    state.pending.remove(entrada)
    cambios = effects.apply(state, opcion.effects)

    cerrados: list[dict] = []
    if ev.time_cost:
        cerrados = state.advance(ev.time_cost, exertion=1.0, queue=False)

    state.log.append(
        {
            "kind": "event_choice",
            "id": ev.id,
            "choice": opcion.id,
            "text": opcion.text,
            "clock_min": state.clock_min,
            "changes": cambios,
        }
    )
    return {
        "event": {
            "id": ev.id,
            "title": ev.title,
            "choice": opcion.id,
            "text": opcion.text,
            "time_cost": ev.time_cost,
        },
        "changes": cambios,
        "days_closed": cerrados,
    }


def pending_view(state: GameState) -> list[dict]:
    salida = []
    for item in state.pending:
        ev = event_catalog.EVENTS.get(item["id"])
        opciones = available_choices(state, ev) if ev else []
        salida.append(
            {
                "uid": item.get("uid"),
                "id": item["id"],
                "title": item["title"],
                "text": item["text"],
                "time_cost": item.get("time_cost", 0),
                "choices": [
                    {"id": c.id, "text": c.text} for c in opciones
                ],
            }
        )
    return salida
