"""Contratos de entrada y salida de la API."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

ActionType = Literal["sleep", "eat", "drink", "wait", "activity", "buy", "visit"]


class CreateGameRequest(BaseModel):
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    start_date: date = Field(
        default=date(1932, 9, 1),
        description="Fecha del día 1 de simulación (05:00).",
    )
    difficulty: int = Field(
        default=1,
        ge=0,
        le=2,
        description="0=fácil, 1=normal, 2=difícil.",
    )


class ActionRequest(BaseModel):
    type: ActionType
    hours: int | None = Field(default=None, ge=1, le=12)
    item: str | None = None
    qty: int | None = Field(default=None, ge=1, le=20)
    npc: str | None = None
    activity: str | None = None


class ResolveRequest(BaseModel):
    choice: str = Field(min_length=1, description="Id de la opción elegida.")


class ClockOut(BaseModel):
    clock_min: int
    day_index: int
    minute_of_day: int
    hour: int
    minute: int
    time_label: str
    period: str
    period_label: str
    date: date
    date_label: str
    weekday: int
    weekday_label: str


class PlayerOut(BaseModel):
    health: float
    hydration: float
    nutrition: float
    fatigue: float
    hygiene: float
    strength: float
    stamina: float
    complexion: float
    knowledge: float
    reputation: float
    money: int
    sleep_hours_today: float
    meals_today: int
    drinks_today: int
    sleep_debt_days: int


class StackOut(BaseModel):
    item_id: str
    name: str
    qty: int
    expires_day: int | None = None


class IdentityOut(BaseModel):
    suspicion: float
    credibility: float


class GameOut(BaseModel):
    game_id: str
    version: int
    pa: int
    pa_max: int
    closed_days: int
    location: str
    location_label: str
    clock: ClockOut
    player: PlayerOut
    identity: IdentityOut
    inventory: list[StackOut]
    npcs_here: list[dict[str, Any]]
    pending_count: int


class ActivityOut(BaseModel):
    id: str
    name: str
    description: str
    duration_hours: int
    location: str | None = None
    kind: str
    implemented: bool
    available: bool
    reason: str | None = None


class ActivitiesOut(BaseModel):
    game_id: str
    pa: int
    activities: list[ActivityOut]


class ActionResultOut(BaseModel):
    game: GameOut
    result: dict


class InventoryOut(BaseModel):
    game_id: str
    money: int
    total_weight: float
    items: list[StackOut]


class NpcsOut(BaseModel):
    game_id: str
    npcs: list[dict[str, Any]]


class PendingOut(BaseModel):
    game_id: str
    events: list[dict[str, Any]]


class ResolveOut(BaseModel):
    game: GameOut
    result: dict


class ShopItemOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    price: int
    effective_price: int
    weight: float


class ShopOut(BaseModel):
    game_id: str
    money: int
    price_multiplier: float
    items: list[ShopItemOut]
