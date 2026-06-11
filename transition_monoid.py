"""
transition_monoid.py
====================

Construccion explicita del MONOIDE DE TRANSICION M(A) asociado a un DFA.

Definicion
----------
Sea A = (Q, Sigma, delta, q0, F) un DFA. Para cada w in Sigma* definimos
la transformacion inducida

    f_w : Q -> Q,    f_w(q) = delta*(q, w).

El conjunto

    M(A) = { f_w : w in Sigma* }

es cerrado bajo la composicion de funciones (puesto que f_{uv} = f_v o f_u),
contiene a la identidad f_epsilon = id_Q y la composicion de funciones es
asociativa. Por lo tanto (M(A), o, id_Q) es un monoide finito (los unicos
elementos posibles son funciones Q -> Q y hay solo |Q|^|Q| de estas).

Construccion algoritmica
------------------------
Se realiza una busqueda en anchura (BFS) sobre Sigma*. Se parte de la
identidad (representante de la palabra vacia) y se aplican uno a uno los
simbolos del alfabeto. Cada vez que aparece una transformacion no vista,
se anade a M(A). Como M(A) es finito, el proceso termina en a lo sumo
|Q|^|Q| pasos.

Para cada transformacion se conserva una palabra representante de
longitud minima (la primera con la que aparece en el BFS), lo que es
util para mostrar clases de equivalencia y para describir el monoide.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from dfa import DFA
from transformation import Transformation


class TransitionMonoid:
    """Monoide de transicion M(A) de un DFA.

    Atributos publicos
    ------------------
    dfa : DFA
        DFA fuente.
    elements : list[Transformation]
        Lista de las transformaciones del monoide (sin repeticiones).
    representatives : dict[Transformation, str]
        Para cada transformacion, una palabra w de longitud minima tal
        que f_w es esa transformacion.
    identity : Transformation
        Elemento identidad del monoide (igual a f_epsilon = id_Q).
    """

    def __init__(self, dfa: DFA) -> None:
        self.dfa = dfa
        self.identity: Transformation = Transformation.identity(dfa.states)
        self.elements: List[Transformation] = []
        self.representatives: Dict[Transformation, str] = {}
        self._index: Dict[Transformation, int] = {}
        self._generators: Dict[str, Transformation] = {
            a: Transformation({q: dfa.step(q, a) for q in dfa.states})
            for a in dfa.alphabet
        }
        self._build()

    # ------------------------------------------------------------------
    # Construccion
    # ------------------------------------------------------------------

    def _add(self, transformation: Transformation, word: str) -> bool:
        """Anade una transformacion si es nueva. Devuelve True si se anadio."""
        if transformation in self._index:
            return False
        self._index[transformation] = len(self.elements)
        self.elements.append(transformation)
        self.representatives[transformation] = word
        return True

    def _build(self) -> None:
        """BFS sobre Sigma*: parte de la identidad y aplica generadores."""
        self._add(self.identity, "")
        queue: Deque[Tuple[str, Transformation]] = deque([("", self.identity)])
        # Recorremos los simbolos siempre en orden alfabetico para producir
        # representantes deterministas independientes del orden del alfabeto.
        symbols: List[str] = sorted(self.dfa.alphabet)
        while queue:
            word, transformation = queue.popleft()
            for a in symbols:
                new_t = transformation.then(self._generators[a])
                new_word = word + a
                if self._add(new_t, new_word):
                    queue.append((new_word, new_t))

    # ------------------------------------------------------------------
    # Consultas estructurales
    # ------------------------------------------------------------------

    @property
    def order(self) -> int:
        """Cardinalidad del monoide |M(A)|."""
        return len(self.elements)

    @property
    def generators(self) -> Dict[str, Transformation]:
        """Diccionario de generadores: { a : f_a } para a in Sigma."""
        return dict(self._generators)

    def index_of(self, transformation: Transformation) -> int:
        """Indice de la transformacion en self.elements."""
        return self._index[transformation]

    def transformation_of(self, word: str) -> Transformation:
        """Devuelve f_w computando la composicion correspondiente."""
        current = self.identity
        for a in word:
            if a not in self._generators:
                raise ValueError(f"Simbolo fuera del alfabeto: {a!r}")
            current = current.then(self._generators[a])
        return current

    # ------------------------------------------------------------------
    # Tabla de Cayley
    # ------------------------------------------------------------------

    def cayley_table(self) -> List[List[int]]:
        """Tabla de Cayley del monoide.

        Devuelve una matriz table tal que table[i][j] es el indice de la
        transformacion resultante de aplicar primero elements[i] y luego
        elements[j], es decir, elements[i].then(elements[j]).
        """
        n = self.order
        table = [[0] * n for _ in range(n)]
        for i, f in enumerate(self.elements):
            for j, g in enumerate(self.elements):
                table[i][j] = self._index[f.then(g)]
        return table

    def pretty_cayley_table(self, labels: Optional[List[str]] = None) -> str:
        """Devuelve la tabla de Cayley formateada como texto."""
        n = self.order
        if labels is None:
            labels = [self._label(i) for i in range(n)]
        table = self.cayley_table()
        width = max(max(len(l) for l in labels), 3)
        header = " " * (width + 1) + "| " + " ".join(l.center(width) for l in labels)
        sep = "-" * (width + 1) + "+-" + "-" * (n * (width + 1) - 1)
        lines = [header, sep]
        for i in range(n):
            row = labels[i].ljust(width) + " | " + " ".join(
                labels[table[i][j]].center(width) for j in range(n)
            )
            lines.append(row)
        return "\n".join(lines)

    def _label(self, i: int) -> str:
        """Etiqueta legible para el i-esimo elemento.

        Se usa la palabra representante: 'e' para epsilon, las demas se
        muestran tal cual.
        """
        w = self.representatives[self.elements[i]]
        return "e" if w == "" else w

    def labels(self) -> List[str]:
        """Lista de etiquetas (palabras representantes) en orden."""
        return [self._label(i) for i in range(self.order)]

    # ------------------------------------------------------------------
    # Propiedades algebraicas
    # ------------------------------------------------------------------

    def has_identity(self) -> bool:
        """Verifica que la identidad pertenece al monoide.

        Es siempre True por construccion, pero util como autodiagnostico.
        """
        return self.identity in self._index

    def is_closed(self) -> bool:
        """Verifica explicitamente la cerradura del conjunto generado."""
        for f in self.elements:
            for g in self.elements:
                if f.then(g) not in self._index:
                    return False
        return True

    def is_associative(self) -> bool:
        """Verifica asociatividad sobre todos los triples.

        Es siempre True para composicion de funciones; se incluye como
        verificacion empirica para los DFAs pequenos usados en clase.
        """
        for f in self.elements:
            for g in self.elements:
                for h in self.elements:
                    if (f.then(g)).then(h) != f.then(g.then(h)):
                        return False
        return True

    def is_commutative(self) -> bool:
        """True si M(A) es un monoide conmutativo (es decir, abeliano)."""
        for i, f in enumerate(self.elements):
            for g in self.elements[i + 1 :]:
                if f.then(g) != g.then(f):
                    return False
        return True

    def is_group(self) -> bool:
        """True si todo elemento de M(A) tiene inverso bajo la composicion."""
        for f in self.elements:
            has_inverse = any(
                f.then(g) == self.identity and g.then(f) == self.identity
                for g in self.elements
            )
            if not has_inverse:
                return False
        return True

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Resumen textual del monoide para reportes."""
        lines = [
            f"Monoide de transicion M(A) de {self.dfa.name}",
            f"  |Q|        = {len(self.dfa.states)}",
            f"  |Sigma|    = {len(self.dfa.alphabet)}",
            f"  |M(A)|     = {self.order}",
            f"  Cota |Q|^|Q| = {len(self.dfa.states) ** len(self.dfa.states)}",
            f"  Conmutativo = {self.is_commutative()}",
            f"  Grupo       = {self.is_group()}",
        ]
        return "\n".join(lines)

    def __iter__(self) -> Iterable[Transformation]:
        return iter(self.elements)

    def __len__(self) -> int:
        return self.order


__all__ = ["TransitionMonoid"]
