"""Acciones del jugador (GDD §13).

Todas las acciones pasan por `perform`, que valida, gasta PA, mueve el reloj y
devuelve un resultado serializable. La API no contiene reglas: sólo llama acá.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from data import items as item_catalog
from data import npcs as npc_catalog
from engine import activities as activity_runtime
from engine import effects, energy, events, needs, prices
from engine import inventory as inv
from engine import npc as npc_runtime
from engine.energy import THIRST_THRESHOLD
from engine.errors import EngineError
from engine.state import GameState

MAX_MEALS_PER_DAY = 3
MAX_DRINKS_PER_DAY = 8
MAX_ACTION_HOURS = 12
MAX_BUY_QTY = 20

SLEEP = "sleep"
EAT = "eat"
DRINK = "drink"
WAIT = "wait"
ACTIVITY = "activity"
BUY = "buy"
VISIT = "visit"


@dataclass
class ActionResult:
    action: str
    minutes: int
    pa_before: int
    pa_after: int
    messages: list[str] = field(default_factory=list)
    deltas: dict = field(default_factory=dict)
    days_closed: list[dict] = field(default_factory=list)
    fired_events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "minutes": self.minutes,
            "pa_before": self.pa_before,
            "pa_after": self.pa_after,
            "messages": self.messages,
            "deltas": self.deltas,
            "days_closed": self.days_closed,
            "fired_events": [
                {k: v for k, v in evento.items() if k in ("id", "title", "uid")}
                for evento in self.fired_events
            ],
        }


def perform(state: GameState, action: str, params: dict) -> ActionResult:
    from engine import difficulty as diff

    # En difícil, morir en cuanto la salud llega a 0.
    if diff.death_threshold(state.difficulty) == 0 and state.player.health <= 0:
        if "muerto" not in state.flags:
            state.flags.append("muerto")

    if "muerto" in state.flags:
        raise EngineError(
            "muerto",
            "El cuerpo no aguantó más. La partida terminó.",
        )
    if state.pending:
        raise EngineError(
            "escena_pendiente",
            "Hay una escena pendiente: resolvela antes de seguir con el día.",
        )

    _begin(state)

    if action == SLEEP:
        return sleep(state, _hours(params))
    if action == EAT:
        return eat(state, _str(params.get("item")) or None)
    if action == DRINK:
        return drink(state, _str(params.get("item")) or None)
    if action == WAIT:
        return wait(state, _hours(params))
    if action == ACTIVITY:
        return do_activity(state, _str(params.get("activity")) or "", params)
    if action == BUY:
        return buy(state, _str(params.get("item")) or "", _qty(params))
    if action == VISIT:
        return visit(state, _str(params.get("npc")) or "")

    raise EngineError("accion_invalida", f"Acción desconocida: {action}")


# ---------- helpers ----------


def _hours(params: dict) -> int:
    valor = params.get("hours")
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _qty(params: dict) -> int:
    valor = params.get("qty") or 1
    try:
        return max(1, min(MAX_BUY_QTY, int(valor)))
    except (TypeError, ValueError):
        return 1


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def _check_hours(hours: int) -> None:
    if hours < 1 or hours > MAX_ACTION_HOURS:
        raise EngineError(
            "horas_invalidas", f"Se permiten entre 1 y {MAX_ACTION_HOURS} horas."
        )


def _begin(state: GameState, location: str | None = None) -> None:
    """Inicio de acción: llegar al lugar y ver si algo interrumpe.

    Las escenas se evalúan también al llegar, no sólo al terminar la actividad:
    si no, una jornada larga se come la ventana horaria del acontecimiento y
    éste nunca ocurre.
    """
    if state.pending:
        raise EngineError(
            "escena_pendiente",
            "Hay una escena pendiente: resolvela antes de seguir con el día.",
        )
    if location:
        state.location = location
    state.queue_events()
    if state.pending:
        raise EngineError(
            "escena_pendiente",
            "Te interrumpen antes de actuar: resolvé la escena pendiente.",
        )


def _spend(state: GameState, cost: int) -> None:
    if state.pa < cost:
        _collapse(state)
        detalle = state.collapse_messages.pop() if state.collapse_messages else ""
        raise EngineError(
            "sin_pa",
            f"Sin PA: te desplomás. {detalle}" if detalle else "Sin PA.",
        )
    state.pa = energy.clamp_pa(state.pa - cost)
    if state.pa == 0:
        _collapse(state)


def _recover(state: GameState, amount: int) -> None:
    state.pa = energy.recover(state.pa, max(0, amount))


def _collapse(state: GameState) -> None:
    """Castigo por quedarse sin PA: el cuerpo y la reputación acusan.

    Se aplica una sola vez por episodio de PA=0 (ver `pa_collapse_applied`).
    """
    if state.pa_collapse_applied:
        return
    p = state.player
    p.health = max(0.0, p.health - 8.0)
    p.hydration = max(0.0, p.hydration - 15.0)
    p.nutrition = max(0.0, p.nutrition - 15.0)
    p.hygiene = max(0.0, p.hygiene - 20.0)
    p.fatigue = min(100.0, p.fatigue + 20.0)
    p.strength = max(0.0, p.strength - 2.0)
    p.stamina = max(0.0, p.stamina - 2.0)
    p.knowledge = max(0.0, p.knowledge - 1.0)
    p.reputation = max(0.0, p.reputation - 3.0)
    state.identity["suspicion"] = min(100.0, state.identity.get("suspicion", 0.0) + 5.0)
    state.identity["credibility"] = max(0.0, state.identity.get("credibility", 100.0) - 5.0)
    robado = min(3, p.money)
    p.money = max(0, p.money - robado)
    state.pa_collapse_applied = True
    # El colapso te cuesta una hora: el tiempo pasa y recuperás 1 PA.
    state.advance(60, exertion=1.0, queue=False)
    state.pa = energy.clamp_pa(state.pa + 1)
    state.collapse_messages.append(
        "Te desplomás sin PA: salud, hidratación, nutrición e higiene bajan; "
        "la fatiga sube; fuerza, resistencia, conocimiento y reputación caen; "
        "la sospecha sube, la credibilidad baja"
        + (f" y te roban {robado} peso(s)." if robado else ".")
        + " Perdés 1 hora y recuperás 1 PA."
    )
    state.log.append(
        {
            "kind": "collapse",
            "clock_min": state.clock_min,
            "robado": robado,
            "message": state.collapse_messages[-1],
        }
    )


def _finish(
    state: GameState,
    action: str,
    minutes: int,
    pa_before: int,
    messages: list[str],
    *,
    deltas: dict | None = None,
    days_closed: list[dict] | None = None,
) -> ActionResult:
    # Si hubo colapso por quedarse sin PA, se avisa en el resultado.
    if state.collapse_messages:
        messages = list(state.collapse_messages) + list(messages)
        state.collapse_messages = []
    return ActionResult(
        action=action,
        minutes=minutes,
        pa_before=pa_before,
        pa_after=state.pa,
        messages=messages,
        deltas=deltas or {},
        days_closed=days_closed or [],
        fired_events=state.take_fired(),
    )


def _day(state: GameState) -> int:
    return state.moment().day_index


# ---------- acciones básicas ----------


def sleep(state: GameState, hours: int) -> ActionResult:
    _check_hours(hours)
    before = state.pa
    # La recuperación siempre supera al coste (×2 vs ×1): si te quedás sin PA,
    # dormir sigue siendo posible y es la salida del callejón sin salida.
    state.pa = energy.clamp_pa(
        state.pa - hours + energy.PA_RECOVERY_SLEEP * hours
    )
    if state.pa > 0:
        state.pa_collapse_applied = False

    rate = needs.SLEEP_FATIGUE_RECOVERY_PER_HOUR * needs.fatigue_recovery_multiplier(hours)
    cerrados = state.advance(hours * 60, mode="sleep", sleep_rate=rate)

    mensajes = [f"Dormiste {hours} hora(s)."]
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state, SLEEP, hours * 60, before, mensajes, deltas={"sleep_hours": hours}
    )


def eat(state: GameState, item_id: str | None = None) -> ActionResult:
    if state.player.meals_today >= MAX_MEALS_PER_DAY:
        raise EngineError(
            "sin_apetito",
            f"Ya comiste {MAX_MEALS_PER_DAY} veces hoy; no podés seguir comiendo.",
        )

    dia = _day(state)
    elegido = item_id or inv.best_food(state.inventory, dia)
    if not elegido:
        raise EngineError(
            "sin_comida", "No tenés comida. Podés comprar en el almacén."
        )

    item = item_catalog.ITEMS.get(elegido)
    if item is None:
        raise EngineError("objeto_desconocido", f"No existe el objeto {elegido}.")
    if item.category != "alimento":
        raise EngineError("no_comestible", f"{item.name} no se come.")
    if inv.available_count(state.inventory, elegido, dia) <= 0:
        raise EngineError("sin_comida", f"No te queda {item.name}.")

    before = state.pa
    # Comer siempre recupera más PA de los que cuesta: si te quedás sin, comer
    # es la salida. Se aplica el neto de una vez para evitar el callejón.
    state.pa = energy.clamp_pa(state.pa - 1 + energy.PA_RECOVERY_EAT)
    if state.pa > 0:
        state.pa_collapse_applied = False

    inv.remove(state.inventory, elegido, 1)
    state.player.nutrition = max(
        0.0, min(100.0, state.player.nutrition + item.nutrition)
    )
    state.player.meals_today += 1

    cerrados = state.advance(60)
    mensajes = [f"Comiste {item.name}."]
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state,
        EAT,
        60,
        before,
        mensajes,
        deltas={
            "item": elegido,
            "nutrition": round(item.nutrition, 3),
            "pa_recovered": energy.PA_RECOVERY_EAT,
        },
        days_closed=cerrados,
    )


def drink(state: GameState, item_id: str | None = None) -> ActionResult:
    if state.player.hydration >= THIRST_THRESHOLD:
        raise EngineError(
            "sin_sed", "No tenés sed: beber ahora no te daría energía."
        )
    if state.player.drinks_today >= MAX_DRINKS_PER_DAY:
        raise EngineError("limite_bebida", "Ya bebiste bastante por hoy.")

    dia = _day(state)
    elegido = item_id or "agua"
    item = item_catalog.ITEMS.get(elegido)
    if item is None:
        raise EngineError("objeto_desconocido", f"No existe el objeto {elegido}.")
    if item.category != "bebida":
        raise EngineError("no_bebible", f"{item.name} no se bebe.")
    if inv.available_count(state.inventory, elegido, dia) <= 0:
        raise EngineError(
            "sin_agua", "No tenés agua. Podés buscarla en el pozo."
        )

    before = state.pa
    state.pa = energy.clamp_pa(state.pa - 1 + energy.PA_RECOVERY_DRINK)
    if state.pa > 0:
        state.pa_collapse_applied = False

    inv.remove(state.inventory, elegido, 1)
    state.player.hydration = min(
        100.0, state.player.hydration + item.hydration
    )
    state.player.drinks_today += 1

    cerrados = state.advance(60)
    mensajes = [f"Bebiste {item.name}."]
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state,
        DRINK,
        60,
        before,
        mensajes,
        deltas={
            "item": elegido,
            "hydration": round(item.hydration, 3),
            "pa_recovered": energy.PA_RECOVERY_DRINK,
        },
        days_closed=cerrados,
    )


def wait(state: GameState, hours: int) -> ActionResult:
    _check_hours(hours)
    before = state.pa
    _spend(state, hours)
    cerrados = state.advance(hours * 60)
    mensajes = [f"Dejaste pasar {hours} hora(s)."]
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state, WAIT, hours * 60, before, mensajes, days_closed=cerrados
    )


# ---------- actividades ----------


def do_activity(state: GameState, activity_id: str, params: dict) -> ActionResult:
    actividad = activity_runtime.by_id(activity_id)
    if actividad is None:
        raise EngineError(
            "actividad_inexistente", f"No existe la actividad {activity_id}."
        )

    if actividad.kind == "buy":
        return buy(state, _str(params.get("item")) or "", _qty(params))
    if actividad.kind == "visit":
        return visit(state, _str(params.get("npc")) or "")

    puede, motivo = activity_runtime.can_start(state, actividad)
    if not puede:
        raise EngineError("no_disponible", motivo or "No podés hacer eso ahora.")

    _begin(state, actividad.location)

    before = state.pa
    _spend(state, actividad.duration_hours)
    cerrados = state.advance(actividad.duration_hours * 60, exertion=actividad.exertion)

    cambios = effects.apply(state, actividad.effects)
    if actividad.location:
        state.location = actividad.location

    mensajes = [f"{actividad.name}: {actividad.duration_hours} hora(s)."]
    if cambios.get("money"):
        mensajes.append(f"Ganaste {int(cambios['money'])} peso(s).")
    if activity_id == "buscar_agua":
        mensajes.append("Llenaste el balde: +2 aguas.")
    if activity_id == "comer":
        mensajes.append("Usá la acción de comer para alimentarte.")
    mensajes.extend(registro["message"] for registro in cerrados)

    return _finish(
        state,
        ACTIVITY,
        actividad.duration_hours * 60,
        before,
        mensajes,
        deltas={k: v for k, v in cambios.items() if not k.startswith("inv:")},
        days_closed=cerrados,
    )


def buy(state: GameState, item_id: str, qty: int = 1) -> ActionResult:
    item = item_catalog.ITEMS.get(item_id)
    if item is None:
        raise EngineError("objeto_desconocido", f"No existe el objeto {item_id}.")
    if item.price <= 0:
        raise EngineError("no_vendible", f"{item.name} no está a la venta.")

    qty = max(1, min(MAX_BUY_QTY, qty))
    unitario = prices.price_of(state, item)
    total = unitario * qty
    if state.player.money < total:
        raise EngineError(
            "sin_dinero",
            f"Necesitás {total} peso(s) y tenés {state.player.money}.",
        )

    actividad = activity_runtime.by_id("comprar")
    if actividad is not None:
        puede, motivo = activity_runtime.can_start(state, actividad)
        if not puede:
            raise EngineError("no_disponible", motivo or "El almacén está cerrado.")

    _begin(state, "almacen")

    before = state.pa
    _spend(state, 1)
    cerrados = state.advance(60, exertion=0.8)

    inv.add(state.inventory, item_id, qty, _day(state))
    state.player.money -= total
    state.location = "almacen"

    mensajes = [f"Compraste {qty} × {item.name} por {total} peso(s)."]
    if prices.is_expensive(state):
        mensajes.append("Los precios están por las nubes: la guerra se paga acá.")
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state,
        BUY,
        60,
        before,
        mensajes,
        deltas={"item": item_id, "qty": qty, "spent": total, "unit_price": unitario},
        days_closed=cerrados,
    )


def visit(state: GameState, npc_id: str) -> ActionResult:
    npc = npc_catalog.NPCS.get(npc_id)
    if npc is None:
        raise EngineError("npc_inexistente", f"No existe {npc_id}.")

    ahora = state.moment()
    if npc_runtime.is_away(npc, state.flags):
        raise EngineError(
            "no_disponible",
            f"{npc.name} no está: {npc.away_label.lower()}.",
        )

    lugar = npc_runtime.location_of(npc, ahora, state.flags)
    if not npc_runtime.is_reachable(lugar):
        raise EngineError(
            "no_disponible",
            f"{npc.name} está en su casa; no es hora de visitarla.",
        )

    actividad = activity_runtime.by_id("visitar")
    if actividad is not None:
        puede, motivo = activity_runtime.can_start(state, actividad)
        if not puede:
            raise EngineError("no_disponible", motivo or "No podés visitar ahora.")

    _begin(state, lugar)

    before = state.pa
    _spend(state, 2)
    cerrados = state.advance(120, exertion=1.0)

    ganancias = npc_runtime.apply_visit(state, npc)
    linea = npc_runtime.visit_line(state, npc)

    mensajes = [linea, f"Pasaste dos horas con {npc.name}."]
    mensajes.extend(registro["message"] for registro in cerrados)
    return _finish(
        state,
        VISIT,
        120,
        before,
        mensajes,
        deltas={"npc": npc_id, **ganancias},
        days_closed=cerrados,
    )


# ---------- escenas ----------


def resolve_event(state: GameState, uid: str, choice_id: str) -> dict:
    resultado = events.resolve(state, uid, choice_id)
    state.queue_events()
    resultado["fired_events"] = [
        {k: v for k, v in evento.items() if k in ("id", "title", "uid")}
        for evento in state.take_fired()
    ]
    return resultado


__all__ = [
    "ActionResult",
    "perform",
    "sleep",
    "eat",
    "drink",
    "wait",
    "do_activity",
    "buy",
    "visit",
    "resolve_event",
    "MAX_MEALS_PER_DAY",
]
