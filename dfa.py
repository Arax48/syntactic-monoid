"""
dfa.py
======

Modulo de Automata Finito Determinista (DFA).

Un DFA se define formalmente como una 5-tupla:

    A = (Q, Sigma, delta, q0, F)

donde:
    Q       : conjunto finito de estados.
    Sigma   : alfabeto finito.
    delta   : Q x Sigma -> Q, funcion de transicion.
    q0      : estado inicial, q0 in Q.
    F       : conjunto de estados de aceptacion, F subset Q.

La funcion de transicion extendida delta* : Q x Sigma* -> Q se define
recursivamente como:

    delta*(q, epsilon) = q
    delta*(q, wa)      = delta(delta*(q, w), a)

para todo q in Q, w in Sigma* y a in Sigma.

El lenguaje aceptado por A es:

    L(A) = { w in Sigma* : delta*(q0, w) in F }.

Este modulo implementa la clase DFA con validacion estructural,
ejecucion de cadenas, calculo de delta* y obtencion de las
transformaciones inducidas por palabras, las cuales son la base
del monoide de transicion construido en transition_monoid.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


class DFAValidationError(ValueError):
    """Se lanza cuando la definicion de un DFA no es estructuralmente valida."""


@dataclass
class DFA:
    """Automata Finito Determinista.

    Atributos
    ---------
    states : set[str]
        Conjunto finito de estados Q.
    alphabet : set[str]
        Alfabeto finito Sigma.
    transitions : dict[str, dict[str, str]]
        Funcion de transicion delta representada como un diccionario
        anidado: transitions[q][a] = delta(q, a).
    start : str
        Estado inicial q0.
    accepting : set[str]
        Conjunto de estados de aceptacion F.
    name : str
        Nombre legible del DFA (opcional, util para reportes).
    """

    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[str, Dict[str, str]]
    start: str
    accepting: Set[str]
    name: str = field(default="DFA")

    def __post_init__(self) -> None:
        self.states = set(self.states)
        self.alphabet = set(self.alphabet)
        self.accepting = set(self.accepting)
        self.validate()

    # ------------------------------------------------------------------
    # Validacion estructural
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Verifica que el DFA es estructuralmente correcto.

        En particular:
            * Q no es vacio.
            * Sigma no es vacio.
            * q0 in Q.
            * F subset Q.
            * delta esta totalmente definida: para todo q in Q y a in Sigma
              existe un valor delta(q, a) in Q.
        """
        if not self.states:
            raise DFAValidationError("Q (estados) no puede ser vacio.")
        if not self.alphabet:
            raise DFAValidationError("Sigma (alfabeto) no puede ser vacio.")
        if self.start not in self.states:
            raise DFAValidationError(
                f"El estado inicial {self.start!r} no pertenece a Q."
            )
        if not self.accepting.issubset(self.states):
            extra = self.accepting - self.states
            raise DFAValidationError(
                f"Estados de aceptacion fuera de Q: {sorted(extra)!r}."
            )
        for q in self.states:
            if q not in self.transitions:
                raise DFAValidationError(
                    f"delta no esta definida para el estado {q!r}."
                )
            row = self.transitions[q]
            for a in self.alphabet:
                if a not in row:
                    raise DFAValidationError(
                        f"delta({q!r}, {a!r}) no esta definida."
                    )
                if row[a] not in self.states:
                    raise DFAValidationError(
                        f"delta({q!r}, {a!r}) = {row[a]!r} no pertenece a Q."
                    )

    # ------------------------------------------------------------------
    # Funcion de transicion
    # ------------------------------------------------------------------

    def step(self, state: str, symbol: str) -> str:
        """Aplica delta(state, symbol)."""
        if state not in self.states:
            raise ValueError(f"Estado desconocido: {state!r}")
        if symbol not in self.alphabet:
            raise ValueError(f"Simbolo fuera del alfabeto: {symbol!r}")
        return self.transitions[state][symbol]

    def delta_star(self, state: str, word: str) -> str:
        """Aplica la funcion de transicion extendida delta*(state, word).

        Sigue la definicion recursiva:
            delta*(q, epsilon) = q
            delta*(q, wa)      = delta(delta*(q, w), a)
        implementada iterativamente para eficiencia.
        """
        current = state
        for symbol in word:
            current = self.step(current, symbol)
        return current

    def run(self, word: str) -> str:
        """delta*(q0, word). Estado alcanzado por w desde el estado inicial."""
        return self.delta_star(self.start, word)

    def accepts(self, word: str) -> bool:
        """True si y solo si w in L(A)."""
        return self.run(word) in self.accepting

    # ------------------------------------------------------------------
    # Transformaciones inducidas por palabras
    # ------------------------------------------------------------------

    def transformation(self, word: str) -> Dict[str, str]:
        """Calcula la transformacion f_w : Q -> Q inducida por w.

        Se define f_w(q) = delta*(q, w). Esta es la pieza fundamental
        sobre la que se construye el monoide de transicion en
        transition_monoid.py.
        """
        return {q: self.delta_star(q, word) for q in self.states}

    # ------------------------------------------------------------------
    # Constructores auxiliares
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "DFA":
        """Construye un DFA a partir de un diccionario simple."""
        return cls(
            states=set(data["states"]),
            alphabet=set(data["alphabet"]),
            transitions={
                q: dict(row) for q, row in data["transitions"].items()
            },
            start=data["start"],
            accepting=set(data["accepting"]),
            name=data.get("name", "DFA"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "DFA":
        """Carga un DFA desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serializa el DFA a un diccionario compatible con from_dict."""
        return {
            "name": self.name,
            "states": sorted(self.states),
            "alphabet": sorted(self.alphabet),
            "transitions": {
                q: dict(self.transitions[q]) for q in sorted(self.states)
            },
            "start": self.start,
            "accepting": sorted(self.accepting),
        }

    # ------------------------------------------------------------------
    # Representacion legible
    # ------------------------------------------------------------------

    def transition_table(self) -> List[List[str]]:
        """Devuelve la tabla de transiciones como una matriz de cadenas.

        La primera fila contiene los simbolos del alfabeto y la primera
        columna los estados. Las celdas restantes contienen delta(q, a).
        """
        symbols = sorted(self.alphabet)
        header = ["delta"] + symbols
        rows: List[List[str]] = [header]
        for q in sorted(self.states):
            mark = ""
            if q == self.start:
                mark += "->"
            if q in self.accepting:
                mark += "*"
            label = f"{mark}{q}" if mark else q
            rows.append([label] + [self.transitions[q][a] for a in symbols])
        return rows

    def pretty_transition_table(self) -> str:
        """Formatea transition_table como texto monoespaciado."""
        rows = self.transition_table()
        widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
        out_lines: List[str] = []
        for r_idx, row in enumerate(rows):
            cells = [cell.ljust(widths[i]) for i, cell in enumerate(row)]
            out_lines.append(" | ".join(cells))
            if r_idx == 0:
                out_lines.append("-+-".join("-" * w for w in widths))
        return "\n".join(out_lines)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"DFA(name={self.name!r}, |Q|={len(self.states)}, "
            f"|Sigma|={len(self.alphabet)}, |F|={len(self.accepting)})"
        )


__all__ = ["DFA", "DFAValidationError"]
