"""
transformation.py
=================

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
"""

from __future__ import annotations

from typing import Dict, Hashable, Iterable, Mapping, Tuple


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
