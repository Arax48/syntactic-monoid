"""Pruebas para backend.language.regex (parser + Thompson)."""

from __future__ import annotations

import pytest

from backend.language.regex import (
    AnyChar,
    CharClass,
    Concat,
    Epsilon,
    RegexParseError,
    Star,
    Symbol,
    Union,
    collect_alphabet,
    parse,
    regex_to_dfa,
    regex_to_nfa,
)


# ----------------------------------------------------------------------
# Parser - AST
# ----------------------------------------------------------------------

def test_parse_vacio_es_epsilon() -> None:
    assert parse("") == Epsilon()


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
    assert parse("a?") == Union(Symbol("a"), Epsilon())


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
    # "a|" significa "a o epsilon"
    assert parse("a|") == Union(Symbol("a"), Epsilon())


def test_parse_grupo_vacio_es_epsilon() -> None:
    assert parse("()") == Epsilon()


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
# Thompson - NFA acepta / rechaza
# ----------------------------------------------------------------------

def test_nfa_simbolo_simple() -> None:
    nfa = regex_to_nfa("a")
    assert nfa.accepts("a")
    assert not nfa.accepts("")
    assert not nfa.accepts("aa")


def test_nfa_concatenacion() -> None:
    nfa = regex_to_nfa("ab")
    assert nfa.accepts("ab")
    assert not nfa.accepts("a")
    assert not nfa.accepts("b")
    assert not nfa.accepts("aab")


def test_nfa_union() -> None:
    nfa = regex_to_nfa("a|b")
    assert nfa.accepts("a")
    assert nfa.accepts("b")
    assert not nfa.accepts("ab")
    assert not nfa.accepts("")


def test_nfa_kleene_acepta_epsilon_y_repeticiones() -> None:
    # 'a*' debe aceptar ε, a, aa, aaa, ...
    nfa = regex_to_nfa("a*")
    assert nfa.accepts("")
    assert nfa.accepts("a")
    assert nfa.accepts("aaaa")


def test_nfa_plus_no_acepta_epsilon() -> None:
    nfa = regex_to_nfa("a+")
    assert not nfa.accepts("")
    assert nfa.accepts("a")
    assert nfa.accepts("aaa")


def test_nfa_interrogacion_acepta_cero_o_uno() -> None:
    nfa = regex_to_nfa("a?", alphabet={"a"})
    assert nfa.accepts("")
    assert nfa.accepts("a")
    assert not nfa.accepts("aa")


def test_nfa_de_clase_de_caracteres() -> None:
    nfa = regex_to_nfa("[ab]+", alphabet={"a", "b"})
    assert nfa.accepts("ababab")
    assert nfa.accepts("a")
    assert not nfa.accepts("")
    # Un simbolo fuera del alfabeto del NFA es un error de uso, no un
    # "rechazo": la API del NFA lo senala con ValueError.
    with pytest.raises(ValueError):
        nfa.accepts("c")


def test_nfa_termina_en_01() -> None:
    # Regex clasica: (0|1)*01
    nfa = regex_to_nfa("(0|1)*01")
    assert nfa.accepts("01")
    assert nfa.accepts("001")
    assert nfa.accepts("1101")
    assert not nfa.accepts("")
    assert not nfa.accepts("0")
    assert not nfa.accepts("1")
    assert not nfa.accepts("10")


def test_nfa_paridad_de_unos() -> None:
    # Numero par de 1s sobre el alfabeto {0, 1}.
    # Regex equivalente: (0*10*1)*0*
    nfa = regex_to_nfa("(0*10*1)*0*", alphabet={"0", "1"})
    assert nfa.accepts("")          # 0 unos: par
    assert nfa.accepts("0")
    assert nfa.accepts("11")
    assert nfa.accepts("1010")
    assert nfa.accepts("00100100")
    assert not nfa.accepts("1")
    assert not nfa.accepts("111")
    assert not nfa.accepts("0010")


def test_nfa_comodin_punto_recorre_alfabeto() -> None:
    nfa = regex_to_nfa(".", alphabet={"a", "b", "c"})
    assert nfa.accepts("a")
    assert nfa.accepts("b")
    assert nfa.accepts("c")
    assert not nfa.accepts("")
    assert not nfa.accepts("ab")


def test_regex_vacia_requiere_alfabeto_explicito() -> None:
    # Sin literales ni alfabeto explicito no podemos construir el NFA
    # (el validador del NFA exige Sigma no vacio).
    with pytest.raises(ValueError):
        regex_to_nfa("")
    # Pero con alfabeto explicito si:
    nfa = regex_to_nfa("", alphabet={"a"})
    assert nfa.accepts("")
    assert not nfa.accepts("a")


# ----------------------------------------------------------------------
# Conversion a DFA via subset construction
# ----------------------------------------------------------------------

def test_dfa_de_regex_acepta_lo_mismo_que_el_nfa() -> None:
    nfa = regex_to_nfa("(0|1)*01")
    dfa = nfa.to_dfa()
    for w in ("01", "001", "1101", "", "0", "1", "10", "111101", "100"):
        assert dfa.accepts(w) == nfa.accepts(w), w


def test_regex_to_dfa_paridad_minimizado_tiene_dos_estados() -> None:
    # El DFA minimo del lenguaje "numero par de 1s" tiene 2 estados.
    dfa = regex_to_dfa("(0*10*1)*0*", alphabet={"0", "1"})
    minimo = dfa.minimize()
    assert len(minimo.states) == 2


def test_regex_to_dfa_mod3_minimizado_tiene_tres_estados() -> None:
    # |w|_1 ≡ 0 (mod 3): la regex 0*(10*10*10*)* admite ceros iniciales
    # libres y luego grupos de exactamente tres unos cada uno (con
    # ceros intercalados entre ellos), reconociendo asi todas las
    # palabras cuyo numero de unos es multiplo de 3.
    dfa = regex_to_dfa("0*(10*10*10*)*", alphabet={"0", "1"})
    minimo = dfa.minimize()
    assert len(minimo.states) == 3
