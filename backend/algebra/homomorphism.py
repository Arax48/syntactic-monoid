"""
backend.algebra.homomorphism
=============================

Modulo de algebra: homomorfismo natural, nucleo y clases de equivalencia.

Sea A = (Q, Sigma, delta, q0, F) un AFD y sea M(A) el monoide de transicion
construido en transition_monoid.py. Se define el homomorfismo natural

    phi : Sigma* -> M(A),    phi(w) = f_w,

que satisface phi(uv) = phi(u) o phi(v) (cuidado con el orden: la
composicion "o" aqui es "primero f_u y luego f_v" porque la palabra se
lee de izquierda a derecha).

El nucleo de phi es la relacion de congruencia sobre Sigma* dada por

    u ~ v   sii   phi(u) = phi(v)   sii   f_u = f_v.

Esta es una congruencia de monoide (compatible con la concatenacion),
y el cociente Sigma*/~ es isomorfo a Im(phi) por el Primer Teorema del
Isomorfismo para monoides:

    Sigma* / Ker(phi)  ~=  Im(phi)  subset  M(A).

Como phi es sobreyectivo por construccion (todo elemento de M(A) es
algun f_w), se tiene de hecho Sigma*/Ker(phi) ~= M(A).

Este modulo expone la clase Homomorphism con metodos para evaluar phi,
obtener clases de equivalencia, enumerar el cociente y verificar el
isomorfismo numericamente.
"""

from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, List, Tuple

from backend.models.afd import AFD
from backend.models.transformation import Transformation
from backend.algebra.transition_monoid import TransitionMonoid


# Cota de profundidad de BFS suficiente para visitar todo M(A).
# Justificacion: en el BFS de TransitionMonoid, cada nivel anade al menos
# un elemento nuevo hasta agotar M(A); por lo tanto, la longitud del
# representante minimo de cualquier f in M(A) es a lo sumo |M(A)| - 1.
def _bfs_depth_bound(monoid_order: int) -> int:
    return max(monoid_order, 1)


