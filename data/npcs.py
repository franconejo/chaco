"""Elenco provisorio (Fase 1.5).

Nombres, edades, ocupaciones y rutinas son **propuesta**: el GDD deja el
reparto pendiente de definición (§22). Están acá para que los sistemas tengan
con quién funcionar y se reemplazan sin tocar el motor.

La rutina es una lista de `(hora_inicio, hora_fin, lugar)`; fuera de esos
rangos el personaje está en su casa (no visitable).

`away_flag` marca la bandera que lo saca del pueblo: mientras esté activa, no
aparece en ningún lugar y las visitas fallan con `away_label`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NpcDef:
    id: str
    name: str
    age: int
    occupation: str
    description: str
    home: str
    routine: tuple[tuple[int, int, str], ...]
    start: dict[str, float] = field(default_factory=dict)
    visits: dict[str, tuple[str, ...]] = field(default_factory=dict)
    knows_secret: bool = False
    away_flag: str | None = None
    away_label: str = "Ausente"


NPCS: dict[str, NpcDef] = {
    npc.id: npc
    for npc in (
        NpcDef(
            id="juana",
            name="Juana",
            age=20,
            occupation="Ayudante en el almacén",
            description=(
                "Amiga de la infancia. Sabe tu edad verdadera y guarda el secreto "
                "como si fuera propio."
            ),
            home="casa_juana",
            routine=((7, 13, "almacen"), (13, 19, "plaza")),
            start={"affection": 35, "trust": 30, "familiarity": 25, "interest": 0},
            knows_secret=True,
            visits={
                "fria": (
                    "Juana te saluda de lejos, con las manos ocupadas.",
                    "«Después hablamos, ¿eh?» Y sigue con lo suyo.",
                ),
                "tibia": (
                    "Juana te guarda un pedazo de banco y te cuenta quién se fue del barrio.",
                    "«¿Comiste?» pregunta, sin levantar la vista del canasto.",
                ),
                "cercana": (
                    "Juana se ríe de algo que dijiste y después se queda callada un rato. "
                    "«Cuidate», dice al final.",
                    "«Si te preguntan, decí que tenés dieciséis. Yo digo lo mismo», murmura.",
                ),
            },
        ),
        NpcDef(
            id="celia",
            name="Celia",
            age=19,
            occupation="Costurera",
            description=(
                "Reservada, de pocas palabras. Trabaja en el taller y va a la iglesia "
                "casi todas las tardes."
            ),
            home="casa_celia",
            routine=((8, 17, "taller"), (17, 19, "iglesia")),
            start={"affection": 10, "trust": 8, "familiarity": 5, "interest": 0},
            visits={
                "fria": (
                    "Celia levanta la vista, asiente y vuelve a la costura.",
                    "«Buenas», dice. Nada más.",
                ),
                "tibia": (
                    "Celia te muestra la costura y se queja del hilo, que viene flojo.",
                    "Habla poco, pero deja de coser mientras habla.",
                ),
                "cercana": (
                    "Celia te pregunta por tu familia y se acuerda del nombre de tu madre.",
                    "«No te quedes mucho por la calle», dice, y se le enrojece la oreja.",
                ),
            },
        ),
        NpcDef(
            id="aurora",
            name="Aurora",
            age=18,
            occupation="Hija de don Ramón",
            description=(
                "Alegre y conversadora. Atiende el almacén con el padre y se ríe de todo, "
                "aunque no siempre tenga ganas."
            ),
            home="casa_aurora",
            routine=((6, 15, "almacen"), (15, 20, "plaza")),
            start={"affection": 15, "trust": 12, "familiarity": 10, "interest": 0},
            visits={
                "fria": (
                    "Aurora te cobra, te da el vuelto y ya está mirando al siguiente.",
                    "«¿Algo más?»",
                ),
                "tibia": (
                    "Aurora te cuenta que su padre anda preocupado por los precios.",
                    "«Vos siempre tan serio. Sonreí un poco», te dice.",
                ),
                "cercana": (
                    "Aurora te guarda el pan de ayer y no te cobra.",
                    "«Si mi padre pregunta, ya te lo vendí», dice, y se ríe.",
                ),
            },
        ),
        NpcDef(
            id="aurelio",
            name="Aurelio",
            age=17,
            occupation="Aprendiz de carpintero",
            description=(
                "Amigo del barrio. Trabaja en el taller de su tío y anda siempre con "
                "una viruta en el pelo."
            ),
            home="casa_aurelio",
            routine=((6, 17, "taller"), (17, 22, "plaza")),
            start={"affection": 30, "trust": 25, "familiarity": 30, "interest": 0},
            away_flag="aurelio_en_el_frente",
            away_label="En el frente, Chaco",
            visits={
                "fria": (
                    "Aurelio está clavando una caja y casi no levanta la cabeza.",
                    "«Después, ¿eh?»",
                ),
                "tibia": (
                    "Aurelio te muestra lo que está haciendo y te pregunta si te animás "
                    "a darle una mano.",
                    "«Mi tío dice que si sigue así, me voy al Chaco igual», cuenta.",
                ),
                "cercana": (
                    "Aurelio te alcanza un banquito y te cuenta un chisme del almacén.",
                    "«Vos y yo no nos vamos a ningún lado, ¿no?», dice, y se ríe para "
                    "no ponerse serio.",
                ),
            },
        ),
        NpcDef(
            id="ramon",
            name="Don Ramón",
            age=52,
            occupation="Almacenero",
            description=(
                "Dueño del almacén. Le faltan empleados desde que empezaron a llevarse "
                "gente y no le gusta hablar de eso."
            ),
            home="casa_ramon",
            routine=((6, 20, "almacen"),),
            start={"affection": 20, "trust": 20, "familiarity": 15, "interest": 0},
            visits={
                "fria": (
                    "Don Ramón anota algo en un cuaderno y no te mira.",
                    "«Si venís a comprar, avisá. Si venís a charlar, esperá.»",
                ),
                "tibia": (
                    "Don Ramón te cuenta que el poroto subió y que ya nadie quiere fiar.",
                    "«Antes éramos cuatro acá. Ahora somos dos y tu amiga.»",
                ),
                "cercana": (
                    "Don Ramón te convida un mate y baja la voz.",
                    "«Si te llega una carta del ejército, no la abras en la calle.»",
                ),
            },
        ),
        NpcDef(
            id="ursula",
            name="Doña Úrsula",
            age=58,
            occupation="Partera y curandera",
            description=(
                "Recibió a medio barrio. Sabe leer, cosa rara en una mujer de su edad, "
                "y sabe callar, cosa más rara todavía."
            ),
            home="casa_ursula",
            routine=((7, 11, "pozo"), (11, 14, "plaza"), (14, 18, "iglesia")),
            start={"affection": 18, "trust": 22, "familiarity": 12, "interest": 0},
            visits={
                "fria": (
                    "Doña Úrsula te mira las manos antes que la cara y no dice nada.",
                    "«Andá con Dios», alcanza, y sigue con sus yerbas.",
                ),
                "tibia": (
                    "Doña Úrsula te ofrece asiento en el pozo y te pregunta si dormís bien.",
                    "«Los muchachos que no duermen son los que se van», dice, sin mirarte.",
                ),
                "cercana": (
                    "Doña Úrsula te explica que a tu madre la atendió ella, un 29 de "
                    "septiembre, con lluvia.",
                    "«Yo me acuerdo de la fecha. Y de lo que anotaron después», agrega.",
                ),
            },
        ),
        NpcDef(
            id="nicanor",
            name="Nicanor",
            age=44,
            occupation="Cartero",
            description=(
                "Reparte las cartas del pueblo y algunas del cuartel. Camina despacio "
                "y sabe más de lo que cuenta."
            ),
            home="casa_nicanor",
            routine=((6, 9, "plaza"), (9, 12, "almacen"), (14, 18, "plaza")),
            start={"affection": 12, "trust": 15, "familiarity": 8, "interest": 0},
            visits={
                "fria": (
                    "Nicanor ordena sobres en silencio y te saluda con la cabeza.",
                    "«Si esperás carta, no llegó», dice, y sigue.",
                ),
                "tibia": (
                    "Nicanor te cuenta que esta semana salieron tres cartas para el Chaco "
                    "y ninguna volvió.",
                    "«Yo sólo reparto», aclara, como si le pesara.",
                ),
                "cercana": (
                    "Nicanor te aparta del mostrador y baja la voz.",
                    "«Si te viene algo con sello del cuartel, avisame antes de abrirlo.»",
                ),
            },
        ),
        NpcDef(
            id="vera",
            name="Sargento Vera",
            age=36,
            occupation="Reclutador",
            description=(
                "Recorre el pueblo con una lista bajo el brazo. Trata de usted a los "
                "viejos y de vos a los muchachos, y nunca se le borra la sonrisa."
            ),
            home="casa_vera",
            routine=((8, 12, "plaza"), (15, 17, "almacen")),
            start={"affection": 0, "trust": 0, "familiarity": 5, "interest": 0},
            visits={
                "fria": (
                    "El sargento Vera te mira como si ya te tuviera anotado en algún lado.",
                    "«¿Edad?» pregunta, y no espera la respuesta para escribir.",
                ),
                "tibia": (
                    "Vera se ríe de algo que no dijiste y guarda la libreta.",
                    "«Los muchachos como vos son los que mejor aguantan el monte», dice.",
                ),
                "cercana": (
                    "Vera te ofrece un cigarrillo y habla del Chaco como de un campo.",
                    "«Allá se hace patria. Acá se hace pan», dice, y te mira.",
                ),
            },
        ),
        NpcDef(
            id="padre_ignacio",
            name="Padre Ignacio",
            age=62,
            occupation="Sacerdote",
            description=(
                "Párroco del pueblo desde hace treinta años. Sabe leer latín y sabe "
                "callar. Quien se confiesa con él, se va más liviano."
            ),
            home="iglesia",
            routine=((6, 12, "iglesia"), (14, 18, "plaza")),
            start={"affection": 25, "trust": 30, "familiarity": 15, "interest": 0},
            visits={
                "fria": (
                    "El padre Ignacio te bendice sin mirarte y sigue con la misa.",
                    "«Rezá por los que se fueron», alcanza.",
                ),
                "tibia": (
                    "El padre te pregunta si estás yendo a misa y te ofrece un asiento.",
                    "«La fe no te libra del Chaco, pero te ayuda a aguantar», dice.",
                ),
                "cercana": (
                    "El padre te aparta después de misa y te pregunta por tu familia.",
                    "«Si alguna vez necesitás un papel, vení a verme. Yo guardo copias.»",
                ),
            },
        ),
        NpcDef(
            id="dona_mercedes",
            name="Doña Mercedes",
            age=46,
            occupation="Lavandera",
            description=(
                "Lava la ropa del barrio en el pozo. Sabe todo lo que pasa porque "
                "todo pasa por sus manos."
            ),
            home="casa_mercedes",
            routine=((6, 11, "pozo"), (11, 14, "plaza"), (14, 18, "pozo")),
            start={"affection": 15, "trust": 12, "familiarity": 20, "interest": 0},
            visits={
                "fria": (
                    "Doña Mercedes te mira por encima del balde y no suelta el jabón.",
                    "«El pozo es de todos, pero el chisme es mío», dice.",
                ),
                "tibia": (
                    "Mercedes te cuenta quién se fue al frente y quién se quedó.",
                    "«Los que se van dejan la ropa. Yo la guardo por si vuelven.»",
                ),
                "cercana": (
                    "Mercedes te convida un mate y baja la voz.",
                    "«Si te llega una carta del cuartel, no la abras solo. Vení.»",
                ),
            },
        ),
        NpcDef(
            id="teniente_ortega",
            name="Teniente Ortega",
            age=29,
            occupation="Oficial del cuartel",
            description=(
                "Joven oficial que vino del sur. Educado, frío, y con una lista "
                "más larga que la del sargento Vera."
            ),
            home="casa_ortega",
            routine=((8, 13, "cuartel"), (15, 17, "plaza")),
            start={"affection": 0, "trust": 0, "familiarity": 3, "interest": 0},
            visits={
                "fria": (
                    "El teniente Ortega te mira como si ya supiera tu nombre.",
                    "«El patriotismo no se declara, se demuestra», dice.",
                ),
                "tibia": (
                    "Ortega te ofrece un cigarrillo y habla del frente como de un aula.",
                    "«Allá se enseña a ser hombre. Acá se enseña a esconderse.»",
                ),
                "cercana": (
                    "Ortega te llama aparte y te pregunta por tu familia.",
                    "«Si algún día querés servir, avisame. Yo te anoto primero.»",
                ),
            },
        ),
    )
}


def get(npc_id: str) -> NpcDef:
    try:
        return NPCS[npc_id]
    except KeyError as exc:
        raise KeyError(f"Personaje desconocido: {npc_id}") from exc


def visitable_ids() -> list[str]:
    return list(NPCS)
