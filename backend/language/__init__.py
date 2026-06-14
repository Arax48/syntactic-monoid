"""
backend.language
================

Lenguajes formales: parseo de expresiones regulares (Thompson),
clasificacion en la jerarquia de Chomsky, lema de bombeo y
auto-generacion de automatas a partir de especificaciones.
"""

from backend.language.regex import (
    RegexParseError,
    parse,
    collect_alphabet,
    regex_to_nfa,
    regex_to_dfa,
)
from backend.language.info_sheet import InfoSheet, build_info_sheet

__all__ = [
    "RegexParseError",
    "parse",
    "collect_alphabet",
    "regex_to_nfa",
    "regex_to_dfa",
    "InfoSheet",
    "build_info_sheet",
]
