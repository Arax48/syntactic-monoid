"""Pruebas para transformation.py."""

from __future__ import annotations

import pytest

from transformation import Transformation


def test_identity_es_identidad() -> None:
    states = {"a", "b", "c"}
    idQ = Transformation.identity(states)
    for q in states:
        assert idQ(q) == q


def test_apply_y_call_equivalentes() -> None:
    f = Transformation({"a": "b", "b": "a"})
    assert f.apply("a") == f("a") == "b"
    assert f.apply("b") == f("b") == "a"


def test_apply_fuera_de_dominio() -> None:
    f = Transformation({"a": "a"})
    with pytest.raises(KeyError):
        f.apply("b")


def test_then_corresponde_a_concatenacion() -> None:
    # f cuenta '1' (Par <-> Impar), g pasa todo a 'Par'
    f = Transformation({"Par": "Impar", "Impar": "Par"})
    g = Transformation({"Par": "Par", "Impar": "Par"})
    # primero f, luego g
    fg = f.then(g)
    assert fg("Par") == "Par"
    assert fg("Impar") == "Par"


def test_compose_es_orden_inverso_de_then() -> None:
    f = Transformation({0: 1, 1: 0})
    g = Transformation({0: 0, 1: 0})
    assert f.compose(g) == g.then(f)
    assert (f @ g) == g.then(f)


def test_then_y_compose_dominios_distintos() -> None:
    f = Transformation({0: 0})
    g = Transformation({1: 1})
    with pytest.raises(ValueError):
        f.then(g)


def test_asociatividad_de_la_composicion() -> None:
    f = Transformation({0: 1, 1: 2, 2: 0})
    g = Transformation({0: 0, 1: 2, 2: 1})
    h = Transformation({0: 2, 1: 1, 2: 2})
    assert (f.then(g)).then(h) == f.then(g.then(h))


def test_identidad_es_neutro_para_then() -> None:
    states = {0, 1, 2}
    f = Transformation({0: 2, 1: 0, 2: 1})
    e = Transformation.identity(states)
    assert e.then(f) == f
    assert f.then(e) == f


def test_igualdad_y_hash() -> None:
    f = Transformation({"a": "b", "b": "a"})
    g = Transformation({"b": "a", "a": "b"})
    h = Transformation({"a": "a", "b": "b"})
    assert f == g
    assert hash(f) == hash(g)
    assert f != h
    assert {f, g, h} == {f, h}


def test_two_line_notacion() -> None:
    f = Transformation({"a": "b", "b": "a"})
    s = f.two_line()
    assert "a" in s and "b" in s


def test_constructor_vacio_levanta() -> None:
    with pytest.raises(ValueError):
        Transformation({})
