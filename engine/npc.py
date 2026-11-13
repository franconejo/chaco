"""Estado y comportamiento de los personajes secundarios (GDD §10 y §15)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from data import locations as location_catalog
from data import npcs as npc_catalog
from data.npcs import NpcDef

if TYPE_CHECKING:  # pragma: no cover
    from engine.clock import Moment
    from engine.state import GameState


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


@dataclass
class NpcState:
    affection: float = 0.0
    trust: float = 0.0
    familiarity: float = 0.0
    interest: float = 0.0
    met: bool = False

    def to_dict(self) -> dict:
        return {
            "affection": round(self.affection, 3),
            "trust": round(self.trust, 3),
            "familiarity": round(self.familiarity, 3),
            "interest": round(self.interest, 3),
            "met": self.met,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> NpcState:
        data = data or {}
        return cls(
            affection=float(data.get("affection", 0.0)),
            trust=float(data.get("trust", 0.0)),
            familiarity=float(data.get("familiarity", 0.0)),
            interest=float(data.get("interest", 0.0)),
            met=bool(data.get("met", False)),
        )


def initial_state(npc_id: str) -> NpcState:
    npc = npc_catalog.get(npc_id)
    start = npc.start
    return NpcState(
        affection=float(start.get("affection", 0.0)),
        trust=float(start.get("trust", 0.0)),
        familiarity=float(start.get("familiarity", 0.0)),
        interest=float(start.get("interest", 0.0)),
        met=False,
    )


def ensure(state: GameState, npc_id: str) -> NpcState:
    if npc_id not in state.npcs:
        state.npcs[npc_id] = initial_state(npc_id)
    return state.npcs[npc_id]


AWAY_LOCATION = "ausente"


def is_away(npc: NpcDef, flags: object = ()) -> bool:
    """El personaje no está en el pueblo: se fue al frente, está preso, etc."""
    return bool(npc.away_flag and npc.away_flag in flags)  # type: ignore[operator]


def location_of(npc: NpcDef, current: Moment, flags: object = ()) -> str:
    """Dónde está el personaje ahora.

    Si su bandera de ausencia está activa, devuelve `AWAY_LOCATION`: no hay
    lugar al que ir a buscarlo y las visitas fallan con un motivo narrativo.
    """
    if is_away(npc, flags):
        return AWAY_LOCATION
    hora = current.hour + current.minute / 60.0
    for inicio, fin, lugar in npc.routine:
        if inicio <= hora < fin:
            return lugar
    return npc.home


def is_reachable(location_id: str) -> bool:
    return location_catalog.is_public(location_id)


def present(state: GameState) -> list[dict]:
    """Personajes que están ahora en el lugar donde está el protagonista."""
    ahora = state.moment()
    salida = []
    for npc in npc_catalog.NPCS.values():
        lugar = location_of(npc, ahora, state.flags)
        if lugar != state.location:
            continue
        estado = ensure(state, npc.id)
        salida.append(
            {
                "id": npc.id,
                "name": npc.name,
                "age": npc.age,
                "occupation": npc.occupation,
                "location": lugar,
                "location_label": location_catalog.label(lugar),
                "affection_label": relationship_label(estado.affection),
                "trust_label": relationship_label(estado.trust),
                "familiarity_label": relationship_label(estado.familiarity),
                "met": estado.met,
            }
        )
    return salida


def known(state: GameState) -> list[dict]:
    ahora = state.moment()
    salida = []
    for npc in npc_catalog.NPCS.values():
        estado = ensure(state, npc.id)
        lugar = location_of(npc, ahora, state.flags)
        ausente = lugar == AWAY_LOCATION
        salida.append(
            {
                "id": npc.id,
                "name": npc.name,
                "age": npc.age,
                "occupation": npc.occupation,
                "description": npc.description,
                "location": lugar,
                "location_label": npc.away_label
                if ausente
                else location_catalog.label(lugar),
                "visitable": is_reachable(lugar),
                "here": lugar == state.location,
                "away": ausente,
                "affection_label": relationship_label(estado.affection),
                "trust_label": relationship_label(estado.trust),
                "familiarity_label": relationship_label(estado.familiarity),
                "met": estado.met,
                "knows_secret": npc.knows_secret,
            }
        )
    return salida


def relationship_label(value: float) -> str:
    if value < 15:
        return "distante"
    if value < 35:
        return "cordial"
    if value < 60:
        return "cercana"
    if value < 80:
        return "muy cercana"
    return "íntima"


def level_key(affection: float) -> str:
    if affection < 15:
        return "fria"
    if affection < 45:
        return "tibia"
    return "cercana"


def visit_line(state: GameState, npc: NpcDef) -> str:
    estado = ensure(state, npc.id)
    level = level_key(estado.affection)
    lines = npc.visits.get(level) or npc.visits.get("tibia") or ("",)
    indice = (state.clock_min // 60 + len(npc.id)) % len(lines)
    return lines[indice]


def visit_gains(state: GameState, npc: NpcDef) -> dict:
    """Ganancia decreciente: cuanto más te conoce, menos suma una charla."""
    estado = ensure(state, npc.id)
    factor = max(0.25, 1.0 - estado.familiarity / 120.0)
    return {
        "familiarity": clamp(estado.familiarity + 5.0 * factor) - estado.familiarity,
        "affection": clamp(estado.affection + 2.5 * factor) - estado.affection,
        "trust": clamp(estado.trust + 1.0 * factor) - estado.trust,
    }


def apply_visit(state: GameState, npc: NpcDef) -> dict:
    estado = ensure(state, npc.id)
    ganancias = visit_gains(state, npc)
    estado.familiarity = clamp(estado.familiarity + ganancias["familiarity"])
    estado.affection = clamp(estado.affection + ganancias["affection"])
    estado.trust = clamp(estado.trust + ganancias["trust"])
    estado.met = True
    return {key: round(value, 3) for key, value in ganancias.items()}
