"""Pruebas del modelo estandar de Maquina de Turing (§6.1 De Castro)."""

import pytest

from backend.models.mt import (
    BLANCO,
    MT,
    CintaBidireccional,
    Desplazamiento,
    MTValidationError,
    ResultadoMT,
    TransicionMT,
)


# ----------------------------------------------------------------------
# MTs de ejemplo
# ----------------------------------------------------------------------

def _mt_empieza_con_a() -> MT:
    """MT que acepta el lenguaje {w ∈ {a,b}* : w empieza con 'a'}.

    Q = {q0, q_acc}, F = {q_acc}, Σ = Γ = {a, b}.
    δ(q0, a) = (q_acc, a, −).  Cualquier otra entrada aborta.
    """
    return MT(
        estados={"q0", "q_acc"},
        estado_inicial="q0",
        estados_aceptacion={"q_acc"},
        alfabeto_entrada={"a", "b"},
        alfabeto_cinta={"a", "b"},
        transiciones=[
            TransicionMT("q0", "a", "q_acc", "a", Desplazamiento.ESTACIONARIA),
        ],
        nombre="empieza_con_a",
    )


def _mt_a_estrella() -> MT:
    """MT que decide {a^n : n ≥ 0} sobre Σ = {a}.

    Avanza a la derecha consumiendo aes; al encontrar el primer blanco,
    pasa al estado de aceptacion. Decide el lenguaje (siempre se detiene).
    """
    return MT(
        estados={"q0", "q_acc"},
        estado_inicial="q0",
        estados_aceptacion={"q_acc"},
        alfabeto_entrada={"a"},
        alfabeto_cinta={"a"},
        transiciones=[
            TransicionMT("q0", "a", "q0", "a", Desplazamiento.DERECHA),
            TransicionMT("q0", BLANCO, "q_acc", BLANCO, Desplazamiento.ESTACIONARIA),
        ],
        nombre="a_estrella",
    )


# ----------------------------------------------------------------------
# Cinta bi-infinita
# ----------------------------------------------------------------------

def test_cinta_lee_blanco_a_la_izquierda_del_origen() -> None:
    """La cinta es infinita en ambas direcciones (§6.1): posiciones
    negativas devuelven el simbolo blanco."""
    cinta = CintaBidireccional("abc")
    cinta.desplazar(Desplazamiento.IZQUIERDA)
    assert cinta.cabezal == -1
    assert cinta.leer() == BLANCO


def test_cinta_escribe_y_lee_en_posicion_negativa() -> None:
    cinta = CintaBidireccional("ab")
    cinta.desplazar(Desplazamiento.IZQUIERDA)
    cinta.escribir("X")
    assert cinta.cabezal == -1
    assert cinta.leer() == "X"
    cinta.desplazar(Desplazamiento.DERECHA)
    assert cinta.leer() == "a"


def test_configuracion_instantanea_incluye_estado() -> None:
    cinta = CintaBidireccional("aab")
    cinta.desplazar(Desplazamiento.DERECHA)
    # cabezal en posicion 1, escaneando 'a' (segundo simbolo)
    config = cinta.configuracion_instantanea("q3")
    assert config == "aq3ab"


# ----------------------------------------------------------------------
# Validacion estructural
# ----------------------------------------------------------------------

def test_estados_aceptacion_vacios_se_rechazan() -> None:
    with pytest.raises(MTValidationError, match="F.*no puede ser vacio"):
        MT(
            estados={"q0"},
            estado_inicial="q0",
            estados_aceptacion=set(),
            alfabeto_entrada={"a"},
            alfabeto_cinta={"a"},
            transiciones=[],
        )


def test_blanco_no_puede_estar_en_gamma() -> None:
    with pytest.raises(MTValidationError, match="blanco.*externo"):
        MT(
            estados={"q0", "q1"},
            estado_inicial="q0",
            estados_aceptacion={"q1"},
            alfabeto_entrada={"a"},
            alfabeto_cinta={"a", BLANCO},   # BLANCO no debe estar en Γ
            transiciones=[],
        )


def test_blanco_no_puede_estar_en_sigma() -> None:
    with pytest.raises(MTValidationError, match="blanco.*Σ"):
        MT(
            estados={"q0", "q1"},
            estado_inicial="q0",
            estados_aceptacion={"q1"},
            alfabeto_entrada={"a", BLANCO},
            alfabeto_cinta={"a"},
            transiciones=[],
        )


def test_transiciones_desde_estados_de_aceptacion_son_prohibidas() -> None:
    """De Castro §6.1: la MT se detiene al ingresar a F."""
    with pytest.raises(MTValidationError, match="aceptacion"):
        MT(
            estados={"q0", "q1"},
            estado_inicial="q0",
            estados_aceptacion={"q1"},
            alfabeto_entrada={"a"},
            alfabeto_cinta={"a"},
            transiciones=[
                TransicionMT("q1", "a", "q0", "a", Desplazamiento.DERECHA),
            ],
        )


