"""Actividades (GDD §13), declaradas como datos.

`kind` define el comportamiento especial:

* `simple`: cuesta PA, avanza el reloj y aplica `effects`.
* `buy`: compra de objetos en el almacén.
* `visit`: visita a un personaje.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TODOS = ("manana", "tarde", "noche")


@dataclass(frozen=True)
class Activity:
    id: str
    name: str
    description: str
    duration_hours: int
    start_periods: tuple[str, ...]
    location: str | None = None
    effects: dict = field(default_factory=dict)
    exertion: float = 1.0
    requires: dict = field(default_factory=dict)
    kind: str = "simple"
    implemented: bool = True


ACTIVITIES: dict[str, Activity] = {
    actividad.id: actividad
    for actividad in (
        Activity(
            id="trabajar",
            name="Trabajar en el almacén",
            description="Acomodar bolsas, anotar pedidos y atender el mostrador.",
            duration_hours=5,
            start_periods=("manana",),
            location="almacen",
            effects={
                "money": 3,
                "attributes": {"stamina": 0.5, "reputation": 0.3},
            },
            exertion=1.2,
        ),
        Activity(
            id="estudiar",
            name="Estudiar",
            description="Leer, practicar cuentas y escribir sin errores.",
            duration_hours=2,
            start_periods=("manana", "tarde"),
            location="casa",
            effects={"attributes": {"knowledge": 1.5}},
            exertion=0.8,
        ),
        Activity(
            id="caminar",
            name="Caminar por el pueblo",
            description="Dar una vuelta. Desarrolla resistencia de a poco.",
            duration_hours=1,
            start_periods=TODOS,
            location="plaza",
            effects={"attributes": {"stamina": 0.3, "strength": 0.2}},
            exertion=1.3,
        ),
        Activity(
            id="entrenar",
            name="Entrenar",
            description="Levantar lo que haya en el patio. Cansa y da fuerza.",
            duration_hours=2,
            start_periods=("manana", "tarde"),
            location="plaza",
            effects={"attributes": {"strength": 0.6, "stamina": 0.4}},
            exertion=1.9,
        ),
        Activity(
            id="descansar",
            name="Descansar",
            description="Sentarse un rato sin hacer nada.",
            duration_hours=1,
            start_periods=TODOS,
            location="casa",
            effects={"needs": {"fatigue": -8}},
            exertion=0.5,
        ),
        Activity(
            id="banarse",
            name="Bañarse",
            description="Agua, jabón y un poco de dignidad.",
            duration_hours=1,
            start_periods=("manana", "tarde"),
            location="casa",
            requires={"item": "agua"},
            effects={"needs": {"hygiene": 30}, "consume": {"agua": 1}},
            exertion=0.7,
        ),
        Activity(
            id="buscar_agua",
            name="Buscar agua",
            description="Ir al pozo con el balde. Gratis, pero pesa.",
            duration_hours=1,
            start_periods=TODOS,
            location="pozo",
            effects={"inventory": {"agua": 2}},
            exertion=1.1,
        ),
        Activity(
            id="comprar",
            name="Comprar en el almacén",
            description="Provisiones para los próximos días.",
            duration_hours=1,
            start_periods=("manana", "tarde"),
            location="almacen",
            kind="buy",
        ),
        Activity(
            id="visitar",
            name="Visitar a alguien",
            description="Pasar un rato con alguien del pueblo.",
            duration_hours=2,
            start_periods=("manana", "tarde"),
            kind="visit",
        ),
    )
}
