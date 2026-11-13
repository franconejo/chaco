"""Inventario con cantidades, peso y vencimiento (GDD §12).

Se guarda como una lista de *pilas* (`Stack`): el mismo objeto comprado en
días distintos vence en días distintos, así que no se pueden fusionar sin
perder información.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data import items as item_catalog


@dataclass
class Stack:
    item_id: str
    qty: int
    expires_day: int | None = None

    def to_dict(self) -> dict:
        return {"item_id": self.item_id, "qty": self.qty, "expires_day": self.expires_day}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stack:
        return cls(
            item_id=str(data["item_id"]),
            qty=int(data.get("qty", 0)),
            expires_day=data.get("expires_day"),
        )

    def is_expired(self, current_day: int) -> bool:
        return self.expires_day is not None and current_day > self.expires_day


def _expiry_for(item_id: str, current_day: int) -> int | None:
    item = item_catalog.ITEMS.get(item_id)
    if item is None or item.shelf_life_days is None:
        return None
    return current_day + item.shelf_life_days


def add(stacks: list[Stack], item_id: str, qty: int, current_day: int) -> None:
    if qty <= 0:
        return
    expires = _expiry_for(item_id, current_day)
    for stack in stacks:
        if stack.item_id == item_id and stack.expires_day == expires:
            stack.qty += qty
            return
    stacks.append(Stack(item_id=item_id, qty=qty, expires_day=expires))


def count(stacks: list[Stack], item_id: str) -> int:
    return sum(stack.qty for stack in stacks if stack.item_id == item_id)


def count_category(stacks: list[Stack], category: str) -> int:
    total = 0
    for stack in stacks:
        item = item_catalog.ITEMS.get(stack.item_id)
        if item and item.category == category:
            total += stack.qty
    return total


def available_count(stacks: list[Stack], item_id: str, current_day: int) -> int:
    return sum(
        stack.qty
        for stack in stacks
        if stack.item_id == item_id and not stack.is_expired(current_day)
    )


def remove(stacks: list[Stack], item_id: str, qty: int) -> int:
    """Consume primero lo que vence antes. Devuelve cuánto se pudo quitar."""
    remaining = qty
    for stack in sorted(stacks, key=lambda s: (s.expires_day is None, s.expires_day or 0)):
        if remaining <= 0:
            break
        if stack.item_id != item_id:
            continue
        taken = min(stack.qty, remaining)
        stack.qty -= taken
        remaining -= taken
    stacks[:] = [stack for stack in stacks if stack.qty > 0]
    return qty - remaining


def purge(stacks: list[Stack], current_day: int) -> list[dict]:
    """Descarta lo vencido y devuelve el detalle para el registro."""
    vencidos = [stack for stack in stacks if stack.is_expired(current_day)]
    if vencidos:
        stacks[:] = [stack for stack in stacks if not stack.is_expired(current_day)]
    return [
        {"item_id": stack.item_id, "qty": stack.qty, "expires_day": stack.expires_day}
        for stack in vencidos
    ]


def best_food(stacks: list[Stack], current_day: int) -> str | None:
    candidates = [
        stack
        for stack in stacks
        if not stack.is_expired(current_day)
        and (item := item_catalog.ITEMS.get(stack.item_id)) is not None
        and item.category == "alimento"
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda s: (-item_catalog.ITEMS[s.item_id].nutrition, s.expires_day or 9999)
    )
    return candidates[0].item_id


def total_weight(stacks: list[Stack]) -> float:
    total = 0.0
    for stack in stacks:
        item = item_catalog.ITEMS.get(stack.item_id)
        if item:
            total += item.weight * stack.qty
    return round(total, 3)


def to_list(stacks: list[Stack]) -> list[dict]:
    return [
        {
            **stack.to_dict(),
            "name": item_catalog.ITEMS[stack.item_id].name
            if stack.item_id in item_catalog.ITEMS
            else stack.item_id,
        }
        for stack in stacks
    ]


def from_list(data: list[dict[str, Any]] | None) -> list[Stack]:
    return [Stack.from_dict(entry) for entry in (data or [])]
