"""Pruebas para backend.models.nfa.

Cubre lo que NO esta ejercitado por los tests de la construccion de
Thompson (test_regex.py): manipulacion directa de la API del NFA,
manejo de ε-transiciones, simulacion no determinista y construccion
de subconjuntos sobre un NFA escrito a mano.
"""

from __future__ import annotations

import pytest

from backend.models import NFA, NFAValidationError


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def nfa_termina_en_01() -> NFA:
    """NFA clasico de tres estados que acepta cadenas terminadas en 01.

    Disenado a mano (sin ε-transiciones) para servir como referencia.
    """
    return NFA(
        states={"q0", "q1", "q2"},
        alphabet={"0", "1"},
        transitions={
            "q0": {"0": {"q0", "q1"}, "1": {"q0"}},
            "q1": {"0": set(), "1": {"q2"}},
            "q2": {"0": set(), "1": set()},
        },
        epsilon_transitions={},
        start="q0",
        accepting={"q2"},
        name="termina_en_01",
    )


@pytest.fixture
def nfa_epsilon_choice() -> NFA:
    """NFA con ε-transiciones que reconoce a* | b*.

    Estructura:
        s0 --ε--> a-loop
        s0 --ε--> b-loop
    """
    return NFA(
        states={"s0", "qa", "qb"},
        alphabet={"a", "b"},
        transitions={
            "qa": {"a": {"qa"}, "b": set()},
            "qb": {"a": set(), "b": {"qb"}},
        },
        epsilon_transitions={"s0": {"qa", "qb"}},
        start="s0",
        accepting={"qa", "qb"},
        name="a*_o_b*",
    )


# ----------------------------------------------------------------------
# Validacion estructural
# ----------------------------------------------------------------------

def test_validacion_rechaza_estados_vacios() -> None:
    with pytest.raises(NFAValidationError):
        NFA(
            states=set(),
            alphabet={"a"},
            transitions={},
            epsilon_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_alfabeto_vacio() -> None:
    with pytest.raises(NFAValidationError):
        NFA(
            states={"q"},
            alphabet=set(),
            transitions={},
            epsilon_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_destino_fuera_de_Q() -> None:
    with pytest.raises(NFAValidationError):
        NFA(
            states={"q"},
            alphabet={"a"},
            transitions={"q": {"a": {"otro"}}},
            epsilon_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_epsilon_a_estado_fuera_de_Q() -> None:
    with pytest.raises(NFAValidationError):
        NFA(
            states={"q"},
            alphabet={"a"},
            transitions={"q": {"a": set()}},
            epsilon_transitions={"q": {"otro"}},
            start="q",
            accepting=set(),
        )


# ----------------------------------------------------------------------
# Cerradura epsilon
# ----------------------------------------------------------------------

def test_epsilon_closure_incluye_al_propio_estado(nfa_epsilon_choice: NFA) -> None:
    assert "s0" in nfa_epsilon_choice.epsilon_closure({"s0"})


def test_epsilon_closure_recorre_transitivamente(nfa_epsilon_choice: NFA) -> None:
    closure = nfa_epsilon_choice.epsilon_closure({"s0"})
    assert closure == frozenset({"s0", "qa", "qb"})


def test_epsilon_closure_sin_epsilon_transiciones(nfa_termina_en_01: NFA) -> None:
    # En un NFA sin ε-transiciones, la cerradura es el propio conjunto.
    closure = nfa_termina_en_01.epsilon_closure({"q0"})
    assert closure == frozenset({"q0"})


# ----------------------------------------------------------------------
# move / extended_move
# ----------------------------------------------------------------------

def test_move_devuelve_destinos_directos(nfa_termina_en_01: NFA) -> None:
    assert nfa_termina_en_01.move({"q0"}, "0") == frozenset({"q0", "q1"})
    assert nfa_termina_en_01.move({"q1"}, "1") == frozenset({"q2"})


def test_extended_move_aplica_cerradura(nfa_epsilon_choice: NFA) -> None:
    # Desde s0, leer 'a' debe llevar a {qa} (via ε y luego a-loop).
    result = nfa_epsilon_choice.extended_move({"s0"}, "a")
    assert result == frozenset({"qa"})


# ----------------------------------------------------------------------
# Simulacion no determinista
# ----------------------------------------------------------------------

def test_accepts_termina_en_01(nfa_termina_en_01: NFA) -> None:
    aceptados = ["01", "001", "1101", "1010101"]
    rechazados = ["", "0", "1", "10", "11", "010"]
    for w in aceptados:
        assert nfa_termina_en_01.accepts(w), f"deberia aceptar {w!r}"
    for w in rechazados:
        assert not nfa_termina_en_01.accepts(w), f"deberia rechazar {w!r}"


def test_accepts_alterna_a_o_b(nfa_epsilon_choice: NFA) -> None:
    aceptados = ["", "a", "aaaa", "b", "bbbb"]
    rechazados = ["ab", "ba", "aab", "bba"]
    for w in aceptados:
        assert nfa_epsilon_choice.accepts(w), f"deberia aceptar {w!r}"
    for w in rechazados:
        assert not nfa_epsilon_choice.accepts(w), f"deberia rechazar {w!r}"


def test_accepts_simbolo_fuera_del_alfabeto_falla(nfa_termina_en_01: NFA) -> None:
    with pytest.raises(ValueError):
        nfa_termina_en_01.accepts("a01")


# ----------------------------------------------------------------------
# Construccion de subconjuntos
# ----------------------------------------------------------------------

def test_to_dfa_reconoce_el_mismo_lenguaje(nfa_termina_en_01: NFA) -> None:
    dfa = nfa_termina_en_01.to_dfa()
    palabras = ["", "0", "1", "01", "001", "1101", "10", "11"]
    for w in palabras:
        assert dfa.accepts(w) == nfa_termina_en_01.accepts(w), w


def test_to_dfa_de_nfa_con_epsilon(nfa_epsilon_choice: NFA) -> None:
    dfa = nfa_epsilon_choice.to_dfa()
    palabras = ["", "a", "b", "aa", "bb", "ab", "ba", "aaaaa"]
    for w in palabras:
        assert dfa.accepts(w) == nfa_epsilon_choice.accepts(w), w


def test_to_dfa_genera_dfa_total_y_valido(nfa_termina_en_01: NFA) -> None:
    """to_dfa() debe devolver un DFA estructuralmente valido (transicion
    total). Implicitamente esto verifica que el sumidero por subconjunto
    vacio se conecta correctamente cuando es alcanzable."""
    dfa = nfa_termina_en_01.to_dfa()
    for q in dfa.states:
        for a in dfa.alphabet:
            assert a in dfa.transitions[q]
            assert dfa.transitions[q][a] in dfa.states


# ----------------------------------------------------------------------
# Serializacion JSON
# ----------------------------------------------------------------------

def test_to_dict_y_from_dict_son_inversos(nfa_termina_en_01: NFA) -> None:
    data = nfa_termina_en_01.to_dict()
    recuperado = NFA.from_dict(data)
    palabras = ["", "0", "01", "001", "1101", "1", "10"]
    for w in palabras:
        assert recuperado.accepts(w) == nfa_termina_en_01.accepts(w), w


def test_to_dict_preserva_epsilon(nfa_epsilon_choice: NFA) -> None:
    data = nfa_epsilon_choice.to_dict()
    assert "s0" in data["epsilon_transitions"]
    assert set(data["epsilon_transitions"]["s0"]) == {"qa", "qb"}
