"""Acontecimientos (GDD §14): definiciones de contenido.

Este archivo es **sólo datos**. El motor (`engine/events.py`) interpreta los
campos; acá se decide qué pasa, cuándo, dónde y qué cuesta.

Campos que importan al escribir contenido:

* `day_min` / `day_max`: ventana en días desde el inicio de la partida.
* `periods` / `locations`: cuándo y dónde puede saltar.
* `requires_flags` (todas) / `any_flags` (alguna) / `forbids_flags` (ninguna).
* `requires_events`: eventos que ya tienen que haber ocurrido.
* `conditions`: rangos sobre necesidades, atributos, `suspicion`,
  `credibility`, `pa`, `days` o relaciones (`npc:juana:affection`).
* `time_cost`: minutos que consume la escena (se cobran al resolverla).
* `chance` / `cooldown_days` / `once`: azar y repetición.
* `choices[].requires_flags` / `requires_items`: opciones que sólo aparecen si
  el jugador se ganó el derecho a elegirlas.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Choice:
    id: str
    text: str
    effects: dict = field(default_factory=dict)
    requires_flags: tuple[str, ...] = ()
    requires_items: tuple[tuple[str, int], ...] = ()

    def is_available(self, flags: list[str], items: dict[str, int]) -> bool:
        if self.requires_flags and not set(self.requires_flags) <= set(flags):
            return False
        for item_id, cantidad in self.requires_items:
            if items.get(item_id, 0) < cantidad:
                return False
        return True


@dataclass(frozen=True)
class EventDef:
    id: str
    title: str
    text: str
    priority: int = 0
    periods: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    day_min: int = 0
    day_max: int | None = None
    requires_flags: tuple[str, ...] = ()
    any_flags: tuple[str, ...] = ()
    forbids_flags: tuple[str, ...] = ()
    requires_events: tuple[str, ...] = ()
    conditions: dict = field(default_factory=dict)
    chance: float = 1.0
    cooldown_days: int = 0
    once: bool = True
    time_cost: int = 0
    choices: tuple[Choice, ...] = ()
    effects: dict = field(default_factory=dict)


EVENTS: dict[str, EventDef] = {
    evento.id: evento
    for evento in (
        # ------------------------------------------------------------------
        # Cadena de la identidad falsa
        # ------------------------------------------------------------------
        EventDef(
            id="aviso_movilizacion",
            title="Aviso en la plaza",
            text=(
                "Un sargento y dos soldados recorren el almacén con una lista. "
                "Preguntan por los mozos del barrio, uno por uno, y anotan la edad "
                "que cada familia declara. Don Ramón contesta por vos antes de que "
                "abras la boca: «Dieciséis, mi sargento. Todavía es un chico.»"
            ),
            priority=6,
            day_min=4,
            periods=("manana",),
            locations=("almacen", "plaza"),
            choices=(
                Choice(
                    id="mostrar_acta",
                    text="Mostrar el acta falsificada y sostener la mirada",
                    effects={
                        "suspicion": 5,
                        "credibility": -5,
                        "flags": ["mostro_acta"],
                    },
                ),
                Choice(
                    id="decir_que_la_tiene_en_casa",
                    text="Decir que el acta quedó en tu casa",
                    effects={
                        "suspicion": 15,
                        "credibility": -8,
                        "flags": ["evadio_control"],
                    },
                ),
                Choice(
                    id="dejar_hablar_a_ramon",
                    text="Callarte y dejar que don Ramón responda",
                    effects={
                        "suspicion": 1,
                        "npc": {"ramon": {"trust": 4}},
                        "flags": ["ramon_te_cubrio"],
                    },
                ),
            ),
        ),
        EventDef(
            id="juana_secreto",
            title="Juana quiere saber",
            text=(
                "Juana te aparta detrás de las bolsas de poroto. «Escuché lo del "
                "sargento. ¿Qué vas a hacer cuando vuelvan?» Te mira fijo, con el "
                "canasto en la cadera, y baja la voz: «Yo puedo decir que somos "
                "primos. Pero necesito saber qué contestás vos.»"
            ),
            priority=7,
            requires_events=("aviso_movilizacion",),
            periods=("manana", "tarde"),
            locations=("almacen", "plaza"),
            choices=(
                Choice(
                    id="contarle_todo",
                    text="Contarle que tenés dieciocho y que el acta miente",
                    effects={
                        "npc": {"juana": {"trust": 10, "affection": 4}},
                        "flags": ["juana_aliada"],
                    },
                ),
                Choice(
                    id="mentirle",
                    text="Decirle que no pasa nada, que exagerás",
                    effects={
                        "npc": {"juana": {"trust": -10, "affection": -3}},
                        "suspicion": 2,
                    },
                ),
                Choice(
                    id="cambiar_de_tema",
                    text="Preguntarle por su familia y salir del paso",
                    effects={"npc": {"juana": {"affection": -4}}},
                ),
            ),
        ),
        EventDef(
            id="investigacion",
            title="Te están investigando",
            text=(
                "Nicanor te alcanza un sobre sin mirarte. Adentro hay una nota: el "
                "cuartel abrió un expediente sobre vos. Preguntaron por tu familia, "
                "por tu trabajo, por si alguien te cubre. «No es que yo quiera "
                "decirte», murmura Nicanor, «pero el sargento Vera anduvo por tu "
                "barrio preguntando.»"
            ),
            priority=8,
            day_min=14,
            any_flags=("mostro_acta", "evadio_control"),
            periods=("manana", "tarde"),
            effects={
                "suspicion": 12,
                "credibility": -5,
                "flags": ["investigado"],
            },
        ),
        EventDef(
            id="orden_de_conscripcion",
            title="Orden de conscripción",
            text=(
                "El teniente Ortega aparece en tu puerta con un papel firmado. «Tu "
                "nombre salió en la lista. Mañana, a las seis, en el cuartel. No "
                "hay apelación.» Te mira sin odio, sin alegría: es un trámite. "
                "Don Ramón está en el umbral y esta vez no puede decir nada."
            ),
            priority=9,
            day_min=20,
            conditions={"suspicion": [30, 100]},
            periods=("manana", "tarde"),
            effects={
                "flags": ["orden_conscripcion"],
            },
        ),
        EventDef(
            id="control_de_documentos",
            title="Control en la esquina",
            text=(
                "El sargento Vera te espera en la esquina con la libreta abierta. "
                "«A ver, mozo. Documento.» Detrás de él hay dos soldados que no "
                "miran a otro lado. En el almacén, don Ramón se asoma al umbral y "
                "vuelve a entrar: hoy no puede ayudarte."
            ),
            priority=6,
            day_min=12,
            periods=("manana", "tarde"),
            locations=("almacen", "plaza"),
            choices=(
                Choice(
                    id="mostrar_acta",
                    text="Entregar el acta falsificada sin decir nada",
                    effects={
                        "suspicion": 3,
                        "credibility": -5,
                        "flags": ["mostro_acta", "control_pasado"],
                    },
                ),
                Choice(
                    id="decir_que_esta_en_tramite",
                    text="Decir que la estás tramitando en Asunción",
                    effects={
                        "suspicion": 9,
                        "credibility": -9,
                        "flags": ["evadio_control"],
                    },
                ),
                Choice(
                    id="llamar_a_ramon",
                    text="Pedirle a don Ramón que responda por vos",
                    requires_flags=("ramon_te_cubrio",),
                    effects={
                        "suspicion": 1,
                        "npc": {"ramon": {"trust": -3, "affection": 4}},
                        "flags": ["control_pasado"],
                    },
                ),
            ),
        ),
        EventDef(
            id="citacion_al_cuartel",
            title="Papel con sello",
            text=(
                "Nicanor te alcanza un sobre sin mirarte a los ojos. Adentro hay "
                "una citación: el jueves, a las ocho, en el cuartel. No dice para "
                "qué. Dice que la ausencia se considera deserción, y la palabra "
                "queda dando vueltas toda la tarde."
            ),
            priority=8,
            day_min=18,
            any_flags=("mostro_acta", "evadio_control"),
            periods=("manana", "tarde"),
            time_cost=30,
            choices=(
                Choice(
                    id="presentarse",
                    text="Presentarte en el cuartel y aguantar lo que venga",
                    effects={
                        "suspicion": -12,
                        "credibility": 6,
                        "needs": {"fatigue": 22, "health": -3},
                        "flags": ["fue_al_cuartel"],
                    },
                ),
                Choice(
                    id="no_presentarse",
                    text="No ir. Que te busquen si quieren",
                    effects={
                        "suspicion": 15,
                        "flags": ["falto_a_la_citacion"],
                    },
                ),
                Choice(
                    id="mandar_a_juana",
                    text="Mandar a Juana a decir que estás enfermo",
                    requires_flags=("juana_aliada",),
                    effects={
                        "suspicion": -4,
                        "npc": {"juana": {"trust": -6, "affection": 3}},
                        "flags": ["juana_fue_al_cuartel"],
                    },
                ),
            ),
        ),
        EventDef(
            id="allanamiento",
            title="Golpes en la puerta",
            text=(
                "Tres golpes, y la puerta se abre antes de que contestes. El sargento "
                "Vera entra con un soldado y mira la pieza como si fuera un mapa. "
                "«Buscamos documentación irregular», dice. El cajón del ropero está "
                "a dos pasos y las dos actas están adentro."
            ),
            priority=9,
            day_min=20,
            conditions={"suspicion": [35, 100]},
            periods=("manana", "tarde", "noche"),
            choices=(
                Choice(
                    id="entregar_la_falsa",
                    text="Entregar el acta falsificada y rezar",
                    effects={
                        "suspicion": -10,
                        "credibility": -10,
                        "flags": ["entrego_acta_falsa"],
                    },
                ),
                Choice(
                    id="decir_que_no_hay_nada",
                    text="Abrir el cajón vos y decir que no hay nada",
                    effects={
                        "suspicion": 8,
                        "credibility": -4,
                        "needs": {"fatigue": 8},
                    },
                ),
                Choice(
                    id="quemar_el_acta",
                    text="Quemar el acta verdadera antes de que la encuentren",
                    requires_items=(("acta_verdadera", 1),),
                    effects={
                        "consume": {"acta_verdadera": 1},
                        "suspicion": -18,
                        "credibility": 8,
                        "flags": ["quemo_el_acta"],
                        "needs": {"fatigue": 5},
                    },
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # El barrio se vacía
        # ------------------------------------------------------------------
        EventDef(
            id="despedida_de_aurelio",
            title="Aurelio se va",
            text=(
                "Aurelio está en el andén con una bolsa al hombro y el uniforme "
                "que le queda grande. Su tío no vino. «Es un mes, me dijeron. "
                "Un mes y volvemos.» Se ríe, y después se queda mirando el suelo "
                "porque no sabe qué más decir."
            ),
            priority=8,
            day_min=8,
            periods=("tarde",),
            locations=("plaza",),
            time_cost=120,
            effects={
                "needs": {"fatigue": 10},
                "flags": ["aurelio_en_el_frente"],
            },
            choices=(
                Choice(
                    id="darle_el_panuelo",
                    text="Darle el pañuelo bordado para que no vuelva con las manos vacías",
                    requires_items=(("panuelo", 1),),
                    effects={
                        "consume": {"panuelo": 1},
                        "npc": {"aurelio": {"affection": 12, "trust": 8}},
                        "flags": ["panuelo_a_aurelio"],
                    },
                ),
                Choice(
                    id="prometer_cuidar_al_tio",
                    text="Prometerle que vas a mirar por su tío",
                    effects={
                        "npc": {"aurelio": {"trust": 12}},
                        "flags": ["prometio_cuidar_al_tio"],
                    },
                ),
                Choice(
                    id="no_decir_nada",
                    text="Quedarte callado y darle la mano",
                    effects={"npc": {"aurelio": {"affection": 4}}},
                ),
            ),
        ),
        EventDef(
            id="carta_del_frente",
            title="Llegó una carta",
            text=(
                "El cartero deja un sobre en el almacén y no lo firma nadie que "
                "conozcas. La letra es de Aurelio y viene del Chaco: habla del calor, "
                "del agua que sabe a barro y de un compañero que ya no está. Al final "
                "pregunta por vos, por el barrio, por si sigue todo igual."
            ),
            priority=4,
            day_min=10,
            requires_events=("despedida_de_aurelio",),
            effects={
                "flags": ["carta_de_aurelio"],
                "needs": {"fatigue": 3},
                "npc": {"aurelio": {"affection": 3}},
            },
        ),
        EventDef(
            id="el_taller_cierra",
            title="Cierran el taller",
            text=(
                "El tío de Aurelio pasa un alambre por la puerta del taller y cuelga "
                "un cartel escrito a lápiz: «Cerrado hasta que vuelva». Nadie compra "
                "muebles en tiempos de guerra. Celia se queda con la costura y con "
                "menos encargos cada semana."
            ),
            priority=3,
            day_min=15,
            effects={"flags": ["taller_cerrado"]},
        ),
        EventDef(
            id="primera_lista_de_bajas",
            title="Leen una lista",
            text=(
                "Un hombre sube al banco de la plaza con el diario doblado y lee en "
                "voz alta. Son nombres cortos, repetidos, de pueblos que nadie del "
                "barrio conoce. Cuando termina, alguien pregunta por Boquerón y el "
                "hombre dice que no sabe, que él sólo lee lo que está escrito."
            ),
            priority=6,
            day_min=26,
            requires_events=("carta_del_frente",),
            periods=("tarde",),
            locations=("plaza",),
            choices=(
                Choice(
                    id="acercarte",
                    text="Acercarte a preguntar por los nombres",
                    effects={
                        "needs": {"fatigue": 6},
                        "flags": ["sabe_leer_listas"],
                        "npc": {"nicanor": {"trust": 4}},
                    },
                ),
                Choice(
                    id="quedarte_lejos",
                    text="Quedarte en el borde de la plaza, sin preguntar",
                    effects={"needs": {"fatigue": -2}},
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Escasez
        # ------------------------------------------------------------------
        EventDef(
            id="suben_los_precios",
            title="Subió todo",
            text=(
                "Don Ramón cambia los carteles del almacén uno por uno, con la letra "
                "apretada de quien no quiere hacerlo. «No es que yo quiera», dice sin "
                "que le preguntes. «El poroto llega con flete del ejército, y el "
                "ejército cobra.»"
            ),
            priority=4,
            day_min=14,
            effects={"flags": ["precios_altos"]},
        ),
        EventDef(
            id="acaparamiento",
            title="Alguien está guardando",
            text=(
                "Detrás del almacén hay bolsas apiladas que no son de don Ramón. "
                "Un vecino las trae de noche y las vuelve a llevar de día. Aurora lo "
                "vio y no sabe qué hacer: «Si le digo a papá, se arma un lío. Si no "
                "le digo, seguimos pagando de más.»"
            ),
            priority=5,
            day_min=17,
            requires_flags=("precios_altos",),
            locations=("almacen",),
            periods=("manana", "tarde"),
            choices=(
                Choice(
                    id="avisar_a_ramon",
                    text="Contarle a don Ramón",
                    effects={
                        "npc": {"ramon": {"trust": 8}, "aurora": {"affection": 4}},
                        "flags": ["denuncio_acaparador"],
                    },
                ),
                Choice(
                    id="comprar_de_mas",
                    text="Aprovechar y comprar barato al acaparador",
                    effects={
                        "money": -6,
                        "inventory": {"chipa": 6, "mandioca": 3},
                        "npc": {"aurora": {"trust": -8}},
                        "flags": ["compro_al_acaparador"],
                    },
                ),
                Choice(
                    id="no_meterme",
                    text="Hacerte el que no viste nada",
                    effects={"npc": {"aurora": {"trust": -3}}},
                ),
            ),
        ),
        EventDef(
            id="vuelve_el_poroto",
            title="Llegó el poroto",
            text=(
                "Un camión de la intendencia deja dos bolsas en la puerta del almacén "
                "y se va sin firmar. Don Ramón abre una, mete la mano y la saca llena "
                "de poroto seco. «Bajamos los precios», dice, y por un rato parece "
                "que el pueblo vuelve a ser el de antes."
            ),
            priority=5,
            day_min=30,
            requires_flags=("precios_altos",),
            effects={"unflags": ["precios_altos"], "flags": ["volvio_el_poroto"]},
        ),
        # ------------------------------------------------------------------
        # Vida cotidiana y afectos
        # ------------------------------------------------------------------
        EventDef(
            id="velorio",
            title="Velorio en la iglesia",
            text=(
                "Se murió el padre de una chica del barrio, de viejo, en la cama. "
                "La iglesia está llena de mujeres de negro y de hombres que no saben "
                "dónde poner las manos. Celia está en el fondo, sola, con un rosario "
                "entre los dedos."
            ),
            priority=5,
            day_min=6,
            periods=("noche",),
            locations=("iglesia", "plaza"),
            choices=(
                Choice(
                    id="quedarte",
                    text="Quedarte toda la noche acompañando",
                    effects={
                        "needs": {"fatigue": 25, "health": -2},
                        "attributes": {"reputation": 4},
                        "npc": {"celia": {"affection": 6, "trust": 4}},
                        "flags": ["velo_toda_la_noche"],
                    },
                ),
                Choice(
                    id="volver_temprano",
                    text="Dar el pésame y volver a dormir",
                    effects={"needs": {"fatigue": 5}},
                ),
            ),
        ),
        EventDef(
            id="aurora_y_el_padre",
            title="Discusión en el almacén",
            text=(
                "Aurora y don Ramón discuten detrás del mostrador. Ella quiere que "
                "le suba el sueldo a Juana, que hace el trabajo de dos. Él dice que "
                "no hay con qué. Cuando te ven, los dos se callan y esperan que "
                "digas algo."
            ),
            priority=5,
            day_min=9,
            periods=("tarde",),
            locations=("almacen",),
            choices=(
                Choice(
                    id="apoyar_a_aurora",
                    text="Apoyar a Aurora: Juana hace el trabajo de dos",
                    effects={
                        "npc": {"aurora": {"affection": 8}, "ramon": {"trust": -5}},
                        "flags": ["apoyo_a_juana"],
                    },
                ),
                Choice(
                    id="apoyar_a_ramon",
                    text="Apoyar a don Ramón: no hay con qué pagar",
                    effects={
                        "npc": {"ramon": {"trust": 8}, "aurora": {"affection": -6}},
                    },
                ),
                Choice(
                    id="no_meterte",
                    text="Decir que es cosa de ellos y volver al mostrador",
                    effects={"npc": {"aurora": {"affection": -2}}},
                ),
            ),
        ),
        EventDef(
            id="celia_en_la_iglesia",
            title="Celia en el banco de atrás",
            text=(
                "Celia no está cosiendo. Está sentada en el último banco, con la "
                "costura en el regazo y la aguja clavada en la tela como si se hubiera "
                "olvidado de sacarla. Cuando te ve, no se sorprende: corre la cartera "
                "para hacerte lugar."
            ),
            priority=3,
            conditions={"npc:celia:familiarity": [20, 100]},
            periods=("tarde",),
            locations=("iglesia",),
            choices=(
                Choice(
                    id="sentarte_al_lado",
                    text="Sentarte al lado y no decir nada",
                    effects={"npc": {"celia": {"affection": 7, "trust": 5}}},
                ),
                Choice(
                    id="preguntarle_que_le_pasa",
                    text="Preguntarle qué le pasa",
                    effects={
                        "npc": {"celia": {"trust": 9, "familiarity": 4}},
                        "flags": ["celia_confio"],
                    },
                ),
            ),
        ),
        EventDef(
            id="juana_cocina_para_dos",
            title="Juana cocinó de más",
            text=(
                "Juana aparece en tu puerta con una olla tapada con un repasador. "
                "«Me salió de más», dice, y no es verdad: cocinó para dos. Se sienta "
                "en el cajón, se sirve primero a vos y después se queda mirando cómo "
                "comés, como si eso fuera la cena."
            ),
            priority=6,
            conditions={"npc:juana:affection": [40, 100]},
            requires_flags=("juana_aliada",),
            periods=("noche",),
            locations=("casa", "plaza"),
            time_cost=90,
            effects={
                "needs": {"nutrition": 30, "fatigue": -6},
                "npc": {"juana": {"affection": 6, "familiarity": 4}},
                "flags": ["ceno_con_juana"],
            },
        ),
        EventDef(
            id="mate_en_la_plaza",
            title="Mate en la plaza",
            text=(
                "Alguien dejó una pava y un mate sobre el banco de la plaza. No hay "
                "dueño a la vista. Al rato aparece un vecino, ceba uno, lo pasa, y "
                "la ronda sigue como si el país no se estuviera partiendo en dos."
            ),
            priority=1,
            periods=("tarde",),
            locations=("plaza",),
            chance=0.35,
            cooldown_days=3,
            once=False,
            effects={"needs": {"fatigue": -4, "hydration": 5}},
        ),
        # ------------------------------------------------------------------
        # Cuerpo
        # ------------------------------------------------------------------
        EventDef(
            id="fiebre",
            title="Te sube la fiebre",
            text=(
                "Empieza en la nuca y baja por la espalda. A media tarde estás "
                "temblando en la cama, con la camisa pegada y los dientes apretados. "
                "Doña Úrsula diría que es el agua. Tu madre diría que es el susto."
            ),
            priority=4,
            conditions={"health": [0, 35]},
            cooldown_days=5,
            once=False,
            choices=(
                Choice(
                    id="tomar_quinina",
                    text="Tomar la quinina que guardabas",
                    requires_items=(("quinina", 1),),
                    effects={
                        "consume": {"quinina": 1},
                        "needs": {"health": 14, "fatigue": -8},
                    },
                ),
                Choice(
                    id="pagar_a_ursula",
                    text="Mandar a buscar a doña Úrsula y pagarle",
                    requires_flags=(),
                    effects={
                        "money": -3,
                        "needs": {"health": 10, "fatigue": -5},
                        "npc": {"ursula": {"trust": 5, "familiarity": 4}},
                    },
                ),
                Choice(
                    id="aguantar",
                    text="Aguantar con agua y frazada",
                    effects={
                        "needs": {"health": -6, "fatigue": 12},
                        "flags": ["aguanto_la_fiebre"],
                    },
                ),
            ),
        ),
        EventDef(
            id="desmayo_por_sed",
            title="Se te nubla la vista",
            text=(
                "El suelo se mueve. Te agarrás del marco de la puerta, pero la mano "
                "no llega. Cuando volvés en sí estás sentado en el piso, con la boca "
                "seca como papel y la camisa empapada."
            ),
            priority=9,
            conditions={"hydration": [0, 20]},
            cooldown_days=2,
            once=False,
            effects={
                "needs": {"health": -8, "fatigue": 10},
                "flags": ["se_desmayo"],
            },
        ),
        EventDef(
            id="hambre_extrema",
            title="El estómago aprieta",
            text=(
                "Hace dos días que no comés bien. Te tiemblan las manos al anotar y "
                "don Ramón te mira de reojo sin decir nada."
            ),
            priority=4,
            conditions={"nutrition": [0, 12]},
            cooldown_days=5,
            once=False,
            effects={"needs": {"health": -6, "fatigue": 6}},
        ),
        EventDef(
            id="charla_de_esquina",
            title="Charla de esquina",
            text=(
                "En la plaza, dos vecinos discuten sobre el precio del poroto. Uno "
                "dice que es culpa de la guerra; el otro, que es culpa de los que "
                "acaparan. Cuando te ven, te piden opinión."
            ),
            priority=1,
            locations=("plaza",),
            periods=("tarde",),
            chance=0.2,
            cooldown_days=2,
            once=False,
            conditions={"fatigue": [0, 70]},
            effects={"needs": {"fatigue": -2}},
        ),
        # ------------------------------------------------------------------
        # Línea histórica
        # ------------------------------------------------------------------
        EventDef(
            id="rumor_de_boqueron",
            title="Noticia del Chaco",
            text=(
                "En la plaza se junta gente alrededor de un hombre que lee el diario "
                "en voz alta. Hablan de Boquerón, de un fortín que cambió de manos y "
                "de nombres que nadie del barrio conoce. Alguien dice que la guerra "
                "va a terminar antes de fin de año. Nadie lo cree."
            ),
            priority=5,
            day_min=28,
            effects={"flags": ["oyo_noticia_boqueron"]},
        ),
        # ------------------------------------------------------------------
        # Línea histórica: Boquerón cayó
        # ------------------------------------------------------------------
        EventDef(
            id="boqueron_cayo",
            title="Cayó Boquerón",
            text=(
                "El diario trae la noticia en primera plana: Boquerón cayó. Tres "
                "semanas de combate, y el fortín cambió de manos. En el barrio nadie "
                "habla de otra cosa. Doña Mercedes cuenta que tres familias del "
                "pueblo recibieron cartas del frente esta semana."
            ),
            priority=7,
            day_min=29,
            effects={
                "flags": ["boqueron_cayo"],
                "needs": {"fatigue": 5},
                "attributes": {"reputation": 1},
            },
        ),
        EventDef(
            id="lista_de_bajas",
            title="Lista de bajas",
            text=(
                "El teniente Ortega lee una lista en la plaza. Nombres, grados, "
                "pueblos. Cuando termina, el silencio dura un rato largo. Alguien "
                "pregunta por Aurelio y Ortega mira la lista otra vez: «No está en "
                "esta. Eso no quiere decir nada.»"
            ),
            priority=8,
            day_min=32,
            requires_events=("boqueron_cayo",),
            locations=("plaza",),
            periods=("tarde",),
            choices=(
                Choice(
                    id="preguntar_por_aurelio",
                    text="Preguntarle al teniente por Aurelio",
                    effects={
                        "npc": {"ortega": {"trust": -3, "familiarity": 5}},
                        "flags": ["pregunto_por_aurelio"],
                    },
                ),
                Choice(
                    id="callarse",
                    text="No preguntar nada y volver a casa",
                    effects={"needs": {"fatigue": 4}},
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Rutas de relación
        # ------------------------------------------------------------------
        EventDef(
            id="juana_te_necesita",
            title="Juana te necesita",
            text=(
                "Juana aparece en tu puerta a la noche, sin canasto, sin delantal. "
                "«Mi hermano se fue al frente. Mi madre no para de llorar. Vos sos "
                "el único que puede quedarse con ella un rato.» Te mira como si "
                "eso fuera lo único que quedara."
            ),
            priority=6,
            requires_flags=("juana_aliada",),
            conditions={"npc:juana:affection": [45, 100]},
            day_min=20,
            periods=("noche",),
            locations=("casa", "plaza"),
            choices=(
                Choice(
                    id="quedarse_con_la_madre",
                    text="Quedarte con la madre de Juana",
                    effects={
                        "needs": {"fatigue": 15, "health": -3},
                        "npc": {"juana": {"trust": 12, "affection": 8}},
                        "flags": ["cuido_a_la_madre_de_juana"],
                    },
                ),
                Choice(
                    id="decir_que_no_podes",
                    text="Decirle que no podés, que tenés tus cosas",
                    effects={
                        "npc": {"juana": {"trust": -15, "affection": -8}},
                        "flags": ["rechazo_a_juana"],
                    },
                ),
            ),
        ),
        EventDef(
            id="celia_te_escribe",
            title="Celia te escribe",
            text=(
                "Una hoja doblada aparece debajo de tu puerta. La letra es de Celia: "
                "«No sé por qué te escribo. Supongo que porque no tengo a quién "
                "más. El taller cerró y mi padre quiere que me case con un viudo del "
                "pueblo de al lado. ¿Vos qué harías?»"
            ),
            priority=5,
            requires_flags=("celia_confio",),
            conditions={"npc:celia:trust": [20, 100]},
            day_min=25,
            periods=("noche",),
            locations=("casa",),
            choices=(
                Choice(
                    id="responder_que_se_quede",
                    text="Responderle que se quede, que la costura vuelve",
                    effects={
                        "npc": {"celia": {"affection": 10, "trust": 8}},
                        "flags": ["celia_se_quedo"],
                    },
                ),
                Choice(
                    id="no_responder",
                    text="No responder. No es tu problema",
                    effects={
                        "npc": {"celia": {"trust": -12, "affection": -6}},
                    },
                ),
            ),
        ),
        # ------------------------------------------------------------------
        # Finales
        # ------------------------------------------------------------------
        EventDef(
            id="final_conscripto",
            title="Te llevan",
            text=(
                "El teniente Ortega aparece con dos soldados y una orden. «Vos. "
                "Mañana, a las seis, en el cuartel.» No pregunta la edad. No mira "
                "el acta. La lista ya tiene tu nombre. Don Ramón te mira desde el "
                "umbral del almacén y no dice nada, porque no hay nada que decir."
            ),
            priority=10,
            day_min=40,
            conditions={"suspicion": [35, 100]},
            effects={
                "flags": ["final_conscripto"],
            },
        ),
        EventDef(
            id="final_el_barrio",
            title="Te quedás",
            text=(
                "Pasan los meses y el barrio sigue. El almacén de don Ramón abre "
                "todos los días. Juana sigue en el mostrador. Celia volvió a coser. "
                "Aurelio no volvió, pero su tío sigue en el taller. Vos seguís "
                "acá, con 16 años en el acta y 19 en el cuerpo, y nadie vino a "
                "buscarte. Alguien te pregunta si no te da miedo y vos decís que "
                "no, que el miedo es otra cosa."
            ),
            priority=10,
            day_min=50,
            conditions={"suspicion": [0, 20]},
            requires_flags=("cuido_a_la_madre_de_juana",),
            effects={
                "flags": ["final_el_barrio"],
            },
        ),
        EventDef(
            id="final_la_huida",
            title="Te vas",
            text=(
                "Una noche, sin avisar, tomás la valija y caminás hacia la estación. "
                "No es cobardía: es que el acta ya no sirve, el sargento ya sabe, "
                "y el barrio ya no es un lugar donde puedas quedarte. Dejás una "
                "carta para Juana y otra para don Ramón. En la estación, el tren "
                "llega a las cinco. Es el mismo tren que lleva a los soldados."
            ),
            priority=10,
            day_min=40,
            conditions={"suspicion": [80, 100]},
            effects={
                "flags": ["final_la_huida"],
            },
        ),
        EventDef(
            id="campo_jordan",
            title="Campo Jord?n",
            text=(
                "Llega la noticia: en Campo Jord?n se pele? cuerpo a cuerpo. Los "
                "diarios hablan de un fort?n que cambi? de manos otra vez. En el "
                "barrio, los que tienen parientes en el frente no duermen. Do?a "
                "Mercedes dice que esta semana salieron cuatro cartas y ninguna "
                "volvi?."
            ),
            priority=6,
            day_min=90,
            effects={
                "flags": ["campo_jordan"],
                "needs": {"fatigue": 4},
                "attributes": {"reputation": 1},
            },
        ),
        EventDef(
            id="nanawa",
            title="Nanawa",
            text=(
                "El diario trae una lista larga. Nanawa fue un infierno, dicen. "
                "Los nombres se leen en la plaza y alguien llora. El teniente "
                "Ortega dice que la guerra va a durar m?s de lo que todos creen, "
                "y que los mozos del pueblo van a tener que ir igual."
            ),
            priority=7,
            day_min=120,
            effects={
                "flags": ["nanawa"],
                "needs": {"fatigue": 6, "health": -2},
            },
        ),
        EventDef(
            id="muerte",
            title="Fin de la partida",
            text=(
                "El cuerpo no aguant? m?s. Los d?as sin comer, sin beber, sin dormir "
                "pasaron factura. En el barrio dicen que te encontraron en la cama, "
                "con la camisa pegada y los ojos abiertos. Don Ram?n cerr? el almac?n "
                "por una semana. Juana no vino a trabajar. El pueblo sigui? sin vos."
            ),
            priority=10,
            requires_flags=("muerto",),
            effects={"flags": ["final_muerte"]},
        ),
    )
}


def get(event_id: str) -> EventDef:
    try:
        return EVENTS[event_id]
    except KeyError as exc:
        raise KeyError(f"Acontecimiento desconocido: {event_id}") from exc
