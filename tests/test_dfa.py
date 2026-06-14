"""Pruebas para dfa.py."""

from __future__ import annotations

import pytest

from backend.models import DFA, DFAValidationError


# ----------------------------------------------------------------------
# Validacion
# ----------------------------------------------------------------------

def test_validacion_rechaza_estados_vacios() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states=set(), alphabet={"0"}, transitions={}, start="q",
            accepting=set())


def test_validacion_rechaza_alfabeto_vacio() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states={"q"}, alphabet=set(),
            transitions={"q": {}}, start="q", accepting=set())


def test_validacion_rechaza_inicio_fuera_de_Q() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states={"q"}, alphabet={"0"},
            transitions={"q": {"0": "q"}}, start="otro", accepting=set())


def test_validacion_rechaza_aceptacion_fuera_de_Q() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states={"q"}, alphabet={"0"},
            transitions={"q": {"0": "q"}}, start="q", accepting={"otro"})


def test_validacion_rechaza_transicion_incompleta() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states={"a", "b"}, alphabet={"0", "1"},
            transitions={"a": {"0": "a"}, "b": {"0": "a", "1": "b"}},
            start="a", accepting={"a"})


def test_validacion_rechaza_destino_fuera_de_Q() -> None:
    with pytest.raises(DFAValidationError):
        DFA(states={"a"}, alphabet={"0"},
            transitions={"a": {"0": "z"}},
            start="a", accepting={"a"})


# ----------------------------------------------------------------------
# delta y delta*
# ----------------------------------------------------------------------

def test_step_paridad(parity_dfa: DFA) -> None:
    assert parity_dfa.step("Par", "1") == "Impar"
    assert parity_dfa.step("Impar", "1") == "Par"
    assert parity_dfa.step("Par", "0") == "Par"


def test_delta_estrella_epsilon(parity_dfa: DFA) -> None:
    for q in parity_dfa.states:
        assert parity_dfa.delta_star(q, "") == q


def test_delta_estrella_recursiva(parity_dfa: DFA) -> None:
    # delta*(q, wa) = delta(delta*(q,w), a)
    w = "1011"
    a = "1"
    lhs = parity_dfa.delta_star("Par", w + a)
    rhs = parity_dfa.step(parity_dfa.delta_star("Par", w), a)
    assert lhs == rhs


def test_run_y_accepts(parity_dfa: DFA) -> None:
    assert parity_dfa.run("") == "Par"
    assert parity_dfa.accepts("")            # 0 unos: aceptada
    assert parity_dfa.accepts("11")          # 2 unos
    assert not parity_dfa.accepts("1")       # 1 uno
    assert parity_dfa.accepts("1001001001001001")  # par de unos


def test_run_paso_invalido(parity_dfa: DFA) -> None:
    with pytest.raises(ValueError):
        parity_dfa.run("12")


# ----------------------------------------------------------------------
# Transformaciones inducidas
# ----------------------------------------------------------------------

def test_transformacion_identidad_en_epsilon(parity_dfa: DFA) -> None:
    t = parity_dfa.transformation("")
    assert t == {q: q for q in parity_dfa.states}


def test_transformacion_0_es_identidad_en_paridad(parity_dfa: DFA) -> None:
    # En el DFA de paridad, leer un 0 no cambia el estado.
    t = parity_dfa.transformation("0")
    assert t == {"Par": "Par", "Impar": "Impar"}


def test_transformacion_1_invierte_paridad(parity_dfa: DFA) -> None:
    t = parity_dfa.transformation("1")
    assert t == {"Par": "Impar", "Impar": "Par"}


# ----------------------------------------------------------------------
# Serializacion
# ----------------------------------------------------------------------

def test_serializacion_roundtrip(parity_dfa: DFA, tmp_path) -> None:
    import json

    path = tmp_path / "parity.json"
    path.write_text(json.dumps(parity_dfa.to_dict()))
    loaded = DFA.from_json(path)
    assert loaded.states == parity_dfa.states
    assert loaded.alphabet == parity_dfa.alphabet
    assert loaded.start == parity_dfa.start
    assert loaded.accepting == parity_dfa.accepting
    assert loaded.transitions == parity_dfa.transitions


def test_tabla_de_transiciones(parity_dfa: DFA) -> None:
    rows = parity_dfa.transition_table()
    assert rows[0] == ["delta", "0", "1"]
    assert len(rows) == 3  # cabecera + 2 estados
