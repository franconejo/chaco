"""Catálogo de objetos (GDD §12).

La moneda es el **peso paraguayo**: el guaraní no se creó hasta 1943, así que
usar guaraníes en 1932 sería un error histórico.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIAS = (
    "alimento",
    "bebida",
    "medicamento",
    "higiene",
    "regalo",
    "carta",
    "documento",
    "personal",
)


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    category: str
    description: str
    price: int = 0
    weight: float = 0.0
    nutrition: float = 0.0
    hydration: float = 0.0
    health: float = 0.0
    hygiene: float = 0.0
    shelf_life_days: int | None = None
    pa_recovery: int = 3
    narrative: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "price": self.price,
            "weight": self.weight,
        }


ITEMS: dict[str, Item] = {
    item.id: item
    for item in (
        Item(
            id="agua",
            name="Agua",
            category="bebida",
            description="Un cántaro de agua del pozo.",
            price=1,
            weight=1.0,
            hydration=18.0,
            pa_recovery=3,
        ),
        Item(
            id="chipa",
            name="Chipa",
            category="alimento",
            description="Chipa de almidón, envuelta en hoja. Aguanta poco.",
            price=1,
            weight=0.2,
            nutrition=14.0,
            shelf_life_days=2,
            pa_recovery=3,
        ),
        Item(
            id="pan",
            name="Pan",
            category="alimento",
            description="Pan casero del almacén.",
            price=1,
            weight=0.3,
            nutrition=16.0,
            shelf_life_days=2,
            pa_recovery=3,
        ),
        Item(
            id="mandioca",
            name="Mandioca",
            category="alimento",
            description="Mandioca cocida. Llena y dura unos días.",
            price=2,
            weight=0.5,
            nutrition=24.0,
            shelf_life_days=4,
            pa_recovery=3,
        ),
        Item(
            id="carne_seca",
            name="Carne seca",
            category="alimento",
            description="Tira de carne secada al sol. Cara, pero rinde.",
            price=3,
            weight=0.4,
            nutrition=30.0,
            shelf_life_days=6,
            pa_recovery=3,
        ),
        Item(
            id="quinina",
            name="Quinina",
            category="medicamento",
            description="Para las fiebres. Amarga como ella sola.",
            price=4,
            weight=0.1,
            health=12.0,
            shelf_life_days=365,
        ),
        Item(
            id="jabon",
            name="Jabón",
            category="higiene",
            description="Jabón de grasa y ceniza.",
            price=2,
            weight=0.2,
            hygiene=25.0,
        ),
        Item(
            id="panuelo",
            name="Pañuelo bordado",
            category="regalo",
            description="Un pañuelo con iniciales bordadas. Sirve para quedar bien.",
            price=3,
            weight=0.05,
        ),
        Item(
            id="carta_papel",
            name="Hoja de papel",
            category="carta",
            description="Papel para escribir una carta.",
            price=1,
            weight=0.01,
        ),
        Item(
            id="acta_verdadera",
            name="Acta de nacimiento verdadera",
            category="documento",
            description="Tu acta real. Si alguien la encuentra, se acabó el engaño.",
            weight=0.0,
            narrative=True,
        ),
        Item(
            id="acta_falsa",
            name="Acta de nacimiento falsificada",
            category="documento",
            description="La que mostrás cuando preguntan. El año no coincide.",
            weight=0.0,
            narrative=True,
        ),
    )
}


def get(item_id: str) -> Item:
    try:
        return ITEMS[item_id]
    except KeyError as exc:
        raise KeyError(f"Objeto desconocido: {item_id}") from exc


def by_category(category: str) -> list[Item]:
    return [item for item in ITEMS.values() if item.category == category]


def buyable() -> list[Item]:
    return [item for item in ITEMS.values() if item.price > 0]


def foods() -> list[Item]:
    return by_category("alimento")


def drinks() -> list[Item]:
    return by_category("bebida")
