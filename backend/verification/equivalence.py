"""
backend.verification.equivalence
================================

Verificacion de equivalencia entre automatas y especificaciones.

La pregunta "¿este automata reconoce el lenguaje que dije?" es
*decidible* para automatas finitos (regulares), y este modulo la
responde con un contraejemplo concreto y MAS CORTO cuando no:

    L(A) = L(B)  ⟺  L(A) △ L(B) = ∅

La construccion de producto + BFS de AFD.find_counterexample garantiza
que la palabra devuelta es la mas corta sobre la que ambos automatas
discrepan. Pedagogicamente esto es oro: el estudiante recibe la palabra
mas pequena que rompe su automata y el veredicto de cada uno sobre ella.

API publica
-----------
    EquivalenceResult       : resultado estructurado con palabra y veredictos.
    check_equivalence       : AFD vs AFD.
    check_against_regex     : AFD vs regex (compila la regex a AFD).
    check_against_nfa       : AFD vs AFN (convierte el AFN con subset construction).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from backend.models.afd import AFD
from backend.models.afn import AFN


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
        w = "λ (cadena vacia)" if self.counterexample == "" else repr(self.counterexample)
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

def check_equivalence(left: AFD, right: AFD) -> EquivalenceResult:
    """Compara dos AFDs y devuelve un EquivalenceResult.

    Cumple las precondiciones:
        * Ambos AFDs deben tener exactamente el mismo alfabeto.

    Devuelve el contraejemplo MAS CORTO (BFS sobre el producto) cuando
    no son equivalentes.
    """
    if left.alphabet != right.alphabet:
        raise ValueError(
            f"Los AFDs tienen alfabetos diferentes: "
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
    dfa: AFD,
    pattern: str,
    alphabet: Optional[Iterable[str]] = None,
) -> EquivalenceResult:
    """Compara un AFD contra el lenguaje denotado por una regex.

    El alfabeto del AFD-especificacion se toma del propio AFD cuando
    el parametro `alphabet` se omite, garantizando asi que ambos AFDs
    sean comparables.
    """
    # Importacion diferida para evitar ciclos al cargar el paquete.
    from backend.language.regex import regex_to_afd

    sigma = set(alphabet) if alphabet is not None else set(dfa.alphabet)
    spec = regex_to_afd(pattern, alphabet=sigma, name=f"L({pattern})")
    return check_equivalence(dfa, spec)


def check_against_nfa(dfa: AFD, afn: AFN) -> EquivalenceResult:
    """Compara un AFD contra un AFN, determinizando el AFN primero."""
    return check_equivalence(dfa, afn.to_afd())


__all__ = [
    "EquivalenceResult",
    "check_equivalence",
    "check_against_regex",
    "check_against_nfa",
]