def test_transicion_duplicada_rompe_determinismo() -> None:
    with pytest.raises(MTValidationError, match="duplicada"):
        MT(
            estados={"q0", "q1"},
            estado_inicial="q0",
            estados_aceptacion={"q1"},
            alfabeto_entrada={"a"},
            alfabeto_cinta={"a"},
            transiciones=[
                TransicionMT("q0", "a", "q0", "a", Desplazamiento.DERECHA),
                TransicionMT("q0", "a", "q1", "a", Desplazamiento.ESTACIONARIA),
            ],
        )


def test_sigma_subconjunto_de_gamma() -> None:
    with pytest.raises(MTValidationError, match="Σ.*Γ"):
        MT(
            estados={"q0", "q1"},
            estado_inicial="q0",
            estados_aceptacion={"q1"},
            alfabeto_entrada={"a", "b"},
            alfabeto_cinta={"a"},   # 'b' no esta en Γ
            transiciones=[],
        )


# ----------------------------------------------------------------------
# Ejecucion
# ----------------------------------------------------------------------

def test_empieza_con_a_acepta_y_rechaza_correctamente() -> None:
    m = _mt_empieza_con_a()
    assert m.acepta("a")
    assert m.acepta("ab")
    assert m.acepta("aaa")
    assert not m.acepta("b")
    assert not m.acepta("ba")
    assert not m.acepta("")  # cadena vacia: q0 lee □, no hay transicion, abortado


def test_a_estrella_decide_correctamente() -> None:
    m = _mt_a_estrella()
    for n in range(0, 6):
        assert m.acepta("a" * n), f"deberia aceptar {'a' * n!r}"


def test_delta_indefinida_produce_abortado() -> None:
    m = _mt_empieza_con_a()
    resultado = m.ejecutar("b")
    assert resultado.resultado is ResultadoMT.ABORTADO


def test_bucle_infinito_detectado_con_max_pasos() -> None:
    """MT que se mueve indefinidamente a la derecha sin aceptar."""
    m = MT(
        estados={"q0", "q1"},
        estado_inicial="q0",
        estados_aceptacion={"q1"},
        alfabeto_entrada={"a"},
        alfabeto_cinta={"a"},
        transiciones=[
            TransicionMT("q0", "a", "q0", "a", Desplazamiento.DERECHA),
            TransicionMT("q0", BLANCO, "q0", BLANCO, Desplazamiento.DERECHA),
        ],
        nombre="loop_derecha",
    )
    r = m.ejecutar("a", max_pasos=50)
    assert r.resultado is ResultadoMT.BUCLE_INFINITO
    assert r.pasos == 50


def test_traza_registra_cada_paso() -> None:
    m = _mt_a_estrella()
    r = m.ejecutar("aa")
    # 3 pasos: leer 'a', leer 'a', leer □ + paso final con q_acc
    assert len(r.traza) >= 3
    # primer paso: estado q0, lee 'a'
    assert r.traza[0].estado == "q0"
    assert r.traza[0].leido == "a"
    # ultimo paso: estado q_acc (aceptacion)
    assert r.traza[-1].estado == "q_acc"


def test_simbolo_fuera_de_sigma_lanza_excepcion() -> None:
    m = _mt_empieza_con_a()
    with pytest.raises(ValueError, match="no pertenece al alfabeto"):
        m.ejecutar("aXb")


# ----------------------------------------------------------------------
# Serializacion
# ----------------------------------------------------------------------

def test_to_dict_y_from_dict_son_inversos() -> None:
    m = _mt_a_estrella()
    data = m.to_dict()
    assert data["tipo"] == "MT"
    m2 = MT.from_dict(data)
    assert m2.estados == m.estados
    assert m2.estado_inicial == m.estado_inicial
    assert m2.estados_aceptacion == m.estados_aceptacion
    assert set(t.lee for t in m2.transiciones) == set(t.lee for t in m.transiciones)
    # comportamiento equivalente
    for n in range(0, 4):
        assert m2.acepta("a" * n) == m.acepta("a" * n)


def test_from_dict_acepta_alias_de_desplazamiento() -> None:
    """Acepta tanto los simbolos del libro (←, →, −) como los alias L/R/S
    para facilitar la entrada desde la web."""
    data = {
        "estados": ["q0", "q1"],
        "estado_inicial": "q0",
        "estados_aceptacion": ["q1"],
        "alfabeto_entrada": ["a"],
        "alfabeto_cinta": ["a"],
        "transiciones": [
            {"desde": "q0", "lee": "a", "a": "q1", "escribe": "a", "desplazamiento": "R"},
        ],
    }
    m = MT.from_dict(data)
    assert m.transiciones[0].desplazamiento is Desplazamiento.DERECHA
