"""Pruebas para transition_monoid.py."""

from __future__ import annotations

from itertools import product

from dfa import DFA
from transformation import Transformation
from transition_monoid import TransitionMonoid


# ----------------------------------------------------------------------
# Tamanios esperados de los ejemplos canonicos
# ----------------------------------------------------------------------

def test_paridad_monoide_tiene_dos_elementos(parity_dfa: DFA) -> None:
    M = TransitionMonoid(parity_dfa)
    # En el DFA de paridad solo hay dos transformaciones: identidad y
    # swap. Esto es Z/2Z como monoide.
    assert M.order == 2
    assert M.is_group()
    assert M.is_commutative()


def test_mod3_monoide_tiene_tres_elementos(mod3_dfa: DFA) -> None:
    M = TransitionMonoid(mod3_dfa)
    # Z/3Z, exactamente 3 transformaciones.
    assert M.order == 3
    assert M.is_group()
    assert M.is_commutative()


def test_ends_with_01_monoide_no_es_grupo(ends_01_dfa: DFA) -> None:
    M = TransitionMonoid(ends_01_dfa)
    # Este DFA tiene "estados absorbentes" desde el punto de vista de
    # algunas transformaciones, por lo que M(A) no es un grupo.
    assert M.order > 0
    assert M.has_identity()
    assert not M.is_group()


# ----------------------------------------------------------------------
# Propiedades algebraicas universales
# ----------------------------------------------------------------------

def test_identidad_pertenece_y_es_neutro(parity_dfa: DFA) -> None:
    M = TransitionMonoid(parity_dfa)
    assert M.has_identity()
    for f in M.elements:
        assert M.identity.then(f) == f
        assert f.then(M.identity) == f


def test_cerradura(parity_dfa: DFA, mod3_dfa: DFA, ends_01_dfa: DFA) -> None:
    for dfa in (parity_dfa, mod3_dfa, ends_01_dfa):
        M = TransitionMonoid(dfa)
        assert M.is_closed()


def test_asociatividad(parity_dfa: DFA, mod3_dfa: DFA, ends_01_dfa: DFA) -> None:
    for dfa in (parity_dfa, mod3_dfa, ends_01_dfa):
        M = TransitionMonoid(dfa)
        assert M.is_associative()


def test_cota_superior_QexpQ(parity_dfa: DFA, mod3_dfa: DFA, ends_01_dfa: DFA) -> None:
    # |M(A)| <= |Q|^|Q|.
    for dfa in (parity_dfa, mod3_dfa, ends_01_dfa):
        M = TransitionMonoid(dfa)
        n = len(dfa.states)
        assert M.order <= n ** n


# ----------------------------------------------------------------------
# Tabla de Cayley
# ----------------------------------------------------------------------

def test_cayley_table_dimension(mod3_dfa: DFA) -> None:
    M = TransitionMonoid(mod3_dfa)
    table = M.cayley_table()
    n = M.order
    assert len(table) == n
    assert all(len(row) == n for row in table)


def test_cayley_table_consistente_con_then(mod3_dfa: DFA) -> None:
    M = TransitionMonoid(mod3_dfa)
    table = M.cayley_table()
    for i, f in enumerate(M.elements):
        for j, g in enumerate(M.elements):
            esperado = M.index_of(f.then(g))
            assert table[i][j] == esperado


def test_cayley_table_paridad_es_z2(parity_dfa: DFA) -> None:
    M = TransitionMonoid(parity_dfa)
    # En Z/2 la tabla es [[0,1],[1,0]].
    table = M.cayley_table()
    # identidad debe estar en posicion 0
    assert M.index_of(M.identity) == 0
    assert table[0] == [0, 1]
    assert table[1] == [1, 0]


# ----------------------------------------------------------------------
# Representantes minimos
# ----------------------------------------------------------------------

def test_palabra_representante_minima(parity_dfa: DFA) -> None:
    M = TransitionMonoid(parity_dfa)
    # En el DFA de paridad:
    #   identidad: representada por epsilon (longitud 0)
    #   swap     : representada por "1" (longitud 1)
    longitudes = sorted(len(M.representatives[f]) for f in M.elements)
    assert longitudes == [0, 1]


def test_transformacion_of_concuerda_con_dfa(mod3_dfa: DFA) -> None:
    M = TransitionMonoid(mod3_dfa)
    for w in ("", "0", "1", "10", "11", "101", "111"):
        esperado = Transformation(mod3_dfa.transformation(w))
        assert M.transformation_of(w) == esperado


# ----------------------------------------------------------------------
# Casos extremos
# ----------------------------------------------------------------------

def test_dfa_de_un_estado_y_alfabeto_unitario() -> None:
    """Caso degenerado: |Q| = 1, |Sigma| = 1.

    Hay una unica funcion Q -> Q (la identidad), de modo que
    M(A) = {id_Q} y todas las palabras son equivalentes entre si.
    """
    dfa = DFA(
        states={"q"},
        alphabet={"a"},
        transitions={"q": {"a": "q"}},
        start="q",
        accepting={"q"},
        name="trivial",
    )
    M = TransitionMonoid(dfa)
    assert M.order == 1
    assert M.is_group()
    assert M.is_commutative()
    assert M.cayley_table() == [[0]]


def test_dfa_alfabeto_unitario_dos_estados() -> None:
    """|Q| = 2, |Sigma| = {a} con a actuando como permutacion.

    M(A) debe ser ciclico de orden 2 ~= Z/2Z.
    """
    dfa = DFA(
        states={"p", "q"},
        alphabet={"a"},
        transitions={"p": {"a": "q"}, "q": {"a": "p"}},
        start="p",
        accepting={"p"},
        name="swap1",
    )
    M = TransitionMonoid(dfa)
    assert M.order == 2
    assert M.is_group()
    # |M(A)|^2 lecturas: a, aa donde aa = identidad.
    assert M.transformation_of("aa") == M.identity


def test_palabras_representantes_son_shortlex(parity_dfa: DFA) -> None:
    """Verifica que los representantes son shortlex (mas cortos primero,
    desempate lexicografico) gracias al orden BFS + simbolos ordenados.
    """
    M = TransitionMonoid(parity_dfa)
    reps = sorted(
        (len(M.representatives[f]), M.representatives[f]) for f in M.elements
    )
    # Para paridad: ("", id), ("1", swap)
    assert [r for _, r in reps] == ["", "1"]


def test_orden_de_columnas_cayley_es_consistente(mod3_dfa: DFA) -> None:
    """La fila i de la tabla es la imagen de elements[i] bajo `then`."""
    M = TransitionMonoid(mod3_dfa)
    table = M.cayley_table()
    for i, f in enumerate(M.elements):
        for j, g in enumerate(M.elements):
            assert M.elements[table[i][j]] == f.then(g)
