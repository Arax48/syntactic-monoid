"""
backend.models.transformation
==============================

Modulo que define el objeto Transformation, una funcion total f : Q -> Q
sobre el conjunto finito de estados de un DFA.

Toda palabra w in Sigma* induce una transformacion

    f_w : Q -> Q, definida por f_w(q) = delta*(q, w),

y la composicion de funciones sobre Q forma un monoide cuya identidad es
la transformacion identidad id_Q(q) = q. La composicion se define como

    (f_v o f_u)(q) = f_v(f_u(q)),

de modo que f_{uv} = f_v o f_u (cuidado con el orden: aplicar primero u y
luego v corresponde a componer "v despues de u").

La clase Transformation es inmutable y hasheable, lo cual permite usarla
como clave en diccionarios y conjuntos al construir el monoide de
transicion mediante BFS (ver transition_monoid.py).

Extended in the new backend with:
    - is_bijective()   : True iff f is a permutation of Q
    - is_idempotent()  : True iff f o f = f
    - orbit(q)         : cyclic orbit {q, f(q), f²(q), ...}
    - fixed_points()   : set of states q such that f(q) = q
    - order()          : smallest n ≥ 1 such that fⁿ = identity (or None)
    - image_set()      : the image Im(f) = { f(q) : q ∈ Q }
    - kernel_partition(): partition of Q into fibers f⁻¹(r)
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Hashable, Iterable, List, Mapping, Set, Tuple, Optional


class Transformation:
    """Funcion total f : Q -> Q sobre un conjunto finito de estados Q.

    Representacion interna: una tupla ordenada de pares (q, f(q)).
    Es inmutable y hasheable.
    """

    __slots__ = ("_mapping", "_items")

    def __init__(self, mapping: Mapping[Hashable, Hashable]) -> None:
        if not mapping:
            raise ValueError("La transformacion no puede ser vacia.")
        items: Tuple[Tuple[Hashable, Hashable], ...] = tuple(
            sorted(mapping.items(), key=lambda kv: str(kv[0]))
        )
        self._items = items
        self._mapping: Dict[Hashable, Hashable] = dict(items)

    # ------------------------------------------------------------------
    # Construccion estandar
    # ------------------------------------------------------------------

    @classmethod
    def identity(cls, states: Iterable[Hashable]) -> "Transformation":
        """Transformacion identidad id_Q(q) = q."""
        return cls({q: q for q in states})

    # ------------------------------------------------------------------
    # API funcional
    # ------------------------------------------------------------------

    @property
    def domain(self) -> Tuple[Hashable, ...]:
        """Dominio de la transformacion ordenado lexicograficamente."""
        return tuple(q for q, _ in self._items)

    def apply(self, q: Hashable) -> Hashable:
        """Aplica la funcion a un estado q en su dominio."""
        if q not in self._mapping:
            raise KeyError(f"El estado {q!r} no esta en el dominio.")
        return self._mapping[q]

    __call__ = apply

    def items(self) -> Tuple[Tuple[Hashable, Hashable], ...]:
        """Pares ordenados (q, f(q))."""
        return self._items

    # ------------------------------------------------------------------
    # Composicion
    # ------------------------------------------------------------------

    def then(self, other: "Transformation") -> "Transformation":
        """Devuelve la composicion (other o self): primero self, luego other.

        Esto corresponde a leer la palabra de izquierda a derecha:
        si self = f_u y other = f_v entonces self.then(other) = f_{uv}.
        """
        if not isinstance(other, Transformation):
            raise TypeError("Solo se puede componer con otra Transformation.")
        if self.domain != other.domain:
            raise ValueError(
                "Las transformaciones deben tener el mismo dominio."
            )
        return Transformation({q: other.apply(self.apply(q)) for q in self.domain})

    def compose(self, other: "Transformation") -> "Transformation":
        """Composicion matematica clasica: (self o other)(q) = self(other(q)).

        Equivalente a other.then(self).
        """
        return other.then(self)

    def __matmul__(self, other: "Transformation") -> "Transformation":
        """Sintaxis self @ other equivalente a self.compose(other)."""
        return self.compose(other)

    # ------------------------------------------------------------------
    # Propiedades algebraicas (NUEVAS)
    # ------------------------------------------------------------------

    def is_bijective(self) -> bool:
        """True si f es una biyeccion (permutacion) de Q.

        Equivalentemente, True si f es invertible en el monoide de
        transformaciones, es decir, si existe g tal que f o g = g o f = id_Q.
        """
        values = [v for _, v in self._items]
        return len(set(values)) == len(values)

    def is_idempotent(self) -> bool:
        """True si f o f = f (f es idempotente).

        Los idempotentes son elementos "estables": aplicar la
        transformacion dos veces da el mismo resultado que aplicarla una vez.
        En un monoide finito, los idempotentes juegan un papel crucial
        en la estructura de Green.
        """
        return self.then(self) == self

    def fixed_points(self) -> Set[Hashable]:
        """Conjunto de puntos fijos: { q in Q : f(q) = q }.

        Los puntos fijos son los estados que la transformacion no mueve.
        """
        return {q for q, v in self._items if q == v}

    def orbit(self, q: Hashable) -> List[Hashable]:
        """Orbita ciclica de q bajo f: [q, f(q), f²(q), ...].

        Se detiene cuando se vuelve a visitar un estado (la orbita
        es finita porque Q es finito).
        """
        if q not in self._mapping:
            raise KeyError(f"El estado {q!r} no esta en el dominio.")
        visited: List[Hashable] = []
        seen: Set[Hashable] = set()
        current = q
        while current not in seen:
            seen.add(current)
            visited.append(current)
            current = self.apply(current)
        return visited

    def image_set(self) -> FrozenSet[Hashable]:
        """Imagen de f: Im(f) = { f(q) : q in Q }.

        |Im(f)| = |Q| si y solo si f es biyectiva.
        """
        return frozenset(v for _, v in self._items)

    def kernel_partition(self) -> List[FrozenSet[Hashable]]:
        """Particion del dominio en fibras f^{-1}(r).

        Cada bloque de la particion es el conjunto de estados que
        mapean al mismo valor bajo f. Esto es el nucleo de f como
        relacion de equivalencia.
        """
        fibers: Dict[Hashable, Set[Hashable]] = {}
        for q, v in self._items:
            fibers.setdefault(v, set()).add(q)
        return [frozenset(s) for s in fibers.values()]

    def order(self) -> Optional[int]:
        """Orden de f en el monoide: menor n >= 1 tal que f^n = id_Q.

        Devuelve None si f no es invertible (no tiene orden finito
        en el sentido de grupo, aunque siempre tiene indice+periodo
        finito en un monoide finito).
        """
        if not self.is_bijective():
            return None
        identity = Transformation.identity(self.domain)
        current = self
        for n in range(1, len(self._items) + 1):
            if current == identity:
                return n
            current = current.then(self)
        return None  # Should not happen for bijective transformations on finite sets

    def cycle_structure(self) -> List[int]:
        """Estructura de ciclos de la transformacion (solo si es biyectiva).

        Devuelve una lista ordenada con las longitudes de los ciclos.
        Por ejemplo, una permutacion (1 2)(3) tiene estructura [1, 2].

        Para transformaciones no biyectivas, devuelve la estructura
        de la parte ciclica (los ciclos en el grafo funcional).
        """
        visited: Set[Hashable] = set()
        cycles: List[int] = []
        for q in self.domain:
            if q in visited:
                continue
            # Follow the orbit until we find a cycle
            path: List[Hashable] = []
            current = q
            while current not in visited:
                visited.add(current)
                path.append(current)
                current = self.apply(current)
            # If current is in path, we found a cycle
            if current in path:
                cycle_start = path.index(current)
                cycles.append(len(path) - cycle_start)
        cycles.sort()
        return cycles

    # ------------------------------------------------------------------
    # Igualdad y hash
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transformation):
            return NotImplemented
        return self._items == other._items

    def __hash__(self) -> int:
        return hash(self._items)

    # ------------------------------------------------------------------
    # Representacion legible
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        pairs = ", ".join(f"{q}->{v}" for q, v in self._items)
        return "[" + pairs + "]"

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Transformation({dict(self._items)!r})"

    def two_line(self) -> str:
        """Notacion clasica de dos lineas usada en teoria de monoides:

            ( q1  q2  q3 )
            ( f1  f2  f3 )
        """
        keys = [str(q) for q, _ in self._items]
        vals = [str(v) for _, v in self._items]
        widths = [max(len(k), len(v)) for k, v in zip(keys, vals)]
        top = " ".join(k.center(w) for k, w in zip(keys, widths))
        bot = " ".join(v.center(w) for v, w in zip(vals, widths))
        return f"( {top} )\n( {bot} )"


__all__ = ["Transformation"]
