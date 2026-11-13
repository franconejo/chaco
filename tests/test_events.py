from engine import actions, events
from engine.state import GameState


def nueva(seed: int = 0) -> GameState:
    return GameState.new(seed=seed)


def test_desmayo_por_deshidratacion():
    s = nueva()
    s.player.hydration = 10
    disparados = s.queue_events()
    assert [evento["id"] for evento in disparados] == ["desmayo_por_sed"]
    assert s.player.health < 100
    assert s.pending == []  # sin opciones se resuelve solo


def test_aviso_de_movilizacion_abre_una_escena():
    s = nueva()
    s.clock_min = 4 * 1440  # día 4, 05:00
    s.location = "almacen"

    disparados = s.queue_events()
    assert disparados[0]["id"] == "aviso_movilizacion"
    assert len(s.pending) == 1
    assert len(s.pending[0]["choices"]) == 3

    with_exc = None
    try:
        actions.perform(s, "sleep", {"hours": 3})
    except Exception as exc:  # noqa: BLE001
        with_exc = exc
    assert with_exc is not None and with_exc.code == "escena_pendiente"


def test_decision_y_cadena_de_dependencias():
    s = nueva()
    s.clock_min = 4 * 1440
    s.location = "almacen"
    s.queue_events()
    uid = s.pending[0]["uid"]

    actions.resolve_event(s, uid, "mostrar_acta")
    assert s.identity["suspicion"] == 2
    assert s.identity["credibility"] == 97
    assert "mostro_acta" in s.flags

    # Resolver el aviso habilita la escena de Juana en el mismo lugar y horario.
    assert len(s.pending) == 1
    assert s.pending[0]["id"] == "juana_secreto"

    uid_juana = s.pending[0]["uid"]
    actions.resolve_event(s, uid_juana, "contarle_todo")
    assert "juana_aliada" in s.flags
    assert s.npcs["juana"].trust > 30


def test_evento_once_no_se_repite():
    s = nueva()
    s.clock_min = 4 * 1440
    s.location = "almacen"
    s.queue_events()
    actions.resolve_event(s, s.pending[0]["uid"], "dejar_hablar_a_ramon")
    actions.resolve_event(s, s.pending[0]["uid"], "cambiar_de_tema")

    s.clock_min = 5 * 1440
    s.location = "almacen"
    ids = [evento["id"] for evento in s.queue_events()]
    assert "aviso_movilizacion" not in ids


def test_cooldown_evita_repeticion_inmediata():
    s = nueva()
    s.player.nutrition = 5
    s.queue_events()
    assert "hambre_extrema" in s.fired
    s.take_fired()

    s.player.nutrition = 5
    assert s.queue_events() == []


def test_el_azar_es_determinista():
    def correr(seed: int) -> list[list[str]]:
        resultados = []
        for hora in range(12, 19):
            s = nueva(seed=seed)
            s.clock_min = hora * 60 - 300
            s.location = "plaza"
            resultados.append([evento["id"] for evento in s.queue_events()])
        return resultados

    assert correr(7) == correr(7)
    assert events.MAX_FIRES_PER_TICK == 1


def test_evento_inexistente():
    s = nueva()
    try:
        actions.resolve_event(s, "no:existe", "x")
        raise AssertionError("debió fallar")
    except Exception as exc:  # noqa: BLE001
        assert exc.code == "evento_inexistente"
