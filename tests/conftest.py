"""Configuracion comun para pytest.

Asegura que la raiz del proyecto este en sys.path para poder importar
los modulos del proyecto desde los tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models import DFA  # noqa: E402


@pytest.fixture
def parity_dfa() -> DFA:
    """DFA de paridad de unos (ejemplo 1)."""
    return DFA(
        states={"Par", "Impar"},
        alphabet={"0", "1"},
        transitions={
            "Par": {"0": "Par", "1": "Impar"},
            "Impar": {"0": "Impar", "1": "Par"},
        },
        start="Par",
        accepting={"Par"},
        name="Paridad de 1s",
    )


@pytest.fixture
def mod3_dfa() -> DFA:
    """DFA que cuenta unos modulo 3 (ejemplo 2)."""
    return DFA(
        states={"r0", "r1", "r2"},
        alphabet={"0", "1"},
        transitions={
            "r0": {"0": "r0", "1": "r1"},
            "r1": {"0": "r1", "1": "r2"},
            "r2": {"0": "r2", "1": "r0"},
        },
        start="r0",
        accepting={"r0"},
        name="Mod 3 unos",
    )


@pytest.fixture
def ends_01_dfa() -> DFA:
    """DFA de cadenas que terminan en 01 (ejemplo 3)."""
    return DFA(
        states={"s0", "s1", "s2"},
        alphabet={"0", "1"},
        transitions={
            "s0": {"0": "s1", "1": "s0"},
            "s1": {"0": "s1", "1": "s2"},
            "s2": {"0": "s1", "1": "s0"},
        },
        start="s0",
        accepting={"s2"},
        name="Termina en 01",
    )
