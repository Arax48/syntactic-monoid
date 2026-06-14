"""
backend.algebra.group_analysis
==============================

Analisis algebraico de M(A) orientado a la deteccion de estructura de
grupo y a las conexiones con el curso de Matematica Discreta II.

Sobre TransitionMonoid (que ya provee is_group, idempotents,
invertible_elements, is_aperiodic, center, element_orders, ...) este
modulo construye una capa de mas alto nivel:

    * Detecta si M(A) es un grupo y, en caso afirmativo, intenta
      identificarlo con un grupo clasico:
        - {e} (grupo trivial)
        - ℤ/pℤ para p primo (unico grupo de orden p)
        - ℤ/nℤ ciclico de orden compuesto
        - V₄ (Klein) cuando es abeliano de orden 4 NO ciclico
        - S₃ cuando es no abeliano de orden 6
    * Encuentra un generador ciclico (representante minimo de palabra)
      cuando M(A) es ciclico.
    * Calcula el orden de cada elemento y su clase.
    * Expone numero de idempotentes, unidades y tamano del centro.

Conexion pedagogica con Discrete Math II:
    cuando M(A) es ℤ/nℤ, las clases del nucleo de φ son literalmente
    las clases de equivalencia modulo n del numero de simbolos
    "contables" de la palabra. Esto es ARITMETICA MODULAR vista a
    traves del monoide de transicion de un automata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.algebra.transition_monoid import TransitionMonoid
from backend.models.transformation import Transformation


# ----------------------------------------------------------------------
# Resultado estructurado
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class GroupAnalysis:
    """Descripcion algebraica de M(A).

    Atributos
    ---------
    is_group : bool
        True si M(A) es un grupo (todo elemento tiene inverso).
    order : int
        |M(A)|.
    is_abelian : bool
        True si la operacion es conmutativa.
    is_cyclic : bool
        True si M(A) es ciclico (existe un generador unico).
    is_aperiodic : bool
        True si todos los subgrupos de M(A) son triviales (Schutzenberger:
        equivalente a que L sea star-free).
    cyclic_generator : Transformation | None
        Si M(A) es ciclico, un generador concreto (transformacion).
        None en otro caso.
    cyclic_generator_word : str | None
        Representante minimo (la palabra mas corta sobre Sigma*) del
        generador ciclico.
    element_orders : dict[Transformation, int | None]
        Orden de cada elemento (None si no es invertible).
    isomorphic_to : str | None
        Etiqueta humana del grupo, e.g. "ℤ/3ℤ", "Klein V₄", "S₃".
        None cuando M(A) no es un grupo.
    num_idempotents : int
    invertible_count : int
    center_size : int
    """

    is_group: bool
    order: int
    is_abelian: bool
    is_cyclic: bool
    is_aperiodic: bool
    cyclic_generator: Optional[Transformation]
    cyclic_generator_word: Optional[str]
    element_orders: Dict[Transformation, Optional[int]] = field(default_factory=dict)
    isomorphic_to: Optional[str] = None
    num_idempotents: int = 0
    invertible_count: int = 0
    center_size: int = 0


# ----------------------------------------------------------------------
# Analisis
# ----------------------------------------------------------------------

def analyze(monoid: TransitionMonoid) -> GroupAnalysis:
    """Construye un GroupAnalysis a partir del monoide de transicion."""
    is_group = monoid.is_group()
    is_abelian = monoid.is_commutative()
    is_aperiodic = monoid.is_aperiodic()
    order = monoid.order
    orders = monoid.element_orders()

    # ¿Es ciclico? Existe un elemento de orden |M|.
    cyclic_gen: Optional[Transformation] = None
    if is_group:
        for f, n in orders.items():
            if n == order:
                cyclic_gen = f
                break
    is_cyclic = cyclic_gen is not None

    cyclic_word = (
        monoid.representatives[cyclic_gen] if cyclic_gen is not None else None
    )

    iso = (
        _identify_group(order, is_abelian, is_cyclic, orders)
        if is_group
        else None
    )

    return GroupAnalysis(
        is_group=is_group,
        order=order,
        is_abelian=is_abelian,
        is_cyclic=is_cyclic,
        is_aperiodic=is_aperiodic,
        cyclic_generator=cyclic_gen,
        cyclic_generator_word=cyclic_word,
        element_orders=orders,
        isomorphic_to=iso,
        num_idempotents=len(monoid.idempotents()),
        invertible_count=len(monoid.invertible_elements()),
        center_size=len(monoid.center()),
    )


# ----------------------------------------------------------------------
# Identificacion de grupos clasicos
# ----------------------------------------------------------------------

def _identify_group(
    order: int,
    is_abelian: bool,
    is_cyclic: bool,
    orders: Dict[Transformation, Optional[int]],
) -> str:
    """Devuelve la etiqueta humana del grupo segun orden y estructura.

    Se cubren con detalle los casos de orden hasta 8, suficientes para
    los ejemplos del curso (paridad → ℤ/2ℤ, mod 3 → ℤ/3ℤ, etc.). Casos
    no cubiertos se reportan de forma descriptiva.
    """
    if order == 1:
        return "{e} (grupo trivial)"

    if _is_prime(order):
        # Teorema clasico: unico grupo de orden p es ℤ/pℤ.
        return f"ℤ/{order}ℤ"

    if is_cyclic:
        # Por estructura de grupos abelianos finitos, si es ciclico de
        # orden n entonces es exactamente ℤ/nℤ.
        return f"ℤ/{order}ℤ (ciclico)"

    if is_abelian:
        # Abeliano no ciclico. Para orden 4 es V₄ (Klein) salvo
        # isomorfismo (los unicos grupos de orden 4 son ℤ/4ℤ y V₄).
        if order == 4:
            return "Klein V₄ ≅ ℤ/2ℤ × ℤ/2ℤ"
        # Para ordenes superiores no abeliano-no-ciclicos requiere mas
        # estructura (factores invariantes). Se reporta de forma generica.
        return f"grupo abeliano no ciclico de orden {order}"

    # No abeliano.
    if order == 6:
        # Los unicos grupos de orden 6 son ℤ/6ℤ (ciclico, abeliano) y S₃.
        return "S₃ (grupo simetrico)"
    if order == 8:
        # Grupos de orden 8 no abelianos: D₄ (diedrico) y Q₈ (cuaterniones).
        # D₄ tiene un elemento de orden 4; Q₈ tiene un unico elemento de
        # orden 2.
        elems_orden_2 = sum(1 for n in orders.values() if n == 2)
        if elems_orden_2 == 1:
            return "Q₈ (cuaterniones)"
        return "D₄ (grupo diedrico)"

    return f"grupo no abeliano de orden {order}"


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


__all__ = ["GroupAnalysis", "analyze"]
