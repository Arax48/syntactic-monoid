"""Pruebas para backend.algebra.group_analysis."""

from __future__ import annotations

import pytest

from backend.algebra import TransitionMonoid, analyze
from backend.models import AFD


# ----------------------------------------------------------------------
# Ejemplos canonicos
# ----------------------------------------------------------------------

def test_paridad_es_Z2(parity_afd: AFD) -> None:
    monoid = TransitionMonoid(parity_afd)
    info = analyze(monoid)
    assert info.is_group
    assert info.order == 2
    assert info.is_abelian
    assert info.is_cyclic
    assert info.isomorphic_to == "ℤ/2ℤ"
    assert info.cyclic_generator_word == "1"


def test_mod3_es_Z3(mod3_afd: AFD) -> None:
    monoid = TransitionMonoid(mod3_afd)
    info = analyze(monoid)
    assert info.is_group
    assert info.order == 3
    assert info.is_abelian
    assert info.is_cyclic
    assert info.isomorphic_to == "ℤ/3ℤ"
    assert info.cyclic_generator_word == "1"


def test_termina_en_01_no_es_grupo(ends_01_afd: AFD) -> None:
    monoid = TransitionMonoid(ends_01_afd)
    info = analyze(monoid)
    assert not info.is_group
    assert info.isomorphic_to is None
    # Caracterizacion algebraica: M(A) es aperiodico ⟺ L es star-free
    # (Schutzenberger). El lenguaje "termina en 01" es star-free.
    assert info.is_aperiodic
    # No es ciclico porque no es grupo.
    assert not info.is_cyclic
    assert info.cyclic_generator is None


# ----------------------------------------------------------------------
# Identificacion de grupos
# ----------------------------------------------------------------------

def test_grupo_trivial_se_identifica() -> None:
    """AFD de un solo estado: monoide trivial {e}."""
    dfa = AFD(
        states={"q"},
        alphabet={"a"},
        transitions={"q": {"a": "q"}},
        start="q",
        accepting={"q"},
        name="trivial",
    )
    info = analyze(TransitionMonoid(dfa))
    assert info.is_group
    assert info.order == 1
    assert info.isomorphic_to == "{e} (grupo trivial)"
    assert info.is_cyclic   # un grupo de orden 1 es trivialmente ciclico
    assert info.is_aperiodic   # ningun subgrupo no-trivial


def test_klein_V4_via_dfa_de_estados_pares_de_dos_simbolos() -> None:
    """AFD sobre {a, b} cuyo monoide es V₄ = ℤ/2ℤ × ℤ/2ℤ.

    Estados (par_a, par_b). a permuta par_a; b permuta par_b.
    Las transformaciones son: id, swap_a, swap_b, swap_ambos.
    """
    dfa = AFD(
        states={"00", "10", "01", "11"},
        alphabet={"a", "b"},
        transitions={
            "00": {"a": "10", "b": "01"},
            "10": {"a": "00", "b": "11"},
            "01": {"a": "11", "b": "00"},
            "11": {"a": "01", "b": "10"},
        },
        start="00",
        accepting={"00"},
        name="V4",
    )
    info = analyze(TransitionMonoid(dfa))
    assert info.is_group
    assert info.order == 4
    assert info.is_abelian
    assert not info.is_cyclic   # V₄ no es ciclico
    assert "Klein" in info.isomorphic_to


def test_grupo_ciclico_de_orden_4_via_alfabeto_unitario() -> None:
    """AFD con un simbolo `a` que rota 4 estados: monoide ciclico ℤ/4ℤ."""
    dfa = AFD(
        states={"s0", "s1", "s2", "s3"},
        alphabet={"a"},
        transitions={
            "s0": {"a": "s1"},
            "s1": {"a": "s2"},
            "s2": {"a": "s3"},
            "s3": {"a": "s0"},
        },
        start="s0",
        accepting={"s0"},
        name="Z4",
    )
    info = analyze(TransitionMonoid(dfa))
    assert info.is_group
    assert info.order == 4
    assert info.is_abelian
    assert info.is_cyclic
    assert info.cyclic_generator_word == "a"
    assert info.isomorphic_to == "ℤ/4ℤ (ciclico)"


# ----------------------------------------------------------------------
# Propiedades secundarias
# ----------------------------------------------------------------------

def test_order_de_elementos_es_consistente(parity_afd: AFD) -> None:
    monoid = TransitionMonoid(parity_afd)
    info = analyze(monoid)
    # En Z/2: identidad tiene orden 1, swap tiene orden 2.
    valores = sorted(o for o in info.element_orders.values() if o is not None)
    assert valores == [1, 2]


def test_centro_de_grupo_abeliano_es_todo_el_grupo(mod3_afd: AFD) -> None:
    info = analyze(TransitionMonoid(mod3_afd))
    assert info.center_size == info.order


def test_aperiodicidad_en_monoide_no_grupo(ends_01_afd: AFD) -> None:
    info = analyze(TransitionMonoid(ends_01_afd))
    # M(A) tiene 5 elementos, no es grupo, pero es aperiodico
    # (todos los subgrupos triviales).
    assert info.order == 5
    assert info.is_aperiodic
    assert not info.is_group
