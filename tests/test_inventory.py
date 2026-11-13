from engine import inventory as inv


def inventario():
    pilas: list[inv.Stack] = []
    return pilas


def test_apilar_y_contar():
    pilas = inventario()
    inv.add(pilas, "chipa", 2, 0)
    inv.add(pilas, "chipa", 1, 0)
    assert inv.count(pilas, "chipa") == 3
    assert len(pilas) == 1


def test_vencimientos_distintos_no_se_fusionan():
    pilas = inventario()
    inv.add(pilas, "chipa", 1, 0)  # vence el día 2
    inv.add(pilas, "chipa", 1, 1)  # vence el día 3
    assert len(pilas) == 2
    assert inv.count(pilas, "chipa") == 2


def test_lo_vencido_no_se_puede_usar_ni_se_cuenta():
    pilas = inventario()
    inv.add(pilas, "chipa", 1, 0)
    assert inv.available_count(pilas, "chipa", 2) == 1
    assert inv.available_count(pilas, "chipa", 3) == 0


def test_purga_al_cerrar_jornada():
    pilas = inventario()
    inv.add(pilas, "chipa", 2, 0)
    inv.add(pilas, "mandioca", 1, 0)
    assert inv.purge(pilas, 2) == []
    vencidos = inv.purge(pilas, 3)
    assert vencidos[0]["item_id"] == "chipa"
    assert inv.count(pilas, "chipa") == 0
    assert inv.count(pilas, "mandioca") == 1


def test_retirar_consume_primero_lo_que_vence_antes():
    pilas = inventario()
    inv.add(pilas, "chipa", 1, 0)  # vence día 2
    inv.add(pilas, "chipa", 1, 5)  # vence día 7
    assert inv.remove(pilas, "chipa", 1) == 1
    restantes = [p for p in pilas if p.item_id == "chipa"]
    assert restantes[0].expires_day == 7


def test_mejor_comida_por_nutricion():
    pilas = inventario()
    inv.add(pilas, "chipa", 1, 0)
    inv.add(pilas, "carne_seca", 1, 0)
    assert inv.best_food(pilas, 0) == "carne_seca"
    assert inv.best_food(pilas, 10) is None  # todo vencido


def test_peso_total():
    pilas = inventario()
    inv.add(pilas, "agua", 2, 0)
    assert inv.total_weight(pilas) == 2.0
