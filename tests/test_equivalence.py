"""Pruebas para backend.verification.equivalence."""

from __future__ import annotations

import pytest

from backend.models import AFD, AFN
from backend.verification import (
    EquivalenceResult,
    check_against_afn,
    check_against_regex,
    check_equivalence,
)


# ----------------------------------------------------------------------
# AFD vs AFD
# ----------------------------------------------------------------------

def test_equivalencia_es_reflexiva(parity_afd: AFD) -> None:
    result = check_equivalence(parity_afd, parity_afd)
    assert result.equivalent
    assert result.counterexample is None


def test_dfa_distintos_dan_contraejemplo(parity_afd: AFD, mod3_afd: AFD) -> None:
    result = check_equivalence(parity_afd, mod3_afd)
    assert not result.equivalent
    assert result.counterexample is not None
    # El contraejemplo debe distinguir a los dos automatas.
    assert parity_afd.accepts(result.counterexample) != mod3_afd.accepts(
        result.counterexample
    )


def test_contraejemplo_es_el_mas_corto_posible(mod3_afd: AFD) -> None:
    """Tomamos una variante del AFD mod 3 que rompe en una palabra
    concreta y verificamos que el contraejemplo es el MAS CORTO."""
    # Variante: hacemos que r1 sea aceptante (mod 3 == 1 en lugar de 0).
    roto = AFD(
        states=mod3_afd.states,
        alphabet=mod3_afd.alphabet,
        transitions={
            q: dict(row) for q, row in mod3_afd.transitions.items()
        },
        start=mod3_afd.start,
        accepting={"r1"},
        name="mod3_roto",
    )
    result = check_equivalence(mod3_afd, roto)
    assert not result.equivalent
    # El contraejemplo mas corto debe ser de longitud 0 ("λ") o 1 ("1").
    # Estos son los dos discrepan: λ es aceptada por mod3_afd y no por
    # roto (r0 aceptante vs r1 aceptante); "1" es aceptada por roto
    # (r1 aceptante) y no por mod3_afd.
    assert len(result.counterexample) <= 1


def test_alfabetos_distintos_levantan_error(parity_afd: AFD) -> None:
    otro = AFD(
        states={"x"},
        alphabet={"a"},
        transitions={"x": {"a": "x"}},
        start="x",
        accepting={"x"},
        name="otro_alfabeto",
    )
    with pytest.raises(ValueError):
        check_equivalence(parity_afd, otro)


def test_summary_es_legible_cuando_son_equivalentes(parity_afd: AFD) -> None:
    result = check_equivalence(parity_afd, parity_afd)
    s = result.summary("mio", "esperado")
    assert "✓" in s
    assert "mio" in s and "esperado" in s


def test_summary_distingue_quien_acepta_y_quien_rechaza(
    parity_afd: AFD, mod3_afd: AFD
) -> None:
    result = check_equivalence(parity_afd, mod3_afd)
    s = result.summary("paridad", "mod3")
    assert "✗" in s
    assert "Contraejemplo" in s
    assert "acepta" in s and "rechaza" in s


# ----------------------------------------------------------------------
# AFD vs regex
# ----------------------------------------------------------------------

def test_dfa_paridad_es_equivalente_a_su_regex(parity_afd: AFD) -> None:
    # (0*10*1)*0*  recognoce "numero par de 1s".
    result = check_against_regex(parity_afd, "(0*10*1)*0*")
    assert result.equivalent, result.summary()


def test_dfa_mod3_es_equivalente_a_su_regex(mod3_afd: AFD) -> None:
    result = check_against_regex(mod3_afd, "0*(10*10*10*)*")
    assert result.equivalent, result.summary()


def test_dfa_ends_with_01_es_equivalente_a_su_regex(ends_01_afd: AFD) -> None:
    result = check_against_regex(ends_01_afd, "(0|1)*01")
    assert result.equivalent, result.summary()


def test_dfa_paridad_no_coincide_con_regex_incorrecta(parity_afd: AFD) -> None:
    # Esta regex reconoce "termina en 0", no "numero par de 1s".
    result = check_against_regex(parity_afd, "(0|1)*0")
    assert not result.equivalent
    # El contraejemplo debe romper en uno u otro sentido.
    assert result.accepted_by_left != result.accepted_by_right


# ----------------------------------------------------------------------
# AFD vs AFN
# ----------------------------------------------------------------------

def test_check_against_nfa_equivalente(ends_01_afd: AFD) -> None:
    # AFN clasico para "termina en 01"
    afn = AFN(
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
        name="termina_en_01_nfa",
    )
    result = check_against_afn(ends_01_afd, afn)
    assert result.equivalent, result.summary()
