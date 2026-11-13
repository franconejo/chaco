"""Mapa del pueblo de Ybycuí (Fase 4).

Describe las zonas visitables y sus conexiones para que el cliente (web y
Ren'Py) pueda dibujar un mapa. El motor no usa este archivo: es sólo
presentación.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MapNode:
    id: str
    label: str
    x: int  # 0..100 (porcentaje del ancho del mapa)
    y: int  # 0..100 (porcentaje del alto del mapa)
    zone: str
    public: bool = True


@dataclass(frozen=True)
class MapEdge:
    a: str
    b: str


# Nodos del mapa (coordenadas en porcentaje del canvas).
NODES: list[MapNode] = [
    MapNode("casa", "Tu casa", 20, 75, "barrio", public=False),
    MapNode("estacion", "Estación", 15, 60, "barrio"),
    MapNode("pozo", "Pozo", 30, 65, "barrio"),
    MapNode("rio", "Río Ybycuí", 25, 85, "barrio"),
    MapNode("casa_juana", "Casa de Juana", 35, 70, "barrio", public=False),
    MapNode("casa_celia", "Casa de Celia", 40, 78, "barrio", public=False),
    MapNode("casa_aurelio", "Casa de Aurelio", 28, 82, "barrio", public=False),
    MapNode("casa_ramon", "Casa de don Ramón", 45, 72, "barrio", public=False),
    MapNode("casa_ursula", "Casa de Úrsula", 32, 58, "barrio", public=False),
    MapNode("casa_nicanor", "Casa de Nicanor", 18, 55, "barrio", public=False),
    MapNode("casa_mercedes", "Casa de Mercedes", 22, 68, "barrio", public=False),
    MapNode("almacen", "Almacén", 55, 45, "centro"),
    MapNode("taller", "Taller", 62, 52, "centro"),
    MapNode("plaza", "Plaza", 50, 35, "centro"),
    MapNode("mercado", "Mercado", 45, 48, "centro"),
    MapNode("iglesia", "Iglesia", 58, 28, "centro"),
    MapNode("casa_padre_ignacio", "Casa del padre", 60, 22, "centro", public=False),
    MapNode("fundicion", "Fundición (La Rosada)", 78, 60, "afueras"),
    MapNode("salto", "Salto Mbocaruzú", 88, 80, "afueras"),
    MapNode("cuartel", "Cuartel", 70, 15, "afueras", public=False),
    MapNode("casa_vera", "Casa del sargento", 75, 22, "afueras", public=False),
    MapNode("casa_ortega", "Casa del teniente", 82, 18, "afueras", public=False),
    MapNode("casa_aurora", "Casa de Aurora", 50, 55, "centro", public=False),
]

EDGES: list[MapEdge] = [
    MapEdge("casa", "estacion"),
    MapEdge("casa", "pozo"),
    MapEdge("pozo", "rio"),
    MapEdge("pozo", "plaza"),
    MapEdge("plaza", "almacen"),
    MapEdge("plaza", "iglesia"),
    MapEdge("plaza", "mercado"),
    MapEdge("almacen", "taller"),
    MapEdge("almacen", "mercado"),
    MapEdge("iglesia", "casa_padre_ignacio"),
    MapEdge("plaza", "fundicion"),
    MapEdge("fundicion", "salto"),
    MapEdge("fundicion", "cuartel"),
    MapEdge("cuartel", "casa_vera"),
    MapEdge("cuartel", "casa_ortega"),
]

ZONE_COLORS: dict[str, str] = {
    "barrio": "#3a4a3a",
    "centro": "#4a3f33",
    "afueras": "#2a3a2a",
}

ZONE_LABELS: dict[str, str] = {
    "barrio": "Barrio de la estación",
    "centro": "Centro del pueblo",
    "afueras": "Afueras y campo",
}


def node_by_id(node_id: str) -> MapNode | None:
    for n in NODES:
        if n.id == node_id:
            return n
    return None


def public_nodes() -> list[MapNode]:
    return [n for n in NODES if n.public]


def edges_for(node_id: str) -> list[MapEdge]:
    return [e for e in EDGES if e.a == node_id or e.b == node_id]
