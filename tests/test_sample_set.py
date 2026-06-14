"""Pruebas para backend.verification.sample_set."""

from __future__ import annotations

from backend.models import DFA
from backend.verification import (
    SampleSetResult,
    SampleVerdict,
    verify_samples,
)


# ----------------------------------------------------------------------
# Casos felices
# ----------------------------------------------------------------------

def test_muestra_vacia_no_pasa_y_no_falla() -> None:
    result = verify_samples(_dummy_dfa(), [], [])
    assert result.total == 0
    assert not result.all_pass
    assert "ninguna" in result.summary().lower()


def test_todas_las_palabras_correctas(parity_dfa: DFA) -> None:
    accept = ["", "11", "1001"]
    reject = ["1", "111"]
    result = verify_samples(parity_dfa, accept, reject)
    assert result.total == 5
    assert result.passed == 5
    assert result.failed == 0
    assert result.all_pass
    assert "✓" in result.summary("paridad")


# ----------------------------------------------------------------------
# Discrepancias
# ----------------------------------------------------------------------

def test_falso_negativo_detectado(parity_dfa: DFA) -> None:
    # "1001" tiene 2 unos (par), pero la marcamos como reject por error.
    result = verify_samples(parity_dfa, [], ["1001"])
    assert result.failed == 1
    verdict = result.mismatches[0]
    assert verdict.expected is False
    assert verdict.actual is True
    assert "rechazar" in result.summary("paridad")
    assert "acepto" in result.summary("paridad")


def test_falso_positivo_detectado(parity_dfa: DFA) -> None:
    # "1" tiene 1 uno (impar), pero la marcamos como accept por error.
    result = verify_samples(parity_dfa, ["1"], [])
    assert result.failed == 1
    verdict = result.mismatches[0]
    assert verdict.expected is True
    assert verdict.actual is False


def test_mezcla_de_aciertos_y_fallos(mod3_dfa: DFA) -> None:
    accept = ["", "111", "010101"]    # 0, 3, 3 unos: todas multiplos de 3 ✓
    reject = ["1", "11", "11111"]      # 1, 2, 5 unos ✓
    rotas = ["1111"]                   # 4 unos: NO es multiplo de 3 -> deberia rechazar
                                       #     marcamos como accept para forzar fallo.
    result = verify_samples(mod3_dfa, accept + rotas, reject)
    assert result.total == 7
    assert result.failed == 1
    assert result.mismatches[0].word == "1111"


# ----------------------------------------------------------------------
# Manejo de errores
# ----------------------------------------------------------------------

def test_simbolo_fuera_del_alfabeto_se_marca_como_error(parity_dfa: DFA) -> None:
    # 'x' no esta en {0, 1}, debe ser tratado como error y no como rechazo.
    result = verify_samples(parity_dfa, ["1x0"], [])
    assert result.failed == 1
    verdict = result.mismatches[0]
    assert verdict.error is not None
    assert "alfabeto" in verdict.error.lower() or "fuera" in verdict.error.lower()
    # Las demas palabras no deben verse afectadas:
    result_combo = verify_samples(parity_dfa, ["11", "1x0", ""], ["1"])
    assert result_combo.passed == 3
    assert result_combo.failed == 1


# ----------------------------------------------------------------------
# Tabla legible
# ----------------------------------------------------------------------

def test_pretty_table_incluye_cabecera_y_simbolos(parity_dfa: DFA) -> None:
    result = verify_samples(parity_dfa, ["", "11"], ["1"])
    table = result.pretty_table()
    assert "palabra" in table
    assert "esperado" in table
    assert "actual" in table
    # ε se representa con el simbolo griego en la celda
    assert "ε" in table
    # Marcadores de exito
    assert "✓" in table


# ----------------------------------------------------------------------
# Auxiliar
# ----------------------------------------------------------------------

def _dummy_dfa() -> DFA:
    """DFA de un solo estado, usado en pruebas que solo necesitan un
    objeto con .accepts(w) bien definido."""
    return DFA(
        states={"q"},
        alphabet={"a"},
        transitions={"q": {"a": "q"}},
        start="q",
        accepting={"q"},
        name="dummy",
    )