class Homomorphism:
    """Homomorfismo natural phi : Sigma* -> M(A), phi(w) = f_w.

    Atributos
    ---------
    dfa : AFD
    monoid : TransitionMonoid
    """

    def __init__(self, dfa: AFD, monoid: TransitionMonoid | None = None) -> None:
        self.dfa = dfa
        self.monoid = monoid if monoid is not None else TransitionMonoid(dfa)

    # ------------------------------------------------------------------
    # phi
    # ------------------------------------------------------------------

    def image(self, word: str) -> Transformation:
        """phi(w) = f_w."""
        return self.monoid.transformation_of(word)

    def equivalent(self, u: str, v: str) -> bool:
        """True si u ~ v en Ker(phi), es decir, si phi(u) = phi(v)."""
        return self.image(u) == self.image(v)

    # ------------------------------------------------------------------
    # Generador de Sigma^{<=n}
    # ------------------------------------------------------------------

    def words_up_to(self, length: int) -> Iterable[str]:
        """Genera todas las palabras de Sigma* de longitud <= length."""
        sigma = sorted(self.dfa.alphabet)
        yield ""
        for n in range(1, length + 1):
            for tup in product(sigma, repeat=n):
                yield "".join(tup)

    # ------------------------------------------------------------------
    # Clases de equivalencia y nucleo
    # ------------------------------------------------------------------

    def equivalence_class(self, word: str, max_length: int = 4) -> List[str]:
        """Devuelve representantes (de longitud <= max_length) de [w].

        Aviso: Sigma* es infinito, por lo que las clases son infinitas;
        este metodo devuelve TODAS las palabras de longitud <= max_length
        que son equivalentes a w. Es util para visualizacion y reportes.
        """
        target = self.image(word)
        return [w for w in self.words_up_to(max_length) if self.image(w) == target]

    def kernel(self, max_length: int = 4) -> Dict[Transformation, List[str]]:
        """Aproximacion finita de Ker(phi).

        Agrupa las palabras de Sigma^{<=max_length} segun su imagen.
        El conjunto de claves coincide exactamente con M(A) cuando
        max_length es suficientemente grande (a lo sumo |M(A)|), porque
        BFS sobre Sigma* visita toda transformacion en a lo sumo |M(A)|
        pasos.
        """
        classes: Dict[Transformation, List[str]] = {f: [] for f in self.monoid.elements}
        for w in self.words_up_to(max_length):
            classes[self.image(w)].append(w)
        return classes

    def quotient(self, max_length: int = 4) -> List[Tuple[str, Transformation, List[str]]]:
        """Lista de elementos del cociente Sigma*/Ker(phi) (truncado).

        Cada tripla es (representante minimo, transformacion, palabras de
        longitud <= max_length en la clase).
        """
        cls = self.kernel(max_length)
        out: List[Tuple[str, Transformation, List[str]]] = []
        for f in self.monoid.elements:
            rep = self.monoid.representatives[f]
            out.append((rep, f, cls[f]))
        return out

    # ------------------------------------------------------------------
    # Verificacion empirica de propiedades
    # ------------------------------------------------------------------

    def verify_homomorphism(self, max_length: int = 3) -> bool:
        """Verifica numericamente que phi(uv) = phi(u).then(phi(v)).

        Recuerde que `.then` es la composicion "primero phi(u), luego
        phi(v)"; es decir, en (M(A), star) con star(f,g) := g o f,
        comprobamos phi(uv) = phi(u) star phi(v).
        """
        words = list(self.words_up_to(max_length))
        for u in words:
            phi_u = self.image(u)
            for v in words:
                if self.image(u + v) != phi_u.then(self.image(v)):
                    return False
        # Verificamos tambien phi(epsilon) = id_Q (neutro del monoide).
        return self.image("") == self.monoid.identity

    def verify_first_isomorphism(self, max_length: int | None = None) -> bool:
        """Verifica numericamente el Primer Teorema del Isomorfismo:

            Sigma* / Ker(phi)  ~=  Im(phi)  =  M(A).

        La comprobacion realmente ejecutada es la siguiente:

            (a) Cada transformacion de M(A) es alcanzada por alguna
                palabra w in Sigma* con |w| <= max_length (verifica que
                phi es sobreyectivo sobre M(A) y que la BFS no es
                degenerada).
            (b) Toda palabra de longitud <= max_length se asigna
                exactamente a una transformacion (siempre cierto, pues
                phi es funcion), y palabras asociadas a transformaciones
                distintas son no-equivalentes (verifica inyectividad de
                la asignacion clase -> transformacion).

        Si max_length es None se usa max_length = |M(A)|, que es
        suficiente por la cota de profundidad de la BFS.
        """
        if max_length is None:
            max_length = _bfs_depth_bound(self.monoid.order)
        cls = self.kernel(max_length)
        # (a) Sobreyectividad: toda transformacion debe tener algun
        #     representante en la truncacion.
        nonempty = sum(1 for words in cls.values() if words)
        if nonempty != self.monoid.order:
            return False
        # (b) Coherencia: cada palabra de su clase debe efectivamente
        #     mapear, via phi, a la transformacion etiqueta.
        for f, words in cls.items():
            for w in words:
                if self.image(w) != f:
                    return False
        return True

    # ------------------------------------------------------------------
    # Reportes textuales
    # ------------------------------------------------------------------

    def kernel_report(self, max_length: int = 3) -> str:
        """Reporte legible de las clases de equivalencia hasta cierta longitud."""
        cls = self.kernel(max_length)
        lines = [
            f"Nucleo (truncado a palabras de longitud <= {max_length}):",
            f"  Numero de clases distintas: {sum(1 for v in cls.values() if v)}",
            f"  |M(A)| = {self.monoid.order}",
            "",
        ]
        for f in self.monoid.elements:
            rep = self.monoid.representatives[f]
            label = "e" if rep == "" else rep
            words = cls[f]
            shown = ", ".join("e" if w == "" else w for w in words)
            lines.append(f"  [{label}]_~  =  {{ {shown} }}")
            lines.append(f"        f = {f}")
        return "\n".join(lines)


__all__ = ["Homomorphism"]
