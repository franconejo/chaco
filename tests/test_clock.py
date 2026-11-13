from datetime import date

from engine.clock import (
    MANANA,
    NOCHE,
    TARDE,
    day_index,
    minute_of_day,
    minutes_until_day_close,
    moment,
    period_of,
)

INICIO = date(1932, 9, 1)


def test_arranque_son_las_cinco_de_la_manana():
    m = moment(0, INICIO)
    assert (m.hour, m.minute) == (5, 0)
    assert m.period == MANANA
    assert m.day_index == 0
    assert m.date == INICIO
    assert m.clock_min == 0


def test_periodos_del_dia():
    assert moment(0, INICIO).period == MANANA  # 05:00
    assert moment(420, INICIO).period == TARDE  # 12:00
    assert moment(840, INICIO).period == NOCHE  # 19:00
    assert moment(1140, INICIO).period == NOCHE  # 00:00
    assert moment(1439, INICIO).period == NOCHE  # 04:59


def test_medianoche_sigue_perteneciendo_a_la_jornada_anterior():
    m = moment(1140, INICIO)  # 19:00 + 5 h
    assert m.day_index == 0
    assert (m.hour, m.minute) == (0, 0)
    assert m.date == date(1932, 9, 2)


def test_cierre_de_jornada_a_las_cinco():
    m = moment(1440, INICIO)
    assert m.day_index == 1
    assert (m.hour, m.minute) == (5, 0)
    assert m.period == MANANA
    assert m.date == date(1932, 9, 2)


def test_limites_de_periodo():
    assert period_of(299) == NOCHE
    assert period_of(300) == MANANA
    assert period_of(719) == MANANA
    assert period_of(720) == TARDE
    assert period_of(1139) == TARDE
    assert period_of(1140) == NOCHE


def test_utilidades_del_reloj():
    assert day_index(0) == 0
    assert day_index(1439) == 0
    assert day_index(1440) == 1
    assert minute_of_day(0) == 300
    assert minutes_until_day_close(0) == 1440
    assert minutes_until_day_close(60) == 1380


def test_labels_para_la_interfaz():
    m = moment(420, INICIO)
    assert m.date_label == "01/09/1932"
    assert m.time_label == "12:00"
    assert m.period_label == "Tarde"
    assert m.weekday == INICIO.weekday()
