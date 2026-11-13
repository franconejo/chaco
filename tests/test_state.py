from datetime import date

import pytest

from engine import actions
from engine.errors import EngineError
from engine.state import GameState

INICIO = date(1932, 9, 1)


def nueva(seed: int = 0) -> GameState:
    return GameState.new(start_date=INICIO, seed=seed)


def test_partida_nueva():
    s = nueva()
    assert s.pa == 24
    assert s.clock_min == 0
    assert s.location == "casa"
    assert s.player.money == 5
    assert s.has_item("agua", 2)
    assert s.has_item("acta_verdadera")
    m = s.moment()
    assert (m.hour, m.minute, m.period) == (5, 0, "manana")


def test_dormir_recupera_pa_pero_no_pasa_del_tope():
    s = nueva()
    r = actions.perform(s, "sleep", {"hours": 3})
    assert r.pa_before == 24
    assert s.pa == 24  # 24 - 3 + 6, recortado a 24
    assert s.player.sleep_hours_today == 3
    assert s.player.fatigue == 0.0
    assert s.moment().hour == 8


def test_dormir_recupera_pa_incluso_con_poco():
    s = nueva()
    s.pa = 1
    actions.perform(s, "sleep", {"hours": 3})
    assert s.pa == 4
    assert s.player.sleep_hours_today == 3


def test_comer_consume_del_inventario():
    s = nueva()
    r = actions.perform(s, "eat", {"item": "chipa"})
    assert r.deltas["item"] == "chipa"
    assert s.player.meals_today == 1
    assert s.has_item("chipa", 1)
    assert round(s.player.nutrition, 1) == 87.5  # 75 + 14 - 1.5


def test_comer_sin_comida_falla():
    s = nueva()
    s.inventory = [
        stack
        for stack in s.inventory
        if stack.item_id not in ("chipa", "pan", "mandioca", "carne_seca")
    ]
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "eat", {})
    assert exc.value.code == "sin_comida"


def test_tres_comidas_por_jornada():
    s = nueva()
    for _ in range(3):
        actions.perform(s, "eat", {})  # elige la mejor comida disponible
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "eat", {})
    assert exc.value.code == "sin_apetito"


def test_beber_consume_agua_y_respeta_la_sed():
    s = nueva()
    actions.perform(s, "drink", {})
    assert s.player.drinks_today == 1
    assert s.has_item("agua", 1)
    assert round(s.player.hydration, 1) == 95.5
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "drink", {})
    assert exc.value.code == "sin_sed"


def test_beber_sin_agua_sugiere_el_pozo():
    s = nueva()
    s.inventory = [stack for stack in s.inventory if stack.item_id != "agua"]
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "drink", {})
    assert exc.value.code == "sin_agua"


def test_cierre_de_jornada_sin_dormir_castiga():
    s = nueva()
    actions.perform(s, "wait", {"hours": 12})  # 05:00 → 17:00
    actions.perform(s, "wait", {"hours": 7})  # 17:00 → 00:00
    assert s.closed_days == 0
    actions.perform(s, "wait", {"hours": 5})  # 00:00 → 05:00
    assert s.closed_days == 1
    assert s.pa == 1
    assert s.player.health < 90
    assert s.player.fatigue > 60
    assert s.player.sleep_debt_days == 1

    cierres = [e for e in s.log if e.get("kind") == "day_close"]
    assert cierres and cierres[-1]["penalized"] is True


def test_snapshot_ida_y_vuelta():
    s = nueva(seed=7)
    actions.perform(s, "sleep", {"hours": 4})
    actions.perform(s, "eat", {"item": "mandioca"})
    actions.perform(s, "activity", {"activity": "caminar"})

    copia = GameState.from_snapshot(s.snapshot())
    assert copia.snapshot() == s.snapshot()
    assert copia.moment() == s.moment()


def test_una_escena_pendiente_bloquea_el_dia():
    s = nueva()
    s.pending.append(
        {
            "uid": "x:0",
            "id": "aviso_movilizacion",
            "title": "Aviso",
            "text": "",
            "choices": [],
        }
    )
    with pytest.raises(EngineError) as exc:
        actions.perform(s, "sleep", {"hours": 3})
    assert exc.value.code == "escena_pendiente"
