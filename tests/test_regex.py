"""Pruebas para backend.language.regex (parser + Thompson)."""

from __future__ import annotations

import pytest

from backend.language.regex import (
    AnyChar,
    CharClass,
    Concat,
    Lambda,
    RegexParseError,
    Star,
    Symbol,
    Union,
    collect_alphabet,
    parse,
    regex_to_afd,
    regex_to_afn,
)


# ----------------------------------------------------------------------
# Parser - AST
# ----------------------------------------------------------------------

def test_parse_vacio_es_epsilon() -> None:
    assert parse("") == Lambda()


def test_parse_simbolo_literal() -> None:
    assert parse("a") == Symbol("a")


def test_parse_concatenacion() -> None:
    assert parse("ab") == Concat(Symbol("a"), Symbol("b"))


def test_parse_concatenacion_es_asociativa_a_la_izquierda() -> None:
    # "abc" se parsea como Concat(Concat(a,b), c)
    expected = Concat(Concat(Symbol("a"), Symbol("b")), Symbol("c"))
    assert parse("abc") == expected


def test_parse_union_tiene_menor_precedencia_que_concat() -> None:
    # "ab|cd" debe ser Union(Concat(a,b), Concat(c,d)) y no
    # Concat(a, Concat(Union(b,c), d)).
    expected = Union(
        Concat(Symbol("a"), Symbol("b")),
        Concat(Symbol("c"), Symbol("d")),
    )
    assert parse("ab|cd") == expected


def test_parse_parentesis_invierten_precedencia() -> None:
    # a(b|c)d se parsea como Concat(Concat(a, b|c), d) por asociatividad
    # izquierda; lo importante es que (b|c) sea un sub-arbol completo
    # y NO que la union "se trague" la `d`.
    expected = Concat(
        Concat(Symbol("a"), Union(Symbol("b"), Symbol("c"))),
        Symbol("d"),
    )
    assert parse("a(b|c)d") == expected


def test_parse_kleene_aplica_solo_al_atomo() -> None:
    # ab* = Concat(a, Star(b))   (no Star(Concat(a,b)))
    assert parse("ab*") == Concat(Symbol("a"), Star(Symbol("b")))


def test_parse_kleene_con_grupo() -> None:
    assert parse("(ab)*") == Star(Concat(Symbol("a"), Symbol("b")))


def test_parse_plus_es_azucar_para_concatenacion_con_estrella() -> None:
    assert parse("a+") == Concat(Symbol("a"), Star(Symbol("a")))


def test_parse_interrogacion_es_azucar_para_union_con_epsilon() -> None:
    assert parse("a?") == Union(Symbol("a"), Lambda())


def test_parse_clase_de_caracteres() -> None:
    result = parse("[abc]")
    assert isinstance(result, CharClass)
    assert result.chars == frozenset({"a", "b", "c"})


def test_parse_clase_con_rango() -> None:
    result = parse("[a-d]")
    assert isinstance(result, CharClass)
    assert result.chars == frozenset({"a", "b", "c", "d"})


def test_parse_comodin_punto() -> None:
    assert parse(".") == AnyChar()


def test_parse_escape_de_caracter_especial() -> None:
    # \( debe ser un parentesis literal
    assert parse("\\(") == Symbol("(")
    assert parse("\\*") == Symbol("*")


def test_parse_union_con_lado_vacio_produce_epsilon() -> None:
    # "a|" significa "a o λ"
    assert parse("a|") == Union(Symbol("a"), Lambda())


def test_parse_grupo_vacio_es_epsilon() -> None:
    assert parse("()") == Lambda()


# ----------------------------------------------------------------------
# Parser - errores
# ----------------------------------------------------------------------

def test_parse_parentesis_sin_cerrar_falla() -> None:
    with pytest.raises(RegexParseError):
        parse("(ab")


def test_parse_estrella_solitaria_falla() -> None:
    with pytest.raises(RegexParseError):
        parse("*a")


def test_parse_clase_sin_cerrar_falla() -> None:
    with pytest.raises(RegexParseError):
        parse("[abc")


def test_parse_rango_invertido_falla() -> None:
    with pytest.raises(RegexParseError):
        parse("[z-a]")


def test_parse_escape_al_final_falla() -> None:
    with pytest.raises(RegexParseError):
        parse("a\\")


# ----------------------------------------------------------------------
# collect_alphabet
# ----------------------------------------------------------------------

def test_collect_alphabet_simbolo_simple() -> None:
    assert collect_alphabet(parse("a")) == frozenset({"a"})


def test_collect_alphabet_palabra() -> None:
    assert collect_alphabet(parse("abc")) == frozenset({"a", "b", "c"})


def test_collect_alphabet_ignora_anychar() -> None:
    # '.' depende del alfabeto externo, no aporta literales propios.
    assert collect_alphabet(parse(".")) == frozenset()


def test_collect_alphabet_incluye_clase_de_caracteres() -> None:
    assert collect_alphabet(parse("[ab]c")) == frozenset({"a", "b", "c"})


