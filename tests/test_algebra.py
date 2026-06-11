"""Pruebas para algebra.py (homomorfismo, nucleo, isomorfismo)."""

from __future__ import annotations

from itertools import product

from dfa import DFA
from algebra import Homomorphism
from transition_monoid import TransitionMonoid


# ----------------------------------------------------------------------
# phi(uv) = phi(u).then(phi(v))
# ----------------------------------------------------------------------

def test_phi_es_homomorfismo_paridad(parity_dfa: DFA) -> None:
    hom = Homomorphism(parity_dfa)
    assert hom.verify_homomorphism(max_length=4)


def test_phi_es_homomorfismo_mod3(mod3_dfa: DFA) -> None:
    hom = Homomorphism(mod3_dfa)
    assert hom.verify_homomorphism(max_length=4)


def test_phi_es_homomorfismo_ends01(ends_01_dfa: DFA) -> None:
    hom = Homomorphism(ends_01_dfa)
    assert hom.verify_homomorphism(max_length=4)


# ----------------------------------------------------------------------
# Equivalencias entre palabras
# ----------------------------------------------------------------------

def test_equivalentes_en_paridad(parity_dfa: DFA) -> None:
    hom = Homomorphism(parity_dfa)
    # epsilon, "00", "11" inducen la identidad
    assert hom.equivalent("", "00")
    assert hom.equivalent("", "11")
    assert hom.equivalent("00", "11")
    assert hom.equivalent("1", "10")
    assert not hom.equivalent("1", "11")


def test_equivalentes_en_mod3(mod3_dfa: DFA) -> None:
    hom = Homomorphism(mod3_dfa)
    # En Z/3, dos palabras son equivalentes sii tienen el mismo numero
    # de unos modulo 3.
    assert hom.equivalent("111", "")
    assert hom.equivalent("1", "1000")
    assert hom.equivalent("11", "0110")
    assert not hom.equivalent("1", "11")


def test_clase_de_equivalencia_paridad(parity_dfa: DFA) -> None:
    hom = Homomorphism(parity_dfa)
    clase = hom.equivalence_class("1", max_length=3)
    # Palabras de longitud <= 3 con numero IMPAR de unos.
    esperado = {
        w for n in range(0, 4)
        for w in ("".join(s) for s in product("01", repeat=n))
        if w.count("1") % 2 == 1
    }
    assert set(clase) == esperado


# ----------------------------------------------------------------------
# Nucleo y primer teorema de isomorfismo
# ----------------------------------------------------------------------

def test_nucleo_tiene_tamano_de_monoide(mod3_dfa: DFA) -> None:
    hom = Homomorphism(mod3_dfa)
    cls = hom.kernel(max_length=4)
    # Toda transformacion debe haber sido alcanzada por alguna palabra
    # de longitud <= 4 (el monoide tiene orden 3 y la BFS lo alcanza en
    # a lo sumo 2 pasos).
    assert len([f for f, ws in cls.items() if ws]) == hom.monoid.order


def test_primer_teorema_de_isomorfismo_paridad(parity_dfa: DFA) -> None:
    hom = Homomorphism(parity_dfa)
    assert hom.verify_first_isomorphism()


def test_primer_teorema_de_isomorfismo_mod3(mod3_dfa: DFA) -> None:
    hom = Homomorphism(mod3_dfa)
    assert hom.verify_first_isomorphism()


def test_primer_teorema_de_isomorfismo_ends01(ends_01_dfa: DFA) -> None:
    hom = Homomorphism(ends_01_dfa)
    assert hom.verify_first_isomorphism()


# ----------------------------------------------------------------------
# Reflexividad / simetria / transitividad de ~
# ----------------------------------------------------------------------

def test_relacion_es_de_equivalencia(parity_dfa: DFA) -> None:
    hom = Homomorphism(parity_dfa)
    palabras = ["", "0", "1", "00", "01", "10", "11", "010", "111"]
    # Reflexividad
    for w in palabras:
        assert hom.equivalent(w, w)
    # Simetria
    for u in palabras:
        for v in palabras:
            assert hom.equivalent(u, v) == hom.equivalent(v, u)
    # Transitividad
    for u in palabras:
        for v in palabras:
            for w in palabras:
                if hom.equivalent(u, v) and hom.equivalent(v, w):
                    assert hom.equivalent(u, w)


def test_quotient_estructura(mod3_dfa: DFA) -> None:
    hom = Homomorphism(mod3_dfa)
    cociente = hom.quotient(max_length=4)
    assert len(cociente) == hom.monoid.order
    # Cada clase debe estar bien representada.
    for rep, f, words in cociente:
        for w in words:
            assert hom.image(w) == f
        assert hom.image(rep) == f
