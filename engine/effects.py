"""Aplicación de efectos (actividades, acontecimientos, elecciones).

Los efectos son diccionarios declarativos para que el contenido no necesite
código. Claves soportadas:

* `money`: ajuste en pesos.
* `needs`: salud, hidratación, nutrición, fatiga, higiene (deltas).
* `attributes`: fuerza, resistencia, complexión, conocimiento, reputación.
* `inventory` / `consume`: `{item_id: cantidad}`.
* `flags`: banderas que se activan.
* `npc`: `{npc_id: {affection, trust, familiarity, interest}}`.
* `suspicion` / `credibility`: identidad falsa (GDD §11).
* `location`: mueve al protagonista.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data.items import ITEMS
from engine import inventory as inv
from engine import npc as npc_runtime
from engine.errors import EngineError

if TYPE_CHECKING:  # pragma: no cover
    from engine.state import GameState

NEED_FIELDS = ("health", "hydration", "nutrition", "fatigue", "hygiene")
ATTRIBUTE_FIELDS = ("strength", "stamina", "complexion", "knowledge", "reputation")
RELATION_FIELDS = ("affection", "trust", "familiarity", "interest")


def apply(state: GameState, effects: dict | None) -> dict:
    if not effects:
        return {}

    cambios: dict[str, float] = {}

    dinero = int(effects.get("money", 0))
    if dinero:
        state.player.money = max(0, state.player.money + dinero)
        cambios["money"] = dinero

    for campo, delta in (effects.get("needs") or {}).items():
        if campo not in NEED_FIELDS:
            continue
        actual = getattr(state.player, campo)
        nuevo = max(0.0, min(100.0, actual + float(delta)))
        setattr(state.player, campo, nuevo)
        cambios[campo] = round(nuevo - actual, 3)

    for campo, delta in (effects.get("attributes") or {}).items():
        if campo not in ATTRIBUTE_FIELDS:
            continue
        actual = getattr(state.player, campo)
        nuevo = max(0.0, min(100.0, actual + float(delta)))
        setattr(state.player, campo, nuevo)
        cambios[campo] = round(nuevo - actual, 3)

    dia = state.moment().day_index

    for item_id, cantidad in (effects.get("inventory") or {}).items():
        if item_id not in ITEMS:
            raise EngineError("objeto_desconocido", f"No existe el objeto {item_id}.")
        inv.add(state.inventory, item_id, int(cantidad), dia)
        cambios[f"inv:{item_id}"] = int(cantidad)

    for item_id, cantidad in (effects.get("consume") or {}).items():
        if item_id not in ITEMS:
            raise EngineError("objeto_desconocido", f"No existe el objeto {item_id}.")
        quitados = inv.remove(state.inventory, item_id, int(cantidad))
        if quitados < int(cantidad):
            raise EngineError(
                "objeto_insuficiente",
                f"Necesitás {cantidad} de {ITEMS[item_id].name} y no alcanza.",
            )
        cambios[f"consumido:{item_id}"] = quitados

    for flag in effects.get("flags") or []:
        if flag not in state.flags:
            state.flags.append(flag)
            cambios[f"flag:{flag}"] = 1

    for flag in effects.get("unflags") or []:
        if flag in state.flags:
            state.flags.remove(flag)
            cambios[f"unflag:{flag}"] = 1

    for npc_id, deltas in (effects.get("npc") or {}).items():
        estado = npc_runtime.ensure(state, npc_id)
        for campo, delta in deltas.items():
            if campo not in RELATION_FIELDS:
                continue
            actual = getattr(estado, campo)
            nuevo = npc_runtime.clamp(actual + float(delta))
            setattr(estado, campo, nuevo)
            cambios[f"npc:{npc_id}:{campo}"] = round(nuevo - actual, 3)

    sospecha = effects.get("suspicion")
    if sospecha:
        state.identity["suspicion"] = max(
            0.0, min(100.0, state.identity.get("suspicion", 0.0) + float(sospecha))
        )
        cambios["suspicion"] = float(sospecha)

    credibilidad = effects.get("credibility")
    if credibilidad:
        state.identity["credibility"] = max(
            0.0, min(100.0, state.identity.get("credibility", 100.0) + float(credibilidad))
        )
        cambios["credibility"] = float(credibilidad)

    lugar = effects.get("location")
    if lugar:
        state.location = lugar
        cambios["location"] = 1

    return cambios
