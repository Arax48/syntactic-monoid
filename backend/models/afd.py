"""
backend.models.afd
==================

Modulo de Automata Finito Determinista (AFD), segun §2.3 del libro de
Rodrigo De Castro ("Introduccion a la Teoria de la Computacion").

Un AFD se define formalmente como una 5-tupla (§2.3):

    M = (Σ, Q, q0, F, δ)

donde:
    Σ   : alfabeto de entrada (tambien llamado alfabeto de cinta).
          Todas las cadenas que lee M pertenecen a Σ*.
    Q   : conjunto finito de estados internos de la unidad de control,
          Q = {q0, q1, ..., qn}.
    q0  : estado inicial, q0 ∈ Q.
    F   : conjunto de estados finales o de aceptacion, F ⊆ Q, F ≠ ∅.
    δ   : funcion de transicion δ : Q × Σ → Q.

Una instruccion δ(q, s) = q' significa: estando en el estado q, en
presencia del simbolo s, la unidad de control pasa al estado q' y se
desplaza una casilla a la derecha (§2.3).

La funcion de transicion extendida δ̂ : Q × Σ* → Q se define
recursivamente (§2.7.2) como:

    δ̂(q, λ) = q,                         q ∈ Q,
    δ̂(q, wa) = δ(δ̂(q, w), a),            w ∈ Σ*, a ∈ Σ.

El lenguaje aceptado o reconocido por M es:

    L(M) = { w ∈ Σ* : δ̂(q0, w) ∈ F }.

Funcionalidades implementadas en este modulo, todas alineadas con
los capitulos 2 y 2.16 del libro:

    minimize()              algoritmo de minimizacion de AFDs (§2.16)
    complement()            AFD que reconoce Σ* − L(M) (§2.10)
    intersection() / union() construccion del producto cartesiano (§2.11)
    is_equivalent()         equivalencia de lenguajes via producto (§2.11)
    find_counterexample()   contraejemplo mas corto cuando difieren
    reachable_states()      estados accesibles desde q0 (§2.7.3)
    is_minimal()            True si el AFD ya es minimo (§2.16)
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from itertools import product as iter_product
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from backend.models.transformation import Transformation


class AFDValidationError(ValueError):
    """Se lanza cuando la definicion de un AFD no es estructuralmente valida."""


@dataclass
class AFD:
    """Automata Finito Determinista (§2.3 De Castro).

    La 5-tupla M = (Σ, Q, q0, F, δ) se representa por:

        alphabet     ~  Σ   (alfabeto de entrada)
        states       ~  Q   (estados internos de la unidad de control)
        start        ~  q0  (estado inicial)
        accepting    ~  F   (estados de aceptacion, F ≠ ∅, F ⊆ Q)
        transitions  ~  δ   (transitions[q][a] = δ(q, a))

    El AFD lee la cadena de entrada de izquierda a derecha, partiendo
    del estado inicial q0; segun §2.3, la accion δ(q, s) = q' es el
    paso computacional basico: cambiar al estado q' y desplazar la
    cabeza una casilla a la derecha.

    Atributos
    ---------
    states : set[str]
        Conjunto finito de estados Q.
    alphabet : set[str]
        Alfabeto finito Σ de entrada.
    transitions : dict[str, dict[str, str]]
        Funcion de transicion δ representada como diccionario anidado:
        transitions[q][a] = δ(q, a).
    start : str
        Estado inicial q0.
    accepting : set[str]
        Conjunto de estados de aceptacion F.
    name : str
        Nombre legible del AFD (opcional, util para reportes).
    """

    states: Set[str]
    alphabet: Set[str]
    transitions: Dict[str, Dict[str, str]]
    start: str
    accepting: Set[str]
    name: str = field(default="AFD")

    def __post_init__(self) -> None:
        self.states = set(self.states)
        self.alphabet = set(self.alphabet)
        self.accepting = set(self.accepting)
        self.validate()

    # ------------------------------------------------------------------
    # Validacion estructural
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Verifica que el AFD es estructuralmente correcto.

        En particular:
            * Q no es vacio.
            * Sigma no es vacio.
            * q0 in Q.
            * F subset Q.
            * delta esta totalmente definida: para todo q in Q y a in Sigma
              existe un valor delta(q, a) in Q.
        """
        if not self.states:
            raise AFDValidationError("Q (estados) no puede ser vacio.")
        if not self.alphabet:
            raise AFDValidationError("Sigma (alfabeto) no puede ser vacio.")
        if self.start not in self.states:
            raise AFDValidationError(
                f"El estado inicial {self.start!r} no pertenece a Q."
            )
        if not self.accepting.issubset(self.states):
            extra = self.accepting - self.states
            raise AFDValidationError(
                f"Estados de aceptacion fuera de Q: {sorted(extra)!r}."
            )
        for q in self.states:
            if q not in self.transitions:
                raise AFDValidationError(
                    f"delta no esta definida para el estado {q!r}."
                )
            row = self.transitions[q]
            for a in self.alphabet:
                if a not in row:
                    raise AFDValidationError(
                        f"delta({q!r}, {a!r}) no esta definida."
                    )
                if row[a] not in self.states:
                    raise AFDValidationError(
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
            delta*(q, λ) = q
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

    def run_trace(self, word: str) -> List[Tuple[str, str, str]]:
        """Ejecuta la palabra devolviendo la traza completa.

        Devuelve una lista de triples (estado_actual, simbolo, estado_siguiente)
        para cada paso de la ejecucion. Util para animaciones paso a paso.
        """
        trace: List[Tuple[str, str, str]] = []
        current = self.start
        for symbol in word:
            next_state = self.step(current, symbol)
            trace.append((current, symbol, next_state))
            current = next_state
        return trace

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
    # Operaciones sobre lenguajes (NUEVAS)
    # ------------------------------------------------------------------

    def reachable_states(self) -> Set[str]:
        """Devuelve el conjunto de estados alcanzables desde q0.

        Un estado q es alcanzable si existe alguna palabra w tal que
        delta*(q0, w) = q. Se calcula mediante BFS.
        """
        visited: Set[str] = set()
        queue: deque[str] = deque([self.start])
        visited.add(self.start)
        while queue:
            state = queue.popleft()
            for a in self.alphabet:
                next_s = self.transitions[state][a]
                if next_s not in visited:
                    visited.add(next_s)
                    queue.append(next_s)
        return visited

    def complement(self) -> "AFD":
        """Devuelve el AFD que acepta el complemento de L(A).

        El complemento se obtiene simplemente invirtiendo los estados
        de aceptacion: F' = Q - F.
        """
        return AFD(
            states=set(self.states),
            alphabet=set(self.alphabet),
            transitions={q: dict(row) for q, row in self.transitions.items()},
            start=self.start,
            accepting=self.states - self.accepting,
            name=f"Complement({self.name})",
        )

    def intersection(self, other: "AFD") -> "AFD":
        """Construye el AFD producto que acepta L(A) ∩ L(B).

        Usa la construccion de producto cartesiano:
            Q' = Q_A × Q_B
            delta'((p,q), a) = (delta_A(p,a), delta_B(q,a))
            F' = F_A × F_B
        """
        if self.alphabet != other.alphabet:
            raise ValueError("Los AFDs deben tener el mismo alfabeto.")
        return self._product(other, lambda a, b: a and b, "Intersection")

    def union(self, other: "AFD") -> "AFD":
        """Construye el AFD producto que acepta L(A) ∪ L(B)."""
        if self.alphabet != other.alphabet:
            raise ValueError("Los AFDs deben tener el mismo alfabeto.")
        return self._product(other, lambda a, b: a or b, "Union")

    def symmetric_difference(self, other: "AFD") -> "AFD":
        """Construye el AFD que acepta L(A) △ L(B) (diferencia simetrica).

        Util para verificar equivalencia: L(A) = L(B) ⟺ L(A) △ L(B) = ∅.
        """
        if self.alphabet != other.alphabet:
            raise ValueError("Los AFDs deben tener el mismo alfabeto.")
        return self._product(other, lambda a, b: a != b, "SymDiff")

    def _product(
        self,
        other: "AFD",
        accept_fn,
        label: str,
    ) -> "AFD":
        """Construccion generica de producto de dos AFDs."""
        def pair(p: str, q: str) -> str:
            return f"({p},{q})"

        states: Set[str] = set()
        transitions: Dict[str, Dict[str, str]] = {}
        accepting: Set[str] = set()
        start = pair(self.start, other.start)

        # BFS to build only reachable states
        queue: deque[Tuple[str, str]] = deque([(self.start, other.start)])
        visited: Set[Tuple[str, str]] = {(self.start, other.start)}

        while queue:
            p, q = queue.popleft()
            s = pair(p, q)
            states.add(s)
            transitions[s] = {}
            if accept_fn(p in self.accepting, q in other.accepting):
                accepting.add(s)
            for a in sorted(self.alphabet):
                np = self.transitions[p][a]
                nq = other.transitions[q][a]
                transitions[s][a] = pair(np, nq)
                if (np, nq) not in visited:
                    visited.add((np, nq))
                    queue.append((np, nq))

        return AFD(
            states=states,
            alphabet=set(self.alphabet),
            transitions=transitions,
            start=start,
            accepting=accepting,
            name=f"{label}({self.name}, {other.name})",
        )

    def is_empty(self) -> bool:
        """True si L(A) = ∅ (no acepta ninguna palabra).

        Se verifica comprobando si algun estado de aceptacion
        es alcanzable desde q0.
        """
        return not (self.reachable_states() & self.accepting)

    def is_equivalent(self, other: "AFD") -> bool:
        """True si L(A) = L(B).

        Se verifica comprobando que la diferencia simetrica es vacia.
        """
        return self.symmetric_difference(other).is_empty()

    def find_counterexample(self, other: "AFD") -> Optional[str]:
        """Encuentra una palabra aceptada por exactamente uno de los dos AFDs.

        Devuelve None si los AFDs son equivalentes.
        Util para dar feedback al estudiante: "Tu automata acepta '010'
        pero no deberia".
        """
        sym_diff = self.symmetric_difference(other)
        # BFS to find a word accepted by the symmetric difference
        if sym_diff.is_empty():
            return None

        queue: deque[Tuple[str, str]] = deque()
        # We need to track the word that reaches each state
        visited: Dict[str, str] = {}  # state -> word
        start = sym_diff.start
        visited[start] = ""
        queue.append((start, ""))

        if start in sym_diff.accepting:
            return ""

        while queue:
            state, word = queue.popleft()
            for a in sorted(sym_diff.alphabet):
                next_s = sym_diff.transitions[state][a]
                if next_s not in visited:
                    new_word = word + a
                    visited[next_s] = new_word
                    if next_s in sym_diff.accepting:
                        return new_word
                    queue.append((next_s, new_word))

        return None

    def minimize(self) -> "AFD":
        """Devuelve el AFD minimo equivalente usando el algoritmo de Hopcroft.

        El AFD minimo tiene el menor numero posible de estados y acepta
        exactamente el mismo lenguaje. Es unico salvo renombramiento de estados.
        """
        # Step 1: Remove unreachable states
        reachable = self.reachable_states()

        # Step 2: Hopcroft's partition refinement
        symbols = sorted(self.alphabet)

        # Initial partition: accepting vs non-accepting (among reachable)
        accepting_r = reachable & self.accepting
        non_accepting_r = reachable - self.accepting

        # Handle edge cases
        if not accepting_r:
            # Empty language - single non-accepting state
            trap = "q0"
            return AFD(
                states={trap},
                alphabet=set(self.alphabet),
                transitions={trap: {a: trap for a in self.alphabet}},
                start=trap,
                accepting=set(),
                name=f"Min({self.name})",
            )
        if not non_accepting_r:
            # Universal language (over reachable states) - single accepting state
            sink = "q0"
            return AFD(
                states={sink},
                alphabet=set(self.alphabet),
                transitions={sink: {a: sink for a in self.alphabet}},
                start=sink,
                accepting={sink},
                name=f"Min({self.name})",
            )

        partition: List[Set[str]] = [accepting_r, non_accepting_r]
        worklist: List[Set[str]] = [accepting_r, non_accepting_r]

        while worklist:
            splitter = worklist.pop()
            for a in symbols:
                # States that transition to splitter on symbol a
                predecessors: Set[str] = set()
                for q in reachable:
                    if self.transitions[q][a] in splitter:
                        predecessors.add(q)
                new_partition: List[Set[str]] = []
                for block in partition:
                    intersection = block & predecessors
                    difference = block - predecessors
                    if intersection and difference:
                        new_partition.append(intersection)
                        new_partition.append(difference)
                        if block in worklist:
                            worklist.remove(block)
                            worklist.append(intersection)
                            worklist.append(difference)
                        else:
                            if len(intersection) <= len(difference):
                                worklist.append(intersection)
                            else:
                                worklist.append(difference)
                    else:
                        new_partition.append(block)
                partition = new_partition

        # Step 3: Build minimized AFD
        # Map each state to its block representative
        state_to_block: Dict[str, int] = {}
        for i, block in enumerate(partition):
            for q in block:
                state_to_block[q] = i

        new_states: Set[str] = set()
        new_transitions: Dict[str, Dict[str, str]] = {}
        new_accepting: Set[str] = set()

        for i, block in enumerate(partition):
            state_name = f"q{i}"
            new_states.add(state_name)
            rep = next(iter(block))  # Any representative
            new_transitions[state_name] = {}
            for a in symbols:
                target_block = state_to_block[self.transitions[rep][a]]
                new_transitions[state_name][a] = f"q{target_block}"
            if rep in self.accepting:
                new_accepting.add(state_name)

        new_start = f"q{state_to_block[self.start]}"

        return AFD(
            states=new_states,
            alphabet=set(self.alphabet),
            transitions=new_transitions,
            start=new_start,
            accepting=new_accepting,
            name=f"Min({self.name})",
        )

    def is_minimal(self) -> bool:
        """True si el AFD ya es minimo.

        Un AFD es minimo si tiene el menor numero de estados posible
        para su lenguaje y todos sus estados son alcanzables.
        """
        minimized = self.minimize()
        return len(self.reachable_states()) == len(minimized.states)

    # ------------------------------------------------------------------
    # Constructores auxiliares
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "AFD":
        """Construye un AFD a partir de un diccionario simple."""
        return cls(
            states=set(data["states"]),
            alphabet=set(data["alphabet"]),
            transitions={
                q: dict(row) for q, row in data["transitions"].items()
            },
            start=data["start"],
            accepting=set(data["accepting"]),
            name=data.get("name", "AFD"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "AFD":
        """Carga un AFD desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serializa el AFD a un diccionario compatible con from_dict."""
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

    def to_json(self, path: str | Path) -> Path:
        """Guarda el AFD en un archivo JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return path

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
            f"AFD(name={self.name!r}, |Q|={len(self.states)}, "
            f"|Sigma|={len(self.alphabet)}, |F|={len(self.accepting)})"
        )


__all__ = ["AFD", "AFDValidationError"]
