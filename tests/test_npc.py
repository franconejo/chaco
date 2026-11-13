from datetime import date

from data import npcs
from engine import npc
from engine.clock import moment
from engine.npc import NpcState

INICIO = date(1932, 9, 1)


def test_rutina_de_juana():
    juana = npcs.get("juana")
    assert npc.location_of(juana, moment(180, INICIO)) == "almacen"  # 08:00
    assert npc.location_of(juana, moment(780, INICIO)) == "plaza"  # 18:00
    assert npc.location_of(juana, moment(1080, INICIO)) == "casa_juana"  # 23:00


def test_casa_privada_no_es_visitable():
    celia = npcs.get("celia")
    lugar = npc.location_of(celia, moment(1080, INICIO))
    assert npc.is_reachable(lugar) is False


def test_etiquetas_de_relacion():
    assert npc.relationship_label(0) == "distante"
    assert npc.relationship_label(20) == "cordial"
    assert npc.relationship_label(50) == "cercana"
    assert npc.relationship_label(70) == "muy cercana"
    assert npc.relationship_label(95) == "íntima"


def test_ganancias_decrecientes():
    from engine.state import GameState

    s = GameState.new()
    s.npcs["juana"] = NpcState(affection=10, trust=10, familiarity=5)
    primera = npc.visit_gains(s, npcs.get("juana"))

    s.npcs["juana"] = NpcState(affection=10, trust=10, familiarity=90)
    segunda = npc.visit_gains(s, npcs.get("juana"))

    assert primera["familiarity"] > segunda["familiarity"] > 0


def test_estado_inicial_desde_la_ficha():
    estado = npc.initial_state("juana")
    assert estado.familiarity == 25
    assert estado.met is False
