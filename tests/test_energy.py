from engine import energy


def test_tope_y_piso_de_pa():
    assert energy.clamp_pa(30) == 24
    assert energy.clamp_pa(-5) == 0
    assert energy.clamp_pa(12) == 12


def test_gasto_y_recuperacion_literal_del_gdd():
    assert energy.spend(24, 3) == 21
    # Dormir 3 PA habilita 6 PA, pero el tope sigue siendo 24.
    assert energy.recover(21, 2 * 3) == 24
    assert energy.recover(24, 3) == 24
    assert energy.recover(10, 2) == 12


def test_umbral_de_sed():
    assert energy.THIRST_THRESHOLD == 95.0
