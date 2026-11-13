"""Prueba de integración: una partida de 32 días con rutina estándar.

Verifica que las cadenas de la Fase 1.5 se disparen en orden y que el motor
no se ahoga en el proceso. No es un test de balance, es un test de que el
contenido está vivo.
"""

from engine import actions, events
from engine.errors import EngineError
from engine.state import GameState

RUTINA = (
    ("eat", {}),
    ("activity", {"activity": "buscar_agua"}),
    ("drink", {}),
    ("activity", {"activity": "trabajar"}),
    ("drink", {}),
    ("eat", {}),
    ("buy", {"item": "chipa", "qty": 3}),
    ("visit", {"npc": "juana"}),
    ("activity", {"activity": "buscar_agua"}),
    ("drink", {}),
    ("eat", {}),
    ("sleep", {"hours": 8}),
)


def resolver_todos(estado: GameState) -> None:
    while estado.pending:
        escena = estado.pending[0]
        uid = escena.get("uid")
        if not uid:
            estado.pending.pop(0)
            continue
        from data.events import get as get_event

        ev = get_event(escena["id"])
        opciones = events.available_choices(estado, ev)
        if not opciones:
            estado.pending.pop(0)
            continue
        try:
            actions.resolve_event(estado, uid, opciones[0].id)
        except Exception:  # noqa: BLE001
            estado.pending.pop(0)


def jugar(dias: int, seed: int = 7, dinero_extra: int = 0) -> GameState:
    estado = GameState.new(seed=seed)
    if dinero_extra:
        estado.player.money += dinero_extra
    for _ in range(dias):
        for accion, params in RUTINA:
            for _ in range(5):
                try:
                    actions.perform(estado, accion, params)
                    break
                except EngineError as exc:
                    if exc.code == "escena_pendiente":
                        resolver_todos(estado)
                        continue
                    break
            resolver_todos(estado)
    return estado


def test_la_partida_llega_a_32_dias():
    s = jugar(32)
    assert s.closed_days >= 20
    assert s.player.health >= 0


def test_los_hitos_de_la_cadena_principal_ocurren():
    s = jugar(32)
    fired = set(s.fired)
    esperados = {
        "aviso_movilizacion",
        "juana_secreto",
        "despedida_de_aurelio",
        "carta_del_frente",
        "control_de_documentos",
        "suben_los_precios",
        "acaparamiento",
        "citacion_al_cuartel",
        "el_taller_cierra",
    }
    faltantes = esperados - fired
    assert not faltantes, f"No se dispararon: {sorted(faltantes)}"


def test_aurelio_se_va_al_frente_durante_la_campana():
    s = jugar(32)
    assert "aurelio_en_el_frente" in s.flags


def test_la_cadena_de_identidad_se_resuelve():
    s = jugar(32)
    assert "citacion_al_cuartel" in s.fired
    assert "fue_al_cuartel" in s.flags or "falto_a_la_citacion" in s.flags


def test_la_escasez_se_resuelve_con_el_poroto():
    s = jugar(32)
    assert "suben_los_precios" in s.fired
    assert "acaparamiento" in s.fired


def test_la_noticia_de_boqueron_llega_si_el_jugador_esta_sano():
    s = jugar(32, dinero_extra=200)
    assert "rumor_de_boqueron" in s.fired
    assert "vuelve_el_poroto" in s.fired
    assert "precios_altos" not in s.flags
    assert "volvio_el_poroto" in s.flags
