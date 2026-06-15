"""
backend.models.pda
==================

Automata de Pila (Pushdown Automaton - PDA).

Un PDA se define formalmente como una 7-tupla:

    P = (Q, Sigma, Gamma, delta, q0, Z0, F)

donde:
    Q       : conjunto finito de estados.
    Sigma   : alfabeto de entrada.
    Gamma   : alfabeto de pila.
    delta   : Q x (Sigma ∪ {λ}) x Gamma -> P(Q x Gamma*),
              funcion de transicion.
    q0      : estado inicial.
    Z0      : simbolo inicial de la pila.
    F       : conjunto de estados de aceptacion.

El PDA acepta por estado final:
    L(P) = { w : (q0, w, Z0) ⊢* (q_f, λ, γ), q_f ∈ F }

o por pila vacia:
    N(P) = { w : (q0, w, Z0) ⊢* (q, λ, λ) }

Este modulo implementa la simulacion no determinista con backtracking
limitado (BFS con cota de pasos) y produce trazas paso a paso para
la animacion educativa de la pila.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


LAMBDA = "λ"


class PDAValidationError(ValueError):
    """Se lanza cuando la definicion de un PDA no es valida."""


# A PDA configuration is (state, remaining_input_index, stack)
Configuration = Tuple[str, int, Tuple[str, ...]]

# A transition rule: (state, input_symbol_or_epsilon, stack_top) -> [(new_state, push_string)]
TransitionRule = Tuple[str, List[str]]  # (new_state, symbols to push onto stack)


@dataclass
class PDATransition:
    """Una regla de transicion del PDA.

    Representa: delta(from_state, input_symbol, stack_top) ∋ (to_state, push_symbols)

    Donde push_symbols es la cadena que se escribe en la pila
    (el primer simbolo queda en el tope).
    """
    from_state: str
    input_symbol: str   # symbol from Sigma, or LAMBDA
    stack_top: str      # symbol from Gamma to pop
    to_state: str
    push_symbols: List[str]  # symbols to push (first = new top), empty = pop without push

    def __str__(self) -> str:
        inp = self.input_symbol if self.input_symbol != LAMBDA else "λ"
        push = "".join(self.push_symbols) if self.push_symbols else "λ"
        return f"δ({self.from_state}, {inp}, {self.stack_top}) → ({self.to_state}, {push})"


@dataclass
class PDAStep:
    """Un paso en la ejecucion del PDA, para animacion."""
    state: str
    input_remaining: str
    stack: List[str]
    rule_applied: Optional[PDATransition] = None
    description: str = ""


@dataclass
class PDA:
    """Automata de Pila (Pushdown Automaton).

    Atributos
    ---------
    states : set[str]
    input_alphabet : set[str]
    stack_alphabet : set[str]
    transitions : list[PDATransition]
    start : str
    start_symbol : str       # Z0, simbolo inicial de la pila
    accepting : set[str]
    name : str
    """

    states: Set[str]
    input_alphabet: Set[str]
    stack_alphabet: Set[str]
    transitions: List[PDATransition]
    start: str
    start_symbol: str
    accepting: Set[str]
    name: str = field(default="PDA")

    def __post_init__(self) -> None:
        self.states = set(self.states)
        self.input_alphabet = set(self.input_alphabet)
        self.stack_alphabet = set(self.stack_alphabet)
        self.accepting = set(self.accepting)
        self.validate()

    def validate(self) -> None:
        """Verifica que el PDA es estructuralmente correcto."""
        if not self.states:
            raise PDAValidationError("Q no puede ser vacio.")
        if not self.input_alphabet:
            raise PDAValidationError("Sigma no puede ser vacio.")
        if not self.stack_alphabet:
            raise PDAValidationError("Gamma no puede ser vacio.")
        if self.start not in self.states:
            raise PDAValidationError(
                f"Estado inicial {self.start!r} no pertenece a Q."
            )
        if self.start_symbol not in self.stack_alphabet:
            raise PDAValidationError(
                f"Simbolo inicial de pila {self.start_symbol!r} no pertenece a Gamma."
            )
        if not self.accepting.issubset(self.states):
            raise PDAValidationError("Algunos estados de aceptacion no pertenecen a Q.")

    # ------------------------------------------------------------------
    # Lookup de transiciones
    # ------------------------------------------------------------------

    def get_transitions(
        self, state: str, symbol: str, stack_top: str
    ) -> List[PDATransition]:
        """Obtiene las transiciones aplicables desde la configuracion dada.

        Busca transiciones que coincidan con (state, symbol, stack_top)
        y tambien transiciones λ (symbol = λ).
        """
        result: List[PDATransition] = []
        for t in self.transitions:
            if t.from_state != state:
                continue
            if t.stack_top != stack_top:
                continue
            if t.input_symbol == symbol or t.input_symbol == LAMBDA:
                result.append(t)
        return result

    # ------------------------------------------------------------------
    # Simulacion
    # ------------------------------------------------------------------

    def accepts(
        self,
        word: str,
        mode: str = "final_state",
        max_steps: int = 10000,
    ) -> bool:
        """Simula el PDA sobre la palabra dada.

        Parametros
        ----------
        word : str
            Palabra de entrada.
        mode : "final_state" | "empty_stack"
            Criterio de aceptacion.
        max_steps : int
            Limite de pasos para evitar bucles infinitos.

        Devuelve True si el PDA acepta la palabra.
        """
        result = self._simulate(word, mode, max_steps)
        return result is not None

    def simulate_trace(
        self,
        word: str,
        mode: str = "final_state",
        max_steps: int = 10000,
    ) -> Optional[List[PDAStep]]:
        """Simula el PDA y devuelve la traza de una ejecucion aceptante.

        Devuelve None si la palabra no es aceptada (dentro del limite de pasos).
        """
        return self._simulate(word, mode, max_steps)

    def _simulate(
        self,
        word: str,
        mode: str,
        max_steps: int,
    ) -> Optional[List[PDAStep]]:
        """BFS sobre configuraciones del PDA.

        Cada configuracion es (estado, indice_en_word, pila).
        Se usa BFS para encontrar la ruta mas corta a una
        configuracion aceptante, y se reconstruye la traza.
        """
        initial_stack = (self.start_symbol,)
        initial_config: Configuration = (self.start, 0, initial_stack)

        # BFS: queue of (config, parent_index, transition_used)
        queue: deque[Tuple[Configuration, int, Optional[PDATransition]]] = deque()
        queue.append((initial_config, -1, None))
        visited: Set[Configuration] = {initial_config}
        history: List[Tuple[Configuration, int, Optional[PDATransition]]] = []

        steps = 0
        while queue and steps < max_steps:
            config, parent_idx, trans = queue.popleft()
            current_idx = len(history)
            history.append((config, parent_idx, trans))

            state, pos, stack = config

            # Check acceptance
            accepted = False
            if pos == len(word):  # All input consumed
                if mode == "final_state" and state in self.accepting:
                    accepted = True
                elif mode == "empty_stack" and not stack:
                    accepted = True

            if accepted:
                # Reconstruct trace
                return self._reconstruct_trace(word, history, current_idx)

            # Generate next configurations
            if not stack:
                continue  # No stack symbol to match

            stack_top = stack[-1]
            applicable: List[PDATransition] = []

            # Transitions consuming input
            if pos < len(word):
                symbol = word[pos]
                applicable.extend(self.get_transitions(state, symbol, stack_top))

            # Lambda transitions (don't consume input)
            for t in self.transitions:
                if (t.from_state == state and
                    t.input_symbol == LAMBDA and
                    t.stack_top == stack_top):
                    applicable.append(t)

            for t in applicable:
                new_pos = pos if t.input_symbol == LAMBDA else pos + 1
                # Pop stack_top, push new symbols
                new_stack = stack[:-1]  # pop
                # Push symbols (last element of push_symbols goes deepest)
                for sym in reversed(t.push_symbols):
                    new_stack = new_stack + (sym,)

                new_config: Configuration = (t.to_state, new_pos, new_stack)
                if new_config not in visited:
                    visited.add(new_config)
                    queue.append((new_config, current_idx, t))
                    steps += 1

        return None  # Not accepted within step limit

    def _reconstruct_trace(
        self,
        word: str,
        history: List[Tuple[Configuration, int, Optional[PDATransition]]],
        final_idx: int,
    ) -> List[PDAStep]:
        """Reconstruye la traza de ejecucion desde el historial BFS."""
        path_indices: List[int] = []
        idx = final_idx
        while idx >= 0:
            path_indices.append(idx)
            _, parent, _ = history[idx]
            idx = parent
        path_indices.reverse()

        trace: List[PDAStep] = []
        for i in path_indices:
            config, _, trans = history[i]
            state, pos, stack = config
            remaining = word[pos:]
            trace.append(PDAStep(
                state=state,
                input_remaining=remaining,
                stack=list(stack),
                rule_applied=trans,
                description=str(trans) if trans else "Configuracion inicial",
            ))
        return trace

    # ------------------------------------------------------------------
    # Serializacion
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "PDA":
        """Construye un PDA a partir de un diccionario."""
        transitions: List[PDATransition] = []
        for rule in data.get("transitions", []):
            transitions.append(PDATransition(
                from_state=rule["from"],
                input_symbol=rule.get("input", LAMBDA),
                stack_top=rule["stack_top"],
                to_state=rule["to"],
                push_symbols=rule.get("push", []),
            ))
        return cls(
            states=set(data["states"]),
            input_alphabet=set(data["input_alphabet"]),
            stack_alphabet=set(data["stack_alphabet"]),
            transitions=transitions,
            start=data["start"],
            start_symbol=data["start_symbol"],
            accepting=set(data.get("accepting", [])),
            name=data.get("name", "PDA"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "PDA":
        """Carga un PDA desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serializa el PDA a un diccionario."""
        transitions = []
        for t in self.transitions:
            transitions.append({
                "from": t.from_state,
                "input": t.input_symbol,
                "stack_top": t.stack_top,
                "to": t.to_state,
                "push": t.push_symbols,
            })
        return {
            "name": self.name,
            "type": "PDA",
            "states": sorted(self.states),
            "input_alphabet": sorted(self.input_alphabet),
            "stack_alphabet": sorted(self.stack_alphabet),
            "transitions": transitions,
            "start": self.start,
            "start_symbol": self.start_symbol,
            "accepting": sorted(self.accepting),
        }

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"PDA(name={self.name!r}, |Q|={len(self.states)}, "
            f"|Sigma|={len(self.input_alphabet)}, "
            f"|Gamma|={len(self.stack_alphabet)}, |F|={len(self.accepting)})"
        )


__all__ = ["PDA", "PDATransition", "PDAStep", "PDAValidationError", "LAMBDA"]
