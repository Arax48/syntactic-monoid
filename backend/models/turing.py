"""
backend.models.turing
=====================

Maquina de Turing (TM) de una sola cinta.

Una maquina de Turing se define formalmente como una 7-tupla:

    M = (Q, Sigma, Gamma, delta, q0, q_accept, q_reject)

donde:
    Q         : conjunto finito de estados.
    Sigma     : alfabeto de entrada (no incluye el blanco).
    Gamma     : alfabeto de la cinta (Sigma ⊂ Gamma, incluye el blanco).
    delta     : Q x Gamma -> Q x Gamma x {L, R}, funcion de transicion.
    q0        : estado inicial.
    q_accept  : estado de aceptacion.
    q_reject  : estado de rechazo.

La cinta es infinita hacia la derecha, inicializada con la entrada
y espacios en blanco (B) en el resto.

La TM para en q_accept o q_reject. Si no para dentro del limite
de pasos, se reporta como "timeout" (reflejo practico del
problema de la detencion).

Funcionalidad:
    - run(input)           : ejecuta la TM hasta aceptar/rechazar/timeout
    - run_trace(input)     : traza paso a paso con snapshots de la cinta
    - TuringTape           : clase auxiliar para la cinta infinita
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


BLANK = "B"  # Simbolo de blanco


class Direction(Enum):
    """Direccion de movimiento del cabezal."""
    LEFT = "L"
    RIGHT = "R"
    STAY = "S"  # Extension: no moverse


class TMResult(Enum):
    """Resultado de la ejecucion de la TM."""
    ACCEPT = "accept"
    REJECT = "reject"
    TIMEOUT = "timeout"


class TMValidationError(ValueError):
    """Se lanza cuando la TM no es valida."""


class TuringTape:
    """Cinta infinita (hacia la derecha) de la maquina de Turing.

    Internamente se representa como una lista que crece dinamicamente.
    Las posiciones negativas del cabezal no son validas (la cinta
    es semi-infinita).
    """

    def __init__(self, input_word: str = "", blank: str = BLANK) -> None:
        self.blank = blank
        self._cells: List[str] = list(input_word) if input_word else []
        self.head: int = 0

    def read(self) -> str:
        """Lee el simbolo bajo el cabezal."""
        if self.head < 0:
            return self.blank
        if self.head >= len(self._cells):
            return self.blank
        return self._cells[self.head]

    def write(self, symbol: str) -> None:
        """Escribe un simbolo bajo el cabezal."""
        # Extend tape if necessary
        while self.head >= len(self._cells):
            self._cells.append(self.blank)
        if self.head >= 0:
            self._cells[self.head] = symbol

    def move(self, direction: Direction) -> None:
        """Mueve el cabezal en la direccion indicada."""
        if direction == Direction.LEFT:
            self.head = max(0, self.head - 1)
        elif direction == Direction.RIGHT:
            self.head += 1
            # Extend if needed
            while self.head >= len(self._cells):
                self._cells.append(self.blank)

    def snapshot(self) -> Tuple[List[str], int]:
        """Devuelve una copia del contenido actual y la posicion del cabezal.

        Util para animaciones paso a paso.
        """
        # Trim trailing blanks for readability (keep at least up to head)
        cells = list(self._cells)
        min_len = self.head + 1
        while len(cells) > min_len and cells[-1] == self.blank:
            cells.pop()
        return cells, self.head

    def __str__(self) -> str:
        cells, head = self.snapshot()
        parts: List[str] = []
        for i, c in enumerate(cells):
            if i == head:
                parts.append(f"[{c}]")
            else:
                parts.append(f" {c} ")
        return "".join(parts)


@dataclass
class TMTransition:
    """Una regla de transicion de la TM.

    delta(from_state, read_symbol) = (to_state, write_symbol, direction)
    """
    from_state: str
    read_symbol: str
    to_state: str
    write_symbol: str
    direction: Direction

    def __str__(self) -> str:
        return (
            f"δ({self.from_state}, {self.read_symbol}) → "
            f"({self.to_state}, {self.write_symbol}, {self.direction.value})"
        )


@dataclass
class TMStep:
    """Un paso en la ejecucion de la TM, para animacion."""
    step_number: int
    state: str
    tape_content: List[str]
    head_position: int
    symbol_read: str
    rule_applied: Optional[TMTransition] = None
    description: str = ""


@dataclass
class TMRunResult:
    """Resultado completo de la ejecucion de una TM."""
    result: TMResult
    steps: int
    final_state: str
    final_tape: List[str]
    final_head: int
    trace: List[TMStep]


@dataclass
class TuringMachine:
    """Maquina de Turing de una sola cinta.

    Atributos
    ---------
    states : set[str]
    input_alphabet : set[str]       # No incluye BLANK
    tape_alphabet : set[str]        # Incluye BLANK
    transitions : list[TMTransition]
    start : str
    accept_state : str
    reject_state : str
    name : str
    """

    states: Set[str]
    input_alphabet: Set[str]
    tape_alphabet: Set[str]
    transitions: List[TMTransition]
    start: str
    accept_state: str
    reject_state: str
    name: str = field(default="TM")

    def __post_init__(self) -> None:
        self.states = set(self.states)
        self.input_alphabet = set(self.input_alphabet)
        self.tape_alphabet = set(self.tape_alphabet)
        # Build transition lookup table
        self._delta: Dict[Tuple[str, str], TMTransition] = {}
        for t in self.transitions:
            key = (t.from_state, t.read_symbol)
            self._delta[key] = t
        self.validate()

    def validate(self) -> None:
        """Verifica que la TM es estructuralmente correcta."""
        if not self.states:
            raise TMValidationError("Q no puede ser vacio.")
        if not self.input_alphabet:
            raise TMValidationError("Sigma no puede ser vacio.")
        if self.start not in self.states:
            raise TMValidationError(
                f"Estado inicial {self.start!r} no pertenece a Q."
            )
        if self.accept_state not in self.states:
            raise TMValidationError(
                f"Estado de aceptacion {self.accept_state!r} no pertenece a Q."
            )
        if self.reject_state not in self.states:
            raise TMValidationError(
                f"Estado de rechazo {self.reject_state!r} no pertenece a Q."
            )
        if self.accept_state == self.reject_state:
            raise TMValidationError(
                "El estado de aceptacion y rechazo deben ser distintos."
            )
        if not self.input_alphabet.issubset(self.tape_alphabet):
            raise TMValidationError(
                "Sigma debe ser subconjunto de Gamma."
            )
        if BLANK not in self.tape_alphabet:
            raise TMValidationError(
                f"El simbolo blanco '{BLANK}' debe pertenecer a Gamma."
            )
        if BLANK in self.input_alphabet:
            raise TMValidationError(
                f"El simbolo blanco '{BLANK}' no debe pertenecer a Sigma."
            )

    # ------------------------------------------------------------------
    # Ejecucion
    # ------------------------------------------------------------------

    def run(
        self,
        input_word: str,
        max_steps: int = 10000,
        record_trace: bool = True,
    ) -> TMRunResult:
        """Ejecuta la TM sobre la palabra de entrada.

        Parametros
        ----------
        input_word : str
            Palabra de entrada (debe estar en Sigma*).
        max_steps : int
            Limite de pasos para evitar ejecuciones infinitas.
        record_trace : bool
            Si True, guarda cada paso para animacion.

        Devuelve
        --------
        TMRunResult con el resultado, pasos, y opcionalmente la traza.
        """
        # Validate input
        for symbol in input_word:
            if symbol not in self.input_alphabet:
                raise ValueError(
                    f"Simbolo {symbol!r} no pertenece al alfabeto de entrada."
                )

        tape = TuringTape(input_word)
        state = self.start
        trace: List[TMStep] = []

        for step in range(max_steps):
            symbol = tape.read()
            tape_content, head_pos = tape.snapshot()

            if record_trace:
                trace.append(TMStep(
                    step_number=step,
                    state=state,
                    tape_content=list(tape_content),
                    head_position=head_pos,
                    symbol_read=symbol,
                    description=f"Estado: {state}, Lee: {symbol}",
                ))

            # Check halting states
            if state == self.accept_state:
                return TMRunResult(
                    result=TMResult.ACCEPT,
                    steps=step,
                    final_state=state,
                    final_tape=tape_content,
                    final_head=head_pos,
                    trace=trace,
                )
            if state == self.reject_state:
                return TMRunResult(
                    result=TMResult.REJECT,
                    steps=step,
                    final_state=state,
                    final_tape=tape_content,
                    final_head=head_pos,
                    trace=trace,
                )

            # Look up transition
            key = (state, symbol)
            if key not in self._delta:
                # No transition defined = implicit reject
                return TMRunResult(
                    result=TMResult.REJECT,
                    steps=step,
                    final_state=state,
                    final_tape=tape_content,
                    final_head=head_pos,
                    trace=trace,
                )

            transition = self._delta[key]
            if record_trace and trace:
                trace[-1].rule_applied = transition

            # Apply transition
            tape.write(transition.write_symbol)
            tape.move(transition.direction)
            state = transition.to_state

        # Timeout
        tape_content, head_pos = tape.snapshot()
        return TMRunResult(
            result=TMResult.TIMEOUT,
            steps=max_steps,
            final_state=state,
            final_tape=tape_content,
            final_head=head_pos,
            trace=trace,
        )

    def accepts(self, word: str, max_steps: int = 10000) -> bool:
        """True si la TM acepta la palabra."""
        return self.run(word, max_steps, record_trace=False).result == TMResult.ACCEPT

    # ------------------------------------------------------------------
    # Serializacion
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "TuringMachine":
        """Construye una TM a partir de un diccionario."""
        transitions: List[TMTransition] = []
        for rule in data.get("transitions", []):
            direction_str = rule.get("direction", "R").upper()
            if direction_str == "L":
                direction = Direction.LEFT
            elif direction_str == "S":
                direction = Direction.STAY
            else:
                direction = Direction.RIGHT

            transitions.append(TMTransition(
                from_state=rule["from"],
                read_symbol=rule["read"],
                to_state=rule["to"],
                write_symbol=rule["write"],
                direction=direction,
            ))

        return cls(
            states=set(data["states"]),
            input_alphabet=set(data["input_alphabet"]),
            tape_alphabet=set(data["tape_alphabet"]),
            transitions=transitions,
            start=data["start"],
            accept_state=data["accept_state"],
            reject_state=data["reject_state"],
            name=data.get("name", "TM"),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "TuringMachine":
        """Carga una TM desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serializa la TM a un diccionario."""
        transitions = []
        for t in self.transitions:
            transitions.append({
                "from": t.from_state,
                "read": t.read_symbol,
                "to": t.to_state,
                "write": t.write_symbol,
                "direction": t.direction.value,
            })
        return {
            "name": self.name,
            "type": "TM",
            "states": sorted(self.states),
            "input_alphabet": sorted(self.input_alphabet),
            "tape_alphabet": sorted(self.tape_alphabet),
            "transitions": transitions,
            "start": self.start,
            "accept_state": self.accept_state,
            "reject_state": self.reject_state,
        }

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"TM(name={self.name!r}, |Q|={len(self.states)}, "
            f"|Sigma|={len(self.input_alphabet)}, "
            f"|Gamma|={len(self.tape_alphabet)})"
        )


__all__ = [
    "TuringMachine", "TuringTape", "TMTransition", "TMStep",
    "TMRunResult", "TMResult", "TMValidationError",
    "Direction", "BLANK",
]
