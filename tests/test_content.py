"""Contenido y mecánicas de la Fase 1.5.

Cubre lo que la fase agregó al motor: opciones condicionales, escenas que
cuestan tiempo, condiciones por relación, ausencias y precios de escasez.
"""

from data import events as catalog
from data.events import Choice, EventDef
from data.events import get as get_event
from data.items import ITEMS
from data.npcs import NPCS
from engine import actions, effects, events, prices
from engine import npc as npc_runtime
from engine.clock import moment
from engine.rng import GameRandom
from engine.state import GameState


def nueva() -> GameState:
    return GameState.new(seed=7)


def rng_de(s: GameState) -> GameRandom:
    return GameRandom(s.seed)


# ---------- opciones condicionales ----------


def test_una_opcion_solo_aparece_si_te_la_ganaste():
    s = nueva()
    s.clock_min = 12 * 1440
    s.location = "almacen"
    ev = get_event("control_de_documentos")

    sin = events.available_choices(s, ev)
    assert [c.id for c in sin] == ["mostrar_acta", "decir_que_esta_en_tramite"]

    s.flags.append("ramon_te_cubrio")
    con = events.available_choices(s, ev)
    assert "llamar_a_ramon" in [c.id for c in con]


def test_no_puedo_elegir_una_opcion_que_no_me_corresponde():
    s = nueva()
    s.clock_min = 12 * 1440
    s.location = "almacen"
    entrada = events.fire(s, get_event("control_de_documentos"))

    try:
        actions.resolve_event(s, entrada["uid"], "llamar_a_ramon")
        raise AssertionError("debió rechazar la opción bloqueada")
    except Exception as exc:  # noqa: BLE001
        assert exc.code == "opcion_no_disponible"


def test_un_evento_cuya_unica_opcion_esta_bloqueada_no_se_dispara(monkeypatch):
    s = nueva()
    ev = EventDef(
        id="solo_bloqueada",
        title="Sin salida",
        text="",
        choices=(Choice(id="a", text="a", requires_flags=("no_existe",)),),
    )
    monkeypatch.setitem(catalog.EVENTS, ev.id, ev)

    assert events.available_choices(s, ev) == []
    disparados = [e["id"] for e in events.collect(s)]
    assert "solo_bloqueada" not in disparados


# ---------- tiempo ----------


def test_una_escena_puede_costar_tiempo():
    s = nueva()
    s.clock_min = 8 * 1440
    ev = get_event("despedida_de_aurelio")
    assert ev.time_cost == 120

    entrada = events.fire(s, ev)
    assert s.clock_min == 8 * 1440  # todavía no se cobró

    events.resolve(s, entrada["uid"], "no_decir_nada")
    assert s.clock_min == 8 * 1440 + 120


def test_un_evento_sin_opciones_cobra_el_tiempo_al_dispararse():
    s = nueva()
    s.clock_min = 1080  # 23:00, en casa
    s.flags.append("juana_aliada")
    s.npcs["juana"] = npc_runtime.initial_state("juana")
    s.npcs["juana"].affection = 60

    ev = get_event("juana_cocina_para_dos")
    events.fire(s, ev)
    assert s.clock_min == 1080 + 90


# ---------- ausencias ----------


def test_un_personaje_en_el_frente_no_esta_en_ningun_lado():
    aurelio = NPCS["aurelio"]
    hora = moment(720, GameState.new().start_date)  # 17:00

    assert npc_runtime.location_of(aurelio, hora) == "plaza"
    assert (
        npc_runtime.location_of(aurelio, hora, ["aurelio_en_el_frente"])
        == npc_runtime.AWAY_LOCATION
    )


def test_no_se_puede_visitar_a_quien_esta_en_el_frente():
    s = nueva()
    s.clock_min = 1020
    s.flags.append("aurelio_en_el_frente")

    try:
        actions.perform(s, "visit", {"npc": "aurelio"})
        raise AssertionError("debió fallar")
    except Exception as exc:  # noqa: BLE001
        assert exc.code == "no_disponible"
        assert "frente" in exc.message.lower()


def test_el_listado_marca_la_ausencia():
    s = nueva()
    s.flags.append("aurelio_en_el_frente")
    ficha = next(n for n in npc_runtime.known(s) if n["id"] == "aurelio")
    assert ficha["away"] is True
    assert ficha["visitable"] is False
    assert "frente" in ficha["location_label"].lower()


# ---------- precios ----------


def test_la_escasez_encarece_el_almacen():
    s = nueva()
    assert prices.price_of(s, ITEMS["mandioca"]) == 2

    s.flags.append("precios_altos")
    assert prices.multiplier(s) == 1.5
    assert prices.price_of(s, ITEMS["mandioca"]) == 3


def test_comprar_con_escasez_cobra_el_precio_nuevo():
    s = nueva()
    s.clock_min = 360  # 11:00
    s.flags.append("precios_altos")
    s.player.money = 5

    resultado = actions.perform(s, "buy", {"item": "mandioca", "qty": 1})
    assert s.player.money == 2
    assert resultado.deltas["unit_price"] == 3


def test_volver_el_poroto_baja_los_precios():
    s = nueva()
    s.flags.append("precios_altos")
    effects.apply(s, {"unflags": ["precios_altos"]})
    assert prices.multiplier(s) == 1.0


# ---------- condiciones nuevas ----------


def test_se_puede_condicionar_por_relacion():
    s = nueva()
    s.clock_min = 780  # 18:00, tarde
    s.location = "iglesia"
    ev = get_event("celia_en_la_iglesia")

    assert events.stat_value(s, "npc:celia:familiarity") == 5.0
    assert events.conditions_ok(s, ev, rng_de(s)) is False

    s.npcs["celia"] = npc_runtime.initial_state("celia")
    s.npcs["celia"].familiarity = 30
    assert events.conditions_ok(s, ev, rng_de(s)) is True


def test_se_puede_condicionar_por_dias_transcurridos():
    s = nueva()
    s.closed_days = 9
    assert events.stat_value(s, "days") == 9.0


def test_any_flags_basta_con_una():
    s = nueva()
    s.clock_min = 18 * 1440
    ev = get_event("citacion_al_cuartel")

    assert events.conditions_ok(s, ev, rng_de(s)) is False

    s.flags.append("evadio_control")
    assert events.conditions_ok(s, ev, rng_de(s)) is True
