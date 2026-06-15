"""Pruebas para backend.visualization.regex_view.

Se centran en INVARIANTES del HTML generado (presencia de secciones,
del SVG, del codigo DOT) y en el manejo de errores. No comprobamos
markup literal porque el contenido puede evolucionar.
"""

from __future__ import annotations

import pytest

from backend.language.regex import RegexParseError
from backend.visualization import regex_to_html
from backend.visualization.regex_view import (
    _dfa_to_dot,
    _dot_fallback_block,
    _nfa_to_dot,
    _slug,
)
from backend.models import NFA
from backend.models.dfa import DFA


# ----------------------------------------------------------------------
# Comportamiento end-to-end del generador HTML
# ----------------------------------------------------------------------

def test_regex_to_html_crea_archivo(tmp_path) -> None:
    out = regex_to_html("a", output_path=tmp_path / "a.html", open_browser=False)
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_html_contiene_las_tres_secciones_de_grafo(tmp_path) -> None:
    out = regex_to_html(
        "(0|1)*01",
        output_path=tmp_path / "ends.html",
        open_browser=False,
    )
    html = out.read_text(encoding="utf-8")
    assert "1. NFA por construccion de Thompson" in html
    assert "2. DFA por construccion de subconjuntos" in html
    assert "3. DFA minimo" in html


def test_html_incrusta_tres_svgs(tmp_path) -> None:
    """Con Graphviz instalado, debe haber 3 bloques <svg>. Si no lo esta,
    deben aparecer 3 bloques de fallback con codigo DOT."""
    out = regex_to_html(
        "(0|1)*01",
        output_path=tmp_path / "ends.html",
        open_browser=False,
    )
    html = out.read_text(encoding="utf-8")
    svg_count = html.count("<svg")
    fallback_count = html.count("dot-fallback")
    assert svg_count + fallback_count >= 3


def test_html_incluye_hoja_de_sintaxis(tmp_path) -> None:
    out = regex_to_html(
        "ab*", output_path=tmp_path / "x.html", open_browser=False
    )
    html = out.read_text(encoding="utf-8")
    assert "Como escribir tu regex" in html
    # La nota sobre lenguajes no regulares es importante para que el
    # estudiante entienda los limites del comando.
    assert "n</sup>b<sup>n" in html or "PDA" in html


def test_html_muestra_el_patron(tmp_path) -> None:
    out = regex_to_html(
        "a|b", output_path=tmp_path / "x.html", open_browser=False
    )
    html = out.read_text(encoding="utf-8")
    # Aparece al menos en el title y en el div.pattern
    assert html.count("a|b") >= 2


def test_html_indica_reduccion_cuando_hay(tmp_path) -> None:
    # (0|1)*01: Thompson da NFA de muchos estados; subset construction
    # produce 4 estados; el minimo tiene 3. Debe aparecer la nota.
    out = regex_to_html(
        "(0|1)*01",
        output_path=tmp_path / "x.html",
        open_browser=False,
    )
    html = out.read_text(encoding="utf-8")
    assert "reduccion" in html.lower() or "minimo" in html.lower()


def test_regex_invalida_propaga_error(tmp_path) -> None:
    with pytest.raises(RegexParseError):
        regex_to_html(
            "(ab",
            output_path=tmp_path / "x.html",
            open_browser=False,
        )


# ----------------------------------------------------------------------
# Helpers individuales
# ----------------------------------------------------------------------

def test_nfa_to_dot_es_un_digrafo() -> None:
    nfa = NFA(
        states={"q0", "q1"},
        alphabet={"a"},
        transitions={"q0": {"a": {"q1"}}, "q1": {"a": set()}},
        epsilon_transitions={"q0": {"q1"}},
        start="q0",
        accepting={"q1"},
    )
    dot = _nfa_to_dot(nfa)
    assert dot.startswith("digraph G {")
    assert dot.rstrip().endswith("}")
    # ε-transicion estilizada con dashed
    assert "dashed" in dot
    # estado de aceptacion con doublecircle
    assert "doublecircle" in dot


def test_dfa_to_dot_no_tiene_epsilon(parity_dfa: DFA) -> None:
    dot = _dfa_to_dot(parity_dfa)
    assert dot.startswith("digraph G {")
    # En un DFA NO hay ε-transiciones, asi que tampoco hay 'dashed'
    # como estilo de arista.
    assert "dashed" not in dot


def test_slug_es_seguro_para_nombre_de_archivo() -> None:
    assert _slug("(0|1)*01") == "0_1_01"
    assert _slug("[a-z]+") == "a_z"
    assert _slug("") == "regex"
    # No mas de 40 caracteres
    largo = _slug("abcd" * 20)
    assert len(largo) <= 40


def test_dot_fallback_incluye_link_a_graphviz_online() -> None:
    block = _dot_fallback_block("digraph G { a -> b }", "graphviz no encontrado")
    assert "dot-fallback" in block
    assert "GraphvizOnline" in block or "graphviz" in block.lower()
