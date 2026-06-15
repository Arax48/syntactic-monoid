"""Pruebas para algebra.py (homomorfismo, nucleo, isomorfismo)."""

from __future__ import annotations

from itertools import product

from backend.models import AFD
from backend.algebra import Homomorphism, TransitionMonoid


# ----------------------------------------------------------------------
# phi(uv) = phi(u).then(phi(v))
# ----------------------------------------------------------------------

def test_phi_es_homomorfismo_paridad(parity_dfa: AFD) -> None:
    hom = Homomorphism(parity_dfa)
    assert hom.verify_homomorphism(max_length=4)


def test_phi_es_homomorfismo_mod3(mod3_dfa: AFD) -> None:
    hom = Homomorphism(mod3_dfa)
    assert hom.verify_homomorphism(max_length=4)


def test_phi_es_homomorfismo_ends01(ends_01_dfa: AFD) -> None:
    hom = Homomorphism(ends_01_dfa)
    assert hom.verify_homomorphism(max_length=4)


# ----------------------------------------------------------------------
# Equivalencias entre palabras
# ----------------------------------------------------------------------

def test_equivalentes_en_paridad(parity_dfa: AFD) -> None:
    hom = Homomorphism(parity_dfa)
    # λ, "00", "11" inducen la identidad
    assert hom.equivalent("", "00")
    assert hom.equivalent("", "11")
    assert hom.equivalent("00", "11")
    assert hom.equivalent("1", "10")
    assert not hom.equivalent("1", "11")


def test_equivalentes_en_mod3(mod3_dfa: AFD) -> None:
    hom = Homomorphism(mod3_dfa)
    # En Z/3, dos palabras son equivalentes sii tienen el mismo numero
    # de unos modulo 3.
    assert hom.equivalent("111", "")
    assert hom.equivalent("1", "1000")
    assert hom.equivalent("11", "0110")
    assert not hom.equivalent("1", "11")


def test_clase_de_equivalencia_paridad(parity_dfa: AFD) -> None:
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

def test_nucleo_tiene_tamano_de_monoide(mod3_dfa: AFD) -> None:
    hom = Homomorphism(mod3_dfa)
    cls = hom.kernel(max_length=4)
    # Toda transformacion debe haber sido alcanzada por alguna palabra
    # de longitud <= 4 (el monoide tiene orden 3 y la BFS lo alcanza en
    # a lo sumo 2 pasos).
    assert len([f for f, ws in cls.items() if ws]) == hom.monoid.order


def _verifica_biyeccion_clase_a_imagen(hom: Homomorphism, max_length: int) -> None:
    """Verificacion explicita y NO-vacua del Primer Teorema:

        (i)  cada f in M(A) es alcanzada por alguna palabra de longitud
             <= max_length, y
        (ii) palabras en clases distintas se mapean a transformaciones
             distintas.
    """
    cls = hom.kernel(max_length=max_length)
    no_vacias = [f for f, ws in cls.items() if ws]
    assert len(no_vacias) == hom.monoid.order, (
        "phi NO es sobreyectivo sobre M(A) hasta longitud "
        f"{max_length}: {len(no_vacias)} != {hom.monoid.order}"
    )
    for f, words in cls.items():
        for w in words:
            assert hom.image(w) == f, (
                f"palabra {w!r} agrupada bajo {f} pero phi({w!r}) != f"
            )
    # Inyectividad clase -> transformacion: si dos clases tienen la misma
    # transformacion etiqueta, debian haber sido fusionadas.
    etiquetas = [f for f, ws in cls.items() if ws]
    assert len(set(etiquetas)) == len(etiquetas)


def test_primer_teorema_de_isomorfismo_paridad(parity_dfa: AFD) -> None:
    hom = Homomorphism(parity_dfa)
    assert hom.verify_first_isomorphism()
    _verifica_biyeccion_clase_a_imagen(hom, max_length=hom.monoid.order)


def test_primer_teorema_de_isomorfismo_mod3(mod3_dfa: AFD) -> None:
    hom = Homomorphism(mod3_dfa)
    assert hom.verify_first_isomorphism()
    _verifica_biyeccion_clase_a_imagen(hom, max_length=hom.monoid.order)


def test_primer_teorema_de_isomorfismo_ends01(ends_01_dfa: AFD) -> None:
    hom = Homomorphism(ends_01_dfa)
    assert hom.verify_first_isomorphism()
    _verifica_biyeccion_clase_a_imagen(hom, max_length=hom.monoid.order)


def test_verify_first_isomorphism_detecta_truncado_insuficiente(ends_01_dfa: AFD) -> None:
    """Prueba que el verificador NO siempre devuelve True (no es vacuo).

    En el AFD "termina en 01", M(A) tiene 5 elementos y el representante
    mas largo tiene longitud 2 (`01` o `11`). Si truncamos por debajo
    todavia se ven todos. Pero si construimos un automata cuyo monoide
    requiera longitudes mayores, la verificacion deberia fallar.

    Aqui simplemente verificamos que el verificador es sensible al limite.
    """
    hom = Homomorphism(ends_01_dfa)
    # Con max_length = 0 solo vemos λ -> 1 clase (la identidad).
    # Si M(A) tiene >= 2 elementos, debe devolver False.
    assert hom.monoid.order > 1
    assert hom.verify_first_isomorphism(max_length=0) is False


# ----------------------------------------------------------------------
# verify_homomorphism
# ----------------------------------------------------------------------

def test_verify_homomorphism_incluye_neutro(parity_dfa: AFD) -> None:
    """phi(λ) debe ser id_Q ademas de la propiedad multiplicativa."""
    hom = Homomorphism(parity_dfa)
    assert hom.image("") == hom.monoid.identity
    assert hom.verify_homomorphism(max_length=3)


# ----------------------------------------------------------------------
# Conformidad Proposicion 3: ~ es mas fina que ~_L
# ----------------------------------------------------------------------

def test_congruencia_de_transicion_es_mas_fina_que_lenguaje(ends_01_dfa: AFD) -> None:
    """Demuestra empiricamente la Proposicion 3 del informe:

        u ~ v  ==>  (q0 alcanza el mismo estado desde xu o xv para todo x)
                ==>  xu in L(A)  ssi  xv in L(A) (caso particular y=eps).

    En el AFD "termina en 01", verificamos que pares ~-equivalentes son
    tambien congruentes para L(A).
    """
    from itertools import product as iproduct

    hom = Homomorphism(ends_01_dfa)
    sigma = sorted(ends_01_dfa.alphabet)
    palabras = [""] + [
        "".join(s) for n in range(1, 4) for s in iproduct(sigma, repeat=n)
    ]
    contexts = palabras
    for u in palabras:
        for v in palabras:
            if hom.equivalent(u, v):
                for x in contexts:
                    for y in contexts:
                        assert (
                            ends_01_dfa.accepts(x + u + y)
                            == ends_01_dfa.accepts(x + v + y)
                        )


# ----------------------------------------------------------------------
# Reflexividad / simetria / transitividad de ~
# ----------------------------------------------------------------------

def test_relacion_es_de_equivalencia(parity_dfa: AFD) -> None:
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


def test_quotient_estructura(mod3_dfa: AFD) -> None:
    hom = Homomorphism(mod3_dfa)
    cociente = hom.quotient(max_length=4)
    assert len(cociente) == hom.monoid.order
    # Cada clase debe estar bien representada.
    for rep, f, words in cociente:
        for w in words:
            assert hom.image(w) == f
        assert hom.image(rep) == f
