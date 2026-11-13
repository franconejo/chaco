from engine import needs
from engine.state import PlayerState


def test_tabla_de_sueno_del_gdd():
    assert needs.day_close_consequences(0, 0) == {
        "hours_slept": 0.0,
        "health_delta": -15.0,
        "fatigue_delta": 30.0,
        "sleep_debt_days": 1,
        "penalized": True,
    }

    dos_horas = needs.day_close_consequences(2, 0)
    assert dos_horas["health_delta"] == -5.0
    assert dos_horas["fatigue_delta"] == 10.0

    tres_horas = needs.day_close_consequences(3, 0)
    assert tres_horas["health_delta"] == 0.0
    assert tres_horas["fatigue_delta"] == 0.0
    assert tres_horas["penalized"] is False
    assert tres_horas["sleep_debt_days"] == 0

    assert needs.day_close_consequences(5, 0)["health_delta"] == 0.0


def test_deuda_de_sueno_se_acumula():
    primera = needs.day_close_consequences(1, 0)
    assert primera["sleep_debt_days"] == 1

    segunda = needs.day_close_consequences(0, 1)
    assert segunda["sleep_debt_days"] == 2
    assert segunda["health_delta"] < primera["health_delta"]
    assert segunda["fatigue_delta"] > primera["fatigue_delta"]


def test_multiplicador_de_descanso():
    assert needs.fatigue_recovery_multiplier(2) == 1.0
    assert needs.fatigue_recovery_multiplier(3) == 1.0
    assert needs.fatigue_recovery_multiplier(4) == 1.25
    assert needs.fatigue_recovery_multiplier(5) == 1.25
    assert needs.fatigue_recovery_multiplier(6) == 0.75


def test_deriva_de_salud_por_deshidratacion():
    p = PlayerState()
    p.hydration = 10.0
    assert needs.health_drift_per_hour(p) < 0

    p.hydration = 80.0
    p.health = 90.0
    assert needs.health_drift_per_hour(p) > 0  # recuperación lenta si está bien


def test_desgaste_al_despertar():
    p = PlayerState(hydration=80.0, nutrition=75.0, fatigue=10.0)
    needs.tick_awake(p, 120)
    assert p.hydration == 75.0
    assert round(p.fatigue, 2) == 12.4
