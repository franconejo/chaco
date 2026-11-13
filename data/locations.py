"""Lugares de Ybycuí, Paraguarí (GDD §2 y §12).

El pueblo está lejos del frente chaqueño (a ~700 km del Chaco), pero la guerra
se siente igual: faltan hombres, suben los precios y llegan cartas del frente.

`public` indica si un personaje puede ser visitado allí. Las casas ajenas no
son accesibles: si alguien está en su casa, no se lo puede visitar.

`zone` agrupa los lugares en zonas del mapa para el cliente (web y Ren'Py).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    description: str
    public: bool = True
    zone: str = "centro"


LOCATIONS: dict[str, Location] = {
    location.id: location
    for location in (
        Location(
            "casa",
            "Tu casa",
            "Una pieza prestada en el barrio de la estación, con lo justo.",
            public=False,
            zone="barrio",
        ),
        Location(
            "almacen",
            "Almacén de don Ramón",
            "Bolsas de poroto, olor a grasa y tabaco. El mostrador de siempre.",
            zone="centro",
        ),
        Location(
            "taller",
            "Taller de don Aurelio",
            "Virutas, serruchos y olor a madera. Acá se arregla todo lo que se rompe.",
            zone="centro",
        ),
        Location(
            "plaza",
            "Plaza de Ybycuí",
            "Plaza con su banco de siempre, árboles de lapacho y el kiosco del centro.",
            zone="centro",
        ),
        Location(
            "mercado",
            "Mercado del pueblo",
            "Puestos de yerba, mandioca, carne seca y frutas de la zona. Los sábados.",
            zone="centro",
        ),
        Location(
            "iglesia",
            "Iglesia de Ybycuí",
            "Sombra, silencio, mujeres de negro y el padre Ignacio en el confesionario.",
            zone="centro",
        ),
        Location(
            "pozo",
            "Pozo del barrio",
            "El pozo compartido, cerca del río Ybycuí. Acá se busca agua y chisme.",
            zone="barrio",
        ),
        Location(
            "rio",
            "Río Ybycuí",
            "El río que baja de la sierra. Agua clara, piedras y lavanderas.",
            zone="barrio",
        ),
        Location(
            "fundicion",
            "Ruinas de la Fundición (La Rosada)",
            "Las ruinas de la fundición de hierro de Carlos Antonio López. Hoy es parque "
            "y memoria. Los muchachos vienen a caminar entre los hornos apagados.",
            zone="afueras",
        ),
        Location(
            "salto",
            "Salto Mbocaruzú",
            "La cascada en el parque nacional. Lejos del pueblo, pero el agua es "
            "fresca y nadie te pregunta nada.",
            zone="afueras",
            public=True,
        ),
        Location(
            "cuartel",
            "Cuartel de reclutamiento",
            "Una casa requisada, con bandera y guardia. Acá se anota a los mozos.",
            public=False,
            zone="afueras",
        ),
        Location(
            "estacion",
            "Estación del ferrocarril",
            "El tren que va a Asunción. De acá salen los que se van y llegan las cartas.",
            zone="barrio",
        ),
        Location("casa_juana", "Casa de Juana", "", public=False, zone="barrio"),
        Location("casa_celia", "Casa de Celia", "", public=False, zone="barrio"),
        Location("casa_aurora", "Casa de Aurora", "", public=False, zone="barrio"),
        Location("casa_aurelio", "Casa de Aurelio", "", public=False, zone="barrio"),
        Location("casa_ramon", "Casa de don Ramón", "", public=False, zone="barrio"),
        Location("casa_ursula", "Casa de doña Úrsula", "", public=False, zone="barrio"),
        Location("casa_nicanor", "Casa de Nicanor", "", public=False, zone="barrio"),
        Location("casa_vera", "Casa del sargento Vera", "", public=False, zone="afueras"),
        Location("casa_padre_ignacio", "Casa del padre Ignacio", "", public=False, zone="centro"),
        Location("casa_mercedes", "Casa de doña Mercedes", "", public=False, zone="barrio"),
        Location("casa_ortega", "Casa del teniente Ortega", "", public=False, zone="afueras"),
    )
}


def get(location_id: str) -> Location:
    try:
        return LOCATIONS[location_id]
    except KeyError as exc:
        raise KeyError(f"Lugar desconocido: {location_id}") from exc


def label(location_id: str) -> str:
    location = LOCATIONS.get(location_id)
    return location.name if location else location_id


def is_public(location_id: str) -> bool:
    location = LOCATIONS.get(location_id)
    return bool(location and location.public)


def zone_of(location_id: str) -> str:
    location = LOCATIONS.get(location_id)
    return location.zone if location else "centro"


ZONES: dict[str, str] = {
    "barrio": "Barrio de la estación",
    "centro": "Centro del pueblo",
    "afueras": "Afueras y campo",
}
