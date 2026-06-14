"""
backend.models.nfa
==================

Automata Finito No Determinista (NFA) con transiciones epsilon.

Un NFA se define formalmente como una 5-tupla:

    N = (Q, Sigma, delta, q0, F)

donde:
    Q       : conjunto finito de estados.
    Sigma   : alfabeto finito.
    delta   : Q x (Sigma ∪ {ε}) -> P(Q), funcion de transicion.
    q0      : estado inicial, q0 ∈ Q.
    F       : conjunto de estados de aceptacion, F ⊆ Q.

La diferencia fundamental con un DFA es que delta puede devolver
multiples estados (o ninguno) y admite transiciones epsilon (sin
consumir simbolo).

El lenguaje aceptado por N es:

    L(N) = { w ∈ Sigma* : delta*(q0, w) ∩ F ≠ ∅ }

donde delta* se extiende a conjuntos de estados y a la cerradura epsilon.

Funcionalidad clave:
    - epsilon_closure(states) : cerradura epsilon de un conjunto de estados
    - move(states, symbol)    : estados alcanzables por un simbolo
    - accepts(word)           : simulacion no determinista
    - to_dfa()                : construccion de subconjuntos (subset construction)
    - run_trace()             : traza paso a paso para animacion
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


EPSILON = "ε"


class NFAValidationError(ValueError):
    """Se lanza cuando la definicion de un NFA no es estructuralmente valida."""


@dataclass
class NFA:
    """Automata Finito No Determinista con transiciones epsilon.

    Atributos
    ---------
    states : set[str]
        Conjunto finito de estados Q.
    alphabet : set[str]
        Alfabeto finito Sigma (NO incluye epsilon).
    transitions : dict[str, dict[str, set[str]]]
        Funcion de transicion delta. transitions[q][a] = conjunto de estados
        alcanzables desde q con el simbolo a.
    epsilon_transitions : dict[str, set[str]]
        Transiciones epsilon. epsilon_transitions[q] = conjunto de estados
        alcanzables desde q sin consumir simbolo.
    start : str
        Estado inicial q0.
    accepting : set[str]
        Conjunto de estados de aceptacion F.
    name : str
        Nombre legible del NFA.
    """

    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[str, Dict[str, Set[str]]]
    epsilon_transitions: Dict[str, Set[str]]
    start: str
    accepting: Set[str]
    name: str = field(default="NFA")

    def __post_init__(self) -> None:
        self.states = set(self.states)
        self.alphabet = set(self.alphabet)
        self.accepting = set(self.accepting)
        # Normalize transitions: ensure all states have entries
        for q in self.states:
            if q not in self.transitions:
                self.transitions[q] = {}
            for a in self.alphabet:
                if a not in self.transitions[q]:
                    self.transitions[q][a] = set()
                else:
                    self.transitions[q][a] = set(self.transitions[q][a])
            if q not in self.epsilon_transitions:
                self.epsilon_transitions[q] = set()
            else:
                self.epsilon_transitions[q] = set(self.epsilon_transitions[q])
        self.validate()

    # ------------------------------------------------------------------
    # Validacion
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Verifica que el NFA es estructuralmente correcto."""
        if not self.states:
            raise NFAValidationError("Q (estados) no puede ser vacio.")
        if not self.alphabet:
            raise NFAValidationError("Sigma (alfabeto) no puede ser vacio.")
        if self.start not in self.states:
            raise NFAValidationError(
                f"El estado inicial {self.start!r} no pertenece a Q."
            )
        if not self.accepting.issubset(self.states):
            extra = self.accepting - self.states
            raise NFAValidationError(
                f"Estados de aceptacion fuera de Q: {sorted(extra)!r}."
            )
        # Verify all transition targets are valid states
        for q in self.states:
            for a in self.alphabet:
                for target in self.transitions.get(q, {}).get(a, set()):
                    if target not in self.states:
                        raise NFAValidationError(
                            f"delta({q!r}, {a!r}) contiene {target!r} que no pertenece a Q."
                        )
            for target in self.epsilon_transitions.get(q, set()):
                if target not in self.states:
                    raise NFAValidationError(
                        f"Transicion epsilon desde {q!r} a {target!r}: {target!r} no pertenece a Q."
                    )

    # ------------------------------------------------------------------
    # Operaciones fundamentales
    # ------------------------------------------------------------------

    def epsilon_closure(self, states: Set[str]) -> FrozenSet[str]:
        """Cerradura epsilon de un conjunto de estados.

        ε-closure(S) es el conjunto de todos los estados alcanzables
        desde algun estado en S siguiendo solo transiciones epsilon
        (incluyendo los propios estados de S).

        Se calcula mediante BFS sobre las transiciones epsilon.
        """
        closure: Set[str] = set(states)
        queue: deque[str] = deque(states)
        while queue:
            q = queue.popleft()
            for target in self.epsilon_transitions.get(q, set()):
                if target not in closure:
                    closure.add(target)
                    queue.append(target)
        return frozenset(closure)

    def move(self, states: Set[str], symbol: str) -> FrozenSet[str]:
        """Conjunto de estados alcanzables desde `states` con `symbol`.

        move(S, a) = ∪_{q ∈ S} delta(q, a)

        NO incluye cerradura epsilon del resultado.
        """
        result: Set[str] = set()
        for q in states:
            result.update(self.transitions.get(q, {}).get(symbol, set()))
        return frozenset(result)

    def extended_move(self, states: Set[str], symbol: str) -> FrozenSet[str]:
        """Movimiento extendido: ε-closure(move(ε-closure(S), a)).

        Esto es lo que realmente se usa en la simulacion: primero
        expandimos por epsilon, luego movemos, luego expandimos de nuevo.
        """
        closed = self.epsilon_closure(states)
        moved = self.move(set(closed), symbol)
        return self.epsilon_closure(set(moved))

    # ------------------------------------------------------------------
    # Simulacion
    # ------------------------------------------------------------------

    def accepts(self, word: str) -> bool:
        """True si el NFA acepta la palabra.

        Simula el NFA rastreando todos los estados posibles
        simultaneamente (simulacion por conjuntos).
        """
        current = self.epsilon_closure({self.start})
        for symbol in word:
            if symbol not in self.alphabet:
                raise ValueError(f"Simbolo fuera del alfabeto: {symbol!r}")
            current = self.extended_move(set(current), symbol)
            if not current:
                return False
        return bool(current & self.accepting)

    def run_trace(self, word: str) -> List[Tuple[FrozenSet[str], str, FrozenSet[str]]]:
        """Traza de ejecucion paso a paso.

        Devuelve una lista de triples:
            (conjunto_estados_actual, simbolo, conjunto_estados_siguiente)

        El primer conjunto incluye la cerradura epsilon.
        """
        trace: List[Tuple[FrozenSet[str], str, FrozenSet[str]]] = []
        current = self.epsilon_closure({self.start})
        for symbol in word:
            if symbol not in self.alphabet:
                raise ValueError(f"Simbolo fuera del alfabeto: {symbol!r}")
            next_states = self.extended_move(set(current), symbol)
            trace.append((current, symbol, next_states))
            current = next_states
        return trace

    # ------------------------------------------------------------------
    # Conversion a DFA (Subset Construction)
    # ------------------------------------------------------------------

    def to_dfa(self) -> "DFA":
        """Convierte el NFA a un DFA equivalente usando la construccion
        de subconjuntos (subset construction).

        Algoritmo:
            1. El estado inicial del DFA es ε-closure({q0}).
            2. Para cada conjunto de estados S y cada simbolo a,
               el nuevo estado es ε-closure(move(S, a)).
            3. Un estado del DFA es de aceptacion si contiene algun
               estado de aceptacion del NFA.
            4. Se construye solo los estados alcanzables (BFS).

        Este es uno de los teoremas fundamentales de la teoria de la
        computacion: todo NFA tiene un DFA equivalente.
        """
        from backend.models.dfa import DFA

        symbols = sorted(self.alphabet)
        start_closure = self.epsilon_closure({self.start})

        # Map frozenset -> state name
        state_map: Dict[FrozenSet[str], str] = {}
        dfa_transitions: Dict[str, Dict[str, str]] = {}
        dfa_accepting: Set[str] = set()

        counter = 0
        queue: deque[FrozenSet[str]] = deque()

        def get_name(state_set: FrozenSet[str]) -> str:
            nonlocal counter
            if state_set not in state_map:
                # Use a readable name based on the contained states
                if not state_set:
                    name = "∅"
                else:
                    name = "{" + ",".join(sorted(state_set)) + "}"
                state_map[state_set] = name
                counter += 1
                queue.append(state_set)
            return state_map[state_set]

        dfa_start = get_name(start_closure)

        while queue:
            current_set = queue.popleft()
            current_name = state_map[current_set]
            dfa_transitions[current_name] = {}

            if current_set & self.accepting:
                dfa_accepting.add(current_name)

            for a in symbols:
                next_set = self.extended_move(set(current_set), a)
                next_name = get_name(next_set)
                dfa_transitions[current_name][a] = next_name

        # Handle empty set state (trap state)
        empty = frozenset()
        if empty in state_map:
            trap_name = state_map[empty]
            if trap_name not in dfa_transitions:
                dfa_transitions[trap_name] = {a: trap_name for a in symbols}

        return DFA(
            states=set(state_map.values()),
            alphabet=set(self.alphabet),
            transitions=dfa_transitions,
            start=dfa_start,
            accepting=dfa_accepting,
            name=f"DFA({self.name})",
        )

    # ------------------------------------------------------------------
    # Serializacion
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "NFA":
        """Construye un NFA a partir de un diccionario."""
        transitions: Dict[str, Dict[str, Set[str]]] = {}
        for q, row in data.get("transitions", {}).items():
            transitions[q] = {}
            for a, targets in row.items():
                if a == EPSILON or a == "epsilon":
                    continue  # epsilon handled separately
                transitions[q][a] = set(targets) if isinstance(targets, list) else {targets}

        epsilon_trans: Dict[str, Set[str]] = {}
        for q, targets in data.get("epsilon_transitions", {}).items():
            epsilon_trans[q] = set(targets) if isinstance(targets, list) else {targets}
        # Also check for epsilon in the transitions dict
        for q, row in data.get("transitions", {}).items():
            for key in (EPSILON, "epsilon"):
                if key in row:
                    targets = row[key]
                    existing = epsilon_trans.get(q, set())
                    if isinstance(targets, list):
                        existing.update(targets)
                    else:
                        existing.add(targets)
                    epsilon_trans[q] = existing

        return cls(
            states=set(data["states"]),
            alphabet=set(data["alphabet"]),
            transitions=transitions,
            epsilon_transitions=epsilon_trans,
            start=data["start"],
            accepting=set(data["accepting"]),
            name=data.get("name", "NFA"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "NFA":
        """Carga un NFA desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serializa el NFA a un diccionario."""
        transitions: Dict[str, Dict[str, List[str]]] = {}
        for q in sorted(self.states):
            transitions[q] = {}
            for a in sorted(self.alphabet):
                targets = self.transitions.get(q, {}).get(a, set())
                if targets:
                    transitions[q][a] = sorted(targets)

        epsilon: Dict[str, List[str]] = {}
        for q in sorted(self.states):
            targets = self.epsilon_transitions.get(q, set())
            if targets:
                epsilon[q] = sorted(targets)

        return {
            "name": self.name,
            "type": "NFA",
            "states": sorted(self.states),
            "alphabet": sorted(self.alphabet),
            "transitions": transitions,
            "epsilon_transitions": epsilon,
            "start": self.start,
            "accepting": sorted(self.accepting),
        }

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"NFA(name={self.name!r}, |Q|={len(self.states)}, "
            f"|Sigma|={len(self.alphabet)}, |F|={len(self.accepting)})"
        )


__all__ = ["NFA", "NFAValidationError", "EPSILON"]
