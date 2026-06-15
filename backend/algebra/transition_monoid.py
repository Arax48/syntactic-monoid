"""
backend.algebra.transition_monoid
==================================

Construccion explicita del MONOIDE DE TRANSICION M(A) asociado a un AFD.

Definicion
----------
Sea A = (Q, Sigma, delta, q0, F) un AFD. Para cada w in Sigma* definimos
la transformacion inducida

    f_w : Q -> Q,    f_w(q) = delta*(q, w).

El conjunto

    M(A) = { f_w : w in Sigma* }

es cerrado bajo la composicion de funciones (puesto que f_{uv} = f_v o f_u),
contiene a la identidad f_epsilon = id_Q y la composicion de funciones es
asociativa. Por lo tanto (M(A), o, id_Q) es un monoide finito (los unicos
elementos posibles son funciones Q -> Q y hay solo |Q|^|Q| de estas).

Extended in the new backend with:
    - idempotents()          : list of idempotent elements e² = e
    - invertible_elements()  : the group of units U(M)
    - is_aperiodic()         : True if M(A) has no non-trivial subgroups
    - center()               : the center Z(M) = {x : xm = mx for all m}
    - right_cayley_graph()   : adjacency list for the Cayley graph
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, List, Optional, Set, Tuple

from backend.models.afd import AFD
from backend.models.transformation import Transformation


class TransitionMonoid:
    """Monoide de transicion M(A) de un AFD.

    Atributos publicos
    ------------------
    dfa : AFD
        AFD fuente.
    elements : list[Transformation]
        Lista de las transformaciones del monoide (sin repeticiones).
    representatives : dict[Transformation, str]
        Para cada transformacion, una palabra w de longitud minima tal
        que f_w es esa transformacion.
    identity : Transformation
        Elemento identidad del monoide (igual a f_epsilon = id_Q).
    """

    def __init__(self, dfa: AFD) -> None:
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

        Se usa la palabra representante: 'e' para λ, las demas se
        muestran tal cual.
        """
        w = self.representatives[self.elements[i]]
        return "e" if w == "" else w

    def labels(self) -> List[str]:
        """Lista de etiquetas (palabras representantes) en orden."""
        return [self._label(i) for i in range(self.order)]

    # ------------------------------------------------------------------
    # Propiedades algebraicas (originales)
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
        verificacion empirica para los AFDs pequenos usados en clase.
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
            for g in self.elements[i + 1:]:
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
    # Propiedades algebraicas (NUEVAS)
    # ------------------------------------------------------------------

    def idempotents(self) -> List[Transformation]:
        """Lista de elementos idempotentes: { e in M(A) : e² = e }.

        Los idempotentes juegan un papel central en la teoria de
        semigrupos finitos y en la estructura de Green de M(A).
        La identidad siempre es idempotente.
        """
        return [f for f in self.elements if f.is_idempotent()]

    def invertible_elements(self) -> List[Transformation]:
        """Grupo de unidades U(M): elementos con inverso bilateral.

        U(M) es siempre un subgrupo de M(A). Si M(A) es un grupo,
        entonces U(M) = M(A).
        """
        units: List[Transformation] = []
        for f in self.elements:
            for g in self.elements:
                if f.then(g) == self.identity and g.then(f) == self.identity:
                    units.append(f)
                    break
        return units

    def inverse_of(self, f: Transformation) -> Optional[Transformation]:
        """Devuelve el inverso de f si existe, None en caso contrario."""
        for g in self.elements:
            if f.then(g) == self.identity and g.then(f) == self.identity:
                return g
        return None

    def is_aperiodic(self) -> bool:
        """True si M(A) es aperiodico.

        Un monoide finito es aperiodico si para todo elemento x existe
        un n tal que x^{n+1} = x^n. Equivalentemente, todos los subgrupos
        de M(A) son triviales (solo contienen la identidad).

        Teorema de Schutzenberger: L es reconocido por un monoide aperiodico
        si y solo si L es una lengua libre de estrellas (star-free).
        """
        for f in self.elements:
            # Compute powers until stabilization
            current = f
            prev = None
            for _ in range(len(self.elements) + 1):
                next_power = current.then(f)
                if next_power == current:
                    break
                prev = current
                current = next_power
            else:
                # Did not stabilize within |M(A)| steps
                return False
        return True

    def center(self) -> List[Transformation]:
        """Centro del monoide Z(M) = { x in M : xm = mx para todo m in M }.

        El centro es el conjunto de elementos que conmutan con todos
        los demas. Siempre contiene la identidad.
        """
        center_elements: List[Transformation] = []
        for f in self.elements:
            if all(f.then(g) == g.then(f) for g in self.elements):
                center_elements.append(f)
        return center_elements

    def right_cayley_graph(self) -> Dict[int, Dict[str, int]]:
        """Grafo de Cayley derecho del monoide.

        Para cada elemento m y cada generador a, hay una arista
        m --a--> m·a. El grafo resultante se devuelve como un
        diccionario { indice_m : { simbolo : indice_destino } }.

        El grafo de Cayley es una herramienta fundamental para
        visualizar la estructura del monoide.
        """
        graph: Dict[int, Dict[str, int]] = {}
        for i, f in enumerate(self.elements):
            graph[i] = {}
            for a in sorted(self.dfa.alphabet):
                product = f.then(self._generators[a])
                graph[i][a] = self._index[product]
        return graph

    def element_orders(self) -> Dict[Transformation, Optional[int]]:
        """Orden de cada elemento del monoide.

        Para elementos invertibles, el orden es el menor n >= 1 tal que
        f^n = identidad. Para elementos no invertibles, devuelve None.
        """
        return {f: f.order() for f in self.elements}

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
            f"  Aperiodico  = {self.is_aperiodic()}",
            f"  |Idempotentes| = {len(self.idempotents())}",
            f"  |Unidades|     = {len(self.invertible_elements())}",
            f"  |Centro|       = {len(self.center())}",
        ]
        return "\n".join(lines)

    def __iter__(self) -> Iterable[Transformation]:
        return iter(self.elements)

    def __len__(self) -> int:
        return self.order


__all__ = ["TransitionMonoid"]
