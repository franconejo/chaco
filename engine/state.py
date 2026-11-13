"""Estado de la partida y avance del tiempo (GDD §6, §7 y §8).

`GameState` es determinista: mismas acciones + misma semilla = mismo mundo.
No conoce HTTP ni SQL; la API sólo lo carga, lo ejecuta y lo guarda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from engine import energy, events, needs
from engine import inventory as inv
from engine.clock import MINUTES_PER_DAY, Moment, moment
from engine.energy import PA_MAX
from engine.inventory import Stack
from engine.npc import NpcState

SCHEMA_VERSION = 2

STARTING_INVENTORY: tuple[tuple[str, int], ...] = (
    ("agua", 2),
    ("chipa", 2),
    ("mandioca", 1),
)
STARTING_DOCUMENTS: tuple[str, ...] = ("acta_verdadera", "acta_falsa")
STARTING_MONEY = 5


@dataclass
class PlayerState:
    health: float = 100.0
    hydration: float = 80.0
    nutrition: float = 75.0
    fatigue: float = 10.0
    hygiene: float = 90.0
    strength: float = 20.0
    stamina: float = 20.0
    complexion: float = 25.0
    knowledge: float = 10.0
    reputation: float = 50.0
    money: int = STARTING_MONEY
    sleep_hours_today: float = 0.0
    meals_today: int = 0
    drinks_today: int = 0
    sleep_debt_days: int = 0
    days_at_zero_health: int = 0

    def to_dict(self) -> dict:
        return {
            "health": round(self.health, 3),
            "hydration": round(self.hydration, 3),
            "nutrition": round(self.nutrition, 3),
            "fatigue": round(self.fatigue, 3),
            "hygiene": round(self.hygiene, 3),
            "strength": round(self.strength, 3),
            "stamina": round(self.stamina, 3),
            "complexion": round(self.complexion, 3),
            "knowledge": round(self.knowledge, 3),
            "reputation": round(self.reputation, 3),
            "money": self.money,
            "sleep_hours_today": round(self.sleep_hours_today, 3),
            "meals_today": self.meals_today,
            "drinks_today": self.drinks_today,
            "sleep_debt_days": self.sleep_debt_days,
            "days_at_zero_health": self.days_at_zero_health,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PlayerState:
        data = data or {}
        campos = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in campos})


@dataclass
class GameState:
    clock_min: int = 0
    pa: int = PA_MAX
    start_date: date = date(1932, 9, 1)
    seed: int = 0
    location: str = "casa"
    difficulty: int = 1
    player: PlayerState = field(default_factory=PlayerState)
    inventory: list[Stack] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    npcs: dict[str, NpcState] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    event_history: dict[str, int] = field(default_factory=dict)
    pending: list[dict] = field(default_factory=list)
    identity: dict[str, float] = field(
        default_factory=lambda: {"suspicion": 0.0, "credibility": 100.0}
    )
    closed_days: int = 0
    log: list[dict] = field(default_factory=list)
    # Transitorio: acontecimientos disparados en la última acción (no se guarda)
    fired_now: list[dict] = field(default_factory=list)
    # Transitorio: mensajes de colapso por quedarse sin PA (no se guarda)
    collapse_messages: list[str] = field(default_factory=list)
    pa_collapse_applied: bool = False

    # ---------- creación ----------

    @classmethod
    def new(cls, start_date: date | None = None, seed: int = 0, difficulty: int = 1) -> GameState:
        from engine import difficulty as diff

        estado = cls(
            start_date=start_date or date(1932, 9, 1),
            seed=seed,
            difficulty=difficulty,
            pa=diff.starting_pa(difficulty),
        )
        estado.player.money = diff.starting_money(difficulty)
        for item_id, cantidad in STARTING_INVENTORY:
            inv.add(estado.inventory, item_id, cantidad, 0)
        for documento in STARTING_DOCUMENTS:
            inv.add(estado.inventory, documento, 1, 0)
        return estado

    # ---------- consulta ----------

    def moment(self) -> Moment:
        return moment(self.clock_min, self.start_date)

    def has_item(self, item_id: str, cantidad: int = 1) -> bool:
        return inv.available_count(self.inventory, item_id, self.moment().day_index) >= cantidad

    def snapshot(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "clock_min": self.clock_min,
            "pa": self.pa,
            "start_date": self.start_date.isoformat(),
            "seed": self.seed,
            "location": self.location,
            "player": self.player.to_dict(),
            "inventory": [stack.to_dict() for stack in self.inventory],
            "flags": list(self.flags),
            "npcs": {npc_id: estado.to_dict() for npc_id, estado in self.npcs.items()},
            "fired": list(self.fired),
            "event_history": dict(self.event_history),
            "pending": list(self.pending),
            "identity": dict(self.identity),
            "difficulty": self.difficulty,
            "closed_days": self.closed_days,
            "pa_collapse_applied": self.pa_collapse_applied,
            "log": self.log[-120:],
        }

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> GameState:
        return cls(
            clock_min=_int(data.get("clock_min"), 0),
            pa=energy.clamp_pa(_int(data.get("pa"), PA_MAX)),
            start_date=date.fromisoformat(data["start_date"]),
            seed=_int(data.get("seed"), 0),
            location=str(data.get("location") or "casa"),
            player=PlayerState.from_dict(data.get("player")),
            inventory=inv.from_list(data.get("inventory")),
            flags=list(data.get("flags") or []),
            npcs={
                npc_id: NpcState.from_dict(valor)
                for npc_id, valor in (data.get("npcs") or {}).items()
            },
            fired=list(data.get("fired") or []),
            event_history={
                str(k): int(v) for k, v in (data.get("event_history") or {}).items()
            },
            pending=list(data.get("pending") or []),
            identity={
                "suspicion": float((data.get("identity") or {}).get("suspicion", 0.0)),
                "credibility": float(
                    (data.get("identity") or {}).get("credibility", 100.0)
                ),
            },
            difficulty=int(data.get("difficulty", 1)),
            closed_days=_int(data.get("closed_days"), 0),
            pa_collapse_applied=bool(data.get("pa_collapse_applied", False)),
            log=list(data.get("log") or []),
        )

    # ---------- avance del tiempo ----------

    def advance(
        self,
        minutes: int,
        *,
        mode: str = "awake",
        exertion: float = 1.0,
        sleep_rate: float = 0.0,
        queue: bool = True,
    ) -> list[dict]:
        """Mueve el reloj en tramos, cerrando jornada en cada corte de 05:00.

        `queue=False` se usa cuando el que avanza el reloj es un acontecimiento
        (por ejemplo, una escena que te hace perder la tarde): sin esta guarda,
        disparar un evento podría encadenar otro dentro de sí mismo.
        """
        if minutes <= 0:
            return []

        cerrados: list[dict] = []
        restante = minutes
        while restante > 0:
            hasta_corte = MINUTES_PER_DAY - (self.clock_min % MINUTES_PER_DAY)
            tramo = min(restante, hasta_corte)

            if mode == "sleep":
                needs.tick_sleep(self.player, tramo, fatigue_per_hour=sleep_rate)
                self.player.sleep_hours_today += tramo / 60.0
            else:
                needs.tick_awake(self.player, tramo, exertion=exertion, difficulty=self.difficulty)

            self.clock_min += tramo
            restante -= tramo

            if self.clock_min % MINUTES_PER_DAY == 0:
                cerrados.append(self._close_day())

        # En difícil, morir en cuanto la salud llega a 0.
        from engine import difficulty as diff

        if diff.death_threshold(self.difficulty) == 0 and self.player.health <= 0:
            if "muerto" not in self.flags:
                self.flags.append("muerto")

        if queue:
            self.queue_events()
        return cerrados

    def queue_events(self) -> list[dict]:
        """Dispara el acontecimiento que corresponda, si hay alguno."""
        if self.pending:
            return []
        disparados = events.collect(self)
        self.fired_now.extend(disparados)
        return disparados

    def take_fired(self) -> list[dict]:
        disparados = self.fired_now
        self.fired_now = []
        return disparados

    def _close_day(self) -> dict:
        p = self.player
        consecuencias = needs.day_close_consequences(
            p.sleep_hours_today, p.sleep_debt_days
        )
        p.health = needs.clamp(p.health + consecuencias["health_delta"])
        p.fatigue = needs.clamp(p.fatigue + consecuencias["fatigue_delta"])
        p.sleep_debt_days = int(consecuencias["sleep_debt_days"])

        # Seguimiento de salud en cero: si llega al umbral, muerte.
        from engine import difficulty as diff

        threshold = diff.death_threshold(self.difficulty)
        if p.health <= 0:
            if threshold == 0:
                # Difícil: muerte inmediata al llegar a 0.
                if "muerto" not in self.flags:
                    self.flags.append("muerto")
                p.days_at_zero_health = 1
            else:
                p.days_at_zero_health += 1
                if p.days_at_zero_health >= threshold and "muerto" not in self.flags:
                    self.flags.append("muerto")
        else:
            p.days_at_zero_health = 0

        dia = self.closed_days
        registro: dict[str, Any] = {"day_index": dia, **consecuencias, "clock_min": self.clock_min}
        self.closed_days += 1

        vencidos = inv.purge(self.inventory, self.closed_days)
        if vencidos:
            registro["spoiled"] = vencidos
            nombres = ", ".join(f"{v['item_id']} ×{v['qty']}" for v in vencidos)
            registro["message"] = f"Se echó a perder: {nombres}."
        elif "muerto" in self.flags and p.days_at_zero_health >= 2:
            registro["message"] = "El cuerpo no aguantó más. Fin de la partida."
        elif consecuencias["penalized"]:
            registro["message"] = (
                "Dormiste menos de tres horas: la salud y la fatiga lo acusan."
            )
        else:
            registro["message"] = "Jornada cerrada. Descansaste lo suficiente."

        p.sleep_hours_today = 0.0
        p.meals_today = 0
        p.drinks_today = 0

        self.log.append({"kind": "day_close", **registro})
        return registro


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
