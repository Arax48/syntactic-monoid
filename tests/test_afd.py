"""Pruebas para dfa.py."""

from __future__ import annotations

import pytest

from backend.models import AFD, AFDValidationError


# ----------------------------------------------------------------------
# Validacion
# ----------------------------------------------------------------------

def test_validacion_rechaza_estados_vacios() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states=set(), alphabet={"0"}, transitions={}, start="q",
            accepting=set())


def test_validacion_rechaza_alfabeto_vacio() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states={"q"}, alphabet=set(),
            transitions={"q": {}}, start="q", accepting=set())


def test_validacion_rechaza_inicio_fuera_de_Q() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states={"q"}, alphabet={"0"},
            transitions={"q": {"0": "q"}}, start="otro", accepting=set())


def test_validacion_rechaza_aceptacion_fuera_de_Q() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states={"q"}, alphabet={"0"},
            transitions={"q": {"0": "q"}}, start="q", accepting={"otro"})


def test_validacion_rechaza_transicion_incompleta() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states={"a", "b"}, alphabet={"0", "1"},
            transitions={"a": {"0": "a"}, "b": {"0": "a", "1": "b"}},
            start="a", accepting={"a"})


def test_validacion_rechaza_destino_fuera_de_Q() -> None:
    with pytest.raises(AFDValidationError):
        AFD(states={"a"}, alphabet={"0"},
            transitions={"a": {"0": "z"}},
            start="a", accepting={"a"})


# ----------------------------------------------------------------------
# delta y delta*
# ----------------------------------------------------------------------

def test_step_paridad(parity_afd: AFD) -> None:
    assert parity_afd.step("Par", "1") == "Impar"
    assert parity_afd.step("Impar", "1") == "Par"
    assert parity_afd.step("Par", "0") == "Par"


def test_delta_estrella_epsilon(parity_afd: AFD) -> None:
    for q in parity_afd.states:
        assert parity_afd.delta_star(q, "") == q


def test_delta_estrella_recursiva(parity_afd: AFD) -> None:
    # delta*(q, wa) = delta(delta*(q,w), a)
    w = "1011"
    a = "1"
    lhs = parity_afd.delta_star("Par", w + a)
    rhs = parity_afd.step(parity_afd.delta_star("Par", w), a)
    assert lhs == rhs


def test_run_y_accepts(parity_afd: AFD) -> None:
    assert parity_afd.run("") == "Par"
    assert parity_afd.accepts("")            # 0 unos: aceptada
    assert parity_afd.accepts("11")          # 2 unos
    assert not parity_afd.accepts("1")       # 1 uno
    assert parity_afd.accepts("1001001001001001")  # par de unos


def test_run_paso_invalido(parity_afd: AFD) -> None:
    with pytest.raises(ValueError):
        parity_afd.run("12")


# ----------------------------------------------------------------------
# Transformaciones inducidas
# ----------------------------------------------------------------------

def test_transformacion_identidad_en_epsilon(parity_afd: AFD) -> None:
    t = parity_afd.transformation("")
    assert t == {q: q for q in parity_afd.states}


def test_transformacion_0_es_identidad_en_paridad(parity_afd: AFD) -> None:
    # En el AFD de paridad, leer un 0 no cambia el estado.
    t = parity_afd.transformation("0")
    assert t == {"Par": "Par", "Impar": "Impar"}


def test_transformacion_1_invierte_paridad(parity_afd: AFD) -> None:
    t = parity_afd.transformation("1")
    assert t == {"Par": "Impar", "Impar": "Par"}


# ----------------------------------------------------------------------
# Serializacion
# ----------------------------------------------------------------------

def test_serializacion_roundtrip(parity_afd: AFD, tmp_path) -> None:
    import json

    path = tmp_path / "parity.json"
    path.write_text(json.dumps(parity_afd.to_dict()))
    loaded = AFD.from_json(path)
    assert loaded.states == parity_afd.states
    assert loaded.alphabet == parity_afd.alphabet
    assert loaded.start == parity_afd.start
    assert loaded.accepting == parity_afd.accepting
    assert loaded.transitions == parity_afd.transitions


def test_tabla_de_transiciones(parity_afd: AFD) -> None:
    rows = parity_afd.transition_table()
    assert rows[0] == ["delta", "0", "1"]
    assert len(rows) == 3  # cabecera + 2 estados
