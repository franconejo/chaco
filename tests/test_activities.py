import pytest

from engine import actions, activities
from engine.errors import EngineError
from engine.state import GameState


def nueva() -> GameState:
    return GameState.new()


def test_trabajar_solo_de_manana():
    s = nueva()
    s.clock_min = 840  # 19:00
    puede, motivo = activities.can_start(s, activities.by_id("trabajar"))
    assert puede is False
    assert motivo is not None


def test_trabajar_paga_y_mueve_al_almacen():
    s = nueva()
    actions.perform(s, "activity", {"activity": "trabajar"})
    assert s.player.money == 8
    assert s.location == "almacen"
    assert s.pa == 19
    assert s.moment().hour == 10


def test_banarse_necesita_agua():
    s = nueva()
    s.inventory = [stack for stack in s.inventory if stack.item_id != "agua"]
    puede, motivo = activities.can_start(s, activities.by_id("banarse"))
    assert puede is False
    assert "Agua" in (motivo or "")


def test_banarse_consume_agua():
    s = nueva()
    actions.perform(s, "activity", {"activity": "banarse"})
    assert s.has_item("agua", 1)


def test_buscar_agua_en_el_pozo():
    s = nueva()
    actions.perform(s, "activity", {"activity": "buscar_agua"})
    assert s.has_item("agua", 4)
    assert s.location == "pozo"


def test_comprar_en_el_almacen():
    s = nueva()
    actions.perform(s, "buy", {"item": "mandioca", "qty": 2})
    assert s.player.money == 1
    assert s.has_item("mandioca", 3)
    assert s.location == "almacen"


def test_comprar_sin_dinero():
    s = nueva()
    s.player.money = 0
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "buy", {"item": "carne_seca", "qty": 1})
    assert exc.value.code == "sin_dinero"


def test_comprar_algo_que_no_esta_a_la_venta():
    s = nueva()
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "buy", {"item": "acta_falsa", "qty": 1})
    assert exc.value.code == "no_vendible"


def test_visitar_a_juana_en_el_almacen():
    s = nueva()
    s.clock_min = 180  # 08:00
    actions.perform(s, "visit", {"npc": "juana"})
    assert s.location == "almacen"
    assert s.pa == 22
    assert s.npcs["juana"].familiarity > 25
    assert s.npcs["juana"].met is True


def test_no_se_puede_visitar_a_quien_esta_en_su_casa():
    s = nueva()
    s.clock_min = 1080  # 23:00
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "visit", {"npc": "celia"})
    assert exc.value.code == "no_disponible"


def test_listado_de_actividades():
    s = nueva()
    listado = activities.available(s)
    por_id = {a["id"]: a for a in listado}
    assert por_id["trabajar"]["available"] is True
    assert por_id["visitar"]["kind"] == "visit"
    assert por_id["comprar"]["kind"] == "buy"