# ----------------------------------------------------------------------
# Thompson - AFN acepta / rechaza
# ----------------------------------------------------------------------

def test_nfa_simbolo_simple() -> None:
    afn = regex_to_afn("a")
    assert afn.accepts("a")
    assert not afn.accepts("")
    assert not afn.accepts("aa")


def test_nfa_concatenacion() -> None:
    afn = regex_to_afn("ab")
    assert afn.accepts("ab")
    assert not afn.accepts("a")
    assert not afn.accepts("b")
    assert not afn.accepts("aab")


def test_nfa_union() -> None:
    afn = regex_to_afn("a|b")
    assert afn.accepts("a")
    assert afn.accepts("b")
    assert not afn.accepts("ab")
    assert not afn.accepts("")


def test_nfa_kleene_acepta_lambda_y_repeticiones() -> None:
    # 'a*' debe aceptar λ, a, aa, aaa, ...
    afn = regex_to_afn("a*")
    assert afn.accepts("")
    assert afn.accepts("a")
    assert afn.accepts("aaaa")


def test_nfa_plus_no_acepta_epsilon() -> None:
    afn = regex_to_afn("a+")
    assert not afn.accepts("")
    assert afn.accepts("a")
    assert afn.accepts("aaa")


def test_nfa_interrogacion_acepta_cero_o_uno() -> None:
    afn = regex_to_afn("a?", alphabet={"a"})
    assert afn.accepts("")
    assert afn.accepts("a")
    assert not afn.accepts("aa")


def test_nfa_de_clase_de_caracteres() -> None:
    afn = regex_to_afn("[ab]+", alphabet={"a", "b"})
    assert afn.accepts("ababab")
    assert afn.accepts("a")
    assert not afn.accepts("")
    # Un simbolo fuera del alfabeto del AFN es un error de uso, no un
    # "rechazo": la API del AFN lo senala con ValueError.
    with pytest.raises(ValueError):
        afn.accepts("c")


def test_nfa_termina_en_01() -> None:
    # Regex clasica: (0|1)*01
    afn = regex_to_afn("(0|1)*01")
    assert afn.accepts("01")
    assert afn.accepts("001")
    assert afn.accepts("1101")
    assert not afn.accepts("")
    assert not afn.accepts("0")
    assert not afn.accepts("1")
    assert not afn.accepts("10")


def test_nfa_paridad_de_unos() -> None:
    # Numero par de 1s sobre el alfabeto {0, 1}.
    # Regex equivalente: (0*10*1)*0*
    afn = regex_to_afn("(0*10*1)*0*", alphabet={"0", "1"})
    assert afn.accepts("")          # 0 unos: par
    assert afn.accepts("0")
    assert afn.accepts("11")
    assert afn.accepts("1010")
    assert afn.accepts("00100100")
    assert not afn.accepts("1")
    assert not afn.accepts("111")
    assert not afn.accepts("0010")


def test_nfa_comodin_punto_recorre_alfabeto() -> None:
    afn = regex_to_afn(".", alphabet={"a", "b", "c"})
    assert afn.accepts("a")
    assert afn.accepts("b")
    assert afn.accepts("c")
    assert not afn.accepts("")
    assert not afn.accepts("ab")


def test_regex_vacia_requiere_alfabeto_explicito() -> None:
    # Sin literales ni alfabeto explicito no podemos construir el AFN
    # (el validador del AFN exige Sigma no vacio).
    with pytest.raises(ValueError):
        regex_to_afn("")
    # Pero con alfabeto explicito si:
    afn = regex_to_afn("", alphabet={"a"})
    assert afn.accepts("")
    assert not afn.accepts("a")


# ----------------------------------------------------------------------
# Conversion a AFD via subset construction
# ----------------------------------------------------------------------

def test_dfa_de_regex_acepta_lo_mismo_que_el_nfa() -> None:
    afn = regex_to_afn("(0|1)*01")
    dfa = afn.to_afd()
    for w in ("01", "001", "1101", "", "0", "1", "10", "111101", "100"):
        assert dfa.accepts(w) == afn.accepts(w), w


def test_regex_to_afd_paridad_minimizado_tiene_dos_estados() -> None:
    # El AFD minimo del lenguaje "numero par de 1s" tiene 2 estados.
    dfa = regex_to_afd("(0*10*1)*0*", alphabet={"0", "1"})
    minimo = dfa.minimize()
    assert len(minimo.states) == 2


def test_regex_to_afd_mod3_minimizado_tiene_tres_estados() -> None:
    # |w|_1 ≡ 0 (mod 3): la regex 0*(10*10*10*)* admite ceros iniciales
    # libres y luego grupos de exactamente tres unos cada uno (con
    # ceros intercalados entre ellos), reconociendo asi todas las
    # palabras cuyo numero de unos es multiplo de 3.
    dfa = regex_to_afd("0*(10*10*10*)*", alphabet={"0", "1"})
    minimo = dfa.minimize()
    assert len(minimo.states) == 3
