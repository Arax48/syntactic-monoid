"""Pruebas para backend.models.afn.

Cubre lo que NO esta ejercitado por los tests de la construccion de
Thompson (test_regex.py): manipulacion directa de la API del AFN,
manejo de λ-transiciones, simulacion no determinista y construccion
de subconjuntos sobre un AFN escrito a mano.
"""

from __future__ import annotations

import pytest

from backend.models import AFN, AFNValidationError


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def nfa_termina_en_01() -> AFN:
    """AFN clasico de tres estados que acepta cadenas terminadas en 01.

    Disenado a mano (sin λ-transiciones) para servir como referencia.
    """
    return AFN(
        states={"q0", "q1", "q2"},
        alphabet={"0", "1"},
        transitions={
            "q0": {"0": {"q0", "q1"}, "1": {"q0"}},
            "q1": {"0": set(), "1": {"q2"}},
            "q2": {"0": set(), "1": set()},
        },
        lambda_transitions={},
        start="q0",
        accepting={"q2"},
        name="termina_en_01",
    )


@pytest.fixture
def nfa_epsilon_choice() -> AFN:
    """AFN con λ-transiciones que reconoce a* | b*.

    Estructura:
        s0 --λ--> a-loop
        s0 --λ--> b-loop
    """
    return AFN(
        states={"s0", "qa", "qb"},
        alphabet={"a", "b"},
        transitions={
            "qa": {"a": {"qa"}, "b": set()},
            "qb": {"a": set(), "b": {"qb"}},
        },
        lambda_transitions={"s0": {"qa", "qb"}},
        start="s0",
        accepting={"qa", "qb"},
        name="a*_o_b*",
    )


# ----------------------------------------------------------------------
# Validacion estructural
# ----------------------------------------------------------------------

def test_validacion_rechaza_estados_vacios() -> None:
    with pytest.raises(AFNValidationError):
        AFN(
            states=set(),
            alphabet={"a"},
            transitions={},
            lambda_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_alfabeto_vacio() -> None:
    with pytest.raises(AFNValidationError):
        AFN(
            states={"q"},
            alphabet=set(),
            transitions={},
            lambda_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_destino_fuera_de_Q() -> None:
    with pytest.raises(AFNValidationError):
        AFN(
            states={"q"},
            alphabet={"a"},
            transitions={"q": {"a": {"otro"}}},
            lambda_transitions={},
            start="q",
            accepting=set(),
        )


def test_validacion_rechaza_lambda_a_estado_fuera_de_Q() -> None:
    with pytest.raises(AFNValidationError):
        AFN(
            states={"q"},
            alphabet={"a"},
            transitions={"q": {"a": set()}},
            lambda_transitions={"q": {"otro"}},
            start="q",
            accepting=set(),
        )


# ----------------------------------------------------------------------
# Cerradura λ
# ----------------------------------------------------------------------

def test_lambda_closure_incluye_al_propio_estado(nfa_epsilon_choice: AFN) -> None:
    assert "s0" in nfa_epsilon_choice.lambda_closure({"s0"})


def test_lambda_closure_recorre_transitivamente(nfa_epsilon_choice: AFN) -> None:
    closure = nfa_epsilon_choice.lambda_closure({"s0"})
    assert closure == frozenset({"s0", "qa", "qb"})


def test_lambda_closure_sin_lambda_transiciones(nfa_termina_en_01: AFN) -> None:
    # En un AFN sin λ-transiciones, la cerradura es el propio conjunto.
    closure = nfa_termina_en_01.lambda_closure({"q0"})
    assert closure == frozenset({"q0"})


# ----------------------------------------------------------------------
# move / extended_move
# ----------------------------------------------------------------------

def test_move_devuelve_destinos_directos(nfa_termina_en_01: AFN) -> None:
    assert nfa_termina_en_01.move({"q0"}, "0") == frozenset({"q0", "q1"})
    assert nfa_termina_en_01.move({"q1"}, "1") == frozenset({"q2"})


def test_extended_move_aplica_cerradura(nfa_epsilon_choice: AFN) -> None:
    # Desde s0, leer 'a' debe llevar a {qa} (via λ y luego a-loop).
    result = nfa_epsilon_choice.extended_move({"s0"}, "a")
    assert result == frozenset({"qa"})


# ----------------------------------------------------------------------
# Simulacion no determinista
# ----------------------------------------------------------------------

def test_accepts_termina_en_01(nfa_termina_en_01: AFN) -> None:
    aceptados = ["01", "001", "1101", "1010101"]
    rechazados = ["", "0", "1", "10", "11", "010"]
    for w in aceptados:
        assert nfa_termina_en_01.accepts(w), f"deberia aceptar {w!r}"
    for w in rechazados:
        assert not nfa_termina_en_01.accepts(w), f"deberia rechazar {w!r}"


def test_accepts_alterna_a_o_b(nfa_epsilon_choice: AFN) -> None:
    aceptados = ["", "a", "aaaa", "b", "bbbb"]
    rechazados = ["ab", "ba", "aab", "bba"]
    for w in aceptados:
        assert nfa_epsilon_choice.accepts(w), f"deberia aceptar {w!r}"
    for w in rechazados:
        assert not nfa_epsilon_choice.accepts(w), f"deberia rechazar {w!r}"


def test_accepts_simbolo_fuera_del_alfabeto_falla(nfa_termina_en_01: AFN) -> None:
    with pytest.raises(ValueError):
        nfa_termina_en_01.accepts("a01")


# ----------------------------------------------------------------------
# Construccion de subconjuntos
# ----------------------------------------------------------------------

def test_to_afd_reconoce_el_mismo_lenguaje(nfa_termina_en_01: AFN) -> None:
    dfa = nfa_termina_en_01.to_afd()
    palabras = ["", "0", "1", "01", "001", "1101", "10", "11"]
    for w in palabras:
        assert dfa.accepts(w) == nfa_termina_en_01.accepts(w), w


def test_to_afd_de_nfa_con_epsilon(nfa_epsilon_choice: AFN) -> None:
    dfa = nfa_epsilon_choice.to_afd()
    palabras = ["", "a", "b", "aa", "bb", "ab", "ba", "aaaaa"]
    for w in palabras:
        assert dfa.accepts(w) == nfa_epsilon_choice.accepts(w), w


def test_to_afd_genera_afd_total_y_valido(nfa_termina_en_01: AFN) -> None:
    """to_afd() debe devolver un AFD estructuralmente valido (transicion
    total). Implicitamente esto verifica que el sumidero por subconjunto
    vacio se conecta correctamente cuando es alcanzable."""
    dfa = nfa_termina_en_01.to_afd()
    for q in dfa.states:
        for a in dfa.alphabet:
            assert a in dfa.transitions[q]
            assert dfa.transitions[q][a] in dfa.states


# ----------------------------------------------------------------------
# Serializacion JSON
# ----------------------------------------------------------------------

def test_to_dict_y_from_dict_son_inversos(nfa_termina_en_01: AFN) -> None:
    data = nfa_termina_en_01.to_dict()
    recuperado = AFN.from_dict(data)
    palabras = ["", "0", "01", "001", "1101", "1", "10"]
    for w in palabras:
        assert recuperado.accepts(w) == nfa_termina_en_01.accepts(w), w


def test_to_dict_preserva_lambda(nfa_epsilon_choice: AFN) -> None:
    data = nfa_epsilon_choice.to_dict()
    assert "s0" in data["lambda_transitions"]
    assert set(data["lambda_transitions"]["s0"]) == {"qa", "qb"}
