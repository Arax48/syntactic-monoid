"""
backend.verification.equivalence
================================

Verificacion de equivalencia entre automatas y especificaciones.

La pregunta "¿este automata reconoce el lenguaje que dije?" es
*decidible* para automatas finitos (regulares), y este modulo la
responde con un contraejemplo concreto y MAS CORTO cuando no:

    L(A) = L(B)  ⟺  L(A) △ L(B) = ∅

La construccion de producto + BFS de DFA.find_counterexample garantiza
que la palabra devuelta es la mas corta sobre la que ambos automatas
discrepan. Pedagogicamente esto es oro: el estudiante recibe la palabra
mas pequena que rompe su automata y el veredicto de cada uno sobre ella.

API publica
-----------
    EquivalenceResult       : resultado estructurado con palabra y veredictos.
    check_equivalence       : DFA vs DFA.
    check_against_regex     : DFA vs regex (compila la regex a DFA).
    check_against_nfa       : DFA vs NFA (convierte el NFA con subset construction).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from backend.models.dfa import DFA
from backend.models.nfa import NFA


@dataclass(frozen=True)
class EquivalenceResult:
    """Resultado de comparar dos automatas (o un automata y una regex).

    Atributos
    ---------
    equivalent : bool
        True si y solo si L(left) = L(right).
    counterexample : str | None
        Si equivalent es False, la palabra MAS CORTA sobre la que los
        dos automatas discrepan (puede ser la palabra vacia). None si
        son equivalentes.
    accepted_by_left, accepted_by_right : bool | None
        Veredictos individuales sobre `counterexample`. None si son
        equivalentes (no hay contraejemplo que evaluar).
    """

    equivalent: bool
    counterexample: Optional[str] = None
    accepted_by_left: Optional[bool] = None
    accepted_by_right: Optional[bool] = None

    def summary(
        self,
        left_name: str = "automata izquierdo",
        right_name: str = "automata derecho",
    ) -> str:
        """Mensaje legible en castellano, listo para mostrar al estudiante."""
        if self.equivalent:
            return f"✓ {left_name} y {right_name} reconocen el mismo lenguaje."
        w = "ε (cadena vacia)" if self.counterexample == "" else repr(self.counterexample)
        if self.accepted_by_left and not self.accepted_by_right:
            who_si, who_no = left_name, right_name
        else:
            who_si, who_no = right_name, left_name
        return (
            f"✗ Los automatas NO son equivalentes.\n"
            f"  Contraejemplo mas corto: {w}.\n"
            f"  El {who_si} la acepta; el {who_no} la rechaza."
        )

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.summary()


# ----------------------------------------------------------------------
# Verificadores
# ----------------------------------------------------------------------

def check_equivalence(left: DFA, right: DFA) -> EquivalenceResult:
    """Compara dos DFAs y devuelve un EquivalenceResult.

    Cumple las precondiciones:
        * Ambos DFAs deben tener exactamente el mismo alfabeto.

    Devuelve el contraejemplo MAS CORTO (BFS sobre el producto) cuando
    no son equivalentes.
    """
    if left.alphabet != right.alphabet:
        raise ValueError(
            f"Los DFAs tienen alfabetos diferentes: "
            f"{sorted(left.alphabet)!r} vs {sorted(right.alphabet)!r}."
        )
    counter = left.find_counterexample(right)
    if counter is None:
        return EquivalenceResult(equivalent=True)
    return EquivalenceResult(
        equivalent=False,
        counterexample=counter,
        accepted_by_left=left.accepts(counter),
        accepted_by_right=right.accepts(counter),
    )


def check_against_regex(
    dfa: DFA,
    pattern: str,
    alphabet: Optional[Iterable[str]] = None,
) -> EquivalenceResult:
    """Compara un DFA contra el lenguaje denotado por una regex.

    El alfabeto del DFA-especificacion se toma del propio DFA cuando
    el parametro `alphabet` se omite, garantizando asi que ambos DFAs
    sean comparables.
    """
    # Importacion diferida para evitar ciclos al cargar el paquete.
    from backend.language.regex import regex_to_dfa

    sigma = set(alphabet) if alphabet is not None else set(dfa.alphabet)
    spec = regex_to_dfa(pattern, alphabet=sigma, name=f"L({pattern})")
    return check_equivalence(dfa, spec)


def check_against_nfa(dfa: DFA, nfa: NFA) -> EquivalenceResult:
    """Compara un DFA contra un NFA, determinizando el NFA primero."""
    return check_equivalence(dfa, nfa.to_dfa())


__all__ = [
    "EquivalenceResult",
    "check_equivalence",
    "check_against_regex",
    "check_against_nfa",
]
